"""Offline coordinator protocol tests. Gate-admission seams are synthetic.

The actual mutation journal/budget and strict file consumer are reused. Nothing
here is a Comparator result, a publication binding or live Zenodo evidence.
"""
import copy,datetime as dt,hashlib,importlib.util,json,py_compile,sys,tempfile,types,unittest,zipfile,io
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
GATES=next((q for q in Path(__file__).resolve().parents if (q/'methods_digest.py').is_file()),None)
if GATES is None:
 import os
 GATES=Path(os.environ['PHASE7_TEST_GATES']).resolve(strict=True)
sys.path.insert(0,str(GATES))
sys.path.insert(0,str(Path(__file__).parent))
import first_digest_publisher as p
import first_digest_state as s
import publisher_recovery as recovery
import publisher_previews as previews

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
actual_digest=load('coordinator_actual_digest',GATES/'methods_digest.py')
mut=load('coordinator_actual_mut',GATES/'phase7_mutation_baseline.py')
preserve=load('coordinator_preserve',GATES/'publication_preservation.py')
import test_publisher_guards as base
TOKEN='FAKE_OFFLINE_TOKEN_NOT_A_CREDENTIAL_123456789'

def encode(v):return p.raw_json(v)
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value if isinstance(value,bytes)else encode(value));return p.binding(path)

class FakeServerMismatch(ValueError):
 def __init__(self,report):self.report=report;super().__init__('SYNTHETIC_SERVER_MISMATCH')
class FakeSM:
 _timestamp=staticmethod(lambda value:dt.datetime.fromisoformat(value.replace('Z','+00:00')))
 transport_contract_sha256=staticmethod(lambda:'a'*64)
 def validate_new_version(self,actual,expected,**context):
  # Protocol fixture only. Existing actual server-managed rule tests remain
  # independently required; this object never runs in execute().
  left,right=copy.deepcopy(actual),copy.deepcopy(expected)
  for value in(left,right):value.pop('updated',None);value.pop('revision_id',None)
  if 'thumbnails'in right.get('links',{})and 'thumbnails'not in left.get('links',{}):
   raise FakeServerMismatch({'status':'HOLD','checks':{'derived_previews':{'status':'HOLD','reason':previews.PENDING}},'reasons':[{'rule':'derived_previews','reason':previews.PENDING}]})
  if 'thumbnails'in left.get('links',{})and 'thumbnails'not in right.get('links',{}):left['links'].pop('thumbnails')
  if left!=right:raise FakeServerMismatch({'status':'HOLD','checks':{},'reasons':[{'rule':'content_metadata','reason':'fixture change'}]})
  return {'status':'SERVER_MANAGED_READBACK_PASS','operation':'NEW_VERSION'}
 def require_links_stats(self,*args,**kwargs):return {'status':'FIXTURE_ONLY'}

class FakeDigest:
 require_write_budget=staticmethod(actual_digest.require_write_budget)
 discover_weekly_record=staticmethod(actual_digest.discover_weekly_record)
 def __init__(self,f):self.f=f;self.fresh_calls=0
 def require_publication_bound(self,package,root,**admission_callbacks):
  self.fresh_calls+=1
  if self.f.fail_gate_after is not None and self.fresh_calls>=self.f.fail_gate_after:raise ValueError('HOLD_SYNTHETIC_ADMISSION_FAILURE')
  return self.f.manifest,{'standard':'SYNTHETIC_NOT_REAL_PUBLICATION_BINDING'}
 def prewrite(self,package,root,method,when,events,*,complete_journal,budget_consumer):
  self.require_publication_bound(package,root);calculated=actual_digest.require_write_budget(events,method,when,complete=complete_journal)
  if calculated!=budget_consumer(root,method,when):raise ValueError('HOLD_ACTUAL_BUDGET_DIFFERENCE')
 def strict_readback(self,package,root,record,receipt,download,*,expected_record,metadata_consumer):
  with patch.object(actual_digest,'require_publication_bound',side_effect=self.require_publication_bound):
   return actual_digest.strict_readback(package,root,record,receipt,download,expected_record=expected_record,metadata_consumer=metadata_consumer)

