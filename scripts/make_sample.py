"""Create an original tiny PDF fixture; never auto-approve a user's textbook."""
import sys
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from mindmap import extract,write

ROOT=Path(__file__).resolve().parents[1]
def main():
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
    path=ROOT/'examples/sample.pdf'
    c=canvas.Canvas(str(path),pagesize=(595,842))
    c.setTitle('原创数学教学测试材料')
    pages=[['第一章 集合与函数概念','1.1 集合','集合可以描述研究对象。',r'集合并集示例：$A \cup B$',
            '1.2 函数','函数描述变量之间的对应关系。',r'一次函数示例：$f(x)=2x+1$'],
           ['第二章 二次函数','2.1 二次函数的图象',r'二次函数示例：$f(x)=x^2$',
            '本文件为原创简化测试夹具，不是教材原文。']]
    for lines in pages:
        c.setFont('STSong-Light',16)
        for i,line in enumerate(lines):c.drawString(45,790-i*48,line)
        c.showPage()
    c.save()
    data=extract(path,ROOT/'examples/config.json')
    write(ROOT/'examples/sample.draft.json',data)
    # These signatures apply only to this explicitly authored fixture.
    for p in data['pages']:
        p.update(review='approved',reviewer='原创夹具编写者',note='与 make_sample.py 中原文核对；非真实教材审核')
    for n in data['nodes']:n['review']='approved'
    for f in data['formulas']:
        f.update(review='approved',reviewer='原创夹具编写者',note='与生成源核对；语法测试另行执行')
    groups=[{'id':'g1','title':'集合：语言与运算','kind':'topic','origin':'teacher','sources':[],
             'formula_ids':[],'review':'approved','rationale':'原创演示的教师复习分组，不对应教材标题'},
            {'id':'g2','title':'函数：对应关系与图象','kind':'topic','origin':'teacher','sources':[],
             'formula_ids':[],'review':'approved','rationale':'原创演示的跨章归类，不声称为高考真题规律'}]
    data['nodes']+=groups
    chosen=lambda text:next(n['id'] for n in data['nodes'] if text in n['title'])
    set_id=chosen('集合并集示例'); func_id=chosen('一次函数示例'); quad_id=chosen('二次函数示例')
    data['exam']={'node_id':'book','children':[{'node_id':'g1','children':[{'node_id':set_id,'children':[]}]},
      {'node_id':'g2','children':[{'node_id':func_id,'children':[]},{'node_id':quad_id,'children':[]}]}]}
    data['relations']=[{'from':func_id,'to':quad_id,'type':'contrast','review':'approved',
      'rationale':'对照一次与二次函数表达式及图象特征；教师设计的复习连接。'}]
    data['structure_review']={'textbook':'approved','exam':'approved','reviewer':'原创夹具编写者',
       'note':'原创简化层级已对照生成源；真实教材须重新审核'}
    write(ROOT/'examples/sample.reviewed.json',data)
    print('Original fixture and two review states created.')
if __name__=='__main__':main()
