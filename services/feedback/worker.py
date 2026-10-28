"""Send only fixed support recipient + validated student Cc; never Helpdesk."""
import json
import os
import smtplib
import ssl
import time
from email import policy
from email.parser import BytesParser
from pathlib import Path
import outbox
from mailer import delivery_addresses


def process(job,config,smtp_factory=smtplib.SMTP_SSL):
    transmitting=False
    response_received=False
    try:
        message=BytesParser(policy=policy.default).parsebytes(outbox.payload_path(job['token']).read_bytes())
        message.replace_header('To',config['recipient'])
        message.replace_header('From','Student Support <'+config['sender']+'>')
        recipients=delivery_addresses(message)
        with smtp_factory(config['host'],int(config['port']),timeout=20,context=ssl.create_default_context()) as smtp:
            smtp.login(config['username'],config['password'])
            transmitting=True
            refused=smtp.send_message(message,from_addr=config['sender'],to_addrs=recipients)
            response_received=True
            outbox.finish(job['token'],'partial' if refused else 'accepted')
    except smtplib.SMTPAuthenticationError:
        outbox.finish(job['token'],'failed')
    except smtplib.SMTPResponseException as exception:
        outbox.finish(job['token'],'retry' if 400<=exception.smtp_code<500 else 'failed')
    except smtplib.SMTPRecipientsRefused as exception:
        codes=[value[0] for value in exception.recipients.values()]
        outbox.finish(job['token'],'retry' if codes and all(400<=code<500 for code in codes) else 'failed')
    except (OSError,smtplib.SMTPException):
        if not response_received:
            outbox.finish(job['token'],'unknown' if transmitting else 'retry')
    except Exception:
        if not response_received:
            outbox.finish(job['token'],'unknown' if transmitting else 'failed')


if __name__=='__main__':
    credential_directory=os.environ.get('CREDENTIALS_DIRECTORY')
    default_config=str(Path(credential_directory)/'smtp-config') if credential_directory else '/etc/student-feedback/config.json'
    config=json.loads(Path(os.environ.get('SUPPORT_SMTP_CONFIG',default_config)).read_text())
    if config['sender']!='student@sp.samzhao.cloud' or config['host']!='smtpdm.aliyun.com' or int(config['port'])!=465:
        raise SystemExit('Unexpected sender or SMTP endpoint; check private configuration.')
    outbox.recover_and_cleanup()
    last_cleanup=0
    while True:
        if time.time()-last_cleanup>300:
            outbox.cleanup()
            last_cleanup=time.time()
        job=outbox.claim()
        if job:
            process(job,config)
        else:
            time.sleep(2)
