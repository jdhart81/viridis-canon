from pathlib import Path
import ast, hashlib, importlib.util, sys, unittest
BASE=Path(__file__).parent/'tests/fixtures/authority_appendix_v001'
RUNTIME=Path(__file__).parent
sys.path.insert(0,str(RUNTIME))
def load(name, filename):
 spec=importlib.util.spec_from_file_location(name,(RUNTIME if filename=='phase7_policy_versions.py' else BASE)/filename)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
old=load('_phase7_authority_before','BEFORE_phase7_policy_versions.py')
new=load('_phase7_authority_after','phase7_policy_versions.py')
current=(BASE/'GAME_PLAN_CURRENT.md').read_bytes()
prior=(BASE/'GAME_PLAN_PRE_OPERATING.md').read_bytes()
expected=old.normalize_authority_plan(prior)
headers=(new.PRIOR_CONTENT_HEADER,new.OWN_RECORD_HEADER,new.APPENDIX_HEADER,new.SIMPLIFICATION_HEADER,new.DECOUPLING_HEADER)
class OperatingAuthorityParserTests(unittest.TestCase):
 def reject(self,data):
  with self.assertRaises(ValueError):new.normalize_authority_plan(data)
 def test_current_approved_appendix_accepted(self):
  self.assertEqual(new.normalize_authority_plan(current),expected)
 def test_exact_old_terminal_plan_still_accepted(self):
  self.assertEqual(new.normalize_authority_plan(prior),expected)
 def test_multiple_later_operational_appendices_accepted(self):
  more=current+b'\n---\n\n## Later operational clarification\nUse the existing pipeline.\n\n---\n\n## Another operational note\nRead before writing.\n'
  self.assertEqual(new.normalize_authority_plan(more),expected)
 def test_later_operational_text_is_not_scientific_evidence(self):
  changed=current.replace(b'up to 24 h',b'up to 12 h')
  self.assertEqual(new.normalize_authority_plan(changed),expected)
 def test_undelimited_operational_appendix_rejected(self):
  self.reject(prior+b'\n## Undelimited operation\ntext\n')
 def test_no_new_exact_operating_mode_pin(self):
  source=(RUNTIME/'phase7_policy_versions.py').read_text()
  self.assertNotIn('OPERATING_MODE_SECTION_SHA256',source)
  self.assertNotIn('OPERATING_MODE_HEADER=',source)
 def test_raw_input_bytes_unchanged(self):
  raw=current;before=hashlib.sha256(raw).hexdigest()
  new.normalize_authority_plan(raw)
  self.assertEqual(hashlib.sha256(raw).hexdigest(),before)
  self.assertEqual(raw,(BASE/'GAME_PLAN_CURRENT.md').read_bytes())
 def test_no_historical_view_bytes_lost(self):
  self.assertEqual(new.normalize_authority_plan(current),old.normalize_authority_plan(prior))
  self.assertEqual(new._normalize_authority_pre_prior_processing(prior[:prior.index(new.PRIOR_CONTENT_HEADER.encode())-6]),expected)
 def test_changed_prior_content_rejected(self):
  self.reject(current.replace(b'Nothing in the processing list ever is.',b'Anything in the processing list ever is.'))
 def test_changed_own_record_section_rejected(self):
  self.reject(current.replace(b'Everything else Zenodo sets',b'Elsewhere else Zenodo sets'))
 def test_changed_catalog_scientific_section_rejected(self):
  self.reject(current.replace(b'Existing catalog records keep',b'Existing catalog records lose'))
 def test_changed_minimal_gate_scientific_section_rejected(self):
  self.reject(current.replace(b'Per-claim witnesses, triviality/depth probes',b'Per-claim witnesses and triviality/depth probes'))
 def test_changed_decoupled_scientific_section_rejected(self):
  start,end=new._authority_section(current,new.DECOUPLING_HEADER)
  changed=current[:start]+current[start:end].replace(b'\n',b' \n',1)+current[end:]
  self.reject(changed)
 def test_every_scientific_header_duplicate_rejected_even_in_ignored_tail(self):
  for header in headers:
   with self.subTest(header=header):self.reject(current+b'\n'+header.encode()+b'\nDuplicate\n')
 def test_exact_prior_to_operating_delimiter_required(self):
  a=current.index(b'## OPERATING MODE ')
  for wrong in (b'\n--- \n\n',b'\n----\n\n',b'\n\n',b'\n---\n\n\n'):
   with self.subTest(delimiter=wrong):self.reject(current[:a-6]+wrong+current[a:])
 def test_extra_prior_scientific_line_rejected(self):
  a=current.index(b'## OPERATING MODE ')
  self.reject(current[:a-6]+b'\nUnapproved scientific text\n'+current[a-6:])
 def test_prior_to_own_delimiter_stays_exact(self):
  a=current.index(new.PRIOR_CONTENT_HEADER.encode())
  self.reject(current[:a-6]+b'\n--- \n\n'+current[a:])
 def test_scientific_order_rejected(self):
  own_a,own_b=new._authority_section(current,new.OWN_RECORD_HEADER)
  prior_a,prior_b=new._authority_section(current,new.PRIOR_CONTENT_HEADER)
  reordered=current[:own_a]+current[prior_a:prior_b]+current[own_a:own_b]+current[prior_b:]
  self.reject(reordered)
 def test_bytes_input_required(self):
  self.reject(current.decode());self.reject(bytearray(current));self.reject(None)
 def test_historical_no_prior_path_unchanged(self):
  a=prior.index(new.PRIOR_CONTENT_HEADER.encode())
  historical=prior[:a-6]
  self.assertEqual(new.normalize_authority_plan(historical),old.normalize_authority_plan(historical))
 def test_only_final_normalizer_ast_changes(self):
  before=ast.parse((BASE/'BEFORE_phase7_policy_versions.py').read_text()).body
  after=ast.parse((RUNTIME/'phase7_policy_versions.py').read_text()).body
  self.assertEqual(len(before),len(after))
  changed=[(a,b)for a,b in zip(before,after)if ast.dump(a)!=ast.dump(b)]
  self.assertEqual(len(changed),1)
  self.assertTrue(isinstance(changed[0][0],ast.FunctionDef))
  self.assertEqual(changed[0][0].name,'normalize_authority_plan')
  self.assertEqual(changed[0][1].name,'normalize_authority_plan')
  self.assertEqual(ast.dump(changed[0][0].body[-1]),ast.dump(changed[0][1].body[-1]))
if __name__=='__main__':unittest.main(verbosity=2)
