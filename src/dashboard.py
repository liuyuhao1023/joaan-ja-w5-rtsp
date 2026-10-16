import json,os,socket,threading,time,urllib.request,urllib.error,urllib.parse,secrets,hashlib,hmac,re
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
API=os.environ.get('MTX_API','http://127.0.0.1:9997');ROOT=Path(os.environ.get('WEB_ROOT',str(Path(__file__).parent.parent/'web')));DATA=Path(os.environ.get('DATA_DIR','/var/lib/joaan-dashboard'));PUBLIC_HOST=os.environ.get('PUBLIC_HOST','192.168.10.10');OP=urllib.request.build_opener(urllib.request.ProxyHandler({}));LOCK=threading.RLock();STATE={'ok':False,'paths':[]};SESSIONS={};FAILURES={}
def api(path,data=None,method=None):
 r=urllib.request.Request(API+path,data=None if data is None else json.dumps(data).encode(),method=method,headers={'Content-Type':'application/json'})
 with OP.open(r,timeout=5) as x:return json.load(x) if x.headers.get('Content-Length')!='0' else {}
def load():
 return json.loads((DATA/'cameras.json').read_text()) if (DATA/'cameras.json').exists() else [{'id':'joaan','name':'乔安 JA-W5','ip':'192.168.10.250','location':'光猫 Wi-Fi','protected':True,'paths':['joaan/main','joaan/sub','joaan/nvr']}]
def save(cams):
 p=DATA/'cameras.tmp';p.write_text(json.dumps(cams,ensure_ascii=False,indent=2));p.chmod(0o600);p.replace(DATA/'cameras.json')
def public(c):return {k:v for k,v in c.items() if k not in ('source','subSource')}
def pathspec(c):
 return [(f"cams/{c['id']}/main",c['source'])]+([(f"cams/{c['id']}/sub",c['subSource'])] if c.get('subSource') else [])
def reconcile(c):
 for name,source in pathspec(c):
  try:api('/v3/config/paths/get/'+name)
  except urllib.error.HTTPError as e:
   if e.code!=404:raise
   api('/v3/config/paths/add/'+name,{'source':source,'rtspTransport':'tcp','sourceOnDemand':False},'POST')
def monitor():
 prev={};then=time.monotonic()
 while True:
  try:
   with LOCK:
    for c in load():
     if not c.get('protected'):
      try:reconcile(c)
      except Exception:pass
   items=api('/v3/paths/list?itemsPerPage=1000')['items'];now=time.monotonic();paths=[]
   for p in items:
    name=p['name'];n=p.get('bytesReceived',0);old=prev.get(name)
    paths.append({'name':name,'ready':p.get('ready',False),'readers':len(p.get('readers') or []),'tracks':p.get('tracks') or [],'bitrate':max(0,n-old)*8/max(now-then,.001) if old is not None else None,'url':f'rtsp://{PUBLIC_HOST}:8554/'+name})
   prev={p['name']:p.get('bytesReceived',0) for p in items};then=now
   with LOCK:STATE.update(ok=True,paths=paths,error=None,checkedAt=time.time())
  except Exception:
   with LOCK:STATE.update(ok=False,paths=[],error='无法连接视频中转服务',checkedAt=time.time())
  time.sleep(3)
