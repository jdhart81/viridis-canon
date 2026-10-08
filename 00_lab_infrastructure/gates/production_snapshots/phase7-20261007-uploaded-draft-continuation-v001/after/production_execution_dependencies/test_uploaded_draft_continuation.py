"""Offline remaining-five protocol; synthetic admission is not live evidence."""
import copy,datetime as dt,hashlib,json,sys,unittest,shutil,os
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import test_coordinator as c
import test_existing_draft_recovery as old
import test_reserved_draft_continuation as prior
import first_digest_uploaded_draft as r
import uploaded_draft_continuation as uc
import legacy_preview_aliases as la
import reserved_draft_continuation as rc
import draft_reservation as dr
import first_digest_publisher as p
import server_managed_fields as sm

class FixtureSM(c.FakeSM):
 _preview_inventory=staticmethod(sm._preview_inventory)
 _preview_url=staticmethod(sm._preview_url)
 def validate_new_version(self,actual,expected,**kwargs):
  result=super().validate_new_version(actual,expected,**kwargs);result.update(phase='DRAFT',record_id=actual['id'],checks={name:{'status':'PASS'}for name in la.REQUIRED_CHECKS});return result

class UploadedTransport(old.RecoveryTransport):
 def request(self,method,*args,**kwargs):
  value=super().request(method,*args,**kwargs)
  if method in{'POST','PUT'}:
   # Keep the synthetic transport response clock consistent with the fixture
   # reservation clock. The real complete consumer prefers response.modified.
   now=self.f.now();value['modified']=now
   self.f.legacy['modified']=now;self.f.native['updated']=now
   if getattr(self.f,'public_native',None) is not None:self.f.public_native['updated']=now;self.f.public_legacy['modified']=now
   path=self.out/f'{self.sequence:03d}_{method}.json';receipt=json.loads(path.read_bytes());receipt['response']=copy.deepcopy(value);receipt['response_sha256']=hashlib.sha256(c.encode(value)).hexdigest();c.write(path,receipt)
   stamp=dt.datetime.fromisoformat(now).timestamp();os.utime(path,(stamp,stamp))
  return value

class Fixture(prior.Fixture):
 def __init__(self):
  super().__init__();self.runtime.sm=FixtureSM();self.native['links'].pop('thumbnails',None)
  out=self.root/'reports/verification-coverage/old-two-uploads';out.mkdir();transport=old.RecoveryTransport('zenodo.org',c.TOKEN,out/'transport',opener=None)
  pairs={}
  with p.JournalWriter(self.root,out/'reservations',c.mut.require_events,self.budget)as writer:
   for prefix,name in(('tex','paper.tex'),('pdf','paper.pdf')):
    body=(self.package/name).read_bytes();url=self.created['links']['bucket']+'/'+name;path=transport.out/f'{transport.sequence+1:03d}_PUT.json';writer.reserve('PUT',url,body,path,self.now(),'prior-upload-'+name.encode().hex(),c.actual_digest.require_write_budget)
    response=transport.request('PUT',url,body,hashlib.sha256(body).hexdigest(),'application/octet-stream',authorized=True)
    v=json.loads(path.read_bytes());v['http_status']=201;c.write(path,v);pairs[prefix+'_upload_receipt']=p.binding(path)
    if prefix=='pdf':
     self.native['links']['thumbnails']={size:'https://zenodo.org/api/iiif/record:'+self.rid+':paper.pdf/full/%5E'+size+',/0/default.jpg'for size in la.SIZES};self.legacy['links']['thumbs']={size:'https://zenodo.org/record/'+self.rid+'/thumb'+size for size in la.SIZES};self.legacy['links']['thumb250']=self.legacy['links']['thumbs']['250']
    transport.request('GET','https://zenodo.org/api/deposit/depositions/'+self.rid);pairs[prefix+'_legacy_receipt']=p.binding(transport.out/f'{transport.sequence:03d}_GET.json')
    transport.request('GET','https://zenodo.org/api/records/'+self.rid+'/draft',accept=p.NATIVE);pairs[prefix+'_native_receipt']=p.binding(transport.out/f'{transport.sequence:03d}_GET.json')
  pairs['terminal_hold']=c.write(out/'RESULT.json',{'status':'HOLD','phase':'UPLOAD_paper.pdf','writes':2,'continuation_attempts':2,'record_id':self.rid,'doi':None,'automatic_retry':False})
  self.uploaded_context=pairs;self.uploaded_pins={k:v['sha256']for k,v in pairs.items()};self.calls=[]
  names=('first_digest_uploaded_draft.py','uploaded_draft_continuation.py','legacy_preview_aliases.py','first_digest_reserved_draft.py','reserved_draft_continuation.py','first_digest_existing_draft.py','draft_reservation.py','first_digest_publisher.py');pins=[{'name':name,'path':str(Path(__file__).parent/name),'sha256':p.sha(Path(__file__).parent/name)}for name in names]
  self.uploaded_plan={**self.continuation_plan,'standard':'VRS-PHASE7-FIRST-DIGEST-UPLOADED-DRAFT-PLAN-1','uploaded_context':pairs,'runtime_pins':pins,'expected_writes':5,'historical_prior_attempts':5};self.uploaded_plan.pop('prior_daily_attempts')
 def run(self,**clock_options):
  with patch.object(dr,'CONTEXT_PINS',self.context_pins),patch.object(rc,'RESERVED_CONTEXT_PINS',self.reserved_pins),patch.object(uc,'UPLOADED_CONTEXT_PINS',self.uploaded_pins),patch.object(p,'require_module_pins',return_value=[]),patch.object(r,'require_module_pins',return_value=[]):
   return r._execute(self.root,self.package,self.uploaded_plan,self.output,c.TOKEN,self.runtime,account_factory=old.RecoveryAccount,transport_factory=UploadedTransport,download_factory=c.FakeDownloads,clock=self.now,**clock_options)

class ProtocolTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_full_five_remaining_real_budget_five_plus_five(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(v['writes'],5);self.assertEqual(len(self.f.calls),5);self.assertEqual(dr.daily_diagnostics(c.mut.require_events(self.f.root,self.f.now()),self.f.now())['used'],10);self.assertEqual([m for m,_ in self.f.calls],['PUT']*4+['POST']);self.assertFalse(any(u.endswith('/paper.pdf')or u.endswith('/paper.tex')or '/pids/'in u or u=='https://zenodo.org/api/deposit/depositions'for _,u in self.f.calls))
  envelope=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());self.assertEqual((envelope['mutations'],envelope['continuation_mutations'],envelope['prior_own_upload_mutations'],envelope['daily_total_attempts']),(9,5,2,10));self.assertEqual(envelope['prior_own_upload_receipts'],{key:self.f.uploaded_context[key]for key in('tex_upload_receipt','pdf_upload_receipt')})
 def test_no_reupload_or_metadata_put_before_execution(self):
  v=self.f.run();proof=json.loads((self.f.output/'METADATA_ALREADY_EXACT.json').read_bytes());self.assertEqual(proof['metadata_puts'],0);self.assertFalse(any(u=='https://zenodo.org/api/deposit/depositions/'+self.f.rid for _,u in self.f.calls));self.assertEqual(len(self.f.uploads),6)
 def test_insufficient_actual_day_budget_halts(self):
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/other',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'other',self.f.root/'reports/verification-coverage/unresolved.json',self.f.now(),'extra',c.actual_digest.require_write_budget)
  before=self.f.index.read_bytes();v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.index.read_bytes(),before)
 def test_historical_events_next_day_budget_is_zero_then_five(self):
  # Entire real immutable prior history remains. Use tomorrow's actual UTC
  # fixture clock, causing the unchanged NY budget consumer to count zero.
  later=dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1);self.f.now=lambda:later.isoformat();v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v)
  initial=json.loads((self.f.output/'INITIAL_DAILY_BUDGET.json').read_bytes());final=json.loads((self.f.output/'FINAL_DAILY_BUDGET.json').read_bytes());self.assertEqual(initial['budget']['used'],0);self.assertEqual(final['daily']['used'],5);self.assertEqual(len(c.mut.require_events(self.f.root,self.f.now())),10)
 def test_rollover_between_precheck_and_first_write_halts(self):
  ny=ZoneInfo('America/New_York');next_day=dt.datetime.now(ny).date()+dt.timedelta(days=1);midnight=dt.datetime.combine(next_day,dt.time(),ny).astimezone(dt.timezone.utc);values=iter([(midnight-dt.timedelta(seconds=1)).isoformat(),(midnight+dt.timedelta(seconds=1)).isoformat()]);self.f.now=lambda:next(values);v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('DAY_OR_ATTEMPT_COUNT_CHANGED',v['failure'])
 def test_uncertain_upload_and_publish_never_replay(self):
  for attempt in(1,5):
   if attempt==5:self.f.close();self.f=Fixture()
   self.f.uncertain_write=attempt;v=self.f.run();self.assertEqual(v['writes'],attempt);self.assertEqual(len(self.f.calls),attempt);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_consumed_output_rejected_without_journal_change(self):
  self.f.run();before=self.f.index.read_bytes()
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(before,self.f.index.read_bytes());self.assertEqual(len(self.f.calls),5)
 def test_duplicate_operation_refused_before_journal_or_network(self):
  before=self.f.index.read_bytes();events=c.mut.require_events(self.f.root,self.f.now())
  with self.assertRaises(Exception):dr.require_unspent_operation(events,events[-1]['operation_id'])
  self.assertEqual(before,self.f.index.read_bytes());self.assertEqual(self.f.calls,[])
 def test_wrong_or_missing_uploaded_context_halts(self):
  del self.f.uploaded_context['pdf_upload_receipt']
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_uploaded_receipt_hash_mismatch_fails(self):
  self.f.uploaded_context['tex_upload_receipt']['sha256']='a'*64
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_frozen_saved_two_file_set_not_arbitrary_adoption(self):
  self.f.native['files']['entries']['paper.pdf']['checksum']='md5:'+'a'*32;v=self.f.run();self.assertEqual(v['writes'],0)
 def test_saved_main_byte_download_mismatch_halts_before_newwrite(self):
  self.f.bad_download='paper.pdf';v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.calls,[])
 def test_private_alias_wrong_size_url_foreign_or_extra_link_halts(self):
  for change in(lambda d:d['links']['thumbs'].__setitem__('250','https://zenodo.org/record/999/thumb250'),lambda d:d['links'].__setitem__('thumb250','https://foreign.example/thumb250'),lambda d:d['links'].__setitem__('extra','https://zenodo.org/record/'+self.f.rid)):
   original=copy.deepcopy(self.f.legacy);change(self.f.legacy);self.f.output=self.f.root/'reports/verification-coverage'/str(len(list((self.f.root/'reports/verification-coverage').iterdir())));v=self.f.run();self.assertEqual(v['writes'],0);self.f.legacy=original
 def test_native_content_after_newupload_halts(self):
  self.f.native_content_mutation=True;v=self.f.run();self.assertEqual(v['writes'],1);self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))
 def test_native_foreign_pdf_preview_halts(self):
  self.f.native['links']['thumbnails']['250']='https://zenodo.org/api/iiif/record:999:paper.pdf/full/250,/0/default.jpg';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_public_pid_or_title_mismatch_no_registration(self):
  for field in('public_pid_mutation','bad_public_legacy'):
   if field=='bad_public_legacy':self.f.close();self.f=Fixture()
   setattr(self.f,field,True);v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH',v);self.assertEqual(v['writes'],5);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_registration_after_full_pass_no_ssot_write(self):
  before=(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes();v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(self.f.runtime.registration.prepare_calls,1);self.assertEqual(before,(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
 def test_snapshot_adoption_does_not_add_prior_writes(self):
  before=c.mut.require_events(self.f.root,self.f.now());adopt=self.f.root/'reports/verification-coverage/adopt';adopt.mkdir()
  for source in Path(__file__).parent.iterdir():
   if source.is_file():shutil.copyfile(source,adopt/source.name)
  self.assertEqual(before,c.mut.require_events(self.f.root,self.f.now()));self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],5)
 def test_eleventh_actual_budget_attempt_refused(self):
  self.f.run()
  with self.assertRaises(Exception):
   with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/eleventh',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'{}',self.f.root/'reports/verification-coverage/eleventh_POST.json',self.f.now(),'eleventh',c.actual_digest.require_write_budget)

class AliasAndContextTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def audit(self):return {'status':'SERVER_MANAGED_READBACK_PASS','operation':'NEW_VERSION','phase':'DRAFT','record_id':self.f.rid,'checks':{name:{'status':'PASS'}for name in la.REQUIRED_CHECKS}}
 def test_each_size_exact_alias_and_inverse_private_guard(self):
  want=copy.deepcopy(self.f.legacy);want['links'].pop('thumb250');want['links'].pop('thumbs');out=la.project(self.f.native,want,self.audit(),sm);self.assertEqual(out,self.f.legacy)
  for size in la.SIZES:
   with self.subTest(size=size):
    self.assertEqual(out['links']['thumbs'][size],'https://zenodo.org/record/'+self.f.rid+'/thumb'+size);bad=copy.deepcopy(out);bad['links']['thumbs'][size]='https://zenodo.org/record/999/thumb'+size
    with self.assertRaises(Exception):c.s.require_private_source(bad,out,self.f.native,sm,c.preserve)
 def test_no_cached_or_foreign_or_nonpass_native_audit(self):
  for key,value in(('status','HOLD'),('operation','PRIOR_VERSION'),('phase','PUBLISHED'),('record_id','999')):
   bad={**self.audit(),key:value}
   with self.subTest(key=key),self.assertRaises(Exception):la.project(self.f.native,self.f.legacy,bad,sm)
  bad=self.audit();bad['checks']['derived_previews']['status']='HOLD'
  with self.assertRaises(Exception):la.project(self.f.native,self.f.legacy,bad,sm)
 def test_missing_or_hold_other_native_check_rejected(self):
  for row in la.REQUIRED_CHECKS:
   bad=self.audit();bad['checks'][row]['status']='HOLD'
   with self.subTest(row=row),self.assertRaises(Exception):la.project(self.f.native,self.f.legacy,bad,sm)
  bad=self.audit();bad['checks'].pop('content_metadata')
  with self.assertRaises(Exception):la.project(self.f.native,self.f.legacy,bad,sm)
 def test_foreign_file_record_host_unapproved_preview_rejected(self):
  for url in('https://zenodo.org/api/iiif/record:999:paper.pdf/full/250,/0/default.jpg','https://foreign.example/api/iiif/record:'+self.f.rid+':paper.pdf/full/250,/0/default.jpg','https://zenodo.org/api/iiif/record:'+self.f.rid+':foreign.pdf/full/250,/0/default.jpg'):
   bad=copy.deepcopy(self.f.native);bad['links']['thumbnails']['250']=url
   with self.subTest(url=url),self.assertRaises(Exception):la.project(bad,self.f.legacy,self.audit(),sm)
 def test_extra_missing_or_malformed_native_size_rejected(self):
  for key,value in(('999','url'),('0250','url'),('250',None)):
   bad=copy.deepcopy(self.f.native)
   if value is None:bad['links']['thumbnails'].pop(key)
   else:bad['links']['thumbnails'][key]=value
   with self.assertRaises(Exception):la.project(bad,self.f.legacy,self.audit(),sm)
 def test_no_disappearance_without_source_delete(self):
  bad=copy.deepcopy(self.f.native);bad['links'].pop('thumbnails')
  with self.assertRaises(Exception):la.project(bad,self.f.legacy,self.audit(),sm)
 def test_wrong_saved_hold_identity_phase_count_rejected(self):
  path=Path(self.f.uploaded_context['terminal_hold']['path']);value=json.loads(path.read_bytes())
  for key,bad in(('phase','PUBLISH'),('writes',1),('continuation_attempts',3),('record_id','999'),('automatic_retry',True)):
   obj={**value,key:bad};c.write(path,obj);self.f.uploaded_context['terminal_hold']=p.binding(path);self.f.uploaded_plan['uploaded_context']=self.f.uploaded_context;self.f.uploaded_pins['terminal_hold']=self.f.uploaded_context['terminal_hold']['sha256'];self.f.output=self.f.root/'reports/verification-coverage'/('hold-'+key);v=self.f.run();self.assertEqual(v['writes'],0)
 def test_remaining_stage_identity_forbids_manuscripts_or_reserve(self):
  a=uc.operation_id('a'*64,'2026-W41',self.f.rid,'PUBLISH',b'{}');self.assertIn(hashlib.sha256(b'{}').hexdigest(),a);self.assertNotEqual(a,rc.operation_id('a'*64,'2026-W41',self.f.rid,'PUBLISH',b'{}'))
  for stage in('CREATE','RESERVE_DOI','UPLOAD_paper.tex','UPLOAD_paper.pdf','METADATA_PUT'):
   with self.subTest(stage=stage),self.assertRaises(Exception):uc.operation_id('a'*64,'2026-W41',self.f.rid,stage,b'{}')
 def test_all39_predecessor_members_byte_identical(self):
  old=c.GATES/'production_snapshots/phase7-20261007-reserved-draft-continuation-v001/after/production_execution_dependencies'
  for row in json.loads((old/'FREEZE.json').read_bytes())['files']:self.assertEqual((old/row['filename']).read_bytes(),(Path(__file__).parent/row['filename']).read_bytes(),row['filename'])
 def test_native_guard_is_before_closed_alias_then_original_private_guard(self):
  source=(Path(__file__).parent/'first_digest_uploaded_draft.py').read_text();start=source.index('    def draft_guard(');end=source.index('    def fresh(',start);body=source[start:end];self.assertLess(body.index('sm.validate_new_version'),body.index('aliases.project'));self.assertLess(body.index('aliases.project'),body.index('state.require_private_source'))

if __name__=='__main__':unittest.main()
