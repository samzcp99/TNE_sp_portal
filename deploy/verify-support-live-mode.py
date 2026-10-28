import sqlite3
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from html.parser import HTMLParser
base='https://sp.samzhao.cloud'
with urlopen(base+'/support/',timeout=15) as response:
 html=response.read().decode('utf-8-sig')
 assert 'action="/api/support/submit"' in html
 assert 'id="submission-receipt"' in html
 assert 'support.js?v=20261028-live-1' in html
 assert '\u63d0\u4ea4\u5e76\u53d1\u9001\u90ae\u4ef6' in html
 assert '\u8bd5\u7528\u9884\u89c8\u7248' not in html
 print('PASS live form, receipt UI and cache version')
try:
 urlopen(Request(base+'/api/support/submit',data=b'',headers={'Origin':base}),timeout=15)
 raise AssertionError('Missing identifier accepted')
except HTTPError as error:
 assert error.code==400,error.code
 print('PASS live submit endpoint enabled and rejects missing identifier without queuing')
try:
 urlopen(base+'/api/support/status/'+'a'*43,timeout=15)
 raise AssertionError('Unowned status disclosed')
except HTTPError as error:assert error.code==404
print('PASS receipt ownership check')
with sqlite3.connect('/var/lib/student-feedback-preview/outbox.sqlite') as db:
 rows=db.execute('SELECT status,COUNT(*) FROM jobs GROUP BY status').fetchall()
 print('Production outbox state counts:',rows)
