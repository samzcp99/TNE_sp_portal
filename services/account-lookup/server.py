"""Private, exact-match student account lookup. No student data in request logs."""
import hashlib
import hmac
import json
import os
import re
import sqlite3
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DATA = Path(os.environ.get('LOOKUP_DATA', '/var/lib/sit-account-lookup'))
SECRET = (DATA / 'secret').read_bytes()
RECORDS = json.loads((DATA / 'records.json').read_text())
LOCK = threading.Lock()
DB = sqlite3.connect(DATA / 'attempts.sqlite', check_same_thread=False)
DB.execute('CREATE TABLE IF NOT EXISTS attempts (scope TEXT, created REAL)')
DB.execute('CREATE INDEX IF NOT EXISTS scope_time ON attempts(scope, created)')
DB.commit()


def normalize(value):
    return unicodedata.normalize('NFKC', value).strip()


def digest(*values):
    return hmac.new(SECRET, '\0'.join(values).encode(), hashlib.sha256).hexdigest()


def take_attempt(ip, school, student_id):
    """Persistent throttles by IP and student ID; identifiers are keyed hashes."""
    scopes = [('ip:' + digest(ip), 20, 600),
              ('student:' + digest(school, student_id), 6, 900)]
    now = time.time()
    with LOCK:
        DB.execute('DELETE FROM attempts WHERE created < ?', (now - 900,))
        for scope, limit, seconds in scopes:
            count = DB.execute('SELECT COUNT(*) FROM attempts WHERE scope=? AND created>?',
                               (scope, now - seconds)).fetchone()[0]
            if count >= limit:
                DB.commit()
                return False
        DB.executemany('INSERT INTO attempts VALUES (?, ?)',
                       [(scope, now) for scope, _, _ in scopes])
        DB.commit()
    return True


class Handler(BaseHTTPRequestHandler):
    server_version = 'Lookup'

    def log_message(self, *_args):
        pass

    def respond(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Length', str(len(body)))
        if status == 429:
            self.send_header('Retry-After', '900')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.respond(405, {'message': '请通过查询表单提交。'})

    def do_POST(self):
        if self.path != '/api/account-lookup':
            return self.respond(404, {'message': '未找到服务。'})
        if self.headers.get('Origin') not in {'https://47.95.144.1', 'https://sp.samzhao.cloud'}:
            return self.respond(403, {'message': '请从本站查询页面提交。'})
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond(415, {'message': '请求格式不正确。'})
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024:
                raise ValueError()
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError()
            school, student_id, surname = [normalize(data.get(k, ''))
                                           for k in ('school', 'student_id', 'surname')]
            if school != 'hue' or not re.fullmatch(r'[0-9]{6,24}', student_id):
                raise ValueError()
            if not re.fullmatch(r'[\u3400-\u9fff]{1,2}', surname):
                raise ValueError()
        except (ValueError, TypeError, AttributeError, json.JSONDecodeError):
            return self.respond(400, {'message': '请填写正确的中国学校学号及中文姓氏（复姓请填写完整）。'})
        ip = self.headers.get('X-Real-IP', 'unknown')
        if not take_attempt(ip, school, student_id):
            return self.respond(429, {'message': '查询次数过多，请 15 分钟后重试，或联系项目老师。'})
        result = RECORDS.get(digest(school, student_id, surname))
        if result is None:
            return self.respond(404, {'message': '信息不匹配或暂未收录，请核对学号与姓氏；仍有问题请联系项目老师。'})
        self.respond(200, {'sit_id': result})


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8765), Handler)
    server.serve_forever()
