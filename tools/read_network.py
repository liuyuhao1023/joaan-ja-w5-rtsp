"""Read-only ONVIF network probe. No automatic IP changes or password guessing."""
import argparse,urllib.request,xml.etree.ElementTree as E
p=argparse.ArgumentParser();p.add_argument('host');p.add_argument('--port',type=int,default=8899);a=p.parse_args()
ns='http://www.onvif.org/ver10/device/wsdl'
body=f'<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"><s:Body><d:GetNetworkInterfaces xmlns:d="{ns}"/></s:Body></s:Envelope>'.encode()
r=urllib.request.Request(f'http://{a.host}:{a.port}/onvif/device_service',data=body,headers={'Content-Type':f'application/soap+xml; charset=utf-8; action="{ns}/GetNetworkInterfaces"'})
op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
try:
 with op.open(r,timeout=5) as response:root=E.fromstring(response.read())
 for item in root.iter():
  if item.tag.split('}')[-1] in ('NetworkInterfaces','Address','PrefixLength','DHCP'):
   print(item.tag.split('}')[-1],item.attrib,(item.text or '').strip())
except Exception as error:
 raise SystemExit(f'{type(error).__name__}: probe failed; check network, service port and device authentication requirements')
