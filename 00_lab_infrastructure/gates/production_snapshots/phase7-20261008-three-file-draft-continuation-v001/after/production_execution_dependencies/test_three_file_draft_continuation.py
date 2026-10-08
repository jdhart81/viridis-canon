"""Offline known-three-file continuation. Fixture admission is not live evidence.

The original real complete mutation accounting, NY-day cap and strict file
readback remain in use. No test executes external requests or certificates.
"""
import copy,datetime as dt,hashlib,json,os,sys,types,unittest,urllib.request
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import test_coordinator as c
import test_existing_draft_recovery as old
import test_uploaded_draft_continuation as prior
import first_digest_uploaded_draft as ud
import first_digest_three_file_draft as r
import three_file_draft_continuation as tc
import owned_archive_wait as aw
import uploaded_draft_continuation as uc
import reserved_draft_continuation as rc
import draft_reservation as dr
import first_digest_publisher as p

class ThreeFileTransport(prior.UploadedTransport):
 def request(self,method,url,*args,**kwargs):
  result=super().request(method,url,*args,**kwargs)
  if method=='PUT'and url.endswith('/METHODS_NOTES.zip'):
   path=self.out/f'{self.sequence:03d}_PUT.json';obj=json.loads(path.read_bytes());obj['http_status']=200 if getattr(self.f,'archive_http200',False)else 201;c.write(path,obj)
  return result

