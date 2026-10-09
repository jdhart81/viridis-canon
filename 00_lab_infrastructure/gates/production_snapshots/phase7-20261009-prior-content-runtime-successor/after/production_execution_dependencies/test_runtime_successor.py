from pathlib import Path
import ast,contextlib,copy,hashlib,importlib.util,json,sys,tempfile,types,unittest
from unittest.mock import patch
D=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('prior_content_runtime_test',D/'runtime_successor.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ROOT=m.ROOT;LEDGER=json.loads(m.raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'));_,b=m.bound(LEDGER['enforcement_activation']);_,b=m.bound(json.loads(b)['authorized_runtime_update']);PREVIOUS=json.loads(b)
class GuardTests(unittest.TestCase):
 def test_actual_current97_source_bytes_and79_inventory(self):
  c={r['path']:m.sha(ROOT/r['path'])for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};m.inventory(PREVIOUS,c);self.assertEqual(len(c),79);self.assertEqual(len(PREVIOUS['additional_modules']),57);self.assertEqual(m.ADDITIONAL_COUNT,59)
 def test_missing_archive_fails(self):
  p=copy.deepcopy(PREVIOUS);p['additional_modules'].pop();c={r['path']:r.get('after_sha256',r.get('sha256'))for r in p['runtime_targets']+p['additional_modules']}
  with self.assertRaises(m.Hold):m.inventory(p,c)
 def test_archive_bytes_change_fails(self):
  c={r['path']:r.get('after_sha256',r.get('sha256'))for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};c[next(p for p in c if '/policy_versions/'in p)]='0'*64
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,c)
 def test_protected_target_bytes_change_fails(self):
  c={r['path']:r.get('after_sha256',r.get('sha256'))for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};c[PREVIOUS['runtime_targets'][0]['path']]='0'*64
  with self.assertRaises(m.Hold):m.inventory(PREVIOUS,c)
 def test_namespace_exact_two_legacy_names_and_functions(self):
  before=(D/'BEFORE_phase7_runtime_update.py').read_bytes();after=(D/'proposed/phase7_runtime_update.py').read_bytes();proof=m.namespace_only_delta(before,after);self.assertEqual(set(proof['added']),m.ADDED);self.assertTrue(proof['all_original_functions_and_other_globals_identical']);self.assertEqual(m.RUNTIME_WRITE_COUNT,7)
 def test_namespace_changed_function_fails(self):
  before=(D/'BEFORE_phase7_runtime_update.py').read_bytes();after=(D/'proposed/phase7_runtime_update.py').read_bytes()+b'\n# foreign\n'
  with self.assertRaises(m.Hold):m.namespace_only_delta(before,after)
 def test_unmodified_scientific_helpers_same_identity(self):
  self.assertIs(m.protected,m.e.protected);self.assertIs(m.merged,m.e.merged);self.assertEqual(m.BUILDER_SHA,'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740');self.assertEqual(m.METHODS_SHA,'5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5')
 def test_materials_all32_actual_pins_and_git_blobs(self):
  c={r['path']:m.sha(ROOT/r['path'])for r in PREVIOUS['runtime_targets']+PREVIOUS['additional_modules']};materials={n:(D/'proposed'/n).read_bytes()if n in m.INSTALL_NAMES else(ROOT/(m.PREFIX+n)).read_bytes()for n in m.MATERIAL_NAMES};files={'00_lab_infrastructure/gates/'+n:{'sha':m.git_blob(b)}for n,b in materials.items()};proof=m.prove_materials(c,materials,files);self.assertEqual(len(proof),32)
 def test_actual97_closure_is_physical_only_no_old_current_authority_pass(self):
  f=next(n for n in ast.parse(Path(m.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='physical_predecessor');calls={ast.unparse(n.func)for n in ast.walk(f)if isinstance(n,ast.Call)};self.assertIn('e.read_bound_closure',calls);self.assertNotIn('e.require_current_closure',calls);self.assertNotIn('require_current_closure',calls);self.assertEqual(m.PRIOR_CLOSURE_SHA,'d4321fae40b3306b666042b24239040c01bd60756846bfc986b8b33b8d9678ff')
 def test_four_catalog_entries_typed_exact(self):
  _,b=m.bound(PREVIOUS['policy_version_catalog']);c=json.loads(b);r=m.expected_catalog(c,{},{});self.assertEqual(m.encoded(r),m.encoded(c));self.assertIsNot(r,c)
 def test_fewer_or_duplicate_catalog_entries_fail(self):
  for rows in [[{'execution_consumer_sha256':'0'*64}]*4,[]]:
   with self.assertRaises(m.Hold):m.expected_catalog({'versions':rows},{},{})
 def test_three_scans_actual_CAS_order(self):
  tree=ast.parse(Path(m.__file__).read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='close');calls=sorted((n.lineno,ast.unparse(n.func))for n in ast.walk(f)if isinstance(n,ast.Call)and ast.unparse(n.func)in {'fresh35','corpus.write_guarded_ledger'});self.assertEqual([n for _,n in calls],['fresh35','fresh35','corpus.write_guarded_ledger','fresh35'])
 def test_current_readiness_real_default_build_no_fixed35_admission(self):
  f=next(n for n in ast.parse(Path(m.__file__).read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='require_current_closure');calls={ast.unparse(n.func)for n in ast.walk(f)if isinstance(n,ast.Call)};self.assertIn('corpus.build',calls);self.assertIn('builder.source_session',calls);self.assertIn('builder.verify_loaded',calls);self.assertIn('preserving_population',calls)
 def test_bool_int_distinct(self):self.assertFalse(m.exact({'a':True},{'a':1}))
class PopulationTests(unittest.TestCase):
 def setUp(self):self.base=copy.deepcopy(LEDGER['publication_entities']);self.current=copy.deepcopy(LEDGER)
 def pass_scanned(self):return copy.deepcopy(self.current)
 def test_actual_baseline35_pass(self):self.assertEqual(m.preserving_population(self.current,self.base,self.pass_scanned()),self.base)
 def test_additive36_fresh_preserving_consumer_pass(self):
  extra=copy.deepcopy(self.base[-1]);extra['id']='NEW_GENUINE_REGISTRATION_FIXTURE';extra['registration_receipt']={'path':'test-receipt.json','sha256':'0'*64};self.current['publication_entities'].append(extra);self.assertEqual(len(m.preserving_population(self.current,self.base,self.pass_scanned())),36)
 def test_removed_baseline_row_fails(self):
  self.current['publication_entities'].pop()
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_changed_prior_row_fails_even_if_scanner_reproduces_it(self):
  self.current['publication_entities'][0]['registration_route']='changed'
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_missing_current_registration_fails(self):
  extra=copy.deepcopy(self.base[-1]);extra['id']='MISSING_GENUINE_REGISTRATION_FIXTURE';self.current['publication_entities'].append(extra);scanned=self.pass_scanned();scanned['publication_entities'].pop()
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,scanned)
 def test_new_row_without_current_receipt_binding_fails(self):
  extra=copy.deepcopy(self.base[-1]);extra['id']='NO_RECEIPT_FIXTURE';extra.pop('registration_receipt',None);self.current['publication_entities'].append(extra)
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_new_receipt_fresh_HOLD_unacceptable_fails(self):
  extra=copy.deepcopy(self.base[-1]);extra['id']='INVALID_REGISTRATION_FIXTURE';extra['enforcement_acceptable']=False;self.current['publication_entities'].append(extra)
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_duplicate_current_row_fails(self):
  self.current['publication_entities'].append(copy.deepcopy(self.base[0]))
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_changed_control_fails(self):
  self.current['premise_declaration_cutover_run']='Run-189'
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
 def test_fresh_scanner_controls_change_fails(self):
  scanned=self.pass_scanned();scanned['enforcement_activation']={'foreign':True}
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,scanned)
 def test_true_integer_current_flag_fails(self):
  self.current['publication_entities'][0]['enforcement_acceptable']=1
  with self.assertRaises(m.Hold):m.preserving_population(self.current,self.base,self.pass_scanned())
if __name__=='__main__':unittest.main()
