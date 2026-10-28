from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json
request=Request('https://sp.samzhao.cloud/api/account-lookup',data=json.dumps({'school':'hue','student_id':'000000000001','surname':'\u6d4b'}).encode(),headers={'Content-Type':'application/json','Origin':'https://sp.samzhao.cloud'})
try:
    urlopen(request,timeout=15)
    raise AssertionError('Synthetic ID should not match')
except HTTPError as error:
    assert error.code==404,error.code
print('PASS new-domain account API origin and generic mismatch response')
