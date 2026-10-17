"""Ordinary child dispatch over temporary fixtures; no scientific publication."""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import guard_methods_digest_release as guard


class OuterDigestGuardTests(unittest.TestCase):
    def fixture(self, root, *, preflight_exit=0, change_after_read=False):
        installed = root / 'installed'; installed.mkdir()
        (root / 'reports').mkdir()
        log = root / 'reports/calls.jsonl'
        config = root / 'CONFIG.json'
        hashes = {}; modules = []
        names = ['invoke_digest_v2.py'] + ['source_%02d.py' % n for n in range(17)]
        for name in names:
            raw = b'# synthetic reviewed source\n'
            if name == 'invoke_digest_v2.py':
                raw = ("import json,sys\nfrom pathlib import Path\n"
                       "go='--go' in sys.argv\n"
                       "with Path(%r).open('a') as f:f.write(json.dumps({'go':go})+'\\n')\n"
                       "%s\nraise SystemExit(0 if go else %d)\n" %
                       (str(log), "Path(%r).write_bytes(b'changed')" % str(installed / 'source_00.py')
                        if change_after_read else '# no source changes', preflight_exit)).encode()
            path = installed / name; path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest(); hashes[name] = digest
            modules.append({'name': name, 'path': str(path), 'sha256': digest})
        shared_path = installed / 'common' / guard.SHARED_INPUT_NAME
        shared_path.parent.mkdir()
        shared_path.write_bytes((Path(__file__).resolve().parents[2] / 'common' / guard.SHARED_INPUT_NAME).read_bytes())
        shared = [{'name':guard.SHARED_INPUT_NAME,'path':str(shared_path),
                   'sha256':guard.SHARED_INPUT_SHA256,'git_path':guard.SHARED_INPUT_GIT_PATH}]
        profile = installed / 'CURRENT_PACKAGING_PROFILE.json'
        profile.write_text(json.dumps({'standard': 'VRS-DIGEST-ONLY-PDF-PACKAGING-PROFILE-1',
                         'status': 'INSTALLED_EXACT_ADDITIVE_SOURCE_READBACK_PASS',
                         'canonical_root': str(root), 'modules': modules, 'shared_dependencies':shared}))
        binding = {'path': str(profile), 'sha256': hashlib.sha256(profile.read_bytes()).hexdigest()}
        nomination = installed / 'INSTALLATION_NOMINATION.json'
        nomination.write_text(json.dumps({'standard': 'VRS-ROOT-REVIEWED-PDF-RUNTIME-INSTALLATION-NOMINATION-12',
                              'status': 'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
                              'profile': binding}))
        config.write_text(json.dumps({'canonical_root': str(root), 'packaging_profile': binding}))
        stack = ExitStack()
        for name, value in [('ROOT', root), ('INSTALLED', installed), ('PROFILE', profile),
                            ('NOMINATION', nomination), ('SOURCE_HASHES', hashes)]:
            stack.enter_context(patch.object(guard, name, value))
        return stack, config, hashlib.sha256(config.read_bytes()).hexdigest(), log

    def args(self, config, sha, root, *, go=False):
        return ['--config', str(config), '--expected-config-sha256', sha] + (
            ['--go', '--output', str(root / 'reports/result')] if go else [])

    def test_public_preflight_uses_one_real_child_and_go_uses_two_new_real_children(self):
        for go in (False, True):
            with self.subTest(go=go), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                stack, config, sha, log = self.fixture(root)
                with stack:
                    self.assertEqual(guard.main(self.args(config, sha, root, go=go)), 0)
                self.assertEqual([json.loads(x) for x in log.read_text().splitlines()],
                                 [{'go': False}, {'go': True}] if go else [{'go': False}])

    def test_real_failed_preflight_code_is_preserved_and_dispatch_never_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); stack, config, sha, log = self.fixture(root, preflight_exit=7)
            with stack:
                self.assertEqual(guard.main(self.args(config, sha, root, go=True)), 7)
            self.assertEqual(log.read_text().splitlines(), ['{"go": false}'])

    def test_source_change_during_real_child_holds_before_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); stack, config, sha, log = self.fixture(root, change_after_read=True)
            with stack:
                self.assertEqual(guard.main(self.args(config, sha, root, go=True)), 1)
            self.assertEqual(log.read_text().splitlines(), ['{"go": false}'])

    def test_wrong_hash_profile_source_missing_or_alias_never_starts_child(self):
        for changed in ('config', 'profile', 'source', 'missing', 'alias', 'pending'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); stack, config, sha, log = self.fixture(root)
                with stack:
                    target = guard.INSTALLED / 'source_00.py'
                    if changed == 'config': config.write_bytes(b'{}')
                    elif changed == 'profile': guard.PROFILE.write_bytes(b'{}')
                    elif changed == 'source': target.write_bytes(b'changed')
                    elif changed == 'missing': target.unlink()
                    elif changed == 'alias':
                        replacement = root / 'same_bytes.py'; replacement.write_bytes(target.read_bytes())
                        target.unlink(); target.symlink_to(replacement)
                    else: guard.SOURCE_HASHES = 'PENDING'
                    self.assertEqual(guard.main(self.args(config, sha, root, go=True)), 1)
                self.assertFalse(log.exists())

    def test_unapproved_output_or_legacy_profile_never_starts_child(self):
        for changed in ('output', 'legacy'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve(); stack, config, sha, log = self.fixture(root)
                with stack:
                    args = self.args(config, sha, root, go=True)
                    if changed == 'output': args[-1] = str(root / 'outside-reports')
                    else:
                        value = json.loads(config.read_bytes()); value['packaging_profile']['path'] = str(root / 'legacy.json')
                        config.write_text(json.dumps(value)); args[3] = hashlib.sha256(config.read_bytes()).hexdigest()
                    self.assertEqual(guard.main(args), 1)
                self.assertFalse(log.exists())

    def test_context_ignores_ctime_only_and_rejects_restored_mtime_content_change(self):
        import os
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp).resolve(); stack,config,sha,_=self.fixture(root)
            with stack:
                before=guard.context(config,sha)
                target=guard.INSTALLED/'source_00.py'; old=target.stat()
                target.chmod(old.st_mode)
                self.assertEqual(guard.context(config,sha),before)
                target.write_bytes(b'# changed reviewed source\n')
                os.utime(target,ns=(old.st_atime_ns,old.st_mtime_ns))
                with self.assertRaises(guard.GuardHold):guard.context(config,sha)

    def test_shared_dependency_tamper_or_missing_binding_never_starts_child(self):
        for change in ('bytes','missing'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp).resolve(); stack,config,sha,log=self.fixture(root)
                with stack:
                    target=guard.INSTALLED/'common'/guard.SHARED_INPUT_NAME
                    if change=='bytes':target.write_bytes(b'# changed shared source')
                    else:target.unlink()
                    self.assertEqual(guard.main(self.args(config,sha,root,go=True)),1)
                self.assertFalse(log.exists())

    def test_child_is_fixed_ordinary_cli_and_never_caller_controller_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); stack, config, sha, _ = self.fixture(root)
            with stack:
                checked = guard.context(config, sha)
                command = guard.child_command(checked, sha)
                self.assertEqual(command[:3], [sys.executable, '-B', str(guard.INSTALLED / 'invoke_digest_v2.py')])
                self.assertIn('--expected-profile-sha256', command)
                self.assertNotIn('--go', command)
                self.assertNotIn('token', ' '.join(command))


if __name__ == '__main__':
    unittest.main()
