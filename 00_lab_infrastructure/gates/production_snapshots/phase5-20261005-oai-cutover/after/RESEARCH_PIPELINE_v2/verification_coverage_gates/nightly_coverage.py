"""Coverage bookkeeping from genuine checkpoint receipts; never generates or verifies proofs."""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import re
import tomllib
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


# The activation receipt is bookkeeping evidence, never proof acceptance evidence.
ACTIVATION_STANDARD = 'VRS-PHASE5-ENFORCEMENT-ACTIVATION-1'
ACTIVATION_SOURCES = {'installation', 'protected_readback', 'registration_ledger',
                      'source_observation', 'scheduler_readback'}
ACTIVATION_PROOFS = {'after_manifest', 'merge_review', 'registration_plan',
                     'protected_baseline', 'scheduler_before'}
APPROVED_REGISTRATION_PLAN_SHA256 = '72044a08aba24d2c82d0b9fd68cb2198bc0075f6a456a0662a5e0554bed23b62'
COVERAGE_FIELDS = ('file_counts', 'run_counts', 'receipt_era', 'mirror_drift', 'errors')
REGISTRATION_IDENTITY_FIELDS = ('id', 'path', 'run_id', 'certificate', 'certificate_sha256',
                                'approved_publication_binding_reviews')


class PreActivationIneligible(ValueError):
    """Valid historical checkpoints are informational and cannot poison future windows."""


def ordinary_run(value):
    if (not isinstance(value, str) or re.fullmatch(r'Run-[0-9]{3}', value) is None
            or not 1 <= int(value[4:]) < 900):
        raise ValueError('canonical ordinary Run-001..899 required')
    return int(value[4:])


