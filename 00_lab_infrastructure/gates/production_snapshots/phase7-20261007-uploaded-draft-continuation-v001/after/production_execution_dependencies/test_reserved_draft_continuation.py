"""Offline seven-write protocol + unchanged real strict rule tests.

Fixture scientific admission is synthetic and never public/cert evidence.
Real complete accounting, mutation cap, source guards and registrar assembly
run unchanged; actual saved-pair proof is separately source-bound.
"""
import copy,datetime as dt,hashlib,json,sys,unittest,ast,shutil
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo
sys.dont_write_bytecode=True;sys.path.insert(0,str(Path(__file__).parent))
import test_coordinator as c
import test_existing_draft_recovery as old
import first_digest_reserved_draft as r
import reserved_draft_continuation as rc
import draft_reservation as dr
import first_digest_publisher as p
import first_digest_state as s

class Fixture(old.Fixture):
 def __init__(self):
  super().__init__();self.before_native=copy.deepcopy(self.native);self.before_legacy=copy.deepcopy(self.legacy)
  n,l=dr.reserved_expected(self.native,self.legacy,self.rid);doi=dr.own_doi(self.rid)
  n['updated']=self.now();n['revision_id']+=2
  l.update(doi=doi,doi_url='https://doi.org/'+doi);l['metadata']['doi']=doi;l['links']['doi']='https://doi.org/'+doi;l['links']['badge']='https://zenodo.org/badge/doi/'+p.urllib.parse.quote(doi,safe='')+'.svg';l['modified']=n['updated']
  prior=self.root/'reports/verification-coverage/old-reserve';prior.mkdir()
  post={'method':'POST','url':'https://zenodo.org/api/records/'+self.rid+'/draft/pids/doi','request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'environment':'zenodo.org','accept':p.NATIVE,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'response_sha256':hashlib.sha256(c.encode(n)).hexdigest(),'response':n}
  path=prior/'reserve_POST.json'
  with p.JournalWriter(self.root,prior/'reservations',c.mut.require_events,self.budget)as writer:writer.reserve('POST',post['url'],b'{}',path,self.now(),'prior-successful-own-reserve',c.actual_digest.require_write_budget)
  c.write(path,post)
  get=lambda url,v,accept:{'method':'GET','url':url,'request_body_sha256':None,'environment':'zenodo.org','accept':accept,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':200,'response_sha256':hashlib.sha256(c.encode(v)).hexdigest(),'response':v}
  self.reserved_context={'reservation_receipt':p.binding(path),'reserved_legacy_receipt':c.write(prior/'legacy_GET.json',get('https://zenodo.org/api/deposit/depositions/'+self.rid,l,'application/json')),'reserved_native_receipt':c.write(prior/'native_GET.json',get('https://zenodo.org/api/records/'+self.rid+'/draft',n,p.NATIVE)),'terminal_hold':c.write(prior/'RESULT.json',{'status':'HOLD','phase':'RESERVE_DOI','writes':1,'recovery_attempts':1,'record_id':self.rid,'doi':None,'automatic_retry':False})}
  self.reserved_pins={k:v['sha256']for k,v in self.reserved_context.items()};self.native=n;self.legacy=l
  pins=[{'name':name,'path':str(Path(__file__).parent/name),'sha256':p.sha(Path(__file__).parent/name)}for name in('first_digest_reserved_draft.py','reserved_draft_continuation.py','first_digest_existing_draft.py','draft_reservation.py','first_digest_publisher.py')]
  self.continuation_plan={'standard':'VRS-PHASE7-FIRST-DIGEST-RESERVED-DRAFT-PLAN-1','status':'FROZEN_READY_NOT_EXECUTED','canonical_root':str(self.root),'package_path':str(self.package),'original_plan':self.original_plan,'own_context':self.context,'reserved_context':self.reserved_context,'runtime_pins':pins,'record_id':self.rid,'expected_writes':7,'prior_daily_attempts':3}
 def run(self,**clock_options):
  with patch.object(dr,'CONTEXT_PINS',self.context_pins),patch.object(rc,'RESERVED_CONTEXT_PINS',self.reserved_pins),patch.object(p,'require_module_pins',return_value=[]),patch.object(r,'require_module_pins',return_value=[]):
   return r._execute(self.root,self.package,self.continuation_plan,self.output,c.TOKEN,self.runtime,account_factory=old.RecoveryAccount,transport_factory=old.RecoveryTransport,download_factory=c.FakeDownloads,clock=self.now,**clock_options)

class ProtocolTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_full_seven_writes_three_plus_seven_real_budget(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(v['writes'],7);self.assertEqual(v['continuation_attempts'],7);self.assertEqual(len(self.f.calls),7);self.assertEqual(len(c.mut.require_events(self.f.root,self.f.now())),10)
  self.assertEqual([m for m,_ in self.f.calls],['PUT']*6+['POST']);self.assertTrue(self.f.calls[-1][1].endswith('/actions/publish'))
  self.assertFalse(any('/draft/pids/'in u or u=='https://zenodo.org/api/deposit/depositions'or u=='https://zenodo.org/api/deposit/depositions/'+self.f.rid for _,u in self.f.calls))
  envelope=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());self.assertEqual((envelope['mutations'],envelope['continuation_mutations'],envelope['prior_own_creation_mutations'],envelope['prior_own_reservation_mutations'],envelope['daily_total_including_prior_failed_create']),(9,7,1,1,10));self.assertEqual(envelope['prior_own_reservation_receipt'],self.f.reserved_context['reservation_receipt'])
 def test_metadata_put_omitted_only_exact_reserved_pair(self):
  self.f.run();proof=json.loads((self.f.output/'METADATA_ALREADY_EXACT.json').read_bytes());self.assertEqual(proof['metadata_puts'],0);self.assertTrue(proof['reserved_doi_projection_only']);self.assertEqual(proof['reservation_receipt'],self.f.reserved_context['reservation_receipt'])
 def test_budget_four_spent_halts_without_write(self):
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/fourth',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'another',self.f.root/'reports/verification-coverage/unresolved.json',self.f.now(),'fourth-spent',c.actual_digest.require_write_budget)
  before=self.f.index.read_bytes();v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.index.read_bytes(),before)
 def test_budget_zero_two_or_wrong_day_not_claimed_three(self):
  for used in(0,2,4):
   with self.subTest(used=used):
    def budget(root,method,when):return {'status':'WRITE_SLOT_AVAILABLE','date_new_york':'2026-10-08','used':used,'remaining_including_next':10-used}
    self.f.runtime.policy.require_write_budget=budget;self.f.runtime.d.require_write_budget=lambda events,method,when,complete:budget(None,None,None)
    self.f.output=self.f.root/'reports/verification-coverage'/('budget-'+str(used));v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('SEVEN_DAILY',v['failure'])
 def test_eleventh_attempt_refused(self):
  self.f.run()
  with self.assertRaises(Exception):
   with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/eleventh',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'{}',self.f.root/'reports/verification-coverage/eleventh_POST.json',self.f.now(),'eleventh',c.actual_digest.require_write_budget)
 def test_uncertain_upload_spent_no_retry(self):
  self.f.uncertain_write=1;v=self.f.run();self.assertEqual(v['writes'],1);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],4);self.assertEqual(len(self.f.calls),1);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_uncertain_publish_spent_no_retry(self):
  self.f.uncertain_write=7;v=self.f.run();self.assertEqual(v['writes'],7);self.assertEqual(len(self.f.calls),7);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_consumed_output_no_replay(self):
  self.f.run();before=self.f.index.read_bytes()
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.index.read_bytes(),before);self.assertEqual(len(self.f.calls),7)
 def test_duplicate_operation_refused_without_journal_or_network(self):
  events=c.mut.require_events(self.f.root,self.f.now());before=self.f.index.read_bytes()
  with self.assertRaises(Exception):dr.require_unspent_operation(events,events[-1]['operation_id'])
  self.assertEqual(before,self.f.index.read_bytes());self.assertEqual(self.f.calls,[])
 def test_missing_reserved_context_halts(self):
  del self.f.reserved_context['reservation_receipt'];v=self.f.run();self.assertEqual(v['writes'],0)
 def test_modified_reserved_context_hash_refused(self):
  self.f.reserved_context['reserved_legacy_receipt']['sha256']='a'*64
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_wrong_plan_identity_or_mutation_count(self):
  for key,value in(('record_id','999'),('expected_writes',8),('prior_daily_attempts',2),('standard','OTHER')):
   with self.subTest(key=key):
    original=self.f.continuation_plan[key];self.f.continuation_plan[key]=value
    with self.assertRaises(Exception):self.f.run()
    self.f.continuation_plan[key]=original
 def test_native_pid_foreign_halts(self):
  self.f.native['pids']['doi']['identifier']='10.5281/zenodo.999';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_native_unreserved_pid_halts(self):
  self.f.native['pids']={};v=self.f.run();self.assertEqual(v['writes'],0)
 def test_extra_native_oai_halts(self):
  self.f.native['pids']['oai']={'identifier':'oai:zenodo.org:'+self.f.rid,'provider':'oai'};v=self.f.run();self.assertEqual(v['writes'],0)
 def test_private_content_changed_halts(self):
  self.f.legacy['metadata']['description']+='DIFFERENT CLAIM';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_private_unknown_field_halts(self):
  self.f.legacy['unlisted']='new';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_private_wrong_doi_each_projection_halts(self):
  for where,key in((self.f.legacy,'doi'),(self.f.legacy,'doi_url'),(self.f.legacy['metadata'],'doi'),(self.f.legacy['links'],'doi'),(self.f.legacy['links'],'badge')):
   with self.subTest(key=key):
    prior=where[key];where[key]='foreign';self.f.output=self.f.root/'reports/verification-coverage'/('wrong-'+str(len(list((self.f.root/'reports/verification-coverage').iterdir()))));v=self.f.run();self.assertEqual(v['writes'],0);where[key]=prior
 def test_missing_private_doi_projection_halts(self):
  del self.f.legacy['metadata']['doi'];v=self.f.run();self.assertEqual(v['writes'],0)
 def test_unencoded_or_missing_badge_halts(self):
  self.f.legacy['links']['badge']='https://zenodo.org/badge/doi/10.5281/zenodo.'+self.f.rid+'.svg';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_extra_or_removed_private_link_halts(self):
  self.f.legacy['links']['extra']='https://zenodo.org';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_published_draft_halts(self):
  self.f.native['is_published']=True;v=self.f.run();self.assertEqual(v['writes'],0)
 def test_duplicate_weekly_foreign_incomplete_race_halts(self):
  for field in('duplicate_week','foreign_account','incomplete_account','racing_account'):
   with self.subTest(field=field):
    setattr(self.f,field,True);self.f.output=self.f.root/'reports/verification-coverage'/field;v=self.f.run();self.assertEqual(v['writes'],0);setattr(self.f,field,False)
 def test_main_download_checksum_halts_before_publish(self):
  self.f.bad_download='METHODS_NOTES.zip';v=self.f.run();self.assertEqual(v['status'],'HOLD');self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))
 def test_native_claim_change_after_upload_not_adopted(self):
  self.f.native_content_mutation=True;v=self.f.run();self.assertEqual(v['writes'],1);self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))
 def test_public_pid_change_halts_after_publish_no_registration(self):
  self.f.public_pid_mutation=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(v['writes'],7);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_public_title_change_halts_after_publish(self):
  self.f.bad_public_legacy=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_registration_only_after_full_readback_and_no_ssot_write(self):
  before=(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes();v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(self.f.runtime.registration.prepare_calls,1);self.assertEqual(before,(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes())
 def test_registration_failure_no_retry(self):
  self.f.registration_failure=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(v['writes'],7);self.assertFalse((self.f.output/'REGISTRATION_ROWS.json').exists())
 def test_prior_transport_references_not_duplicate_attempts(self):
  self.f.run()
  for name,key in(('OWN_CREATION_RECEIPT.json','creation_receipt'),('OWN_RESERVATION_RECEIPT.json','reservation_receipt')):
   ref=json.loads((self.f.output/name).read_bytes());self.assertNotIn('environment',ref);self.assertEqual(ref['receipt'],self.f.context[key]if key in self.f.context else self.f.reserved_context[key])
 def test_source_snapshot_adoption_preserves_three_spent_attempts(self):
  before=c.mut.require_events(self.f.root,self.f.now());adopt=self.f.root/'reports/verification-coverage/adopted-source';adopt.mkdir()
  for source in Path(__file__).parent.iterdir():
   if source.is_file():shutil.copyfile(source,adopt/source.name)
  self.assertEqual(before,c.mut.require_events(self.f.root,self.f.now()));self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],3)
 def test_rollover_halts_before_any_mutation(self):
  ny=ZoneInfo('America/New_York');next_day=dt.datetime.now(ny).date()+dt.timedelta(days=1);midnight=dt.datetime.combine(next_day,dt.time(),ny).astimezone(dt.timezone.utc);times=iter([(midnight-dt.timedelta(seconds=1)).isoformat(),(midnight+dt.timedelta(seconds=1)).isoformat()]);self.f.now=lambda:next(times)
  v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('DAY_OR_ATTEMPT_COUNT_CHANGED',v['failure'])

class PureTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def pair(self):
  post=json.loads(Path(self.f.reserved_context['reservation_receipt']['path']).read_bytes());return rc.predicted_reserved_pair(self.f.before_native,self.f.before_legacy,self.f.rid,post)
 def context(self,sm=None):
  with patch.object(rc,'RESERVED_CONTEXT_PINS',self.f.reserved_pins):return rc.require_reserved_context(self.f.reserved_context,{k:json.loads(Path(b['path']).read_bytes())for k,b in self.f.reserved_context.items()},self.f.before_native,self.f.before_legacy,{'manifest':self.f.manifest,'mirror':None},sm or self.f.runtime.sm,c.preserve)
 def test_exact_closed_own_doi_projections(self):
  ack,n,l=self.pair();doi=dr.own_doi(self.f.rid);self.assertEqual(l['doi'],doi);self.assertEqual(l['doi_url'],'https://doi.org/'+doi);self.assertEqual(l['metadata']['doi'],doi);self.assertEqual(l['links']['doi'],'https://doi.org/'+doi);self.assertEqual(l['links']['badge'],'https://zenodo.org/badge/doi/10.5281%2Fzenodo.'+self.f.rid+'.svg')
  left=copy.deepcopy(l);right=copy.deepcopy(self.f.before_legacy)
  for key in('doi','doi_url'):left.pop(key)
  left['metadata'].pop('doi');left['links'].pop('doi');left['links']['badge']=right['links']['badge'];self.assertEqual(left,right)
 def test_actual_whole_native_and_private_pair_pass(self):
  import server_managed_fields as sm
  self.context(sm)
 def test_actual_whole_native_extra_content_pid_access_fails(self):
  import server_managed_fields as sm
  ack,expected,wanted=self.pair()
  for mutate in(lambda n:n['metadata'].update(description='CLAIM CHANGED'),lambda n:n.update(unlisted='new'),lambda n:n['pids']['doi'].update(identifier='10.5281/zenodo.999'),lambda n:n['access'].update(record='restricted')):
   changed=copy.deepcopy(expected);mutate(changed)
   with self.subTest(mutate=mutate),self.assertRaises(Exception):sm.validate_new_version(changed,expected,host='zenodo.org',record_id=self.f.rid,phase='DRAFT',temporal_baseline=self.f.before_native,own_operation_record_id=self.f.rid)
 def test_foreign_rid_reservation_body_or_provider_fails(self):
  original=json.loads(Path(self.f.reserved_context['reservation_receipt']['path']).read_bytes())
  for key,value in(('url','https://zenodo.org/api/records/999/draft/pids/doi'),('request_body_sha256','a'*64),('http_status',200),('accept','application/json')):
   changed=copy.deepcopy(original);changed[key]=value
   with self.subTest(key=key),self.assertRaises(Exception):rc.predicted_reserved_pair(self.f.before_native,self.f.before_legacy,self.f.rid,changed)
  for key,value in(('provider','other'),('client','other'),('identifier','10.5281/zenodo.999')):
   changed=copy.deepcopy(original);changed['response']['pids']['doi'][key]=value
   with self.subTest(key=key),self.assertRaises(Exception):rc.predicted_reserved_pair(self.f.before_native,self.f.before_legacy,self.f.rid,changed)
 def test_no_arbitrary_existing_doi_adoption(self):
  self.f.before_legacy['metadata']['doi']='10.5281/zenodo.'+self.f.rid
  with self.assertRaises(Exception):self.pair()
 def test_missing_or_extra_reserved_context_rejected(self):
  for key in('reservation_receipt','reserved_legacy_receipt','reserved_native_receipt','terminal_hold'):
   with self.subTest(key=key):
    prior=self.f.reserved_context.pop(key)
    with self.assertRaises(Exception):self.context()
    self.f.reserved_context[key]=prior
 def test_wrong_hold_phase_count_or_identity_rejected(self):
  path=Path(self.f.reserved_context['terminal_hold']['path']);original=json.loads(path.read_bytes())
  for key,value in(('phase','CREATE'),('writes',2),('recovery_attempts',2),('record_id','999'),('automatic_retry',True),('doi','10.5281/zenodo.23226761')):
   changed={**original,key:value};c.write(path,changed)
   with self.subTest(key=key),self.assertRaises(Exception):self.context()
  c.write(path,original)
 def test_native_or_private_saved_content_mismatch_rejected(self):
  for name in('reserved_legacy_receipt','reserved_native_receipt'):
   path=Path(self.f.reserved_context[name]['path']);original=json.loads(path.read_bytes());changed=copy.deepcopy(original);changed['response']['metadata']['description']+='DIFFERENT CLAIM';c.write(path,changed)
   with self.subTest(name=name),self.assertRaises(Exception):self.context()
   c.write(path,original)
 def test_no_create_reserve_or_metadata_put_source(self):
  source=(Path(__file__).parent/'first_digest_reserved_draft.py').read_text();self.assertNotIn("mutation(writer,'POST','https://zenodo.org/api/deposit/depositions',",source);self.assertNotIn("mutation(writer,'PUT','https://zenodo.org/api/deposit/depositions/'+rid,",source);self.assertNotIn("mutation(writer,'POST','https://zenodo.org/api/records/'+rid+'/draft/pids/doi'",source)
 def test_closed_identity_distinct_from_both_previous_attempts(self):
  a=rc.operation_id('a'*64,'2026-W41',self.f.rid,'PUBLISH',b'{}');self.assertIn(hashlib.sha256(b'{}').hexdigest(),a);self.assertIn(self.f.rid,a);self.assertNotEqual(a,dr.operation_id('a'*64,'2026-W41',self.f.rid,'PUBLISH',b'{}'));self.assertNotEqual(a,rc.operation_id('a'*64,'2026-W41',self.f.rid,'UPLOAD_paper.tex',b'{}'))
  for stage in('CREATE','RESERVE_DOI','METADATA_PUT'):
   with self.subTest(stage=stage),self.assertRaises(Exception):rc.operation_id('a'*64,'2026-W41',self.f.rid,stage,b'{}')
 def test_all_predecessor_files_byte_identical(self):
  olddir=c.GATES/'production_snapshots/phase7-20261007-existing-draft-doi-recovery-v002/after/production_execution_dependencies'
  for row in json.loads((olddir/'FREEZE.json').read_bytes())['files']:self.assertEqual((olddir/row['filename']).read_bytes(),(Path(__file__).parent/row['filename']).read_bytes(),row['filename'])
 def test_existing_public_pid_oai_closed_rule_unchanged(self):
  import server_managed_fields as sm
  n=copy.deepcopy(self.f.native);after=copy.deepcopy(n);after['pids']['oai']={'identifier':'oai:zenodo.org:'+self.f.rid,'provider':'oai'};publish={'method':'POST','url':'https://zenodo.org/api/deposit/depositions/'+self.f.rid+'/actions/publish','http_status':202,'response_sha256':'a'*64,'response':{'id':int(self.f.rid)}}
  sm.require_pids(after,n,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='PUBLISHED',own_publish_response=publish,same_operation_reservation_id=self.f.rid)
  after['pids']['oai']['identifier']='oai:zenodo.org:999'
  with self.assertRaises(Exception):sm.require_pids(after,n,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='PUBLISHED',own_publish_response=publish,same_operation_reservation_id=self.f.rid)

if __name__=='__main__':unittest.main()