class FakeAccount:
 def __init__(self,token,out,opener,*,pace):self.out=Path(out);self.out.mkdir();self.f=ACTIVE
 def complete(self,week,discover):
  # Every account read must happen under the actual journal lock.
  try:
   with p.JournalWriter(self.f.root,self.f.output/'second-lock',mut.require_events,self.f.budget):pass
  except Exception as exc:
   if 'CONCURRENT_EXECUTION'not in str(exc):raise
  else:raise AssertionError('account discovery was outside journal lock')
  if self.f.duplicate_week:raise ValueError('HOLD_WEEKLY_DIGEST_ALREADY_EXISTS')
  write(self.out/'RESULT.json',{'standard':'SYNTHETIC_DOUBLE_PASS_FIXTURE','status':'NO_EXISTING_WEEKLY_RECORD','writes':0})
  return {'status':'NO_EXISTING_WEEKLY_RECORD'}

class FakeDownloads:
 def __init__(self,token,opener,out):self.out=Path(out);self.out.mkdir(parents=True);self.public=[];self.n=0;self.f=ACTIVE
 def get(self,name,rid,expected,*,published,published_url=None):
  self.n+=1;data=self.f.uploads[name]
  if self.f.bad_download==name:data+=b'bad'
  if hashlib.sha256(data).hexdigest()!=expected['sha256']or hashlib.md5(data).hexdigest()!=expected['md5']or len(data)!=expected['size']:raise ValueError('HOLD_DOWNLOADED_EXACT_OWN_BYTES')
  path=self.out/(str(self.n)+'_'+name);p.immutable(path,data)
  if published:self.public.append({'filename':name,'url':published_url,'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'md5':hashlib.md5(data).hexdigest(),'bytes':len(data)})
  return data

class FakeTransport:
 class NoRedirect(p.urllib.request.HTTPRedirectHandler):pass
 def __init__(self,host,token,out,*,opener):self.out=Path(out);self.out.mkdir(parents=True);self.sequence=0;self.f=ACTIVE;self.f.transport=self
 def request(self,method,url,body=None,expected_sha256=None,content_type='application/json',authorized=False,accept='application/json'):
  self.sequence+=1;f=self.f;native=accept==p.NATIVE;is_mutation=method!='GET';now=dt.datetime.now(dt.timezone.utc).isoformat()
  receipt={'method':method,'url':url,'request_body_sha256':expected_sha256,'environment':'zenodo.org','accept':accept,'status':'STARTED_NO_RETRY'}
  path=self.out/f'{self.sequence:03d}_{method}.json'
  if is_mutation:
   f.calls.append((method,url));assert authorized and hashlib.sha256(body).hexdigest()==expected_sha256
   # A real, source-bound reservation already exists before fake network.
   events=mut.require_events(f.root,f.now());assert any(e['status']=='STARTED_NO_RETRY'for e in events)
   if f.uncertain_write==len(f.calls):
    receipt['status']='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY';write(path,receipt);raise RuntimeError('HOLD_TRANSPORT_UNCERTAIN_NO_RETRY')
  if method=='GET'and url=='https://zenodo.org/api/records/21971052':
   value=copy.deepcopy(f.source_native if native else f.source_legacy)
   if f.changed_source and f.calls:
    if native:value['metadata']['rights'][0]['title']={'en':'CHANGED VOCABULARY'}
    else:value['metadata']['title']='Changed source title'
  elif method=='POST'and url=='https://zenodo.org/api/deposit/depositions':
   f.created=f.creation(now);value=copy.deepcopy(f.created);predicted=f.expected_native
   f.native,f.legacy=s.initial_expected(f.created,{'id':f.rid,'revision_id':0,'expires_at':now},predicted,f.source_native,f.api,f.runtime.sm,preserve,source_legacy=f.source_legacy)
  elif method=='GET'and url=='https://zenodo.org/api/deposit/depositions/'+f.rid:value=copy.deepcopy(f.legacy)
  elif method=='GET'and url=='https://zenodo.org/api/records/'+f.rid+'/draft':value=copy.deepcopy(f.native)
  elif method=='PUT'and url=='https://zenodo.org/api/deposit/depositions/'+f.rid:
   assert json.loads(body)==f.api;value=copy.deepcopy(f.legacy)
  elif method=='PUT'and'/api/files/'in url:
   name=url.rsplit('/',1)[-1];f.uploads[name]=body;fid='00000000-0000-0000-0000-%012d'%len(f.uploads);md5=hashlib.md5(body).hexdigest()
   row={'filename':name,'filesize':len(body),'checksum':md5,'id':fid,'links':{'download':'https://zenodo.org/api/records/'+f.rid+'/draft/files/'+name+'/content','self':'https://zenodo.org/api/deposit/depositions/'+f.rid+'/files/'+fid}}
   value={'key':name,'checksum':'md5:'+md5,'size':len(body),'is_head':True,'delete_marker':False,'mimetype':'application/octet-stream'}
   approved={'name':name,'size':len(body),'md5':md5};f.native['files']['entries'][name]=s.file_from_upload(row,value,approved,f.rid);s.refresh_totals(f.native);f.legacy['files'].append(row)
   if f.native_content_mutation:f.native['metadata']['description']+='UNREVIEWED CLAIM'
   if f.preview_enabled and name=='paper.pdf':f.native['links']['thumbnails']={'250':'https://zenodo.org/api/records/'+f.rid+'/files/paper.pdf/preview'}
  elif method=='POST'and url.endswith('/actions/publish'):
   value={'id':int(f.rid),'state':'done','submitted':True,'doi':'10.5281/zenodo.'+f.rid,'conceptdoi':'10.5281/zenodo.'+f.parent,'conceptrecid':f.parent,'modified':now};f.public_native,doi,concept=s.public_projection(f.native,value,f.rid);f.public_legacy=s.public_legacy_projection(f.source_legacy,f.public_native,f.public,doi,concept)
  elif method=='GET'and url=='https://zenodo.org/api/records/'+f.rid:
   value=copy.deepcopy(f.public_native if native else f.public_legacy)
   if native:
    f.public_reads+=1
    if f.public_reads<=f.preview_pending:value['links'].pop('thumbnails',None)
    if f.public_pid_mutation:value['pids']['doi']['identifier']='10.5281/zenodo.999999'
  else:raise AssertionError('unexpected fake request '+method+' '+url)
  if is_mutation:
   value['modified']=now
   if f.legacy is not None:f.legacy['modified']=now;f.native['updated']=now
  receipt.update(status='HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE',http_status=200,response_sha256=hashlib.sha256(encode(value)).hexdigest(),response=value);write(path,receipt)
  return value

class FakeRegistration:
 def __init__(self,f):self.f=f;self.prepare_calls=0;self.consume_calls=0
 def assemble_evidence(self,**kwargs):
  import methods_digest_registration
  return methods_digest_registration.assemble_evidence(**kwargs)
 def prepare_registration(self,root,package,evidence):
  self.prepare_calls+=1
  self.f.runtime.fresh(package,self.f.plan)
  obj=json.loads(Path(evidence['path']).read_bytes())
  if self.f.registration_failure:raise ValueError('HOLD_SYNTHETIC_REGISTRATION_FAILURE')
  assert obj['record_id']==self.f.rid
  return {'standard':'SYNTHETIC_PROTOCOL_ONLY_NOT_A_REAL_REGISTRATION','public_evidence':evidence,'certifies':False}
 def require_registration(self,root,binding):
  self.consume_calls+=1;self.f.runtime.fresh(self.f.package,self.f.plan)
  return {'receipt':json.loads(Path(binding['path']).read_bytes())}
 def entity_rows(self,root,binding,ledger):
  self.require_registration(root,binding);return [{'fixture':'PROTOCOL_ONLY_NO_SSOT_WRITE'}]

ACTIVE=None
class Fixture:
 def __init__(self,*,seven=False):
  global ACTIVE
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name).resolve();self.package=self.root/'package';self.package.mkdir();self.output=self.root/'reports/verification-coverage/execution';self.calls=[];self.uploads={};self.rid='701';self.parent='700';self.legacy=None;self.native=None;self.uncertain_write=None;self.bad_download=None;self.changed_source=False;self.duplicate_week=False;self.fail_gate_after=None;self.native_content_mutation=False;self.public_pid_mutation=False;self.preview_pending=0;self.public_reads=0;self.preview_enabled=False;self.registration_failure=False
  self.now=lambda:dt.datetime.now(dt.timezone.utc).isoformat();public,before,legacy,native,template=base.fixture();before.update(title='Historical Run125 title',description='Existing UNCERTIFIED banner',doi=legacy['doi']);legacy['metadata']=copy.deepcopy(before);native['metadata']['title']=before['title'];native['parent']={'access':{'owned_by':{'user':'1591505'}}};native['custom_fields']={'legacy:communities':['viridis-canon']};self.source_legacy=legacy;self.source_native=native
  # Source public record schema remains exact; no new after-fields are trusted.
  legacy.update(conceptdoi='10.5281/zenodo.21971051',conceptrecid='21971051',created='2026-10-01T00:00:00+00:00',doi_url='https://doi.org/'+legacy['doi'],files=[],links={},modified='2026-10-01T00:00:00+00:00',owners=[{'id':'1591505'}],recid='21971052',revision=0,stats={},title=before['title'])
  self.public=public;self.before=before;self.api=p.metadata.closed_payload(public,before);self.expected_native=p.metadata.native_metadata(public,before,legacy,native,template)
  names=['paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip'];members=[('notes/README.txt',b'SYNTHETIC NOT A SCIENCE CERTIFICATE')];arc=actual_digest.archive_bytes(members)
  contents={'paper.tex':b'SYNTHETIC fixture Tex','paper.pdf':b'%PDF-SYNTHETIC fixture','metadata.json':encode(public),'METHODS_NOTES.zip':arc}
  for name,data in contents.items():write(self.package/name,data)
  ids=[r for r in p.FIRST8 if not seven or r!='Run-130'];self.manifest={'release_week':'2026-W41','source_metadata':write(self.root/'source_before.json',before),'notes':[{'run_id':rid,'certificate':{'sha256':'b'*64},'publication_binding':{'sha256':'c'*64},'policy_receipt':{'sha256':'d'*64}}for rid in ids],'public_metadata':public,'uploads':[{'filename':n,'sha256':p.sha(self.package/n),'md5':hashlib.md5(contents[n]).hexdigest(),'bytes':len(contents[n])}for n in names],'archive_members':actual_digest.member_inventory(members)}
  self.plan={'standard':'VRS-PHASE7-FIRST-DIGEST-PUBLISH-PLAN-1','status':'FROZEN_READY_NOT_EXECUTED','canonical_root':str(self.root),'package_path':str(self.package),'digest_manifest':write(self.package/'DIGEST_MANIFEST.json',self.manifest),'digest_publication_binding':write(self.package/'PUBLICATION_BINDING.json',{'standard':'SYNTHETIC_NOT_BOUND'}),'source_before_metadata':self.manifest['source_metadata'],'source_legacy':write(self.root/'source_legacy.json',legacy),'source_native':write(self.root/'source_native.json',native),'relation_vocabulary_source':write(self.root/'relation.json',{'metadata':{'related_identifiers':[{'relation_type':template}]}}),'community_mirror_proof':write(self.root/'mirror.json',{'status':'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN','public_post_publish_exact_preservation':True}),'runtime_pins':[],'expected_writes':9,'first_notes':ids}
  write(self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json',{'tree_root':str(self.root),'run_entities':[]})
  self.runtime=types.SimpleNamespace(d=FakeDigest(self),sm=FakeSM(),preservation=preserve,mut=mut,transport=types.SimpleNamespace(NoRedirect=FakeTransport.NoRedirect))
  self.budget=lambda root,method,when:actual_digest.require_write_budget(mut.require_events(root,when),method,when,complete=True);self.runtime.policy=types.SimpleNamespace(require_write_budget=self.budget);self.runtime.fresh=lambda package,plan:self.runtime.d.require_publication_bound(package,self.root);self.runtime.registration=FakeRegistration(self)
  index=self.root/p.JournalWriter.__module__.replace('.','/') if False else self.root/'reports/verification-coverage/2026-10-07/phase7-approved-audit-execution-v001/publication/MUTATION_JOURNAL_INDEX.json';index.parent.mkdir(parents=True);write(index.parent/'existing.json',{'fixture':'not an empty claimed capture'});baseline=mut.capture(self.root,self.now());bp=write(index.parent/'MUTATION_BASELINE.json',baseline);write(index,{'standard':mut.INDEX_STANDARD,'status':'ACTIVE','baseline':bp,'reservations':[],'updated_at_utc':self.now()});self.index=index;ACTIVE=self
 def creation(self,now):
  metadata=copy.deepcopy(self.api['metadata']);metadata.update(imprint_publisher='Zenodo',prereserve_doi={'doi':'10.5281/zenodo.'+self.rid,'recid':int(self.rid)})
  return {'conceptrecid':self.parent,'created':now,'files':[],'id':int(self.rid),'links':{'bucket':'https://zenodo.org/api/files/00000000-0000-0000-0000-000000000001'},'metadata':metadata,'modified':now,'owner':1591505,'record_id':int(self.rid),'state':'unsubmitted','submitted':False,'title':self.public['title']}
 def run(self,**clock_options):
  with patch.object(p,'require_module_pins',return_value=[]):return p._execute(self.root,self.package,self.plan,self.output,TOKEN,self.runtime,account_factory=FakeAccount,transport_factory=FakeTransport,download_factory=FakeDownloads,clock=self.now,**clock_options)
 def close(self):self.t.cleanup()

class CoordinatorTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_nine_writes_full_offline_flow_exact_budget(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(v['writes'],9);self.assertEqual(len(self.f.calls),9);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],9)
  self.assertEqual([m for m,_ in self.f.calls],['POST']+['PUT']*7+['POST']);self.assertEqual(len(list((self.f.output/'checkpoints').glob('*.json'))),20)
 def test_no_duplicate_transport_receipt_echo(self):
  self.f.run();ref=json.loads((self.f.output/'OWN_CREATION_RECEIPT.json').read_bytes());self.assertNotIn('environment',ref);self.assertEqual(ref['status'],'REFERENCE_ONLY_NOT_ANOTHER_MUTATION')
 def test_exact_seven_cleared_notes_allowed(self):
  self.f.close();self.f=Fixture(seven=True);v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertNotIn('Run-130',v['notes'])
 def test_wrong_cohort_holds_before_any_write(self):
  self.f.plan['first_notes']=list(p.FIRST8[:-1])
  with self.assertRaises(p.PublishHold):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_wrong_week_title_holds_before_any_write(self):
  self.f.manifest['public_metadata']['title']='Changed';self.f.plan['digest_manifest']=write(self.f.package/'DIGEST_MANIFEST.json',self.f.manifest)
  with self.assertRaises(p.PublishHold):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_duplicate_week_under_lock_holds_zero_writes(self):
  self.f.duplicate_week=True;v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.calls,[]);self.assertIn('ALREADY_EXISTS',v['failure'])
 def test_uncertain_creation_slot_spent_no_retry(self):
  self.f.uncertain_write=1;v=self.f.run();self.assertEqual(v['writes'],1);self.assertEqual(len(self.f.calls),1);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],1);self.assertIsNone(v['record_id'])
 def test_uncertain_upload_slot_spent_no_publish(self):
  self.f.uncertain_write=4;v=self.f.run();self.assertEqual(v['writes'],4);self.assertEqual(len(self.f.calls),4);self.assertFalse(any(url.endswith('/publish')for _,url in self.f.calls))
 def test_source_title_change_holds_without_adoption(self):
  self.f.changed_source=True;v=self.f.run();self.assertEqual(v['writes'],1);self.assertIn('FRESH_SOURCE',v['failure'])
 def test_changed_download_holds_before_next_write(self):
  self.f.bad_download='paper.pdf';v=self.f.run();self.assertEqual(v['writes'],4);self.assertIn('DOWNLOADED',v['failure'])
 def test_gate_admission_failure_holds_no_weak_pass(self):
  self.f.fail_gate_after=1;v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(v['status'],'HOLD')
 def test_replay_same_output_is_refused(self):
  self.f.run()
  with self.assertRaises(p.PublishHold):self.f.run()
  self.assertEqual(len(self.f.calls),9)
 def test_public_envelope_uses_original_post_and_closed_context(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);e=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());ctx=json.loads(Path(e['server_context']['path']).read_bytes());self.assertEqual(ctx['operation'],'NEW_VERSION');self.assertEqual(ctx['phase'],'PUBLISHED');self.assertEqual(len(e['public_downloads']),6);self.assertIn('/transport/',e['own_publish_receipt']['path']);self.assertEqual(len(e['notes']),8)
 def test_payload_encoding_source_fields_preserved(self):
  self.f.run();md=json.loads((self.f.output/'API_METADATA_PAYLOAD.json').read_bytes())['metadata'];self.assertEqual(md['upload_type'],'publication');self.assertEqual(md['publication_type'],'preprint');self.assertEqual(md['license'],'cc-by-4.0');self.assertEqual(md['creators'],self.f.before['creators']);self.assertEqual(md['communities'],self.f.before['communities']);self.assertNotIn('resource_type',md)
 def test_checkpoint_recovery_is_read_only_and_no_replay(self):
  self.f.uncertain_write=2;v=self.f.run();r=recovery.inspect_checkpoints(self.f.output,p.read_regular);self.assertEqual(r['attempted_mutations_at_least'],v['writes']);self.assertFalse(r['replay_authorized']);self.assertEqual(len(self.f.calls),2)

