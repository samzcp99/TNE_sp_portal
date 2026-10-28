"""Synthetic, isolated tests. Never send email or use the student dataset."""
import io,os,tempfile,unittest
from unittest.mock import patch
from PIL import Image,PngImagePlugin
state=tempfile.TemporaryDirectory()
os.environ['SUPPORT_STATE']=state.name
from app import app,database,clean_image
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
  return {'captcha_id':identifier,'captcha':'bbbbb','category':'contact_update','reason':'old_phone','name':'Example Student','domestic_id':'1234567890','student_id':'TEST0001','contact_email':'student@example.com','mobile':'+86 12345678901','occurred_at':'2026-10-28T12:00','timezone':'Asia/Shanghai','consent':'yes'}
 def submit(self,data,client=None,headers=None):
  return (client or self.client).post('/api/support/preview',data=data,base_url=ORIGIN,headers=headers or self.headers)
 def test_success_and_replay(self):
  identifier=self.challenge();data=self.payload(identifier);response=self.submit(data)
  self.assertEqual(response.status_code,200);result=response.get_json();self.assertEqual(result['mode'],'preview');self.assertIn('previous mobile number',result['body']);self.assertNotIn('sam.zhao',str(result));self.assertTrue(result['reference'].startswith('PREVIEW-'))
  self.assertEqual(self.submit(data).status_code,400)
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
