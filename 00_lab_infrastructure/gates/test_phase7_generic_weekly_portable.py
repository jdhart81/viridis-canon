"""Run generic weekly source-only cases in a clean, repo-bound subprocess.

Fixture default/transport consumers never represent publication admission.
No endpoint, credential, generation or protected verifier is invoked.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
G=Path(__file__).resolve().parent
F=G/'tests/fixtures/phase7_generic_weekly_executor_v002'
PRODUCTION=['weekly_digest_executor.py', 'weekly_digest_boundary.py', 'weekly_digest_runtime.py', 'weekly_checkpoint_replay.py', 'prepare_weekly_digest_plan.py', 'invoke_weekly_digest.py', 'weekly_archive_wait.py', 'weekly_digest_queue.py', 'prepare_weekly_configuration.py', 'capture_weekly_inputs.py', 'weekly_pending_discovery.py', 'owned_digest_machine.py', 'owned_journal_writer.py', 'owned_legacy_preview_aliases.py', 'owned_prior_legacy.py', 'owned_weekly_discovery.py', 'runtime_closure_view.py']
class GenericWeeklyPortableTests(unittest.TestCase):
 def test_frozen_generic_weekly_bundle(self):
  manifest=json.loads((F/'CI_SOURCE_MANIFEST.json').read_bytes())
  with tempfile.TemporaryDirectory(prefix='phase7-generic-ci-')as temp:
   out=Path(temp).resolve(strict=True)
   for name in PRODUCTION:
    source=G/name;self.assertTrue(source.is_file());self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),manifest['production'][name]);shutil.copyfile(source,out/name)
   for row in manifest['fixtures']:
    source=F/row['path'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);target=out/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
   result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(out),'-p','test*.py'],cwd=out,capture_output=True,text=True,timeout=90)
   self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 310 tests',result.stderr);self.assertIn('OK',result.stderr)
if __name__=='__main__':unittest.main()
