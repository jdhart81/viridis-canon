"""Receipt-only closeout reporting. The installed science guard remains authority.

Authentic HOLD journals can only reset a dated window. This consumer does not
verify Lean, issue certificates, publish, or modify historical receipts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys

import nightly_coverage as nc

CANONICAL_ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
INSTALLED_GUARD_SHA256 = 'fd9a4fe406445f3181391ca83f462c4889fb3392c4c93d5ac0d54838c223484f'
HISTORICAL_CONSUMER_SHA256 = '9663c006df997e368373f64e0f10e324661893d7b9246ea92a6c8dfec0b7ec3b'
HISTORICAL_CLOSEOUT = {
    'path': 'reports/verification-coverage/closeout-streak/2026-10-10/20261010T231231.963664Z/CLOSEOUT_STREAK_REPORT.json',
    'sha256': '9ef0b57a1cc642510c1bdaead892b38d43191ec005769bf84743139ef1a0e791',
}
TZ = nc.TZ


def reporting_cutover(root: Path, activation: dict, now: dt.datetime):
    """Use the completed deployed closure; never accept a caller-selected epoch."""
    wrapper = nc._load_source(root, activation['binding'])
    reference = wrapper.get('authorized_runtime_update')
    if reference is None:
        return None
    update = nc._load_source(root, reference)
    own = nc.binding(Path(__file__))['sha256']
    target = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/closeout_streak.py'
    rows = [row for row in update['additional_modules'] if row.get('path') == target]
    # Until the existing activation validator admits these exact deployed
    # reporting bytes, retain the previous global-rejection behavior.
    if len(rows) != 1 or rows[0].get('sha256') != own:
        return None
    protected = nc._load_source(root, update['protected_readback'])
    installed = nc._aware(update['installed_at_utc'])
    completed = nc._aware(protected['at_utc'])
    if not nc._aware(activation['activated_at_utc']) <= installed <= completed <= now:
        raise ValueError('reporting cutover must follow completed protected closure')
    guard = 'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
    targets = [row for row in update['runtime_targets'] if row.get('path') == guard]
    if len(targets) != 1 or targets[0].get('after_sha256') != INSTALLED_GUARD_SHA256:
        raise ValueError('reporting cutover changes the installed nightly authority')
    first = nc.first_eligible_window(completed + dt.timedelta(microseconds=1))
    return {'runtime_update': reference, 'protected_readback': update['protected_readback'],
            'completed_at_utc': completed.isoformat(), 'first_eligible_window': first,
            'collector_sha256': own, 'guard_sha256': INSTALLED_GUARD_SHA256}


def historical_rejections(root: Path, cutover: dict) -> dict[str, dict]:
    """Keep the exact pre-deployment rejection inventory and all bound inputs."""
    history = nc._load_source(root, HISTORICAL_CLOSEOUT)
    if (history.get('standard') != 'VRS-SEVEN-NIGHTLY-CLOSEOUT-1'
            or history.get('consecutive_clean_closed_windows') != 0
            or nc._aware(history['observed_at_utc']) >= nc._aware(cutover['completed_at_utc'])
            or history['authority']['installed_guard']['sha256'] != INSTALLED_GUARD_SHA256
            or history['authority']['closeout_consumer']['sha256'] != HISTORICAL_CONSUMER_SHA256):
        raise ValueError('exact historical rejection inventory must precede deployed cutover')
    inputs = {}
    for binding in history['input_reports']:
        path = nc._source_path(root, binding, historical_absolute=True)
        if path in inputs:
            raise ValueError('duplicate historical report binding')
        inputs[path] = binding
    result = {}
    for rejection in history['rejected']:
        path = Path(rejection['path'])
        if path not in inputs or path in result:
            raise ValueError('historical rejection outside complete bound inventory')
        report = json.loads(path.read_bytes())
        finish_path = nc._source_path(root, report['checkpoint'], historical_absolute=True)
        if (not finish_path.is_relative_to(root / 'RESEARCH_PIPELINE_v2/nightly_checkpoints')
                or finish_path.name != 'FINISH.json'):
            raise ValueError('historical FINISH outside canonical nightly journal')
        finish = json.loads(finish_path.read_bytes())
        nc._source_path(root, {'path': str(finish_path.with_name('START.json').relative_to(root)),
                              'sha256': finish['start_receipt_sha256']})
        for field in ('coverage_ledger', 'enforcement_activation'):
            if field in report:
                nc._source_path(root, report[field], historical_absolute=True)
        relative = str(path.relative_to(root))
        result[relative] = {'path': relative, 'sha256': inputs[path]['sha256']}
    if len(result) != 10:
        raise ValueError('complete ten historical rejected reports required')
    return result


def held_checkpoint_window(root: Path, report: dict, now: dt.datetime, *, activation=None) -> tuple[str, dict]:
    """Anchor an actual HOLD to its immutable nightly journal, never grant PASS.

    This separate bookkeeping path does not replace checkpoint_window: every
    clean window still passes the unchanged fresh science/claim/premise gates.
    An unknown or damaged journal remains globally fail-closed.
    """
    if (not isinstance(report, dict) or report.get('mode') != 'ENFORCING'
            or report.get('enforcement') is not True or report.get('status') != 'HOLD'):
        raise ValueError('only an explicit enforcing HOLD can be a dated failure')
    root = root.resolve()
    activation = activation or nc.load_enforcement_activation(root, now=now)
    checkpoint = nc._source_path(root, report['checkpoint'], historical_absolute=True)
    if (not checkpoint.is_relative_to(root / 'RESEARCH_PIPELINE_v2/nightly_checkpoints')
            or checkpoint.name != 'FINISH.json'):
        raise ValueError('HOLD checkpoint outside canonical checkpoint root')
    finish = json.loads(checkpoint.read_bytes())
    start_path = checkpoint.with_name('START.json')
    start_path = nc._source_path(root, {'path': str(start_path.relative_to(root)),
                                    'sha256': finish['start_receipt_sha256']})
    start = json.loads(start_path.read_bytes())
    if any(obj.get('standard') != 'VRS-NIGHTLY-CHECKPOINT-1' for obj in (start, finish)):
        raise ValueError('HOLD checkpoint standard mismatch')
    if (start.get('invocation_id') != checkpoint.parent.name
            or finish.get('invocation_id') != start['invocation_id']
            or finish.get('started_at_utc') != start['started_at_utc']):
        raise ValueError('HOLD checkpoint invocation/start identity mismatch')
    started, completed = nc._aware(start['started_at_utc']), nc._aware(finish['completed_at_utc'])
    observed = nc._aware(report['observed_at_utc'])
    if not started <= completed <= observed <= now:
        raise ValueError('future or reversed HOLD checkpoint/report timestamps')
    if finish.get('status') not in ('NIGHTLY_PROGRESS_PASS', 'HOLD_NIGHTLY_PROGRESS'):
        raise ValueError('unknown HOLD journal terminal status')
    incidents = finish.get('incidents')
    if (not isinstance(incidents, list) or any(not isinstance(x, str) or not x for x in incidents)
            or (finish['status'] == 'HOLD_NIGHTLY_PROGRESS' and not incidents)
            or (finish['status'] == 'NIGHTLY_PROGRESS_PASS' and incidents)):
        raise ValueError('HOLD journal incidents/status inconsistent')
    if ('checkpoint_status' in report and report['checkpoint_status'] != finish['status']) or (
            'incidents' in report and report['incidents'] != incidents):
        raise ValueError('HOLD report differs from immutable journal status/incidents')
    generation = finish['generation']
    window = generation['window']
    day = dt.date.fromisoformat(window['window_id'])
    lower = dt.datetime.combine(day, dt.time(1), TZ).astimezone(dt.timezone.utc)
    upper = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(1), TZ).astimezone(dt.timezone.utc)
    if (window.get('standard') != 'VRS-NIGHTLY-WINDOW-1'
            or window.get('timezone') != 'America/New_York'
            or nc._aware(window['starts_at_utc']) != lower
            or nc._aware(window['ends_at_utc']) != upper
            or type(window.get('satisfied')) is not bool
            or not lower <= started <= completed < upper):
        raise ValueError('HOLD journal is not within its real nightly window')
    if lower < nc._aware(activation['activated_at_utc']) or started < nc._aware(activation['activated_at_utc']):
        raise nc.PreActivationIneligible('PRE_ACTIVATION_INELIGIBLE: HOLD journal precedes completed activation')
    # A failed generation may legitimately lack a new paper; its real window is
    # anchored by the immutable invocation rather than an invented generation.
    nc.validate_report_activation(root, report, activation)
    return day.isoformat(), finish


def weekly_report_for_checkpoint(root: Path, report: dict, *, now: dt.datetime | None = None,
                                 activation=None) -> dict:
    """Persist coverage even for an authentic HOLD; never certify its window."""
    root = Path(root).resolve()
    now = now or dt.datetime.now(dt.timezone.utc)
    activation = activation or nc.load_enforcement_activation(root, now=now)
    if report.get('status') == 'HOLD':
        held_checkpoint_window(root, report, now, activation=activation)
    else:
        nc.checkpoint_window(root, report, now, activation=activation)
    ledger = nc.validate_report_activation(root, report, activation)
    return nc.weekly_report(root, ledger, report['checkpoint'], now=now)


def collect_closeout_streak(root: Path, reports: list[Path], *, now: dt.datetime | None = None) -> dict:
    """Count closed consecutive nightly windows once; replay cannot increase the count."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must include timezone')
    root = Path(root).resolve()
    grouped, rejected, ineligible, anchored_failures = {}, [], [], []
    local = now.astimezone(TZ)
    current_day = local.date() if local.hour >= 1 else local.date() - dt.timedelta(days=1)
    last_closed = current_day - dt.timedelta(days=1)
    try:
        activation = nc.load_enforcement_activation(root, now=now)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {'standard': 'VRS-SEVEN-NIGHTLY-CLOSEOUT-1', 'observed_at_utc': now.isoformat(),
                'status': 'HOLD_ENFORCEMENT_ACTIVATION', 'required': 7,
                'consecutive_clean_closed_windows': 0, 'last_closed_window': last_closed.isoformat(),
                'windows': {}, 'ineligible': [],
                'counting_rule': 'Only distinct genuine closed post-activation NY 01:00 windows count; an invalid activation cannot support a streak.',
                'rejected': [{'cause': type(exc).__name__ + ': ' + str(exc)}],
                'proof_execution': False, 'zenodo_writes': False}
    cutover, historical, collected_inputs = None, {}, []
    try:
        cutover = reporting_cutover(root, activation, now)
        if cutover is not None:
            historical = historical_rejections(root, cutover)
            # A caller cannot omit damaged/new evidence or delete old rejects.
            reports = list((root / 'reports/verification-coverage').rglob('NIGHTLY_CYCLE_REPORT.json'))
            for path in sorted(reports):
                if any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
                    raise ValueError('nightly report input contains a symlink')
                source = {'path': str(path.relative_to(root)), 'sha256': nc.binding(path)['sha256']}
                nc._source_path(root, source)
                collected_inputs.append(source)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {'standard': 'VRS-SEVEN-NIGHTLY-CLOSEOUT-1', 'observed_at_utc': now.isoformat(),
                'status': 'HOLD_REPORTING_CUTOVER', 'required': 7,
                'consecutive_clean_closed_windows': 0, 'last_closed_window': last_closed.isoformat(),
                'windows': {}, 'ineligible': [], 'anchored_failures': [],
                'rejected': [{'cause': type(exc).__name__ + ': ' + str(exc)}],
                'blocking_rejected': [{'cause': type(exc).__name__ + ': ' + str(exc)}],
                'proof_execution': False, 'zenodo_writes': False}
    for path in sorted(set(Path(p).resolve() for p in reports)):
        report = None
        try:
            report = json.loads(path.read_text())
            if not isinstance(report, dict):
                raise ValueError('nightly report must be an object')
            # Explicit report-only history never contributes a clean window.
            if report.get('mode') == 'REPORT_ONLY' and report.get('enforcement') is not True:
                continue
            if report.get('mode') != 'ENFORCING' or report.get('enforcement') is not True:
                raise ValueError('unknown nightly reporting mode or enforcement flag')
            day, finish = nc.checkpoint_window(Path(root), report, now, activation=activation)
            if cutover is not None and day < cutover['first_eligible_window']:
                ineligible.append({'report': nc.binding(path), 'status': 'PRE_REPORTING_CUTOVER_INELIGIBLE'})
                continue
            if cutover is not None and (nc._aware(finish['started_at_utc']) <= nc._aware(cutover['completed_at_utc'])
                    or nc._aware(finish['generation']['generated_at_utc']) <= nc._aware(cutover['completed_at_utc'])):
                raise ValueError('START/generation precedes completed reporting closure')
            grouped.setdefault(day, []).append({'report': nc.binding(path), 'clean': nc._clean(report, finish)})
        except nc.PreActivationIneligible as exc:
            ineligible.append({'report': nc.binding(path), 'status': 'PRE_ACTIVATION_INELIGIBLE', 'cause': str(exc)})
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            cause = type(exc).__name__ + ': ' + str(exc)
            try:
                day, _ = held_checkpoint_window(Path(root), report, now, activation=activation)
            except nc.PreActivationIneligible as old:
                ineligible.append({'report': nc.binding(path), 'status': 'PRE_ACTIVATION_INELIGIBLE', 'cause': str(old)})
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as anchor:
                rejected.append({'path': str(path), 'cause': cause,
                                 'anchor_cause': type(anchor).__name__ + ': ' + str(anchor)})
            else:
                own = nc.binding(path)
                grouped.setdefault(day, []).append({'report': own, 'clean': False})
                anchored_failures.append({'window': day, 'report': own, 'cause': cause})
    count, day = 0, last_closed
    while (cutover is None or day.isoformat() >= cutover['first_eligible_window']) and day.isoformat() in grouped and all(row['clean'] for row in grouped[day.isoformat()]):
        count += 1
        day -= dt.timedelta(days=1)
    # Untrusted/malformed enforcing evidence cannot support a clean streak.
    blocking = [row for row in rejected if str(Path(row['path']).relative_to(root)) not in historical]
    if blocking:
        count = 0
    return {'standard': 'VRS-SEVEN-NIGHTLY-CLOSEOUT-1', 'observed_at_utc': now.isoformat(),
            'status': 'SEVEN_CLEAN_NIGHTLY_WINDOWS' if count >= 7 else 'PENDING_GENUINE_NIGHTLY_WINDOWS',
            'required': 7, 'consecutive_clean_closed_windows': count,
            'last_closed_window': last_closed.isoformat(), 'windows': grouped, 'rejected': rejected, 'ineligible': ineligible,
            'blocking_rejected': blocking, 'historical_rejections': historical,
            'reporting_cutover': cutover,
            **({'input_reports': collected_inputs} if cutover is not None else {}),
            'anchored_failures': anchored_failures,
            'enforcement_activation': activation['binding'], 'activated_at_utc': activation['activated_at_utc'],
            'first_eligible_window': activation['first_eligible_window'],
            'premise_declaration_cutover_run': activation['premise_declaration_cutover_run'],
            'counting_rule': 'Distinct closed America/New_York 01:00 nightly windows; all enforcing reports in a counted window must be clean; missing dates break the streak.',
            'proof_execution': False, 'zenodo_writes': False}

