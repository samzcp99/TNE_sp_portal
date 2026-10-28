import json,smtplib,ssl
from pathlib import Path
from mailer import build_email
config=json.loads(Path('/etc/student-feedback/config.json').read_text())
marker=Path('/etc/student-feedback/test-sent')
if marker.exists():
    print('Test already accepted by SMTP; no duplicate sent.')
    raise SystemExit(0)
message=build_email('SP-DEMO-001',category='contact_update',name='Example Student (TEST ONLY)',student_id='EXAMPLE0001',contact_email='student@example.com',mobile='+86 1XXXXXXXXXX',reason='The previous mobile number is no longer available. This is a delivery test; please do not forward to Helpdesk.')
message.replace_header('Subject','[TEST - NO ACTION REQUIRED] Student contact update - EXAMPLE0001')
try:
    with smtplib.SMTP_SSL(config['host'],config['port'],timeout=20,context=ssl.create_default_context()) as smtp:
        smtp.login(config['username'],config['password'])
        refused=smtp.send_message(message,from_addr=config['sender'],to_addrs=[config['recipient']])
        if refused:raise RuntimeError('Recipient rejected')
    marker.write_text('SMTP accepted one synthetic test message. Inbox delivery not independently verified.\n')
    print('PASS: SMTP authenticated and accepted one synthetic test message for the configured recipient. Inbox delivery still needs confirmation.')
except smtplib.SMTPAuthenticationError as error:
    print('SMTP authentication failed; response code:',error.smtp_code)
    raise SystemExit(2)
except smtplib.SMTPResponseException as error:
    print('SMTP request rejected; response code:',error.smtp_code)
    print(error.smtp_error.decode(errors='replace')[:300])
    raise SystemExit(3)
