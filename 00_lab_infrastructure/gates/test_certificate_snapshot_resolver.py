"""Portable regression for unchanged inspector binding resolution reuse."""
import ast,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
G=HERE if (HERE/'certificate_inspection.py').is_file() else HERE.parent
if not (G/'certificate_inspection.py').is_file():
 G=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/RESEARCH_PIPELINE_v2/verification_coverage_gates')
POLICY=HERE/'phase7_audit_policy.py' if (HERE/'phase7_audit_policy.py').is_file() else G/'phase7_audit_policy.py'
sys.path.insert(0,str(G));spec=importlib.util.spec_from_file_location('resolver_policy_proposal',POLICY);policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
from certificate_inspection import resolve_binding

def h(b):return hashlib.sha256(b).hexdigest()
class ResolverTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();(self.root/'RESEARCH_PIPELINE_v2').mkdir();self.snap={}
 def tearDown(self):self.tmp.cleanup()
 def file(self,name,b=b'exact'):
  p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);return {'path':name,'sha256':h(b)}
 def cert(self,bindings):
  c={'bindings':bindings};raw=(json.dumps(c)+'\n').encode();p=self.root/'CERT.json';p.write_bytes(raw);return {'path':'CERT.json','sha256':h(raw)}
 def inspect(self,p,r):
  c=json.loads(p.read_bytes());return {'valid':True,'run_id':'Run-143','sha256':h(p.read_bytes()),'candidate_sha256':c['bindings']['candidate_proof']['sha256']}
 def go(self,b,inspector=None):return policy._snapshot_certificate(self.root,self.cert(b),inspector or self.inspect,self.snap,'Run-143')
 def test_root_relative_pass(self):
  b=self.file('candidate');self.go({'candidate_proof':b});self.assertIn(str(self.root/'candidate'),self.snap)
 def test_pipeline_relative_pass(self):
  b=self.file('RESEARCH_PIPELINE_v2/candidate');b['path']='candidate';self.go({'candidate_proof':b});self.assertIn(str(self.root/'RESEARCH_PIPELINE_v2/candidate'),self.snap)
 def test_mixed_base_pass(self):
  a=self.file('candidate');b=self.file('RESEARCH_PIPELINE_v2/proof');b['path']='proof';self.go({'candidate_proof':a,'sealed':{'paper':b}});self.assertEqual(len(self.snap),3)
 def test_absolute_current_pass(self):
  b=self.file('candidate');b['path']=str(self.root/'candidate');self.go({'candidate_proof':b})
 def test_same_target_alias_not_ambiguous(self):
  b=self.file('candidate');(self.root/'RESEARCH_PIPELINE_v2/candidate').symlink_to(self.root/'candidate');self.go({'candidate_proof':b})
 def test_ambiguous_equal_hash_fails(self):
  b=self.file('candidate');self.file('RESEARCH_PIPELINE_v2/candidate')
  with self.assertRaisesRegex(ValueError,'ambiguous'):self.go({'candidate_proof':b})
 def test_different_hash_other_base_does_not_admit_wrong(self):
  b=self.file('candidate');self.file('RESEARCH_PIPELINE_v2/candidate',b'wrong');self.go({'candidate_proof':b});self.assertNotIn(str(self.root/'RESEARCH_PIPELINE_v2/candidate'),self.snap)
 def test_hash_mismatch_fails(self):
  b=self.file('candidate');b['sha256']=h(b'other')
  with self.assertRaisesRegex(ValueError,'hash-mismatched'):self.go({'candidate_proof':b})
 def test_missing_fails(self):
  with self.assertRaisesRegex(ValueError,'missing'):self.go({'candidate_proof':{'path':'absent','sha256':h(b'x')}})
 def test_outside_absolute_fails(self):
  with self.assertRaisesRegex(ValueError,'outside'):self.go({'candidate_proof':{'path':'/private/tmp/outside-not-admitted','sha256':h(b'x')}})
 def test_outside_relative_fails(self):
  with self.assertRaisesRegex(ValueError,'outside'):self.go({'candidate_proof':{'path':'../outside-not-admitted','sha256':h(b'x')}})
 def test_outside_symlink_fails(self):
  b=self.file('candidate');(self.root/'candidate').unlink();(self.root/'candidate').symlink_to('/private/tmp/outside-not-admitted')
  with self.assertRaisesRegex(ValueError,'outside'):self.go({'candidate_proof':b})
 def test_finish_race_fails(self):
  b=self.file('candidate');self.go({'candidate_proof':b});(self.root/'candidate').write_bytes(b'changed')
  with self.assertRaisesRegex(policy.PolicyHold,'input changed'):policy._finish(self.snap)
 def test_inspector_hold_fails(self):
  b=self.file('candidate')
  with self.assertRaisesRegex(policy.PolicyHold,'consumer HOLD'):self.go({'candidate_proof':b},lambda p,r:{'valid':False})
 def test_run_identity_fails(self):
  b=self.file('candidate')
  def f(p,r):return {**self.inspect(p,r),'run_id':'Run-144'}
  with self.assertRaisesRegex(policy.PolicyHold,'consumer HOLD'):self.go({'candidate_proof':b},f)
 def test_candidate_identity_fails(self):
  b=self.file('candidate')
  def f(p,r):return {**self.inspect(p,r),'candidate_sha256':h(b'wrong')}
  with self.assertRaisesRegex(policy.PolicyHold,'candidate inspection'):self.go({'candidate_proof':b},f)
 def test_original_functions_exact_except_snapshot(self):
  def functions(p):return {x.name:ast.dump(x,include_attributes=False)for x in ast.parse(p.read_text()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
  baseline=HERE/'BEFORE_phase7_audit_policy.py'
  if not baseline.is_file():
   baseline=G/'policy_versions/66f9c7133a82aec937392086b6102a616370ea17817a14ecc18e7a1d72c99654/phase7_audit_policy.py'
  before=functions(baseline);after=functions(POLICY);self.assertEqual(set(before),set(after));self.assertEqual([k for k in before if before[k]!=after[k]],['_snapshot_certificate'])
if __name__=='__main__':unittest.main(verbosity=2)
