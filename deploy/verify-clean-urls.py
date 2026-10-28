from urllib.request import urlopen,build_opener,HTTPRedirectHandler
from urllib.error import HTTPError
from html.parser import HTMLParser
class NoRedirect(HTTPRedirectHandler):
 def redirect_request(self,*args):return None
client=build_opener(NoRedirect())
base='https://sp.samzhao.cloud'
redirects={'/accounts_info.html':'/account/','/about.html':'/about/','/index.html':'/','/account/index.html':'/account/','/about/index.html':'/about/','/tools/index.html':'/tools/','/support/index.html':'/support/','/tools/pswd/index.html':'/tools/pswd/','/snake.html':'/snake/','/mahjong/majong.html':'/mahjong/'}
for old,new in redirects.items():
 try:client.open(base+old+'?check=clean',timeout=15);raise AssertionError('No redirect: '+old)
 except HTTPError as error:
  assert error.code==301,(old,error.code)
  assert error.headers['Location']==base+new+'?check=clean',(old,error.headers['Location'])
 with urlopen(base+old,timeout=15) as response:assert response.status==200 and response.url==base+new
 print('PASS legacy redirect',old,'->',new)
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,tag,attrs):
  for key,value in attrs:
   if key=='href' and value and value.startswith('/'):self.links.append(value)
for path in ['/','/account/','/about/','/tools/','/support/','/tools/pswd/']:
 with urlopen(base+path,timeout=15) as response:
  assert response.status==200
  page=Links();page.feed(response.read().decode('utf-8-sig'))
  assert not any('.html' in link for link in page.links),(path,page.links)
  if path=='/account/':
   assert 'no-store' in response.headers['Cache-Control']
   assert 'noindex' in response.headers['X-Robots-Tag']
   assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
 print('PASS clean route and links',path)
with urlopen('https://47.95.144.1/account/',timeout=15) as response:assert response.status==200
print('PASS direct IP clean route; account privacy headers retained')
