"""Offline textbook extraction, structural review gate and HTML packaging. Python 3.10+."""
import argparse
import base64
import copy
import hashlib
import html
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADING = re.compile(r'^(第[一二三四五六七八九十百\d]+章\s*.+|\d+\.\d+(?:\.\d+)?\s+.+)$')
MATH = re.compile(r'[=<>≤≥∈∉∪∩√∞∑±]|\\[a-zA-Z]+|\$')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def extract(pdf, config):
    from pypdf import PdfReader
    reader = PdfReader(pdf)
    cfg = read(config) if config else {}
    pages, nodes, formulas = [], [], []
    root = {'id':'book', 'title':cfg.get('title', Path(pdf).stem), 'kind':'book',
            'origin':'metadata', 'sources':[], 'formula_ids':[], 'review':'pending'}
    nodes.append(root)
    tree = {'node_id':'book', 'children':[]}
    chapter, section = tree, tree
    offset = cfg.get('printed_page_offset', 0)
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        pages.append({'pdf_page':i, 'printed_page':str(i+offset), 'text':text,
                      'review':'pending', 'reviewer':'', 'note':'',
                      'extraction':'text-layer' if text.strip() else 'empty-needs-manual-transcription'})
        for line_number, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            source = {'pdf_page':i, 'line':line_number, 'quote':line}
            if HEADING.match(line):
                node = {'id':f'n{len(nodes)}', 'title':line, 'kind':'heading', 'origin':'textbook',
                        'sources':[source], 'formula_ids':[], 'review':'pending'}
                nodes.append(node)
                branch = {'node_id':node['id'], 'children':[]}
                if line.startswith('第'):
                    tree['children'].append(branch)
                    chapter = section = branch
                elif re.match(r'^\d+\.\d+\.\d+', line):
                    section['children'].append(branch)
                else:
                    chapter['children'].append(branch)
                    section = branch
            elif line:
                node = {'id':f'n{len(nodes)}', 'title':line, 'kind':'excerpt', 'origin':'textbook',
                        'sources':[source], 'formula_ids':[], 'review':'pending'}
                nodes.append(node)
                section['children'].append({'node_id':node['id'], 'children':[]})
            else:
                continue
            if MATH.search(line):
                # Only explicit dollar-delimited LaTeX is copied. No inferred PDF math conversion.
                matches = re.findall(r'\$\$?(.*?)\$\$?', line)
                for raw_math in (matches or [line]):
                    fid = f'f{len(formulas)+1}'
                    formulas.append({'id':fid, 'raw':raw_math, 'latex':raw_math if matches else None,
                                     'source':source, 'review':'pending', 'reviewer':'', 'note':''})
                    node['formula_ids'].append(fid)
    return {'schema_version':'1.0', 'book':{'title':root['title'], 'edition':cfg.get('edition','请填写教材版本'),
             'publisher':cfg.get('publisher','人教A版（须核对）'), 'pdf_name':Path(pdf).name,
             'sha256':sha(pdf), 'page_count':len(pages), 'printed_page_offset':offset},
            'pages':pages, 'nodes':nodes, 'formulas':formulas, 'textbook':tree,
            'exam':{'node_id':'book', 'children':[]}, 'relations':[],
            'structure_review':{'textbook':'pending','exam':'pending','reviewer':'','note':''}}

