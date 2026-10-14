"""Cold import-scope regressions using genuine old finder/session bodies.

All admission inputs and imports are synthetic resolved temporary files. The
original reader/finder/cache-view bodies are selected from SHA-bound sources;
no production validate, corpus build, health, recovery or network call runs.
These contributor tests are not an independent implementation review.
"""
import ast
import contextlib
import hashlib
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
BUILDER_SHA = 'da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740'
VIEW_SHA = '1bc540543f0058eeff6e3d5e80bdee20858be387b0a9e36bc11019407747d771'
BUILDER_GIT = 'production_snapshots/phase7-20261008-owned-weekly-source-provenance/after/production_execution_dependencies/prepare_first_seven_plan.py'
VIEW_GIT = 'production_snapshots/phase7-20261008-own-record-comparison/before/execution/runtime_closure_view.py'
PRIVATE_ARCHIVE = 'reports/verification-coverage/2026-10-09/prior-content-digest-execution-v001/weekly-source-adoption-v001'


def exact_old_source(kind):
    name, expected, git = ('prepare_first_seven_plan.py', BUILDER_SHA, BUILDER_GIT) if kind == 'builder' else ('runtime_closure_view.py', VIEW_SHA, VIEW_GIT)
    choices = [HERE.parents[1] / git, HERE.parents[2] / PRIVATE_ARCHIVE / name]
    found = [p for p in choices if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == expected]
    if not found:
        raise AssertionError('genuine SHA-bound original scope source unavailable: ' + name)
    return found[0].read_bytes()


def scope_bodies(kind):
    """Keep exact original AST bodies; omit unrelated production globals/main."""
    names = ({'PlanHold', 'require', 'sha_bytes', 'read', 'sha', 'verify_loaded', 'SourceLoader', 'SourceFinder', 'source_session'}
             if kind == 'builder' else {'ScopeHold', 'need', 'verify_own_cache', 'exact_runtime_view'})
    selected = [n for n in ast.parse(exact_old_source(kind)).body
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names]
    if {n.name for n in selected} != names:
        raise AssertionError('incomplete genuine source-session body selection')
    prelude = 'import contextlib, hashlib, importlib.abc, importlib.machinery, importlib.util, sys\nfrom pathlib import Path\n'
    return (prelude + ast.unparse(ast.Module(body=selected, type_ignores=[])) + '\n').encode()


