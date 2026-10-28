"""Preview-only support form: self-hosted CAPTCHA, image validation, no delivery."""
import base64
import hashlib
import hmac
import io
import json
import os
import random
import re
import secrets
import sqlite3
import time
import warnings
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request, session
from PIL import Image, ImageDraw, ImageFont, ImageOps, UnidentifiedImageError
from mailer import build_email

STATE = Path(os.environ.get('SUPPORT_STATE', '/var/lib/student-feedback-preview'))
STATE.mkdir(parents=True, exist_ok=True)
key_path = STATE / 'session-secret'
if not key_path.exists():
    fd = os.open(key_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(secrets.token_bytes(32))
KEY = key_path.read_bytes()
app = Flask(__name__)
app.config.update(SECRET_KEY=KEY, MAX_CONTENT_LENGTH=10 * 1024 * 1024,
                  SESSION_COOKIE_NAME='support_session', SESSION_COOKIE_SECURE=True,
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')
Image.MAX_IMAGE_PIXELS = 8_000_000
ALLOWED_ORIGINS = {'https://sp.samzhao.cloud', 'https://47.95.144.1'}
CATEGORIES = {'contact_update', 'mfa', 'login', 'password', 'learning', 'other'}
REASONS = {'old_phone': 'The previous mobile number is no longer available.',
           'new_contact': 'The student needs to update their contact details.',
           'lost_device': 'The student no longer has access to their authentication device.',
           'code_failed': 'The student cannot receive or use the verification code.',
           'other': ''}


@contextmanager
def database():
    connection = sqlite3.connect(STATE / 'limits.sqlite', timeout=5)
    connection.execute('CREATE TABLE IF NOT EXISTS challenges (id TEXT PRIMARY KEY, owner TEXT, answer TEXT, expires REAL)')
    connection.execute('CREATE TABLE IF NOT EXISTS hits (scope TEXT, created REAL)')
    connection.execute('CREATE INDEX IF NOT EXISTS hits_scope ON hits(scope,created)')
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def digest(value):
    return hmac.new(KEY, value.encode(), hashlib.sha256).hexdigest()


def throttle(kind, limit, interval):
    ip = request.headers.get('X-Real-IP', request.remote_addr or '')
    scope = kind + ':' + digest(ip)
    now = time.time()
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('DELETE FROM hits WHERE created < ?', (now - 3600,))
        db.execute('DELETE FROM challenges WHERE expires < ?', (now,))
        count = db.execute('SELECT COUNT(*) FROM hits WHERE scope=? AND created>?', (scope, now-interval)).fetchone()[0]
        if count >= limit:
            return False
        db.execute('INSERT INTO hits VALUES (?,?)', (scope, now))
    return True


def error(message, status=400):
    return jsonify(message=message), status


@app.after_request
def private_response(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.errorhandler(413)
def too_large(_exception):
    return error('附件总大小超出限制，请缩小图片后重试。', 413)


@app.get('/api/support/captcha')
def captcha():
    if not throttle('captcha', 30, 600):
        return error('刷新过于频繁，请稍后再试。', 429)
    if 'sid' not in session:
        session['sid'] = secrets.token_urlsafe(24)
    answer = ''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(5))
    challenge = secrets.token_urlsafe(24)
    with database() as db:
        db.execute('DELETE FROM challenges WHERE owner=?', (digest(session['sid']),))
        db.execute('INSERT INTO challenges VALUES (?,?,?,?)', (challenge, digest(session['sid']), digest(answer), time.time()+120))
    image = Image.new('RGB', (240, 88), '#fff7e9')
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 35)
    except OSError:
        font = ImageFont.load_default()
    noise = random.SystemRandom()
    for _ in range(8):
        draw.line([(noise.randrange(240),noise.randrange(88)),(noise.randrange(240),noise.randrange(88))], fill='#dbc4a5', width=1)
    for index, character in enumerate(answer):
        draw.text((18+index*43, noise.randrange(15,25)), character, font=font, fill=noise.choice(['#553524','#755039','#654330']))
    for _ in range(120):
        draw.point((noise.randrange(240),noise.randrange(88)), fill='#c6a784')
    output = io.BytesIO()
    image.save(output, format='PNG')
    return jsonify(id=challenge, image='data:image/png;base64,'+base64.b64encode(output.getvalue()).decode(), expires_in=120)


def consume_captcha(identifier, answer):
    owner = digest(session.get('sid', ''))
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT owner,answer,expires FROM challenges WHERE id=?', (identifier,)).fetchone()
        if not row or row[0] != owner:
            return False
        db.execute('DELETE FROM challenges WHERE id=?', (identifier,))
    return row[2] > time.time() and hmac.compare_digest(row[1], digest(answer.strip().upper()))


def clean_image(upload):
    raw = upload.read(3*1024*1024+1)
    if not raw or len(raw) > 3*1024*1024:
        raise ValueError('每张截图必须小于 3 MB。')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as check:
                if check.format not in ('JPEG','PNG','WEBP'):
                    raise ValueError('截图仅支持 JPG、PNG 或 WebP。')
                check.verify()
            with Image.open(io.BytesIO(raw)) as original:
                original.load()
                oriented = ImageOps.exif_transpose(original)
                converted = oriented.convert('RGB')
                converted.thumbnail((2000,2000))
                clean = Image.new('RGB', converted.size, 'white')
                clean.paste(converted)
                output = io.BytesIO()
                clean.save(output, format='PNG')
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exception:
        raise ValueError('截图无法读取或像素过大，请重新截图上传。') from exception
    if output.tell() > 3*1024*1024:
        raise ValueError('截图处理后仍超过 3 MB，请裁剪后上传。')
    return output.getvalue(), 'png'


@app.post('/api/support/preview')
def preview():
    if request.headers.get('Origin') not in ALLOWED_ORIGINS:
        return error('请从本站反馈页面提交。', 403)
    if not throttle('submit', 10, 600):
        return error('尝试次数过多，请十分钟后重试。', 429)
    form = request.form
    if form.get('website'):
        return error('请求无效。')
    if not consume_captcha(form.get('captcha_id','')[:100], form.get('captcha','')[:10]):
        return error('验证码错误或已过期，请换一张重试。')
    def field(name, maximum, required=False):
        value = form.get(name,'').strip()
        if required and not value:
            labels = {'name':'姓名', 'student_id':'外方学生 ID', 'mobile':'联系电话',
                      'domestic_id':'国内学号', 'contact_email':'私人邮箱'}
            raise ValueError('请填写'+labels.get(name, '必填信息')+'。')
        if len(value)>maximum or '\x00' in value:
            raise ValueError('请完整填写表单，并检查输入长度。')
        return value
    try:
        name = field('name',80,True)
        domestic = field('domestic_id',24,True)
        student_id = field('student_id',32,True)
        email = field('contact_email',180,True)
        category = field('category',30,True)
        mobile = field('mobile',32,True)
        description = field('description',1500)
        error_text = field('error',500)
        tried = field('tried',500)
        occurred = field('occurred_at',32,True)
        zone = field('timezone',80,True)
        if not re.fullmatch(r'\d{6,24}',domestic) or not re.fullmatch(r'[A-Za-z0-9-]{3,32}',student_id):
            raise ValueError('请检查国内学号和外方学生 ID。')
        if category not in CATEGORIES or form.get('consent')!='yes':
            raise ValueError('请选择问题类型，并阅读勾选信息使用说明。')
        if mobile and not re.fullmatch(r'\+?[0-9 ()-]{6,32}',mobile):
            raise ValueError('请填写带国家区号的有效联系电话。')
        datetime.fromisoformat(occurred)
        from zoneinfo import ZoneInfo
        ZoneInfo(zone)
        reason_key = field('reason',30)
        if reason_key not in REASONS:
            raise ValueError('请选择问题原因。')
        if category not in {'contact_update','mfa'} and not description:
            raise ValueError('请简要描述遇到的问题。')
        reason = REASONS[reason_key]
        if description:
            reason = (reason+'\n' if reason else '')+description
        if not reason:
            raise ValueError('请填写问题描述或选择具体原因。')
        uploads = [item for item in request.files.getlist('screenshots') if item.filename]
        if len(uploads)>3:
            raise ValueError('最多上传三张截图。')
        images = [clean_image(item) for item in uploads]
        ticket='PREVIEW-'+datetime.now(timezone.utc).strftime('%Y%m%d')+'-'+secrets.token_hex(3).upper()
        message=build_email(ticket,category=category,name=name,student_id=student_id,contact_email=email,mobile=mobile,reason=reason,error=error_text,tried=tried,domestic_id=domestic,occurred_at=occurred+' ('+zone+')',attachments=images)
    except (ValueError,KeyError) as exception:
        return error(str(exception))
    return jsonify(mode='preview',reference=ticket,cc=str(message['Cc']),subject=str(message['Subject']),body=message.get_body(preferencelist=('plain',)).get_content(),attachments=[{'name':'screenshot-'+str(i+1)+'.png','size':len(item[0])} for i,item in enumerate(images)],message='预览已生成，未发送邮件。')
