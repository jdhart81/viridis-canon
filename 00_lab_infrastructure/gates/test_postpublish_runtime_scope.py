"""Synthetic source-scope regressions; no live consumer or admission evidence."""
from copy import deepcopy
import contextlib
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location('scope_fixture_postpublish', HERE / 'postpublish_digest.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class Scope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.pins = []
        self.modules = {}
        self.previous = {}
        self.events = []
        self.depth = 0
        for i in range(129):
            path = self.root / ('fixture_%03d.py' % i)
            path.write_text('fixture_value = %d\n' % i)
            name = '_postpublish_scope_fixture_%03d' % i
            module = types.ModuleType(name)
            module.__file__ = str(path)
            self.install(name, module)
            self.modules[name] = module
            self.pins.append({'name': path.name, 'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        view_path = self.root / 'runtime_closure_view.py'
        view_path.write_bytes((HERE / 'runtime_closure_view.py').read_bytes())
        self.view_pin = {'name': view_path.name, 'path': str(view_path), 'sha256': p.digest(view_path.read_bytes())}
        self.pins.append(self.view_pin)
        self.runtime = self.pins[:99]
        closure_path = self.root / 'closure.json'
        closure_path.write_bytes(p.encoded({'source_pins': self.runtime}))
        self.closure = p.binding(closure_path)
        self.plan = {'purpose_source_pins': self.pins, 'current_runtime_closure': self.closure}
        self.require_failure = None
        self.full_calls = 0

        def read_bound(binding):
            _, data = p.bound(self.root, binding)
            self.events.append('bound_table')
            return json.loads(data)

        def require(binding):
            self.full_calls += 1
            self.events.append('full_closure')
            self.assertGreater(self.depth, 0)
            for i in range(99, 129):
                self.assertNotIn('_postpublish_scope_fixture_%03d' % i, sys.modules)
            for i in range(99):
                name = '_postpublish_scope_fixture_%03d' % i
                self.assertIs(sys.modules[name], self.modules[name])
            if self.require_failure:
                raise ValueError(self.require_failure)
            return read_bound(binding)

        self.current = types.SimpleNamespace(read_bound_closure=read_bound, require_current_closure=require)

        @contextlib.contextmanager
        def session(root, plan):
            self.assertEqual(root, self.root)
            self.assertIs(plan, self.plan)
            self.events.append('session_enter')
            self.depth += 1
            try:
                yield
            finally:
                self.depth -= 1
                self.events.append('session_exit')

        self.invoke = types.SimpleNamespace(session=session)
        self.addCleanup(self.restore)

    def install(self, name, module):
        if name not in self.previous:
            self.previous[name] = sys.modules.get(name)
        sys.modules[name] = module

    def restore(self):
        for name, previous in self.previous.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous

    def call(self):
        original_load = p.load

        def measured_load(root, binding, name):
            self.assertGreater(self.depth, 0, 'adapter loaded before original source session')
            self.assertEqual(binding, {k: self.view_pin[k] for k in ('path', 'sha256')})
            self.events.append('view_loaded')
            return original_load(root, binding, name)

        with patch.object(p, 'load', side_effect=measured_load):
            return p.require_current_in_source_session(self.root, self.plan, self.current, self.invoke)

    def assert_restored(self):
        for name, module in self.modules.items():
            self.assertIs(sys.modules[name], module)
        self.assertEqual(self.depth, 0)

    def test_130_purpose_sources_99_runtime_sources_use_original_full_closure(self):
        self.assertEqual(self.call()['source_pins'], self.runtime)
        self.assertEqual(self.full_calls, 1)
        self.assertEqual(self.events[:3], ['session_enter', 'view_loaded', 'bound_table'])
        self.assert_restored()

    def test_bad_closure_hash_rejected_before_full_consumer(self):
        self.plan['current_runtime_closure'] = dict(self.closure, sha256='0' * 64)
        with self.assertRaisesRegex(ValueError, 'BOUND_HASH'):
            self.call()
        self.assertEqual(self.full_calls, 0)
        self.assert_restored()

    def test_full_consumer_hold_propagates_and_restores_source_identities(self):
        self.require_failure = 'HOLD_ACTUAL_CLOSURE_FAILURE'
        with self.assertRaisesRegex(ValueError, 'ACTUAL_CLOSURE_FAILURE'):
            self.call()
        self.assertEqual(self.full_calls, 1)
        self.assert_restored()

    def test_changed_purpose_source_is_never_hidden(self):
        Path(self.pins[120]['path']).write_text('changed fixture bytes\n')
        with self.assertRaisesRegex(ValueError, 'CURRENT_PURPOSE_SOURCE'):
            self.call()
        self.assertEqual(self.full_calls, 0)
        self.assert_restored()

    def test_foreign_cached_own_source_is_never_hidden(self):
        path = self.root / 'foreign.py'
        path.write_text('foreign = True\n')
        module = types.ModuleType('_postpublish_scope_foreign')
        module.__file__ = str(path)
        self.install(module.__name__, module)
        with self.assertRaisesRegex(ValueError, 'FOREIGN_CACHED_OWN_SOURCE'):
            self.call()
        self.assertIs(sys.modules[module.__name__], module)
        self.assert_restored()

    def test_runtime_hash_must_be_an_exact_subset_of_purpose_hashes(self):
        path = self.root / 'wrong-subset.json'
        path.write_bytes(p.encoded({'source_pins': [dict(self.runtime[0], sha256='f' * 64)]}))
        self.plan['current_runtime_closure'] = p.binding(path)
        with self.assertRaisesRegex(ValueError, 'MEASURED_RUNTIME_EXACT_SUBSET'):
            self.call()
        self.assertEqual(self.full_calls, 0)
        self.assert_restored()

    def test_missing_or_duplicate_view_pin_fails_closed(self):
        for pins in (self.pins[:-1], self.pins + [self.view_pin]):
            self.plan['purpose_source_pins'] = pins
            with self.assertRaisesRegex(ValueError, 'UNIQUE_RUNTIME_VIEW_SOURCE'):
                self.call()
        self.assertEqual(self.full_calls, 0)
        self.assert_restored()

    def registration_fixture(self, *, fail_after_cas):
        """Exercise actual composition on synthetic files/modules, never live inputs."""
        ssot = self.root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        ssot.parent.mkdir()
        before = {'file_entities': [], 'run_entities': [], 'publication_entities': [{'id': 'fixture-old', 'path': 'old', 'enforcement_acceptable': True}], 'enforcement_activation': {'fixture': 'preserved'}, 'premise_declaration_cutover_run': 'Run-188'}
        ssot.write_bytes(p.encoded(before))
        package = self.root / 'fixture-digest'
        package.mkdir()
        (self.root / 'fixture-note').mkdir()
        receipt = {'path': str(self.root / 'fixture-registration.json'), 'sha256': '1' * 64}
        rows = [
            {'id': 'fixture-group', 'path': 'fixture-digest', 'entity_type': 'METHODS_DIGEST_GROUP', 'certifies': False, 'certificate_valid': False, 'note_ids': ['fixture-note'], 'registration_receipt': receipt, 'enforcement_acceptable': True, 'registration_revalidated': True, 'publication_registration_status': 'PASS'},
            {'id': 'fixture-note', 'path': 'fixture-note', 'entity_type': 'METHODS_DIGEST_NOTE', 'group_id': 'fixture-group', 'certifies': 'LISTED_NOTE_SCOPE_ONLY', 'registration_receipt': receipt, 'enforcement_acceptable': True, 'registration_revalidated': True, 'publication_registration_status': 'PASS'},
        ]
        self.pins[99]['name'] = 'invoke_weekly_digest.py'
        self.plan.update(runtime_consumer={k: self.pins[0][k] for k in ('path', 'sha256')}, source_origin={'fixture': 'synthetic'}, package=str(package), new_run_ids=['Run-127'])
        state = {'phase': 'PUBLISHED', 'published': True, 'record_id': 'fixture-record', 'concept_id': 'fixture-concept', 'last_validation': {'fixture': 'validation'}, 'attempts': [{'transport': {'fixture': 'transport'}, 'validation': {'fixture': 'validation'}}]}
        validation = {'step': 'PUBLISH', 'record_id': state['record_id'], 'transport': state['attempts'][-1]['transport'], 'registration_receipt': receipt}
        plan_path = self.root / 'plan.json'
        plan_path.write_bytes(p.encoded(self.plan))
        plan_binding = p.binding(plan_path)
        result_path = self.root / 'publication-result.json'
        result_path.write_bytes(p.encoded({'status': 'PUBLISHED_STRICT_READBACK_PASS', 'published': True, 'ssot_writes': 0, 'plan': plan_binding, 'checkpoint': {'fixture': 'checkpoint'}, 'record_id': state['record_id'], 'concept_id': state['concept_id']}))
        config = {'plan': plan_binding, 'publication_result': p.binding(result_path), 'expected_ssot_sha256': p.digest(ssot.read_bytes())}
        for key in ('merged_pr', 'merged_commit', 'merged_tree'):
            path = self.root / (key + '.json')
            path.write_bytes(b'{}')
            config[key] = p.binding(path)
        engine = types.ModuleType('weekly_digest_executor')
        engine.require_plan = lambda root, plan: self.assertEqual(plan, self.plan)
        engine.bound = lambda root, binding: (self.root, state if binding == {'fixture': 'checkpoint'} else validation)
        machine = types.ModuleType('owned_digest_machine')
        machine.digest = lambda value: p.digest(p.encoded(value))
        machine.validate = lambda actual, digest: self.assertEqual(actual, state)
        registrar = types.ModuleType('methods_digest_registration')
        registrar.require_registration = lambda root, binding, ledger: {'receipt': {'record_id': state['record_id'], 'package_path': package.relative_to(self.root).as_posix(), 'children': [{'run_id': 'Run-127'}], 'public_evidence': {'fixture': 'public'}}}
        registrar.entity_rows = lambda *args: deepcopy(rows)
        registrar._object = lambda *args: (self.root, {})
        registrar.current_digest = lambda *args: ({}, {})
        registrar._snapshot_digest = lambda *args: self.events.append('material_snapshot')
        registrar._check_public = lambda *args, **kwargs: self.events.append('public_material_check')
        registrar._finish = lambda *args: self.events.append('material_finish')
        registrar.d = types.SimpleNamespace(strict_readback=lambda *args: None)
        corpus = types.ModuleType('corpus_ledger')
        def build(root, certroot, *, previous_ledger):
            self.events.append('fresh_scan')
            return deepcopy(previous_ledger)
        def cas(path, value, expected):
            self.assertEqual(p.digest(path.read_bytes()), expected)
            self.events.append('ssot_cas')
            path.write_bytes(p.encoded(value))
            return p.digest(path.read_bytes())
        corpus.build = build
        corpus.write_guarded_ledger = cas
        live = types.ModuleType('weekly_digest_runtime')
        live.require_origin = lambda *args: self.events.append('origin')
        for i, module in enumerate((engine, machine, registrar, corpus, live), 100):
            module.__file__ = self.pins[i]['path']
            self.install(module.__name__, module)
            self.modules[module.__name__] = module
        real_load = p.load
        real_bound = p.bound
        closure_rows = []
        original_require = self.current.require_current_closure
        def full_current(binding):
            count = len(json.loads(ssot.read_bytes())['publication_entities'])
            closure_rows.append(count)
            result = original_require(binding)
            if count > 1 and fail_after_cas:
                raise ValueError('HOLD_SYNTHETIC_FINAL_CLOSURE_AFTER_CAS')
            return result
        self.current.require_current_closure = full_current
        def routed_load(root, binding, name):
            if name == '_exact_postpublish_source_session':
                return self.invoke
            if name == '_exact_postpublish_current_runtime':
                return self.current
            self.assertGreater(self.depth, 0)
            return real_load(root, binding, name)
        # Synthetic register_once parses a fresh plan; session uses the same
        # exact contents rather than Python object identity for this fixture.
        @contextlib.contextmanager
        def session(root, actual_plan):
            self.assertEqual(actual_plan, self.plan)
            self.depth += 1
            self.events.append('session_enter')
            try:
                yield
            finally:
                self.depth -= 1
                self.events.append('session_exit')
        self.invoke.session = session
        def routed_bound(root, value):
            if value in ({'fixture': 'checkpoint'}, {'fixture': 'validation'}):
                return self.root / 'plan.json', plan_path.read_bytes()
            return real_bound(root, value)
        output = self.root / 'reports/verification-coverage/fixture-postpublish'
        with patch.object(p, 'ROOT', self.root), patch.object(p, 'verify_config'), patch.object(p, 'load', side_effect=routed_load), patch.object(p, 'bound', side_effect=routed_bound):
            if fail_after_cas:
                with self.assertRaisesRegex(ValueError, 'FINAL_CLOSURE_AFTER_CAS'):
                    p.register_once(config, output)
            else:
                result = p.register_once(config, output)
                self.assertEqual(result['status'], 'PRESERVING_REGISTRATION_FRESH_RESCAN_PASS')
        self.assertEqual(closure_rows, [1, 3])
        self.assertEqual(self.events.count('ssot_cas'), 1)
        self.assertEqual(self.events.count('fresh_scan'), 2)
        self.assertEqual(json.loads(ssot.read_bytes())['enforcement_activation'], before['enforcement_activation'])
        self.assertEqual(json.loads(ssot.read_bytes())['publication_entities'][0], before['publication_entities'][0])
        self.assertEqual((output / 'RESULT.json').exists(), not fail_after_cas)
        self.assert_restored()

    def test_post_cas_final_closure_runs_and_restores_purpose_cache(self):
        self.registration_fixture(fail_after_cas=False)

    def test_post_cas_final_closure_failure_never_seals_success(self):
        self.registration_fixture(fail_after_cas=True)


if __name__ == '__main__':
    unittest.main()
