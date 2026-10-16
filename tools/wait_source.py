import json,time,urllib.request
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
while True:
 try:
  with op.open('http://127.0.0.1:9997/v3/paths/list',timeout=3) as r:items=json.load(r)['items']
  if any(p['name']=='joaan/main' and p['ready'] for p in items):break
 except Exception:pass
 time.sleep(5)
