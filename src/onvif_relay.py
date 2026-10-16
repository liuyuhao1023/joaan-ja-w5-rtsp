from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone
import xml.etree.ElementTree as E
import ipaddress, json, os

HOST=os.environ.get('PUBLIC_HOST','192.168.10.10')
URL=f'http://{HOST}:8899/onvif/device_service'
MEDIA=f'http://{HOST}:8899/onvif/media_service'
STREAM=f'rtsp://{HOST}:8554/joaan/nvr'
NS={'s':'http://www.w3.org/2003/05/soap-envelope','tds':'http://www.onvif.org/ver10/device/wsdl','trt':'http://www.onvif.org/ver10/media/wsdl','tt':'http://www.onvif.org/ver10/schema','ter':'http://www.onvif.org/ver10/error'}
ENC='''<tt:Name>H264 1080p</tt:Name><tt:UseCount>1</tt:UseCount><tt:Encoding>H264</tt:Encoding><tt:Resolution><tt:Width>1920</tt:Width><tt:Height>1080</tt:Height></tt:Resolution><tt:Quality>5</tt:Quality><tt:RateControl><tt:FrameRateLimit>15</tt:FrameRateLimit><tt:EncodingInterval>1</tt:EncodingInterval><tt:BitrateLimit>2048</tt:BitrateLimit></tt:RateControl><tt:H264><tt:GovLength>30</tt:GovLength><tt:H264Profile>Main</tt:H264Profile></tt:H264><tt:Multicast><tt:Address><tt:Type>IPv4</tt:Type><tt:IPv4Address>0.0.0.0</tt:IPv4Address></tt:Address><tt:Port>0</tt:Port><tt:TTL>1</tt:TTL><tt:AutoStart>false</tt:AutoStart></tt:Multicast><tt:SessionTimeout>PT60S</tt:SessionTimeout>'''
SRC='''<tt:Name>Joaan Source</tt:Name><tt:UseCount>1</tt:UseCount><tt:SourceToken>source0</tt:SourceToken><tt:Bounds x="0" y="0" width="1920" height="1080"/>'''
PROF=f'''<trt:Profiles token="profile0" fixed="true"><tt:Name>Joaan H264</tt:Name><tt:VideoSourceConfiguration token="sourcecfg0">{SRC}</tt:VideoSourceConfiguration><tt:VideoEncoderConfiguration token="encoder0">{ENC}</tt:VideoEncoderConfiguration></trt:Profiles>'''
OPT='''<tt:QualityRange><tt:Min>5</tt:Min><tt:Max>5</tt:Max></tt:QualityRange><tt:H264><tt:ResolutionsAvailable><tt:Width>1920</tt:Width><tt:Height>1080</tt:Height></tt:ResolutionsAvailable><tt:GovLengthRange><tt:Min>30</tt:Min><tt:Max>30</tt:Max></tt:GovLengthRange><tt:FrameRateRange><tt:Min>15</tt:Min><tt:Max>15</tt:Max></tt:FrameRateRange><tt:EncodingIntervalRange><tt:Min>1</tt:Min><tt:Max>1</tt:Max></tt:EncodingIntervalRange><tt:H264ProfilesSupported>Main</tt:H264ProfilesSupported></tt:H264>'''

