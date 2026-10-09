"""Exact portable source capsule; no production runtime admission."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest
G=Path(__file__).resolve().parent
D=G/'production_snapshots/phase7-20261009-prior-content-runtime-successor/after/production_execution_dependencies/portable'
PIN='4727944947d9f88282b54bf884c4406e0f32bf221b18142f932719d0cf115b98'
class SourceTests(unittest.TestCase):
 def test_77_isolated_prior_content_runtime_cases(self):
  p=D/'PORTABLE_CI_FREEZE.json';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),PIN)
  for row in json.loads(p.read_bytes())['files']:
   q=D/row['filename'];self.assertTrue(q.is_file());self.assertFalse(q.is_symlink());self.assertEqual(q.stat().st_size,row['bytes']);self.assertEqual(hashlib.sha256(q.read_bytes()).hexdigest(),row['sha256'])
  result=subprocess.run([sys.executable,'-B',str(D/'portable_runner.py'),str(D)],text=True,capture_output=True,timeout=90)
  self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 77 tests',result.stderr)
if __name__=='__main__':unittest.main()
