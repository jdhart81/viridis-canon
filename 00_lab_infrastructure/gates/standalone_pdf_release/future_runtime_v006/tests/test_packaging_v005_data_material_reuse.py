"""Pure same-operation DATA reuse; no operational science or live admission.

All paths, observations, clocks and transport responses are synthetic. Real
candidate byte/path/identity guards remain active; only source validation and
transport are replaced at their explicit fixture seams.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.request

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_catalog as catalog
import packaging_runtime as runtime
import manuscript_access_registry as registry


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class FixtureOwner:
    def __init__(self, output):
        self.owner_evidence_directory = output
        output.mkdir(parents=True)
        self.depth = 0
        self.closed = False
        self.now = 100.0
        self.first_get = None
        self.deadline_calls = 0

    def deadline_guard(self):
        self.deadline_calls += 1
        runtime.need(not self.closed, 'FIXTURE_CLOSED_OWNER_OPERATION')
        runtime.need(self.first_get is None or self.now <= self.first_get + 900,
                     'FIXTURE_OWNER_DEADLINE_EXPIRED')

    def begin_observation_operation(self):
        self.deadline_guard()
        self.depth += 1

    def end_observation_operation(self, *, failed):
        assert self.depth > 0
        self.depth -= 1
        if failed or self.depth == 0:
            self.closed = True


class PureDataMaterialReuseTests(unittest.TestCase):
    def make_root(self, tmp):
        root = Path(tmp).resolve() / 'canonical'
        root.mkdir()
        return root

    def binding(self, path):
        return {'path': str(path), 'sha256': digest(path.read_bytes())}

    def scoped(self, root, context):
        stack = ExitStack()
        stack.enter_context(patch.object(catalog, 'checked_context', return_value=context))
        stack.enter_context(catalog.operation_scope(root, {'synthetic_profile': True}, context))
        return stack

    def owned_fixture(self, root, folder='owner'):
        context = FixtureOwner(root / 'reports/verification-coverage' / folder)
        paths = {}
        for category, filename, raw in (
                ('observations', 'ACTUAL_BODY.json', b'{"fixture":"complete-owner-body","status":"PASS"}'),
                ('transport', '001_GET.json', b'{"method":"GET","fixture":"complete-transport"}'),
                ('bytes', 'paper.pdf', b'%PDF-fixture-exact-manuscript-bytes')):
            path = context.owner_evidence_directory / category / '0001' / filename
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            paths[category] = path
        return context, paths

    def test_json_reuses_only_parse_after_two_fresh_reads_and_returns_isolated_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            path = root / 'material.json'
            raw = b'{"status":"PASS","nested":{"values":[1,2]},"guarded":true}'
            path.write_bytes(raw)
            binding = self.binding(path)
            actual_loads = json.loads
            actual_reads = Path.read_bytes
            parses, reads = [], []

            def loads(value, *args, **kwargs):
                if value == raw:
                    parses.append('parse-exact-data')
                return actual_loads(value, *args, **kwargs)

            def read(p):
                if p == path:
                    reads.append('fresh-full-read')
                return actual_reads(p)

            with patch.object(runtime.json, 'loads', side_effect=loads), \
                    patch.object(Path, 'read_bytes', read), runtime.json_data_scope(root):
                first = runtime.object_at(root, binding)[2]
                first['nested']['values'].append('caller mutation')
                first['status'] = 'CALLER_ONLY'
                second = runtime.object_at(root, binding)[2]
                self.assertEqual(second, actual_loads(raw))
                self.assertEqual(reads, ['fresh-full-read', 'fresh-full-read'])
                self.assertEqual(parses, ['parse-exact-data'])
                with self.assertRaises(runtime.PackagingHold):
                    runtime.parse_json_data(root, path, raw, copy_result=False)
                _, fresh_raw = runtime.read(root, binding)
                internal = runtime.parse_json_data(root, path, fresh_raw, copy_result=False)
                if isinstance(internal, dict):
                    internal['guarded'] = False
                self.assertTrue(runtime.object_at(root, binding)[2]['guarded'])

    def test_json_parser_semantics_and_exception_cleanup_remain_exact(self):
        for raw in (b'{broken', b'{"bad":"\xff"}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as tmp:
                root = self.make_root(tmp)
                path = root / 'material.json'
                path.write_bytes(raw)
                binding = self.binding(path)
                with self.assertRaises((json.JSONDecodeError, UnicodeDecodeError)):
                    with runtime.json_data_scope(root):
                        runtime.object_at(root, binding)
                path.write_bytes(b'{"duplicate":1,"duplicate":2,"values":[null,true,3.5]}')
                with runtime.json_data_scope(root):
                    self.assertEqual(runtime.object_at(root, self.binding(path))[2],
                                     {'duplicate': 2, 'values': [None, True, 3.5]})

    def test_nested_scope_and_new_or_failed_operations_never_reuse_prior_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            path = root / 'material.json'
            raw = b'{"material":[1,2,3]}'
            path.write_bytes(raw)
            binding = self.binding(path)
            actual = json.loads
            calls = []

            def loads(value, *args, **kwargs):
                if value == raw:
                    calls.append('parse')
                return actual(value, *args, **kwargs)

            with patch.object(runtime.json, 'loads', side_effect=loads):
                with runtime.json_data_scope(root):
                    runtime.object_at(root, binding)
                    with runtime.json_data_scope(root):
                        runtime.object_at(root, binding)
                    self.assertEqual(len(calls), 1)
                with self.assertRaisesRegex(RuntimeError, 'synthetic operation failure'):
                    with runtime.json_data_scope(root):
                        runtime.object_at(root, binding)
                        raise RuntimeError('synthetic operation failure')
                with runtime.json_data_scope(root):
                    runtime.object_at(root, binding)
                self.assertEqual(len(calls), 3)
                foreign = Path(tmp).resolve() / 'foreign'
                foreign.mkdir()
                other = foreign / 'material.json'
                other.write_bytes(raw)
                with runtime.json_data_scope(foreign):
                    runtime.object_at(foreign, self.binding(other))
                self.assertEqual(len(calls), 4)

    def test_json_cached_material_cannot_hide_changed_bytes_or_identity_or_source_alias(self):
        for change in ('bytes', 'replace', 'mode', 'leaf-link', 'parent-link'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root = self.make_root(tmp)
                folder = root / 'source-material'
                folder.mkdir()
                path = folder / 'material.json'
                raw = b'{"guarded":true }'
                path.write_bytes(raw)
                binding = self.binding(path)
                context = FixtureOwner(root / 'reports/verification-coverage/owner')
                with self.assertRaises(runtime.PackagingHold):
                    with self.scoped(root, context), runtime.json_data_scope(root):
                        runtime.object_at(root, binding)
                        if change == 'bytes':
                            before = path.stat()
                            path.write_bytes(b'{"guarded":false}')
                            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                        elif change == 'replace':
                            replacement = folder / 'replacement'
                            replacement.write_bytes(raw)
                            os.replace(replacement, path)
                        elif change == 'mode':
                            path.chmod(0o400)
                        elif change == 'leaf-link':
                            other = folder / 'other'
                            other.write_bytes(raw)
                            path.unlink()
                            path.symlink_to(other)
                        else:
                            relocated = root / 'relocated'
                            folder.rename(relocated)
                            folder.symlink_to(relocated, target_is_directory=True)
                        runtime.object_at(root, binding)
                self.assertTrue(context.closed)
                self.assertIsNone(catalog._SCIENCE.get())
                self.assertIsNone(catalog._READ_CAPTURE.get())

    def test_owned_buffer_has_one_fresh_read_but_original_reader_capture_stays_active(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            context, paths = self.owned_fixture(root)
            owned = paths['bytes']
            raw = owned.read_bytes()
            ordinary = root / 'original-proof.lean'
            ordinary.write_bytes(b'unchanged original reader input')
            actual = Path.read_bytes
            counts = {'owned': 0, 'original': 0}

            def read(p):
                if p == owned:
                    counts['owned'] += 1
                elif p == ordinary:
                    counts['original'] += 1
                return actual(p)

            with self.assertRaises(runtime.PackagingHold), \
                    self.scoped(root, context), patch.object(Path, 'read_bytes', read):
                data = catalog.scientific_data(root)
                self.assertEqual(data.read_owned(owned, expected_sha256=digest(raw)), raw)
                self.assertEqual(data.read_owned(owned, expected_sha256=digest(raw)), raw)
                self.assertEqual(counts['owned'], 2)
                self.assertEqual(data.inputs[str(owned)]['sha256'], digest(raw))
                ordinary.read_bytes()
                self.assertEqual(counts['original'], 2)
                self.assertIn(str(ordinary), data.inputs)
                self.assertIsNone(context.first_get)
                ordinary.write_bytes(b'changed original proof input')
                data.assert_current()
            self.assertTrue(context.closed)

    def test_owned_buffer_is_confined_to_exact_evidence_leaves_and_all_three_categories(self):
        for invalid in ('outside', 'other-category', 'leaf-link', 'parent-link', 'directory', 'missing'):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as tmp:
                root = self.make_root(tmp)
                context, paths = self.owned_fixture(root)
                unscoped = catalog.ScientificInputData(root, context)
                with self.assertRaises(runtime.PackagingHold):
                    unscoped.read_owned(paths['bytes'])
                self.assertEqual(unscoped.inputs, {})
                with self.assertRaises((runtime.PackagingHold, FileNotFoundError)):
                    with self.scoped(root, context):
                        data = catalog.scientific_data(root)
                        for path in paths.values():
                            self.assertEqual(data.read_owned(path), path.read_bytes())
                        if invalid == 'outside':
                            target = root / 'source.py'
                            target.write_bytes(b'outside owned DATA category')
                        elif invalid == 'other-category':
                            target = context.owner_evidence_directory / 'other/material.json'
                            target.parent.mkdir()
                            target.write_bytes(b'{}')
                        elif invalid == 'leaf-link':
                            target = paths['bytes'].parent / 'linked.pdf'
                            target.symlink_to(paths['bytes'])
                        elif invalid == 'parent-link':
                            link = context.owner_evidence_directory / 'bytes/linked'
                            link.symlink_to(paths['bytes'].parent, target_is_directory=True)
                            target = link / paths['bytes'].name
                        elif invalid == 'directory':
                            target = paths['bytes'].parent
                        else:
                            target = paths['bytes'].parent / 'missing.pdf'
                        data.read_owned(target)
                self.assertTrue(context.closed)
                self.assertIsNone(catalog._SCIENCE.get())
                self.assertIsNone(catalog._READ_CAPTURE.get())

    def test_owned_buffer_rechecks_all_six_identity_fields_and_postread_races(self):
        for change in ('bytes', 'inode', 'mode', 'mtime', 'leaf-link', 'postread-bytes', 'postread-parent-link', 'postread-expired'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                root = self.make_root(tmp)
                context, paths = self.owned_fixture(root)
                path = paths['bytes']
                raw = path.read_bytes()
                with self.assertRaises(runtime.PackagingHold):
                    with self.scoped(root, context):
                        data = catalog.scientific_data(root)
                        data.read_owned(path, expected_sha256=digest(raw))
                        if change == 'bytes':
                            before = path.stat()
                            path.write_bytes(b'X' * len(raw))
                            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                        elif change == 'inode':
                            replacement = path.parent / 'replacement'
                            replacement.write_bytes(raw)
                            os.replace(replacement, path)
                        elif change == 'mode':
                            path.chmod(0o400)
                        elif change == 'mtime':
                            before = path.stat()
                            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000))
                        elif change == 'leaf-link':
                            other = path.parent / 'other.pdf'
                            other.write_bytes(raw)
                            path.unlink()
                            path.symlink_to(other)
                        if change == 'postread-expired':
                            path = paths['bytes'].parent / 'fresh-expired.pdf'
                            path.write_bytes(raw)
                            context.first_get = 100.0
                            context.now = 100.0
                            self.assertNotIn(str(path), data.inputs)
                        if change.startswith('postread'):
                            actual = Path.read_bytes
                            fired = []

                            def race(p):
                                value = actual(p)
                                if p == path and not fired:
                                    fired.append(True)
                                    if change == 'postread-expired':
                                        context.now = 1001.0
                                    elif change == 'postread-bytes':
                                        path.write_bytes(b'X' * len(raw))
                                    else:
                                        relocated = path.parent.with_name('relocated')
                                        path.parent.rename(relocated)
                                        path.parent.symlink_to(relocated, target_is_directory=True)
                                return value

                            with patch.object(Path, 'read_bytes', race):
                                data.read_owned(path, expected_sha256=digest(raw))
                        else:
                            data.read_owned(path, expected_sha256=digest(raw))
                self.assertTrue(context.closed)
                self.assertIsNone(catalog._SCIENCE.get())
                self.assertIsNone(catalog._READ_CAPTURE.get())
                if change == 'postread-expired':
                    self.assertNotIn(str(path), data.inputs)
                    self.assertEqual(context.first_get, 100.0)
                    self.assertEqual(context.now, 1001.0)
                self.assertTrue((context.owner_evidence_directory / 'SCIENTIFIC_INPUT_DATA_HOLD.json').is_file())
                self.assertFalse((context.owner_evidence_directory / 'SCIENTIFIC_INPUT_DATA_FINAL.json').exists())

    def test_owned_reuse_preserves_complete_input_and_inventory_guards(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            context, paths = self.owned_fixture(root)
            certs = root / 'certificates'
            certs.mkdir()
            run = root / 'science-engine/07_nightly_engine/compound research papers/Run-001'
            run.mkdir(parents=True)
            paper = run / 'paper.pdf'
            paper.write_bytes(b'complete original paper fixture')
            corpus = SimpleNamespace(discover=lambda r: ([], [], []), GENERATION_ROOT=root / 'mirror')
            with self.assertRaisesRegex(runtime.PackagingHold, 'SCIENTIFIC_INPUT_INVENTORY_CHANGED'):
                with self.scoped(root, context):
                    data = catalog.scientific_data(root)
                    data.capture_inventory(corpus, certs)
                    for path in paths.values():
                        data.read_owned(path)
                    paper.read_bytes()
                    self.assertTrue(set(str(p) for p in paths.values()) <= set(data.inputs))
                    (run / 'new-claim.json').write_bytes(b'new unapproved scientific premise')
                    data.assert_current()

    def factory_fixture(self, root, clock, request_effect=None):
        output = root / 'reports/verification-coverage/owner-factory'
        registry_path = root / 'registry.json'
        registry_path.write_text(json.dumps({'standard': registry.STANDARD,
            'status': 'NOMINATED_INPUTS_NOT_AUTHORITY', 'observation_context': registry.CONTEXT, 'entries': []}))
        profile = {'access_registry': self.binding(registry_path)}
        calls = []

        class NoRedirect(urllib.request.BaseHandler):
            pass

        class Transport:
            def __init__(self, host, token, out, opener):
                self.out = out
                self.out.mkdir(parents=True)
                self.sequence = 0

            def request(self, method, url, *, accept):
                calls.append((method, url, accept))
                self.sequence += 1
                body = {'id': 23308138, 'metadata': {'fixture': 'complete-body', 'nested': [1, 2]},
                        'accept': accept}
                (self.out / f'{self.sequence:03d}_GET.json').write_text(json.dumps(
                    {'method': method, 'url': url, 'accept': accept, 'response': body}))
                if request_effect is not None:
                    request_effect()
                return deepcopy(body)

        actual_import = catalog.importlib.import_module

        def imports(name, *args, **kwargs):
            if name == 'zenodo_transport':
                return SimpleNamespace(NoRedirect=NoRedirect, ZenodoTransport=Transport)
            if name == 'first_digest_publisher':
                return SimpleNamespace(PacedOpener=lambda opener: SimpleNamespace(deadline=None))
            if name == 'manuscript_access_registry':
                return registry
            return actual_import(name, *args, **kwargs)

        stack = ExitStack()
        stack.enter_context(patch.object(runtime, 'validate', return_value=profile))
        stack.enter_context(patch.object(catalog.importlib, 'import_module', side_effect=imports))
        stack.enter_context(patch.object(catalog.time, 'monotonic', side_effect=lambda: clock[0]))
        context = catalog.owner_context(root, {'fixture': True}, 'fixture-only-secret', output)
        return stack, context, calls

    def test_actual_factory_replay_checks_body_transport_stamp_expiry_and_closes(self):
        for changed in ('body', 'transport', 'stamp', 'expired', 'postresponse-expired'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                root = self.make_root(tmp)
                clock = [1000.0]
                effect = (lambda: clock.__setitem__(0, 1901.0)) if changed == 'postresponse-expired' else None
                fixture, context, calls = self.factory_fixture(root, clock, effect)
                with fixture, self.assertRaises(runtime.PackagingHold):
                    with self.scoped(root, context):
                        self.assertIsNone(context.observation_timing()['observation_elapsed_seconds'])
                        first = context.owner_getter('23308138', 'application/json')
                        self.assertEqual(first['metadata']['nested'], [1, 2])
                        first['metadata']['nested'].append('caller only')
                        self.assertEqual(context.owner_getter('23308138', 'application/json')['metadata']['nested'], [1, 2])
                        self.assertEqual(len(calls), 1)
                        if changed == 'expired':
                            clock[0] = 1901.0
                        else:
                            output = context.owner_evidence_directory
                            target = {'body': output / 'observations/0001/ACTUAL_BODY.json',
                                      'transport': output / 'transport/001_GET.json',
                                      'stamp': output / 'observations/0001/OBSERVATION.json'}[changed]
                            target.write_text('{"tampered":true}')
                        context.owner_getter('23308138', 'application/json')
                self.assertEqual(len(calls), 1)
                self.assertIsNone(catalog._SCIENCE.get())
                self.assertIsNone(catalog._READ_CAPTURE.get())
                with self.assertRaises(runtime.PackagingHold):
                    context.owner_getter('23308138', 'application/json')
                self.assertEqual(len(calls), 1)

    def test_authorized_cas_invalidates_pure_material_without_caching_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_root(tmp)
            context, paths = self.owned_fixture(root)
            canonical = root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
            canonical.parent.mkdir()
            before_raw = b'{"qualified":true}'
            after_raw = b'{"qualified":false}'
            canonical.write_bytes(before_raw)
            before = {'path': str(canonical), 'sha256': digest(before_raw)}
            after = {'path': str(canonical), 'sha256': digest(after_raw)}
            predicates = []
            with self.scoped(root, context), runtime.json_data_scope(root):
                data = catalog.scientific_data(root)
                first = runtime.object_at(root, before)[2]
                predicates.append(first['qualified'])
                data.authorize_cas(canonical, before['sha256'], after['sha256'])
                canonical.write_bytes(after_raw)
                data.finish_cas()
                second = runtime.object_at(root, after)[2]
                predicates.append(second['qualified'])
                self.assertEqual(predicates, [True, False])
                self.assertEqual(len(data.cas_events), 1)
                self.assertIsNone(data.pending_cas)
                with self.assertRaises(runtime.PackagingHold):
                    runtime.object_at(root, before)
                self.assertFalse(runtime.object_at(root, after)[2]['qualified'])
                self.assertEqual(len(data.cas_events), 1)


if __name__ == '__main__':
    unittest.main()