def response(op):
 now=datetime.now(timezone.utc)
 data={
 'GetDeviceInformation':('<tds:GetDeviceInformationResponse><tds:Manufacturer>Joaan Relay</tds:Manufacturer><tds:Model>H264 Gateway</tds:Model><tds:FirmwareVersion>1.0</tds:FirmwareVersion><tds:SerialNumber>ja-w5-relay-demo</tds:SerialNumber><tds:HardwareId>Ubuntu-MediaMTX</tds:HardwareId></tds:GetDeviceInformationResponse>'),
 'GetCapabilities':f'''<tds:GetCapabilitiesResponse><tds:Capabilities><tt:Device><tt:XAddr>{URL}</tt:XAddr><tt:Network><tt:IPFilter>false</tt:IPFilter><tt:ZeroConfiguration>false</tt:ZeroConfiguration><tt:IPVersion6>false</tt:IPVersion6><tt:DynDNS>false</tt:DynDNS></tt:Network><tt:System><tt:DiscoveryResolve>false</tt:DiscoveryResolve><tt:DiscoveryBye>false</tt:DiscoveryBye><tt:RemoteDiscovery>false</tt:RemoteDiscovery><tt:SystemBackup>false</tt:SystemBackup><tt:SystemLogging>false</tt:SystemLogging><tt:FirmwareUpgrade>false</tt:FirmwareUpgrade><tt:SupportedVersions><tt:Major>2</tt:Major><tt:Minor>0</tt:Minor></tt:SupportedVersions></tt:System><tt:Security><tt:TLS1.1>false</tt:TLS1.1><tt:TLS1.2>false</tt:TLS1.2><tt:OnboardKeyGeneration>false</tt:OnboardKeyGeneration><tt:AccessPolicyConfig>false</tt:AccessPolicyConfig><tt:X.509Token>false</tt:X.509Token><tt:SAMLToken>false</tt:SAMLToken><tt:KerberosToken>false</tt:KerberosToken><tt:RELToken>false</tt:RELToken></tt:Security></tt:Device><tt:Media><tt:XAddr>{MEDIA}</tt:XAddr><tt:StreamingCapabilities><tt:RTPMulticast>false</tt:RTPMulticast><tt:RTP_TCP>true</tt:RTP_TCP><tt:RTP_RTSP_TCP>true</tt:RTP_RTSP_TCP></tt:StreamingCapabilities><tt:Extension><tt:ProfileCapabilities><tt:MaximumNumberOfProfiles>1</tt:MaximumNumberOfProfiles></tt:ProfileCapabilities></tt:Extension></tt:Media></tds:Capabilities></tds:GetCapabilitiesResponse>''',
 'GetServices':f'''<tds:GetServicesResponse><tds:Service><tds:Namespace>{NS['tds']}</tds:Namespace><tds:XAddr>{URL}</tds:XAddr><tds:Version><tt:Major>2</tt:Major><tt:Minor>0</tt:Minor></tds:Version></tds:Service><tds:Service><tds:Namespace>{NS['trt']}</tds:Namespace><tds:XAddr>{MEDIA}</tds:XAddr><tds:Version><tt:Major>2</tt:Major><tt:Minor>0</tt:Minor></tds:Version></tds:Service></tds:GetServicesResponse>''',
 'GetScopes':'''<tds:GetScopesResponse><tds:Scopes><tt:ScopeDef>Fixed</tt:ScopeDef><tt:ScopeItem>onvif://www.onvif.org/type/video_encoder</tt:ScopeItem></tds:Scopes><tds:Scopes><tt:ScopeDef>Fixed</tt:ScopeDef><tt:ScopeItem>onvif://www.onvif.org/name/JoaanRelay</tt:ScopeItem></tds:Scopes></tds:GetScopesResponse>''',
 'GetHostname':'<tds:GetHostnameResponse><tds:HostnameInformation><tt:FromDHCP>false</tt:FromDHCP><tt:Name>JoaanRelay</tt:Name></tds:HostnameInformation></tds:GetHostnameResponse>',
 'GetProfiles':f'<trt:GetProfilesResponse>{PROF}</trt:GetProfilesResponse>',
 'GetProfile':f'<trt:GetProfileResponse>{PROF.replace("trt:Profiles","trt:Profile")}</trt:GetProfileResponse>',
 'GetVideoEncoderConfigurations':f'<trt:GetVideoEncoderConfigurationsResponse><trt:Configurations token="encoder0">{ENC}</trt:Configurations></trt:GetVideoEncoderConfigurationsResponse>',
 'GetVideoEncoderConfiguration':f'<trt:GetVideoEncoderConfigurationResponse><trt:Configuration token="encoder0">{ENC}</trt:Configuration></trt:GetVideoEncoderConfigurationResponse>',
 'GetVideoSourceConfigurations':f'<trt:GetVideoSourceConfigurationsResponse><trt:Configurations token="sourcecfg0">{SRC}</trt:Configurations></trt:GetVideoSourceConfigurationsResponse>',
 'GetVideoSourceConfiguration':f'<trt:GetVideoSourceConfigurationResponse><trt:Configuration token="sourcecfg0">{SRC}</trt:Configuration></trt:GetVideoSourceConfigurationResponse>',
 'GetVideoSources':'<trt:GetVideoSourcesResponse><trt:VideoSources token="source0"><tt:Framerate>15</tt:Framerate><tt:Resolution><tt:Width>1920</tt:Width><tt:Height>1080</tt:Height></tt:Resolution></trt:VideoSources></trt:GetVideoSourcesResponse>',
 'GetVideoEncoderConfigurationOptions':f'<trt:GetVideoEncoderConfigurationOptionsResponse><trt:Options>{OPT}</trt:Options></trt:GetVideoEncoderConfigurationOptionsResponse>',
 'GetStreamUri':f'<trt:GetStreamUriResponse><trt:MediaUri><tt:Uri>{STREAM}</tt:Uri><tt:InvalidAfterConnect>false</tt:InvalidAfterConnect><tt:InvalidAfterReboot>false</tt:InvalidAfterReboot><tt:Timeout>PT60S</tt:Timeout></trt:MediaUri></trt:GetStreamUriResponse>',
 'GetAudioSources':'<trt:GetAudioSourcesResponse/>',
 'GetAudioEncoderConfigurations':'<trt:GetAudioEncoderConfigurationsResponse/>',
 'GetAudioSourceConfigurations':'<trt:GetAudioSourceConfigurationsResponse/>',
 'GetServiceCapabilities':'<trt:GetServiceCapabilitiesResponse><trt:Capabilities SnapshotUri="false" Rotation="false"><trt:ProfileCapabilities MaximumNumberOfProfiles="1"/><trt:StreamingCapabilities RTPMulticast="false" RTP_TCP="true" RTP_RTSP_TCP="true"/></trt:Capabilities></trt:GetServiceCapabilitiesResponse>',
 }
 if op=='GetSystemDateAndTime':
  return f'<tds:GetSystemDateAndTimeResponse><tds:SystemDateAndTime><tt:DateTimeType>NTP</tt:DateTimeType><tt:DaylightSavings>false</tt:DaylightSavings><tt:TimeZone><tt:TZ>UTC0</tt:TZ></tt:TimeZone><tt:UTCDateTime><tt:Time><tt:Hour>{now.hour}</tt:Hour><tt:Minute>{now.minute}</tt:Minute><tt:Second>{now.second}</tt:Second></tt:Time><tt:Date><tt:Year>{now.year}</tt:Year><tt:Month>{now.month}</tt:Month><tt:Day>{now.day}</tt:Day></tt:Date></tt:UTCDateTime></tds:SystemDateAndTime></tds:GetSystemDateAndTimeResponse>'
 if op not in data:return '<s:Fault><s:Code><s:Value>s:Receiver</s:Value><s:Subcode><s:Value>ter:ActionNotSupported</s:Value></s:Subcode></s:Code><s:Reason><s:Text xml:lang="en">Read-only relay: action not supported</s:Text></s:Reason></s:Fault>'
 return data[op]

