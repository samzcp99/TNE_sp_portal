from urllib.request import urlopen
from html.parser import HTMLParser
class Form(HTMLParser):
    def __init__(self):super().__init__();self.inputs=[];self.selects=[]
    def handle_starttag(self,tag,attrs):
        if tag=='input':self.inputs.append(dict(attrs))
        if tag=='select':self.selects.append(dict(attrs))
for path in ['/','/tools/','/account/','/about/','/tools/pswd/']:
    with urlopen('https://47.95.144.1'+path,timeout=15) as r:
        text=r.read().decode('utf-8-sig');assert r.status==200
        assert '\u6e56\u5317\u7b2c\u4e8c\u5e08\u8303\u5b66\u9662' not in text
        if path=='/account/':
            p=Form();p.feed(text)
            assert len([x for x in p.inputs if x.get('type')!='hidden'])==2
            assert not p.selects
            assert any(x.get('name')=='school' and x.get('value')=='hue' for x in p.inputs)
        if path=='/tools/pswd/':assert '/css/pswd-theme.css' in text
        print('PASS',path)
with urlopen('https://47.95.144.1/css/portal.css') as r:
    css=r.read().decode('utf-8-sig');assert '#3730a3' in css and '#6ee7b7' in css
    assert '#0e3944' not in css and '#ea6321' not in css
print('PASS neutral school copy, two visible query fields, indigo and mint palette')
