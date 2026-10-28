import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
fixture=json.loads(Path('/root/sit-lookup-test.json').read_text())
def call(payload, public=False, origin='https://sit.samzhao.cloud'):
    endpoint=('https://sit.samzhao.cloud' if public else 'http://127.0.0.1:8765')+'/api/account-lookup'
    headers={'Content-Type':'application/json','X-Real-IP':'198.18.0.42'}
    if origin: headers['Origin']=origin
    req=Request(endpoint,data=json.dumps(payload).encode(),headers=headers)
    try:
        with urlopen(req,timeout=10) as r: return r.status,json.loads(r.read()),r.headers
    except HTTPError as e: return e.code,json.loads(e.read()),e.headers
payload={k:fixture[k] for k in ('school','student_id','surname')}
code,result,headers=call(payload,public=True)
assert code==200 and result=={'sit_id':fixture['sit_id']},'Exact match failed'
assert 'no-store' in headers['Cache-Control']
wrong={**payload,'surname':'\u6d4b\u8bd5'}
assert call(wrong)[0]==404,'Wrong surname revealed a record'
unknown={**payload,'student_id':'000000000000'}
assert call(unknown)[1]==call(wrong)[1],'Failure reveals whether ID exists'
assert call(payload,origin=None)[0]==403
assert call({**payload,'student_id':'1 OR 1=1'})[0]==400
assert call({**payload,'surname':''})[0]==400
assert call({**payload,'surname':'\u5f20\u4e09\u4e30'})[0]==400
fake={'school':'hue','student_id':'999999999999','surname':'\u6d4b'}
for i in range(6): assert call(fake)[0]==404
assert call(fake)[0]==429,'Per-student throttle missing'
print('PASS: exact match returns only SIT ID; wrong surname/unknown ID share a failure; malformed input and foreign-origin requests rejected; persistent student throttle works.')
with urlopen('https://sit.samzhao.cloud/accounts_info.html') as r:
    page=r.read().decode('utf-8-sig')
    assert r.status==200
    assert 'no-store' in r.headers['Cache-Control']
    assert 'noindex' in r.headers['X-Robots-Tag']
    assert "frame-ancestors 'none'" in r.headers['Content-Security-Policy']
    assert fixture['student_id'] not in page and fixture['sit_id'] not in page
    assert 'const DATA' not in page and 'exportCsv' not in page
for path in ['/','/tools/','/tools/pswd/','/js/account-lookup.js','/css/portal.css']:
    with urlopen('https://sit.samzhao.cloud'+path) as r: assert r.status==200
print('PASS: public form contains no embedded student data; privacy headers and portal/tool assets verified over HTTPS.')
