"""Portable unit fixtures only; never certificate/publication evidence."""
from copy import deepcopy
from pathlib import Path
import ast,datetime as dt,hashlib,json,sys,tempfile,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
G=HERE
sys.path[:0]=[str(HERE)]
import nightly_minimal_policy as p
import phase7_policy_versions as v
CANDIDATE='''import Mathlib
namespace Example
variable (a : ℝ)
theorem bounded (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) : q ≤ 1 := by exact hq1
theorem identical (x : ℕ) : x = x := by rfl
theorem witness : (0 : ℝ) ≤ 1 := by norm_num
end Example
'''
FORMAL=CANDIDATE.replace('by exact hq1','by sorry').replace('by rfl','by sorry').replace('by norm_num','by sorry')
INSPECTION={'certified_theorems':['bounded','identical','witness'],'nonvacuity':['witness']}
class ScopeTests(unittest.TestCase):
 def scope(self):return p.claim_scope(CANDIDATE,FORMAL,INSPECTION,['bounded','identical'])
 def test_exact_hypotheses_conclusion_context_and_model(self):
  s=self.scope();self.assertIn('hq0',s[0]['explicit_binders_and_hypotheses']);self.assertIn('hq1',s[0]['explicit_binders_and_hypotheses']);self.assertEqual(s[0]['conclusion'],'q ≤ 1');self.assertEqual(s[0]['ambient_source_context'],[{'line':3,'source_text':'variable (a : ℝ)'}]);self.assertEqual(s[0]['model_fidelity']['empirically_identified'],[])
 def test_reflexivity_is_labelled_trivial_without_probe(self):self.assertEqual(self.scope()[1]['evidence_class'],'CERTIFIED_TRIVIAL')
 def test_optional_claim_witness_and_depth_dont_invent_gates(self):
  s=self.scope();self.assertTrue(all(x['nonvacuity_obligation']is None for x in s));self.assertTrue(all(x['scope_status']=='SOURCE_BOUND_CURRENT_DETERMINISTIC_REVIEW_REQUIRED'for x in s));self.assertNotIn('SUBSTANTIVE',json.dumps(s))
 def test_certified_export_selection_required(self):
  for selected in[[],['foreign'],['bounded','bounded'],'bounded',[True]]:
   with self.subTest(selected=selected):self.assertRaises(ValueError,p.claim_scope,CANDIDATE,FORMAL,INSPECTION,selected)
 def test_runlevel_nonvacuity_missing_never_discharge(self):
  for nv in[[],['witness','witness']]:
   i=deepcopy(INSPECTION);i['nonvacuity']=nv;self.assertRaises(ValueError,p.claim_scope,CANDIDATE,FORMAL,i,['bounded'])
 def test_aligned_hypothesis_or_conclusion_mismatch(self):
  for old,new in[('(hq0 : 0 ≤ q)',''),('(hq1 : q ≤ 1)','(hq1 : q < 1)'),(': q ≤ 1',': q < 1')]:
   with self.subTest(new=new):self.assertRaises(ValueError,p.claim_scope,CANDIDATE,FORMAL.replace(old,new),INSPECTION,['bounded'])
 def test_ambient_hypothesis_not_omitted(self):self.assertEqual(self.scope()[0]['ambient_source_context'][0]['source_text'],'variable (a : ℝ)')
 def test_vacuous_headline_is_not_selected(self):
  for typ in['True','False']:
   c='theorem vacuous : '+typ+' := by sorry';i={'certified_theorems':['vacuous'],'nonvacuity':['witness']};self.assertRaises(ValueError,p.claim_scope,c,c,i,['vacuous'])
 def test_prior_historical_runs_not_generic(self):
  for run in['Run-188','Run-META-001','Run-900','Run-190x','Run-001','Run-0100']:
   self.assertRaises(ValueError,p.canonical_run,run)
 def test_new_nightly_run_canonical(self):self.assertEqual(p.canonical_run('Run-189'),'Run-189');self.assertEqual(p.canonical_run('Run-899'),'Run-899')
 def test_frozen_paper_exact_including_disclaimer(self):
  s=self.scope();b=p.expected_paper('Run-189','INDEPENDENT',s);main=p.validate_exact_body('Run-189','INDEPENDENT',s,b);self.assertIn(p.DISCLAIMER,main);self.assertNotIn(p.ARCHIVE_MARKER,main);self.assertIn(b'Entirely UNCERTIFIED',b)
 def test_number_hypothesis_science_banner_disclaimer_mutations_hold(self):
  s=self.scope();b=p.expected_paper('Run-189','INDEPENDENT',s)
  mutations=[b.replace(b'No additional equation',b'We derive a new physical law. No additional equation'),b.replace(b'Run-189',b'Run-190'),b.replace(p.DISCLAIMER.encode(),b'Validated empirically',1),b.replace(b'Every sentence',b'Some sentences'),b+b'\nExtra theorem claim.\n']
  for v0 in mutations:self.assertRaises(ValueError,p.validate_exact_body,'Run-189','INDEPENDENT',s,v0)
 def test_unlisted_foundation_basis_hold(self):self.assertRaises(ValueError,p.expected_paper,'Run-189','VERIFIED_PHYSICS',self.scope())
 def test_future_or_naive_time_is_not_accepted(self):self.assertRaises(ValueError,p.time,'2026-01-01T00:00:00')