class RecoveryMustFailTests(unittest.TestCase):
 setUp=CoordinatorTests.setUp
 tearDown=CoordinatorTests.tearDown
 def test_spent_reservation_before_latest_checkpoint_retained(self):
  self.f.uncertain_write=1;self.f.run()
  for path in (self.f.output/'checkpoints').glob('*.json'):
   if not path.name.startswith('001_'):path.unlink()
  v=recovery.inspect_checkpoints(self.f.output,p.read_regular);self.assertEqual(v['attempted_mutations_at_least'],1);self.assertFalse(v['replay_authorized'])
 def test_mutated_optional_transport_binding_fails(self):
  self.f.uncertain_write=1;self.f.run();path=next((self.f.output/'transport').glob('*_POST.json'));path.write_bytes(path.read_bytes()+b' ')
  with self.assertRaises(ValueError):recovery.inspect_checkpoints(self.f.output,p.read_regular)
 def test_foreign_checkpoint_optional_path_fails(self):
  self.f.uncertain_write=1;self.f.run();path=sorted((self.f.output/'checkpoints').glob('*.json'))[-1];row=json.loads(path.read_bytes());row['transport_receipt']=write(self.f.root/'foreign.json',{}) ;write(path,row)
  with self.assertRaises(ValueError):recovery.inspect_checkpoints(self.f.output,p.read_regular)
 def test_foreign_record_creation_anchor_fails(self):
  self.f.uncertain_write=2;self.f.run();path=sorted((self.f.output/'checkpoints').glob('*.json'))[-1];row=json.loads(path.read_bytes());row['own_record_id']='999';write(path,row)
  with self.assertRaises(ValueError):recovery.inspect_checkpoints(self.f.output,p.read_regular)

