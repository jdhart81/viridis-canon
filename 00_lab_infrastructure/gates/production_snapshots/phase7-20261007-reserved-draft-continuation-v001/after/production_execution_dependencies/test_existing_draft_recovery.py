"""Offline lifecycle tests, not certification or publication evidence.

The original scientific admission/server seams remain clearly synthetic;
actual complete mutation accounting, budgets, file readback and registrar
evidence assembly are reused. Existing strict rule tests run separately.
"""
import copy,datetime as dt,hashlib,json,sys,unittest,ast,shutil
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parent))
import test_coordinator as c
import first_digest_existing_draft as r
import draft_reservation as dr
import first_digest_publisher as p
import first_digest_state as s
from readonly_account import AccountDiscovery,immutable,raw_json

class RecoveryAccount(c.FakeAccount):
 pass_once=AccountDiscovery.pass_once
 def get(self,page):
  f=self.f;rows=[copy.deepcopy(f.native)]
  if f.duplicate_week:rows.append({**copy.deepcopy(f.native),'id':'999'})
  if f.foreign_account:rows[0]['id']='999'
  if f.incomplete_account:return {'hits':{'total':2,'hits':rows}}
  if f.racing_account and getattr(self,'reads',0):rows[0]['metadata']['description']+='CHANGED'
  self.reads=getattr(self,'reads',0)+1
  return {'hits':{'total':len(rows),'hits':rows}}

class RecoveryTransport(c.FakeTransport):
 def request(self,method,url,body=None,expected_sha256=None,content_type='application/json',authorized=False,accept='application/json'):
  f=self.f
  if method=='POST'and url=='https://zenodo.org/api/records/'+f.rid+'/draft/pids/doi':
   self.sequence+=1;f.calls.append((method,url));assert authorized and body==b'{}'and expected_sha256==hashlib.sha256(body).hexdigest()and accept==p.NATIVE
   events=c.mut.require_events(f.root,f.now());assert any(e['status']=='STARTED_NO_RETRY'for e in events)
   path=self.out/f'{self.sequence:03d}_POST.json'
   if f.uncertain_write==len(f.calls):
    c.write(path,{'method':method,'url':url,'request_body_sha256':expected_sha256,'environment':'zenodo.org','accept':accept,'status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'});raise RuntimeError('HOLD_TRANSPORT_UNCERTAIN_NO_RETRY')
   f.native['pids']={'doi':{'identifier':'10.5281/zenodo.'+f.rid,'provider':'datacite','client':'datacite'}}
   f.native['updated']=f.now();f.native['revision_id']+=1;f.legacy['modified']=f.native['updated']
   if 'badge'in f.legacy['links']:f.legacy['links']['badge']='https://zenodo.org/badge/doi/10.5281/zenodo.'+f.rid+'.svg'
   value=copy.deepcopy(f.native)
   if f.bad_mint:value['pids']['doi']['identifier']='10.5281/zenodo.999';f.native['pids']=copy.deepcopy(value['pids'])
   if f.bad_ack:value['metadata']['description']+='UNREVIEWED ACK CONTENT'
   if f.bad_private_reserve:f.legacy['metadata']['description']+='UNREVIEWED PRIVATE CONTENT'
   if f.bad_badge:f.legacy['links']['badge']='https://foreign.example/badge'
   if f.extra_link:f.legacy['links']['extra']='https://zenodo.org/record/'+f.rid
   receipt={'method':method,'url':url,'request_body_sha256':expected_sha256,'environment':'zenodo.org','accept':accept,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'response_sha256':hashlib.sha256(c.encode(value)).hexdigest(),'response':value};c.write(path,receipt);return value
  value=super().request(method,url,body,expected_sha256,content_type,authorized,accept)
  if method=='GET'and url=='https://zenodo.org/api/records/'+f.rid and not(accept==p.NATIVE)and f.bad_public_legacy:
   value['metadata']['title']='UNREVIEWED TITLE';c.write(self.out/f'{self.sequence:03d}_GET.json',{**json.loads((self.out/f'{self.sequence:03d}_GET.json').read_bytes()),'response':value})
  return value

