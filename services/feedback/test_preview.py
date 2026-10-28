"""Synthetic, isolated tests. Never send email or use the student dataset."""
import io,os,tempfile,unittest
import uuid
from unittest.mock import patch
from PIL import Image,PngImagePlugin
state=tempfile.TemporaryDirectory()
os.environ['SUPPORT_STATE']=state.name
from app import app,database,clean_image
from mailer import build_email,delivery_addresses
ORIGIN='https://sp.samzhao.cloud'
class SupportTests(unittest.TestCase):
 def setUp(self):
  self.client=app.test_client()
  self.headers={'Origin':ORIGIN,'X-Real-IP':'198.18.0.'+str(list(type(self).__dict__).index(self._testMethodName)+10)}
 def challenge(self,client=None):
  with patch('app.secrets.choice',return_value='B'):
   response=(client or self.client).get('/api/support/captcha',base_url=ORIGIN,headers=self.headers)
  self.assertEqual(response.status_code,200)
  data=response.get_json();self.assertNotIn('answer',data);self.assertTrue(data['image'].startswith('data:image/png;base64,'))
  return data['id']
 def payload(self,identifier):
  return {'captcha_id':identifier,'captcha':'bbbbb','category':'contact_update','reason':'old_phone','name':'Example Student','domestic_id':'1234567890','student_id':'TEST0001','contact_email':'student@example.com','contact_email_confirm':'student@example.com','phone_country':'CN','mobile':'13800000000','occurred_at':'2026-10-28T12:00','timezone':'Asia/Shanghai','consent':'yes'}
 def submit(self,data,client=None,headers=None):
  return (client or self.client).post('/api/support/preview',data=data,base_url=ORIGIN,headers=headers or self.headers)
 def test_success_and_replay(self):
  identifier=self.challenge();data=self.payload(identifier);response=self.submit(data)
  self.assertEqual(response.status_code,200);result=response.get_json();self.assertEqual(result['mode'],'preview');self.assertIn('previous mobile number',result['body']);self.assertNotIn('sam.zhao',str(result));self.assertTrue(result['reference'].startswith('PREVIEW-'))
  self.assertEqual(self.submit(data).status_code,400)
  self.assertEqual(result['cc'],'student@example.com')
 def test_student_cc_envelope(self):
  message=build_email('PREVIEW-TEST',category='login',name='Example',student_id='TEST0001',contact_email='student@example.com')
  self.assertEqual(str(message['Cc']),'student@example.com')
  self.assertEqual(str(message['Reply-To']),'student@example.com')
  self.assertIn('student@example.com',delivery_addresses(message))
  message.replace_header('To','student@example.com')
  self.assertEqual(delivery_addresses(message),['student@example.com'])
  test=build_email('PREVIEW-TEST',category='login',name='Example',student_id='TEST0001',contact_email='student@example.com',cc_student=False)
  self.assertIsNone(test['Cc'])
 def test_wrong_and_expired(self):
  identifier=self.challenge();data=self.payload(identifier);data['captcha']='WRONG';self.assertEqual(self.submit(data).status_code,400)
  identifier=self.challenge()
  with database() as db:db.execute('UPDATE challenges SET expires=0 WHERE id=?',(identifier,))
  self.assertEqual(self.submit(self.payload(identifier)).status_code,400)
 def test_session_binding_and_origin(self):
  identifier=self.challenge();other=app.test_client();self.challenge(other)
  self.assertEqual(self.submit(self.payload(identifier),client=other).status_code,400)
  self.assertEqual(self.submit(self.payload(identifier),headers={'Origin':'https://untrusted.example'}).status_code,403)
 def test_invalid_fields(self):
  data=self.payload(self.challenge());data['consent']='no';self.assertEqual(self.submit(data).status_code,400)
  data=self.payload(self.challenge());data['contact_email']='student@example.com\r\nBcc: other@example.com';self.assertEqual(self.submit(data).status_code,400)
 def test_contact_validation_at_api(self):
  for field,value in [('mobile','1660000000'),('contact_email_confirm','different@example.com')]:
   data=self.payload(self.challenge());data[field]=value
   self.assertEqual(self.submit(data).status_code,400)
  data=self.payload(self.challenge());result=self.submit(data)
  self.assertEqual(result.status_code,200)
  self.assertIn('Mobile: +8613800000000',result.get_json()['body'])
 def test_live_submission_deduplicates_and_binds_receipt(self):
  app.config['DELIVERY_ENABLED']=True
  try:
   data=self.payload(self.challenge());data['submission_id']=str(uuid.uuid4())
   response=self.client.post('/api/support/submit',data=data,base_url=ORIGIN,headers=self.headers)
   self.assertEqual(response.status_code,202)
   first=response.get_json();self.assertEqual(first['mode'],'live');self.assertEqual(first['status'],'queued')
   duplicate=self.client.post('/api/support/submit',data=data,base_url=ORIGIN,headers=self.headers)
   self.assertEqual(duplicate.status_code,202);self.assertEqual(duplicate.get_json()['token'],first['token'])
   status=self.client.get('/api/support/status/'+first['token'],base_url=ORIGIN)
   self.assertEqual(status.status_code,200)
   other=app.test_client()
   self.assertEqual(other.get('/api/support/status/'+first['token'],base_url=ORIGIN).status_code,404)
  finally:app.config['DELIVERY_ENABLED']=False
 def test_core_details_required_for_every_category(self):
  for index,category in enumerate(['contact_update','mfa','login','password','learning','other']):
   self.headers['X-Real-IP']='198.18.1.'+str(index+10)
   for field in ['name','student_id','mobile']:
    data=self.payload(self.challenge());data.update(category=category,description='Synthetic issue description')
    data[field]='   '
    self.assertEqual(self.submit(data).status_code,400,(category,field))
 def test_image_processing(self):
  image=Image.new('RGB',(100,80),'white');output=io.BytesIO();metadata=PngImagePlugin.PngInfo();metadata.add_text('SensitiveMetadata','REMOVE ME');image.save(output,format='PNG',pnginfo=metadata)
  from werkzeug.datastructures import FileStorage
  content,_=clean_image(FileStorage(stream=io.BytesIO(output.getvalue()),filename='test.png'))
  with Image.open(io.BytesIO(content)) as clean:self.assertNotIn('SensitiveMetadata',clean.info)
  data=self.payload(self.challenge());data['screenshots']=(io.BytesIO(output.getvalue()),'test.png');result=self.submit(data);self.assertEqual(result.status_code,200);self.assertEqual(len(result.get_json()['attachments']),1)
  data=self.payload(self.challenge());data['screenshots']=(io.BytesIO(b'not an image'),'fake.png');self.assertEqual(self.submit(data).status_code,400)
 def test_throttle(self):
  headers={**self.headers,'X-Real-IP':'198.18.0.240'}
  for i in range(30):self.assertEqual(self.client.get('/api/support/captcha',base_url=ORIGIN,headers=headers).status_code,200)
  self.assertEqual(self.client.get('/api/support/captcha',base_url=ORIGIN,headers=headers).status_code,429)
if __name__=='__main__':
 try:unittest.main(verbosity=2)
 finally:state.cleanup()
