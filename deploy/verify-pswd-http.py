from pathlib import Path
from urllib.request import urlopen
from html.parser import HTMLParser
import re
root=Path('/opt/pswd/pswd-main/dist')
base='https://sit.samzhao.cloud'
count=0
for f in root.rglob('*'):
    if not f.is_file(): continue
    path='/tools/pswd/'+f.relative_to(root).as_posix()
    with urlopen(base+path,timeout=15) as response:
        assert response.status==200,(path,response.status)
        assert response.read()==f.read_bytes(),path
    count+=1
print(f'PASS: {count} deployed PSWD files match the build over HTTPS, including scripts, styles, fonts and license.')
for path in ['/','/tools/','/tools/pswd/']:
    with urlopen(base+path,timeout=15) as response:
        page=response.read().decode('utf-8-sig')
        assert response.status==200
        if path=='/': assert 'href="/tools/"' in page
        if path=='/tools/': assert 'href="/tools/pswd/"' in page
        if path=='/tools/pswd/':
            assert 'component-url="/tools/pswd/_astro/' in page
            assert 'https://reset.sit.ac.nz' in page
        print('PASS:',path)