def _sha(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise ValueError('lowercase SHA-256 required')
    return value


def activation_binding(value):
    if not isinstance(value, dict) or set(value) != {'path', 'sha256'}:
        raise ValueError('exact activation/source path and SHA-256 binding required')
    relative = value['path']
    if (not isinstance(relative, str) or not relative or Path(relative).is_absolute()
            or any(part in ('.', '..') for part in Path(relative).parts)):
        raise ValueError('nonempty canonical tree-relative activation/source path required')
    if str(Path(relative)) != relative:
        raise ValueError('canonical unnormalized activation/source path forbidden')
    _sha(value['sha256'])
    return dict(value)


def _source_path(root, value, *, historical_absolute=False):
    if historical_absolute and isinstance(value, dict) and isinstance(value.get('path'), str) and Path(value['path']).is_absolute():
        # Existing protected baseline bytes contain absolute historical bindings.
        # They must resolve beneath the identical canonical root, never elsewhere.
        absolute = Path(value['path'])
        if not absolute.is_relative_to(root):
            raise ValueError('historical source binding outside canonical tree')
        value = {**value, 'path': str(absolute.relative_to(root))}
    value = activation_binding(value)
    path = root / value['path']
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError('activation/source path contains a symlink')
        current = current.parent
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('activation/source receipt is not a regular canonical file')
    if hashlib.sha256(resolved.read_bytes()).hexdigest() != value['sha256']:
        raise ValueError('activation/source SHA-256 mismatch')
    return resolved


def _load_source(root, value):
    obj = json.loads(_source_path(root, value).read_bytes())
    if not isinstance(obj, dict):
        raise ValueError('activation/source receipt object required')
    return obj


def _nested_sources(root, obj, seen=None, base=None):
    """Re-read recursively referenced receipt bytes, including existing baselines."""
    seen = set() if seen is None else seen
    base = root if base is None else base
    if isinstance(obj, dict):
        if set(obj) == {'path', 'sha256'}:
            reference = obj
            if isinstance(obj.get('path'), str) and not Path(obj['path']).is_absolute():
                # Unchanged historical manifests resolve their own relative
                # predecessor names beside the manifest, with full containment
                # and SHA checks. Root-relative new receipts stay authoritative.
                at_root, at_parent = root / obj['path'], base / obj['path']
                if at_root.exists() and at_parent.exists() and at_root.resolve() != at_parent.resolve():
                    raise ValueError('ambiguous recursive receipt binding')
                if not at_root.exists() and at_parent.exists():
                    reference = {**obj, 'path': str(at_parent.relative_to(root))}
            path = _source_path(root, reference, historical_absolute=True)
            if path in seen:
                return
            seen.add(path)
            try:
                child = json.loads(path.read_bytes())
            except (UnicodeDecodeError, json.JSONDecodeError):
                return  # Non-JSON configuration/source bytes are still hash-bound.
            _nested_sources(root, child, seen, path.parent)
        else:
            for child in obj.values():
                _nested_sources(root, child, seen, base)
    elif isinstance(obj, list):
        for child in obj:
            _nested_sources(root, child, seen, base)


def first_eligible_window(activated):
    local = activated.astimezone(TZ)
    day = local.date()
    boundary = dt.datetime.combine(day, dt.time(1), TZ)
    if boundary.astimezone(dt.timezone.utc) < activated:
        day += dt.timedelta(days=1)
    return day.isoformat()


def _registrations(root, ledger, original_plan):
    if ledger.get('tree_root') != str(root):
        raise ValueError('registration ledger canonical root differs')
    planned = original_plan.get('publication_entities')
    rows = ledger.get('publication_entities')
    if (not isinstance(planned, list) or len(planned) != 27 or
            not isinstance(rows, list) or any(not isinstance(e, dict) for e in planned + rows)):
        raise ValueError('original approved 27 registrations and current table required')
    expected = {e.get('id'): e for e in planned}
    actual = {e.get('id'): e for e in rows}
    if len(expected) != 27 or len(actual) != len(rows) or any(not isinstance(k, str) or not k for k in expected):
        raise ValueError('unique original registration identities required')
    if not expected.keys() <= actual.keys():
        raise ValueError('original publication registration was lost')
    for eid, original in expected.items():
        for field in REGISTRATION_IDENTITY_FIELDS:
            if not original.get(field) or actual[eid].get(field) != original[field]:
                raise ValueError('original publication registration identity/review changed: ' + eid + '/' + field)
    # Reuse the exact existing preserving consumer and public banner validator.
    # No status/name/count inference can replace these fresh checks.
    from corpus_ledger import preserve_publication_registrations, validate_uncertified_readback
    fresh = preserve_publication_registrations(copy.deepcopy(ledger), ledger)
    reviewed = fresh.get('publication_entities', [])
    if len(reviewed) != len(rows) or {e.get('id') for e in reviewed} != set(actual):
        raise ValueError('fresh preserving registration consumer changed identities')
    for entity in reviewed:
        if entity.get('enforcement_acceptable') is not True:
            raise ValueError('fresh publication registration is not enforcement-acceptable: ' + str(entity.get('id')))
        status = entity.get('publication_registration_status')
        if status == 'HOLD_NO_CLAIM_MAP':
            validate_uncertified_readback(root, entity)
        elif status != 'PASS':
            raise ValueError('registration is neither bound claim PASS nor explicit no-map public banner HOLD')
    return fresh


def _timestamp(obj, key, ceiling):
    value = _aware(obj[key])
    if value > ceiling:
        raise ValueError('future activation dependency timestamp: ' + key)
    return value


def _scheduler(root, receipt):
    if receipt.get('standard') != 'VRS-PHASE5-SCHEDULER-READBACK-1':
        raise ValueError('actual scheduler readback required')
    path = _source_path(root, receipt['raw_configuration'])
    raw = path.read_bytes()
    try:
        actual = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError):
        actual = tomllib.loads(raw.decode())
    if actual != receipt.get('automation') or not isinstance(actual, dict):
        raise ValueError('scheduler fields do not match captured actual configuration bytes')
    return actual


