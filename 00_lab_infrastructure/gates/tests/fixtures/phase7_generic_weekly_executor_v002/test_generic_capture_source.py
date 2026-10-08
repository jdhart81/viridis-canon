"""GET capture caller fixtures; no actual runtime or API admission claimed."""
import contextlib,copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import capture_weekly_inputs as capture
import prepare_weekly_configuration as c
import weekly_digest_executor as e
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.patches=[];self.calls=[];self.week='2026-W42';self.rid='23226761';self.token='fixture-memory-only-token-no-live-permission';self.registration={'receipt':{'record_id':self.rid,'release_week':'2026-W41'}};self.discovery={'start_kind':'CREATE_WEEK','record_id':None,'concept_id':None};self.native={'id':self.rid,'parent':{'id':'23226760'},'versions':{'index':1,'is_latest':True,'is_latest_draft':True}};self.legacy={'id':int(self.rid),'conceptrecid':'23226760'}
  builder=types.SimpleNamespace(verify_loaded=lambda *a:None,source_session=lambda *a:contextlib.nullcontext())
  self.patches=[patch.object(c,'ROOT',self.root),patch.object(capture,'preflight_sources',return_value={'purpose_source_pins':[],'before_ssot_sha256':'a'*64}),patch.object(capture,'load',return_value=builder)]
  for p in self.patches:p.start()
  modules={}
  transport=types.ModuleType('zenodo_transport');transport.NoRedirect=lambda:object();outer=self
  class Transport:
   def __init__(self,host,token,out,opener):self.out=Path(out);self.out.mkdir(parents=True);self.i=0
   def request(self,method,url,accept):
    outer.assertEqual(method,'GET');outer.calls.append((method,url,accept));self.i+=1;obj={'method':method,'url':url,'accept':accept,'environment':'zenodo.org','http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':copy.deepcopy(outer.native if accept=='application/vnd.inveniordm.v1+json'else outer.legacy)};p=self.out/f'{self.i:03d}_GET.json';p.write_bytes(c.encode(obj));return obj['response']
  transport.ZenodoTransport=Transport;modules['zenodo_transport']=transport
  discovery=types.ModuleType('owned_weekly_discovery')
  def account(root,week,token,out,opener):
   out.mkdir(parents=True);p=out/'DISCOVERY.json';p.write_bytes(c.encode(dict(self.discovery,release_week=week)));return c.binding(p)
  discovery.capture=account;modules['owned_weekly_discovery']=discovery
  pub=types.ModuleType('first_digest_publisher');pub.PacedOpener=lambda inner:inner;modules['first_digest_publisher']=pub
  registrar=types.ModuleType('methods_digest_registration');registrar.require_registration=lambda *a:copy.deepcopy(self.registration);modules['methods_digest_registration']=registrar
  self.modules=modules
 def tearDown(self):
  for p in reversed(self.patches):p.stop()
  self.tmp.cleanup()
 def call(self):
  with patch.dict(sys.modules,self.modules),patch.object(capture.urllib.request,'build_opener',return_value=object()):return capture.capture_inputs(self.root,{'source_session_consumer':{'path':str(self.root/'fixture-builder.py'),'sha256':'a'*64}},self.week,self.rid,self.token,self.root/'reports/verification-coverage/get-inputs',source_registration={'path':str(self.root/'fixture-reg.json'),'sha256':'b'*64})
 def test_first_week_uses_other_week_default_source_and_real_get_roles(self):
  result=self.call();value=json.loads(Path(result['path']).read_bytes());self.assertEqual(value['source_native_receipt'],value['source_native_before_create']);self.assertEqual(value['zenodo_writes'],0);self.assertEqual([x[0]for x in self.calls],['GET','GET']);self.assertNotIn(self.token,Path(result['path']).read_text())
 def test_same_week_uses_actual_default_latest_selected_record(self):
  self.week='2026-W41';self.discovery={'start_kind':'NEW_VERSION','record_id':self.rid,'concept_id':'23226760'};self.call();self.assertEqual(len(self.calls),2)
 def test_first_source_same_week_cannot_start_new_concept(self):self.registration['receipt']['release_week']=self.week;self.assertRaises(ValueError,self.call)
 def test_same_source_foreign_default_record_fails(self):self.registration['receipt']['record_id']='9';self.assertRaises(ValueError,self.call)
 def test_same_discovery_foreign_source_record_fails(self):self.week='2026-W41';self.discovery={'start_kind':'NEW_VERSION','record_id':'9','concept_id':'8'};self.assertRaises(ValueError,self.call)
 def test_first_discovery_invented_record_or_concept_fails(self):self.discovery['record_id']='9';self.assertRaises(ValueError,self.call)
 def test_unlisted_start_kind_fails(self):self.discovery['start_kind']='CREATE';self.assertRaises(ValueError,self.call)
 def test_nonlatest_or_pending_source_native_fails(self):self.native['versions']['is_latest_draft']=False;self.assertRaises(ValueError,self.call)
if __name__=='__main__':unittest.main()