def validate(data, release=False):
    errors = []
    def check(test, message):
        if not test: errors.append(message)
    check(data.get('schema_version') == '1.0', 'schema_version 必须为 1.0')
    book = data.get('book', {})
    check(isinstance(book.get('page_count'), int) and book.get('page_count',0)>0, 'page_count 无效')
    check(bool(re.fullmatch(r'[a-f0-9]{64}', book.get('sha256',''))), 'PDF SHA256 无效')
    pages = data.get('pages', [])
    check([p.get('pdf_page') for p in pages] == list(range(1,book.get('page_count',0)+1)), 'pages 必须连续且覆盖全部 PDF 页')
    pmap = {p.get('pdf_page'):p for p in pages}
    nodes, formulas = data.get('nodes',[]), data.get('formulas',[])
    nmap = {n.get('id'):n for n in nodes}
    fmap = {f.get('id'):f for f in formulas}
    check(len(nmap)==len(nodes) and None not in nmap, 'node id 重复或缺失')
    check(len(fmap)==len(formulas) and None not in fmap, 'formula id 重复或缺失')
    def source(s, label):
        p = pmap.get(s.get('pdf_page'))
        check(bool(p), label+' 页码无效')
        check(isinstance(s.get('line'),int) and s.get('line',0)>0, label+' 行号无效')
        check(bool(s.get('quote')), label+' 缺少原文')
        if p:
            lines = p.get('text','').splitlines()
            index = s.get('line',0)-1
            check(0<=index<len(lines) and lines[index].strip()==s.get('quote'), label+' 原文与逐页文本不一致')
    for p in pages:
        check(p.get('review') in ['pending','approved'], 'page review 无效')
        if release:
            check(p.get('review')=='approved' and bool(p.get('reviewer')), f"PDF 第 {p.get('pdf_page')} 页未签署复核")
            check(bool(p.get('text','').strip()), '空白/扫描页需要人工转录；不能直接发布')
    for n in nodes:
        check(isinstance(n.get('title'),str) and bool(n.get('title')), 'node title 无效')
        check(n.get('origin') in ['textbook','teacher','metadata'], 'node origin 无效')
        check(n.get('review') in ['pending','approved'], 'node review 无效')
        if n.get('origin')=='textbook': check(bool(n.get('sources')), n['id']+' 缺少教材溯源')
        if n.get('origin')=='teacher': check(bool(n.get('rationale')), n['id']+' 教师补充缺少说明')
        for s in n.get('sources',[]): source(s,n['id'])
        for fid in n.get('formula_ids',[]): check(fid in fmap, n['id']+' 公式引用不存在')
        if release: check(n.get('review')=='approved', n['id']+' 未复核')
    for f in formulas:
        source(f.get('source',{}),f['id'])
        check(f.get('review') in ['pending','approved'], 'formula review 无效')
        if f.get('latex') is not None: check(isinstance(f['latex'],str), 'latex 必须是字符串或 null')
        if release:
            check(f.get('review')=='approved' and bool(f.get('reviewer')) and bool(f.get('latex')), f['id']+' 公式未签署复核/未转录')
    def walk(branch, mode, seen, ancestors, depth=0):
        if depth>100: errors.append('树深度超过 100'); return
        nid=branch.get('node_id')
        check(nid in nmap, mode+' 引用不存在: '+str(nid))
        check(nid not in ancestors, mode+' 循环: '+str(nid))
        check(nid not in seen, mode+' 重复节点: '+str(nid))
        seen.add(nid)
        n=nmap.get(nid,{})
        if mode=='textbook':
            check(n.get('origin') in ['textbook','metadata'], '严格教材树含教师补充')
            if n.get('origin')=='textbook': check(any(s.get('quote')==n.get('title') for s in n.get('sources',[])), '严格教材标题必须保留原文')
        if nid in ancestors: return
        for child in branch.get('children',[]): walk(child,mode,seen,ancestors|{nid},depth+1)
    for mode in ['textbook','exam']:
        seen=set()
        walk(data.get(mode,{}),mode,seen,set())
        if mode=='textbook':
            expected={n['id'] for n in nodes if n.get('origin') in ['textbook','metadata']}
            check(seen==expected, '教材树必须覆盖所有教材/元数据节点')
    # Strict preorder must not reverse extracted source order; hierarchy is still a human decision.
    def order(b):
        n=nmap.get(b.get('node_id'),{})
        seq=[(s['pdf_page'],s['line']) for s in n.get('sources',[])[:1]]
        for c in b.get('children',[]): seq+=order(c)
        return seq
    sequence=order(data.get('textbook',{}))
    check(sequence==sorted(sequence), '教材树顺序与原文页/行顺序不一致')
    for edge in data.get('relations',[]):
        check(edge.get('from') in nmap and edge.get('to') in nmap, '关系端点不存在')
        check(edge.get('type') in ['prerequisite','equivalent','application','contrast'], '关系类型无效')
        check(bool(edge.get('rationale')), '关系缺少教师依据')
        if release: check(edge.get('review')=='approved', '复习关系未复核')
    if release:
        review=data.get('structure_review',{})
        check(all(review.get(m)=='approved' for m in ['textbook','exam']) and bool(review.get('reviewer')), '双模式结构未签署复核')
        check(bool(data.get('exam',{}).get('children')), '复习模式不能为空')
    return errors