def validate_activation_receipt(root, receipt, *, now):
    """Validate immutable actual operation evidence; this never activates anything."""
    root = Path(root).resolve(strict=True)
    expected_keys = {'standard', 'status', 'tree_root', 'generation_root', 'scheduler_id', 'timezone',
                     'activated_at_utc', 'premise_declaration_cutover_run', 'first_eligible_window', 'sources', 'proofs'}
    if not isinstance(receipt, dict) or set(receipt) != expected_keys:
        raise ValueError('closed enforcement activation receipt fields required')
    if receipt['standard'] != ACTIVATION_STANDARD or receipt['status'] != 'ENFORCEMENT_ACTIVATED':
        raise ValueError('completed enforcement activation receipt required')
    if receipt['tree_root'] != str(root) or receipt['timezone'] != 'America/New_York':
        raise ValueError('activation root/timezone differs')
    from mirror_parity import GENERATION_ROOT
    if receipt['generation_root'] != str(GENERATION_ROOT) or receipt['scheduler_id'] != 'viridis-nightly-science-generator':
        raise ValueError('activation generation root or existing scheduler identity differs')
    activated = _aware(receipt['activated_at_utc'])
    if now.tzinfo is None or activated > now:
        raise ValueError('future or timezone-naive enforcement activation')
    cutoff = ordinary_run(receipt['premise_declaration_cutover_run'])
    floor = first_eligible_window(activated)
    if receipt['first_eligible_window'] != floor:
        raise ValueError('first eligible window is not the derived future NY calendar boundary')
    if (not isinstance(receipt['sources'], dict) or set(receipt['sources']) != ACTIVATION_SOURCES
            or not isinstance(receipt['proofs'], dict) or set(receipt['proofs']) != ACTIVATION_PROOFS):
        raise ValueError('complete exact activation source/proof set required')
    sources = {k: _load_source(root, v) for k, v in receipt['sources'].items()}
    proofs = {k: _load_source(root, v) for k, v in receipt['proofs'].items()}
    _nested_sources(root, receipt)
    install, manifest, merge = sources['installation'], proofs['after_manifest'], proofs['merge_review']
    gate_modules = {'certificate_inspection', 'claim_binding', 'corpus_ledger', 'doi_audit', 'doi_triage',
                    'mirror_parity', 'production_hooks', 'publication_gate', 'run_flow', 'static_pregate',
                    'theorem_coverage', 'publication_binding', 'manuscript_structure', 'release_packet',
                    'nightly_coverage', 'nightly_publication_intake', 'premise_declaration'}
    TARGETS = {'RESEARCH_PIPELINE_v2/verification_coverage_gates/' + name + '.py' for name in gate_modules} | {
        '_ZENODO_DEPOSITS/publish_dated_bundles.py', '_ZENODO_DEPOSITS/weekend_canon_lockstep.py',
        '_ZENODO_DEPOSITS/release_coherence.py', 'RESEARCH_PIPELINE_v2/nightly_checkpoint.py',
        'RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py'}
    if (install.get('standard') != 'VRS-PHASE5-HOOK-INSTALL-1'
            or install.get('status') != 'INSTALLED_HASH_READBACK_PASS' or install.get('root') != str(root)
            or install.get('manifest_sha256') != receipt['proofs']['after_manifest']['sha256']):
        raise ValueError('exact installed hash-readback FINISH/manifest required')
    installed, rows = install.get('installed'), manifest.get('snapshots')
    if not isinstance(installed, list) or not isinstance(rows, list):
        raise ValueError('installed target and manifest tables required')
    target_rows = {e.get('path'): e for e in installed if isinstance(e, dict)}
    manifest_rows = {e.get('relative_path'): e for e in rows if isinstance(e, dict)}
    if len(target_rows) != len(installed) or set(target_rows) != TARGETS or len(manifest_rows) != len(rows) or set(manifest_rows) != TARGETS:
        raise ValueError('exact complete 22 installed/manifest target set required')
    for relative, entry in target_rows.items():
        if _sha(entry.get('after_sha256')) != _sha(manifest_rows[relative].get('after_sha256')):
            raise ValueError('installed target hash differs from reviewed final manifest')
        _source_path(root, {'path': relative, 'sha256': entry['after_sha256']})
    if (merge.get('standard') != 'VRS-PHASE5-MERGE-REVIEW-1' or merge.get('status') != 'MERGED_REQUIRED_CHECKS_PASS'
            or merge.get('release_commit') != install.get('release_commit')
            or not isinstance(merge.get('release_commit'), str) or re.fullmatch(r'[0-9a-f]{40}', merge['release_commit']) is None):
        raise ValueError('independently captured merge and required CI proof required')
    pr = _load_source(root, merge['pull_request_readback'])
    checks_path = _source_path(root, merge['checks_readback'])
    checks = json.loads(checks_path.read_bytes())
    if (pr.get('number') != 50 or pr.get('state') != 'MERGED'
            or pr.get('mergeCommit', {}).get('oid') != merge['release_commit']
            or not isinstance(checks, list) or not checks or
            any(not isinstance(e, dict) or e.get('bucket') != 'pass' for e in checks)):
        raise ValueError('actual PR50 merge/check readbacks do not establish a complete required pass')
    baseline, protected = proofs['protected_baseline'], sources['protected_readback']
    if (baseline.get('standard') != 'VRS-PROTECTED-IMPLEMENTATION-BASELINE-1'
            or baseline.get('canonical_pipeline_root') != str(root / 'RESEARCH_PIPELINE_v2')
            or protected.get('status') != 'LIVE_PROTECTED_HASH_READBACK_PASS'
            or protected.get('baseline_sha256') != receipt['proofs']['protected_baseline']['sha256']):
        raise ValueError('actual protected post-install readback and exact reconciled baseline required')
    reconciliation = baseline.get('deployed_f2g_baseline_reconciliation', {})
    if (protected.get('approved_overlay_release') != reconciliation.get('release_commit')
            or protected.get('approved_overlay_manifest_sha256') != reconciliation.get('overlay_manifest_sha256')):
        raise ValueError('protected readback does not bind the authoritative F2G reconciliation')
    remote = {**baseline.get('deployed_pre_f2h_sha256', {}), **baseline.get('protected_remote_implementation_sha256', {})}
    remote.update({e['path']: e['deployed_authority_sha256'] for e in reconciliation.get('changes', [])})
    local = {**baseline.get('protected_implementation_sha256', {}), **baseline.get('unchanged_support_sha256', {})}
    expected = {('DEPLOYED_DROPLET', k): _sha(v) for k, v in remote.items()}
    expected.update({('CANONICAL_LOCAL', str(root / 'RESEARCH_PIPELINE_v2' / k)): _sha(v) for k, v in local.items()})
    observed = protected.get('checks')
    if not isinstance(observed, list) or any(not isinstance(e, dict) for e in observed):
        raise ValueError('actual protected target readback table required')
    joined = {(e.get('surface'), e.get('path')): e for e in observed}
    if len(joined) != len(observed) or set(joined) != set(expected):
        raise ValueError('protected readback omits or adds an authoritative local/remote target')
    for identity, expected_hash in expected.items():
        entry = joined[identity]
        if entry.get('expected_sha256') != expected_hash or entry.get('actual_sha256') != expected_hash or entry.get('match') is not True:
            raise ValueError('protected actual/expected hash differs')
    if receipt['proofs']['registration_plan']['sha256'] != APPROVED_REGISTRATION_PLAN_SHA256:
        raise ValueError('original exact approved 27-registration plan SHA-256 required')
    plan, snapshot = proofs['registration_plan'], sources['registration_ledger']
    if plan.get('tree_root') != str(root) or snapshot.get('premise_declaration_cutover_run') != receipt['premise_declaration_cutover_run']:
        raise ValueError('registration baseline root or cutover differs')
    _registrations(root, snapshot, plan)
    observation = sources['source_observation']
    if (observation.get('standard') != 'VRS-PHASE5-CUTOVER-OBSERVATION-1'
            or observation.get('tree_root') != str(root) or observation.get('generation_root') != receipt['generation_root']
            or observation.get('next_run') != receipt['premise_declaration_cutover_run']
            or observation.get('next_run_sealed') is not False):
        raise ValueError('actual next ordinary run source/mirror observation required')
    latest = ordinary_run(observation.get('latest_run'))
    if cutoff != latest + 1:
        raise ValueError('cutover does not follow the observed latest ordinary run')
    for key, expected_root in (('generation_state', receipt['generation_root']), ('mirror_state', str(root))):
        state = _load_source(root, observation[key])
        run_ids = state.get('run_ids')
        if (state.get('root') != expected_root or not isinstance(run_ids, list) or not run_ids
                or len(run_ids) != len(set(run_ids)) or max(ordinary_run(r) for r in run_ids) != latest
                or receipt['premise_declaration_cutover_run'] in run_ids):
            raise ValueError('captured source/mirror state selects a stale or wrong cutover')
    current = _scheduler(root, sources['scheduler_readback'])
    previous = _scheduler(root, proofs['scheduler_before'])
    if current.get('id') != receipt['scheduler_id'] or previous.get('id') != receipt['scheduler_id'] or current.get('status') != 'ACTIVE':
        raise ValueError('same existing ACTIVE scheduler required')
    allowed_scheduler_changes = {'prompt', 'updated_at', 'next_run_at'}
    if {k: v for k, v in current.items() if k not in allowed_scheduler_changes} != {k: v for k, v in previous.items() if k not in allowed_scheduler_changes}:
        raise ValueError('scheduler cadence/model/settings changed outside the approved prompt')
    rrule = current.get('rrule')
    if not isinstance(rrule, str):
        raise ValueError('actual unchanged four-checkpoint calendar schedule required')
    calendar = dict(part.split('=', 1) for part in rrule.removeprefix('RRULE:').split(';') if '=' in part)
    if (calendar.get('FREQ') != 'DAILY' or calendar.get('BYHOUR') != '1,7,13,19'
            or calendar.get('BYMINUTE', '0') != '0' or calendar.get('BYSECOND', '0') != '0'):
        raise ValueError('scheduler no longer has the approved four daily checkpoints')
    cwd = current.get('cwds', [current.get('cwd')])
    if cwd != [receipt['generation_root']]:
        raise ValueError('scheduler source cwd differs')
    prompt = current.get('prompt')
    if not isinstance(prompt, str):
        raise ValueError('actual enforcing scheduler prompt required')
    commands = [line for line in prompt.splitlines() if 'nightly_checkpoint.py' in line and ('--begin' in line or '--finish' in line)]
    if (not any('--begin' in line for line in commands) or not any('--finish' in line for line in commands)
            or any('--enforce-new-artifacts' not in line for line in commands)
            or '--require-premise-declaration' not in prompt
            or not all(token in prompt for token in ('foundation_basis', 'SEALED_RUN_MANIFEST', 'SEALED_CLAIM_INVENTORY'))):
        raise ValueError('actual finish/replay enforcement and explicit new-run premise issuance/sealing missing')
    started = _timestamp(install, 'started_at_utc', activated)
    installed_at = _timestamp(install, 'completed_at_utc', activated)
    protected_at = _timestamp(protected, 'at_utc', activated)
    ledger_at = _timestamp(snapshot, 'activation_snapshot_observed_at_utc', activated)
    source_at = _timestamp(observation, 'observed_at_utc', activated)
    scheduler_at = _timestamp(sources['scheduler_readback'], 'observed_at_utc', activated)
    merged_at = _timestamp(merge, 'observed_at_utc', activated)
    if not merged_at <= started <= installed_at <= protected_at <= ledger_at <= source_at <= scheduler_at <= activated:
        raise ValueError('reversed activation operation/readback chronology')
    return {'activated_at_utc': activated.isoformat(), 'first_eligible_window': floor,
            'premise_declaration_cutover_run': receipt['premise_declaration_cutover_run'],
            'registration_plan': plan, 'receipt': receipt}


