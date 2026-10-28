"""Run as root to import private records; never place input in the web root."""
import hashlib
import hmac
import json
import os
import sys
import unicodedata
from pathlib import Path

destination = Path('/var/lib/sit-account-lookup')
destination.mkdir(mode=0o750, parents=True, exist_ok=True)
secret_file = destination / 'secret'
if not secret_file.exists():
    secret_file.write_bytes(os.urandom(32))
secret = secret_file.read_bytes()
records = {}
for row in json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')):
    values = [unicodedata.normalize('NFKC', row[k]).strip()
              for k in ('school', 'student_id', 'surname')]
    key = hmac.new(secret, '\0'.join(values).encode(), hashlib.sha256).hexdigest()
    if key in records:
        raise ValueError('Duplicate student lookup key')
    records[key] = row['sit_id']
temporary = destination / 'records.next.json'
temporary.write_text(json.dumps(records))
temporary.replace(destination / 'records.json')
print('Imported record count:', len(records))
