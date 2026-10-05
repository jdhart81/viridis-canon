"""Hash-bound Phase 5 hook installation; plan-only unless explicitly applied.

No scheduler, protected verifier, generation root, or remote service changes.
The approved INV-9 issuer intake revision is an exact separately pinned target.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

GATE_MODULES = {'certificate_inspection', 'claim_binding', 'corpus_ledger', 'doi_audit', 'doi_triage',
                'mirror_parity', 'production_hooks', 'publication_gate', 'run_flow', 'static_pregate',
                'theorem_coverage', 'publication_binding', 'manuscript_structure', 'release_packet',
                'nightly_coverage', 'nightly_publication_intake', 'premise_declaration'}
TARGETS = {'RESEARCH_PIPELINE_v2/verification_coverage_gates/'+name+'.py' for name in GATE_MODULES} | {
    '_ZENODO_DEPOSITS/publish_dated_bundles.py', '_ZENODO_DEPOSITS/weekend_canon_lockstep.py',
    '_ZENODO_DEPOSITS/release_coherence.py', 'RESEARCH_PIPELINE_v2/nightly_checkpoint.py',
    'RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(root, snapshot_root):
    root, snapshot_root = Path(root).resolve(), Path(snapshot_root).resolve()
    manifest_path = snapshot_root/'AFTER_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    rows = manifest.get('snapshots')
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('malformed snapshot manifest')
    if len(rows) != len(TARGETS) or {row.get('relative_path') for row in rows} != TARGETS:
        raise ValueError('complete exact consumer installation target set required')
    result = {'standard': 'VRS-PHASE5-HOOK-INSTALL-1', 'mode': 'PLAN_ONLY', 'status': 'READY',
              'root': str(root), 'manifest_sha256': sha(manifest_path), 'targets': [], 'reasons': [],
              'protected_verifier_issuer_changes': True, 'protected_verifier_changes': False,
              'protected_issuer_intake_changes': True, 'scheduler_modified': False,
              'generation_root_modified': False, 'zenodo_writes': False}
    for row in rows:
        relative = row['relative_path']
        target, after = root/relative, snapshot_root/row['after_path']
        if target.is_symlink() or not target.resolve().is_relative_to(root):
            raise ValueError('target symlink or outside certification root: '+relative)
        if str(target) != row.get('production_path'):
            raise ValueError('manifest target does not match the selected root: '+relative)
        if after.is_symlink() or not after.resolve().is_relative_to(snapshot_root) or not after.is_file():
            raise ValueError('missing or external prepared file: '+relative)
        if sha(after) != row['after_sha256']:
            raise ValueError('prepared after hash mismatch: '+relative)
        if relative == 'RESEARCH_PIPELINE_v2/issue_lean_zero_sorry_certificate.py':
            baseline = json.loads((Path(__file__).resolve().parents[2]/'comparator-deploy/PROTECTED_IMPLEMENTATION_BASELINE.json').read_text())
            approval = baseline['premise_declaration_intake_approval']
            expected = baseline['protected_implementation_sha256']['issue_lean_zero_sorry_certificate.py']
            if approval.get('approved_by') != 'Justin' or approval.get('verifier_kernel_axiom_changes') is not False or approval.get('new_sha256') != expected:
                raise ValueError('approved protected issuer intake baseline required')
            if row['before_sha256'] != approval['old_sha256'] or row['after_sha256'] != expected:
                raise ValueError('protected issuer intake old/new hash mismatch')
        if row['before_path'] is not None:
            before = snapshot_root/row['before_path']
            if before.is_symlink() or not before.resolve().is_relative_to(snapshot_root) or sha(before) != row['before_sha256']:
                raise ValueError('sealed before hash mismatch: '+relative)
        actual = sha(target) if target.is_file() else None
        regular = not target.exists() or target.is_file()
        matched = regular and actual in {row['before_sha256'], row['after_sha256']}
        if not matched:
            result['status'] = 'HOLD'; result['reasons'].append('live target drift: '+relative)
        result['targets'].append({**row, 'live_sha256': actual, 'live_before_match': regular and actual == row['before_sha256'],
                                  'already_after': regular and actual == row['after_sha256'], 'matched': matched})
    return result


def apply(root, snapshot_root, *, expected_manifest_sha256, release_commit, receipt_dir):
    root, snapshot_root, receipt_dir = Path(root).resolve(), Path(snapshot_root).resolve(), Path(receipt_dir).resolve()
    if not receipt_dir.is_relative_to(root/'reports/verification-coverage') or receipt_dir.exists():
        raise ValueError('new immutable installation receipt directory required')
    if not isinstance(release_commit, str) or len(release_commit) != 40 or any(c not in '0123456789abcdef' for c in release_commit):
        raise ValueError('merged release commit SHA required')
    plan = inspect(root, snapshot_root)
    if plan['manifest_sha256'] != expected_manifest_sha256:
        raise ValueError('reviewed manifest SHA mismatch')
    if plan['status'] != 'READY':
        return plan
    receipt_dir.mkdir(parents=True, exist_ok=False)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    start = {**plan, 'mode': 'APPLY', 'status': 'INSTALL_STARTED', 'release_commit': release_commit, 'started_at_utc': now}
    (receipt_dir/'START.json').write_text(json.dumps(start, sort_keys=True, indent=2)+'\n')
    installed = []
    try:
        for row in plan['targets']:
            target = root/row['relative_path']; after = snapshot_root/row['after_path']
            actual = sha(target) if target.is_file() else None
            if target.is_symlink() or actual != row['live_sha256']:
                raise ValueError('concurrent live edit before installation: '+row['relative_path'])
            if sha(after) != row['after_sha256']:
                raise ValueError('prepared file changed during installation: '+row['relative_path'])
            if not row['already_after']:
                target.parent.mkdir(parents=True, exist_ok=True)
                mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else 0o644
                with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.'+target.name+'.phase5.', delete=False) as handle:
                    temporary = Path(handle.name); handle.write(after.read_bytes()); handle.flush(); os.fsync(handle.fileno())
                os.chmod(temporary, mode)
                os.replace(temporary, target)
            readback = sha(target)
            if readback != row['after_sha256']:
                raise ValueError('installed readback hash mismatch: '+row['relative_path'])
            installed.append({'path': row['relative_path'], 'before_sha256': row['live_sha256'],
                              'after_sha256': readback, 'written': not row['already_after']})
        final = {**start, 'status': 'INSTALLED_HASH_READBACK_PASS', 'installed': installed,
                 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                 'enforcement_scheduler_activation': 'SEPARATE_EXPLICIT_EXISTING_SCHEDULER_UPDATE',
                 'rollback': 'Use exact sealed before snapshots only through a separately authorized hash-checked change; never auto-rollback or overwrite a concurrent edit.'}
    except Exception as exc:
        final = {**start, 'status': 'HOLD_PARTIAL_INSTALLATION', 'installed': installed,
                 'completed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'reasons': [type(exc).__name__+': '+str(exc)]}
    (receipt_dir/'FINISH.json').write_text(json.dumps(final, sort_keys=True, indent=2)+'\n')
    return final


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--snapshots', type=Path, default=Path(__file__).parent/'production_snapshots/phase5-20261004')
    parser.add_argument('--apply', action='store_true'); parser.add_argument('--expected-manifest-sha256')
    parser.add_argument('--release-commit'); parser.add_argument('--receipt-dir', type=Path)
    args = parser.parse_args()
    try:
        if args.apply:
            if None in (args.expected_manifest_sha256, args.release_commit, args.receipt_dir):
                raise ValueError('apply requires reviewed manifest hash, merged release commit and receipt directory')
            result = apply(args.root, args.snapshots, expected_manifest_sha256=args.expected_manifest_sha256,
                           release_commit=args.release_commit, receipt_dir=args.receipt_dir)
        else:
            result = inspect(args.root, args.snapshots)
    except Exception as exc:
        result = {'status': 'HOLD', 'reasons': [type(exc).__name__+': '+str(exc)], 'zenodo_writes': False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result['status'] in {'READY', 'INSTALLED_HASH_READBACK_PASS'} else 2


if __name__ == '__main__': raise SystemExit(main())
