"""Coverage bookkeeping from genuine checkpoint receipts; never generates or verifies proofs."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('America/New_York')


def binding(path: Path) -> dict:
    return {'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def _aware(value: str) -> dt.datetime:
    result = dt.datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError('timestamp must include timezone')
    return result


def checkpoint_window(root: Path, report: dict, now: dt.datetime) -> tuple[str, dict]:
    """Re-read immutable START/FINISH bytes rather than trusting a report's date."""
    root = root.resolve()
    receipt = report['checkpoint']
    checkpoint = Path(receipt['path']).resolve(strict=True)
    if not checkpoint.is_relative_to(root / 'RESEARCH_PIPELINE_v2/nightly_checkpoints') or checkpoint.name != 'FINISH.json':
        raise ValueError('checkpoint outside canonical checkpoint root')
    if binding(checkpoint)['sha256'] != receipt['sha256']:
        raise ValueError('checkpoint hash mismatch')
    start_path = checkpoint.with_name('START.json')
    start, finish = json.loads(start_path.read_text()), json.loads(checkpoint.read_text())
    if any(obj.get('standard') != 'VRS-NIGHTLY-CHECKPOINT-1' for obj in (start, finish)):
        raise ValueError('checkpoint standard mismatch')
    if start.get('invocation_id') != checkpoint.parent.name or finish.get('invocation_id') != start['invocation_id']:
        raise ValueError('checkpoint invocation mismatch')
    if finish.get('start_receipt_sha256') != binding(start_path)['sha256']:
        raise ValueError('FINISH does not bind START bytes')
    started, completed = _aware(start['started_at_utc']), _aware(finish['completed_at_utc'])
    observed = _aware(report['observed_at_utc'])
    if not started <= completed <= observed <= now:
        raise ValueError('future or reversed checkpoint/report timestamps')
    if finish.get('started_at_utc') != start['started_at_utc']:
        raise ValueError('checkpoint start timestamp changed')
    generation = finish['generation']
    window = generation['window']
    day = dt.date.fromisoformat(window['window_id'])
    lower = dt.datetime.combine(day, dt.time(1), TZ).astimezone(dt.timezone.utc)
    upper = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(1), TZ).astimezone(dt.timezone.utc)
    if window.get('standard') != 'VRS-NIGHTLY-WINDOW-1' or window.get('timezone') != 'America/New_York':
        raise ValueError('generation window standard mismatch')
    if _aware(window['starts_at_utc']) != lower or _aware(window['ends_at_utc']) != upper:
        raise ValueError('generation window is not the real nightly window')
    generated = _aware(generation['generated_at_utc'])
    if not lower <= generated <= completed < upper or window.get('satisfied') is not True:
        raise ValueError('generation did not satisfy the checkpoint window')
    return day.isoformat(), finish


def _clean(report: dict, finish: dict) -> bool:
    coverage = report.get('coverage', {})
    gate = report.get('new_artifact_publication_gate', {})
    counts = coverage.get('receipt_era', {})
    return (report.get('mode') == 'ENFORCING' and report.get('enforcement') is True
            and report.get('status') == 'ENFORCING_PASS'
            and finish.get('status') == 'NIGHTLY_PROGRESS_PASS' and finish.get('incidents') == []
            and coverage.get('errors') == [] and coverage.get('mirror_drift') == []
            and isinstance(counts.get('total'), int) and isinstance(counts.get('certified'), int)
            and gate.get('status') == 'PASS' and gate.get('exact_publication_binding') is True
            and gate.get('claim_gate', {}).get('status') == 'PASS')


def collect_streak(root: Path, reports: list[Path], *, now: dt.datetime | None = None) -> dict:
    """Count closed consecutive nightly windows once; replay cannot increase the count."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must include timezone')
    grouped, rejected = {}, []
    for path in sorted(set(Path(p).resolve() for p in reports)):
        try:
            report = json.loads(path.read_text())
            # Report-only history never counts toward or breaks an enforcing streak.
            if report.get('mode') != 'ENFORCING' or report.get('enforcement') is not True:
                continue
            day, finish = checkpoint_window(Path(root), report, now)
            grouped.setdefault(day, []).append({'report': binding(path), 'clean': _clean(report, finish)})
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            rejected.append({'path': str(path), 'cause': type(exc).__name__ + ': ' + str(exc)})
    local = now.astimezone(TZ)
    current_day = local.date() if local.hour >= 1 else local.date() - dt.timedelta(days=1)
    last_closed = current_day - dt.timedelta(days=1)
    count, day = 0, last_closed
    while day.isoformat() in grouped and all(row['clean'] for row in grouped[day.isoformat()]):
        count += 1
        day -= dt.timedelta(days=1)
    # Untrusted/malformed enforcing evidence cannot support a clean streak.
    if rejected:
        count = 0
    return {'standard': 'VRS-SEVEN-NIGHTLY-WINDOWS-1', 'observed_at_utc': now.isoformat(),
            'status': 'SEVEN_CLEAN_NIGHTLY_WINDOWS' if count >= 7 else 'PENDING_GENUINE_NIGHTLY_WINDOWS',
            'required': 7, 'consecutive_clean_closed_windows': count,
            'last_closed_window': last_closed.isoformat(), 'windows': grouped, 'rejected': rejected,
            'counting_rule': 'Distinct closed America/New_York 01:00 nightly windows; all enforcing reports in a counted window must be clean; missing dates break the streak.',
            'proof_execution': False, 'zenodo_writes': False}


def weekly_report(root: Path, ledger: dict, checkpoint: dict, *, now: dt.datetime | None = None) -> dict:
    """Persist the first fresh ledger snapshot of each ISO week without rewriting it."""
    now = now or dt.datetime.now(dt.timezone.utc)
    year, week, _ = now.astimezone(TZ).isocalendar()
    output = Path(root) / 'reports/verification-coverage/weekly' / f'{year}-W{week:02}'
    report_path = output / 'WEEKLY_LEDGER_REPORT.json'
    if report_path.exists():
        previous = json.loads(report_path.read_text())
        snapshot = output / 'corpus_ledger.json'
        if previous['ledger']['sha256'] != binding(snapshot)['sha256']:
            raise ValueError('weekly ledger snapshot hash mismatch')
        return previous
    from corpus_ledger import render_markdown
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'corpus_ledger.json'
    with snapshot.open('x') as handle:
        handle.write(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    with (output / 'LEDGER.md').open('x') as handle:
        handle.write(render_markdown(ledger))
    report = {'standard': 'VRS-WEEKLY-COVERAGE-1', 'week': f'{year}-W{week:02}',
              'observed_at_utc': now.isoformat(), 'ledger': binding(snapshot), 'checkpoint': checkpoint,
              'coverage': {key: ledger[key] for key in ('file_counts', 'run_counts', 'receipt_era', 'mirror_drift', 'errors')},
              'status': 'HOLD' if ledger['errors'] or ledger['mirror_drift'] else 'REPORTED',
              'zenodo_writes': False, 'proof_execution': False}
    with report_path.open('x') as handle:
        handle.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
    return report
