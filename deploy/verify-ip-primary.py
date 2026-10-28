import re
from urllib.request import urlopen,Request
from urllib.error import HTTPError
base='https://47.95.144.1'
for path in ['/','/tools/','/account/','/about/','/tools/pswd/','/tools/pswd/sitemap-0.xml','/tools/pswd/sitemap-index.xml','/tools/pswd/robots.txt']:
    with urlopen(base+path,timeout=15) as r:
        text=r.read().decode('utf-8-sig')
        assert r.status==200 and r.url==base+path,(path,r.status,r.url)
        assert not re.search(r'sam\s*zhao|samzhao\.cloud',text,re.I),path
        print('PASS',path,'direct IP HTTPS; no personal name or domain in response')
with urlopen('https://sit.samzhao.cloud/tools/',timeout=15) as r:
    assert r.url==base+'/tools/' and r.status==200
print('PASS old domain redirects to IP')
try:
    urlopen(Request(base+'/api/account-lookup',data=b'{}',headers={'Content-Type':'application/json','Origin':base}),timeout=15)
    raise AssertionError('Lookup must remain paused')
except HTTPError as e: assert e.code==503
print('PASS lookup remains paused')
