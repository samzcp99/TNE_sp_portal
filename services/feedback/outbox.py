"""Private durable outbox. Payloads expire after 24h; receipts after 7 days."""
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

STATE = Path(os.environ.get('SUPPORT_STATE','/var/lib/student-feedback-preview'))


@contextmanager
def database():
    STATE.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(STATE/'outbox.sqlite',timeout=5)
    db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS jobs (token TEXT PRIMARY KEY, request_key TEXT UNIQUE, owner TEXT, student TEXT, ip TEXT, reference TEXT, status TEXT, created REAL, updated REAL, next_try REAL, attempts INTEGER DEFAULT 0)')
    try:
        with db:
            yield db
    finally:
        db.close()


def payload_path(token):
    return STATE/'outbox'/(token+'.eml')


def receipt(row):
    return {'mode':'live','token':row['token'],'reference':row['reference'],'status':row['status']}


def find(request_key,owner):
    with database() as db:
        row=db.execute('SELECT * FROM jobs WHERE request_key=? AND owner=?',(request_key,owner)).fetchone()
    return receipt(row) if row else None


def status(token,owner):
    with database() as db:
        row=db.execute('SELECT * FROM jobs WHERE token=? AND owner=?',(token,owner)).fetchone()
    return receipt(row) if row else None


def enqueue(message,request_key,owner,student,ip,reference):
    now=time.time()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT * FROM jobs WHERE request_key=? AND owner=?',(request_key,owner)).fetchone()
        if existing:
            return receipt(existing)
        checks=[('created>?',(now-86400,),50),
                ('student=? AND created>?',(student,now-900),3),
                ('ip=? AND created>?',(ip,now-900),5)]
        for condition,parameters,limit in checks:
            if db.execute('SELECT COUNT(*) FROM jobs WHERE '+condition,parameters).fetchone()[0]>=limit:
                raise ValueError('提交次数已达到上限，请稍后再试或联系项目老师。')
        token=secrets.token_urlsafe(32)
        folder=STATE/'outbox'
        folder.mkdir(mode=0o700,exist_ok=True)
        path=payload_path(token)
        from email import policy
        payload=message.as_bytes(policy=policy.SMTP)
        if len(payload)>9*1024*1024:
            raise ValueError('附件总量过大，请减少截图或裁剪后再提交。')
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,0)',(token,request_key,owner,student,ip,reference,'queued',now,now,now))
        except Exception:
            path.unlink(missing_ok=True)
            raise
    return {'mode':'live','token':token,'reference':reference,'status':'queued'}


def recover_and_cleanup():
    now=time.time()
    with database() as db:
        # A stopped process could have submitted DATA without receiving the reply.
        db.execute("UPDATE jobs SET status='unknown',updated=? WHERE status='sending'",(now,))
    cleanup()


def cleanup():
    now=time.time()
    with database() as db:
        stale=db.execute('SELECT token FROM jobs WHERE created<? AND status IN (\'queued\',\'retry\')',(now-86400,)).fetchall()
        for row in stale:
            db.execute("UPDATE jobs SET status='expired',updated=? WHERE token=?",(now,row['token']))
        terminal=db.execute("SELECT token FROM jobs WHERE status NOT IN ('queued','retry','sending')").fetchall()
        for row in terminal:
            payload_path(row['token']).unlink(missing_ok=True)
        db.execute('DELETE FROM jobs WHERE created<?',(now-7*86400,))
    folder=STATE/'outbox'
    if folder.exists():
        with database() as db:
            known={row[0] for row in db.execute('SELECT token FROM jobs')}
        for path in folder.glob('*.eml'):
            if path.stem not in known and path.stat().st_mtime<now-3600:
                path.unlink(missing_ok=True)


def claim():
    now=time.time()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute("SELECT * FROM jobs WHERE status IN ('queued','retry') AND next_try<=? ORDER BY created LIMIT 1",(now,)).fetchone()
        if row:
            db.execute("UPDATE jobs SET status='sending',attempts=attempts+1,updated=? WHERE token=?",(now,row['token']))
    return dict(row) if row else None


def finish(token,state):
    now=time.time()
    with database() as db:
        row=db.execute('SELECT attempts FROM jobs WHERE token=?',(token,)).fetchone()
        if state=='retry' and row and row['attempts']>=5:
            state='failed'
        delay=min(3600,60*2**min(row['attempts'] if row else 1,6))
        db.execute('UPDATE jobs SET status=?,updated=?,next_try=? WHERE token=?',(state,now,now+delay,token))
    if state!='retry':
        payload_path(token).unlink(missing_ok=True)