def load_enforcement_activation(root, ledger=None, *, now=None):
    """Only the canonical SSOT can nominate activation; no timestamp/CLI override."""
    now = now or dt.datetime.now(dt.timezone.utc)
    root = Path(root).resolve(strict=True)
    canonical = root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
    if canonical.is_symlink() or not canonical.is_file():
        raise ValueError('regular authoritative coverage ledger required')
    authoritative = json.loads(canonical.read_bytes())
    if not isinstance(authoritative, dict) or authoritative.get('tree_root') != str(root):
        raise ValueError('authoritative activation ledger root differs')
    if ledger is not None and ledger != authoritative:
        raise ValueError('caller activation ledger differs from authoritative SSOT bytes')
    evidence = activation_binding(authoritative.get('enforcement_activation'))
    if not Path(evidence['path']).is_relative_to('reports/verification-coverage'):
        raise ValueError('activation receipt outside canonical reports root')
    receipt = _load_source(root, evidence)
    activation = validate_activation_receipt(root, receipt, now=now)
    if authoritative.get('premise_declaration_cutover_run') != activation['premise_declaration_cutover_run']:
        raise ValueError('authoritative cutover differs from immutable activation')
    _registrations(root, authoritative, activation['registration_plan'])
    activation['binding'] = evidence
    return activation


