import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

import nightly_coverage
import run_flow
from test_activation_guard import ActivationFixture


class GenuineNightlyWindowsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.now = dt.datetime(2026, 10, 11, 12, tzinfo=dt.timezone.utc)
        self.reports = []
        self.activation_fixture = ActivationFixture(self, self.root)

    def receipt(self, day, suffix='a', clean=True):
        timezone = ZoneInfo('America/New_York')
        date = dt.date.fromisoformat(day)
        lower = dt.datetime.combine(date, dt.time(1), timezone)
        upper = dt.datetime.combine(date + dt.timedelta(days=1), dt.time(1), timezone)
        invocation = day + '-' + suffix
        directory = self.root / 'RESEARCH_PIPELINE_v2/nightly_checkpoints' / invocation
        directory.mkdir(parents=True)
        start = {'standard': 'VRS-NIGHTLY-CHECKPOINT-1', 'invocation_id': invocation,
                 'started_at_utc': (lower + dt.timedelta(minutes=1)).isoformat()}
        sp = directory / 'START.json'; sp.write_text(json.dumps(start))
        finish = {'standard': start['standard'], 'invocation_id': invocation,
                  'started_at_utc': start['started_at_utc'],
                  'completed_at_utc': (lower + dt.timedelta(hours=1)).isoformat(),
                  'start_receipt_sha256': nightly_coverage.binding(sp)['sha256'],
                  'status': 'NIGHTLY_PROGRESS_PASS' if clean else 'HOLD_NIGHTLY_PROGRESS',
                  'incidents': [] if clean else ['HOLD_PACKAGE'],
                  'generation': {'latest_run': 'Run-188', 'generated_at_utc': (lower + dt.timedelta(minutes=5)).isoformat(),
                                 'window': {'standard': 'VRS-NIGHTLY-WINDOW-1', 'window_id': day,
                                            'timezone': 'America/New_York', 'satisfied': True,
                                            'starts_at_utc': lower.isoformat(), 'ends_at_utc': upper.isoformat()}}}
        fp = directory / 'FINISH.json'; fp.write_text(json.dumps(finish))
        report = {'mode': 'ENFORCING', 'enforcement': True,
                  'observed_at_utc': (lower + dt.timedelta(hours=2)).isoformat(),
                  'status': 'ENFORCING_PASS' if clean else 'HOLD', 'checkpoint': nightly_coverage.binding(fp),
                  'coverage': {'errors': [], 'mirror_drift': [], 'receipt_era': {'total': 71, 'certified': 71}},
                  'new_artifact_publication_gate': {'status': 'PASS', 'exact_publication_binding': True,
                                                   'claim_gate': {'status': 'PASS'}}}
        self.activation_fixture.attach(report, day)
        rp = self.root / 'reports/verification-coverage' / invocation / 'NIGHTLY_CYCLE_REPORT.json'
        rp.parent.mkdir(parents=True); rp.write_text(json.dumps(report)); self.reports.append(rp)
        return rp, fp, sp

    def collect(self):
        return nightly_coverage.collect_streak(self.root, self.reports, now=self.now)

    def change(self, path, update):
        obj = json.loads(path.read_text()); update(obj); path.write_text(json.dumps(obj))

    def test_seven_distinct_real_closed_windows_pass(self):
        for day in range(4, 11): self.receipt(f'2026-10-{day:02}')
        result = self.collect()
        self.assertEqual(result['consecutive_clean_closed_windows'], 7)
        self.assertEqual(result['status'], 'SEVEN_CLEAN_NIGHTLY_WINDOWS')

    def test_repeated_same_day_and_same_receipt_count_once(self):
        for i in range(8): self.receipt('2026-10-10', str(i))
        self.reports += self.reports
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 1)

    def test_current_open_window_cannot_count(self):
        self.receipt('2026-10-11')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_missing_latest_window_prevents_stale_streak(self):
        for day in range(3, 10): self.receipt(f'2026-10-{day:02}')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_any_hold_within_window_breaks_streak(self):
        self.receipt('2026-10-10'); self.receipt('2026-10-10', 'later', clean=False)
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_missing_day_breaks_continuity(self):
        for day in (6, 7, 9, 10): self.receipt(f'2026-10-{day:02}')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 2)

    def test_report_only_does_not_count(self):
        rp, _, _ = self.receipt('2026-10-10')
        self.change(rp, lambda d: d.update(mode='REPORT_ONLY', enforcement=False))
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_current_binding_and_claim_gate_mandatory(self):
        rp, _, _ = self.receipt('2026-10-10')
        for bad in ({'status': 'PASS', 'exact_publication_binding': False, 'claim_gate': {'status': 'PASS'}},
                    {'status': 'PASS', 'exact_publication_binding': True, 'claim_gate': {'status': 'HOLD'}}, {}):
            self.change(rp, lambda d: d.update(new_artifact_publication_gate=bad))
            self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_checkpoint_mutation_rejected(self):
        _, fp, _ = self.receipt('2026-10-10')
        fp.write_text(fp.read_text() + ' ')
        result = self.collect()
        self.assertEqual(result['consecutive_clean_closed_windows'], 0)
        self.assertIn('checkpoint hash mismatch', result['rejected'][0]['cause'])

    def test_original_start_mutation_rejected(self):
        _, _, sp = self.receipt('2026-10-10')
        sp.write_text(sp.read_text() + ' ')
        self.assertIn('FINISH does not bind START', self.collect()['rejected'][0]['cause'])

    def test_future_observation_rejected(self):
        rp, _, _ = self.receipt('2026-10-10')
        self.change(rp, lambda d: d.update(observed_at_utc='2026-10-12T12:00:00+00:00'))
        self.assertTrue(self.collect()['rejected'])

    def test_dst_window_is_calendar_day_not_fixed_24_hours(self):
        self.now = dt.datetime(2026, 11, 2, 12, tzinfo=dt.timezone.utc)
        self.receipt('2026-11-01')
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 1)

    def test_drift_or_missing_coverage_cannot_pass(self):
        rp, _, _ = self.receipt('2026-10-10')
        self.change(rp, lambda d: d['coverage'].update(mirror_drift=['Run-102']))
        self.assertEqual(self.collect()['consecutive_clean_closed_windows'], 0)

    def test_weekly_snapshot_is_immutable_and_hash_checked(self):
        ledger = {'file_counts': {}, 'run_counts': {}, 'receipt_era': {'total': 71}, 'mirror_drift': [], 'errors': []}
        with patch('corpus_ledger.render_markdown', return_value='Ledger'):
            original = nightly_coverage.weekly_report(self.root, ledger, {'sha256': 'first'}, now=self.now)
            changed = copy.deepcopy(ledger); changed['receipt_era']['total'] = 72
            repeated = nightly_coverage.weekly_report(self.root, changed, {'sha256': 'second'}, now=self.now)
            self.assertEqual(original, repeated)
            snapshot = Path(original['ledger']['path']); snapshot.write_text(snapshot.read_text() + ' ')
            with self.assertRaisesRegex(ValueError, 'weekly ledger snapshot hash mismatch'):
                nightly_coverage.weekly_report(self.root, changed, {}, now=self.now)


