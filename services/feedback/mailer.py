"""Build short, forwardable support emails. This module does not send mail."""
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
import re
import os

SENDER = 'student@sp.samzhao.cloud'
RECIPIENT = os.environ.get('SUPPORT_RECIPIENT', 'support-recipient@example.invalid')

def build_email(ticket, *, category, name, student_id, contact_email, mobile='', reason='', error='', tried='', domestic_id='', occurred_at='', attachments=()):
    for value in (ticket, category, name, student_id, contact_email, mobile):
        if '\r' in value or '\n' in value:
            raise ValueError('Unexpected newline in a single-line field')
    if not re.fullmatch(r'[A-Za-z0-9._+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', contact_email):
        raise ValueError('Invalid contact email')
    if not re.fullmatch(r'[A-Za-z0-9-]{1,32}', ticket):
        raise ValueError('Invalid ticket reference')
    subjects = {'contact_update':'Student contact update', 'mfa':'MFA access issue', 'login':'Unable to sign in', 'password':'Password reset issue', 'learning':'Learning platform issue', 'other':'Student account support'}
    if category not in subjects:
        raise ValueError('Unknown category')
    title = subjects[category]
    request = ('Please update the contact details for the student below.' if category == 'contact_update' else
               'Please help restore MFA access for the student below.' if category == 'mfa' else
               'Please assist the student below with their account issue.')
    lines = ['Hi team,', '', request, '', f'Student ID: {student_id}', f'Name: {name}', f'Email: {contact_email}']
    if mobile: lines.append(f'Mobile: {mobile}')
    if domestic_id: lines.append(f'Domestic student ID: {domestic_id}')
    if occurred_at: lines.append(f'Occurred at: {occurred_at}')
    if reason: lines.extend(['', ('Reason: ' if category in ('contact_update','mfa') else 'Issue: ') + reason.strip()])
    if error: lines.append('Error message: ' + error.strip())
    if tried: lines.append('Already tried: ' + tried.strip())
    if attachments: lines.extend(['', f'Screenshots attached: {len(attachments)}'])
    lines.extend(['', 'Thank you.', '', f'Reference: {ticket}', 'Student-submitted request via the independent Study Guide.'])
    message = EmailMessage()
    message['From'] = f'Student Support <{SENDER}>'
    message['To'] = RECIPIENT
    message['Reply-To'] = contact_email
    message['Subject'] = f'{title} - {student_id} [{ticket}]'
    message['Date'] = formatdate(localtime=False)
    message['Message-ID'] = make_msgid(domain='sp.samzhao.cloud')
    message.set_content('\n'.join(lines))
    if len(attachments) > 3:
        raise ValueError('Maximum three screenshots')
    for index, (content, subtype) in enumerate(attachments, 1):
        if subtype not in ('jpeg', 'png', 'webp'):
            raise ValueError('Only validated, re-encoded screenshot images are allowed')
        if len(content) > 3 * 1024 * 1024:
            raise ValueError('Screenshot exceeds limit')
        message.add_attachment(content, maintype='image', subtype=subtype, filename=f'screenshot-{index}.{subtype}')
    return message

if __name__ == '__main__':
    from pathlib import Path
    from email import policy
    from email.parser import BytesParser
    sample = build_email('SP-DEMO-001', category='contact_update', name='Example Student', student_id='EXAMPLE0001', contact_email='student@example.com', mobile='+86 1XXXXXXXXXX', reason='The previous mobile number is no longer available.')
    Path('/opt/student-feedback-contact-example.eml').write_bytes(sample.as_bytes(policy=policy.SMTP))
    parsed = BytesParser(policy=policy.default).parsebytes(sample.as_bytes())
    assert parsed['From'].addresses[0].addr_spec == SENDER
    assert parsed['To'].addresses[0].addr_spec == RECIPIENT
    assert parsed['Reply-To'].addresses[0].addr_spec == 'student@example.com'
    assert 'Student ID: EXAMPLE0001' in parsed.get_body().get_content()
    assert len(list(parsed.iter_attachments())) == 0
    print('PASS sample email headers/body. Sample generated only; no mail sent.')