def latex_check(data, node='node'):
    result=subprocess.run([node,str(ROOT/'scripts/check_math.cjs'),str(ROOT/'assets/vendor/katex.js')],
        input=json.dumps(data.get('formulas',[])),text=True,encoding='utf-8',capture_output=True)
    if result.returncode: raise ValueError(result.stderr or result.stdout)
    return json.loads(result.stdout)

def vendor_check():
    manifest=read(ROOT/'assets/vendor/manifest.json')
    for item in manifest['files']:
        if sha(ROOT/'assets/vendor'/item['file'])!=item['sha256']: raise ValueError('vendor hash mismatch: '+item['file'])

def build(data, output, node='node', release=False):
    errors=validate(data,release)
    if errors: raise ValueError('\n'.join(errors))
    math=latex_check(data,node)
    if release and any(not f['valid'] for f in math): raise ValueError('KaTeX 语法校验失败: '+json.dumps(math,ensure_ascii=False))
    vendor_check()
    vendor=ROOT/'assets/vendor'
    css=(vendor/'katex.css').read_text(encoding='utf-8')
    def embed_font(match):
        name=match.group(1)
        path=vendor/name
        mime='font/woff2' if name.endswith('.woff2') else ('font/woff' if name.endswith('.woff') else 'font/ttf')
        return 'url(data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+')'
    css=re.sub(r'url\([\"\']?(fonts/[^)\"\']+)[\"\']?\)',embed_font,css)
    payload=copy.deepcopy(data)
    payload['build']={'release':release, 'math_validation':math}
    template=(ROOT/'assets/template.html').read_text(encoding='utf-8')
    js='\n'.join((vendor/name).read_text(encoding='utf-8') for name in ['d3.js','markmap.js','katex.js'])
    js=re.sub(r'//# sourceMappingURL=.*', '', js)
    js=re.sub(r'</script', r'<\/script',js,flags=re.I)
    replacements={'__TITLE__':html.escape(data['book']['title']), '__KATEX_CSS__':css,
                  '__VENDOR_JS__':js,'__DATA__':json.dumps(payload,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')}
    for key,value in replacements.items(): template=template.replace(key,value)
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(template,encoding='utf-8')
    return {'html':str(path),'bytes':path.stat().st_size,'release':release,'math':math}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd',required=True)
    e=sub.add_parser('extract'); e.add_argument('pdf'); e.add_argument('--config'); e.add_argument('--out',required=True)
    v=sub.add_parser('validate'); v.add_argument('data'); v.add_argument('--release',action='store_true'); v.add_argument('--node',default='node'); v.add_argument('--pdf')
    b=sub.add_parser('build'); b.add_argument('data'); b.add_argument('--out',required=True); b.add_argument('--release',action='store_true'); b.add_argument('--node',default='node')
    args=p.parse_args()
    try:
        if args.cmd=='extract': write(args.out,extract(args.pdf,args.config)); print('已提取草稿；全部内容需要复核。')
        elif args.cmd=='validate':
            data=read(args.data); errors=validate(data,args.release)
            if args.pdf and sha(args.pdf)!=data['book']['sha256']: errors.append('源 PDF 指纹不一致')
            math=latex_check(data,args.node)
            if args.release and any(not f['valid'] for f in math): errors.append('KaTeX 校验失败')
            report={'ok':not errors,'errors':errors,'math':math,'pdf_identity_checked':bool(args.pdf)}
            print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if not errors else 2
        else: print(json.dumps(build(read(args.data),args.out,args.node,args.release),ensure_ascii=False,indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('失败: '+str(exc)); return 2

if __name__=='__main__': raise SystemExit(main())
