"""Own reserve transition unit tests; full acceptance is still live-only."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import test_generic_before as f
class Tests(unittest.TestCase):
 def setUp(self):
  self.f=f.Tests(methodName='runTest');self.f.setUp();self.b=self.f.b;self.rid='23300001';self.concept='23300000';self.doi={'doi':{'identifier':'10.5281/zenodo.'+self.rid,'provider':'datacite','client':'datacite'}}
  self.response={'id':self.rid,'parent':{'id':self.concept},'pids':copy.deepcopy(self.doi)};self.state={'record_id':self.rid,'concept_id':self.concept,'completed':[],'attempts':[{'transport':None,'outcome':'RESERVED'}]};self.b.before_expected={'pids':{},'files':{'entries':{}}};self.b.before_legacy={'id':int(self.rid),'record_id':int(self.rid),'conceptrecid':self.concept,'state':'unsubmitted','submitted':False,'metadata':{'prereserve_doi':{'doi':'10.5281/zenodo.'+self.rid,'recid':int(self.rid)},'title':'Unchanged title','extra_science':['unchanged']},'links':{'badge':'https://zenodo.org/badge/doi/.svg','bucket':'unchanged'},'files':[]};self.b.sequence=0;self.b.sources=[];self.checked=[]
  self.receipt={'environment':'zenodo.org','method':'POST','url':'https://zenodo.org/api/records/'+self.rid+'/draft/pids/doi','accept':'application/vnd.inveniordm.v1+json','http_status':201,'request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'response_sha256':hashlib.sha256(e.raw_json(self.response)).hexdigest(),'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':self.response}
  self.p=self.f.root/'own_POST.json';self.save()
  self.b.get=lambda rid,pub,native=False:(copy.deepcopy({'id':self.rid,'pids':self.doi}if native else self.expected_legacy()),self.operation)
  self.b.prior=lambda *a,**kw:(None,None,None,None)
  def full(state,expected,wanted,legacy,native,**kw):
   self.assertEqual(expected['pids'],self.doi);self.assertEqual(native['pids'],self.doi);self.assertEqual(wanted,self.expected_legacy());self.assertEqual(legacy,wanted);self.checked.append(copy.deepcopy(expected));self.b.last_server_context={'fixture_only':True};self.b.last_draft_audit={'fixture_only':True}
  self.b.full_draft=full
 def save(self):self.p.write_bytes(e.raw_json(self.receipt));self.operation=e.binding(self.p)
 def expected_legacy(self):
  x=copy.deepcopy(self.b.before_legacy);doi='10.5281/zenodo.'+self.rid;url='https://doi.org/'+doi;x.update(doi=doi,doi_url=url);x['metadata']['doi']=doi;x['links'].update(doi=url,badge='https://zenodo.org/badge/doi/'+doi.replace('/','%2F')+'.svg');return x
 def tearDown(self):self.f.tearDown()
 def call(self,response=None):return self.b.after(self.state,'RESERVE_DOI',self.response if response is None else response,self.operation)
 def test_first_empty_native_pid_gains_only_exact_own_reservation(self):
  before=copy.deepcopy(self.b.before_legacy);report,ownership=self.call();self.assertIsNone(ownership);self.assertEqual(len(self.checked),1);self.assertEqual(self.checked[0]['pids'],self.doi);self.assertEqual(self.b.before_expected['pids'],{});self.assertEqual(self.b.before_legacy,before);saved=json.loads(Path(report['path']).read_bytes());self.assertEqual(saved['expected_native']['pids'],self.doi);self.assertEqual(saved['expected_legacy'],self.expected_legacy())
 def test_existing_same_pid_remains_identical(self):
  self.b.before_expected['pids']=copy.deepcopy(self.doi);self.call();self.assertEqual(self.checked[0]['pids'],self.b.before_expected['pids'])
 def test_foreign_record_parent_identifier_provider_client_or_extra_pid_fails(self):
  cases=[]
  for key,value in [('id','9'),('parent',{'id':'8'})]:x=copy.deepcopy(self.response);x[key]=value;cases.append(x)
  for key,value in [('identifier','10.5281/zenodo.9'),('provider','oai'),('client','other'),('extra',True)]:x=copy.deepcopy(self.response);x['pids']['doi'][key]=value;cases.append(x)
  for x in cases:
   with self.subTest(response=x):self.assertRaises(ValueError,self.call,x);self.assertEqual(self.checked,[])
 def test_missing_native_pid_response_is_not_inferred_from_legacy(self):
  x=copy.deepcopy(self.response);x['pids']={};self.assertRaises(ValueError,self.call,x);self.assertEqual(self.checked,[])
 def test_pending_roundtrip_cannot_grant_native_pid(self):
  self.receipt['status']='PENDING';self.save();self.assertRaises(ValueError,self.call);self.assertEqual(self.checked,[])
 def test_foreign_legacy_preregistration_never_restored_from_after(self):
  self.b.before_legacy['metadata']['prereserve_doi']['recid']=9;self.assertRaises(ValueError,self.call);self.assertEqual(self.checked,[])
 def test_minted_legacy_pid_already_in_before_is_not_rereserved(self):
  self.b.before_legacy['doi']='10.5281/zenodo.'+self.rid;self.assertRaises(ValueError,self.call);self.assertEqual(self.checked,[])
 def test_receipt_wrong_endpoint_representation_status_or_request_body_fails(self):
  original=copy.deepcopy(self.receipt)
  for field,value in [('url','https://zenodo.org/api/records/9/draft/pids/doi'),('accept','application/json'),('http_status',200),('request_body_sha256','0'*64)]:
   with self.subTest(field=field):self.receipt=copy.deepcopy(original);self.receipt[field]=value;self.save();self.assertRaises(ValueError,self.call);self.assertEqual(self.checked,[])
if __name__=='__main__':unittest.main()
