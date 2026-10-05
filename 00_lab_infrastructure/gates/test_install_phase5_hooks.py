"""Installer simulations touch only temporary fixtures, never the live tree."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from install_phase5_hooks import apply, inspect, sha, TARGETS


class Phase5InstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name).resolve()
        self.root = base/'runtime'; self.root.mkdir()
        self.snapshots = base/'snapshots'
        shutil.copytree(Path(__file__).parent/'production_snapshots/phase5-20261004', self.snapshots)
        mp = self.snapshots/'AFTER_MANIFEST.json'; manifest = json.loads(mp.read_text())
        existing = {row['relative_path'] for row in manifest['snapshots']}
        for relative in sorted(TARGETS-existing):
            source = Path(__file__).parent/'premise_declaration.py' if relative.endswith('/premise_declaration.py') else Path(__file__).resolve().parents[2]/'comparator-deploy/issue_lean_zero_sorry_certificate.py'
            after = self.snapshots/'after'/relative;after.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,after)
            before = None
            if relative.endswith('/issue_lean_zero_sorry_certificate.py'):
                before=self.snapshots/'before'/relative;before.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(Path(__file__).parent/'fixtures/comparator_issuer_unchanged.py',before)
            manifest['snapshots'].append({'relative_path':relative,'production_path':str(self.root/relative),'after_path':str(after.relative_to(self.snapshots)),'after_sha256':sha(after),'before_path':str(before.relative_to(self.snapshots)) if before else None,'before_sha256':sha(before) if before else None,'before_exists':before is not None})
        for row in manifest['snapshots']:
            target = self.root/row['relative_path']; row['production_path'] = str(target)
            if row['before_path'] is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.snapshots/row['before_path'], target)
        mp.write_text(json.dumps(manifest))
        self.manifest_sha = sha(mp)
        self.receipt = self.root/'reports/verification-coverage/install-fixture'

    def execute(self, expected=None):
        return apply(self.root, self.snapshots, expected_manifest_sha256=expected or self.manifest_sha,
                     release_commit='1'*40, receipt_dir=self.receipt)

    def test_plan_reads_all22_targets_and_writes_nothing(self):
        before = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        result = inspect(self.root, self.snapshots)
        self.assertEqual(result['status'], 'READY'); self.assertEqual(len(result['targets']), 22)
        after = {str(p): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before, after); self.assertFalse(self.receipt.exists())

    def test_one_byte_concurrent_live_change_holds_before_any_install(self):
        target = self.root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/claim_binding.py'
        target.write_bytes(target.read_bytes()+b' ')
        result = self.execute()
        self.assertEqual(result['status'], 'HOLD'); self.assertFalse(self.receipt.exists())
        self.assertFalse((self.root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py').exists())

    def test_exact_apply_reads_back_all22_and_skips_unchanged_dependencies(self):
        result = self.execute()
        self.assertEqual(result['status'], 'INSTALLED_HASH_READBACK_PASS')
        self.assertEqual(len(result['installed']), 22)
        self.assertEqual(sum(row['written'] for row in result['installed']),sum(row['before_sha256']!=row['after_sha256'] for row in inspect(self.root,self.snapshots)['targets']))
        self.assertTrue(result['protected_issuer_intake_changes']);self.assertFalse(result['protected_verifier_changes']); self.assertFalse(result['scheduler_modified'])
        self.assertTrue((self.receipt/'START.json').is_file()); self.assertTrue((self.receipt/'FINISH.json').is_file())
        self.assertTrue(all(row['already_after'] for row in inspect(self.root, self.snapshots)['targets']))

    def test_wrong_reviewed_manifest_hash_rejects_without_writes(self):
        with self.assertRaisesRegex(ValueError, 'reviewed manifest SHA mismatch'):
            self.execute(expected='0'*64)
        self.assertFalse(self.receipt.exists())

    def test_changed_prepared_file_rejects_without_installation(self):
        p = self.snapshots/'after/RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py'
        p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError, 'prepared after hash mismatch'):
            self.execute()
        self.assertFalse(self.receipt.exists())

    def test_missing_dependency_target_set_rejected(self):
        p = self.snapshots/'AFTER_MANIFEST.json'; obj = json.loads(p.read_text()); obj['snapshots'].pop()
        p.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, 'complete exact consumer'):
            inspect(self.root, self.snapshots)

    def test_new_target_symlink_never_overwritten(self):
        p = self.root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py'
        p.symlink_to(self.root/'not-yet-present')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.execute()
        self.assertTrue(p.is_symlink()); self.assertFalse(self.receipt.exists())

    def test_rehashed_unapproved_issuer_bytes_refused(self):
        relative='RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py'
        after=self.snapshots/'after'/relative;after.write_bytes(after.read_bytes()+b' ')
        p=self.snapshots/'AFTER_MANIFEST.json';obj=json.loads(p.read_text())
        row=next(row for row in obj['snapshots'] if row['relative_path']==relative);row['after_sha256']=sha(after)
        p.write_text(json.dumps(obj));self.manifest_sha=sha(p)
        with self.assertRaisesRegex(ValueError,'protected issuer intake old/new hash mismatch'):self.execute()
        self.assertFalse(self.receipt.exists())

    def test_receipt_outside_reports_refused(self):
        with self.assertRaisesRegex(ValueError, 'immutable installation receipt'):
            apply(self.root, self.snapshots, expected_manifest_sha256=self.manifest_sha,
                  release_commit='1'*40, receipt_dir=self.root/'wrong receipt')


if __name__ == '__main__': unittest.main()
