"""Fixture integration routes only; no live admission or source writes."""
from pathlib import Path
from copy import deepcopy
import datetime as dt,hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
N=W=G=HERE
sys.path[:0]=[str(HERE),str(HERE/'test_fixtures')]
import nightly_release_checkpoint as c
import digest_weekly_state as w
class Fixtures(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='nightlycheckpointfixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();(self.root/'RESEARCH_PIPELINE_v2').mkdir();self.src=self.root/'science-engine/Run-189';self.src.mkdir(parents=True);(self.src/'paper.tex').write_bytes(b'exact original');self.cert=self.root/'cert.json';self.cert.write_bytes(b'{}');self.row={'id':'Run-189','status':'CERTIFIED','certificate_valid':True,'certificate':str(self.cert),'path':str(self.src)};self.ledger={'tree_root':str(self.root),'run_entities':[self.row]};self.save_ledger();self.params=dict(selection_invocation='actual-current-stage-001')
 def save_ledger(self):self.lp=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';self.lp.write_bytes(c.digest.raw_json(self.ledger))
 def selected(self):return c.source_for_cycle(self.root,'Run-189',{'path':'cycle','sha256':'a'*64},{'path':'metadata','sha256':'b'*64},[],**self.params)
 def mocks(self,basis='INDEPENDENT'):
  return patch.object(c.policy,'snapshot_certificate',return_value=({'foundation_basis':basis},{'certified_theorems':['main','witness'],'nonvacuity':['witness']})),patch.object(c.policy,'fresh_target',return_value={'fixture':'not gate'}),patch.object(c.policy,'source_values',return_value={'fixture':'not gate'})
 def test_selector_uses_current_maincertificate_basis_exports_and_exact_source(self):
  a,b,d=self.mocks()
  with a as cert,b as target,d as values:
   v=self.selected();self.assertEqual(v['foundation_basis'],'INDEPENDENT');self.assertEqual(v['selected_theorems'],['main','witness']);self.assertEqual(v['source_manuscript'],c.policy.binding(self.src/'paper.tex'));self.assertFalse(v['certifies']);cert.assert_called_once();target.assert_called_once();values.assert_called_once()
 def test_hassorry_debt_uncertified_or_mirror_drift_never_selects_certificate(self):
  for status in('HAS_SORRY','DEBT','MIRROR_DRIFT','CLEAN_UNCERTIFIED'):
   self.row['status']=status;self.save_ledger()
   with patch.object(c.policy,'snapshot_certificate')as cert:self.assertRaises(ValueError,self.selected);cert.assert_not_called()
 def test_invalid_certificate_missing_duplicate_or_foreign_tree_hold(self):
  for change in('invalid','missing','duplicate','tree'):
   row=deepcopy(self.row);ledger=deepcopy(self.ledger)
   if change=='invalid':row['certificate_valid']=False;ledger['run_entities']=[row]
   elif change=='missing':ledger['run_entities']=[]
   elif change=='duplicate':ledger['run_entities']*=2
   else:ledger['tree_root']='/different/tree'
   self.lp.write_bytes(c.digest.raw_json(ledger));self.assertRaises(ValueError,self.selected)
 def test_unknown_basis_never_promoted(self):
  a,b,d=self.mocks('EMPIRICALLY_VALIDATED')
  with a,b,d:self.assertRaises(ValueError,self.selected)
 def test_source_outside_mirror_never_read_for_certification(self):
  self.row['path']='/etc';self.save_ledger();a,b,d=self.mocks()
  with a,b,d:self.assertRaises(ValueError,self.selected)
 def test_explicit_scoped_selection_preserved_without_changing_exports(self):
  a,b,d=self.mocks()
  with a,b,d:v=c.source_for_cycle(self.root,'Run-189',{}, {},[],selection_invocation='actual-current-stage-001',selected_theorems=['main']);self.assertEqual(v['selected_theorems'],['main'])
 def test_row_or_ledger_race_holds(self):
  a,b,_=self.mocks()
  def mutate(*args):self.lp.write_bytes(b'{}');return{}
  with a,b,patch.object(c.policy,'source_values',side_effect=mutate):self.assertRaises(ValueError,self.selected)
 def test_stage_default_generator_called_once_and_result_unadmitted(self):
  staged={'status':'EXACT_NIGHTLY_SCOPE_SOURCE_AND_PDF_STAGED_NOT_ADMITTED','run_id':'Run-189','certifies':False}
  with patch.object(c,'source_for_cycle',return_value={'fixture':'source'})as source,patch.object(c.generator,'prepare_source',return_value=staged)as gen:
   self.assertEqual(c.stage_checkpoint(self.root,self.root/'note','Run-189',{}, {},[],selection_invocation='stage-current-invocation',render=object()),staged);gen.assert_called_once();source.assert_called_once()
 def test_stage_failed_or_wrong_run_result_hold(self):
  for v in({'status':'PASS','run_id':'Run-189'},{'status':'EXACT_NIGHTLY_SCOPE_SOURCE_AND_PDF_STAGED_NOT_ADMITTED','run_id':'Run-190'}):
   with patch.object(c,'source_for_cycle',return_value={}),patch.object(c.generator,'prepare_source',return_value=v):self.assertRaises(ValueError,c.stage_checkpoint,self.root,self.root/'note','Run-189',{}, {},[],selection_invocation='stage-current-invocation',render=object())
 def test_review_requires_new_invocation_then_actual_admit(self):
  note=self.root/'note';note.mkdir();(note/'NIGHTLY_SCOPE_SOURCE.json').write_bytes(c.digest.raw_json({'selection_invocation':'stage-current-invocation'}))
  with patch.object(c.generator,'admit',return_value={'actual':'unit route'})as gen:self.assertRaises(ValueError,c.review_checkpoint,self.root,note,{},review_invocation='stage-current-invocation');gen.assert_not_called();self.assertEqual(c.review_checkpoint(self.root,note,{},review_invocation='review-current-invocation'),{'actual':'unit route'});gen.assert_called_once()
class CohortTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='nightlycohortfixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.note=self.root/'note';self.note.mkdir();self.account=self.root/'account.json';self.proof={'release_week':'2026-W41','start_kind':'NEW_VERSION'};self.account.write_bytes(c.digest.raw_json(self.proof));self.binding={k:c.digest.binding(self.account)[k]for k in('path','sha256')};self.admitted={'receipt':{'record_id':'23300000','release_week':'2026-W41'}};self.actual={'run_id':'Run-189','status':'PUBLICATION_BOUND','exact_publication_binding':True}
 def scope(self,**extra):return c.new_note_specs(self.root,[self.note],{},week='2026-W41',account_discovery=self.binding,predecessor_registration={},**extra)
 def same(self):return patch.object(w,'require_account_discovery',return_value={'status':'EXISTING_WEEKLY_RECORD','record_id':'23300000'}),patch('methods_digest_registration.require_registration',return_value=self.admitted),patch.object(w,'registered_lineage_runs',return_value={'Run-125','Run-127'}),patch.object(c.digest,'current_note_consumer',return_value=self.actual)
 def test_actual_latest_default_predecessor_and_new_default_note_routes(self):
  a,b,d,e=self.same()
  with a,b as reg,d,e as default:specs,discovery=self.scope();self.assertEqual(specs,[{'run_id':'Run-189','path':str(self.note)}]);reg.assert_called_once();default.assert_called_once();self.assertEqual(discovery['record_id'],'23300000')
 def test_missing_or_wrong_current_default_predecessor_holds(self):
  a,b,d,e=self.same();self.admitted['receipt']['record_id']='23226761'
  with a,b,d,e:self.assertRaises(ValueError,self.scope)
 def test_ancestral_note_duplicate_or_nonbound_status_hold(self):
  for change in('ancestor','status','binding','historical_run'):
   a,b,d,e=self.same();actual=deepcopy(self.actual)
   if change=='ancestor':actual['run_id']='Run-127'
   elif change=='status':actual['status']='DRAFT_CHECKS_PASS_NOT_PUBLICATION_BOUND'
   elif change=='binding':actual['exact_publication_binding']=False
   else:actual['run_id']='Run-188'
   with a,b,d,patch.object(c.digest,'current_note_consumer',return_value=actual):self.assertRaises(ValueError,self.scope)
 def test_duplicate_new_note_and_emptycohort_hold(self):
  a,b,d,e=self.same()
  with a,b,d,e:
   for notes in([], [self.note,self.note]):self.assertRaises(ValueError,c.new_note_specs,self.root,notes,{},week='2026-W41',account_discovery=self.binding,predecessor_registration={})
 def test_wrong_discovered_week_hold(self):
  self.proof['release_week']='2026-W42';self.account.write_bytes(c.digest.raw_json(self.proof));self.binding={k:c.digest.binding(self.account)[k]for k in('path','sha256')};a,b,d,e=self.same()
  with a,b,d,e:self.assertRaises(ValueError,self.scope)
 def test_first_week_only_complete_no_existing_proof(self):
  self.proof={'release_week':'2026-W42','start_kind':'CREATE_WEEK'};self.account.write_bytes(c.digest.raw_json(self.proof));self.binding={k:c.digest.binding(self.account)[k]for k in('path','sha256')}
  with patch.object(w,'require_account_discovery',return_value={'status':'NO_EXISTING_WEEKLY_RECORD'}),patch.object(c.digest,'current_note_consumer',return_value=self.actual):specs,_=c.new_note_specs(self.root,[self.note],{},week='2026-W42',account_discovery=self.binding);self.assertEqual(specs[0]['run_id'],'Run-189')
 def test_first_week_with_predecessor_or_wrongkind_hold(self):
  self.proof={'release_week':'2026-W42','start_kind':'NEW_VERSION'};self.account.write_bytes(c.digest.raw_json(self.proof));self.binding={k:c.digest.binding(self.account)[k]for k in('path','sha256')}
  with patch.object(w,'require_account_discovery',return_value={'status':'NO_EXISTING_WEEKLY_RECORD'}):self.assertRaises(ValueError,c.new_note_specs,self.root,[self.note],{},week='2026-W42',account_discovery=self.binding)
 def test_no_independent_W41_holds(self):
  self.proof['start_kind']='CREATE_WEEK';self.account.write_bytes(c.digest.raw_json(self.proof));self.binding={k:c.digest.binding(self.account)[k]for k in('path','sha256')}
  with patch.object(w,'require_account_discovery',return_value={'status':'NO_EXISTING_WEEKLY_RECORD'}):self.assertRaises(ValueError,self.scope)
 def test_package_uses_unmodified_default_prepare_and_require_current(self):
  m={'fixture':'not live package'}
  with patch.object(c,'new_note_specs',return_value=([{'run_id':'Run-189','path':str(self.note)}],{'status':'EXISTING_WEEKLY_RECORD'})),patch.object(c.digest,'prepare',return_value=m)as prep,patch.object(c.digest,'require_current',return_value=m)as current,patch.object(c.digest,'binding',return_value={'path':'unitmanifest','sha256':'a'*64}):
   result=c.stage_weekly_package(self.root,self.root/'package','2026-W41',[self.note],{}, {},'2026-10-08',account_discovery={},render=object());self.assertEqual(result['status'],'ACTUAL_DEFAULT_NOTE_COHORT_AND_METHODS_PACKAGE_STAGED_NOT_PUBLISHED');self.assertEqual(result['zenodo_writes'],0);self.assertFalse(result['certifies']);self.assertEqual(prep.call_args.kwargs['existing_title'],'Viridis Methods Digest — 2026-W41');current.assert_called_once();self.assertNotIn('consume',prep.call_args.kwargs)
 def test_package_consumer_mismatch_hold(self):
  with patch.object(c,'new_note_specs',return_value=([{'run_id':'Run-189','path':str(self.note)}],{'status':'EXISTING_WEEKLY_RECORD'})),patch.object(c.digest,'prepare',return_value={}),patch.object(c.digest,'require_current',return_value={'changed':True}):self.assertRaises(ValueError,c.stage_weekly_package,self.root,self.root/'package','2026-W41',[self.note],{}, {},'2026-10-08',account_discovery={},render=object())
 def test_source_has_no_http_certification_key_or_scheduler_creation(self):
  text=(HERE/'nightly_release_checkpoint.py').read_text()
  for bad in('urllib','subprocess','keychain','create_automation','issue_lean_zero_sorry_certificate','comparator_cloud_lean_verifier'):self.assertNotIn(bad,text)

class ActualApiTests(unittest.TestCase):
 def test_real_digest_prepare_and_require_current_return_manifest_mapping(self):
  # Actual immutable byte package API, with only fixture note-admission inputs.
  # This verifies the real return ABI, not a fabricated live admission.
  with tempfile.TemporaryDirectory(prefix='real-digest-return-')as temp:
   root=Path(temp).resolve();source=root/'source.json';source.write_bytes(c.digest.raw_json({'creators':[{'name':'Fixture Author'}],'license':'cc-by-4.0'}));out=root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/fixture';source_binding=c.digest.binding(source)
   note={'run_id':'Run-189','path':str(root/'note'),'foundation_basis':'INDEPENDENT','section':'MAIN_NOTES','claim_table':[{'lean_theorem':'fixture_theorem','semantic_tier':'DEPTH_NOT_ASSESSED','nonvacuity_label':'certified; nonvacuity not demonstrated','headline_eligible':False}],'prior_dois':[]}
   consumed={'notes':[note],'members':[('fixture-only.txt',b'fixture bytes')],'input_bindings':{},'authority':{}}
   with patch.object(c,'new_note_specs',return_value=([{'run_id':'Run-189','path':str(root/'note')}],{'status':'EXISTING_WEEKLY_RECORD'})),patch.object(c.digest,'consume_notes',return_value=consumed):
    result=c.stage_weekly_package(root,out,'2026-W41',[root/'note'],{},source_binding,'2026-10-08',account_discovery={},render=lambda _:b'%PDF-1.4\nfixture\n%%EOF\n')
    actual=c.digest.require_current(out,root)
    self.assertIsInstance(actual,dict);self.assertEqual(actual['standard'],c.digest.STANDARD);self.assertEqual(result['notes'],['Run-189']);self.assertEqual(result['zenodo_writes'],0)
 def test_tuple_return_regression_is_not_admitted(self):
  with patch.object(c,'new_note_specs',return_value=([{'run_id':'Run-189','path':'fixture-note'}],{'status':'EXISTING_WEEKLY_RECORD'})),patch.object(c.digest,'prepare',return_value={'fixture':'manifest'}),patch.object(c.digest,'require_current',return_value=({'fixture':'manifest'},{})):
   self.assertRaises(ValueError,c.stage_weekly_package,Path('/private/tmp'),Path('/private/tmp/unused-return-fixture'),'2026-W41',[],{}, {},'2026-10-08',account_discovery={},render=object())
