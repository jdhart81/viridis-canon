"""Test-only routing for immutable schema-1 executors; never a runtime fallback."""
import hashlib, os, subprocess, sys, unittest
from unittest import mock
from pathlib import Path
HISTORICAL_SHA='66cc830f4814ee943c616d754d61cff9be5a65607e0a26ec4f91acd23ce630d7'

def historical_protocol(gates, source, *, timeout=600):
 gates=Path(gates).resolve(strict=True);source=Path(source).resolve(strict=True)
 if not source.is_relative_to(gates/'production_snapshots'):raise ValueError('closed historical test source required')
 baseline=gates/'testdata/digest_public_state/methods_digest_registration_v1.txt'
 if hashlib.sha256(baseline.read_bytes()).hexdigest()!=HISTORICAL_SHA:raise ValueError('historical test registrar bytes changed')
 # This fresh test subprocess alone preloads the exact schema-1 dependency. All
 # original snapshot assertions/source bytes and current-schema tests stay intact.
 code="""import hashlib,sys,types,unittest
from pathlib import Path
gates,source,baseline,expected=map(str,sys.argv[1:])
sys.path.insert(0,gates)
raw=Path(baseline).read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('historical registrar bytes changed')
m=types.ModuleType('methods_digest_registration');m.__file__=baseline
sys.modules[m.__name__]=m;exec(compile(raw,baseline,'exec'),m.__dict__)
if m.STANDARD!='VRS-METHODS-DIGEST-REGISTRATION-1':raise ValueError('historical schema changed')
suite=unittest.defaultTestLoader.discover(source,pattern='test*.py')
result=unittest.TextTestRunner(verbosity=1).run(suite)
raise SystemExit(0 if result.wasSuccessful()else 1)
"""
 env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gates);env['PYTHONDONTWRITEBYTECODE']='1'
 return subprocess.run([sys.executable,'-B','-c',code,str(gates),str(source),str(baseline),HISTORICAL_SHA],cwd=source,env=env,capture_output=True,text=True,timeout=timeout)

class HistoricalAdapterTests(unittest.TestCase):
 def test_current_consumer_still_requires_schema2_context(self):
  import methods_digest_registration as current
  self.assertEqual(current.STANDARD,'VRS-METHODS-DIGEST-REGISTRATION-2')
  self.assertIn('public_state_context',current.EVIDENCE_FIELDS)
  self.assertEqual(hashlib.sha256((Path(__file__).parent/'testdata/digest_public_state/methods_digest_registration_v1.txt').read_bytes()).hexdigest(),HISTORICAL_SHA)
 def test_changed_historical_hash_fails_before_subprocess(self):
  gate=Path(__file__).parent;source=gate/'production_snapshots/phase7-20261007-first-digest/after/production_execution_dependencies'
  with mock.patch.object(hashlib,'sha256',return_value=type('Changed',(),{'hexdigest':lambda self:'0'*64})()),mock.patch.object(subprocess,'run')as run:
   self.assertRaises(ValueError,historical_protocol,gate,source);run.assert_not_called()
 def test_foreign_source_cannot_select_historical_route(self):
  self.assertRaises(ValueError,historical_protocol,Path(__file__).parent,Path(__file__).parent)

if __name__=='__main__':unittest.main()