class PinnedImportTests(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name).resolve();self.name='coordinator_pinned_fixture';self.path=self.root/(self.name+'.py')
 def tearDown(self):sys.modules.pop(self.name,None);self.t.cleanup()
 def test_stale_pyc_is_ignored_for_pinned_import(self):
  self.path.write_text('VALUE = 1\n');py_compile.compile(str(self.path),doraise=True);st=self.path.stat();self.path.write_text('VALUE = 2\n');import os;os.utime(self.path,ns=(st.st_atime_ns,st.st_mtime_ns));finder=p.PinnedFinder(self.root,[{'name':self.path.name,'path':str(self.path),'sha256':p.sha(self.path)}]);sys.meta_path.insert(0,finder)
  try:import importlib;m=importlib.import_module(self.name);self.assertEqual(m.VALUE,2)
  finally:sys.meta_path.remove(finder)
 def test_changed_pinned_import_holds(self):
  self.path.write_text('VALUE = 1\n');expected=p.sha(self.path);self.path.write_text('VALUE = 2\n');loader=p.PinnedLoader(self.path,expected)
  with self.assertRaises(p.PublishHold):loader.exec_module(types.ModuleType(self.name))
 def test_unlisted_own_module_holds(self):
  self.path.write_text('VALUE = 1\n');sys.path.insert(0,str(self.root));finder=p.PinnedFinder(self.root,[])
  try:
   with self.assertRaises(p.PublishHold):finder.find_spec(self.name)
  finally:sys.path.remove(str(self.root))