def validate_report_activation(root, report, activation):
    """Re-read the hash-bound per-cycle SSOT snapshot; report fields are not authority."""
    if report.get('enforcement_activation') != activation['binding']:
        raise ValueError('report activation binding missing or differs')
    snapshot = _load_source(root, report.get('coverage_ledger'))
    if snapshot.get('enforcement_activation') != activation['binding'] or snapshot.get('premise_declaration_cutover_run') != activation['premise_declaration_cutover_run']:
        raise ValueError('cycle ledger activation binding/cutover differs')
    _registrations(root, snapshot, activation['registration_plan'])
    if report.get('coverage') != {key: snapshot[key] for key in COVERAGE_FIELDS}:
        raise ValueError('report coverage differs from pinned cycle ledger snapshot')
    return snapshot


def checkpoint_window(root: Path, report: dict, now: dt.datetime, *, activation=None) -> tuple[str, dict]:
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
    if not lower <= generated <= completed < upper:
        raise ValueError('generation did not satisfy the checkpoint window')
    if activation is not None:
        activated = _aware(activation['activated_at_utc'])
        if lower < activated or started < activated or generated < activated:
            raise PreActivationIneligible('PRE_ACTIVATION_INELIGIBLE: window/START/generation precedes completed activation')
        if window.get('satisfied') is not True:
            raise ValueError('generation did not satisfy the checkpoint window')
        snapshot = validate_report_activation(root, report, activation)
        latest = generation.get('latest_run')
        if ordinary_run(latest) < ordinary_run(activation['premise_declaration_cutover_run']):
            raise ValueError('generated ordinary run precedes premise-declaration cutover')
        gate = report.get('new_artifact_publication_gate', {})
        joined = [e for e in snapshot.get('publication_entities', []) if e.get('run_id') == latest]
        joined = joined or [e for e in snapshot.get('run_entities', []) if e.get('id') == latest and e.get('kind') == 'PAPER']
        if len(joined) != 1 or gate.get('entity_id') != joined[0]['id']:
            raise ValueError('new-artifact gate is not joined to the exact generated run')
        if gate.get('premise_declaration_required') is not True or gate.get('premise_declaration', {}).get('status') != 'PASS':
            raise ValueError('actual required premise-declaration gate did not PASS')
        # Reuse the real publication/claim/premise consumer against the pinned
        # snapshot, never a caller's self-declared gate PASS. Source is read only
        # for parity; the Comparator-bound certificate remains proof authority.
        source_runs = [e for e in snapshot.get('run_entities', []) if e.get('id') == latest and e.get('kind') == 'PAPER']
        if len(source_runs) != 1:
            raise ValueError('generated run has no unique source/mirror parity row')
        from mirror_parity import run_parity
        parity = run_parity(root, source_runs[0]['path'])
        if parity.get('status') != 'MATCH' or parity.get('errors') or parity.get('differences'):
            raise ValueError('fresh generated-run source/mirror parity failed')
        from publication_gate import evaluate_publication
        fresh_gate = evaluate_publication(root / joined[0]['path'], snapshot,
                                         entity_id=joined[0]['id'], enforce=True,
                                         require_premise_declaration=True)
        if (fresh_gate.get('status') != 'PASS' or fresh_gate.get('exact_publication_binding') is not True
                or fresh_gate.get('claim_gate', {}).get('status') != 'PASS'
                or fresh_gate.get('premise_declaration_required') is not True
                or fresh_gate.get('premise_declaration', {}).get('status') != 'PASS'):
            raise ValueError('fresh actual publication/claim/premise gate failed')
    if window.get('satisfied') is not True:
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
            and type(counts.get('total')) is int and type(counts.get('certified')) is int
            and gate.get('status') == 'PASS' and gate.get('exact_publication_binding') is True
            and gate.get('claim_gate', {}).get('status') == 'PASS')


