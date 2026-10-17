"""Cause-specific compiler-cache mutations over isolated fixture-only copies.

Each named mutation must first pass its unmodified target, then fail that exact
unittest assertion with zero errors. An unqualified mutation stops the runner.
Only the tiny registered-source cache tests run; no full source session runs.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

TEST_PREFIX = 'test_closed_data_loader_cache.ClosedDataLoaderCacheTests.'
SOURCE = 'closed_data_loader.py'
COPIED = (SOURCE, 'test_closed_data_loader_cache.py', 'build_source_chain.py')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def method(tree, name):
    classes = [node for node in tree.body
               if isinstance(node, ast.ClassDef) and node.name == 'ClosedDataLoader']
    if len(classes) != 1:
        raise ValueError('UNIQUE_CLOSED_LOADER_CLASS_REQUIRED')
    found = [node for node in classes[0].body
             if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(found) != 1:
        raise ValueError('UNIQUE_MUTATION_METHOD_REQUIRED:' + name)
    return found[0]


def memoize_return(tree, name, attr):
    """A bad mutable/result memo, deliberately confined to a mutant source."""
    node = method(tree, name)
    if not node.args.args or node.args.args[0].arg != 'self':
        raise ValueError('INSTANCE_MUTATION_METHOD_REQUIRED:' + name)
    changed = 0
    class Returns(ast.NodeTransformer):
        def visit_Return(self, statement):
            nonlocal changed
            if statement.value is None:
                return statement
            changed += 1
            return [ast.Assign(targets=[ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()),
                                                      attr=attr, ctx=ast.Store())],
                               value=statement.value),
                    ast.Return(value=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()),
                                                   attr=attr, ctx=ast.Load()))]
    node.body = [item for statement in node.body
                 for item in ((lambda v: v if isinstance(v, list) else [v])
                              (Returns().visit(statement)))]
    if not changed:
        raise ValueError('MUTATION_RETURN_ANCHOR_REQUIRED:' + name)
    node.body[:0] = ast.parse(
        'if hasattr(self, %r):\n    return self.%s\n' % (attr, attr)).body


def mutable_proof(tree):
    node = method(tree, '_decode_proof')
    changed = 0
    class Returns(ast.NodeTransformer):
        def visit_Return(self, statement):
            nonlocal changed
            if statement.value is None:
                return statement
            changed += 1
            return [ast.Assign(targets=[ast.Name(id='_MUTANT_REPLAY_PROOF', ctx=ast.Store())],
                               value=statement.value),
                    ast.Return(value=ast.Name(id='_MUTANT_REPLAY_PROOF', ctx=ast.Load()))]
    node.body = [item for statement in node.body
                 for item in ((lambda v: v if isinstance(v, list) else [v])
                              (Returns().visit(statement)))]
    if not changed:
        raise ValueError('MUTATION_PROOF_RETURN_REQUIRED')
    node.body[:0] = ast.parse('global _MUTANT_REPLAY_PROOF\n'
                              'try:\n    return _MUTANT_REPLAY_PROOF\n'
                              'except NameError:\n    pass\n').body


def stale_exec_globals(tree):
    node = method(tree, 'execute')
    node.body[:0] = ast.parse(
        'if hasattr(self, "_mutant_executed_globals"):\n'
        '    globals.update(self._mutant_executed_globals)\n'
        '    return None\n'
        'self._mutant_executed_globals = globals\n').body


def clear_noop(tree):
    method(tree, 'clear_code_cache').body = [ast.Return(value=ast.Constant(value=None))]


def omit_key_fields(tree, fields):
    node = method(tree, '_derivation_key')
    returns = [statement for statement in node.body if isinstance(statement, ast.Return)]
    if len(returns) != 1 or not isinstance(returns[0].value, ast.Tuple):
        raise ValueError('UNIQUE_DERIVATION_KEY_TUPLE_REQUIRED')
    items = returns[0].value.elts
    matched = [item for item in items if ast.unparse(item) in fields]
    if len(matched) != len(fields):
        raise ValueError('EXACT_DERIVATION_KEY_FIELDS_REQUIRED:' + repr(fields))
    returns[0].value.elts = [item for item in items if ast.unparse(item) not in fields]


def omit_key_state_member(tree, field):
    node = method(tree, '_derivation_key'); changed = 0
    class State(ast.NodeTransformer):
        def visit_Subscript(self, expression):
            nonlocal changed
            if ast.unparse(expression) == "captured['state_raw']":
                changed += 1
                return ast.parse('self._encoded_state({key: value for key, value '
                                 'in captured["state"].items() if key != %r})' % field,
                                 mode='eval').body
            return self.generic_visit(expression)
    State().visit(node)
    if changed != 1:
        raise ValueError('UNIQUE_DERIVATION_STATE_FIELD_REQUIRED')


def skip_post_capture(tree):
    method(tree, '_check_capture').body = [ast.Return(value=ast.Constant(value=None))]


def admit_unknown_kwargs(tree):
    node = method(tree, '_cache_eligible'); changed = 0
    class Eligibility(ast.NodeTransformer):
        def visit_UnaryOp(self, expression):
            nonlocal changed
            if (isinstance(expression.op, ast.Not) and isinstance(expression.operand, ast.Name)
                    and expression.operand.id == 'kwargs'):
                changed += 1
                return ast.Constant(value=True)
            return self.generic_visit(expression)
    Eligibility().visit(node)
    if changed != 1:
        raise ValueError('UNIQUE_UNKNOWN_KWARGS_EXCLUSION_REQUIRED')


def omit_entry_bound(tree):
    node = method(tree, '_cache_put'); loops = [n for n in ast.walk(node) if isinstance(n, ast.While)]
    if len(loops) != 1:
        raise ValueError('UNIQUE_CACHE_EVICTION_LOOP_REQUIRED')
    loops[0].test = ast.Constant(value=False)


def omit_byte_bound(tree):
    node = method(tree, '_cache_put'); changed = 0
    class Bytes(ast.NodeTransformer):
        def visit_Attribute(self, expression):
            nonlocal changed
            if (isinstance(expression.value, ast.Name) and expression.value.id == 'self'
                    and expression.attr == 'CACHE_MAX_BYTES'):
                changed += 1
                return ast.Constant(value=10 ** 50)
            return self.generic_visit(expression)
    Bytes().visit(node)
    if changed != 3:
        raise ValueError('EXACT_THREE_CACHE_BYTE_BOUNDS_REQUIRED')


def skip_baseline_guard(tree):
    node = method(tree, '_source_guard'); changed = 0
    for statement in node.body:
        if (isinstance(statement, ast.If) and isinstance(statement.test, ast.Compare)
                and isinstance(statement.test.left, ast.Name)
                and statement.test.left.id == 'baseline'):
            changed += 1
            statement.test = ast.Constant(value=False)
    if changed != 1:
        raise ValueError('UNIQUE_BASELINE_METADATA_GUARD_REQUIRED')


def omit_exec_counter(tree):
    node = method(tree, 'execute'); changed = 0
    for statement in node.body:
        if (isinstance(statement, ast.AugAssign)
                and ast.unparse(statement.target) == "self._compiler_stats['actual_exec_calls']"):
            changed += 1
            statement.value = ast.Constant(value=0)
    if changed != 1:
        raise ValueError('UNIQUE_ACTUAL_EXEC_COUNTER_REQUIRED')


def skip_post_data(tree):
    node = method(tree, 'execute'); changed = 0
    class Updates(ast.NodeTransformer):
        def visit_Expr(self, statement):
            nonlocal changed
            call = statement.value
            if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == 'globals' and call.func.attr == 'update'
                    and len(call.args) == 1 and isinstance(call.args[0], ast.Name)
                    and call.args[0].id == 'data'):
                changed += 1
                return ast.Pass()
            return self.generic_visit(statement)
    Updates().visit(node)
    if changed != 1:
        raise ValueError('UNIQUE_POST_LOAD_DATA_UPDATE_REQUIRED')


MUTANTS = (
    ('cached_source_guard_skips_fresh_physical_checks',
     lambda tree: memoize_return(tree, '_source_guard', '_mutant_source_capture'),
     'test_warm_hit_rechecks_missing_and_changed_physical_source'),
    ('mutable_cached_proof_aliases_prior_receipts', mutable_proof,
     'test_cached_serialized_proof_is_rehydrated_without_mutable_aliases'),
    ('cached_module_globals_skip_fresh_execution', stale_exec_globals,
     'test_reuses_code_but_runs_fresh_globals_and_per_call_source_proof'),
    ('post_load_data_is_not_reapplied', skip_post_data,
     'test_post_load_platform_data_applies_on_each_fresh_execution'),
    ('cache_clear_retains_derivations', clear_noop,
     'test_clear_removes_only_derivations_and_preserves_future_execution'),
    ('data_remap_omitted_from_derivation_key',
     lambda tree: omit_key_state_member(tree, 'remaps'),
     'test_data_remap_change_is_rederived_and_never_reuses_old_values'),
    ('allowlist_omitted_from_derivation_key',
     lambda tree: omit_key_state_member(tree, 'allowlist'),
     'test_allowlist_changes_rederive_and_revocation_holds_on_warm_cache'),
    ('registered_paths_omitted_from_derivation_key',
     lambda tree: omit_key_state_member(tree, 'registered_paths'),
     'test_registered_same_raw_alias_rederives_full_registered_path_proof'),
    ('requested_filename_omitted_from_derivation_key',
     lambda tree: omit_key_fields(tree, {"captured['requested']"}),
     'test_exact_requested_filename_spelling_is_part_of_compiler_key'),
    ('optimization_omitted_from_derivation_key',
     lambda tree: omit_key_fields(tree, {'optimize'}),
     'test_compiler_flags_inheritance_and_optimization_have_distinct_keys'),
    ('flags_and_inheritance_omitted_from_derivation_key',
     lambda tree: omit_key_fields(tree, {'flags', 'dont_inherit', 'flags | inherited'}),
     'test_compiler_flags_inheritance_and_optimization_have_distinct_keys'),
    ('unknown_compile_kwargs_wrongly_cacheable', admit_unknown_kwargs,
     'test_unknown_kwargs_and_ast_returning_compile_are_uncached'),
    ('cache_entry_eviction_bound_removed', omit_entry_bound,
     'test_cache_bounds_evict_old_code_and_account_serialized_bytes'),
    ('cache_serialized_byte_bound_removed', omit_byte_bound,
     'test_byte_limit_does_not_retain_oversize_code_or_proof'),
    ('post_derivation_physical_compare_and_swap_removed', skip_post_capture,
     'test_post_compile_source_race_holds_before_cache_or_proof_commit'),
    ('post_derivation_data_compare_and_swap_removed', skip_post_capture,
     'test_post_compile_data_race_holds_before_cache_or_proof_commit'),
    ('registered_baseline_guard_removed', skip_baseline_guard,
     'test_baseline_and_registration_metadata_corruption_cannot_be_cached'),
    ('compiler_callable_identity_omitted_from_derivation_key',
     lambda tree: omit_key_fields(tree, {'(id(compiler), compiler)'}),
     'test_replacing_compiler_callable_requires_new_pure_derivation'),
    ('actual_exec_attempt_counter_not_incremented', omit_exec_counter,
     'test_exec_attempts_failures_and_successes_are_separate_counters'),
)


def mutate(raw, operation):
    tree = ast.parse(raw)
    operation(tree)
    result = (ast.unparse(ast.fix_missing_locations(tree)) + '\n').encode()
    compile(result, '<isolated-fixture-mutant>', 'exec')
    return result


def run(tests, output, interpreter):
    output.mkdir(parents=True, exist_ok=False)
    captured = {name: (tests / name).read_bytes() for name in COPIED}
    root = next(parent for parent in tests.parents
                if (parent / '00_lab_infrastructure/gates/standalone_pdf_release/runtime/packaging_runtime.py').is_file())
    env = dict(os.environ, VRS_W42_PUBLIC_TEST_REPO=str(root))
    for name in ('PYTHONPATH', 'PYTHONHOME', 'PYTHONPYCACHEPREFIX'):
        env.pop(name, None)
    results = []
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='w42-cache-causal-') as folder:
        copied = Path(folder).resolve()
        for name, raw in captured.items():
            (copied / name).write_bytes(raw)

        def execute(label, test):
            command = [interpreter, '-B', '-m', 'unittest', TEST_PREFIX + test]
            start = time.monotonic()
            result = subprocess.run(command, cwd=copied, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=540)
            stdout = output / (label + '.stdout.txt'); stdout.write_bytes(result.stdout)
            stderr = output / (label + '.stderr.txt'); stderr.write_bytes(result.stderr)
            diagnostic = result.stderr.decode('utf-8', errors='replace')
            failures = re.findall(r'^FAIL: (\S+)', diagnostic, re.M)
            errors = re.findall(r'^ERROR: (\S+)', diagnostic, re.M)
            return {'label': label, 'named_test': TEST_PREFIX + test, 'command': command,
                    'returncode': result.returncode, 'seconds': time.monotonic() - start,
                    'assertion_failures': len(failures), 'errors': len(errors),
                    'named_assertion_failure': bool(failures) and set(failures) == {test},
                    'exact_one_test': bool(re.search(r'Ran 1 test\b', diagnostic)),
                    'stdout': {'path': str(stdout), 'sha256': sha(result.stdout)},
                    'stderr': {'path': str(stderr), 'sha256': sha(result.stderr)}}

        for name, operation, test in MUTANTS:
            baseline = execute(name + '.baseline', test)
            mutated = mutate(captured[SOURCE], operation)
            (copied / SOURCE).write_bytes(mutated)
            try:
                mutant = execute(name + '.mutant', test)
            finally:
                (copied / SOURCE).write_bytes(captured[SOURCE])
            qualified = (baseline['returncode'] == 0 and baseline['assertion_failures'] == 0
                         and baseline['errors'] == 0 and baseline['exact_one_test']
                         and mutant['returncode'] == 1 and mutant['assertion_failures'] > 0
                         and mutant['named_assertion_failure'] and mutant['errors'] == 0
                         and mutant['exact_one_test'])
            results.append({'name': name, 'source_file': SOURCE,
                            'before_sha256': sha(captured[SOURCE]),
                            'mutant_sha256': sha(mutated), 'target': TEST_PREFIX + test,
                            'baseline': baseline, 'mutant': mutant,
                            'qualified_assertion_kill': qualified})
            if not qualified:
                break
    if any((tests / name).read_bytes() != raw for name, raw in captured.items()):
        raise ValueError('SOURCE_CAPTURE_DRIFT')
    report = {'standard': 'VRS-W42-FIXTURE-COMPILER-CACHE-CAUSAL-REPLAY-1',
              'interpreter': interpreter, 'seconds': time.monotonic() - started,
              'source_hashes': {name: sha(raw) for name, raw in captured.items()},
              'mutants': results, 'required_count': len(MUTANTS), 'count': len(results),
              'qualified_assertion_kills': sum(row['qualified_assertion_kill'] for row in results),
              'full_source_session_executed': False, 'core_execution': 0,
              'science_or_source_admission_claim': False, 'stops_at_first_unqualified_result': True}
    path = output / 'CACHE_CAUSAL.json'
    path.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'path': str(path), 'sha256': sha(path.read_bytes()),
                      'count': report['count'], 'required_count': report['required_count'],
                      'qualified_assertion_kills': report['qualified_assertion_kills']}))
    return 0 if report['qualified_assertion_kills'] == len(MUTANTS) else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--python', required=True)
    args = parser.parse_args()
    raise SystemExit(run(Path(__file__).resolve().parent, args.output.resolve(), args.python))
