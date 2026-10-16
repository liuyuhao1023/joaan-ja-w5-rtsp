"""Create a local admin password hash; never commit the resulting auth.json."""
import argparse,getpass,hashlib,json,os,secrets
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--data-dir',default='/var/lib/joaan-dashboard');a=p.parse_args()
password=getpass.getpass('New admin password (12+ characters): ')
if len(password)<12:raise SystemExit('Use at least 12 characters')
if password!=getpass.getpass('Confirm password: '):raise SystemExit('Passwords differ')
root=Path(a.data_dir);root.mkdir(parents=True,exist_ok=True);salt=secrets.token_bytes(16)
f=root/'auth.json'
if f.exists():raise SystemExit('auth.json already exists; back it up before intentional rotation')
fd=os.open(f,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as out:json.dump({'salt':salt.hex(),'hash':hashlib.pbkdf2_hmac('sha256',password.encode(),salt,200000).hex()},out)
print('Created admin account; username: admin')
