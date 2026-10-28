import hashlib,hmac,json,os,tempfile,threading,importlib.util
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import Request,urlopen
from urllib.error import HTTPError
with tempfile.TemporaryDirectory() as temporary:
    data=Path(temporary);secret=b'synthetic-verification-key'
    data.joinpath('secret').write_bytes(secret)
    key=hmac.new(secret,'hue\x001234567890\x00\u6d4b'.encode(),hashlib.sha256)
    data.joinpath('records.json').write_text(json.dumps({key.hexdigest():'TEST-ONLY-ID'}))
    os.environ['LOOKUP_DATA']=temporary
    spec=importlib.util.spec_from_file_location('lookup','/opt/sit-account-lookup/server.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler);threading.Thread(target=server.serve_forever,daemon=True).start()
    def post(base,payload):
        request=Request(base+'/api/account-lookup',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Origin':'https://47.95.144.1','X-Real-IP':'198.18.0.49'})
        try:
            with urlopen(request,timeout=10) as r:return r.status,json.loads(r.read())
        except HTTPError as e:return e.code,json.loads(e.read())
    base='http://127.0.0.1:'+str(server.server_port);payload={'school':'hue','student_id':'1234567890','surname':'\u6d4b'}
    assert post(base,payload)==(200,{'sit_id':'TEST-ONLY-ID'})
    assert post(base,{**payload,'surname':'\u5f20'})[0]==404
    for i in range(4):assert post(base,payload)[0]==200
    assert post(base,payload)[0]==429
    server.shutdown();module.DB.close()
print('PASS synthetic exact match, wrong surname, and persistent rate limiting')
for path in ['/accounts_info.html','/tools/','/about.html','/js/account-lookup.js']:
    with urlopen('https://47.95.144.1'+path,timeout=15) as r:
        text=r.read().decode('utf-8-sig');assert r.status==200
        if path=='/accounts_info.html':assert 'id="lookup-form"' in text and 'no-store' in r.headers['Cache-Control'] and 'const DATA' not in text
print('PASS public HTTPS form, script and privacy headers')
assert post('https://47.95.144.1',{'school':'hue','student_id':'000000000000','surname':'\u6d4b'})[0]==404
print('PASS public IP API accepts requests and returns generic mismatch for synthetic unknown ID')
