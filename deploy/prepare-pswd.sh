set -eu
mkdir -p /opt/sit-build /opt/pswd
cd /opt/sit-build
curl -fsS --connect-timeout 10 --max-time 120 -O https://nodejs.org/dist/v22.21.0/node-v22.21.0-linux-x64.tar.xz
curl -fsS --connect-timeout 10 --max-time 30 -O https://nodejs.org/dist/v22.21.0/SHASUMS256.txt
grep ' node-v22.21.0-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum -c -
tar -xJf node-v22.21.0-linux-x64.tar.xz
./node-v22.21.0-linux-x64/bin/node --version