def require_actual_installed_guard(root: Path) -> dict:
    """CLI refuses another root, import path or version of science authority."""
    if root != CANONICAL_ROOT or root.resolve() != CANONICAL_ROOT:
        raise ValueError('closeout reporting requires the exact canonical Cowork root')
    expected = root / 'RESEARCH_PIPELINE_v2/verification_coverage_gates/nightly_coverage.py'
    if expected.is_symlink() or Path(nc.__file__).resolve() != expected:
        raise ValueError('closeout reporting must import the actual installed guard')
    own = nc.binding(expected)
    if own['sha256'] != INSTALLED_GUARD_SHA256:
        raise ValueError('installed guard differs from the approved d25e closure')
    return own


def _weekly_current_candidate(root, paths, now):
    """Use an actual report from this ISO week; never substitute old coverage."""
    candidates = []
    for path in paths:
        try:
            report = json.loads(path.read_bytes())
            if not isinstance(report, dict):
                raise ValueError('weekly candidate must be a report object')
            observed = nc._aware(report['observed_at_utc'])
            if (report.get('mode') == 'ENFORCING' and report.get('enforcement') is True
                    and observed <= now
                    and observed.astimezone(TZ).isocalendar()[:2] == now.astimezone(TZ).isocalendar()[:2]):
                candidates.append((observed, path, report))
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            continue
    errors = []
    for _, path, report in sorted(candidates, key=lambda row: (row[0], str(row[1])), reverse=True):
        try:
            weekly = weekly_report_for_checkpoint(root, report, now=now)
            return {'status': weekly['status'], 'weekly_report': weekly,
                    'current_cycle_report': nc.binding(path), 'skipped_candidates': errors}
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            errors.append({'path': str(path), 'cause': type(exc).__name__ + ': ' + str(exc)})
    return {'status': 'HOLD_NO_CURRENT_AUTHENTIC_WEEKLY_COVERAGE', 'skipped_candidates': errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description='Receipt-only closeout streak and weekly coverage reporting')
    parser.add_argument('--root', type=Path, default=CANONICAL_ROOT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--weekly', action='store_true')
    args = parser.parse_args(argv)
    root = args.root
    now = dt.datetime.now(dt.timezone.utc)
    guard = require_actual_installed_guard(root)
    # No caller-selected subset: every saved coverage report remains visible.
    paths = sorted((root / 'reports/verification-coverage').rglob('NIGHTLY_CYCLE_REPORT.json'))
    for source in paths:
        nc._source_path(root, {'path': str(source.relative_to(root)),
                               'sha256': nc.binding(source)['sha256']})
    if Path(__file__).resolve() != root / 'RESEARCH_PIPELINE_v2/verification_coverage_gates/closeout_streak.py':
        raise ValueError('closeout consumer must be the own canonical source')
    report = collect_closeout_streak(root, paths, now=now)
    report['authority'] = {'installed_guard': guard, 'closeout_consumer': nc.binding(Path(__file__))}
    if 'input_reports' not in report:
        report['input_reports'] = [nc.binding(path) for path in paths]
    elif report.get('reporting_cutover') is not None:
        paths = [root / source['path'] for source in report['input_reports']]
    output = args.output or (root / 'reports/verification-coverage/closeout-streak'
                            / now.astimezone(TZ).date().isoformat()
                            / now.strftime('%Y%m%dT%H%M%S.%fZ'))
    allowed = root / 'reports/verification-coverage/closeout-streak'
    if not output.is_relative_to(allowed) or output == allowed or output.resolve() != output:
        raise ValueError('closeout output must be an own canonical closeout-streak directory')
    if output.exists():
        raise ValueError('closeout output already exists; preserve the prior receipt')
    if args.weekly:
        report['weekly_coverage'] = _weekly_current_candidate(root, paths, now)
    # Validate all sources again before the closeout-report write.
    require_actual_installed_guard(root)
    if report.get('reporting_cutover') is not None:
        epoch = report['reporting_cutover']
        nc._source_path(root, epoch['runtime_update'])
        nc._source_path(root, epoch['protected_readback'])
        if historical_rejections(root, epoch) != report['historical_rejections']:
            raise ValueError('historical rejection inputs changed during closeout observation')
        if nc.binding(Path(__file__))['sha256'] != epoch['collector_sha256']:
            raise ValueError('closeout collector changed during observation')
        actual_paths = sorted(str(p.relative_to(root)) for p in
                              (root / 'reports/verification-coverage').rglob('NIGHTLY_CYCLE_REPORT.json'))
        if actual_paths != sorted(row['path'] for row in report['input_reports']):
            raise ValueError('nightly report inventory changed during closeout observation')
    for source in report['input_reports']:
        nc._source_path(root, source, historical_absolute=True)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    path = output / 'CLOSEOUT_STREAK_REPORT.json'
    with path.open('x') as handle:
        handle.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
    actual = json.loads(path.read_bytes())
    if actual != report:
        raise ValueError('closeout receipt readback mismatch')
    print(json.dumps({'status': report['status'], 'consecutive_clean_closed_windows': report['consecutive_clean_closed_windows'],
                      'required': 7, 'receipt': nc.binding(path), 'enforcement_changed': False,
                      'proof_execution': False, 'zenodo_writes': False}, sort_keys=True))
    weekly_hold = args.weekly and report['weekly_coverage']['status'] != 'REPORTED'
    return 2 if report.get('blocking_rejected', report['rejected']) or report['status'] in {'HOLD_ENFORCEMENT_ACTIVATION', 'HOLD_REPORTING_CUTOVER'} or weekly_hold else 0


if __name__ == '__main__':
    raise SystemExit(main())