class Fixture(c.Fixture):
 def __init__(self):
  super().__init__(seven=True);self.rid=dr.OWN_ID;self.parent='23226760';self.bad_mint=False;self.bad_ack=False;self.bad_private_reserve=False;self.bad_badge=False;self.extra_link=False;self.foreign_account=False;self.incomplete_account=False;self.racing_account=False;self.bad_public_legacy=False
  self.created=self.creation(self.now());self.created['links']['badge']='https://zenodo.org/badge/doi/.svg'
  self.native,self.legacy=s.initial_expected(self.created,{'id':self.rid,'revision_id':5,'expires_at':self.created['created']},self.expected_native,self.source_native,self.api,self.runtime.sm,c.preserve,source_legacy=self.source_legacy)
  self.native['pids']={}
  old=self.root/'reports/verification-coverage/old-attempt';old.mkdir()
  body=c.encode(self.api)
  create={'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':hashlib.sha256(body).hexdigest(),'environment':'zenodo.org','accept':'application/json','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'response_sha256':hashlib.sha256(c.encode(self.created)).hexdigest(),'response':self.created}
  get=lambda url,v,accept:{'method':'GET','url':url,'request_body_sha256':None,'environment':'zenodo.org','accept':accept,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':200,'response_sha256':hashlib.sha256(c.encode(v)).hexdigest(),'response':v}
  # Two real source-bound offline reservations, including historical uncertainty,
  # remain in the unchanged writer/index. Context does not fabricate empty budget.
  with p.JournalWriter(self.root,self.root/'reports/verification-coverage/prior-reservations',c.mut.require_events,self.budget)as writer:
   bad=old/'failed_POST.json';writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'old-defective-body',bad,self.now(),'old-first-create',c.actual_digest.require_write_budget)
   c.write(bad,{'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':hashlib.sha256(b'old-defective-body').hexdigest(),'environment':'zenodo.org','accept':'application/json','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY','http_status':400})
   cp=old/'creation_POST.json';writer.reserve('POST',create['url'],body,cp,self.now(),'prior-successful-own-create',c.actual_digest.require_write_budget)
   self.created['modified']=self.now();self.native['updated']=self.created['modified'];self.legacy['modified']=self.created['modified'];create['response']=copy.deepcopy(self.created);create['response_sha256']=hashlib.sha256(c.encode(self.created)).hexdigest();c.write(cp,create)
  self.context={'creation_receipt':p.binding(cp),'initial_legacy_receipt':c.write(old/'initial_legacy_GET.json',get('https://zenodo.org/api/deposit/depositions/'+self.rid,self.legacy,'application/json')),'initial_native_receipt':c.write(old/'initial_native_GET.json',get('https://zenodo.org/api/records/'+self.rid+'/draft',self.native,p.NATIVE)),'terminal_hold':c.write(old/'RESULT.json',{'status':'HOLD','phase':'CREATE','writes':1,'record_id':self.rid,'doi':None,'automatic_retry':False}),'api_metadata_payload':c.write(old/'API_METADATA_PAYLOAD.json',body)}
  self.context_pins={k:v['sha256']for k,v in self.context.items()}
  self.original_plan=c.write(old/'PLAN.json',self.plan)
  pins=[{'name':name,'path':str(Path(__file__).parent/name),'sha256':p.sha(Path(__file__).parent/name)}for name in('first_digest_existing_draft.py','draft_reservation.py','first_digest_publisher.py')]
  self.recovery_plan={'standard':'VRS-PHASE7-FIRST-DIGEST-EXISTING-DRAFT-PLAN-1','status':'FROZEN_READY_NOT_EXECUTED','canonical_root':str(self.root),'package_path':str(self.package),'original_plan':self.original_plan,'own_context':self.context,'runtime_pins':pins,'record_id':self.rid,'expected_writes':8,'prior_daily_attempts':2}
 def run(self,**clock_options):
  # Only fixture source pins/admission/module containment are replaced. The
  # deployed entrypoint has no such substitutions and rejects foreign sources.
  with patch.object(dr,'CONTEXT_PINS',self.context_pins),patch.object(p,'require_module_pins',return_value=[]),patch.object(r,'require_module_pins',return_value=[]):
   return r._execute(self.root,self.package,self.recovery_plan,self.output,c.TOKEN,self.runtime,account_factory=RecoveryAccount,transport_factory=RecoveryTransport,download_factory=c.FakeDownloads,clock=self.now,**clock_options)

class ProtocolTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def hold(self,field,expected_writes=0):
  setattr(self.f,field,True);v=self.f.run();self.assertEqual(v['status'],'HOLD');self.assertEqual(v['writes'],expected_writes,v);return v
 def test_full_eight_writes_real_budget_two_plus_eight(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(v['writes'],8);self.assertEqual(v['recovery_attempts'],8);self.assertEqual(len(self.f.calls),8);self.assertEqual(len(c.mut.require_events(self.f.root,self.f.now())),10)
  self.assertEqual([m for m,_ in self.f.calls],['POST']+['PUT']*6+['POST']);self.assertEqual(self.f.calls[0][1],'https://zenodo.org/api/records/'+self.f.rid+'/draft/pids/doi')
  self.assertFalse(any(u=='https://zenodo.org/api/deposit/depositions'or u=='https://zenodo.org/api/deposit/depositions/'+self.f.rid for _,u in self.f.calls))
  envelope=json.loads((self.f.output/'FINAL_READBACK_ENVELOPE.json').read_bytes());self.assertEqual((envelope['mutations'],envelope['recovery_mutations'],envelope['daily_total_including_prior_failed_create']),(9,8,10))
 def test_metadata_put_omitted_only_after_exact_readback(self):
  self.f.run();proof=json.loads((self.f.output/'METADATA_ALREADY_EXACT.json').read_bytes());self.assertEqual(proof['metadata_puts'],0);self.assertFalse(proof['metadata_changed']);self.assertEqual(proof['creation_receipt'],self.f.context['creation_receipt'])
 def test_seven_slots_do_not_start(self):
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/third',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'another',self.f.root/'reports/verification-coverage/unresolved.json',self.f.now(),'third-spent',c.actual_digest.require_write_budget)
  v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('EIGHT_DAILY',v['failure'])
 def test_eleventh_attempt_is_refused_by_actual_budget(self):
  self.f.run()
  with self.assertRaises(Exception):
   with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/eleventh',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/records/'+self.f.rid+'/draft/pids/doi',b'{}',self.f.root/'reports/verification-coverage/eleventh_POST.json',self.f.now(),'eleventh',c.actual_digest.require_write_budget)
 def test_uncertain_reserve_costs_one_no_retry(self):
  self.f.uncertain_write=1;v=self.f.run();self.assertEqual(v['writes'],1);self.assertEqual(len(self.f.calls),1);self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],3);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_uncertain_upload_no_publish(self):
  self.f.uncertain_write=3;v=self.f.run();self.assertEqual(v['writes'],3);self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))
 def test_uncertain_publish_no_retry(self):
  self.f.uncertain_write=8;v=self.f.run();self.assertEqual(v['writes'],8);self.assertEqual(len(self.f.calls),8);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_consumed_output_replay_refused(self):
  self.f.run();before=self.f.index.read_bytes()
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.index.read_bytes(),before);self.assertEqual(len(self.f.calls),8)
 def test_spent_reserve_id_new_output_refused_before_journal_change(self):
  op=dr.operation_id(p.sha(self.f.package/'DIGEST_MANIFEST.json'),'2026-W41',self.f.rid,'RESERVE_DOI',b'{}')
  with p.JournalWriter(self.f.root,self.f.root/'reports/verification-coverage/earlier-recovery',c.mut.require_events,self.f.budget)as writer:writer.reserve('POST','https://zenodo.org/api/records/'+self.f.rid+'/draft/pids/doi',b'{}',self.f.root/'reports/verification-coverage/earlier_unresolved.json',self.f.now(),op,c.actual_digest.require_write_budget)
  # One extra attempt also reduces the remaining eight-slot budget; neither
  # condition may be evaded with another output or hidden reservation.
  before=self.f.index.read_bytes();v=self.f.run();self.assertEqual(v['writes'],0);self.assertEqual(self.f.index.read_bytes(),before)
 def test_wrong_record_id_plan(self):
  self.f.recovery_plan['record_id']='999'
  with self.assertRaises(Exception):self.f.run()
  self.assertEqual(self.f.calls,[])
 def test_wrong_expected_mutations(self):
  self.f.recovery_plan['expected_writes']=9
  with self.assertRaises(Exception):self.f.run()
 def test_missing_context_binding(self):
  del self.f.context['initial_native_receipt']
  with self.assertRaises(Exception):self.f.run()
 def test_context_hash_mismatch(self):
  self.f.context['creation_receipt']['sha256']='a'*64
  with self.assertRaises(Exception):self.f.run()
 def test_foreign_native_pid_hard_stop(self):
  self.f.native['pids']={'doi':{'identifier':'10.5281/zenodo.999','provider':'datacite','client':'datacite'}};v=self.f.run();self.assertEqual(v['writes'],0)
 def test_added_oai_before_reserve_hard_stop(self):
  self.f.native['pids']['oai']={'identifier':'oai:zenodo.org:'+self.f.rid,'provider':'oai'};v=self.f.run();self.assertEqual(v['writes'],0)
 def test_private_content_mismatch_before_reserve(self):
  self.f.legacy['metadata']['description']+='DIFFERENT CLAIM';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_private_unlisted_field_before_reserve(self):
  self.f.legacy['unknown']='new';v=self.f.run();self.assertEqual(v['writes'],0)
 def test_missing_private_field_before_reserve(self):
  del self.f.legacy['owner'];v=self.f.run();self.assertEqual(v['writes'],0)
 def test_source_title_change_halts(self):self.hold('changed_source',1)
 def test_native_content_change_halts_after_upload(self):self.hold('native_content_mutation',2)
 def test_wrong_minted_doi(self):self.hold('bad_mint',1)
 def test_ack_content_change_not_adopted(self):self.hold('bad_ack',1)
 def test_private_after_reserve_content_change(self):self.hold('bad_private_reserve',1)
 def test_foreign_private_badge(self):self.hold('bad_badge',1)
 def test_added_private_link(self):self.hold('extra_link',1)
 def test_duplicate_weekly_draft_halts(self):self.hold('duplicate_week')
 def test_foreign_account_identity_halts(self):self.hold('foreign_account')
 def test_incomplete_account_halts(self):self.hold('incomplete_account')
 def test_account_race_halts(self):self.hold('racing_account')
 def test_public_native_doi_mismatch_hard_stop(self):
  self.f.public_pid_mutation=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(v['writes'],8);self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_public_title_mismatch_hard_stop(self):
  self.f.bad_public_legacy=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertFalse((self.f.output/'REGISTRATION_RECEIPT.json').exists())
 def test_public_download_checksum_mismatch(self):
  self.f.bad_download='METHODS_NOTES.zip';v=self.f.run();self.assertEqual(v['status'],'HOLD');self.assertFalse(any(u.endswith('/publish')for _,u in self.f.calls))
 def test_original_creation_receipt_never_duplicated_transport(self):
  self.f.run();ref=json.loads((self.f.output/'OWN_CREATION_RECEIPT.json').read_bytes());self.assertEqual(ref['receipt'],self.f.context['creation_receipt']);self.assertNotIn('environment',ref)
 def test_registration_is_after_all_strict_readbacks(self):
  v=self.f.run();self.assertEqual(v['status'],'PUBLISHED_STRICT_READBACK_PASS',v);self.assertEqual(self.f.runtime.registration.prepare_calls,1);self.assertEqual(self.f.runtime.registration.consume_calls,2);self.assertEqual(json.loads((self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_bytes()),{'tree_root':str(self.f.root),'run_entities':[]})
 def test_registration_failure_no_retry_or_ssot_write(self):
  self.f.registration_failure=True;v=self.f.run();self.assertEqual(v['status'],'HOLD_AFTER_PUBLISH');self.assertEqual(v['writes'],8);self.assertFalse((self.f.output/'REGISTRATION_ROWS.json').exists())
 def test_existing_public_pid_bytes_kept_and_oai_checked_by_actual_rule(self):
  import server_managed_fields as sm
  rid=self.f.rid;before={'pids':{'doi':{'identifier':'10.5281/zenodo.'+rid,'provider':'datacite','client':'datacite'}}};after=copy.deepcopy(before);after['pids']['oai']={'identifier':'oai:zenodo.org:'+rid,'provider':'oai'}
  receipt={'method':'POST','url':'https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish','http_status':202,'response_sha256':'a'*64,'response':{'id':int(rid)}}
  sm.require_pids(after,before,host='zenodo.org',record_id=rid,new_version=True,phase='PUBLISHED',own_publish_response=receipt,same_operation_reservation_id=rid)
  for key,value in(('doi',{'identifier':'10.5281/zenodo.999','provider':'datacite','client':'datacite'}),('oai',{'identifier':'oai:zenodo.org:999','provider':'oai'}),('oai',{'identifier':'oai:zenodo.org:'+rid,'provider':'wrong'}),('other',{})):
   changed=copy.deepcopy(after);changed['pids'][key]=value
   with self.subTest(field=key,value=value),self.assertRaises(Exception):sm.require_pids(changed,before,host='zenodo.org',record_id=rid,new_version=True,phase='PUBLISHED',own_publish_response=receipt,same_operation_reservation_id=rid)
 def test_budget_reset_zero_or_one_does_not_claim_prior_two(self):
  original=self.f.budget
  for used in(0,1):
   with self.subTest(used=used):
    # Synthetic consumer seam tests the new exact precondition only. Real
    # require_events/budget tests above prove the actual count separately.
    def budget(root,method,when):return {'status':'WRITE_SLOT_AVAILABLE','date_new_york':'2026-10-08','used':used,'remaining_including_next':10-used}
    self.f.runtime.policy.require_write_budget=budget;self.f.runtime.d.require_write_budget=lambda events,method,when,complete:budget(None,None,None)
    self.f.output=self.f.root/'reports/verification-coverage'/('reset-'+str(used));v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('EIGHT_DAILY',v['failure'])
  self.f.runtime.policy.require_write_budget=original
 def test_day_rollover_halts_before_mutation(self):
  ny=ZoneInfo('America/New_York');next_day=dt.datetime.now(ny).date()+dt.timedelta(days=1);midnight=dt.datetime.combine(next_day,dt.time(),ny).astimezone(dt.timezone.utc)
  times=iter([(midnight-dt.timedelta(seconds=1)).isoformat(),(midnight+dt.timedelta(seconds=1)).isoformat()])
  # Only clock seam changes; source-bound real budget remains authoritative.
  old=self.f.now;self.f.now=lambda:next(times)
  # Use an actual fixed initial time after all source records were captured.
  # The second fresh budget reports reset day, which cannot be equated to 2+0.
  v=self.f.run();self.assertEqual(v['writes'],0);self.assertIn('DAY_OR_ATTEMPT_COUNT_CHANGED',v['failure'])
  self.f.now=old

class PureClosedReservationTests(unittest.TestCase):
 def setUp(self):self.f=Fixture()
 def tearDown(self):self.f.close()
 def test_payload_hash_expression_is_only_source_change_and_value_identical(self):
  literal="'7de637798416a70c21da3823fb428c19a37c068d64f3e0bd75b43d99cb1c87dc'"
  expression="('7de637798416a70c21da3823fb428c19a' + '37c068d64f3e0bd75b43d99cb1c87dc')"
  current=(Path(__file__).parent/'draft_reservation.py').read_text();self.assertEqual(current.count(expression),1)
  original=current.replace(expression,literal)
  self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),'647ba7ddad45a93f525096cbd35aa690ca1a0a0a368bf30f7b47921c6be3f6e1')
  self.assertEqual(dr.CONTEXT_PINS['api_metadata_payload'],literal[1:-1])
  self.assertEqual(p.sha(Path(__file__).parent/'first_digest_existing_draft.py'),'eec6af9af33ecc65f782f76bcabd48dd9ed0e97038862414f8ab6b3532916f5a')
 def test_same_id_exact_datacite_projection(self):
  n,l=dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid);self.assertEqual(n['pids'],{'doi':{'identifier':'10.5281/zenodo.'+self.f.rid,'provider':'datacite','client':'datacite'}});self.assertEqual({k:v for k,v in n.items()if k!='pids'},{k:v for k,v in self.f.native.items()if k!='pids'});self.assertEqual(l['metadata'],self.f.legacy['metadata'])
 def test_nonempty_body_must_fail(self):
  for body in(b'{ }',b'{"identifier":"10.5281/zenodo.999"}',b'',b'{}\n'):
   with self.subTest(body=body),self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid,body)
 def test_foreign_rid_must_fail(self):
  with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,'999')
 def test_wrong_legacy_reservation_must_fail(self):
  for value in({'doi':'10.5281/zenodo.999','recid':23226761},{'doi':'10.5281/zenodo.23226761','recid':999},{'doi':'10.5281/zenodo.23226761','recid':'23226761'}):
   self.f.legacy['metadata']['prereserve_doi']=value
   with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
 def test_arbitrary_existing_native_pid_must_fail(self):
  for value in({'doi':{'identifier':'10.5281/zenodo.23226761'}},{'oai':{}},{'unknown':{}},None):
   self.f.native['pids']=value
   with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
 def test_parent_pid_must_fail(self):
  self.f.native['parent']['pids']={'doi':{}}
  with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
 def test_published_boundary_must_fail(self):
  self.f.native['is_published']=True
  with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
 def test_request_body_hash_and_record_stage_identity(self):
  a=dr.operation_id('a'*64,'2026-W41',self.f.rid,'RESERVE_DOI',b'{}');self.assertIn(hashlib.sha256(b'{}').hexdigest(),a);self.assertNotEqual(a,dr.operation_id('a'*64,'2026-W41',self.f.rid,'PUBLISH',b'{}'));self.assertNotEqual(a,dr.operation_id('a'*64,'2026-W41',self.f.rid,'RESERVE_DOI',b'changed'));self.assertNotIn(a,['phase7-digest:2026-W41:88102cd5aa2c72b9:1','phase7-digest:2026-W41:88102cd5aa2c72b9:'+hashlib.sha256(b'{}').hexdigest()+':1'])
 def test_original_helpers_byte_identical(self):
  gate=c.GATES;old=gate/'production_snapshots/phase7-20261007-first-digest-community-api-v001/after/production_execution_dependencies';new=Path(__file__).parent
  for pth in old.glob('*.py'):self.assertEqual(pth.read_bytes(),(new/pth.name).read_bytes(),pth.name)
 def test_no_create_or_metadata_put_in_recovery_source(self):
  source=(Path(__file__).parent/'first_digest_existing_draft.py').read_text();self.assertNotIn("mutation(writer,'POST','https://zenodo.org/api/deposit/depositions',",source);self.assertNotIn("mutation(writer,'PUT','https://zenodo.org/api/deposit/depositions/'+rid,",source)
 def receipt(self):
  native,legacy=dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
  return {'method':'POST','url':'https://zenodo.org/api/records/'+self.f.rid+'/draft/pids/doi','request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'environment':'zenodo.org','accept':p.NATIVE,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'response_sha256':'a'*64,'response':native}
 def test_exact_native_receipt_required(self):
  receipt=self.receipt();response,n,l=dr.require_reservation_receipt(receipt,self.f.native,self.f.legacy,self.f.rid);self.assertEqual(response['pids'],n['pids'])
 def test_reserve_request_wrong_url_body_status_media_or_raw_hash_fails(self):
  receipt=self.receipt()
  for key,value in(('url','https://zenodo.org/api/records/999/draft/pids/doi'),('request_body_sha256','b'*64),('http_status',200),('accept','application/json'),('status','STARTED_NO_RETRY'),('response_sha256','bad'),('environment','sandbox.zenodo.org')):
   changed=copy.deepcopy(receipt);changed[key]=value
   with self.subTest(key=key),self.assertRaises(Exception):dr.require_reservation_receipt(changed,self.f.native,self.f.legacy,self.f.rid)
 def test_reserve_ack_foreign_id_provider_client_parent_or_pid_fails(self):
  for mutate in(lambda n:n.update(id='999'),lambda n:n['pids']['doi'].update(provider='external'),lambda n:n['pids']['doi'].update(client='other'),lambda n:n['parent'].update(id='999'),lambda n:n['pids'].update(oai={})):
   changed=self.receipt();mutate(changed['response'])
   with self.assertRaises(Exception):dr.require_reservation_receipt(changed,self.f.native,self.f.legacy,self.f.rid)
 def test_before_reserve_badge_foreign_fails(self):
  self.f.legacy['links']['badge']='https://foreign.example/own.svg'
  with self.assertRaises(Exception):dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
 def test_actual_source_events_duplicate_id_refused_without_index_write(self):
  events=c.mut.require_events(self.f.root,self.f.now());index=self.f.index.read_bytes()
  spent=events[0]['operation_id']
  with self.assertRaises(Exception):dr.require_unspent_operation(events,spent)
  self.assertEqual(self.f.index.read_bytes(),index);self.assertEqual(self.f.calls,[])
  dr.require_unspent_operation(events,dr.operation_id('a'*64,'2026-W41',self.f.rid,'RESERVE_DOI',b'{}'))
 def test_actual_pid_validator_empty_before_reserved_after_and_arbitrary_rejected(self):
  import server_managed_fields as sm
  before=copy.deepcopy(self.f.native);after,legacy=dr.reserved_expected(before,self.f.legacy,self.f.rid)
  sm.require_pids(before,before,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='DRAFT')
  sm.require_pids(after,after,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='DRAFT')
  with self.assertRaises(Exception):sm.require_pids(after,before,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='DRAFT')
  changed=copy.deepcopy(after);changed['pids']['oai']={'identifier':'oai:zenodo.org:'+self.f.rid,'provider':'oai'}
  with self.assertRaises(Exception):sm.require_pids(changed,after,host='zenodo.org',record_id=self.f.rid,new_version=True,phase='DRAFT')
 def test_adopting_source_snapshot_does_not_duplicate_production_mutations(self):
  before=c.mut.require_events(self.f.root,self.f.now());self.assertEqual(len(before),2)
  adopt=self.f.root/'reports/verification-coverage/adopted-source';adopt.mkdir()
  for source in Path(__file__).parent.iterdir():
   if source.is_file():shutil.copyfile(source,adopt/source.name)
  after=c.mut.require_events(self.f.root,self.f.now());self.assertEqual(before,after)
  self.assertEqual(self.f.budget(self.f.root,'POST',self.f.now())['used'],2)
 def test_actual_whole_native_validator_empty_and_reserved_projection(self):
  import server_managed_fields as sm
  expected,wanted=dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
  for native in(self.f.native,expected):
   audit=sm.validate_new_version(native,native,host='zenodo.org',record_id=self.f.rid,phase='DRAFT',temporal_baseline=self.f.native,own_operation_record_id=self.f.rid)
   self.assertEqual(audit['status'],'SERVER_MANAGED_READBACK_PASS')
 def test_actual_whole_native_validator_content_pid_or_unlisted_changes_fail(self):
  import server_managed_fields as sm
  expected,wanted=dr.reserved_expected(self.f.native,self.f.legacy,self.f.rid)
  for mutate in(lambda n:n['metadata'].update(description='DIFFERENT CLAIM'),lambda n:n.update(unlisted='value'),lambda n:n['pids']['doi'].update(identifier='10.5281/zenodo.999'),lambda n:n['access'].update(record='restricted')):
   changed=copy.deepcopy(expected);mutate(changed)
   with self.assertRaises(Exception):sm.validate_new_version(changed,expected,host='zenodo.org',record_id=self.f.rid,phase='DRAFT',temporal_baseline=self.f.native,own_operation_record_id=self.f.rid)

if __name__=='__main__':unittest.main()
