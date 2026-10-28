import http.cookiejar,json,urllib.request,urllib.error
base='https://sp.samzhao.cloud'
for path in ['/','/support/','/css/support.css','/js/support.js','/accounts_info.html','/tools/pswd/']:
 with urllib.request.urlopen(base+path,timeout=15) as r:
  text=r.read().decode('utf-8-sig');assert r.status==200
  if path=='/':assert 'href="/support/"' in text
  if path=='/support/':assert 'id="support-form"' in text and 'no-store' in r.headers['Cache-Control'] and 'frame-ancestors' in r.headers['Content-Security-Policy']
  print('PASS HTTPS',path)
jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
with client.open(base+'/api/support/captcha',timeout=15) as r:
 data=json.load(r);assert data['expires_in']==120;assert 'answer' not in data;assert data['image'].startswith('data:image/png;base64,')
 assert 'no-store' in r.headers['Cache-Control']
assert any(cookie.secure and cookie.name=='support_session' for cookie in jar)
body=urllib.parse.urlencode({'captcha_id':data['id'],'captcha':'WRONG','category':'login'}).encode()
try:client.open(urllib.request.Request(base+'/api/support/preview',data=body,headers={'Origin':base}),timeout=15);raise AssertionError('Invalid CAPTCHA accepted')
except urllib.error.HTTPError as e:assert e.code==400
print('PASS live CAPTCHA JSON, secure session cookie, wrong answer rejection')
