"""Current own-policy/recovery source cases in a clean repo-bound subprocess.

All fixture consumers are source-only tests, never publication admission.
Historical generic310 has a distinct captured-source runner and manifest.
"""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,tempfile,unittest
G=Path(__file__).resolve().parent
F=G/'tests/fixtures/phase7_own_record_recovery_v001'
PRODUCTION=['weekly_digest_executor.py','weekly_digest_boundary.py','weekly_digest_runtime.py','weekly_checkpoint_replay.py','prepare_weekly_digest_plan.py','invoke_weekly_digest.py','weekly_archive_wait.py','weekly_digest_queue.py','prepare_weekly_configuration.py','capture_weekly_inputs.py','weekly_pending_discovery.py','owned_digest_machine.py','owned_journal_writer.py','owned_legacy_preview_aliases.py','owned_prior_legacy.py','owned_weekly_discovery.py','runtime_closure_view.py','owned_creation_recovery.py','own_prior_record.py','own_record_comparison.py','methods_digest_registration.py','methods_digest_registration_legacy_0fc739.py','digest_public_state.py','phase7_policy_versions.py']
class CurrentOwnRecordPortableTests(unittest.TestCase):
    def test_current_source_policy_recovery_and_boundary(self):
        manifest=json.loads((F/'CI_SOURCE_MANIFEST.json').read_bytes())
        self.assertEqual(set(manifest['production']),set(PRODUCTION))
        self.assertEqual(manifest['expected_tests'],151)
        with tempfile.TemporaryDirectory(prefix='phase7-own-record-ci-')as temp:
            out=Path(temp).resolve(strict=True)
            for name in PRODUCTION:
                source=G/'tests/fixtures/phase7_prior_content_historical_v001'/name;self.assertTrue(source.is_file());self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),manifest['production'][name]);shutil.copyfile(source,out/name)
            for row in manifest['fixtures']:
                source=F/row['path'];self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),row['sha256']);target=out/row['path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(out),'-p','test*.py'],cwd=out,capture_output=True,text=True,timeout=90)
            self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr);self.assertIn('Ran 151 tests',result.stderr);self.assertIn('OK',result.stderr)
if __name__=='__main__':unittest.main()
