#!/usr/bin/env python3
"""Prepare immutable evidence for a new review; never repair a historical receipt in place."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
STANDARD = 'VRS-SCIENTIFIC-RECONCILIATION-1'
ALIASES = {'STATEMENT_CONTRACT.json': 'formalization/STATEMENT_CONTRACT.json'}
REQUIRED = ['FINALIZED_PACKAGE.json', 'POST_ARISTOTLE_REVIEW.json', 'PAPER_PACKAGE_MANIFEST.json', 'paper.pdf', 'paper.tex']

class ReconciliationError(ValueError):
    pass

def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode()

def digest(data):
    return hashlib.sha256(data).hexdigest()

def obj(path):
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ReconciliationError('Expected JSON object: ' + path.name)
    return value

def local(root, name):
    if not isinstance(name, str) or not name or '\\' in name:
        raise ReconciliationError('Invalid artifact path')
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or '.' in rel.parts or str(rel) != name:
        raise ReconciliationError('Artifact path is not canonical and relative')
    target = root / rel
    if any(x.is_symlink() for x in [target, *target.parents] if x == root or root in x.parents):
        raise ReconciliationError('Symlink artifact refused')
    if not target.resolve().is_relative_to(root.resolve()):
        raise ReconciliationError('Artifact escapes source root')
    return target

def source_inventory(root):
    if root.is_symlink() or not root.is_dir():
        raise ReconciliationError('Source must be a real directory')
    result = {}
    for path in sorted(root.rglob('*')):
        if '__pycache__' in path.parts:
            continue
        if path.is_symlink():
            raise ReconciliationError('Symlink in scientific source')
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            result[rel] = digest(path.read_bytes())
    for name in REQUIRED:
        if name not in result:
            raise ReconciliationError('Required source absent: ' + name)
    return result

def inspect_bindings(root):
    inventory = source_inventory(root)
    review = obj(root / 'POST_ARISTOTLE_REVIEW.json')
    final = obj(root / 'FINALIZED_PACKAGE.json')
    if review.get('verdict') != 'pass' or final.get('status') != 'FINALIZED':
        raise ReconciliationError('Reconciliation requires an existing historical finalized review; it cannot invent one')
    rows = []
    for kind, binding in [('finalized.artifact_sha256', final.get('artifact_sha256')),
                          ('review.artifacts', review.get('artifacts')),
                          ('review.reviewed_evidence_sha256', review.get('reviewed_evidence_sha256'))]:
        if binding is None:
            continue
        if not isinstance(binding, dict):
            raise ReconciliationError('Malformed declared binding set')
        for name, expected in sorted(binding.items()):
            path = local(root, name)
            if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected):
                raise ReconciliationError('Malformed historical hash')
            actual = inventory.get(name)
            row = {'binding': kind, 'declared_path': name, 'reviewed_sha256': expected,
                   'current_sha256': actual, 'resolved_path': name if actual else None}
            if actual == expected:
                row['status'] = 'EXACT_CURRENT_MATCH'
            elif actual is not None:
                row['status'] = 'CHANGED_REQUIRES_INDEPENDENT_REVIEW'
            else:
                alias = ALIASES.get(name)
                alias_path = local(root, alias) if alias else None
                if alias_path and alias_path.is_file() and digest(alias_path.read_bytes()) == expected:
                    row.update(status='EXACT_BYTES_AT_EXPLICIT_ALTERNATE_PATH', resolved_path=alias,
                               resolved_sha256=expected)
                else:
                    row['status'] = 'MISSING_REQUIRES_INDEPENDENT_REVIEW'
            rows.append(row)
    if not rows:
        raise ReconciliationError('No historical evidence bindings')
    return inventory, rows

def prepare(run, *, finalized_root=HERE/'finalized_runs', output_root=HERE/'scientific_reconciliations', author_invocation):
    if not re.fullmatch(r'Run-[1-9][0-9]*', run):
        raise ReconciliationError('Explicit canonical Run identity required')
    if not isinstance(author_invocation, str) or not author_invocation.strip():
        raise ReconciliationError('Preparation invocation attribution required')
    source = local(finalized_root, run)
    inventory, rows = inspect_bindings(source)
    final = obj(source/'FINALIZED_PACKAGE.json')
    if final.get('run_id') != run:
        raise ReconciliationError('Finalized run identity mismatch')
    request = {'standard': STANDARD, 'run_id': run, 'status': 'INDEPENDENT_RECONCILIATION_REVIEW_REQUIRED',
               'source_root': str(source.resolve()), 'source_inventory_sha256': inventory,
               'declared_bindings': rows, 'prepared_by_invocation': author_invocation,
               'scientific_status_upgraded': False, 'kernel_admission': False, 'publication_authorized': False,
               'runtime_activation': False, 'historical_artifacts_rewritten': False,
               'required_review': ['Review exact current manifest and claim-to-proof scope.',
                    'Check all source changes, missing bindings and explicit alternate-path resolutions.',
                    'Validate the exact existing proof certificate and dependency evidence; do not claim a new proof.',
                    'Independently replay applicable numerical evidence from an isolated copy.',
                    'Bind the new review to this full request and exact current scientific bytes.',
                    'Keep empirical status, kernel/no-kernel disposition and publication approval separate.']}
    identity = digest(canonical(request))
    target = output_root / run / identity
    if output_root.is_symlink() or (output_root/run).is_symlink() or target.is_symlink():
        raise ReconciliationError('Symlink destination refused')
    if target.exists():
        verify_packet(target)
        if obj(target/'RECONCILIATION_REQUEST.json') != request:
            raise ReconciliationError('Immutable request differs')
        return {'status': request['status'], 'run_id': run, 'request_sha256': identity, 'path': str(target), 'created': False}
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = Path(tempfile.mkdtemp(prefix='.prepare-', dir=target.parent))
    try:
        (temporary/'source').mkdir(mode=0o700)
        for name, expected in inventory.items():
            data = local(source, name).read_bytes()
            if digest(data) != expected:
                raise ReconciliationError('Source changed while snapshotting')
            destination = temporary/'source'/name
            destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            destination.write_bytes(data); destination.chmod(0o600)
        (temporary/'RECONCILIATION_REQUEST.json').write_bytes(canonical(request))
        (temporary/'RECONCILIATION_REQUEST.json').chmod(0o600)
        if source_inventory(source) != inventory:
            raise ReconciliationError('Source changed during preparation')
        verify_packet(temporary, expected_identity=identity)
        os.rename(temporary, target)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return {'status': request['status'], 'run_id': run, 'request_sha256': identity, 'path': str(target), 'created': True}

def verify_packet(packet, *, expected_identity=None):
    if packet.is_symlink() or not packet.is_dir():
        raise ReconciliationError('Packet must be a real directory')
    request_path = local(packet, 'RECONCILIATION_REQUEST.json')
    request = obj(request_path)
    if request.get('standard') != STANDARD or request.get('status') != 'INDEPENDENT_RECONCILIATION_REVIEW_REQUIRED':
        raise ReconciliationError('Unexpected request contract')
    if any(request.get(k) is not False for k in ['scientific_status_upgraded', 'kernel_admission', 'publication_authorized', 'runtime_activation', 'historical_artifacts_rewritten']):
        raise ReconciliationError('Request cannot grant authority')
    if digest(canonical(request)) != (expected_identity or packet.name) or request_path.read_bytes() != canonical(request):
        raise ReconciliationError('Request identity or encoding changed')
    if source_inventory(packet/'source') != request['source_inventory_sha256']:
        raise ReconciliationError('Snapshot changed')
    inventory, rows = inspect_bindings(packet/'source')
    if rows != request['declared_bindings']:
        raise ReconciliationError('Declared comparison changed')
    return request

def validate_review(packet, review_path, *, current_source=None):
    """Verify a separately authored review without converting it into release authority."""
    from datetime import datetime
    request = verify_packet(packet)
    if review_path.is_symlink() or not review_path.is_file():
        raise ReconciliationError('Review must be a real file')
    review = obj(review_path)
    if review.get('standard') != 'VRS-SCIENTIFIC-RECONCILIATION-REVIEW-1' or review.get('run_id') != request['run_id']:
        raise ReconciliationError('Unexpected independent review identity')
    if review.get('request_sha256') != packet.name or review.get('source_inventory_sha256') != request['source_inventory_sha256']:
        raise ReconciliationError('Review does not bind the exact request and complete scientific bytes')
    reviewer = review.get('reviewer') or {}
    if (not reviewer.get('provider') or not reviewer.get('model') or not reviewer.get('review_invocation_id')
        or reviewer.get('preparer_invocation_id') != request['prepared_by_invocation']
        or reviewer['review_invocation_id'] == request['prepared_by_invocation']
        or reviewer.get('independent_from_preparer') is not True):
        raise ReconciliationError('An attributed, separate review invocation is required')
    try:
        reviewed = datetime.fromisoformat(review['reviewed_at_utc'].replace('Z', '+00:00'))
        if reviewed.utcoffset() is None or reviewed.timestamp() < (packet/'RECONCILIATION_REQUEST.json').stat().st_mtime:
            raise ValueError('review predates sealed request')
    except (KeyError, TypeError, ValueError) as error:
        raise ReconciliationError('Review chronology must follow the sealed request') from error
    if review.get('verdict') not in {'PASS', 'HOLD'} or not isinstance(review.get('findings'), list):
        raise ReconciliationError('Explicit review verdict and findings required')
    if review.get('no_new_proof') is not True or any(review.get(k) is not False for k in ['historical_artifacts_rewritten', 'publication_authorized', 'runtime_admission']):
        raise ReconciliationError('Reconciliation review cannot grant proof, publication or runtime authority')
    artifacts = review.get('review_artifact_sha256')
    if not isinstance(artifacts, dict) or not artifacts:
        raise ReconciliationError('Independent review evidence bindings required')
    for name, expected in artifacts.items():
        path = local(review_path.parent, name)
        if not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected) or not path.is_file() or digest(path.read_bytes()) != expected:
            raise ReconciliationError('Independent review artifact changed or missing: '+name)
    if review['verdict'] == 'PASS':
        pdf = review.get('complete_pdf_review') or {}
        count = pdf.get('page_count')
        if (pdf.get('passed') is not True or type(count) is not int or count < 1
            or pdf.get('pages_reviewed') != list(range(1, count+1))
            or pdf.get('paper_pdf_sha256') != request['source_inventory_sha256']['paper.pdf']):
            raise ReconciliationError('Passing reconciliation requires complete exact PDF review')
    if current_source is not None and source_inventory(current_source) != request['source_inventory_sha256']:
        raise ReconciliationError('Current scientific source differs from reviewed snapshot')
    return {'run_id':request['run_id'], 'request_sha256':packet.name, 'review_sha256':digest(review_path.read_bytes()),
            'review_verdict':review['verdict'],
            'status':'SCIENTIFIC_HOLD' if review['verdict']=='HOLD' else 'RECONCILIATION_REVIEW_PASSED_SUCCESSOR_PACKAGE_REQUIRED',
            'findings':review['findings'], 'kernel_admission':False, 'publication_authorized':False,
            'production_activation':False, 'historical_artifacts_rewritten':False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', required=True)
    parser.add_argument('--author-invocation', required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.run, author_invocation=args.author_invocation), indent=2))
    except (ReconciliationError, OSError, ValueError) as error:
        print(json.dumps({'status':'HOLD_RECONCILIATION','reason':str(error)})); return 2
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
