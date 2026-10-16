import importlib.util,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'src/onvif_relay.py'
spec=importlib.util.spec_from_file_location('relay',p);relay=importlib.util.module_from_spec(spec);spec.loader.exec_module(relay)
class ProtocolTests(unittest.TestCase):
 def test_stream_uri_matches_relay(self):
  value=relay.response('GetStreamUri');self.assertIn(relay.STREAM,value);self.assertIn('InvalidAfterReboot>false',value)
 def test_mutation_is_rejected(self):
  self.assertIn('ActionNotSupported',relay.response('SetNetworkInterfaces'))
 def test_profile_is_h264(self):
  self.assertIn('<tt:Encoding>H264</tt:Encoding>',relay.response('GetProfiles'))
if __name__=='__main__':unittest.main()