class Fixture(prior.Fixture):
 def __init__(self):
  # Put the immutable old five attempts on the preceding NY day. The actual
  # consumer still reads all history; only today's two count toward its cap.
  yesterday=dt.datetime.now(ZoneInfo('America/New_York'))-dt.timedelta(days=1)
  oldtime=yesterday.astimezone(dt.timezone.utc)
  class Earlier(dt.datetime):
   @classmethod
   def now(cls,tz=None):return oldtime.astimezone(tz)if tz else oldtime.replace(tzinfo=None)
  with patch.object(c,'dt',types.SimpleNamespace(datetime=Earlier,timezone=dt.timezone)):
   super().__init__()
  for path in self.root.rglob('*.json'):
   obj=json.loads(path.read_bytes())
   if obj.get('environment')=='zenodo.org'and obj.get('method')in{'POST','PUT'}:
    stamp=oldtime.timestamp()+1;os.utime(path,(stamp,stamp))
  self.runtime.root=self.root
  source=self.root/'reports/verification-coverage/old-three-files';source.mkdir()
  inventory=[]
  for name in('paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
   data=(self.package/name).read_bytes();inventory.append(dict(name=name,path=str(self.package/name),size=len(data),sha256=hashlib.sha256(data).hexdigest(),md5=hashlib.md5(data).hexdigest()))
  self.inventory=c.write(source/'APPROVED_SIX_FILES.json',{'files':inventory})
  transport=prior.UploadedTransport('zenodo.org',c.TOKEN,source/'transport',opener=None);pairs={}
  with p.JournalWriter(self.root,source/'reservations',c.mut.require_events,self.budget)as writer:
   body=(self.package/'metadata.json').read_bytes();url=self.created['links']['bucket']+'/metadata.json';rp=transport.out/'001_PUT.json';writer.reserve('PUT',url,body,rp,self.now(),'prior-metadata-upload',c.actual_digest.require_write_budget);transport.request('PUT',url,body,hashlib.sha256(body).hexdigest(),'application/octet-stream',authorized=True);obj=json.loads(rp.read_bytes());obj['http_status']=201;c.write(rp,obj);pairs['metadata_upload_receipt']=p.binding(rp)
   transport.request('GET','https://zenodo.org/api/deposit/depositions/'+self.rid);pairs['metadata_legacy_receipt']=p.binding(transport.out/'002_GET.json')
   transport.request('GET','https://zenodo.org/api/records/'+self.rid+'/draft',accept=p.NATIVE);pairs['metadata_native_receipt']=p.binding(transport.out/'003_GET.json')
   body=(self.package/'METHODS_NOTES.zip').read_bytes();url=self.created['links']['bucket']+'/METHODS_NOTES.zip';rp=transport.out/'004_PUT.json';writer.reserve('PUT',url,body,rp,self.now(),'old-uncertain-archive',c.actual_digest.require_write_budget);c.write(rp,{'method':'PUT','url':url,'request_body_sha256':hashlib.sha256(body).hexdigest(),'environment':'zenodo.org','accept':'application/json','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY','error_type':'URLError'});pairs['uncertain_archive_receipt']=p.binding(rp)
  pairs['terminal_hold']=c.write(source/'RESULT.json',{'status':'HOLD','phase':'UPLOAD_METHODS_NOTES.zip','writes':2,'continuation_attempts':2,'record_id':self.rid,'doi':None,'automatic_retry':False,'failure':'TransportHold: HOLD_TRANSPORT_UNCERTAIN_NO_RETRY:URLError'})
  observed=self.root/'reports/verification-coverage/readonly-absence';observed.mkdir();reads=old.RecoveryTransport('zenodo.org',c.TOKEN,observed/'transport',opener=None)
  reads.request('GET','https://zenodo.org/api/deposit/depositions/'+self.rid);pairs['absence_legacy_receipt']=p.binding(reads.out/'001_GET.json');reads.request('GET','https://zenodo.org/api/records/'+self.rid+'/draft',accept=p.NATIVE);pairs['absence_native_receipt']=p.binding(reads.out/'002_GET.json')
  downloads=[]
  for name in tc.KNOWN:
   data=(self.package/name).read_bytes();download=c.write(observed/'downloads'/name,data);get=c.write(observed/'downloads'/(name+'.GET.json'),dict(standard='VRS-PHASE7-EXACT-FILE-GET-1',status='EXACT_BYTES_PASS',authenticated=True,method='GET',url='https://zenodo.org/api/records/'+self.rid+'/draft/files/'+name+'/content',filename=name,bytes=len(data),sha256=download['sha256'],md5=hashlib.md5(data).hexdigest(),path=download['path']));downloads.append(dict(filename=name,download=download,get_receipt=get,md5=hashlib.md5(data).hexdigest(),size=len(data)))
  pairs['adjudication_result']=c.write(observed/'RESULT.json',dict(standard='VRS_PHASE7_UNCERTAIN_UPLOAD_READ_ONLY_OBSERVATIONS_1',status='READ_ONLY_OBSERVATIONS_NOT_ACCEPTANCE',record_id=self.rid,published=False,mutations=0,acceptance_evidence=False,certifies=False,archive_observation='ABSENT_FROM_BOTH_INVENTORIES_OBSERVED_ONLY',present_files=list(tc.KNOWN),absent_files=list(tc.REMAINING),downloads=downloads,driver_sha256='a'*64,credentials_recorded=False,automatic_retry=False));pairs['adjudication_diff']=c.write(observed/'FULL_PAIR_DIFF.json',dict(standard='READ_ONLY_PATH_DIFFERENCES_NOT_ACCEPTANCE_1',certifies=False,legacy=[],native=[]))
  self.three_context=pairs;self.three_paths={k:str(Path(v['path']).relative_to(self.root))for k,v in pairs.items()};self.three_pins={k:v['sha256']for k,v in pairs.items()};self.prior_uploaded=c.write(source/'UPLOADED_PLAN.json',self.uploaded_plan)
  pins=self.uploaded_plan['runtime_pins']+[{'name':name,'path':str(Path(__file__).parent/name),'sha256':p.sha(Path(__file__).parent/name)}for name in('first_digest_three_file_draft.py','three_file_draft_continuation.py','owned_archive_wait.py')]
  self.three_plan=dict(standard='VRS-PHASE7-FIRST-DIGEST-THREE-FILE-DRAFT-PLAN-1',status='FROZEN_READY_NOT_EXECUTED',canonical_root=str(self.root),package_path=str(self.package),prior_uploaded_plan=self.prior_uploaded,three_file_context=pairs,runtime_pins=pins,record_id=self.rid,expected_writes=4,historical_prior_attempts=7,infrastructure_retry=1)
  self.calls=[]
 def run(self,**opts):
  with patch.object(dr,'CONTEXT_PINS',self.context_pins),patch.object(rc,'RESERVED_CONTEXT_PINS',self.reserved_pins),patch.object(uc,'UPLOADED_CONTEXT_PINS',self.uploaded_pins),patch.object(tc,'THREE_CONTEXT_PINS',self.three_pins),patch.object(tc,'THREE_CONTEXT_PATHS',self.three_paths),patch.object(tc,'ADJUDICATOR_SHA256','a'*64),patch.object(tc,'INVENTORY_SHA256',self.inventory['sha256']),patch.object(tc,'PRIOR_PLAN_SHA256',self.prior_uploaded['sha256']),patch.object(aw,'ARCHIVE_SHA256',p.sha(self.package/'METHODS_NOTES.zip')),patch.object(aw,'ARCHIVE_SIZE',(self.package/'METHODS_NOTES.zip').stat().st_size),patch.object(aw,'OWN_ARCHIVE_URL',self.created['links']['bucket']+'/METHODS_NOTES.zip'),patch.object(p,'require_module_pins',return_value=[]),patch.object(ud,'require_module_pins',return_value=[]),patch.object(r,'require_module_pins',return_value=[]):
   return r._execute(self.root,self.package,self.three_plan,self.output,c.TOKEN,self.runtime,account_factory=old.RecoveryAccount,transport_factory=ThreeFileTransport,download_factory=c.FakeDownloads,clock=self.now,**opts)
 def revise(self,key,obj):
  path=Path(self.three_context[key]['path']);c.write(path,obj);self.three_context[key]=p.binding(path);self.three_pins[key]=self.three_context[key]['sha256']

class ProtocolTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_four_only_remaining_real_day_two_to_six(self):
  self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],2)
  oldbytes=Path(self.f.three_context['uncertain_archive_receipt']['path']).read_bytes();v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(v['writes'],4);self.assertEqual([u.rsplit('/',1)[-1]for _,u in self.f.calls],['METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json','publish']);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],6);self.assertEqual(len(c.mut.require_events(self.f.root,self.f.now())),11);self.assertEqual(oldbytes,Path(self.f.three_context['uncertain_archive_receipt']['path']).read_bytes())
  env=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());self.assertEqual((env['mutations'],env['confirmed_acknowledged_mutations'],env['global_lifecycle_attempts'],env['continuation_mutations']),(10,9,11,4));self.assertFalse(any('/pids/'in u or u.endswith('/metadata.json')or u.endswith('/paper.tex')or u.endswith('/paper.pdf')for _,u in self.f.calls));self.assertEqual(self.f.runtime.registration.prepare_calls,1)
 def test_next_day_zero_to_four_all_history_retained(self):
  later=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1);self.f.now=lambda:later.isoformat();v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);initial=json.loads((self.f.output/'INITIAL_DAILY_BUDGET.json').read_bytes());final=json.loads((self.f.output/'FINAL_DAILY_BUDGET.json').read_bytes());self.assertEqual(initial['budget']['used'],0);self.assertEqual(final['daily']['used'],4);self.assertEqual(len(c.mut.require_events(self.f.root,self.f.now())),11)
 def test_no_replay_consumed_output(self):
  self.f.run();before=self.f.index.read_bytes()
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(before,self.f.index.read_bytes());self.assertEqual(len(self.f.calls),4)
 def test_new_uncertain_zip_charged_once_never_publish_retry(self):
  self.f.uncertain_write=1;v=self.f.run();self.assertEqual(v['writes'],1);self.assertEqual(len(self.f.calls),1);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],3);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_uncertain_publish_never_replay(self):
  self.f.uncertain_write=4;v=self.f.run();self.assertEqual(v['writes'],4);self.assertEqual(len(self.f.calls),4);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_fresh_archive_appeared_forbids_reupload(self):
  self.f.native['files']['entries']['METHODS_NOTES.zip']={};v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.calls,[])
 def test_fresh_metadata_or_pid_content_mismatch_halts(self):
  for mode in('description','pid'):
   if mode=='pid':self.f.close();self.f=Fixture();self.f.native['pids']['doi']['identifier']='10.5281/zenodo.999'
   else:self.f.native['metadata']['description']+='OTHER CLAIM'
   v=self.f.run();self.assertEqual(v['writes'],0)
 def test_fresh_known_download_mismatch_before_new_write(self):
  self.f.bad_download='metadata.json';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_changed_public_pid_or_title_no_registration(self):
  for flag in('public_pid_mutation','bad_public_legacy'):
   if flag=='bad_public_legacy':self.f.close();self.f=Fixture()
   setattr(self.f,flag,True);v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH',v);self.assertEqual(v['writes'],4);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_registration_proposals_do_not_write_ssot(self):
  before=(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes();self.f.run();self.assertEqual(before,(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
 def test_plan_typed_counts_and_exact_first_retry(self):
  for key,values in(('expected_writes',(True,4.0,'4',5)),('historical_prior_attempts',(True,7.0,'7',6)),('infrastructure_retry',(True,0,2,3,1.0,'1'))):
   for value in values:
    with self.subTest(key=key,value=value):
     original=self.f.three_plan[key];self.f.three_plan[key]=value
     with self.assertRaises(Exception):self.f.run()
     self.f.three_plan[key]=original
  self.assertEqual(self.f.calls,[])
 def test_missing_context_and_hash_mismatch_no_call(self):
  self.f.three_context['metadata_upload_receipt']['sha256']='a'*64
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_saved_hold_is_never_promoted(self):
  obj=json.loads(Path(self.f.three_context['terminal_hold']['path']).read_bytes());obj['status']='PUBLISHED_STRICT_READBACK_PASS';self.f.revise('terminal_hold',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_unknown_archive_is_never_fake_201(self):
  obj=json.loads(Path(self.f.three_context['uncertain_archive_receipt']['path']).read_bytes());obj['http_status']=201;self.f.revise('uncertain_archive_receipt',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_foreign_saved_metadata_upload_rejected(self):
  obj=json.loads(Path(self.f.three_context['metadata_upload_receipt']['path']).read_bytes());obj['url']='https://zenodo.org/api/files/foreign/metadata.json';self.f.revise('metadata_upload_receipt',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_metadata_actual_201_not_200_or_unknown(self):
  obj=json.loads(Path(self.f.three_context['metadata_upload_receipt']['path']).read_bytes());obj['http_status']=200;self.f.revise('metadata_upload_receipt',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_saved_absence_pair_cannot_adopt_arbitrary_content(self):
  obj=json.loads(Path(self.f.three_context['absence_native_receipt']['path']).read_bytes());obj['response']['metadata']['description']+='NEW';self.f.revise('absence_native_receipt',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_nonempty_diff_not_an_accepted_observation(self):
  obj=json.loads(Path(self.f.three_context['adjudication_diff']['path']).read_bytes());obj['native']=['metadata'];self.f.revise('adjudication_diff',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_committed_or_partial_archive_is_not_absence(self):
  obj=json.loads(Path(self.f.three_context['adjudication_result']['path']).read_bytes());obj['archive_observation']='COMMITTED';self.f.revise('adjudication_result',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_download_bytes_and_receipt_and_foreign_url_fail(self):
  for mode in('bytes','receipt','url'):
   if mode!='bytes':self.f.close();self.f=Fixture()
   obj=json.loads(Path(self.f.three_context['adjudication_result']['path']).read_bytes());row=obj['downloads'][0]
   if mode=='bytes':Path(row['download']['path']).write_bytes(b'wrong')
   else:
    rp=Path(row['get_receipt']['path']);get=json.loads(rp.read_bytes());get['url']='https://zenodo.org/api/records/999/draft/files/paper.tex/content'if mode=='url'else get['url'];get['authenticated']=False if mode=='receipt'else True;c.write(rp,get);row['get_receipt']=p.binding(rp);self.f.revise('adjudication_result',obj)
   v=self.f.run();self.assertEqual(v['writes'],0)
 def test_duplicate_and_missing_downloads_rejected(self):
  obj=json.loads(Path(self.f.three_context['adjudication_result']['path']).read_bytes());obj['downloads'][2]=obj['downloads'][1];self.f.revise('adjudication_result',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_new_operation_nonce_distinct_from_consumed_old_driver(self):
  ctx=self.f.three_context
  with patch.object(tc,'THREE_CONTEXT_PINS',self.f.three_pins):
   x=tc.operation_id('a'*64,'2026-W41',self.f.rid,'UPLOAD_METHODS_NOTES.zip',b'x',ctx);self.assertNotEqual(x,uc.operation_id('a'*64,'2026-W41',self.f.rid,'UPLOAD_METHODS_NOTES.zip',b'x'));self.assertEqual(x,tc.operation_id('a'*64,'2026-W41',self.f.rid,'UPLOAD_METHODS_NOTES.zip',b'x',ctx))
   for stage in('CREATE','RESERVE_DOI','METADATA_PUT','UPLOAD_metadata.json','UPLOAD_paper.pdf','UPLOAD_paper.tex'):
    with self.subTest(stage=stage),self.assertRaises(Exception):tc.operation_id('a'*64,'2026-W41',self.f.rid,stage,b'x',ctx)

 def test_identical_prefailure_leaf_cannot_replace_postfailure_absence(self):
  for role,oldrole in(('absence_legacy_receipt','metadata_legacy_receipt'),('absence_native_receipt','metadata_native_receipt')):
   original=self.f.three_context[role];self.assertEqual(original['sha256'],self.f.three_context[oldrole]['sha256']);self.f.three_context[role]=copy.deepcopy(self.f.three_context[oldrole]);v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('EXACT_POSTFAILURE_SOURCE_PATH',v['failure']);self.f.three_context[role]=original;self.f.output=self.f.root/'reports/verification-coverage/second-provenance'
 def test_adjudicator_wrong_source_hash_rejected(self):
  obj=json.loads(Path(self.f.three_context['adjudication_result']['path']).read_bytes());obj['driver_sha256']='b'*64;self.f.revise('adjudication_result',obj);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_same_archive_extra_attempt_or_fourth_refused(self):
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/extra',c.mut.require_events,self.f.budget)as writer:
   data=(self.f.package/'METHODS_NOTES.zip').read_bytes();url=self.f.created['links']['bucket']+'/METHODS_NOTES.zip';path=self.f.root/'reports/verification-coverage/extra_PUT.json';writer.reserve('PUT',url,data,path,self.f.now(),'other-archive-retry',c.actual_digest.require_write_budget);c.write(path,dict(method='PUT',url=url,request_body_sha256=hashlib.sha256(data).hexdigest(),environment='zenodo.org',accept='application/json',status='HOLD_TRANSPORT_UNCERTAIN_NO_RETRY',error_type='URLError'))
  # Move execution to tomorrow so this is not merely a daily cap rejection.
  tomorrow=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1);self.f.now=lambda:tomorrow.isoformat();v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('ONLY_ORIGINAL_UNCERTAINTY',v['failure'])

 def test_current_other_day_slots_do_not_substitute_expected_two_or_zero(self):
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/other',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'other',self.f.root/'reports/verification-coverage/other.json',self.f.now(),'foreign-current-attempt',c.actual_digest.require_write_budget)
  before=self.f.index.read_bytes();v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(before,self.f.index.read_bytes())
 def test_duplicate_operation_refused_by_unchanged_consumer(self):
  with patch.object(tc,'THREE_CONTEXT_PINS',self.f.three_pins):op=tc.operation_id(p.sha(self.f.package/'DIGEST_MANIFEST.json'),'2026-W41',self.f.rid,'UPLOAD_METHODS_NOTES.zip',(self.f.package/'METHODS_NOTES.zip').read_bytes(),self.f.three_context)
  with self.assertRaises(Exception):dr.require_unspent_operation([{'operation_id':op}],op)
  self.assertEqual(self.f.calls,[]);self.assertLess(len(op),180)
 def test_all48_predecessor_members_byte_identical(self):
  old=c.GATES/'production_snapshots/phase7-20261007-uploaded-draft-continuation-v001/after/production_execution_dependencies'
  rows=json.loads((old/'FREEZE.json').read_bytes())['files'];self.assertEqual(len(rows),48)
  for row in rows:self.assertEqual((old/row['filename']).read_bytes(),(Path(__file__).parent/row['filename']).read_bytes(),row['filename'])
 def test_nine_original_strict_function_bodies_byte_identical(self):
  import ast
  a=(Path(__file__).parent/'first_digest_uploaded_draft.py').read_text();b=(Path(__file__).parent/'first_digest_three_file_draft.py').read_text()
  def bodies(source):
   lines=source.splitlines(keepends=True);return {node.name:''.join(lines[node.lineno-1:node.end_lineno])for node in ast.walk(ast.parse(source))if isinstance(node,ast.FunctionDef)}
  aa,bb=bodies(a),bodies(b)
  for name in('emit','checkpoint','saved','ev','preview_context','read_source','own_pair','draft_guard','fresh'):self.assertEqual(aa[name],bb[name],name)
 def test_publication_and_registration_blocks_remain_byte_identical(self):
  a=(Path(__file__).parent/'first_digest_uploaded_draft.py').read_text();b=(Path(__file__).parent/'first_digest_three_file_draft.py').read_text()
  for start,end in(("            result['phase']='PUBLISH'","            require(result['writes']=="),("            # This is an input adapter", "            result.update(status='PUBLISHED_STRICT_READBACK_PASS'")):
   def block(x):i=x.index(start);return x[i:x.index(end,i)]
   self.assertEqual(block(a),block(b))

 def test_genuine_archive_201_required_not_200_success(self):
  self.f.archive_http200=True;v=self.f.run();self.assertEqual(v['writes'],1);self.assertIn('GENUINE_OWN_ARCHIVE_201',v['failure']);self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))

class WaitTests(unittest.TestCase):
 def setUp(self):
  self.calls=[];self.inner=types.SimpleNamespace(deadline=None,open=lambda request,timeout:self.calls.append((request,timeout))or 'response');self.body=b'archive';self.url='https://zenodo.org/api/files/00000000-0000-0000-0000-000000000001/METHODS_NOTES.zip';self.stack=patch.multiple(aw,ARCHIVE_SHA256=hashlib.sha256(self.body).hexdigest(),ARCHIVE_SIZE=len(self.body),OWN_ARCHIVE_URL=self.url);self.stack.start();self.opener=aw.OwnedArchiveWait(self.inner,self.url,hashlib.sha256(self.body).hexdigest(),len(self.body))
 def tearDown(self):self.stack.stop()
 def test_only_exact_archive_600_every_other_request120(self):
  request=urllib.request.Request(self.url,data=self.body,method='PUT');self.assertEqual(self.opener.open(request,timeout=120),'response');self.assertEqual(self.calls[-1][1],600)
  for method,url,body in(('GET',self.url,None),('PUT',self.url.replace('METHODS_NOTES.zip','paper.pdf'),b'other'),('POST','https://zenodo.org/api/deposit/depositions/23226761/actions/publish',b'{}')):
   request=urllib.request.Request(url,data=body,method=method);self.opener.open(request,timeout=120);self.assertEqual(self.calls[-1][1],120)
 def test_wrong_bucket_host_body_size_rejected_without_open(self):
  for url,body in((self.url.replace('000000000001','000000000999'),self.body),(self.url.replace('zenodo.org','foreign.example'),self.body),(self.url,self.body+b'!'),(self.url,b'changed')):
   with self.subTest(url=url),self.assertRaises(Exception):self.opener.open(urllib.request.Request(url,data=body,method='PUT'),timeout=120)
  self.assertEqual(self.calls,[])
 def test_default120_strict_timeout_and_no_retry_on_exception(self):
  for timeout in(600,120.0,True,121):
   with self.subTest(timeout=timeout),self.assertRaises(Exception):self.opener.open(urllib.request.Request(self.url,data=self.body,method='PUT'),timeout=timeout)
  count=[]
  def error(*a,**k):count.append(1);raise OSError('uncertain')
  self.inner.open=error
  with self.assertRaises(OSError):self.opener.open(urllib.request.Request(self.url,data=self.body,method='PUT'))
  self.assertEqual(len(count),1)
 def test_deadline_proxy_preserves_preview_poll_bound(self):
  self.opener.deadline=123;self.assertEqual(self.inner.deadline,123);self.assertEqual(self.opener.deadline,123)
 def test_wait_constructor_requires_exact_frozen_archive(self):
  for url,digest,size in((self.url+'?x=1',hashlib.sha256(self.body).hexdigest(),len(self.body)),(self.url.replace('000000000001','000000000999'),hashlib.sha256(self.body).hexdigest(),len(self.body)),(self.url,'a'*64,len(self.body)),(self.url,hashlib.sha256(self.body).hexdigest(),True)):
   with self.subTest(url=url),self.assertRaises(Exception):aw.OwnedArchiveWait(self.inner,url,digest,size)

class RealTransportWaitTests(unittest.TestCase):
 def test_receipts_and_acceptance_identical_with_real_original_transport(self):
  import tempfile
  transport=c.load('actual_three_wait_transport',c.GATES/'zenodo_transport.py');url='https://zenodo.org/api/files/1487b1c9-45df-4b52-af5f-d2f7cd123b98/METHODS_NOTES.zip';body=b'fixture archive';bodysha=hashlib.sha256(body).hexdigest()
  class Response:
   status=201
   def __init__(self,url,data):self.url=url;self.data=data
   def read(self,*args):return self.data
   def __enter__(self):return self
   def __exit__(self,*args):return False
  class Inner:
   deadline=None
   def __init__(self,data):self.data=data;self.calls=[]
   def open(self,request,timeout=120):self.calls.append((request.get_method(),request.full_url,timeout));return Response(request.full_url,self.data)
  with tempfile.TemporaryDirectory()as tmp,patch.multiple(aw,ARCHIVE_SHA256=bodysha,ARCHIVE_SIZE=len(body)):
   for number,payload in enumerate((b'{"key":"METHODS_NOTES.zip"}',b'warning: not JSON')):
    direct=Inner(payload);wrapped=Inner(payload);plain=transport.ZenodoTransport('zenodo.org',c.TOKEN,Path(tmp)/(str(number)+'plain'),opener=direct);profile=transport.ZenodoTransport('zenodo.org',c.TOKEN,Path(tmp)/(str(number)+'profile'),opener=aw.OwnedArchiveWait(wrapped,url,bodysha,len(body)))
    if number==0:
     a=plain.request('PUT',url,body,bodysha,'application/octet-stream',authorized=True);b=profile.request('PUT',url,body,bodysha,'application/octet-stream',authorized=True);self.assertEqual(a,b)
    else:
     for obj in(plain,profile):
      with self.assertRaises(transport.TransportHold):obj.request('PUT',url,body,bodysha,'application/octet-stream',authorized=True)
    self.assertEqual((plain.out/'001_PUT.json').read_bytes(),(profile.out/'001_PUT.json').read_bytes());self.assertEqual(direct.calls[0][2],120);self.assertEqual(wrapped.calls[0][2],600);self.assertEqual(len(wrapped.calls),1)
 def test_original_url_and_hash_reject_before_adapter_or_network(self):
  import tempfile
  transport=c.load('actual_three_wait_transport_rejection',c.GATES/'zenodo_transport.py');calls=[];url=aw.OWN_ARCHIVE_URL;body=b'archive';digest=hashlib.sha256(body).hexdigest();inner=types.SimpleNamespace(deadline=None,open=lambda *a,**k:calls.append(1))
  with tempfile.TemporaryDirectory()as tmp,patch.multiple(aw,ARCHIVE_SHA256=digest,ARCHIVE_SIZE=len(body)):
   obj=transport.ZenodoTransport('zenodo.org',c.TOKEN,Path(tmp),opener=aw.OwnedArchiveWait(inner,url,digest,len(body)))
   for badurl,badhash in((url,'a'*64),(url.replace('zenodo.org','foreign.example'),digest),(url+'?token=x',digest)):
    with self.assertRaises(transport.TransportHold):obj.request('PUT',badurl,body,badhash,authorized=True)
   self.assertEqual(calls,[])

if __name__=='__main__':unittest.main()
