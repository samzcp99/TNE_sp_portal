from urllib.request import urlopen
from html.parser import HTMLParser
class Page(HTMLParser):
 def __init__(self):super().__init__();self.nav=False;self.links=[];self.inputs=[];self.text=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='nav' and a.get('aria-label')=='\u4e3b\u5bfc\u822a':self.nav=True
  if self.nav and tag=='a':self.links.append(a)
  if tag=='input':self.inputs.append(a)
 def handle_endtag(self,tag):
  if tag=='nav':self.nav=False
for path in ['/','/tools/','/account/','/about/','/tools/pswd/']:
 with urlopen('https://47.95.144.1'+path,timeout=15) as r:
  html=r.read().decode('utf-8-sig');assert r.status==200;p=Page();p.feed(html)
  assert {a.get('href') for a in p.links}=={'/','/tools/','/account/','/about/'},path
  assert len([a for a in p.links if 'aria-current' in a])==1,path
  assert 'SP<span' not in html and 'brand-mark' not in html,path
  assert '\u5b66\u4e60\u5c0f\u7ad9' in html,path
  if path=='/account/':
   student=next(a for a in p.inputs if a.get('name')=='student_id');assert student['inputmode']=='numeric' and student['enterkeyhint']=='next'
   assert len([a for a in p.inputs if a.get('type')!='hidden'])==2
  print('PASS',path,'navigation, neutral word brand, HTTPS')
with urlopen('https://47.95.144.1/css/portal.css') as r:
 css=r.read().decode('utf-8-sig');assert css.count('{')==css.count('}')
 assert '#6b4834' in css and '#3730a3' not in css and '#0e3944' not in css
 assert 'grid-template-columns:repeat(4' in css and 'min-height:54px' in css and 'font-size:16px' in css
print('PASS coffee/oat theme, mobile navigation, larger inputs and touch targets')
