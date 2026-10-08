import copy
import os
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import mindmap as m

class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.data=m.read(m.ROOT/'examples/sample.reviewed.json')
        self.node=os.environ.get('MINDMAP_NODE','node')
        self.temp_root=Path.cwd()/'work'/'mindmap-tests'
        self.temp_root.mkdir(parents=True,exist_ok=True)
    def test_real_pdf_to_draft(self):
        d=m.extract(m.ROOT/'examples/sample.pdf',m.ROOT/'examples/config.json')
        self.assertEqual(d['book']['page_count'],2)
        self.assertEqual(d['book']['sha256'],m.sha(m.ROOT/'examples/sample.pdf'))
        self.assertEqual(len(d['formulas']),3)
        self.assertTrue(any(n['title']=='1.1 集合' for n in d['nodes']))
        self.assertFalse(m.validate(d))
        self.assertTrue(m.validate(d,True))
    def test_reviewed_passes(self):
        self.assertEqual(m.validate(self.data,True),[])
        self.assertTrue(all(f['valid'] for f in m.latex_check(self.data,self.node)))
    def test_scan_and_ordinary_math_are_not_auto_approved(self):
        self.data['formulas'][0]['latex']=None
        self.assertFalse(m.latex_check(self.data,self.node)[0]['valid'])
        self.assertTrue(any('未转录' in e for e in m.validate(self.data,True)))
    def test_unsigned_formula_blocked(self):
        self.data['formulas'][0]['reviewer']=''
        self.assertTrue(any('公式未签署' in e for e in m.validate(self.data,True)))
    def test_source_mismatch_and_page_coverage(self):
        self.data['nodes'][1]['sources'][0]['quote']='伪造原文'
        self.data['pages'].pop()
        errors=m.validate(self.data)
        self.assertTrue(any('不一致' in e for e in errors))
        self.assertTrue(any('覆盖' in e for e in errors))
    def test_tree_cycle_and_missing_formula(self):
        self.data['exam']['children'][0]['children'].append({'node_id':'book','children':[]})
        self.data['nodes'][0]['formula_ids']=['nonexistent']
        errors=m.validate(self.data)
        self.assertTrue(any('循环' in e for e in errors))
        self.assertTrue(any('公式引用' in e for e in errors))
    def test_teacher_not_allowed_in_strict_tree(self):
        self.data['textbook']['children'].append({'node_id':'g1','children':[]})
        self.assertTrue(any('教师补充' in e for e in m.validate(self.data)))
    def test_order_reversal(self):
        self.data['textbook']['children'].reverse()
        self.assertTrue(any('顺序' in e for e in m.validate(self.data)))
    def test_bad_latex_release_rejected(self):
        self.data['formulas'][0]['latex']=r'\frac{'
        result=m.latex_check(self.data,self.node)
        self.assertFalse(result[0]['valid'])
        with tempfile.TemporaryDirectory(dir=self.temp_root) as t:
            with self.assertRaisesRegex(ValueError,'KaTeX'):m.build(self.data,Path(t)/'bad.html',self.node,True)
    def test_empty_page_release_rejected(self):
        self.data['pages'][0]['text']=''
        self.assertTrue(any('空白/扫描页' in e for e in m.validate(self.data,True)))
    def test_html_is_self_contained_and_payload_escaped(self):
        self.data['nodes'][-1]['title']='</script><img src=x onerror=alert(1)>'
        with tempfile.TemporaryDirectory(dir=self.temp_root) as t:
            out=Path(t)/'map.html';m.build(self.data,out,self.node,True)
            text=out.read_text(encoding='utf-8')
            self.assertNotIn('</script><img src=x',text)
            self.assertNotIn('src="https://',text)
            self.assertNotIn('url(fonts/',text)
            self.assertIn('data:font/woff2;base64,',text)
            self.assertIn("connect-src 'none'",text)

if __name__=='__main__':unittest.main()