class EnforcingRoutingTests(unittest.TestCase):
    def result(self, mode='REPORT_ONLY', status='REPORTED'):
        return {key: value for key, value in [('mode', mode), ('status', status), ('checkpoint_status', 'PASS'),
                                            ('coverage', {}), ('doi_counts', {}), ('reports', {})]}

    def test_cli_default_stays_report_only(self):
        with patch.object(sys, 'argv', ['run_flow.py', '--root', '/r', '--checkpoint', '/f']), \
                patch('run_flow.cycle_report', return_value=self.result()) as call, patch('builtins.print'):
            self.assertEqual(run_flow.main(), 0)
            self.assertFalse(call.call_args.kwargs['enforce_new_artifacts'])

    def test_explicit_enforcing_hold_returns_nonzero(self):
        with patch.object(sys, 'argv', ['run_flow.py', '--root', '/r', '--checkpoint', '/f', '--enforce-new-artifacts']), \
                patch('run_flow.cycle_report', return_value=self.result('ENFORCING', 'HOLD')) as call, patch('builtins.print'):
            self.assertEqual(run_flow.main(), 2)
            self.assertTrue(call.call_args.kwargs['enforce_new_artifacts'])

    def test_mode_flags_are_mutually_exclusive(self):
        with patch.object(sys, 'argv', ['run_flow.py', '--root', '/r', '--checkpoint', '/f', '--report-only', '--enforce-new-artifacts']), \
                patch.object(sys, 'stderr'), self.assertRaises(SystemExit):
            run_flow.main()

    def test_prepared_checkpoint_routes_flag_and_propagates_failure(self):
        path = Path(__file__).parent/'production_snapshots/phase5-20261005-oai-cutover/after/RESEARCH_PIPELINE_v2/nightly_checkpoint.py'
        continuity = types.ModuleType('science_foundry_continuity'); continuity.evaluate = lambda: {}
        controller = types.ModuleType('autonomous_pipeline_controller'); controller.build_state = lambda: {}
        spec = importlib.util.spec_from_file_location('prepared_nightly_checkpoint', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, science_foundry_continuity=continuity, autonomous_pipeline_controller=controller):
            spec.loader.exec_module(module)
        completed = types.SimpleNamespace(returncode=2, stdout='HOLD', stderr='')
        with patch('subprocess.run', return_value=completed) as run, patch('builtins.print'):
            self.assertEqual(module.verification_coverage_after_checkpoint(Path('/f'), enforce_new_artifacts=True), 2)
            self.assertIn('--enforce-new-artifacts', run.call_args.args[0])
            self.assertNotIn('--report-only', run.call_args.args[0])
            self.assertIn('--intake-reviewed-nightly', run.call_args.args[0])
        with patch('subprocess.run', return_value=completed) as run, patch('builtins.print'):
            module.verification_coverage_after_checkpoint(Path('/f'))
            self.assertIn('--report-only', run.call_args.args[0])
            self.assertNotIn('--intake-reviewed-nightly', run.call_args.args[0])



class CoverageCycleIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkpoint = self.root/'RESEARCH_PIPELINE_v2/nightly_checkpoints/invocation/FINISH.json'
        self.checkpoint.parent.mkdir(parents=True)
        self.checkpoint.write_text(json.dumps({'invocation_id': 'invocation', 'status': 'NIGHTLY_PROGRESS_PASS',
                                               'incidents': [], 'generation': {'latest_run': 'Run-186',
                                                   'generated_at_utc': '2026-09-30T06:00:00+00:00',
                                                   'window': {'starts_at_utc': '2026-09-30T05:00:00+00:00'}}}))
        self.checkpoint.with_name('START.json').write_text(json.dumps({'started_at_utc': '2026-09-30T05:01:00+00:00'}))
        self.ledger = {'file_counts': {}, 'run_counts': {}, 'receipt_era': {'total': 71, 'certified': 71},
                       'mirror_drift': [], 'errors': [], 'run_entities': [
                           {'id': 'Run-186', 'kind': 'PAPER', 'path': 'science-engine/Run-186', 'status': 'CERTIFIED'}]}
        self.gate = {'status': 'PASS', 'exact_publication_binding': True, 'claim_gate': {'status': 'PASS'}}
        self.activation = {'binding': {'path': 'reports/verification-coverage/TEST_ONLY.json', 'sha256': 'a'*64},
                           'activated_at_utc': '2026-01-01T05:00:00+00:00'}
        (self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').write_text(json.dumps(self.ledger))
        self.patches = [patch('nightly_coverage.load_enforcement_activation', return_value=self.activation),
                        patch('corpus_ledger.build', return_value=self.ledger),
                        patch('corpus_ledger.render_markdown', return_value='Ledger'),
                        patch('doi_audit.build_audit', return_value={'published_records': []}),
                        patch('doi_audit.render_markdown', return_value='Audit'),
                        patch('doi_triage.build_triage', return_value={'counts': {}, 'records': []}),
                        patch('doi_triage.markdown', return_value='Triage'),
                        patch('nightly_coverage.checkpoint_window'), patch('nightly_coverage.weekly_report', return_value={}),
                        patch('nightly_coverage.collect_streak', return_value={'consecutive_clean_closed_windows': 0})]
        for obj in self.patches: obj.start(); self.addCleanup(obj.stop)

    def cycle(self, enforcing=True):
        with patch('production_hooks.publication_report', return_value=self.gate) as report:
            result = run_flow.cycle_report(self.root, self.checkpoint, self.root/'output', enforce_new_artifacts=enforcing)
        return result, report

    def test_enforcing_cycle_checks_latest_artifact_and_outputs_pass(self):
        result, report = self.cycle()
        self.assertEqual(result['mode'], 'ENFORCING'); self.assertEqual(result['status'], 'ENFORCING_PASS')
        self.assertTrue(report.call_args.kwargs['enforce_new_artifacts'])
        self.assertEqual(report.call_args.args[1], self.root.resolve()/'science-engine/Run-186')
        self.assertFalse(result['zenodo_writes']); self.assertFalse(result['generated_extra_run'])

    def test_binding_or_claim_hold_prevents_clean_pass(self):
        self.gate['exact_publication_binding'] = False
        result, _ = self.cycle()
        self.assertEqual(result['status'], 'HOLD')

    def test_report_only_does_not_activate_new_artifact_gate(self):
        result, report = self.cycle(enforcing=False)
        self.assertEqual(result['mode'], 'REPORT_ONLY'); self.assertFalse(result['enforcement'])
        self.assertIsNone(result['new_artifact_publication_gate']); report.assert_not_called()

    def test_registered_final_release_is_preferred_to_sealed_source(self):
        self.ledger['publication_entities'] = [{'id': 'publication:nightly-Run-186', 'run_id': 'Run-186',
                                               'path': 'RESEARCH_PIPELINE_v2/publication_releases/Run-186/attempt-1'}]
        result, report = self.cycle()
        self.assertEqual(result['status'], 'ENFORCING_PASS')
        self.assertEqual(report.call_args.args[1], self.root.resolve()/'RESEARCH_PIPELINE_v2/publication_releases/Run-186/attempt-1')

    def test_intake_hold_prevents_clean_pass(self):
        (self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').write_text(json.dumps(self.ledger))
        with patch('nightly_publication_intake.prepare', return_value={'status': 'HOLD', 'reasons': ['review pending']}), \
                patch('nightly_publication_intake.apply') as apply, patch('production_hooks.publication_report', return_value=self.gate):
            result = run_flow.cycle_report(self.root, self.checkpoint, self.root/'output', enforce_new_artifacts=True, intake_reviewed_nightly=True)
        self.assertEqual(result['status'], 'HOLD'); apply.assert_not_called()

    def test_ready_intake_routes_exact_expected_ledger_hash(self):
        (self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').write_text(json.dumps(self.ledger))
        with patch('nightly_publication_intake.prepare', return_value={'status': 'READY_FOR_AUTHORIZED_REGISTRATION', 'ledger_sha256': 'exact-hash'}), \
                patch('nightly_publication_intake.apply', return_value={'status': 'PUBLICATION_BOUND_REGISTERED'}) as apply, \
                patch('production_hooks.publication_report', return_value=self.gate):
            result = run_flow.cycle_report(self.root, self.checkpoint, self.root/'output', enforce_new_artifacts=True, intake_reviewed_nightly=True)
        self.assertEqual(result['status'], 'ENFORCING_PASS')
        self.assertEqual(apply.call_args.kwargs['expected_ledger_sha256'], 'exact-hash')

    def test_intake_cannot_run_in_report_only_mode(self):
        with self.assertRaisesRegex(ValueError, 'requires explicit enforcing mode'):
            run_flow.cycle_report(self.root, self.checkpoint, self.root/'output', intake_reviewed_nightly=True)

    def test_duplicate_latest_entity_is_hold(self):
        self.ledger['run_entities'].append(copy.deepcopy(self.ledger['run_entities'][0]))
        result, _ = self.cycle()
        self.assertEqual(result['status'], 'HOLD')
        self.assertIn('no unique canonical ledger entity', result['new_artifact_publication_gate']['reasons'][0])

if __name__ == '__main__': unittest.main()