class MoreCoordinatorTests(unittest.TestCase):
 setUp=CoordinatorTests.setUp
 tearDown=CoordinatorTests.tearDown
 def test_scientific_metadata_change_stops_before_next_write(self):
  self.f.native_content_mutation=True;v=self.f.run();self.assertEqual(v['writes'],3);self.assertEqual(v['status'],'HOLD');self.assertFalse(any(url.endswith('/publish')for _,url in self.f.calls))
 def test_foreign_public_pid_stops_after_publish(self):
  self.f.public_pid_mutation=True;v=self.f.run();self.assertEqual(v['writes'],9);self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertFalse((self.f.output/'FINAL_READBACK_ENVELOPE.json').exists())
 def test_known_preview_pending_only_get_polls(self):
  self.f.preview_enabled=True;self.f.preview_pending=2;v=self.f.run(sleep=lambda _:None);self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(len(self.f.calls),9);index=json.loads((self.f.output/'PREVIEW_POLL_INDEX.json').read_bytes());self.assertEqual(len(index['polls']),2);e=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());ctx=json.loads(Path(e['server_context']['path']).read_bytes());self.assertNotEqual(Path(e['native_public_get_receipt']['path']).name,ctx['revision_evidence']['first_native_get_receipt_name'])
 def test_preview_deadline_does_not_publish_again(self):
  self.f.preview_enabled=True;self.f.preview_pending=1000;clock={'value':0}
  def sleep(seconds):clock['value']+=seconds
  v=self.f.run(monotonic=lambda:clock['value'],sleep=sleep);self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(v['writes'],9);self.assertIn('TEN_MINUTE',v['failure']);self.assertEqual(clock['value'],600);self.assertFalse((self.f.output/'FINAL_READBACK_ENVELOPE.json').exists());self.assertTrue((self.f.output/'preview-polls/001.json').exists())
 def test_preview_with_main_metadata_change_does_not_poll(self):
  self.f.preview_enabled=True;self.f.public_pid_mutation=True;self.f.preview_pending=10;v=self.f.run(sleep=lambda _:None);self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(self.f.public_reads,1)
 def test_day_budget_two_used_blocks_creation(self):
  for number in range(2):write(self.f.index.parent/(str(number)+'_prior.json'),{'method':'PUT','url':'https://zenodo.org/api/deposit/depositions/888','request_body_sha256':'b'*64,'environment':'zenodo.org','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'})
  v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('NINE_DAILY_SLOTS',v['failure'])
 def test_one_prior_slot_allows_exact_tenth_total(self):
  write(self.f.index.parent/'prior.json',{'method':'PUT','url':'https://zenodo.org/api/deposit/depositions/888','request_body_sha256':'b'*64,'environment':'zenodo.org','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'});v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(len(mut.require_events(self.f.root,self.f.now())),10)

