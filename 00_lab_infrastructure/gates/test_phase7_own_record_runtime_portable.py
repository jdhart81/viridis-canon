"""Isolated portable own-record runtime source/preservation cases only."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest
G=Path(__file__).resolve().parent
D=G/'production_snapshots/phase7-20261008-own-record-runtime-successor/after/production_execution_dependencies'
PIN='b8a6b270581cc551243116758bb8e83f33a61daa4a2897255c780fd7ce081c56'
class SourceTests(unittest.TestCase):
 def test_88_isolated_portable_runtime_cases(self):
  p=D/'PORTABLE_CI_FREEZE.json';self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),PIN)
  for row in json.loads(p.read_bytes())['files']:
   q=D/row['filename'];self.assertTrue(q.is_file());self.assertFalse(q.is_symlink());self.assertEqual(q.stat().st_size,row['bytes']);self.assertEqual(hashlib.sha256(q.read_bytes()).hexdigest(),row['sha256'])
  result=subprocess.run([sys.executable,'-B',str(D/'portable_runner.py'),str(D),str(G)],text=True,capture_output=True,timeout=90)
  self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 88 tests',result.stderr)
if __name__=='__main__':unittest.main()
