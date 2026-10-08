"""Portable exact-source/fixture regression for the generic runtime caller."""
from pathlib import Path
import hashlib,json,subprocess,sys,unittest
GIT_SUBDIR='production_snapshots/phase7-20261008-generic-weekly-runtime/after/production_execution_dependencies'
PORTABLE_FREEZE_SHA='76103f00b7045989f3797614b3493a7d877320cff618168392ee16fc42aebdc3'
class GenericWeeklyRuntimeSnapshotTests(unittest.TestCase):
 def test_exact_source_and_captured_predecessor_all75_regressions(self):
  gates=Path(__file__).resolve().parent;source=gates/GIT_SUBDIR;freeze=source/'PORTABLE_CI_FREEZE.json';self.assertEqual(hashlib.sha256(freeze.read_bytes()).hexdigest(),PORTABLE_FREEZE_SHA)
  rows=json.loads(freeze.read_bytes())['files'];self.assertEqual(len(rows),99);self.assertEqual(len({r['filename']for r in rows}),99)
  for r in rows:
   p=source/r['filename'];self.assertFalse(p.is_symlink());self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['sha256'])
  result=subprocess.run([sys.executable,'-B',str(source/'portable_runner.py'),str(source),str(gates)],capture_output=True,text=True,timeout=60)
  self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 75 tests',result.stderr);self.assertIn('\nOK\n',result.stderr)
if __name__=='__main__':unittest.main()
