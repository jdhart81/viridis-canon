"""Complete raw account continuation fixtures; no scientific admission claim."""
import copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_pending_discovery as p
import weekly_digest_executor as e
import owned_digest_machine as m
import test_weekly_weekly_discovery as raw
class Tests(unittest.TestCase):
 def setUp(self):
  self.fixture=raw.Tests(methodName='runTest');self.fixture.setUp();self.root=self.fixture.root;self.rid='23300001';self.parent='23300000';self.week='2026-W42';self.replays=[]
  self.plan={'start_kind':'CREATE_WEEK','release_week':self.week,'approved_inventory':[dict(name=n,path=str(self.root/n),bytes=1,sha256='a'*64,md5='b'*32)for n in sorted(m.NAMES)]}
  def put(name,value):x=self.root/name;x.write_bytes(e.raw_json(value));return e.binding(x)
  self.native={'id':self.rid,'metadata':{'title':'Viridis Methods Digest — '+self.week,'description':'Fixture scope only'},'parent':{'id':self.parent},'versions':{'index':1,'is_latest':False,'is_latest_draft':True},'pids':{},'is_draft':True,'is_published':False,'status':'draft'}
  created=put('create.json',{'method':'POST','url':'https://zenodo.org/api/deposit/depositions','environment':'zenodo.org','http_status':201,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':{'id':int(self.rid),'conceptrecid':self.parent,'submitted':False,'state':'unsubmitted','files':[],'links':{'latest_draft':'https://zenodo.org/api/deposit/depositions/'+self.rid}}})
  firstn=put('firstn.json',{'method':'GET','url':'https://zenodo.org/api/records/'+self.rid+'/draft','accept':'application/vnd.inveniordm.v1+json','environment':'zenodo.org','http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':self.native})
  firstl=put('firstl.json',{'method':'GET','url':'https://zenodo.org/api/deposit/depositions/'+self.rid,'environment':'zenodo.org','http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':{'id':int(self.rid),'conceptrecid':self.parent}})
  report=put('validated.json',{'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','status':'STRICT_DRAFT_SOURCE_NATIVE_LEGACY_FILES_PIDS_PASS','record_id':self.rid,'owned_native_get':firstn,'expected_native':self.native})
  reservation=put('reservation.json',{'fixture_only':True});s=m.initial(m.digest(self.plan),self.plan['approved_inventory'],start_kind='CREATE_WEEK');s=m.reserve(s,'CREATE_WEEK',reservation,'fixture-genuine-op');self.state=m.finish(s,created,report,ownership={'record_id':self.rid,'concept_id':self.parent,'first_owned_draft':firstn,'first_owned_legacy_draft':firstl,'inherited_inventory':[]})
  self.replayer=types.ModuleType('weekly_checkpoint_replay')
  def replay(plan,state,*,root):self.assertEqual(plan,self.plan);self.assertEqual(root,self.root);m.validate(state,m.digest(plan));self.replays.append(True)
  self.replayer.require_checkpoint=replay
 def tearDown(self):self.fixture.tearDown()
 def proof(self,rows):
  f=self.root/'records.json';f.write_bytes(e.raw_json({'records':rows}));v={k:copy.deepcopy(self.state[k])for k in('record_id','concept_id','creation_receipt','first_owned_draft','first_owned_legacy_draft','last_validation')};v.update(standard=p.STANDARD,status='COMPLETE_OWN_PENDING_ACCOUNT_CONTINUATION_NOT_PUBLICATION_CLEARANCE',release_week=self.week,plan_sha256=m.digest(self.plan),passes=[self.fixture.pages(rows),self.fixture.pages(rows)],records=e.binding(f),record_count=len(rows),own_pending_count=sum(str(x['id'])==self.rid for x in rows),producer_sha256=p.source_sha(),writes=0);return v
 def call(self,value):
  with patch.dict(sys.modules,{'weekly_checkpoint_replay':self.replayer}):return p.require_pending(value,root=self.root,plan=self.plan,state=self.state)
 def test_exact_genuinely_owned_pending_row_full_two_pass_pass(self):
  v=self.proof([raw.record(),self.native]);self.assertEqual(self.call(v)['own_pending_count'],1);self.assertTrue(self.replays)
 def test_endpoint_omits_draft_plus_independent_owned_baseline_pass(self):self.assertEqual(self.call(self.proof([raw.record()]))['own_pending_count'],0)
 def test_foreign_pending_same_week_is_never_filtered(self):
  r=copy.deepcopy(self.native);r['id']='23999999';r['parent']['id']='23999998';self.assertRaises(ValueError,self.call,self.proof([raw.record(),self.native,r]))
 def test_foreign_published_same_week_is_never_filtered(self):self.assertRaises(ValueError,self.call,self.proof([raw.record(),self.native,raw.record('23999999',week=self.week,parent='23999998')]))
 def test_own_published_row_cannot_be_hidden_as_pending(self):
  r=copy.deepcopy(self.native);r.update(is_draft=False,is_published=True,status='published');self.assertRaises(ValueError,self.call,self.proof([raw.record(),r]))
 def test_changed_own_parent_metadata_version_or_pid_fails(self):
  for key,value in [('parent',{'id':'9'}),('metadata',{'title':'Viridis Methods Digest — '+self.week}),('versions',{'index':2,'is_latest':False,'is_latest_draft':True}),('pids',{'doi':{'identifier':'foreign'}})]:
   with self.subTest(field=key):r=copy.deepcopy(self.native);r[key]=value;self.assertRaises(ValueError,self.call,self.proof([r]))
 def test_two_pass_race_fails(self):
  v=self.proof([raw.record(),self.native]);v['passes'][1]=self.fixture.pages([raw.record()]);self.assertRaises(ValueError,self.call,v)
 def test_omitted_whole_page_or_changed_raw_bytes_fails(self):
  v=self.proof([raw.record(),self.native]);v['passes'][0]=[];self.assertRaises(ValueError,self.call,v)
  v=self.proof([raw.record(),self.native]);_,r=e.bound(self.root,v['passes'][0][0]);Path(r['response_path']).write_bytes(b'{}');self.assertRaises(ValueError,self.call,v)
 def test_own_state_binding_or_plan_hash_substitution_fails(self):
  for key,val in [('record_id','9'),('concept_id','8'),('plan_sha256','0'*64),('creation_receipt',self.state['first_owned_draft'])]:
   with self.subTest(key=key):v=self.proof([self.native]);v[key]=val;self.assertRaises(ValueError,self.call,v)
 def test_reserved_failed_or_non_owned_state_never_grants_filter(self):
  for phase in ['NOT_STARTED','HOLD','UNCERTAIN']:
   with self.subTest(phase=phase):self.state['phase']=phase;self.assertRaises(ValueError,self.call,self.proof([self.native]))
 def test_duplicate_owned_account_identity_fails(self):self.assertRaises(ValueError,self.call,self.proof([self.native,copy.deepcopy(self.native)]))
 def test_type_differences_in_own_fields_fail(self):
  r=copy.deepcopy(self.native);r['versions']['index']=True;self.assertRaises(ValueError,self.call,self.proof([r]))
 def test_original_initial_producer_bytes_unchanged(self):self.assertEqual(e.sha(Path(p.original.__file__)),'18bb000d76258a3a5a04bbdd85a4274bbc3128bdee370c906515c5aa86653213')
if __name__=='__main__':unittest.main()
