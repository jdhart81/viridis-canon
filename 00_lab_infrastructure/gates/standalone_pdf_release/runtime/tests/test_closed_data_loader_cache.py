"""Fixture-only compiler reuse preserves fresh source checks and execution.

Every source below is tiny, explicitly registered DATA in a new private root.
The real loader constructor, source checker, transformer, compiler and exec run.
These tests establish no scientific, source-session or publication admission.
"""
from __future__ import annotations

import __future__
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from closed_data_loader import ClosedDataLoader


class ClosedDataLoaderCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='w42-compiler-cache-')
        self.addCleanup(self.temporary.cleanup)
        self.loader = ClosedDataLoader(Path(self.temporary.name) / 'closed-loader')
        self.addCleanup(self.loader.clear_code_cache)
        self.raw = (b'from pathlib import Path\nROOT = Path("original")\n'
                    b'VALUES = []\nVALUES.append("fresh execution")\n'
                    b'def result():\n    return ROOT, VALUES\n')
        self.path, self.digest = self.source('tiny_registered.py', self.raw)

    def source(self, name, raw):
        path = self.loader.root / 'cache-test-sources' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        digest = self.loader.register_source(path, raw)
        return path, digest

    def compile(self, **options):
        return self.loader.compile(self.raw, str(self.path), 'exec', **options)

    def stats(self):
        result = self.loader.compile_cache_stats()
        fields = {
            'compile_interface_calls', 'pure_code_derivations', 'cache_hits',
            'cache_misses', 'uncached_calls', 'actual_exec_calls',
            'successful_exec_calls', 'source_checks', 'cache_entries',
            'cache_serialized_bytes', 'cache_evictions', 'cache_clears',
            'peak_cache_entries', 'peak_cache_serialized_bytes',
            'max_cache_entries', 'max_cache_serialized_bytes',
        }
        self.assertEqual(set(result), fields)
        self.assertTrue(all(type(value) is int and value >= 0
                            for value in result.values()))
        return result

    def delta(self, before, field):
        return self.stats()[field] - before[field]

    def assert_holds(self, operation, cause):
        held = None
        try:
            operation()
        except (ValueError, OSError, AssertionError) as error:
            held = error
        self.assertIsNotNone(held, 'missing required source-integrity HOLD: ' + cause)
        return held

    def test_reuses_code_but_runs_fresh_globals_and_per_call_source_proof(self):
        before = self.stats(); receipts = len(self.loader.receipts)
        first = self.compile(); second = self.compile()
        self.assertIsInstance(first, types.CodeType)
        self.assertIs(first, second)
        a, b = {'__name__': 'first'}, {'__name__': 'second'}
        self.loader.execute(first, a); a['VALUES'].append('caller state')
        self.loader.execute(second, b)
        self.assertEqual(b['VALUES'], ['fresh execution'])
        self.assertIsNot(a['VALUES'], b['VALUES'])
        self.assertIsNot(a['result'], b['result'])
        self.assertIs(a['result'].__globals__, a)
        self.assertIs(b['result'].__globals__, b)
        self.assertEqual(len(self.loader.receipts) - receipts, 2)
        self.assertEqual(self.delta(before, 'compile_interface_calls'), 2)
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.assertEqual(self.delta(before, 'cache_hits'), 1)
        self.assertEqual(self.delta(before, 'actual_exec_calls'), 2)
        self.assertEqual(self.delta(before, 'successful_exec_calls'), 2)
        self.assertGreaterEqual(self.delta(before, 'source_checks'), 4)

    def test_cached_serialized_proof_is_rehydrated_without_mutable_aliases(self):
        self.loader.remaps[self.digest] = {'ROOT': 'Path("fixture-root")'}
        self.compile(); original = copy.deepcopy(self.loader.receipts[-1])
        old = self.loader.receipts[-1]
        old['declared_data_globals']['ROOT'] = 'Path("corrupted-report-only")'
        old['registered_exact_paths'].append('corrupted-report-only')
        old['function_class_ast_hashes']['result'] = 'corrupted-report-only'
        self.compile(); fresh = self.loader.receipts[-1]
        self.assertEqual(fresh, original)
        self.assertIsNot(fresh, old)
        self.assertIsNot(fresh['declared_data_globals'], old['declared_data_globals'])
        self.assertIsNot(fresh['registered_exact_paths'], old['registered_exact_paths'])
        self.assertIsNot(fresh['function_class_ast_hashes'], old['function_class_ast_hashes'])

    def test_warm_hit_rechecks_missing_and_changed_physical_source(self):
        self.compile(); before = self.stats()
        self.path.unlink()
        self.assert_holds(self.compile, 'missing physical source')
        self.path.write_bytes(self.raw + b'\n# physical drift\n')
        self.assert_holds(self.compile, 'physical bytes changed with original raw argument')
        self.path.write_bytes(self.raw)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertIsInstance(self.compile(), types.CodeType)

    def test_warm_hit_rejects_final_and_parent_symlink_sources(self):
        self.compile(); original = self.path.with_name('physical_original.py')
        self.path.rename(original); self.path.symlink_to(original)
        try:
            self.assert_holds(self.compile, 'final source symlink')
        finally:
            self.path.unlink(); original.rename(self.path)
        directory = self.path.parent; renamed = directory.with_name('physical-directory')
        directory.rename(renamed); directory.symlink_to(renamed, target_is_directory=True)
        try:
            self.assert_holds(self.compile, 'source ancestor symlink')
        finally:
            directory.unlink(); renamed.rename(directory)

    def test_warm_hit_rejects_changed_raw_and_unregistered_or_foreign_filename(self):
        self.compile(); before = self.stats()
        self.assert_holds(lambda: self.loader.compile(self.raw + b'\n', str(self.path), 'exec'),
                          'raw hash changed')
        unregistered = self.loader.root / 'unregistered.py'; unregistered.write_bytes(self.raw)
        foreign = Path(self.temporary.name) / 'foreign.py'; foreign.write_bytes(self.raw)
        for path in (unregistered, foreign):
            self.assert_holds(lambda p=path: self.loader.compile(self.raw, str(p), 'exec'),
                              'unregistered physical source path')
        self.assertEqual(self.delta(before, 'cache_hits'), 0)

    def test_exact_requested_filename_spelling_is_part_of_compiler_key(self):
        first = self.compile(); before = self.stats()
        relative = os.path.relpath(self.path, Path.cwd())
        second = self.loader.compile(self.raw, relative, 'exec')
        self.assertEqual(first.co_filename, str(self.path))
        self.assertEqual(second.co_filename, relative)
        self.assertIsNot(first, second)
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        third = self.loader.compile(self.raw, relative, 'exec')
        self.assertIs(second, third)

    def test_registered_same_raw_alias_rederives_full_registered_path_proof(self):
        first = self.compile(); before = self.stats()
        alias, digest = self.source('same_raw_registered.py', self.raw)
        self.assertEqual(digest, self.digest)
        second = self.compile()
        self.assertIsNot(first, second)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.assertEqual(self.loader.receipts[-1]['registered_exact_paths'],
                         sorted((str(self.path), str(alias))))
        alias_code = self.loader.compile(self.raw, str(alias), 'exec')
        self.assertEqual(alias_code.co_filename, str(alias))

    def test_data_remap_change_is_rederived_and_never_reuses_old_values(self):
        self.loader.remaps[self.digest] = {'ROOT': 'Path("first")'}
        first = self.compile(); before = self.stats()
        self.loader.remaps[self.digest] = {'ROOT': 'Path("second")'}
        second = self.compile(); namespace = {}
        self.loader.execute(second, namespace)
        self.assertEqual(namespace['ROOT'], Path('second'))
        self.assertIsNot(first, second)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.assertEqual(self.loader.receipts[-1]['declared_data_globals'],
                         {'ROOT': 'Path("second")'})

    def test_warm_hit_still_rejects_non_literal_and_unapplied_remaps(self):
        self.loader.remaps[self.digest] = {'ROOT': 'Path("accepted")'}
        self.compile(); before = self.stats()
        for remap, cause in (({'ROOT': 'open("unreachable")'}, 'non literal DATA expression'),
                             ({'ABSENT': '1'}, 'unapplied undeclared DATA name')):
            self.loader.remaps[self.digest] = remap
            self.assert_holds(self.compile, cause)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)

    def test_allowlist_changes_rederive_and_revocation_holds_on_warm_cache(self):
        raw = b'OTHER = 1\n'
        path, digest = self.source('closed_extra_data.py', raw)
        self.loader.explicit_extra_allowlist[digest] = frozenset({'OTHER'})
        self.loader.remaps[digest] = {'OTHER': '2'}
        compile_source = lambda: self.loader.compile(raw, str(path), 'exec')
        first = compile_source(); before = self.stats()
        self.loader.explicit_extra_allowlist[digest] = frozenset({'OTHER', 'UNUSED'})
        second = compile_source()
        self.assertIsNot(first, second)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.loader.explicit_extra_allowlist[digest] = frozenset()
        self.assert_holds(compile_source, 'closed DATA allowlist revocation')

    def test_baseline_and_registration_metadata_corruption_cannot_be_cached(self):
        self.compile(); baseline = copy.deepcopy(self.loader.source_baselines[self.digest])
        original_known = self.loader.known[self.digest]
        original_paths = set(self.loader.source_paths[self.digest])
        mutations = (
            lambda: self.loader.source_baselines[self.digest].update(original_sha256='0' * 64),
            lambda: self.loader.source_baselines[self.digest]['original_function_class_asts'].update(result='0' * 64),
            lambda: self.loader.source_baselines[self.digest]['appended_literal_data_names'].append('UNDECLARED'),
            lambda: self.loader.known.__setitem__(self.digest, (original_known[0], self.raw + b'\n')),
            lambda: self.loader.source_paths[self.digest].add(str(self.loader.root / 'not-registered.py')),
        )
        for number, mutate in enumerate(mutations):
            with self.subTest(number=number):
                mutate()
                try:
                    self.assert_holds(self.compile, 'immutable registered baseline corruption')
                finally:
                    self.loader.source_baselines[self.digest] = copy.deepcopy(baseline)
                    self.loader.known[self.digest] = original_known
                    self.loader.source_paths[self.digest] = set(original_paths)

    def test_post_compile_source_race_holds_before_cache_or_proof_commit(self):
        original = self.loader.real_compile
        def racing_compile(*args, **kwargs):
            code = original(*args, **kwargs)
            self.path.write_bytes(self.raw + b'\n# changed while deriving\n')
            return code
        self.loader.real_compile = racing_compile
        before = self.stats(); receipts = len(self.loader.receipts)
        self.assert_holds(self.compile, 'post-derivation physical source compare-and-swap')
        self.assertEqual(self.stats()['cache_entries'], before['cache_entries'])
        self.assertEqual(len(self.loader.receipts), receipts)

    def test_post_compile_data_race_holds_before_cache_or_proof_commit(self):
        original = self.loader.real_compile
        self.loader.remaps[self.digest] = {'ROOT': 'Path("before-compile")'}
        def racing_compile(*args, **kwargs):
            code = original(*args, **kwargs)
            self.loader.remaps[self.digest] = {'ROOT': 'Path("during-compile")'}
            return code
        self.loader.real_compile = racing_compile
        before = self.stats(); receipts = len(self.loader.receipts)
        self.assert_holds(self.compile, 'post-derivation DATA compare-and-swap')
        self.assertEqual(self.stats()['cache_entries'], before['cache_entries'])
        self.assertEqual(len(self.loader.receipts), receipts)

    def test_compiler_flags_inheritance_and_optimization_have_distinct_keys(self):
        plain = self.compile(flags=0, dont_inherit=True, optimize=0)
        inherited = self.compile(flags=0, dont_inherit=False, optimize=0)
        future = self.compile(flags=__future__.annotations.compiler_flag,
                              dont_inherit=True, optimize=0)
        optimized = self.compile(flags=0, dont_inherit=True, optimize=1)
        self.assertEqual(plain.co_flags & __future__.annotations.compiler_flag, 0)
        self.assertNotEqual(inherited.co_flags & __future__.annotations.compiler_flag, 0)
        self.assertNotEqual(future.co_flags & __future__.annotations.compiler_flag, 0)
        self.assertIsNot(plain, inherited)
        self.assertIsNot(plain, future)
        self.assertIsNot(plain, optimized)
        for options, expected in (({'flags': 0, 'dont_inherit': True, 'optimize': 0}, plain),
                                  ({'flags': 0, 'dont_inherit': False, 'optimize': 0}, inherited),
                                  ({'flags': __future__.annotations.compiler_flag,
                                    'dont_inherit': True, 'optimize': 0}, future),
                                  ({'flags': 0, 'dont_inherit': True, 'optimize': 1}, optimized)):
            self.assertIs(self.compile(**options), expected)

    def test_unknown_kwargs_and_ast_returning_compile_are_uncached(self):
        before = self.stats()
        first = self.compile(_feature_version=7)
        second = self.compile(_feature_version=7)
        self.assertIsInstance(first, types.CodeType)
        self.assertIsNot(first, second)
        a = self.compile(flags=ast.PyCF_ONLY_AST)
        b = self.compile(flags=ast.PyCF_ONLY_AST)
        self.assertIsInstance(a, ast.Module)
        self.assertIsInstance(b, ast.Module)
        self.assertIsNot(a, b)
        self.assertEqual(self.delta(before, 'uncached_calls'), 4)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.stats()['cache_entries'], before['cache_entries'])

    def test_replacing_compiler_callable_requires_new_pure_derivation(self):
        first = self.compile(); original = self.loader.real_compile; calls = []
        def replacement(*args, **kwargs):
            calls.append((args[1], args[2]))
            return original(*args, **kwargs)
        self.loader.real_compile = replacement; before = self.stats()
        second = self.compile(); third = self.compile()
        self.assertIsNot(first, second)
        self.assertIs(second, third)
        self.assertEqual(calls, [(str(self.path), 'exec')])
        self.assertEqual(self.delta(before, 'pure_code_derivations'), 1)
        self.assertEqual(self.delta(before, 'cache_hits'), 1)

    def test_unhashable_compiler_callable_has_fresh_uncached_derivations(self):
        original = self.loader.real_compile
        class UnhashableCompiler:
            __hash__ = None
            def __call__(self, *args, **kwargs):
                return original(*args, **kwargs)
        self.loader.real_compile = UnhashableCompiler(); before = self.stats()
        first = self.compile(); second = self.compile()
        self.assertIsNot(first, second)
        self.assertEqual(self.delta(before, 'uncached_calls'), 2)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.stats()['cache_entries'], before['cache_entries'])

    def test_cache_bounds_evict_old_code_and_account_serialized_bytes(self):
        self.loader.CACHE_MAX_ENTRIES = 2
        sources = [self.source('bounded_%d.py' % i, ('VALUE = %d\n' % i).encode())
                   for i in range(3)]
        codes = []
        for path, unused_digest in sources:
            codes.append(self.loader.compile(path.read_bytes(), str(path), 'exec'))
            stats = self.stats()
            self.assertLessEqual(stats['cache_entries'], 2)
            self.assertLessEqual(stats['cache_serialized_bytes'], self.loader.CACHE_MAX_BYTES)
        self.assertEqual(self.stats()['cache_entries'], 2)
        self.assertEqual(self.stats()['cache_evictions'], 1)
        self.assertGreater(self.stats()['cache_serialized_bytes'], 0)
        path = sources[0][0]; again = self.loader.compile(path.read_bytes(), str(path), 'exec')
        self.assertIsNot(again, codes[0])
        self.assertEqual(self.stats()['cache_evictions'], 2)
        self.assertLessEqual(self.stats()['peak_cache_entries'], 2)

    def test_byte_limit_does_not_retain_oversize_code_or_proof(self):
        self.loader.CACHE_MAX_BYTES = 1
        before = self.stats(); first = self.compile(); second = self.compile()
        self.assertIsNot(first, second)
        self.assertEqual(self.stats()['cache_entries'], 0)
        self.assertEqual(self.stats()['cache_serialized_bytes'], 0)
        self.assertEqual(self.delta(before, 'cache_hits'), 0)
        self.assertEqual(self.stats()['peak_cache_serialized_bytes'], 0)

    def test_clear_removes_only_derivations_and_preserves_future_execution(self):
        first = self.compile(); before = self.stats()
        self.assertGreater(before['cache_entries'], 0)
        self.loader.clear_code_cache(); empty = self.stats()
        self.assertEqual(empty['cache_entries'], 0)
        self.assertEqual(empty['cache_serialized_bytes'], 0)
        self.assertEqual(empty['cache_clears'], before['cache_clears'] + 1)
        self.assertEqual(empty['compile_interface_calls'], before['compile_interface_calls'])
        second = self.compile(); self.assertIsNot(first, second)
        namespace = {}; self.loader.execute(second, namespace)
        self.assertEqual(namespace['VALUES'], ['fresh execution'])

    def test_cache_entries_contain_immutable_code_proof_and_size_only(self):
        code = self.compile()
        self.assertEqual(len(self.loader._code_cache), 1)
        entry = next(iter(self.loader._code_cache.values()))
        self.assertIs(type(entry), tuple)
        self.assertEqual(len(entry), 3)
        self.assertIs(entry[0], code)
        self.assertIs(type(entry[1]), bytes)
        self.assertIs(type(entry[2]), int)
        self.assertGreater(entry[2], len(entry[1]))
        self.assertEqual(json.loads(entry[1]), self.loader.receipts[-1])

    def test_post_load_platform_data_applies_on_each_fresh_execution(self):
        raw = b'_FROZEN_HASHES = {"from_source": 1}\nbuiltins = "from_source"\n'
        path, digest = self.source('nightly_manuscript_access.py', raw)
        first = self.loader.compile(raw, str(path), 'exec')
        self.loader.post_load_data[digest] = {'_FROZEN_HASHES': {'first': 1}, 'builtins': 'first DATA','LABEL_AUTHORITY':{'path':str(self.loader.root/'first-authority.json'),'sha256':'0'*64},'NATIVE_RENDERER':str(self.loader.root/'fixture-executable'),'RENDER_CACHE':{'path':str(self.loader.root/'fixture-cache.json'),'sha256':'2'*64}}
        a = {}; self.loader.execute(first, a)
        second = self.loader.compile(raw, str(path), 'exec')
        self.loader.post_load_data[digest] = {'_FROZEN_HASHES': {'second': 2}, 'builtins': 'second DATA','LABEL_AUTHORITY':{'path':str(self.loader.root/'second-authority.json'),'sha256':'1'*64},'NATIVE_RENDERER':str(self.loader.root/'fixture-executable'),'RENDER_CACHE':{'path':str(self.loader.root/'fixture-cache.json'),'sha256':'2'*64}}
        b = {}; self.loader.execute(second, b)
        self.assertIs(first, second)
        self.assertEqual(a['_FROZEN_HASHES'], {'first': 1})
        self.assertEqual(a['builtins'], 'first DATA')
        self.assertEqual(b['_FROZEN_HASHES'], {'second': 2})
        self.assertEqual(b['builtins'], 'second DATA')
        self.assertNotEqual(a['LABEL_AUTHORITY'],b['LABEL_AUTHORITY'])
        self.loader.post_load_data[digest]['UNDECLARED'] = True
        self.assert_holds(lambda: self.loader.execute(second, {}), 'closed post-load DATA keys')

    def test_exec_attempts_failures_and_successes_are_separate_counters(self):
        path, unused_digest = self.source('raises.py', b'raise ValueError("fresh exec failure")\n')
        code = self.loader.compile(path.read_bytes(), str(path), 'exec'); before = self.stats()
        with self.assertRaisesRegex(ValueError, 'fresh exec failure'):
            self.loader.execute(code, {})
        self.assertEqual(self.delta(before, 'actual_exec_calls'), 1)
        self.assertEqual(self.delta(before, 'successful_exec_calls'), 0)
        good = self.compile(); self.loader.execute(good, {})
        self.assertEqual(self.delta(before, 'actual_exec_calls'), 2)
        self.assertEqual(self.delta(before, 'successful_exec_calls'), 1)