class ManifestTests(unittest.TestCase):
 def setUp(self):
  self.values={'run':'Run-189','inspection':{'candidate_path':'/exact/candidate.lean','candidate_sha256':'a'*64}}
  self.source={'certificate':{'path':'/exact/certificate.json','sha256':'b'*64}}
  uploads=[{'filename':n,'sha256':'c'*64}for n in sorted(p.UPLOAD_NAMES)]
  self.manifest={'standard':p.scoped.STANDARD,'scope':p.scoped.REVIEW_SCOPE,'run_id':'Run-189','certificate':self.source['certificate'],'candidate':{'path':'/exact/candidate.lean','sha256':'a'*64},'formal_statement':{'path':'/exact/statement.lean','sha256':'d'*64},'claim_map':next(x for x in uploads if x['filename']=='SCOPED_CLAIM_MAP.json'),'statement_inventory':next(x for x in uploads if x['filename']=='SCOPED_STATEMENT_INVENTORY.json'),'foundation_basis':next(x for x in uploads if x['filename']=='SCOPED_FOUNDATION_BASIS.json'),'uploads':uploads,'final_tex_sha256':'e'*64,'final_pdf_sha256':'f'*64,'statement_scope':[{'fixture':'no admission'}]}
 def check(self):return p.require_manifest(self.manifest,self.values,self.source)
 def test_exactclosed_manifest_pass(self):self.assertEqual(self.check(),self.manifest)
 def test_every_missing_manifest_field_hold(self):
  for field in p.MANIFEST_FIELDS:
   with self.subTest(field=field):m=deepcopy(self.manifest);m.pop(field);self.assertRaises(ValueError,p.require_manifest,m,self.values,self.source)
 def test_extra_scientific_field_hold(self):self.manifest['scientific_claim']='new physics';self.assertRaises(ValueError,self.check)
 def test_missing_any_publicfile_hold(self):
  for name in p.UPLOAD_NAMES:
   with self.subTest(name=name):m=deepcopy(self.manifest);m['uploads']=[x for x in m['uploads']if x['filename']!=name];self.assertRaises(ValueError,p.require_manifest,m,self.values,self.source)
 def test_extra_public_science_file_hold(self):self.manifest['uploads'].append({'filename':'NEW_THEOREM.lean','sha256':'1'*64});self.assertRaises(ValueError,self.check)
 def test_duplicate_publicfile_hold(self):self.manifest['uploads'][-1]=deepcopy(self.manifest['uploads'][0]);self.assertRaises(ValueError,self.check)
 def test_hash_and_binding_field_shape_hold(self):
  for fn in[lambda m:m['uploads'][0].__setitem__('sha256','wrong'),lambda m:m['uploads'][0].__setitem__('field','unclassified'),lambda m:m.__setitem__('certificate',{'path':'/wrong','sha256':'b'*64}),lambda m:m['candidate'].__setitem__('sha256','f'*64),lambda m:m['claim_map'].__setitem__('filename','other.json')]:
   m=deepcopy(self.manifest);fn(m);self.assertRaises(ValueError,p.require_manifest,m,self.values,self.source)
 def test_wrong_run_standard_or_scope_hold(self):
  for key,val in[('run_id','Run-190'),('scope','SCIENTIFIC_FULL_PAPER'),('standard','NEW')]:
   m=deepcopy(self.manifest);m[key]=val;self.assertRaises(ValueError,p.require_manifest,m,self.values,self.source)
class ArtifactIOTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='nightlyscopefixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
 def test_bound_file_exact_pass_and_change_hold(self):
  f=self.root/'p';f.write_bytes(b'original');b=p.binding(f);seen={};self.assertEqual(p.read(self.root,b,seen)[1],b'original');f.write_bytes(b'changed');self.assertRaises(ValueError,p.finish,seen)
 def test_unlisted_binding_field_missing_file_foreign_file_hold(self):
  for b in[{'path':str(self.root/'missing'),'sha256':'a'*64},{'path':'/etc/hosts','sha256':'a'*64},{'path':str(self.root/'missing'),'sha256':'a'*64,'extra':True}]:self.assertRaises(ValueError,p.read,self.root,b,{})
 def test_symlink_refused(self):
  f=self.root/'file';f.write_bytes(b'exact');l=self.root/'alias';l.symlink_to(f);self.assertRaises(ValueError,p.read,self.root,{'path':str(l),'sha256':p.d.sha(f)},{})
 def test_exclusive_immutable_output_no_rewrite(self):
  import prepare_nightly_note as generator
  f=self.root/'out';generator.exclusive(f,b'exact');self.assertEqual(f.read_bytes(),b'exact');self.assertRaises(FileExistsError,generator.exclusive,f,b'changed');self.assertEqual(f.read_bytes(),b'exact')
 def test_wrong_or_malformed_source_contract_hold_before_certificate(self):
  for s in[{}, {'standard':p.SOURCE_STANDARD}, {'standard':'fake','status':'CERTIFIED','run_id':'Run-189','certifies':True}]:self.assertRaises(ValueError,p.source_values,self.root,s,{})
class DefaultDispatchTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='nightlydispatchfixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.note=self.root/'note';self.note.mkdir()
 def rule(self,v0):self.note.joinpath('PHASE7_RULE_EXECUTION.json').write_text(json.dumps(v0))
 def test_oldreceipt_no_newconsumer_import_or_runtime_side_effect(self):
  self.rule({'standard':'VRS-PHASE7-APPROVED-RULE-EXECUTION-1'});self.assertIsNone(v._nightly_scope_implementation(self.note,self.root))
 def test_old_require_route_body_unchanged(self):
  self.rule({'standard':'old'})
  with patch.object(v,'_require_note_publication_bound_historical',return_value={'old':'exact'})as old:self.assertEqual(v.require_note_publication_bound(self.note,self.root,{},object()),{'old':'exact'});old.assert_called_once()
 def test_old_binding_route_body_unchanged(self):
  self.rule({'standard':'old'})
  with patch.object(v,'_prepare_publication_binding_historical',return_value={'old':'exact'})as old:self.assertEqual(v.prepare_publication_binding(self.note,self.root,{},object()),{'old':'exact'});old.assert_called_once()
 def test_newreceipt_without_actual_installed_runtime_never_pass(self):self.rule({'standard':p.RULE_STANDARD,'execution_consumer_sha256':p.source_sha()});self.assertRaises(Exception,v._nightly_scope_implementation,self.note,self.root)
 def test_dispatcher_original_raw_prefix_byteexact(self):self.assertTrue((HERE/'phase7_policy_versions.py').read_bytes().startswith((HERE/'BEFORE_phase7_policy_versions.py').read_bytes()))
 def test_all_historical_dispatch_functions_byteexact(self):
  old=(HERE/'BEFORE_phase7_policy_versions.py').read_text();new=(HERE/'phase7_policy_versions.py').read_text();nodes=ast.parse(new).body
  for node in ast.parse(old).body:
   if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
    first=next(n for n in nodes if isinstance(n,type(node))and n.name==node.name);self.assertEqual(ast.get_source_segment(old,node),ast.get_source_segment(new,first))
 def test_no_verifier_network_or_issuer_changes(self):
  text=(HERE/'nightly_minimal_policy.py').read_text()
  for forbidden in['subprocess','urlopen(', 'requests.post', 'local_lean_fallback','issue_lean_zero_sorry_certificate(']:self.assertNotIn(forbidden,text)
 def test_no_fake_auditrow_or_optional_proof_gate(self):
  text=(HERE/'nightly_minimal_policy.py').read_text();self.assertIn("'new_historical_audit_row':False",text);self.assertIn("'optional_depth_or_claim_witness_is_release_gate':False",text)
class SourceContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='nightlysourcefixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  def saved(name,body):
   f=self.root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(body if isinstance(body,bytes)else p.d.raw_json(body));return p.binding(f)
  self.saved=saved
  self.cb=saved('candidate.lean',CANDIDATE.encode());self.fb=saved('formal.lean',FORMAL.encode())
  self.cert={'run_id':'Run-189','issued_at_utc':'2026-10-07T12:00:00+00:00','bindings':{'candidate_proof':self.cb,'formal_statement':self.fb},'foundation_basis':'INDEPENDENT'}
  self.certbinding=saved('certificate.json',self.cert)
  self.inspection={**deepcopy(INSPECTION),'valid':True,'run_id':'Run-189','sha256':self.certbinding['sha256'],'candidate_path':self.cb['path'],'candidate_sha256':self.cb['sha256']}
  cycle=saved('cycle.json',{'observed_at_utc':'2026-10-07T13:00:00+00:00','local_lean_execution':False,'checkpoint':saved('FINISH.json',{'unit_fixture':'not_actual_pass'}),'run_flows':[{'id':'Run-189'}]})
  pins=[]
  for name in ['nightly_minimal_policy.py','certificate_inspection.py','scoped_release.py','theorem_coverage.py','premise_declaration.py','science_release_stage.py','phase7_audit_policy.py']:
   b=saved('sources/'+name,b'unit fixture source closure');pins.append({'name':name,**b})
  self.source={'standard':p.SOURCE_STANDARD,'status':'STAGED_SOURCE_NOT_REVIEW_OR_PUBLICATION_BOUND','run_id':'Run-189','certificate':self.certbinding,'source_manuscript':saved('source.tex',b'historical physical assumptions'),'before_metadata':saved('metadata.json',{'metadata':{'title':'Keep original title','creators':[{'name':'Hart, Justin D.'}]}}),'selected_theorems':['bounded','identical'],'foundation_basis':'INDEPENDENT','selection_at_utc':'2026-10-07T14:00:00+00:00','selection_invocation':'later-source-invocation-fixture','prior_cycle':cycle,'source_pins':pins,'source_generator_sha256':p.source_sha(),'certifies':False}
 def check(self,source=None):
  # Only this unit fixture certificate acceptance seam is mocked. Actual
  # Comparator/main-certificate consumer coverage is tested separately.
  with patch.object(p,'inspect_certificate',return_value=self.inspection):return p.source_values(self.root,source or self.source,{})
 def test_closed_source_fixture_retains_exact_science_and_prior_checkpoint(self):
  v0=self.check();self.assertEqual(v0['run'],'Run-189');self.assertEqual(v0['candidate_text'],CANDIDATE);self.assertEqual(v0['scope'][0]['conclusion'],'q ≤ 1');self.assertFalse('status'in v0)
 def test_invalid_certificate_consumer_never_falls_back(self):self.inspection['valid']=False;self.assertRaises(ValueError,self.check)
 def test_certificate_wrong_run_or_hash_hold(self):
  for key,val in[('run_id','Run-190'),('sha256','f'*64)]:
   original=self.inspection[key];self.inspection[key]=val;self.assertRaises(ValueError,self.check);self.inspection[key]=original
 def test_missing_run_level_nonvacuity_hold(self):self.inspection['nonvacuity']=[];self.assertRaises(ValueError,self.check)
 def test_missing_required_source_or_duplicate_name_hold(self):
  for fn in[lambda s:s['source_pins'].pop(),lambda s:s['source_pins'].append(deepcopy(s['source_pins'][0])),lambda s:s.__setitem__('source_generator_sha256','f'*64)]:
   s=deepcopy(self.source);fn(s);self.assertRaises(ValueError,self.check,s)
 def test_source_hash_change_hold(self):Path(self.source['source_manuscript']['path']).write_bytes(b'changed');self.assertRaises(ValueError,self.check)
 def test_same_or_future_or_pre_certificate_stage_hold(self):
  for at in['2026-10-07T13:00:00+00:00','2026-10-06T14:00:00+00:00',(p.now()+dt.timedelta(hours=1)).isoformat()]:
   s=deepcopy(self.source);s['selection_at_utc']=at;self.assertRaises(ValueError,self.check,s)
 def test_wrong_prior_run_locallean_missing_checkpoint_hold(self):
  old=json.loads(Path(self.source['prior_cycle']['path']).read_bytes())
  for fn in[lambda c:c.__setitem__('run_flows',[{'id':'Run-188'}]),lambda c:c.__setitem__('local_lean_execution',True),lambda c:c.pop('checkpoint'),lambda c:c.__setitem__('observed_at_utc','2026-10-07T15:00:00+00:00')]:
   c=deepcopy(old);fn(c);s=deepcopy(self.source);s['prior_cycle']=self.saved('altered_cycle.json',c);self.assertRaises(ValueError,self.check,s)
 def test_nested_certificate_binding_missing_or_ambiguous_hold(self):
  original=self.cert['bindings']['candidate_proof']
  for value in[{'path':'missing.lean','sha256':'a'*64},{'path':'../foreign','sha256':'a'*64}]:
   cert=deepcopy(self.cert);cert['bindings']['candidate_proof']=value;s=deepcopy(self.source);s['certificate']=self.saved('badcertificate.json',cert);self.inspection['sha256']=s['certificate']['sha256'];self.assertRaises(ValueError,self.check,s)
class NominatedDispatchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='nightlynominatedfixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.note=self.root/'note';self.note.mkdir();self.path='RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_minimal_policy.py';self.module=self.root/self.path;self.module.parent.mkdir(parents=True);self.module.write_bytes(Path(p.__file__).read_bytes());self.runtime={'additional_modules':[{'path':self.path,'sha256':p.source_sha()}]}
  self.commit_runtime()
  self.note.joinpath('PHASE7_RULE_EXECUTION.json').write_text(json.dumps({'standard':p.RULE_STANDARD,'execution_consumer_sha256':p.source_sha()}))
 def commit_runtime(self):
  r=self.root/'runtime.json';r.write_bytes(p.d.raw_json(self.runtime));a=self.root/'activation.json';a.write_bytes(p.d.raw_json({'authorized_runtime_update':p.binding(r)}));l=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';l.write_bytes(p.d.raw_json({'enforcement_activation':p.binding(a)}))
 def check(self):
  # A nominated-source selector fixture, never a publication consumer pass.
  with patch.object(v,'current_catalog',return_value={}),patch.object(p,'__file__',str(self.module)):
   return v._nightly_scope_implementation(self.note,self.root)
 def test_exact_nominated_source_selection_not_science_pass(self):self.assertIs(self.check(),p)
 def test_wrong_nominated_hash_path_or_duplicate_hold(self):
  for rows in [[{'path':self.path,'sha256':'f'*64}],[{'path':self.path+'-alias','sha256':p.source_sha()}],self.runtime['additional_modules']*2]:
   self.runtime={'additional_modules':rows};self.commit_runtime();self.assertRaises(ValueError,self.check)
 def test_wrong_loaded_source_identity_hold(self):
  with patch.object(v,'current_catalog',return_value={}):self.assertRaises(ValueError,v._nightly_scope_implementation,self.note,self.root)
 def test_changed_activated_module_bytes_hold(self):self.module.write_bytes(b'changed');self.assertRaises(ValueError,self.check)

if __name__=='__main__':unittest.main()
