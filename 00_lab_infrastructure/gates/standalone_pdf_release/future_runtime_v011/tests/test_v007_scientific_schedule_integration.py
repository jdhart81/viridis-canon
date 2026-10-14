"""One-use schedule through original folds, using synthetic science only.

The original source is parsed to select its unchanged fold/label/comparator
functions. No original module, scientific predicate, proof, network transport,
canonical source, or production entry is imported or executed by this fixture.
"""
import ast
import contextlib
from copy import deepcopy
import datetime as dt
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
GATES = HERE.parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime
import packaging_catalog as catalog
import manuscript_access_registry as registry
import scientific_registration_worker as science

SIZES = (7, 10, 10, 10, 10, 9, 2)
REGISTRAR_SHA = 'e97c6e906b6b2feeb348fc60dc0f4c22eac86cb23eac6f29afbf33dfe9df3cb5'
POPULATION_SHA = 'b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'


class SyntheticOriginalHold(ValueError):
    pass


def original_controls():
    """Only selected pure control functions; all scientific calls injected."""
    path = GATES / 'methods_digest_registration.py'
    body = path.read_bytes()
    assert runtime.sha(body) == REGISTRAR_SHA
    names = {'entity_rows', 'preserve', '_public_label_read_record_pre_prior_processing',
             'public_label_read_record'}
    nodes = [n for n in ast.parse(body).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes} == names
    denied = lambda *a, **k: (_ for _ in ()).throw(AssertionError('original science/network called'))
    env = {'Path': Path, 'deepcopy': deepcopy, 'dt': dt,
           'GROUP_ROUTE': 'METHODS_DIGEST_GROUP_V1', 'NOTE_ROUTE': 'METHODS_DIGEST_NOTE_V1',
           'RegistrationHold': SyntheticOriginalHold, 'require_registration': denied,
           '_get_record': denied, 'd': SimpleNamespace(raw_json=science.raw)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return SimpleNamespace(__name__='synthetic_original_registration',
                           RegistrationHold=SyntheticOriginalHold, **{n: env[n] for n in names})


def original_population():
    path = GATES / ('production_snapshots/phase7-20261009-prior-content-runtime-successor/'
                    'after/production_execution_dependencies/runtime_successor.py')
    body = path.read_bytes()
    assert runtime.sha(body) == POPULATION_SHA
    names = {'exact', 'preserving_population'}
    nodes = [n for n in ast.parse(body).body
             if isinstance(n, ast.FunctionDef) and n.name in names]
    env = {'re': re, 'encoded': science.raw, 'need': runtime.need}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), env)
    return env['preserving_population']


