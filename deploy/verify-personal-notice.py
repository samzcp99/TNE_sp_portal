from urllib.request import urlopen,Request
from urllib.error import HTTPError
base='https://sit.samzhao.cloud'
for path in ['/','/tools/','/account/','/about/','/tools/pswd/']:
    with urlopen(base+path,timeout=15) as response:
        page=response.read().decode('utf-8-sig')
        assert response.status==200
        assert '\u975e\u5b98\u65b9' in page,path
        assert 'href="/about/"' in page,path
        assert 'SIT Southern Institute of Technology' not in page,path
        if path=='/account/':
            assert '<form' not in page and 'account-lookup.js' not in page
        print('PASS',path,'personal-site notice present')
try:
    urlopen(Request(base+'/api/account-lookup',data=b'{}',headers={'Content-Type':'application/json','Origin':base}),timeout=15)
    raise AssertionError('Lookup must be unavailable')
except HTTPError as e:
    assert e.code==503,e.code
    assert b'Student lookup is unavailable' in e.read()
print('PASS student lookup API is unavailable')
