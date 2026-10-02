#!/usr/bin/env python3
"""Report-only v3 coverage of the canonical control plane; no new verification."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
from certificate_inspection import inspect_certificate
from static_pregate import scan
from run_flow import flow
from mirror_parity import GENERATION_ROOT, run_parity

PRIORITY = ('MIRROR_DRIFT', 'UNSOUND', 'HAS_SORRY', 'DEBT', 'NO_FORMALIZATION', 'CLEAN_UNCERTIFIED', 'CERTIFIED')
DEFAULT_ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')


def partition_status(*conditions):
    active = set(conditions)
    return next(s for s in PRIORITY if s in active)


def counts(rows):
    found = Counter(r['status'] for r in rows)
    return {s: found[s] for s in PRIORITY}


def run_id(path):
    for part in Path(path).parts:
        match = re.fullmatch(r'Run-(\d+)(?:[_-].*)?', part)
        if match:
            return f'Run-{int(match[1]):03d}'
    return None


def discover(root):
    paths, errors, excluded = [], [], []
    def onerror(error):
        errors.append(str(error))
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
        for name in list(dirs):
            if name in ('_LATEST', '.git'):
                dirs.remove(name)
                if name == '_LATEST':
                    excluded.append(str(Path(directory) / name))
        for filename in files:
            if filename.endswith('.lean'):
                paths.append(Path(directory) / filename)
    return sorted(paths), errors, sorted(excluded)


def file_status(result, certificate=None, expected=False):
    conditions = []
    if result.get('unexpected_axioms') or result.get('has_sorryAx'):
        conditions.append('UNSOUND')
    if result.get('has_sorry'):
        conditions.append('HAS_SORRY')
    if result.get('errors') or (result.get('flags') and not conditions) or (expected and not certificate):
        conditions.append('DEBT')
    if certificate and certificate['valid']:
        conditions.append('CERTIFIED')
    elif result.get('static_pass') and not conditions:
        conditions.append('CLEAN_UNCERTIFIED')
    return partition_status(*conditions)


def build(root, cert_root, generation_root=GENERATION_ROOT):
    root, cert_root = Path(root).resolve(), Path(cert_root).resolve()
    if not root.is_dir() or not cert_root.is_dir():
        raise ValueError('missing canonical root or certificate root')
    papers = root / 'science-engine/07_nightly_engine/compound research papers'
    if not papers.is_dir():
        raise ValueError('missing canonical nightly paper root: ' + str(papers))
    certs = [inspect_certificate(p, root) for p in sorted(cert_root.glob('Run-*/LEAN_ZERO_SORRY_CERTIFICATE.json'))]
    by_hash = {c['candidate_sha256']: c for c in certs if c['valid']}
    by_run = {c['run_id']: c for c in certs if c.get('run_id')}
    paths, errors, excluded = discover(root)
    file_entities = []
    for path in paths:
        relative = path.relative_to(root)
        result = scan(path)
        cert = by_hash.get(result.get('sha256'))
        rid = run_id(relative)
        zone = next((part for part in relative.parts if re.match(r'^\d\d_', part)), relative.parts[0])
        result.update(id='file:' + str(relative), path=str(relative), absolute_path=str(path), zone=zone,
            entity_type='FILE', scope='DEPENDENCY' if '.lake' in relative.parts or '01_MATHLIB' in relative.parts else 'CORPUS', run_id=rid, certificate=cert['path'] if cert else None,
            certificate_valid=bool(cert), doi=None)
        result['status'] = file_status(result, cert, expected=rid is not None)
        result['reasons'] = result['errors'] + [f['kind'] for f in result['flags']]
        if not cert:
            result['reasons'].append('no valid certificate binds these bytes')
        file_entities.append(result)
    papers = root / 'science-engine/07_nightly_engine/compound research papers'
    run_entities = []
    for path in sorted(papers.glob('Run-*')):
        if not path.is_dir():
            continue
        if path.name == 'Run-META-001_canon-synthesis':
            run_entities.append({'id': path.name, 'kind': 'SYNTHESIS', 'entity_type': 'RUN',
                'path': str(path.relative_to(root)), 'status': 'CLEAN_UNCERTIFIED',
                'certificate_valid': False, 'certificate': None, 'reasons': ['synthesis; excluded from paper coverage denominator']})
            continue
        rid = run_id(path.name)
        if rid is None:
            continue
        members = [f for f in file_entities if Path(f['absolute_path']).is_relative_to(path)]
        cert = by_run.get(rid)
        # A run's verification entity is its immutable certificate envelope if present.
        # Historical WIP/challenge copies stay individually classified in the file table.
        if cert and cert['valid']:
            candidate = scan(Path(cert['candidate_path']))
            status = file_status(candidate, cert)
            reasons = candidate['errors'] + [f['kind'] for f in candidate['flags']]
            if status != 'CERTIFIED':
                reasons.append('issued candidate fails static pre-gate')
        else:
            conditions = [f['status'] for f in members if f['status'] in ('UNSOUND', 'HAS_SORRY')]
            conditions += ['DEBT'] if int(rid.split('-')[1]) >= 116 or cert else []
            if not members:
                conditions.append('NO_FORMALIZATION')
            if not conditions:
                conditions.append('CLEAN_UNCERTIFIED')
            status = partition_status(*conditions)
            reasons = (cert or {}).get('reasons', []) + ['no valid certificate for immutable run envelope']
        underlying_status = status
        parity = run_parity(root, path.relative_to(root), generation_root)
        if parity['status'] != 'MATCH':
            status = 'MIRROR_DRIFT'
            reasons += ['source/mirror parity failed'] + parity['errors']
        run_entities.append({'parity': parity, 'underlying_status': underlying_status, 'id': rid, 'kind': 'PAPER', 'entity_type': 'RUN', 'path': str(path.relative_to(root)),
            'status': status, 'source_file_ids': [f['id'] for f in members], 'certificate': cert['path'] if cert else None,
            'certificate_valid': bool(cert and cert['valid'] and status == 'CERTIFIED'),
            'certificate_artifacts': cert.get('sealed_paper_inputs', {}) if cert else {},
            'certified_theorems': cert.get('certified_theorems', []) if cert else [],
            'nonvacuity': cert.get('nonvacuity', []) if cert else [], 'reasons': reasons})
    rows = [r for r in run_entities if r['kind'] == 'PAPER']
    for row in rows:
        row['flow'] = flow(root, row)
    receipt = [r for r in rows if 116 <= int(r['id'].split('-')[1]) ]
    return {'schema_version': 'verification-coverage-v4', 'mode': 'REPORT_ONLY', 'tree_root': str(root),
        'cert_root': str(cert_root), 'generation_root_parity_only': str(generation_root), 'priority': list(PRIORITY), 'errors': errors, 'excluded_latest': excluded,
        'trust_boundary': 'Existing hash-bound Comparator certificates only; static scans cannot certify.',
        'run_scope': 'Immutable certified envelope when available; original WIP/challenge copies remain separate FILE entities.',
        'file_counts': counts(file_entities), 'run_counts': counts(rows), 'synthesis_count': sum(r['kind']=='SYNTHESIS' for r in run_entities),
        'eligible_paper_runs': sum(r['status']!='MIRROR_DRIFT' for r in rows),
        'mirror_drift': [r['id'] for r in rows if r['status']=='MIRROR_DRIFT'],
        'receipt_era': {'certified': sum(r['status']=='CERTIFIED' for r in receipt), 'total': len(receipt)},
        'recorded_certificate_counts': {'present': len(certs), 'current_existing_consumer': sum(c.get('recorded_certificate_current', False) for c in certs), 'current_witness_evidence_pass': sum(c['valid'] for c in certs)},
        'certificates': certs, 'file_entities': file_entities, 'run_entities': run_entities}


def render_markdown(ledger):
    lines = ['# Canonical corpus ledger', '', 'Mode: REPORT_ONLY; no public metadata changes or new verification.',
        '', 'Canonical tree: `' + ledger['tree_root'] + '`', 'Certificate root: `' + ledger['cert_root'] + '`',
        '', ledger['trust_boundary'], '', ledger['run_scope'], '',
        'Strict priority: ' + ' > '.join(ledger['priority']), '', '## Counts', '',
        '| Status | File entities | Paper run entities |', '|---|---:|---:|']
    lines += [f"| {s} | {ledger['file_counts'][s]} | {ledger['run_counts'][s]} |" for s in PRIORITY]
    lines += ['', 'Receipt-era coverage: ' + str(ledger['receipt_era']) + '.',
        f"Synthesis entities: {ledger['synthesis_count']} (outside paper denominator). _LATEST pointers excluded: {len(ledger['excluded_latest'])}.",
        'Recorded certificate inspection: ' + str(ledger['recorded_certificate_counts']),
        '', '## Run entities', '', '| Run | Kind | Status | Reasons |', '|---|---|---|---|']
    lines += [f"| {r['id']} | {r['kind']} | {r['status']} | {'; '.join(r['reasons'] + r.get('flow', {}).get('causes', []))} |" for r in ledger['run_entities']]
    lines += ['', '## File entities', '', '| Path | Status | Axioms |', '|---|---|---|']
    lines += [f"| `{f['path']}` | {f['status']} | {', '.join(f['declared_axioms'])} |" for f in ledger['file_entities']]
    lines += ['', '## Inspection errors', ''] + ledger['errors']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build'])
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--cert-root', type=Path, default=Path('RESEARCH_PIPELINE_v2/lean_certificates'))
    parser.add_argument('--generation-root', type=Path, default=GENERATION_ROOT, help='parity only, never certification')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    cert_root = args.cert_root if args.cert_root.is_absolute() else args.root / args.cert_root
    try:
        ledger = build(args.root, cert_root, args.generation_root)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        args.out.with_name('LEDGER.md').write_text(render_markdown(ledger))
    except Exception as exc:
        print(json.dumps({'status': 'HOLD', 'mode': 'REPORT_ONLY', 'reasons': [type(exc).__name__ + ': ' + str(exc)]}))
        return 1
    print(json.dumps({k: ledger[k] for k in ('file_counts','run_counts','receipt_era','synthesis_count','errors')}, indent=2))
    return 1 if ledger['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