class Handler(BaseHTTPRequestHandler):
 def allowed(self):
  ip=ipaddress.ip_address(self.client_address[0]);return any(ip in ipaddress.ip_network(n) for n in os.environ.get('ALLOWED_NETWORKS','127.0.0.0/8').split(','))
 def do_POST(self):
  if not self.allowed():self.send_error(403);return
  try:
   n=int(self.headers.get('Content-Length','0'))
   if n<1 or n>65536:self.send_error(400);return
   root=E.fromstring(self.rfile.read(n));body=root.find('{'+NS['s']+'}Body')
   if body is None:body=root.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
   op=list(body)[0].tag.split('}')[-1]
   payload=response(op);print(self.client_address[0],op,flush=True)
   xmlns=' '.join(f'xmlns:{k}="{v}"' for k,v in NS.items());out=(f'<?xml version="1.0" encoding="utf-8"?><s:Envelope {xmlns}><s:Body>{payload}</s:Body></s:Envelope>').encode()
   self.send_response(500 if '<s:Fault>' in payload else 200);self.send_header('Content-Type','application/soap+xml; charset=utf-8');self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out)
  except Exception as e:
   print('request error',type(e).__name__,flush=True);self.send_error(400)
 def do_GET(self):
  if not self.allowed():self.send_error(403);return
  out=b'{"service":"Joaan H264 ONVIF relay","readOnly":true}';self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(out)));self.end_headers();self.wfile.write(out)
 def log_message(self,*a):pass

if __name__=='__main__':ThreadingHTTPServer((os.environ.get('ONVIF_BIND','127.0.0.1'),8899),Handler).serve_forever()