def collect_streak(root: Path, reports: list[Path], *, now: dt.datetime | None = None) -> dict:
    """Count closed consecutive nightly windows once; replay cannot increase the count."""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must include timezone')
    grouped, rejected, ineligible = {}, [], []
    local = now.astimezone(TZ)
    current_day = local.date() if local.hour >= 1 else local.date() - dt.timedelta(days=1)
    last_closed = current_day - dt.timedelta(days=1)
    try:
        activation = load_enforcement_activation(root, now=now)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        return {'standard': 'VRS-SEVEN-NIGHTLY-WINDOWS-1', 'observed_at_utc': now.isoformat(),
                'status': 'HOLD_ENFORCEMENT_ACTIVATION', 'required': 7,
                'consecutive_clean_closed_windows': 0, 'last_closed_window': last_closed.isoformat(),
                'windows': {}, 'ineligible': [],
                'counting_rule': 'Only distinct genuine closed post-activation NY 01:00 windows count; an invalid activation cannot support a streak.',
                'rejected': [{'cause': type(exc).__name__ + ': ' + str(exc)}],
                'proof_execution': False, 'zenodo_writes': False}
    for path in sorted(set(Path(p).resolve() for p in reports)):
        try:
            report = json.loads(path.read_text())
            # Report-only history never counts toward or breaks an enforcing streak.
            if report.get('mode') != 'ENFORCING' or report.get('enforcement') is not True:
                continue
            day, finish = checkpoint_window(Path(root), report, now, activation=activation)
            grouped.setdefault(day, []).append({'report': binding(path), 'clean': _clean(report, finish)})
        except PreActivationIneligible as exc:
            ineligible.append({'report': binding(path), 'status': 'PRE_ACTIVATION_INELIGIBLE', 'cause': str(exc)})
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            rejected.append({'path': str(path), 'cause': type(exc).__name__ + ': ' + str(exc)})
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
            'last_closed_window': last_closed.isoformat(), 'windows': grouped, 'rejected': rejected, 'ineligible': ineligible,
            'enforcement_activation': activation['binding'], 'activated_at_utc': activation['activated_at_utc'],
            'first_eligible_window': activation['first_eligible_window'],
            'premise_declaration_cutover_run': activation['premise_declaration_cutover_run'],
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