class DraftFilenameAndStateTests(unittest.TestCase):
 def test_draft_order_uses_full_field_preserving_adapter(self):
  rows=[{'filename':str(n)+'.json','filesize':n,'checksum':'a'*32,'id':str(n),'links':{'self':'own'}}for n in range(5)];v=preserve.require_file_preservation(s.private_file_compare_rows(rows[::-1]),s.private_file_compare_rows(rows));self.assertEqual(v['mode'],'FILENAME_KEYED_SET')
 def test_draft_checksum_change_fails(self):
  before=[{'filename':'paper.pdf','checksum':'a'*32,'filesize':1,'id':'one','links':{}}];after=copy.deepcopy(before);after[0]['checksum']='b'*32
  with self.assertRaises(Exception):preserve.require_file_preservation(s.private_file_compare_rows(after),s.private_file_compare_rows(before))
 def test_draft_other_field_change_fails(self):
  before=[{'filename':'paper.pdf','checksum':'a'*32,'filesize':1,'id':'one','links':{}}];after=copy.deepcopy(before);after[0]['id']='two'
  with self.assertRaises(Exception):preserve.require_file_preservation(s.private_file_compare_rows(after),s.private_file_compare_rows(before))
 def test_draft_conflicting_key_fails(self):
  with self.assertRaises(Exception):s.private_file_compare_rows([{'filename':'paper.pdf','key':'other.pdf'}])
 def test_publish_projection_preserves_prior_source_preview(self):
  before={'pids':{'doi':{'identifier':'10.5281/zenodo.701'}},'parent':{'id':'700'},'links':{'thumbnails':{'250':'approved source'}},'files':{'entries':{'paper.pdf':{'key':'paper.pdf','links':{'preview':'approved source'}}}}};response={'id':701,'state':'done','submitted':True,'doi':'10.5281/zenodo.701','conceptdoi':'10.5281/zenodo.700','conceptrecid':'700'};v,_,_=s.public_projection(before,response,'701');self.assertEqual(v['links']['thumbnails'],before['links']['thumbnails']);self.assertEqual(v['files']['entries']['paper.pdf']['links']['preview'],'approved source')