class ScientificScheduleIntegration(unittest.TestCase):
    def fixture(self, root):
        output = root / 'reports/verification-coverage/synthetic-owner'
        output.mkdir(parents=True)
        ordinary = [{'id': f'ordinary:{i}', 'path': f'ordinary/{i}',
                     'publication_registration_status': 'PASS', 'enforcement_acceptable': True}
                    for i in range(27)]
        scanner = {'tree_root': str(root), 'run_entities': [
            {'id': 'Run-001', 'status': 'CERTIFIED', 'certificate_valid': True,
             'path': 'run/001', 'certificate': 'cert/001'},
            {'id': 'Run-002', 'status': 'CERTIFIED', 'certificate_valid': True,
             'path': 'run/002', 'certificate': 'cert/002'}], 'file_entities': [],
            'unknown_scanner_field': {'ordered': ['second', 'first']},
            'publication_entities': deepcopy(ordinary), 'publication_holds': [],
            'enforcement_activation': {'path': 'activation.json', 'sha256': '1'*64},
            'premise_declaration_cutover_run': 'Run-188'}
        original = original_controls()
        receipts = {}; entries = []; all_rows = deepcopy(ordinary)
        for ordinal, count in enumerate(SIZES):
            bound = {'path': f'registration-{ordinal}.json', 'sha256': f'{ordinal+2:x}'*64}
            children = []
            for note in range(count):
                cert = root / f'certificates/group-{ordinal}-note-{note}.json'
                cert.parent.mkdir(exist_ok=True); cert.write_bytes(b'exact synthetic certificate DATA')
                children.append({'id': f'note:{ordinal}:{note}', 'path': f'notes/{ordinal}/{note}',
                    'run_id': f'Run-{ordinal*10+note+1:03d}',
                    'certificate': {'path': str(cert), 'sha256': runtime.sha(cert.read_bytes())},
                    'publication_binding': {'path': f'note-binding-{ordinal}-{note}', 'sha256': 'a'*64}})
            receipt = {'record_id': str(24000000+ordinal), 'doi': f'10.5281/zenodo.{24000000+ordinal}',
                       'release_week': f'2026-W40-{ordinal}', 'package_path': f'digests/{ordinal}',
                       'children': children}
            material = {'receipt': receipt}
            receipts[science.raw(bound)] = material
            all_rows.extend(original.entity_rows(root, bound, scanner,
                            consume=lambda *a, value=material, **k: deepcopy(value)))
            entries.append({'registration': bound, 'archive': {'synthetic': 'present'}, 'prior_chain': None})
        previous = {**deepcopy(scanner), 'publication_entities': all_rows}
        ctx = registry.RegistryContext.__new__(registry.RegistryContext)
        ctx.root = root; ctx.deadline_guard = None
        ctx.scientific_consumer = None; ctx.scientific_batch = None
        ctx._registry = lambda: ({'entries': deepcopy(entries)}, b'synthetic registry DATA')
        data = catalog.ScientificInputData(root, ctx)
        data.scan_data = deepcopy(scanner)
        rows = [{'name': name, 'path': str(root/name), 'sha256': 'b'*64}
                for name in sorted(runtime.MODULE_NAMES)]
        with patch.object(science, 'source_rows', return_value=rows):
            batch = science.ScienceBatch(root, {'path': 'profile.json', 'sha256': 'c'*64},
                                        ctx, previous, scanner, output)
        observed = []

        def execute(planned):
            for config, config_bound in planned:
                observed.append((deepcopy(config), deepcopy(config_bound)))
                material = deepcopy(receipts[science.raw(config['binding'])])
                result = {'outcome': 'SCIENCE_RESULT', 'original_result': material, 'original_hold': None,
                    'config': deepcopy(config_bound),
                    'completed_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                    'completed_monotonic': science.time.monotonic()}
                path = output / (config['stage']+'-'+str(config['ordinal'])+'-synthetic-result.json')
                path.write_bytes(science.raw(result))
                key = batch._key(config['stage'], config['binding'])
                batch.jobs[key] = {'config': deepcopy(config), 'binding': science.binding(path),
                    'manifest': {'path': 'separate-union-tests', 'sha256': 'd'*64},
                    'pid': 1000+len(observed), 'exit_code': 0}

        stack = contextlib.ExitStack()
        stack.enter_context(patch.object(science, 'source_rows', return_value=rows))
        stack.enter_context(patch.object(catalog, 'scientific_data', return_value=data))
        stack.enter_context(patch.object(runtime, 'build_worker_source_manifest',
                                        return_value={'synthetic': 'separate source tests'}))
        stack.enter_context(patch.object(science, 'evaluation_state',
                                        return_value={'synthetic': 'separate dependency tests'}))
        stack.enter_context(patch.object(batch, '_execute', side_effect=execute))
        fresh = stack.enter_context(patch.object(batch, '_fresh_union'))
        stack.enter_context(patch.object(registry.registration, '_original_registrar', return_value=original))
        stack.enter_context(patch.object(registry.registration, 'is_v3_binding', return_value=False))
        return stack, scanner, previous, entries, ctx, data, batch, observed, original, fresh

    def test_real_prepare_emits_exact_35_distinct_stage_configs_and_label_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
            with stack:
                batch.prepare()
                self.assertEqual(len(planned), 35)
                self.assertEqual(len({c['job_nonce'] for c, _ in planned}), 35)
                self.assertEqual({c['operation'] for c, _ in planned}, {batch.operation})
                for stage in science.STAGES:
                    jobs = [c for c, _ in planned if c['stage'] == stage]
                    self.assertEqual([c['ordinal'] for c in jobs], list(range(7)))
                    self.assertEqual([c['binding'] for c in jobs], [e['registration'] for e in entries])
                    self.assertTrue(all(c['evaluation_kwargs'] == {'views': None, 'prior_chain_receipts': None}
                                        for c in jobs))
                    if stage.startswith('labels_'):
                        self.assertTrue(all(c['ledger'] is None and c['ledger_sha256'] is None for c in jobs))
                    else:
                        self.assertTrue(all(runtime.object_at(root, c['ledger'])[2] == scanner for c in jobs))
                self.assertEqual(fresh.call_count, 1)
                self.assertIs(ctx.scientific_batch, batch)
                self.assertEqual(len(previous['publication_entities']), 92)

    def test_master_original_fold_full92_labels_two_saved_calls_and_all35_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
            pair_calls = []
            legacy = {'metadata': {'title': 'Synthetic title', 'description': 'Synthetic text'}, 'files': []}
            native = {'synthetic': 'actual local observation'}
            ctx.owner_getter = lambda rid, accept: (pair_calls.append((rid, accept)) or
                              deepcopy(legacy if accept == registry.CONTEXT['legacy_accept'] else native))

            def consume(root_, bound, ledger=None, *, views=None, **kwargs):
                value = ctx._scientific_registration(bound, ledger, views=None)
                if views is not None:
                    value.update(public_legacy=deepcopy(views[0]), public_native=deepcopy(views[1]),
                                 prior_processing_audit={'synthetic': 'no actual admission'})
                return value
            ctx.require_registration = consume
            with stack:
                batch.prepare()
                for stage in ('build', 'activation_current_preserve'):
                    with batch.stage(stage):
                        current = original.preserve(deepcopy(scanner), previous,
                            legacy=lambda ledger, old: {**deepcopy(ledger),
                                'publication_entities': deepcopy(old['publication_entities'])}, consume=consume)
                    self.assertEqual(current['publication_entities'], previous['publication_entities'])
                compare = original_population()
                self.assertEqual(compare(previous, previous['publication_entities'][:35], current),
                                 previous['publication_entities'])
                with batch.stage('doi'):
                    for entry in entries: consume(root, entry['registration'], current, views=None)
                for entry in entries:
                    receipt = next(c['original_result']['receipt'] for c in
                        (runtime.object_at(root, slot['binding'])[2] for slot in batch.jobs.values())
                        if c['original_result']['receipt']['record_id'] ==
                        str(24000000+entries.index(entry)))
                    row = {'doi': receipt['doi'], 'deposit_paths': [str(root/receipt['package_path'])],
                           'methods_digest_registration': {'tree_root': str(root), 'receipt': entry['registration']}}
                    label = ctx.public_label_read_record(row, legacy=lambda row: self.fail('generic bypass'))
                    self.assertEqual(label['status'], 'READ')
                self.assertEqual(len(pair_calls), 14)
                self.assertEqual(len(batch.used), 35)
                self.assertEqual(fresh.call_count, 36)
                consumed = [runtime.object_at(root, bound)[2]
                            for bound in batch.summary()['consumptions']]
                self.assertEqual(len(consumed), 35)
                self.assertEqual(len({row['job_nonce'] for row in consumed}), 35)
                for row in consumed:
                    self.assertEqual(row['status'], 'ACTUAL_LIVE_ORIGINAL_FUNCTION_DATA_CONSUMED_NOT_NEW_AUTHORITY')
                    self.assertEqual(row['evaluation_kwargs'], {'views': None, 'prior_chain_receipts': None})
                    self.assertTrue(row['all_other_whole_argument_fields_equal'])
                    self.assertIs(row['certifies'], False)
                    worker = None if row['worker_whole_argument'] is None else runtime.object_at(root, row['worker_whole_argument'])[2]
                    master = None if row['master_whole_argument'] is None else runtime.object_at(root, row['master_whole_argument'])[2]
                    self.assertEqual(science.argument_projection(worker), science.argument_projection(master))
                    actual_fields = [] if master is None else [field for field in sorted(science.PUB_FIELDS)
                        if (field in master) != (field in worker) or master.get(field) != worker.get(field)]
                    self.assertEqual([diff['field'] for diff in row['allowed_publication_differences']], actual_fields)
                    for diff in row['allowed_publication_differences']:
                        field = diff['field']
                        self.assertEqual(diff['worker_present'], field in worker)
                        self.assertEqual(diff['master_present'], field in master)
                        self.assertEqual(diff['worker_value_sha256'], None if field not in worker else runtime.sha(science.raw(worker[field])))
                        self.assertEqual(diff['master_value_sha256'], None if field not in master else runtime.sha(science.raw(master[field])))
                for stage in ('build', 'activation_current_preserve'):
                    ledgers = [runtime.object_at(root, row['master_whole_argument'])[2]
                               for row in consumed if row['stage'] == stage]
                    self.assertEqual([len(v['publication_entities']) for v in ledgers], [27, 35, 46, 57, 68, 79, 89])
                self.assertEqual(sum(row['master_whole_argument'] is None for row in consumed), 14)
                batch.close(complete=True)
                self.assertTrue(batch.closed)
                self.assertIsNone(ctx.scientific_consumer)

    def test_genuine_typed_hold_preserves_all92_and_comparator_rejects(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
            with stack:
                batch.prepare()
                key = batch._key('build', entries[3]['registration'])
                slot = batch.jobs[key]; path = Path(slot['binding']['path'])
                value = json.loads(path.read_bytes())
                value.update(outcome='SCIENTIFIC_HOLD', original_result=None,
                    original_hold={'module': original.__name__, 'class': 'RegistrationHold',
                                   'message': 'actual synthetic current certificate debt'})
                path.write_bytes(science.raw(value)); slot['binding'] = science.binding(path)
                # Exact source/class reconstruction has the owner's separate
                # closed-definition tests. This fixture delivers the typed
                # synthetic exception into the unchanged original fold.
                with patch.object(science, 'resolved_hold',
                        side_effect=lambda root_, hold: original.RegistrationHold(hold['message'])), batch.stage('build'):
                    current = original.preserve(deepcopy(scanner), previous,
                        legacy=lambda ledger, old: {**deepcopy(ledger),
                            'publication_entities': deepcopy(old['publication_entities'])},
                        consume=lambda root_, bound, ledger: ctx._scientific_registration(bound, ledger, views=None))
                self.assertEqual(len(current['publication_entities']), 92)
                self.assertEqual({r['id'] for r in current['publication_entities']},
                                 {r['id'] for r in previous['publication_entities']})
                held = [r for r in current['publication_entities'] if r['enforcement_acceptable'] is False]
                self.assertEqual(len(held), 11)
                self.assertTrue(all(r['status'] == 'DEBT' and 'certificate debt' in r['reasons'][0] for r in held))
                with self.assertRaisesRegex(runtime.PackagingHold, 'FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY'):
                    original_population()(previous, previous['publication_entities'][:35], current)
                self.assertEqual(len(batch.used), 7)
                batch.close(complete=False)
                self.assertEqual(len(batch.jobs)-len(batch.used), 28)
                with self.assertRaises(runtime.PackagingHold):
                    with batch.stage('doi'): pass

    def test_original_comparator_rejects_missing_child_reorder_and_unknown_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, *_ = self.fixture(root)
            stack.close(); compare = original_population()
            for change in ('missing', 'reordered', 'unknown'):
                with self.subTest(change=change):
                    current = deepcopy(previous)
                    if change == 'missing': current['publication_entities'].pop()
                    elif change == 'reordered': current['publication_entities'][-2:] = reversed(current['publication_entities'][-2:])
                    else: current['publication_entities'][-1]['unknown_science_field'] = 'changed'
                    with self.assertRaisesRegex(runtime.PackagingHold, 'FRESH_COMPLETE_DEFAULT_REGISTRATION_REPLAY'):
                        compare(previous, previous['publication_entities'][:35], current)

    def test_missing_group_or_actual_cas_cannot_prepare_or_dispatch(self):
        for cause in ('group', 'cas'):
            with self.subTest(cause=cause), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
                if cause == 'group': batch.previous['publication_entities'].pop(27)
                else: data.cas_events.append({'actual': 'canonical effect'})
                with stack, self.assertRaises(runtime.PackagingHold): batch.prepare()
                self.assertEqual(planned, [])
                self.assertFalse(batch.output.exists())
                self.assertIsNone(ctx.scientific_consumer)

    def test_incomplete_execution_never_installs_a_reusable_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
            with stack, patch.object(batch, '_execute', side_effect=runtime.PackagingHold('actual child abnormal')):
                with self.assertRaisesRegex(runtime.PackagingHold, 'actual child abnormal'): batch.prepare()
                self.assertFalse(batch.prepared)
                self.assertIsNone(ctx.scientific_consumer)
                self.assertIsNone(ctx.scientific_batch)
                self.assertEqual(batch.used, set())

    def test_unknown_or_current_run_drift_rejects_before_consumption_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            stack, scanner, previous, entries, ctx, data, batch, planned, original, fresh = self.fixture(root)
            with stack:
                batch.prepare()
                for change in ('unknown', 'debt', 'run_order'):
                    with self.subTest(change=change):
                        ledger = deepcopy(scanner)
                        if change == 'unknown': ledger['additional_unknown'] = 'cannot ignore'
                        elif change == 'debt': ledger['run_entities'][0]['status'] = 'DEBT'
                        else: ledger['run_entities'].reverse()
                        with batch.stage('build'), self.assertRaisesRegex(runtime.PackagingHold, 'NONPUBLICATION_WHOLE_ARGUMENT'):
                            ctx._scientific_registration(entries[0]['registration'], ledger, views=None)
                self.assertEqual(batch.used, set())
                self.assertEqual(batch.summary()['consumptions'], [])
                self.assertEqual(list(batch.output.glob('*CONSUMPTION*')), [])
                # Only the initial completed preparation guard ran.
                self.assertEqual(fresh.call_count, 1)


if __name__ == '__main__':
    unittest.main()