class ClosedFixtureCorrectionTests(unittest.TestCase):
    """Pure source-selection/adapter controls; no native helper is called.

    Native function objects below are constructed from exact code constants but
    never invoked. Full canonical source-session execution remains the separate
    real normal/negative CI route; these controls cannot qualify Mac or science.
    """
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix='closed-platform-source-')
        self.addCleanup(self.temporary.cleanup)
        self.loader=ClosedDataLoader(Path(self.temporary.name)/'loader')
        self.path=self.loader.root/'canonical-root/_ZENODO_DEPOSITS/standalone_pdf_runtime/nightly_manuscript_access.py'
        self.path.parent.mkdir(parents=True)
        self.raw=(HERE.parent/'nightly_manuscript_access.py').read_bytes()
        self.path.write_bytes(self.raw);self.loader.register_source(self.path,self.raw)
        self.loader.enroll_portable_access_prerequisite(self.path)
        self.code=self.loader.real_compile(self.raw,str(self.path),'exec')
        self.namespace_modules={}

    @staticmethod
    def span(source,name):
        nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)and n.name==name]
        assert len(nodes)==1
        node=nodes[0];lines=source.splitlines(keepends=True)
        return sum(map(len,lines[:node.lineno-1])),sum(map(len,lines[:node.end_lineno]))

    def test_both_actual_legacy_mutation_spans_preserve_linked_and_all_other_bytes(self):
        from run_archival_profile_mutants import MUTANTS,exact_function_mutation
        source=(HERE.parent/'packaging_runtime.py').read_text()
        scopes={'profile_accepts_wrong_note_preparation':'_validate_legacy',
                'source_session_capability_not_revoked':'_session_legacy'}
        for name,file,old,replacement,test in MUTANTS:
            if name not in scopes:continue
            with self.subTest(name=name):
                self.assertEqual(file,'packaging_runtime.py');self.assertEqual(source.count(old),2)
                function=scopes[name];start,end=self.span(source,function)
                changed=exact_function_mutation(source,function,old,replacement)
                expected=source[start:end].replace(old,replacement)
                self.assertEqual(changed,source[:start]+expected+source[end:])
                self.assertEqual(changed.count(old),1)
                # Removing either scoped distinction must fail the same exact
                # byte oracle, rather than being credited as an import error.
                wrong=source.replace(old,replacement)
                with self.assertRaises(AssertionError):
                    self.assertEqual(wrong,source[:start]+expected+source[end:])

    def test_mutation_selector_rejects_missing_duplicate_function_and_duplicate_guard(self):
        from run_archival_profile_mutants import exact_function_mutation
        old='return True';replacement='return False'
        cases=[('def other():\n    return True\n','wanted'),
               ('def wanted():\n    return True\ndef wanted():\n    return True\n','wanted'),
               ('def wanted():\n    return 1\n','wanted'),
               ('def wanted():\n    if True:\n        return True\n    return True\n','wanted')]
        for source,name in cases:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'MUTATION_'):
                exact_function_mutation(source,name,old,replacement)

    def namespace(self,name='nightly_manuscript_access'):
        # Construct code objects only; do not execute the access module or call
        # its prerequisites/native/renderer/validator functions in pure tests.
        module=types.ModuleType(name);namespace=module.__dict__
        namespace['__file__']=str(self.path)
        for code in self.code.co_consts:
            if not isinstance(code,types.CodeType):continue
            if code.co_name=='NativeRenderAdmission':
                methods={c.co_name:types.FunctionType(c,namespace)for c in code.co_consts
                         if isinstance(c,types.CodeType)}
                namespace[code.co_name]=type(code.co_name,(),methods)
            elif code.co_name.startswith('native_render')or code.co_name in {
                    'require_native_render_supervision','close_render_group'}:
                namespace[code.co_name]=types.FunctionType(code,namespace)
        self.namespace_modules[id(namespace)]=module
        return module,namespace

    def apply(self,operation,namespace):
        from unittest.mock import patch
        module=self.namespace_modules[id(namespace)]
        with patch.dict(sys.modules,{'nightly_manuscript_access':module}):
            before={k:v for k,v in namespace.items()if k!='require_native_render_supervision'}
            operation(self.code,namespace)
            self.assertIs(namespace['require_native_render_supervision'],self.loader._portable_access['helper'])
            self.assertTrue(all(namespace[k]is value for k,value in before.items()))
            receipt=self.loader.portable_access_receipts[-1]
            self.assertIs(receipt['Mac_native_qualification'],False)
            self.assertIs(receipt['scientific_validator_or_source_session_override'],False)
            self.assertIs(receipt['actual_native_helpers_code_equal_original_source'],True)
            self.assertEqual(receipt['canonical_module_name'],namespace['__name__'])

    def test_closed_adapter_accepts_only_two_actual_producer_objects_and_preserves_native_bodies(self):
        for name in ('nightly_manuscript_access','_exact_current_archival_access'):
            with self.subTest(name=name):
                module,namespace=self.namespace(name)
                self.apply(self.loader._apply_portable_access_prerequisite,namespace)
        self.assertEqual(len(self.loader.portable_access_receipts),2)

    def test_adapter_drift_counterfeit_and_arbitrary_callable_hold_before_replacement(self):
        from unittest.mock import patch
        helper=self.loader._portable_access['helper']
        for change in ('unknown_name','ambient_object','wrong_file','native_body','arbitrary_helper','physical_source'):
            with self.subTest(change=change):
                module,namespace=self.namespace();original=namespace['require_native_render_supervision']
                if change=='unknown_name':namespace['__name__']='ambient_access'
                if change=='wrong_file':namespace['__file__']=str(self.path.with_name('other.py'))
                if change=='native_body':namespace['native_render']=lambda *a,**k:None
                if change=='arbitrary_helper':self.loader._portable_access['helper']=lambda:None
                if change=='physical_source':self.path.write_bytes(self.raw+b'\n# changed TEST ONLY source\n')
                published=types.ModuleType('nightly_manuscript_access')if change=='ambient_object'else module
                try:
                    with patch.dict(sys.modules,{'nightly_manuscript_access':published}):
                        with self.assertRaisesRegex(ValueError,'PORTABLE_ACCESS|REGISTERED_SOURCE'):
                            self.loader._apply_portable_access_prerequisite(self.code,namespace)
                    self.assertIs(namespace['require_native_render_supervision'],original)
                finally:
                    self.path.write_bytes(self.raw);self.loader._portable_access['helper']=helper

    def test_actual_adapter_assignment_omission_is_killed_by_same_positive_assertion_oracle(self):
        import closed_data_loader
        import copy
        module,namespace=self.namespace()
        self.apply(self.loader._apply_portable_access_prerequisite,namespace)
        tree=ast.parse(Path(closed_data_loader.__file__).read_bytes())
        klass=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='ClosedDataLoader')
        method=copy.deepcopy(next(n for n in klass.body if isinstance(n,ast.FunctionDef)
            and n.name=='_apply_portable_access_prerequisite'))
        selected=[(i,n)for i,n in enumerate(method.body)if isinstance(n,ast.Assign)
            and len(n.targets)==1 and isinstance(n.targets[0],ast.Subscript)
            and isinstance(n.targets[0].value,ast.Name)and n.targets[0].value.id=='globals'
            and isinstance(n.targets[0].slice,ast.Constant)
            and n.targets[0].slice.value=='require_native_render_supervision']
        self.assertEqual(len(selected),1)
        index,node=selected[0];method.body[index]=ast.copy_location(ast.Pass(),node)
        mutant_tree=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
        defined={};exec(compile(mutant_tree,'<TEST_ONLY_PREREQUISITE_ASSIGNMENT_OMISSION>','exec'),vars(closed_data_loader),defined)
        mutant=types.MethodType(defined[method.name],self.loader)
        module,namespace=self.namespace()
        # ValueError/import/runtime errors propagate as ERROR; only this exact
        # positive assertion oracle's AssertionError is causal kill evidence.
        with self.assertRaises(AssertionError):self.apply(mutant,namespace)
        print('CLOSED_PORTABLE_PREREQUISITE_MUTANT_ASSERTION_KILLED=omit_fixed_assignment')



if __name__ == '__main__':
    unittest.main()