class RegistrationIntegrationTests(unittest.TestCase):
 setUp=CoordinatorTests.setUp
 tearDown=CoordinatorTests.tearDown
 def test_original_evidence_adapter_schema_and_exact_downloads(self):
  import methods_digest_registration as g
  result=self.f.run();self.assertEqual(result['status'],'PUBLISHED_STRICT_READBACK_PASS',result)
  e=json.loads((self.f.output/'REGISTRATION_EVIDENCE.json').read_bytes())
  self.assertEqual(set(e),g.EVIDENCE_FIELDS);self.assertEqual(e['status'],'SOURCE_BOUND_READBACK_INPUTS')
  public=json.loads(Path(e['public_legacy_receipt']['path']).read_bytes())['response']
  byname={f['key']:f for f in public['files']}
  self.assertEqual(len(e['downloads']),6)
  for row in e['downloads']:
   self.assertEqual(row['url'],byname[row['filename']]['links']['self'])
   self.assertEqual(row['binding']['sha256'],p.sha(row['binding']['path']))
  self.assertEqual(result['registration_status'],'FRESH_CONSUMER_PASS_NOT_SSOT_WRITTEN')
  self.assertFalse(json.loads((self.f.output/'REGISTRATION_ROWS.json').read_bytes())['certifies'])
 def test_fresh_source_receipts_not_draft_lineage(self):
  self.f.run();e=json.loads((self.f.output/'REGISTRATION_EVIDENCE.json').read_bytes())
  for field,accept in [('source_legacy_receipt','application/json'),('source_native_receipt',p.NATIVE)]:
   receipt=json.loads(Path(e[field]['path']).read_bytes())
   self.assertEqual(receipt['method'],'GET');self.assertEqual(receipt['url'],'https://zenodo.org/api/records/21971052');self.assertEqual(receipt['accept'],accept)
  self.assertIn('/transport/',e['own_publish_receipt']['path'])
 def test_registration_hold_after_publish_never_retries(self):
  self.f.registration_failure=True;r=self.f.run()
  self.assertEqual(r['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(r['writes'],9);self.assertIn('REGISTRATION',r['failure']);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists());self.assertEqual(len(self.f.calls),9)
 def test_actual_source_community_predicate_preserves_equality(self):
  import methods_digest_registration as g
  expected=g.source_custom_fields(self.f.public,self.f.source_legacy,self.f.source_native)
  self.assertEqual(expected,{'legacy:communities':['viridis-canon']});self.f.run()
  native=json.loads((self.f.output/'EXPECTED_NATIVE_PUBLIC.json').read_bytes());self.assertEqual(native['custom_fields'],expected)
 def test_unlisted_source_custom_field_holds_before_write(self):
  self.f.source_native['custom_fields']['extra']='unapproved';self.f.plan['source_native']=write(self.f.root/'source_native.json',self.f.source_native)
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_source_membership_mismatch_holds_before_write(self):
  self.f.source_native['custom_fields']['legacy:communities']=['other'];self.f.plan['source_native']=write(self.f.root/'source_native.json',self.f.source_native)
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_download_refuses_inferred_foreign_url(self):
  downloads=p.Downloads(TOKEN,None,self.f.root/'never-network')
  with self.assertRaises(p.PublishHold):downloads.get('paper.pdf',self.f.rid,{'size':1,'sha256':'a'*64,'md5':'a'*32},published=True,published_url='https://zenodo.org/api/records/999/files/paper.pdf/content')
 def test_download_requires_actual_public_link(self):
  downloads=p.Downloads(TOKEN,None,self.f.root/'never-network')
  with self.assertRaises(p.PublishHold):downloads.get('paper.pdf',self.f.rid,{'size':1,'sha256':'a'*64,'md5':'a'*32},published=True)
 def test_adapter_does_not_accept_cached_pass_field(self):
  import methods_digest_registration as g
  self.f.run();e=json.loads((self.f.output/'REGISTRATION_EVIDENCE.json').read_bytes())
  self.assertNotIn('accepted',e);self.assertNotIn('PASS',e.values());self.assertEqual(self.f.runtime.registration.prepare_calls,1);self.assertEqual(self.f.runtime.registration.consume_calls,2)

if __name__=='__main__':unittest.main()

