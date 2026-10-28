import tempfile
import unittest
import time
import smtplib
from pathlib import Path
import outbox
from worker import process
from mailer import build_email


CONFIG={'host':'smtpdm.aliyun.com','port':465,'username':'sender@example.com','password':'TEST-ONLY','sender':'sender@example.com','recipient':'support@example.com'}


class FakeSMTP:
    sent=[]
    def __init__(self,*args,**kwargs):pass
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def login(self,*args):pass
    def send_message(self,message,**kwargs):
        type(self).sent.append((message,kwargs))
        return {}


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        outbox.STATE=Path(self.temp.name)
        FakeSMTP.sent=[]
    def tearDown(self):self.temp.cleanup()
    def enqueue(self,key='request',student='student',ip='ip'):
        message=build_email('SP-TEST-0001',category='login',name='Example',student_id='TEST0001',contact_email='student@example.com')
        return outbox.enqueue(message,key,'owner',student,ip,'SP-TEST-0001')
    def test_dedup_and_receipt_owner(self):
        first=self.enqueue();second=self.enqueue()
        self.assertEqual(first['token'],second['token'])
        self.assertIsNone(outbox.status(first['token'],'different-owner'))
        self.assertEqual(outbox.status(first['token'],'owner')['status'],'queued')
    def test_envelope_and_cleanup(self):
        item=self.enqueue();job=outbox.claim();process(job,CONFIG,FakeSMTP)
        self.assertEqual(FakeSMTP.sent[0][1]['to_addrs'],['support@example.com','student@example.com'])
        self.assertEqual(str(FakeSMTP.sent[0][0]['To']),'support@example.com')
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'accepted')
        self.assertFalse(outbox.payload_path(item['token']).exists())
    def test_unknown_not_retried(self):
        class Uncertain(FakeSMTP):
            def send_message(self,*args,**kwargs):raise OSError('synthetic connection loss')
        item=self.enqueue();process(outbox.claim(),CONFIG,Uncertain)
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'unknown')
        self.assertIsNone(outbox.claim())
        self.assertFalse(outbox.payload_path(item['token']).exists())
    def test_partial_not_retried(self):
        class Partial(FakeSMTP):
            def send_message(self,*args,**kwargs):return {'student@example.com':(550,b'rejected')}
        item=self.enqueue();process(outbox.claim(),CONFIG,Partial)
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'partial')
        self.assertIsNone(outbox.claim())
    def test_retry_and_auth_failure(self):
        class Offline(FakeSMTP):
            def __init__(self,*args,**kwargs):raise OSError('synthetic unavailable')
        item=self.enqueue();process(outbox.claim(),CONFIG,Offline)
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'retry')
        class AuthFailure(FakeSMTP):
            def login(self,*args):raise smtplib.SMTPAuthenticationError(535,b'denied')
        with outbox.database() as db:db.execute('UPDATE jobs SET next_try=0')
        process(outbox.claim(),CONFIG,AuthFailure)
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'failed')
    def test_restart_recovery_and_ttl(self):
        item=self.enqueue();outbox.claim();outbox.recover_and_cleanup()
        self.assertEqual(outbox.status(item['token'],'owner')['status'],'unknown')
        self.assertFalse(outbox.payload_path(item['token']).exists())
        second=self.enqueue('request2')
        with outbox.database() as db:db.execute('UPDATE jobs SET created=? WHERE token=?',(time.time()-86401,second['token']))
        outbox.cleanup()
        self.assertEqual(outbox.status(second['token'],'owner')['status'],'expired')
        self.assertFalse(outbox.payload_path(second['token']).exists())
    def test_student_limit(self):
        for i in range(3):self.enqueue('request'+str(i))
        with self.assertRaises(ValueError):self.enqueue('request4')


if __name__=='__main__':unittest.main(verbosity=2)