def module_from_bytes(name, raw, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def candidate_runtime():
    # No gate directory or production module is added to sys.path.
    path = HERE / 'packaging_runtime.py'
    return module_from_bytes('_synthetic_v002_cold_runtime', path.read_bytes(), path)


def put(root, relative, value):
    p = root / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    p.write_bytes(raw)
    return {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest()}


@contextlib.contextmanager
def cold_cache(names):
    """Restore every pre-existing module identity; discard only fixture imports."""
    previous = {name: sys.modules.pop(name) for name in names if name in sys.modules}
    try:
        yield
    finally:
        for name in names:
            sys.modules.pop(name, None)
        sys.modules.update(previous)


def origin(root, label, rows, runtime):
    oid, tree_sha = 'a' * 40, 'b' * 40
    blobs = []
    for row in rows:
        raw = Path(row['path']).read_bytes()
        blobs.append({'path': row['git_path'], 'mode': '100644', 'type': 'blob',
                      'sha': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()})
    return {
        'pull_request': put(root, label + '/pr.json', {'state': 'MERGED', 'baseRefName': 'main', 'number': 999,
            'url': 'https://github.com/jdhart81/viridis-canon/pull/999', 'mergeCommit': {'oid': oid},
            'statusCheckRollup': [{'name': n, 'status': 'COMPLETED', 'conclusion': 'SUCCESS'} for n in runtime.REQUIRED_CHECKS]}),
        'merge_commit': put(root, label + '/commit.json', {'sha': oid, 'tree': {'sha': tree_sha}}),
        'tree': put(root, label + '/tree.json', {'sha': tree_sha, 'truncated': False, 'tree': blobs}),
    }


@contextlib.contextmanager
def synthetic_validation_case(mode='ok'):
    """Real v002 validate body and actual finder; fake authority is explicit."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary).resolve()
        runtime = candidate_runtime()
        original_sources = {
            'prepare_first_seven_plan.py': scope_bodies('builder'),
            'runtime_closure_view.py': scope_bodies('view'),
            'corpus_ledger.py': b"ORIGIN = 'SYNTHETIC_ORIGINAL'\ndef build(*a, **kw):\n    raise AssertionError('SOURCE_ONLY must not build scientific corpus')\n",
            'runtime_successor.py': (
                "import hashlib, json\nfrom pathlib import Path\nimport corpus_ledger\nimport packaging_catalog\n"
                "if type(corpus_ledger.__loader__).__name__ != 'SourceLoader' or type(packaging_catalog.__loader__).__name__ != 'SourceLoader':\n"
                "    raise AssertionError('original/candidate must resolve through genuine finder')\n"
                "def read_bound_closure(binding):\n    return json.loads(Path(binding['path']).read_bytes())\n"
                "def current_closure(folder, protected):\n" +
                ("    raise RuntimeError('synthetic helper failure inside original scope')\n" if mode == 'helper-failure' else
                 "    if hashlib.sha256(Path(protected['path']).read_bytes()).hexdigest() != protected['sha256']:\n"
                 "        raise ValueError('synthetic protected fixture changed')\n"
                 "    return json.loads((Path(folder) / 'closure.json').read_bytes())\n") +
                "def preserving_population(*a, **kw):\n    raise AssertionError('SOURCE_ONLY cannot claim scientific population admission')\n").encode(),
        }
        original_sources.update({f'_cold_original_{i:03d}.py': b'# synthetic original pin\n' for i in range(126)})
        originals = []
        for name, raw in original_sources.items():
            value = put(root, 'original-gates/' + name, raw)
            originals.append({'name': name, **value, 'git_path': 'fixture/original/' + name})
        base = [{k: row[k] for k in ('name', 'path', 'sha256')} for row in originals]
        by_name = {row['name']: {k: row[k] for k in ('path', 'sha256')} for row in base}
        old_origin = origin(root, 'original-proof', originals, runtime)
        protected = put(root, 'protected.json', {'fixture': 'not scientific admission'})
        closure = put(root, 'closure.json', {'source_pins': base[:99], 'protected_readback': protected, 'certifies': False})
        scope = put(root, 'scope.json', {'canonical_root': str(root), 'purpose_source_pins': base,
            'source_session_consumer': by_name['prepare_first_seven_plan.py'], 'current_runtime_closure': closure,
            'runtime_consumer': by_name['runtime_successor.py'], 'source_origin': {
                'merged_pr': old_origin['pull_request'], 'merged_commit': old_origin['merge_commit'],
                'merged_tree': old_origin['tree'], 'source_rows': originals}})
        modules = []
        for name in sorted(runtime.MODULE_NAMES):
            raw = b"ORIGIN = 'SYNTHETIC_CANDIDATE'\n" if name == 'packaging_catalog.py' else b'# synthetic additive pin\n'
            value = put(root, 'candidate-gates/' + name, raw)
            modules.append({'name': name, **value, 'git_path': runtime.GIT_PREFIX + name})
        new_origin = origin(root, 'additive-proof', modules, runtime)
        provider = put(root, 'provider.json', {'standard': 'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1',
            'provider_tool': 'mcp__codex_app__read_thread', 'thread_id': '01a12d47-02a3-78f3-beb4-6b8e1a079dd2',
            'user_messages': [{'type': 'userMessage', 'id': '01a132f6-4708-7440-a9ba-ebf03deeb906',
                'content': [{'type': 'text', 'text': runtime.USER_DIRECTIVE + '\n'}]}]})
        authority = put(root, 'authority.json', {'standard': 'VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1',
            'source': 'Current user message in this Codex chat', 'user_text': runtime.USER_DIRECTIVE,
            'captured_at_utc': '2020-01-01T00:00:00Z', 'scientific_scope_changes': False, 'provider_instruction': provider})
        review = put(root, 'review.json', {'standard': 'VRS-INDEPENDENT-PDF-RUNTIME-SOURCE-REVIEW-13',
            'status': 'EXACT_COMPLETE_CANDIDATE_REVIEW_PASS', 'reviewer': 'Synthetic fixture only; no production authority',
            'source_hashes': {r['name']: r['sha256'] for r in modules}, 'legacy_closure': closure,
            **runtime.SOURCE_REVIEW_CHANGE_FLAGS, 'review_scope': 'SOURCE_ONLY',
            'actual_live_runtime_admission': False, 'actual_seven_record_admission': 'PENDING_POST_INSTALL_FRESH_READBACK'})
        registry = put(root, 'registry.json', {'fixture': 'no live reads'})
        put(root, 'RESEARCH_PIPELINE_v2/corpus_ledger.json', {'publication_entities': [], 'fixture': 'not a science population'})
        profile = put(root, runtime.PROFILE_PATH, {'standard': runtime.STANDARD, 'status': runtime.STATUS,
            'canonical_root': str(root), 'installed_at_utc': '2020-01-02T00:00:00Z', 'user_authority': authority,
            'legacy_closure': closure, 'legacy_consumer': by_name['runtime_successor.py'], 'legacy_scope': scope,
            'source_session_consumer': by_name['prepare_first_seven_plan.py'], 'modules': modules,
            'source_origin': new_origin, 'source_review': review, 'access_registry': registry,
            'default_routes': runtime.DEFAULT_ROUTES, 'predecessor_installation': runtime.PREDECESSOR_INSTALLATION,
            'transient_rehydration': runtime.TRANSIENT_REHYDRATION_POLICY,'data_alias_observation':registry,'platform_timezone_observation':registry})
        events = []
        real_proof, real_load = runtime.source_proof, runtime.load

        def prove(*args, **kwargs):
            result = real_proof(*args, **kwargs)
            events.append('proved-original' if len(args[2]) == 130 else 'proved-additive')
            return result

        def load(*args, **kwargs):
            if args[1] in (by_name['runtime_successor.py'], by_name['runtime_closure_view.py']):
                if not {'proved-original', 'proved-additive', 'root-plan-checked'} <= set(events):
                    raise AssertionError('operational exec before complete source proof')
                if not any(type(f).__name__ == 'SourceFinder' for f in sys.meta_path):
                    raise AssertionError('cold operational exec before genuine source finder')
            return real_load(*args, **kwargs)

        names = {r['name'][:-3] for r in [*base, *modules]}
        with contextlib.ExitStack() as stack:
            stack.enter_context(cold_cache(names))
            for field, value in [('LEGACY_CLOSURE', closure), ('LEGACY_SCOPE', scope),
                                 ('LEGACY_CONSUMER', by_name['runtime_successor.py']),
                                 ('SESSION_CONSUMER', by_name['prepare_first_seven_plan.py']),
                                 ('PROVIDER_SHA', provider['sha256'])]:
                stack.enter_context(patch.object(runtime, field, value))
            stack.enter_context(patch.object(runtime, 'require_nomination', return_value={'merged_source_commit': 'a' * 40}))
            stack.enter_context(patch.object(runtime,'require_data_alias_observation',return_value={'explicit_synthetic_alias_fixture':True}))
            stack.enter_context(patch.object(runtime,'require_platform_timezone_observation',return_value={'explicit_synthetic_native_fixture':True}))
            stack.enter_context(patch.object(runtime, 'predecessor_installation', return_value={'fixture': 'separately tested'}))
            stack.enter_context(patch.object(runtime, 'require_installed_plan', side_effect=lambda *a: events.append('root-plan-checked')))
            stack.enter_context(patch.object(runtime, 'legacy_transient_precheck', return_value={'transient_source_writes': 0, 'fixture': 'separately tested'}))
            stack.enter_context(patch.object(runtime, 'source_proof', side_effect=prove))
            stack.enter_context(patch.object(runtime, 'load', side_effect=load))
            stack.enter_context(patch('socket.create_connection', side_effect=AssertionError('synthetic fixture must not use network')))
            yield root, runtime, profile, base, modules, events


def child_case(mode):
    before_finders = tuple(sys.meta_path)
    before_spec = importlib.util.spec_from_file_location
    error = None
    with synthetic_validation_case(mode) as (root, runtime, profile, base, modules, events):
        if any(str(root / directory) in sys.path for directory in ('original-gates', 'candidate-gates')):
            raise AssertionError('fixture gates must not enter sys.path')
        try:
            result = runtime.validate(root, profile)
        except Exception as exc:
            result = None
            error = {'type': type(exc).__name__, 'message': str(exc)}
        if tuple(sys.meta_path) != before_finders or importlib.util.spec_from_file_location is not before_spec:
            raise AssertionError('genuine finder/spec cleanup failed')
        report = {'mode': mode, 'result': result, 'error': error, 'events': events,
                  'finder_and_spec_restored': True, 'real_production_admission': False}
    print(json.dumps(report, sort_keys=True))
    return 0 if error is None else 3


class ColdValidateEntryTests(unittest.TestCase):
    def child(self, mode):
        with tempfile.TemporaryDirectory() as temporary:
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            return subprocess.run([sys.executable, '-B', str(Path(__file__).resolve()), '--synthetic-cold-child', mode],
                                  cwd=Path(temporary).resolve(), env=env, text=True, capture_output=True, timeout=20)

    def test_cold_direct_cli_resolves_original_and_candidate_through_genuine_finder(self):
        completed = self.child('ok')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report['result']['status'], 'ACTUAL_SOURCE_HELPER_AND_ADDITIVE_PACKAGING_SCOPE_PASS')
        self.assertIs(report['result']['scientific_population_admitted'], False)
        self.assertIs(report['result']['certifies'], False)
        self.assertEqual(report['result']['ssot_writes'], 0)
        self.assertTrue(report['finder_and_spec_restored'])
        self.assertEqual(len(report['result']['source_pins']), 149)

    def test_cold_child_failure_returns_nonzero_and_restores_genuine_scope(self):
        completed = self.child('helper-failure')
        self.assertEqual(completed.returncode, 3, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertIn('synthetic helper failure', report['error']['message'])
        self.assertTrue(report['finder_and_spec_restored'])
        self.assertIsNone(report['result'])

    def test_changed_original_source_holds_before_operational_exec(self):
        before = tuple(sys.meta_path), importlib.util.spec_from_file_location
        with synthetic_validation_case() as (root, runtime, profile, base, modules, events):
            Path(next(r['path'] for r in base if r['name'] == 'corpus_ledger.py')).write_bytes(b'# changed fixture source\n')
            with self.assertRaisesRegex(runtime.PackagingHold, 'SOURCE_HASH_OR_RACE'):
                runtime.validate(root, profile)
            self.assertEqual(events, [])
            self.assertNotIn('corpus_ledger', sys.modules)
        self.assertEqual(tuple(sys.meta_path), before[0])
        self.assertIs(importlib.util.spec_from_file_location, before[1])

    def test_foreign_cached_original_module_is_rejected_before_import(self):
        before = tuple(sys.meta_path), importlib.util.spec_from_file_location
        with synthetic_validation_case() as (root, runtime, profile, base, modules, events):
            foreign = types.ModuleType('corpus_ledger')
            foreign.__file__ = str(root / 'foreign.py')
            (root / 'foreign.py').write_bytes(b'# unapproved fixture module\n')
            sys.modules['corpus_ledger'] = foreign
            with self.assertRaisesRegex(ValueError, 'FOREIGN_OR_CONFLICTING_OWN_IMPORT'):
                runtime.validate(root, profile)
            self.assertIs(sys.modules['corpus_ledger'], foreign)
        self.assertEqual(tuple(sys.meta_path), before[0])
        self.assertIs(importlib.util.spec_from_file_location, before[1])

    def test_body_failure_still_rechecks_protected_helper_inputs_and_cleans_scope(self):
        before = tuple(sys.meta_path), importlib.util.spec_from_file_location
        cached = {name: sys.modules.get(name) for name in ('corpus_ledger', 'packaging_catalog')}
        with synthetic_validation_case() as (root, runtime, profile, base, modules, events):
            protected = json.loads((root / 'closure.json').read_bytes())['protected_readback']
            with self.assertRaisesRegex(ValueError, 'synthetic protected fixture changed') as held:
                with runtime.session(root, profile):
                    self.assertTrue(any(type(f).__name__ == 'SourceFinder' for f in sys.meta_path))
                    Path(protected['path']).write_bytes(b'changed protected fixture during failed body')
                    raise RuntimeError('synthetic operational body failure')
            self.assertIsInstance(held.exception.__context__, RuntimeError)
            self.assertIn('synthetic operational body failure', str(held.exception.__context__))
            # Two entry validations and the unconditional source-only exit
            # validation all execute the genuine merged-source proof path.
            self.assertEqual(events.count('proved-original'), 3)
            self.assertEqual(events.count('proved-additive'), 3)
            self.assertEqual(tuple(sys.meta_path), before[0])
            self.assertIs(importlib.util.spec_from_file_location, before[1])
        for name, identity in cached.items():
            self.assertIs(sys.modules.get(name), identity)


class GenuineScopeCleanupTests(unittest.TestCase):
    @contextlib.contextmanager
    def scope_fixture(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            rows = []
            for name in ('_cold_original_probe', '_cold_candidate_probe'):
                value = put(root, 'gates/' + name + '.py', ('VALUE = ' + repr(name) + '\n').encode())
                rows.append({'name': name + '.py', **value})
            builder = module_from_bytes('_genuine_fixture_builder', scope_bodies('builder'), root / 'builder.py')
            view = module_from_bytes('_genuine_fixture_view', scope_bodies('view'), root / 'view.py')
            with cold_cache({r['name'][:-3] for r in rows}):
                yield root, rows, builder, view

    def test_nested_failure_restores_outer_finder_and_then_original_hooks(self):
        before = tuple(sys.meta_path), importlib.util.spec_from_file_location
        with self.scope_fixture() as (root, rows, builder, view):
            with builder.source_session(root, rows):
                original = importlib.import_module('_cold_original_probe')
                outer = tuple(sys.meta_path), importlib.util.spec_from_file_location
                with self.assertRaisesRegex(RuntimeError, 'nested fixture failure'):
                    with builder.source_session(root, rows):
                        self.assertIs(importlib.import_module('_cold_original_probe'), original)
                        raise RuntimeError('nested fixture failure')
                self.assertEqual(tuple(sys.meta_path), outer[0])
                self.assertIs(importlib.util.spec_from_file_location, outer[1])
                self.assertIs(sys.modules['_cold_original_probe'], original)
        self.assertEqual(tuple(sys.meta_path), before[0])
        self.assertIs(importlib.util.spec_from_file_location, before[1])

    def test_unchanged_old_cache_view_restores_purpose_only_identity_on_failure(self):
        with self.scope_fixture() as (root, rows, builder, view):
            with builder.source_session(root, rows):
                original = importlib.import_module('_cold_original_probe')
                candidate = importlib.import_module('_cold_candidate_probe')
                with self.assertRaisesRegex(RuntimeError, 'view fixture failure'):
                    with view.exact_runtime_view(root, rows, rows[:1]):
                        self.assertIs(sys.modules['_cold_original_probe'], original)
                        self.assertNotIn('_cold_candidate_probe', sys.modules)
                        raise RuntimeError('view fixture failure')
                self.assertIs(sys.modules['_cold_candidate_probe'], candidate)

    def test_tampered_import_holds_without_leaking_finder_or_spec_override(self):
        before = tuple(sys.meta_path), importlib.util.spec_from_file_location
        with self.scope_fixture() as (root, rows, builder, view):
            with self.assertRaisesRegex(ValueError, 'PINNED_IMPORT_CHANGED|RUNTIME_CLOSURE_CHANGED'):
                with builder.source_session(root, rows):
                    Path(rows[0]['path']).write_bytes(b"raise AssertionError('untrusted bytes must not execute')\n")
                    importlib.import_module('_cold_original_probe')
            self.assertNotIn('_cold_original_probe', sys.modules)
        self.assertEqual(tuple(sys.meta_path), before[0])
        self.assertIs(importlib.util.spec_from_file_location, before[1])


if __name__ == '__main__':
    if sys.argv[1:2] == ['--synthetic-cold-child']:
        raise SystemExit(child_case(sys.argv[2]))
    unittest.main()
