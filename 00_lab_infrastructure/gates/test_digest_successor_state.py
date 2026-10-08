from pathlib import Path
from copy import deepcopy
import ast,hashlib,importlib.util,json,sys,unittest
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
# Existing portable fixtures remain scientific fixtures, never network proof.
G=HERE if (HERE/'methods_digest.py').is_file()else HERE.parent
if not(G/'methods_digest.py').is_file():G=Path('/private/tmp/viridis-phase7-source-bound-public-state/00_lab_infrastructure/gates')
sys.path.extend([str(G),str(Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001/first-digest-three-file-executor-v001'))])
import digest_public_state as p
import digest_public_state_legacy_b5545 as old
import digest_successor_state as s
from test_digest_public_state import StateFixture,mirror_proof
class SuccessorFixture:
 def __init__(self):
  self.f=StateFixture();self.native=deepcopy(self.f.native);self.legacy=deepcopy(self.f.legacy);self.before=deepcopy(self.f.before)
  self.native['parent']['id']=self.f.parent;self.native['parent']['access']={'owned_by':{'user':'3974'}};self.native['access']=deepcopy(self.before['access']);self.native['custom_fields']={};self.native['links']=old.canonical_links(self.native['id'],self.f.parent)
  self.native['versions']['index']=1;self.native['versions']['is_latest_draft']=True
  self.legacy['conceptrecid']=self.f.parent;self.legacy['conceptdoi']='10.5281/zenodo.'+self.f.parent;self.legacy['metadata']['relations']['version'][0].update(index=0,parent={'pid_type':'recid','pid_value':self.f.parent});self.legacy['links']=deepcopy(self.native['links'])
  self.before['custom_fields']={};self.before['parent']=deepcopy(self.native['parent']);self.before['versions']['index']=2
 def predict(self):return s.predict_native(self.f.public,self.legacy,self.native,self.before,self.f.created,self.f.reserved,self.f.published)
 def close(self):self.f.close()
class SuccessorTests(unittest.TestCase):
 def setUp(self):self.f=SuccessorFixture();self.addCleanup(self.f.close)
 def test_sameconcept_expected_pub_closes_metadata_access_owner_graph_and_ordinal(self):
  v=self.f.predict();self.assertEqual(v['versions']['index'],2);self.assertEqual(v['parent']['id'],self.f.f.parent);self.assertEqual(v['metadata'],self.f.before['metadata']);self.assertEqual(v['access'],self.f.native['access']);self.assertEqual(v['parent']['communities'],self.f.native['parent']['communities']);self.assertEqual(v['custom_fields'],{});self.assertFalse('certifies'in v)
 def test_existing_draft_absent_nativeordinal_is_sourcepredicted(self):self.f.before['versions']['index']=None;self.assertEqual(self.f.predict()['versions']['index'],2)
 def test_wrong_parent_owner_access_or_reusedordinal_neverpasses(self):
  for fn in[lambda x:x.before['parent'].__setitem__('id','123456'),lambda x:x.before['parent']['access']['owned_by'].__setitem__('user','123456'),lambda x:x.before['access'].__setitem__('record','restricted'),lambda x:x.before['versions'].__setitem__('index',1),lambda x:x.native['versions'].__setitem__('index',True)]:
   with self.subTest(fn=fn):
    f=SuccessorFixture();self.addCleanup(f.close);fn(f);self.assertRaises(ValueError,f.predict)
 def test_community_every_sourcegraph_field_exact_or_fail(self):
  for fn in[lambda x:x.before['parent']['communities'].__setitem__('default','wrong'),lambda x:x.before['parent']['communities']['entries'][0]['metadata'].__setitem__('description','changed'),lambda x:x.before.__setitem__('custom_fields',{'other:claim':'PASS'}),lambda x:x.f.public.__setitem__('communities',[])]:
   with self.subTest(fn=fn):
    f=SuccessorFixture();self.addCleanup(f.close);fn(f);self.assertRaises(ValueError,f.predict)
 def test_unknown_or_foreign_source_link_rejected(self):
  for key in old.canonical_links(self.f.native['id'],self.f.f.parent):
   f=SuccessorFixture();self.addCleanup(f.close);f.native['links'][key]='https://foreign.test/';self.assertRaises(ValueError,f.predict)
 def test_sameconcept_dispatcher_community_predicts_exact_original_source(self):self.assertEqual(p.community_fields(self.f.f.public,self.f.legacy,self.f.native,self.f.before),({},self.f.native['parent']['communities']))
 def test_original_distinct_parent_community_rules_remain_strict(self):
  f=StateFixture();self.addCleanup(f.close);self.assertEqual(p.community_fields(f.public,f.legacy,f.native,f.before),old.community_fields(f.public,f.legacy,f.native,f.before));f.before['parent']['communities']=deepcopy(f.native['parent']['communities']);self.assertRaises(ValueError,p.community_fields,f.public,f.legacy,f.native,f.before)
 def test_original_current_and_exact_historical_contexts_still_consume(self):
  f=StateFixture();self.addCleanup(f.close);new=f.consume();f.context=old.assemble_context(record_id=f.rid,**f.roles);legacy=f.consume();self.assertEqual(new,legacy)
 def test_unknown_context_producer_shape_or_standard_rejected(self):
  for key,val in[('standard','UNKNOWN'),('producer_sha256','a'*64),('phase','DRAFT'),('extra',True)]:
   f=StateFixture();self.addCleanup(f.close);f.context=old.assemble_context(record_id=f.rid,**f.roles);f.context[key]=val;self.assertRaises(ValueError,f.consume)
 def test_new_context_missing_anyrole_or_fake_binding_is_hold(self):
  roles={k:{'path':'/private/tmp/fixture/'+k,'sha256':'a'*64}for k in s.ROLES};c=s.assemble_context(record_id='999999',**roles)
  for name in s.ROLES:
   bad=deepcopy(c);bad['source_bindings'].pop(name);self.assertRaises(ValueError,s.consume_context,bad,load=lambda x:{},public={},evidence_sources={})
  roles['creation_receipt']['unknown']=1;self.assertRaises(ValueError,s.assemble_context,record_id='999999',**roles)
 def test_mirror_proof_all_existing_decisive_checks_remain(self):
  s.require_mirror_proof(mirror_proof())
  for name in mirror_proof()['checks']:
   m=mirror_proof();m['checks'][name]=False;self.assertRaises(ValueError,s.require_mirror_proof,m)
 def test_original_raw_legacy_producer_and_all_original_definitions_preserved(self):
  raw=(HERE/'digest_public_state_legacy_b5545.py').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38')
  oldtext=raw.decode();newtext=(HERE/'digest_public_state.py').read_text();self.assertTrue(newtext.startswith(oldtext));before={n.name:ast.get_source_segment(oldtext,n)for n in ast.parse(oldtext).body if isinstance(n,ast.FunctionDef)}
  nodes=ast.parse(newtext).body
  for name,body in before.items():self.assertEqual(body,ast.get_source_segment(newtext,next(n for n in nodes if isinstance(n,ast.FunctionDef)and n.name==name)))
 def test_no_Lean_transport_or_fake_status_implemented(self):
  raw=(HERE/'digest_successor_state.py').read_text();self.assertNotIn('urlopen(',raw);self.assertNotIn('subprocess',raw);self.assertNotIn('CERTIFIED',raw);self.assertIn('registration.require_registration(',raw)
 def test_first_legacy_requires_explicit_bound_source(self):
  self.assertRaises(ValueError,s.first_legacy_receipt_from_creation,{},root=HERE);b={'path':'/private/tmp/actual_GET.json','sha256':'a'*64};self.assertEqual(s.first_legacy_receipt_from_creation({'first_owned_legacy_draft':b},root=HERE),b)
class InitialCreationTests(unittest.TestCase):
 def fixture(self):
  f=SuccessorFixture();self.addCleanup(f.close);src=f.native;sl=f.legacy;rid=f.f.rid;parent=f.f.parent
  public={'title':'Viridis Methods Digest — 2026-W41','creators':[{'name':'Hart, Justin D.'}],'license':{'id':'cc-by-4.0'},'access_right':'open','communities':[{'id':'viridis-canon'}],'language':'eng','resource_type':{'type':'publication','subtype':'preprint','title':'Preprint'},'description':'Exact old seven scope','publication_date':'2026-10-07','keywords':['old-seven']}
  sl['metadata']={**deepcopy(public),'doi':sl['doi'],'relations':sl['metadata']['relations']}
  src['metadata']={'title':public['title'],'publisher':'Zenodo'};src['files']={'enabled':True,'count':1,'total_bytes':10,'order':[],'entries':{'paper.pdf':{'access':{'hidden':False},'key':'paper.pdf','id':'11111111-1111-4111-8111-111111111111','size':10,'checksum':'md5:'+'a'*32,'metadata':{},'ext':'pdf','mimetype':'application/pdf','storage_class':'L','links':{'self':'https://zenodo.org/api/records/'+src['id']+'/files/paper.pdf','content':'https://zenodo.org/api/records/'+src['id']+'/files/paper.pdf/content'}}}}
  from digest_metadata import closed_payload
  from first_digest_state import encode_api_communities
  md=encode_api_communities(closed_payload(public,public))['metadata'];md['prereserve_doi']={'doi':'10.5281/zenodo.'+rid,'recid':int(rid)};md['imprint_publisher']='Zenodo'
  created={'conceptdoi':'10.5281/zenodo.'+parent,'conceptrecid':parent,'created':'2026-10-08T12:00:00Z','modified':'2026-10-08T12:00:00Z','id':int(rid),'record_id':int(rid),'owner':3974,'state':'unsubmitted','submitted':False,'title':public['title'],'metadata':md,'files':[{'id':'11111111-1111-4111-8111-111111111111','filename':'paper.pdf','filesize':10,'checksum':'a'*32,'links':{'self':'https://zenodo.org/api/deposit/depositions/'+rid+'/files/11111111-1111-4111-8111-111111111111','download':'https://zenodo.org/api/records/'+rid+'/draft/files/paper.pdf/content'}}],'links':{'latest_draft':'https://zenodo.org/api/deposit/depositions/'+rid,'publish':'https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish'}}
  r={'environment':'zenodo.org','method':'POST','url':'https://zenodo.org/api/deposit/depositions/'+src['id']+'/actions/newversion','http_status':201,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':'a'*64,'request_body_sha256':'b'*64,'response':created}
  first={'id':rid,'revision_id':0,'expires_at':created['created']}
  return f,r,first
 def test_initial_prediction_uses_source_science_and_genuine_ack_only(self):
  f,r,first=self.fixture();expected,legacy=s.initial_newversion_projection(f.legacy,f.native,r,r['response'],first);self.assertEqual(expected['metadata'],f.native['metadata']);self.assertEqual(expected['parent'],f.native['parent']);self.assertEqual(expected['versions']['index'],2);self.assertEqual(legacy,r['response']);self.assertEqual(expected['files']['entries']['paper.pdf']['checksum'],'md5:'+'a'*32)
 def test_untrusted_after_scientific_values_do_not_become_expected(self):
  f,r,first=self.fixture();first.update(metadata={'title':'Invented stronger claim'},access={'record':'restricted'},files={'entries':{}});e,_=s.initial_newversion_projection(f.legacy,f.native,r,r['response'],first);self.assertEqual(e['metadata'],f.native['metadata']);self.assertEqual(set(e['files']['entries']),{'paper.pdf'});self.assertNotEqual(e['access'],first['access'])
 def test_every_initial_science_chain_ack_mismatch_rejected(self):
  cases=[lambda f,r,n:r['response']['metadata'].__setitem__('description','new claim'),lambda f,r,n:r['response'].__setitem__('title','other'),lambda f,r,n:r['response'].__setitem__('owner',99),lambda f,r,n:r['response'].__setitem__('conceptrecid','1234'),lambda f,r,n:r['response']['files'][0].__setitem__('checksum','f'*32),lambda f,r,n:r['response']['files'][0].__setitem__('filesize',11),lambda f,r,n:r['response']['files'][0].__setitem__('id','wrong'),lambda f,r,n:r['response']['files'].append(deepcopy(r['response']['files'][0])),lambda f,r,n:r.__setitem__('http_status',200),lambda f,r,n:r.__setitem__('url','https://zenodo.org/api/deposit/depositions'),lambda f,r,n:n.__setitem__('revision_id',True),lambda f,r,n:n.__setitem__('expires_at','2026-10-08T12:01:00Z')]
  for fn in cases:
   with self.subTest(fn=fn):
    f,r,n=self.fixture();fn(f,r,n);self.assertRaises(ValueError,s.initial_newversion_projection,f.legacy,f.native,r,r['response'],n)
 def test_unknown_inherited_metadata_field_is_rejected(self):
  f,r,n=self.fixture();f.legacy['metadata']['scientific_claim']='stronger';self.assertRaises(ValueError,s.initial_newversion_projection,f.legacy,f.native,r,r['response'],n)

class CompleteContextTests(InitialCreationTests):
 # These tests exercise constructors and closed selectors only. The mocked
 # predecessor admission is not a science/publication pass or network receipt.
 def context_fixture(self):
  from test_digest_public_state import save,receipt
  from unittest.mock import patch
  f,r,n=self.fixture();root=f.f.root;oldid=f.native['id'];sid='23226761';f.native['id']=sid;f.native['pids']['doi']['identifier']='10.5281/zenodo.'+sid;f.native['pids']['oai']['identifier']='oai:zenodo.org:'+sid;f.native['links']=old.canonical_links(sid,f.f.parent);f.legacy.update(id=int(sid),doi='10.5281/zenodo.'+sid,recid=sid,doi_url='https://doi.org/10.5281/zenodo.'+sid,links=deepcopy(f.native['links']));f.legacy['metadata']['doi']=f.legacy['doi'];r['url']='https://zenodo.org/api/deposit/depositions/'+sid+'/actions/newversion'
  initial,fl=s.initial_newversion_projection(f.legacy,f.native,r,r['response'],n);pub={k:deepcopy(v)for k,v in f.legacy['metadata'].items()if k not in('doi','relations')};pub['description']='49 new separately scoped notes; prior seven retained on the predecessor'
  before=deepcopy(initial);before['metadata']['description']=pub['description'];before['links']={}
  reserve={'id':f.f.rid,'parent':{'id':f.f.parent},'pids':deepcopy(before['pids'])}
  bindings={'source_legacy_receipt':receipt(root/'source_legacy.json','GET','https://zenodo.org/api/records/'+sid,f.legacy),'source_native_receipt':receipt(root/'source_native.json','GET','https://zenodo.org/api/records/'+sid,f.native,p.NATIVE_ACCEPT),'source_native_before_create':receipt(root/'source_before_create.json','GET','https://zenodo.org/api/records/'+sid,f.native,p.NATIVE_ACCEPT),'first_own_native_draft':receipt(root/'transport/003_GET.json','GET','https://zenodo.org/api/records/'+f.f.rid+'/draft',initial,p.NATIVE_ACCEPT),'first_own_legacy_draft':receipt(root/'transport/002_GET.json','GET','https://zenodo.org/api/deposit/depositions/'+f.f.rid,fl),'before_publish_native_receipt':receipt(root/'transport/027_GET.json','GET','https://zenodo.org/api/records/'+f.f.rid+'/draft',before,p.NATIVE_ACCEPT),'creation_receipt':save(root/'transport/001_POST.json',r),'reservation_receipt':receipt(root/'reserve.json','POST','https://zenodo.org/api/records/'+f.f.rid+'/draft/pids/doi',reserve,p.NATIVE_ACCEPT,201),'publish_receipt':receipt(root/'transport/028_POST.json','POST','https://zenodo.org/api/deposit/depositions/'+f.f.rid+'/actions/publish',f.f.published,code=202),'mirror_proof':save(root/'mirror.json',mirror_proof()),'predecessor_registration':save(root/'predecessor.json',{'not_an_actual_admission':'unit-test-constructor'}),'successor_digest_manifest':save(root/'successor_manifest.json',{'release_week':'2026-W41','public_metadata':pub,'notes':[{'run_id':v}for v in sorted(s.NEW_49)]})}
  context=s.assemble_context(record_id=f.f.rid,**bindings);e={k:bindings[k]for k in('source_legacy_receipt','source_native_receipt')};e['own_publish_receipt']=bindings['publish_receipt']
  def load(b):
   raw=Path(b['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),b['sha256']);return json.loads(raw)
  admitted={'receipt':{'record_id':sid,'release_week':'2026-W41','children':[{'run_id':v}for v in sorted(s.OLD_SEVEN)]}}
  return root,context,pub,e,load,admitted
 def consume(self,ctx,pub,e,load,admitted):
  from unittest.mock import patch
  with patch('methods_digest_registration.require_registration',return_value=admitted):return p.consume_context(ctx,load=load,public=pub,evidence_sources=e)
 def test_complete_newcontext_predicts_sameconcept_without_any_admissionflag(self):
  root,c,public,e,load,a=self.context_fixture();v=self.consume(c,public,e,load,a);self.assertEqual(v['native']['versions']['index'],2);self.assertEqual(v['legacy_relation']['version'][0]['index'],1);self.assertEqual(v['record_id'],'999999');self.assertNotIn('status',v);self.assertNotIn('certifies',v)
 def test_complete_newcontext_missing_historical_seven_or_wrong_noteids_is_hold(self):
  for mutation in['prior','future','collision','week','beforeunknown','firstchecksum','publishurl']:
   with self.subTest(mutation=mutation):
    root,c,pub,e,load,a=self.context_fixture()
    if mutation=='prior':a['receipt']['children'].pop()
    else:
     role={'future':'successor_digest_manifest','collision':'successor_digest_manifest','week':'successor_digest_manifest','beforeunknown':'before_publish_native_receipt','firstchecksum':'first_own_native_draft','publishurl':'publish_receipt'}[mutation];b=c['source_bindings'][role];x=json.loads(Path(b['path']).read_bytes())
     if mutation=='future':x['notes'][0]['run_id']='Run-189'
     elif mutation=='collision':x['notes'][0]['run_id']='Run-125'
     elif mutation=='week':x['release_week']='2026-W42'
     elif mutation=='beforeunknown':x['response']['unclassified_science']='stronger'
     elif mutation=='firstchecksum':x['response']['files']['entries']['paper.pdf']['checksum']='md5:'+'f'*32
     elif mutation=='publishurl':x['url']='https://zenodo.org/api/deposit/depositions/999998/actions/publish'
     raw=(json.dumps(x,sort_keys=True,indent=2)+'\n').encode();Path(b['path']).write_bytes(raw);b['sha256']=hashlib.sha256(raw).hexdigest()
    self.assertRaises(ValueError,self.consume,c,pub,e,load,a)

if __name__=='__main__':unittest.main()
