"""Actual historical source preservation and direct dispatch; no publication."""
import ast,hashlib,inspect,unittest
from pathlib import Path
from unittest.mock import patch
import corpus_ledger as c
import publication_gate as p
import doi_audit as a
import public_metadata_readback as r
import methods_digest_registration as g

FIXTURES=Path(__file__).parent/'fixtures/registration_baselines'
PINS={'corpus_ledger.py':'bfd2ec16c1e9c39ebcd39fdb45ccf9683b6864a95d3496109df49f9a7639a173','publication_gate.py':'a44fe11deccc4d1246d4d2b0fc53621807e1f06061eafff1fb684615fcff7fef','doi_audit.py':'23173076f35f62ca0696544c3a5c7ee2bcf7bc39a8a649390ec8e616c2c06f29','publication_gate_scoped.py':'6c4f4506df1de812101dc5b97efdfbd0ed3d3bb3c5681266fa470474a119c30c','public_metadata_readback.py':'e731c8d61741d53caca7f627f0d400c8238c15fb57bf2bf9b23fc38d0d2ceca7'}
def raw_function(raw,name):
 lines=raw.splitlines(keepends=True);n=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)and n.name==name);return n,b''.join(lines[n.body[0].lineno-1:n.end_lineno])
class DispatchTests(unittest.TestCase):
 def preserve_functions(self,name,module,rename):
  old=(FIXTURES/name).read_bytes();self.assertEqual(hashlib.sha256(old).hexdigest(),PINS[name]);new=Path(module.__file__).read_bytes()
  for n in ast.parse(old).body:
   if not isinstance(n,ast.FunctionDef):continue
   before,oldbody=raw_function(old,n.name);fresh,newbody=raw_function(new,rename.get(n.name,n.name));self.assertEqual(oldbody,newbody,n.name);self.assertEqual(ast.dump(before.args),ast.dump(fresh.args),n.name)
 def test_corpus_original_every_function_exact(self):self.preserve_functions('corpus_ledger.py',c,{'preserve_publication_registrations':'_preserve_publication_registrations_legacy'})
 def test_publication_original_evaluator_default_exact(self):self.preserve_functions('publication_gate.py',p,{'evaluate_publication':'_evaluate_publication_original_legacy'})
 def test_publication_scoped_evaluator_exact(self):self.preserve_functions('publication_gate_scoped.py',p,{'evaluate_publication':'_evaluate_publication_scoped_legacy'})
 def test_doi_audit_every_original_function_exact(self):self.preserve_functions('doi_audit.py',a,{'build_audit':'_build_audit_legacy'})
 def test_public_reader_every_original_function_exact(self):self.preserve_functions('public_metadata_readback.py',r,{'read_record':'_read_record_legacy','readback':'_readback_legacy'})
 def test_every_new_wrapper_is_one_direct_return(self):
  rows=[(c,'_preserve_publication_registrations_source_original','preserve'),(p,'evaluate_publication','evaluate_publication'),(a,'build_audit','augment_audit'),(r,'read_record','public_label_read_record'),(r,'readback','public_label_readback')]
  for module,name,target in rows:
   n,_=raw_function(Path(module.__file__).read_bytes(),name);self.assertEqual(len(n.body),1);self.assertIsInstance(n.body[0],ast.Return);call=n.body[0].value;self.assertIsInstance(call,ast.Call);self.assertEqual(ast.unparse(call.func),'methods_digest_registration.'+target)
 def test_current_corpus_namespace_wrapper_and_old_alias_are_exact(self):
  from phase7_runtime_update import corpus_preservation
  raw=Path(c.__file__).read_bytes();proof=corpus_preservation((FIXTURES/'corpus_ledger.py').read_bytes(),raw)
  self.assertEqual(proof['registry_import_caller']['status'],'EXACT_ORIGINAL_ALIAS_AND_APPROVED_NAMESPACE_WRAPPER')
  self.assertEqual(proof['registry_import_caller']['body_sha256'],{'_preserve_publication_registrations_source_original':'a1f8d99c93e4d88fede85b47dd241124bc1503ea47916198e1e38139f795d028','preserve_publication_registrations':'25191bd9ad9f9ff7bfb00a9ce92173555e56d1da00a503ee883e15123942d94e'})
 def test_corpus_delegates_original_function_and_inputs(self):
  ledger={};previous={'publication_entities':[]}
  with patch.object(g,'preserve',return_value='result')as f:self.assertEqual(c.preserve_publication_registrations(ledger,previous),'result');f.assert_called_once_with(ledger,previous,legacy=c._preserve_publication_registrations_legacy)
 def test_publication_delegates_both_actual_defaults(self):
  with patch.object(g,'evaluate_publication',return_value='result')as f:
   self.assertEqual(p.evaluate_publication(Path('artifact'),{},entity_id='id',inspector='inspector',enforce=True,require_premise_declaration=True),'result');f.assert_called_once_with(Path('artifact'),{},legacy=p._evaluate_publication_original_legacy,scoped_legacy=p._evaluate_publication_scoped_legacy,entity_id='id',inspector='inspector',enforce=True,require_premise_declaration=True)
 def test_doi_wrapper_passes_actual_legacy_result(self):
  with patch.object(a,'_build_audit_legacy',return_value={'old':'audit'})as old,patch.object(g,'augment_audit',return_value='result')as f:
   self.assertEqual(a.build_audit('root',{},certificate_assessor='inspector'),'result');old.assert_called_once_with('root',{},certificate_assessor='inspector');f.assert_called_once_with('root',{}, {'old':'audit'})
 def test_reader_wrapper_passes_unchanged_get_reader(self):
  with patch.object(g,'public_label_read_record',return_value='result')as f:self.assertEqual(r.read_record({'doi':'test'}),'result');f.assert_called_once_with({'doi':'test'},legacy=r._read_record_legacy)
 def test_parallel_reader_wrapper_unchanged_scheduler(self):
  with patch.object(g,'public_label_readback',return_value='result')as f:self.assertEqual(r.readback({'published_records':[]}),'result');f.assert_called_once_with({'published_records':[]},legacy=r._readback_legacy)
 def test_default_legacy_ordinary_failed_artifact_result_unchanged(self):
  artifact=Path('/nonexistent/closed-unit-fixture');ledger={'tree_root':'/nonexistent/closed-unit-fixture','file_entities':[],'run_entities':[],'publication_entities':[]}
  self.assertEqual(p.evaluate_publication(artifact,ledger),p._evaluate_publication_original_legacy(artifact,ledger))
 def test_same_body_missing_named_legacy_dispatch_fails_structural_rule(self):
  raw=Path(c.__file__).read_bytes().replace(b'legacy=_preserve_publication_registrations_legacy',b'legacy=lambda ledger, previous: ledger');n,_=raw_function(raw,'_preserve_publication_registrations_source_original');call=n.body[0].value;arg=next(k.value for k in call.keywords if k.arg=='legacy');self.assertNotIsInstance(arg,ast.Name)