class Handler(BaseHTTPRequestHandler):
 def reply(self,status,obj,cookie=None):
  data=json.dumps(obj,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Content-Length',str(len(data)))
  if cookie:self.send_header('Set-Cookie',cookie)
  self.end_headers();self.wfile.write(data)
 def auth(self):
  cookie=dict(x.strip().split('=',1) for x in self.headers.get('Cookie','').split(';') if '=' in x);return SESSIONS.get(cookie.get('session',''),0)>time.time()
 def do_GET(self):
  if self.path=='/api/status':
   with LOCK:self.reply(200,dict(STATE,network={'routeOk':any(p['ready'] for p in STATE['paths'])}));return
  if self.path=='/api/cameras':
   with LOCK:self.reply(200,{'cameras':[public(c) for c in load()],'authenticated':self.auth()});return
  if self.path in ('/','/index.html','/topology.html'):
   data=(ROOT/('topology.html' if self.path=='/topology.html' else 'index.html')).read_text().replace('192.168.10.10',PUBLIC_HOST).encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
  self.reply(404,{'error':'页面不存在'})
 def do_POST(self):
  try:
   origin=self.headers.get('Origin');host=self.headers.get('Host')
   if origin and urllib.parse.urlsplit(origin).netloc!=host:return self.reply(403,{'error':'请求来源不匹配'})
   if int(self.headers.get('Content-Length',0))>16384:return self.reply(413,{'error':'请求过大'})
   body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
   if self.path=='/api/login':
    ip=self.client_address[0];count,expiry=FAILURES.get(ip,(0,0))
    if expiry<time.time():count=0
    if count>=8:return self.reply(429,{'error':'尝试过多，请 5 分钟后重试'})
    cfg=json.loads((DATA/'auth.json').read_text());hashed=hashlib.pbkdf2_hmac('sha256',str(body.get('password','')).encode(),bytes.fromhex(cfg['salt']),200000).hex()
    if body.get('username')!='admin' or not hmac.compare_digest(hashed,cfg['hash']):FAILURES[ip]=(count+1,time.time()+300);return self.reply(401,{'error':'用户名或密码不正确'})
    token=secrets.token_urlsafe(32);SESSIONS[token]=time.time()+28800;FAILURES.pop(ip,None);return self.reply(200,{'ok':True},'session='+token+'; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
   if not self.auth():return self.reply(401,{'error':'请先登录管理账号'})
   with LOCK:
    cams=load()
    if self.path=='/api/cameras':
     id=body.get('id') or secrets.token_hex(4)
     if not re.fullmatch('[a-z0-9_-]{1,32}',id):raise ValueError('设备 ID 无效')
     old=next((c for c in cams if c['id']==id),None)
     if old and old.get('protected'):raise ValueError('现有乔安设备已保护，避免中断录像')
     name=str(body.get('name','')).strip();source=str(body.get('source','')).strip();sub=str(body.get('subSource','')).strip()
     if not name or len(name)>80:raise ValueError('请输入设备名称（最多 80 字）')
     for u in [source]+([sub] if sub else []):
      parsed=urllib.parse.urlsplit(u)
      if parsed.scheme!='rtsp' or not parsed.hostname:raise ValueError('请输入完整 rtsp:// 地址')
     c={'id':id,'name':name,'ip':urllib.parse.urlsplit(source).hostname,'location':str(body.get('location',''))[:120],'source':source,'subSource':sub,'protected':False,'paths':[f'cams/{id}/main']+([f'cams/{id}/sub'] if sub else [])}
     # Apply only this device's paths, then persist and recover them on service restart.
     for path,url in pathspec(c):
      try:api('/v3/config/paths/get/'+path);api('/v3/config/paths/patch/'+path,{'source':url},'PATCH')
      except urllib.error.HTTPError as e:
       if e.code!=404:raise
       api('/v3/config/paths/add/'+path,{'source':url,'rtspTransport':'tcp','sourceOnDemand':False},'POST')
     if old:
      for path in set(old['paths'])-set(c['paths']):api('/v3/config/paths/delete/'+path,method='DELETE')
     save([x for x in cams if x['id']!=id]+[c]);return self.reply(200,{'camera':public(c)})
    if self.path=='/api/cameras/delete':
     c=next((x for x in cams if x['id']==body.get('id')),None)
     if not c or c.get('protected'):raise ValueError('该设备不可移除')
     for path in c['paths']:
      try:api('/v3/config/paths/delete/'+path,method='DELETE')
      except urllib.error.HTTPError as e:
       if e.code!=404:raise
     save([x for x in cams if x['id']!=c['id']]);return self.reply(200,{'ok':True})
    if self.path=='/api/logout':
     cookie=dict(x.strip().split('=',1) for x in self.headers.get('Cookie','').split(';') if '=' in x);SESSIONS.pop(cookie.get('session',''),None);return self.reply(200,{'ok':True},'session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
   self.reply(404,{'error':'接口不存在'})
  except ValueError as e:self.reply(400,{'error':str(e)})
  except Exception:self.reply(502,{'error':'配置未完成，请检查中转服务后重试'})
if __name__=='__main__':
 DATA.mkdir(exist_ok=True,parents=True)
 if not (DATA/'cameras.json').exists():save(load())
 threading.Thread(target=monitor,daemon=True).start();ThreadingHTTPServer((os.environ.get('WEB_BIND','127.0.0.1'),int(os.environ.get('WEB_PORT','8088'))),Handler).serve_forever()
