from pathlib import Path
import ast,contextlib,hashlib,importlib.util,json,tempfile,types,unittest
from unittest.mock import patch
D=Path(__file__).resolve().parent

def load(name):
 p=D/(name+'.py');s=importlib.util.spec_from_file_location('test_'+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Pins(unittest.TestCase):
 def test_root_construction_closed_CORE_adds_only_two_legacy_names(self):
  m=load('prepare_weekly_configuration');old=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/2026-10-08/first-digest-audited-catalog-backlog-v001/own-record-weekly-source-adoption-v001/prepare_weekly_configuration.py');tree=ast.parse(old.read_bytes());n=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='CORE'for t in n.targets));self.assertEqual(m.CORE-ast.literal_eval(n.value),{'own_record_comparison_legacy_cf74da.py','methods_digest_registration_legacy_21b813.py'})
 def test_root_adopter_literal_CONFIG_matches_actual(self):
  a=load('root_weekly_configuration');self.assertEqual(a.CONFIG_SHA,hashlib.sha256((D/'prepare_weekly_configuration.py').read_bytes()).hexdigest());self.assertEqual(a.PRODUCTION['prepare_weekly_configuration.py'],a.CONFIG_SHA)
 def test_extension_pin_matches_actual_adopter(self):
  x=load('root_weekly_purpose_specs');self.assertEqual(x.ADOPTER_SHA,hashlib.sha256((D/'root_weekly_configuration.py').read_bytes()).hexdigest())
 def test_coordinator_every_literal_exact_actual_source(self):
  c=load('root_orchestration');a,x,u=c.callers();self.assertEqual(Path(a.__file__),c.ADOPTER);self.assertEqual(Path(x.__file__),c.EXTENSION);self.assertEqual(Path(u.__file__),c.UTILITY)
 def test_recovery_actual_entrypoint_no_http_or_newversion(self):
  tree=ast.parse((D/'root_orchestration.py').read_bytes());f=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='recover_existing_draft');calls={ast.unparse(n.func)for n in ast.walk(f)if isinstance(n,ast.Call)};self.assertIn('entry.recover_owned_creation',calls);self.assertIn('a.preflight_sources',calls);self.assertIn('u.require_current_closure',calls);self.assertFalse(any('request' in n or 'urlopen' in n for n in calls));self.assertFalse(any(isinstance(n,ast.Constant)and n.value=='NEW_VERSION'for n in ast.walk(f)))
 def test_original_private_dependencies_remain_byte_exact(self):
  c=load('root_orchestration');self.assertTrue(all(c.sha(r['path'])==r['sha256']for r in c.DEPENDENCIES));self.assertEqual(c.DEPENDENCIES[5]['sha256'],'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740')
 def test_frozen_pending_production_bytes_match_actual_source(self):
  a=load('root_weekly_configuration');p=json.loads((D/'FINAL_POLICY_BINDINGS.json').read_bytes());self.assertEqual(a.PRODUCTION['own_prior_record.py'],p['own_prior_record.py']['sha256']);self.assertEqual(a.PRODUCTION['weekly_digest_runtime.py'],p['weekly_digest_runtime.py']['sha256'])
 def test_no_automatic_entrypoint(self):
  for name in ['runtime_successor','root_orchestration','root_weekly_configuration','root_weekly_purpose_specs','prepare_weekly_configuration']:self.assertIn("raise SystemExit('HOLD:",(D/(name+'.py')).read_text())
if __name__=='__main__':unittest.main()
