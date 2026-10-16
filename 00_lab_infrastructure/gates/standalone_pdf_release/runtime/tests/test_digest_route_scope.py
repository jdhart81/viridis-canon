"""Digest source scope is fixed; excluded publisher bytes cannot enter it."""
import ast
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime


class DigestRouteScopeTests(unittest.TestCase):
    def rows(self, root, names, prefix):
        result = []
        for name in sorted(names):
            file = root / name
            file.write_bytes(b'# isolated source fixture\n')
            result.append({'name': name, 'path': str(file),
                'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                'git_path': prefix + name})
        return result

    def test_exact_digest_set_excludes_only_successor_and_has_one_default_route(self):
        self.assertEqual(len(runtime.MODULE_NAMES), 18)
        self.assertEqual(runtime.MODULE_NAMES,
                         runtime.FROZEN_FULL_MODULE_NAMES - {'publish_successor_wave_guarded.py'})
        self.assertEqual(runtime.DEFAULT_ROUTES, {'digest': 'invoke_digest_v2.py'})
        self.assertEqual(runtime.STANDARD, 'VRS-DIGEST-ONLY-PDF-PACKAGING-PROFILE-1')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            rows = self.rows(root, runtime.MODULE_NAMES, runtime.GIT_PREFIX)
            self.assertEqual(len(runtime.module_table(root, rows)), 18)
            successor = self.rows(root, {'publish_successor_wave_guarded.py'}, runtime.GIT_PREFIX)[0]
            for bad in [rows[:-1], rows + [successor], rows[:-1] + [successor], rows + [rows[0]]]:
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                    runtime.module_table(root, bad)

    def test_historical_module_sets_stay_complete_seventeen_or_nineteen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            for version in range(1, 12):
                prefix = ('00_lab_infrastructure/gates/standalone_pdf_release/'
                          f'future_runtime_v{version:03d}/')
                names = runtime.FROZEN_MODULE_NAMES if version < 7 else runtime.FROZEN_FULL_MODULE_NAMES
                rows = self.rows(root, names, prefix)
                self.assertEqual(len(runtime.module_table(root, rows, git_prefix=prefix)),
                                 17 if version < 7 else 19)
                with self.assertRaisesRegex(runtime.PackagingHold, 'CLOSED_ADDITIVE_MODULES'):
                    runtime.module_table(root, [r for r in rows
                        if r['name'] != 'publish_successor_wave_guarded.py'], git_prefix=prefix)

    def test_current_scope_refuses_successor_source_cache_package_and_link(self):
        for suffix in ['.py', '.pyc', '']:
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                file = root / ('publish_successor_wave_guarded' + suffix)
                if suffix:
                    file.write_bytes(b'# excluded source\n')
                else:
                    file.mkdir()
                with self.assertRaisesRegex(runtime.PackagingHold, 'CURRENT_IMPORT_ARTIFACT'):
                    runtime.current_import_artifact_guard(root)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            (root / 'publish_successor_wave_guarded.py').symlink_to(root / 'absent')
            with self.assertRaisesRegex(runtime.PackagingHold, 'CURRENT_IMPORT_ARTIFACT'):
                runtime.current_import_artifact_guard(root)

    def test_current_workers_bootstrap_the_same_closed_set_at_unversioned_path(self):
        # Compile definitions without __main__; no process or scientific call.
        for name, field in [('scientific_registration_worker.py', 'BOOTSTRAP_MODULE_NAMES'),
                            ('owner_content_worker.py', 'MODULE_NAMES')]:
            path = HERE / name
            tree = ast.parse(path.read_bytes())
            constants = {}
            for node in tree.body:
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == field for t in node.targets):
                    self.assertIsInstance(node.value, ast.Call)
                    self.assertEqual(node.value.func.id, 'frozenset')
                    constants[field] = frozenset(ast.literal_eval(node.value.args[0]))
            self.assertEqual(constants[field], runtime.MODULE_NAMES)
            source = path.read_text()
            self.assertNotIn('standalone_pdf_runtime_v012', source)
            self.assertIn('_ZENODO_DEPOSITS/standalone_pdf_runtime', source)

    def test_both_worker_bootstraps_refuse_excluded_successor_before_source_import(self):
        import owner_content_worker as owner
        import scientific_registration_worker as science
        for check in [owner.reject_import_artifacts, science._bootstrap_artifacts]:
            for suffix in ['.py', '.pyc', '']:
                with self.subTest(worker=check.__module__, suffix=suffix), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp).resolve()
                    check(root)
                    path = root / ('publish_successor_wave_guarded' + suffix)
                    if suffix:
                        path.write_bytes(b'# excluded\n')
                    else:
                        path.mkdir()
                    with self.assertRaisesRegex(ValueError, 'IMPORT_ARTIFACT'):
                        check(root)

    def test_outer_guard_needs_no_successor_and_refuses_one_if_present(self):
        import test_outer_digest_guard as outer_tests
        helper = outer_tests.OuterDigestGuardTests(methodName='runTest')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, config, digest, log = helper.fixture(root)
            with stack:
                checked = outer_tests.guard.context(config, digest)
                self.assertNotIn('publish_successor_wave_guarded.py', checked['sources'])
                (outer_tests.guard.INSTALLED / 'publish_successor_wave_guarded.py').write_bytes(b'# excluded\n')
                with self.assertRaisesRegex(outer_tests.guard.GuardHold, 'alternate current-code import artifact'):
                    outer_tests.guard.context(config, digest)
                self.assertFalse(log.exists())


if __name__ == '__main__':
    unittest.main()
