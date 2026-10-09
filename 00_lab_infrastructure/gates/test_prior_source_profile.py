"""Current source-only preservation and exact prewrite authority regressions."""
from pathlib import Path
from copy import deepcopy
import ast,hashlib,importlib.util,json,tempfile,unittest
import own_record_comparison as own
HERE=Path(__file__).resolve().parent;OLD=HERE/'tests/fixtures/phase7_prior_content_historical_v001'
def functions(p):return {n.name:ast.dump(n)for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
def load(p,n):
 spec=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
class SourceTests(unittest.TestCase):
 def test_non_adapter_own_functions_exact(self):
  a=functions(OLD/'own_record_comparison.py');b=functions(HERE/'own_record_comparison.py')
  for n,v in a.items():
   if n not in{'require_prior_exact','consume_context'}:self.assertEqual(v,b[n],n)
 def test_non_adapter_weekly_functions_exact(self):
  a=functions(OLD/'digest_weekly_state.py');b=functions(HERE/'digest_weekly_state.py')
  for n,v in a.items():
   if n!='registered_relation_template':self.assertEqual(v,b[n],n)
 def test_entire_old_authority_prefix_exact(self):self.assertTrue((HERE/'phase7_policy_versions.py').read_bytes().startswith((OLD/'phase7_policy_versions.py').read_bytes()))
 def test_two_names_all_other_runtime_statements_exact(self):
  def split(p):
   tree=ast.parse(p.read_bytes());out=[];names=None
   for n in tree.body:
    if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='POLICY_MODULE_NAMES'for t in n.targets):names=ast.literal_eval(n.value.args[0])
    else:out.append(ast.dump(n))
   return names,out
  a,x=split(OLD/'phase7_runtime_update.py');b,y=split(HERE/'phase7_runtime_update.py');self.assertEqual(x,y);self.assertEqual(b,a|{'methods_digest_registration_legacy_21b813.py','own_record_comparison_legacy_cf74da.py'})
  for bad in (b|{'foreign.py'},b-{'own_record_comparison_legacy_cf74da.py'}):self.assertNotEqual(b,bad)
 def test_runtime_new_pin_exact(self):
  table=next(n for n in ast.parse((HERE/'weekly_digest_runtime.py').read_bytes()).body if isinstance(n,ast.Assign)and n.targets[0].id=='UNCHANGED');self.assertEqual(ast.literal_eval(table.value)['methods_digest_registration.py'],hashlib.sha256((HERE/'methods_digest_registration.py').read_bytes()).hexdigest())
 def test_runtime_admission_only_adds_two_prewrite_authority_statements(self):
  def fn(p):return next(m for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.ClassDef)and n.name=='ActualRuntime'for m in n.body if isinstance(m,ast.FunctionDef)and m.name=='admission')
  a=fn(OLD/'weekly_digest_runtime.py');b=fn(HERE/'weekly_digest_runtime.py');self.assertEqual(ast.unparse(b.body[4]),"own.require_bound_authority(self.root, plan['authority'])");del b.body[3:5];self.assertEqual(ast.dump(a),ast.dump(b))
 def test_six_prior_download_checks_and_actual_report_preserved(self):
  before=(OLD/'weekly_digest_boundary.py').read_text();after=(HERE/'weekly_digest_boundary.py').read_text()
  for line in before.splitlines():
   if 'prior_files=successor.predecessor_inventory'in line or 'PRIOR_EXACT_MAIN_SET'in line or 'for row in prior_files:self.downloads.get'in line:self.assertIn(line,after)
  self.assertIn("self.last_prior_audit=self.emit('prior_audits/'+Path(nb['path']).stem+'.json'",after);self.assertIn("'prior_processing_audit':deepcopy(self.last_prior_audit)",after)
 def test_checkpoint_full_real_pair_contract_allows_diagnostic_only(self):
  s=(OLD/'weekly_checkpoint_replay.py').read_text();self.assertNotIn('set(report)',s);self.assertIn("metadata.exact(report['expected_native'],native)and metadata.exact(report['expected_legacy'],legacy)",s)
class AuthorityTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.raw=(HERE/'test_fixtures/prior_content_authority.md').read_bytes();self.live=self.root/'reports/verification-coverage/GAME_PLAN.md';self.live.parent.mkdir(parents=True);self.live.write_bytes(self.raw);self.snapshot=self.root/'authority/GAME_PLAN_SNAPSHOT.md';self.snapshot.parent.mkdir();self.snapshot.write_bytes(self.raw);self.path=self.root/'authority/AUTHORITY.json';self.write()
 def bind(self,p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 def write(self):self.path.write_text(json.dumps({'standard':'VRS-EXACT-OWN-RECORD-AUTHORITY-1','authority_snapshot':self.bind(self.snapshot),'section_sha256':own.AUTHORITY_SECTION_SHA256,'actual_sha256':hashlib.sha256(self.snapshot.read_bytes()).hexdigest()}));self.binding=self.bind(self.path)
 def check(self):return own.require_bound_authority(self.root,self.binding)
 def test_exact_snapshot_and_live_sections_pass(self):self.assertEqual(self.check()['prior_section_sha256'],own.PRIOR_AUTHORITY_SECTION_SHA256)
 def test_old_only_snapshot_fails_before_write(self):self.snapshot.write_bytes(self.raw[:self.raw.index(own.PRIOR_AUTHORITY_HEADER.encode())-1]);self.write();self.assertRaises(ValueError,self.check)
 def test_changed_snapshot_refrozen_or_live_section_fails(self):
  self.snapshot.write_bytes(self.raw.replace(b'Nothing in the processing list ever is.',b'Nothing in the processing list is.'));self.write();self.assertRaises(ValueError,self.check);self.snapshot.write_bytes(self.raw);self.write();self.live.write_bytes(self.raw.replace(b'Nothing in the processing list ever is.',b'Nothing in the processing list is.'));self.assertRaises(ValueError,self.check)
 def test_mutable_snapshot_alias_fails(self):self.snapshot=self.live;self.write();self.assertRaises(ValueError,self.check)
 def test_wrong_observed_full_snapshot_hash_fails(self):
  a=json.loads(self.path.read_bytes());a['actual_sha256']='a'*64;self.path.write_text(json.dumps(a));self.binding=self.bind(self.path);self.assertRaises(ValueError,self.check)
 def test_future_append_does_not_invalidate_immutable_section(self):self.live.write_bytes(self.raw+b'\n---\n\n## Future independently approved section\ncontent\n');self.check()
 def test_framing_keeps_exact_historical_science_view(self):
  v=load(HERE/'phase7_policy_versions.py','new_versions');old=load(OLD/'phase7_policy_versions.py','old_versions');prefix=self.raw[:self.raw.index(v.PRIOR_CONTENT_HEADER.encode())-6];self.assertEqual(v.normalize_authority_plan(self.raw),old.normalize_authority_plan(prefix))
 def test_framing_changed_rule_boundary_or_unknown_tail_fails(self):
  v=load(HERE/'phase7_policy_versions.py','new_bad_versions')
  for raw in (self.raw.replace(b'Nothing in the processing list ever is.',b'Nothing in the processing list is.'),self.raw+b'\n## Unknown\ntext\n',self.raw.replace(b'\n---\n\n'+v.PRIOR_CONTENT_HEADER.encode(),b'\n--- \n\n'+v.PRIOR_CONTENT_HEADER.encode())):
   with self.subTest(rawsha=hashlib.sha256(raw).hexdigest()):self.assertRaises(ValueError,v.normalize_authority_plan,raw)
if __name__=='__main__':unittest.main()
