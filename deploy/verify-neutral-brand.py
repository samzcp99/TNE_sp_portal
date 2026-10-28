from html.parser import HTMLParser
from urllib.request import urlopen
import re
class Page(HTMLParser):
    def __init__(self): super().__init__();self.parts=[];self.links=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1
        for key,value in attrs:
            if tag=='a' and key=='href':self.links.append(value)
            if key in ('content','aria-label','title','alt') and value:self.parts.append(value)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
for path in ['/','/tools/','/accounts_info.html','/about.html','/tools/pswd/']:
    with urlopen('https://47.95.144.1'+path,timeout=15) as r:
        p=Page();p.feed(r.read().decode('utf-8-sig'))
        assert r.status==200
        assert not re.search(r'\bSIT\b|MySIT|Southern Institute|sam\s*zhao',' '.join(p.parts),re.I),path
        if path=='/':assert 'https://my.sit.ac.nz' in p.links and 'https://reset.sit.ac.nz' in p.links and 'https://blackboard.sit.ac.nz' in p.links
        print('PASS',path,'neutral public copy; HTTPS OK')
print('PASS original official destination links retained')
