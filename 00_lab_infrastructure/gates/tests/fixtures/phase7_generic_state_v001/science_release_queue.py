"""Report-only, certificate-specific release intake. No publication transport or verifier."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

DEFAULT_ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
SCHEMA = 'VRS-SCIENCE-RELEASE-QUEUE-1'
PAPER_ROOT = Path('science-engine/07_nightly_engine/compound research papers')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_json(value):
    return json.dumps(value, indent=2, sort_keys=True).encode() + b'\n'


def run_id(value):
    if re.fullmatch(r'Run-[0-9]{3}', str(value)) is None:
        raise ValueError('canonical Run-NNN identity required')
    return str(value)


def contained_file(root, path):
    root, path = Path(root).resolve(strict=True), Path(path)
    if not path.is_absolute():
        path = root / path
    if not path.is_file() or path.is_symlink() or not path.resolve(strict=True).is_relative_to(root):
        raise ValueError('missing, symlinked or out-of-tree file: ' + str(path))
    return path.resolve()


def full_directory_snapshot(root, directory):
    root, directory = Path(root).resolve(strict=True), Path(directory)
    if directory.is_symlink() or not directory.is_dir() or not directory.resolve().is_relative_to(root):
        raise ValueError('missing, symlinked or out-of-tree run directory')
    files = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink():
            raise ValueError('run directory contains a symlink')
        if path.is_file():
            files[str(path.relative_to(directory))] = digest(path)
    if not files:
        raise ValueError('empty run source directory')
    return files


def load_existing_consumers(root):
    """Load canonical existing consumers only; no CLI substitution of verifier code."""
    root = Path(root).resolve(strict=True)
    pipeline = root / 'RESEARCH_PIPELINE_v2'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(pipeline))
    result = {}
    for name, relative in (('proof_track', 'nightly_proof_track.py'),
                           ('inspection', 'verification_coverage_gates/certificate_inspection.py')):
        path = contained_file(root, pipeline / relative)
        spec = importlib.util.spec_from_file_location('release_intake_' + name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result[name] = module
        result[name + '_binding'] = {'path': str(path), 'sha256': digest(path)}
    return result


def published_run_joins(root, ledger, target_run=None):
    """A missing SSOT row cannot make a deposited run unpublished."""
    root = Path(root).resolve(strict=True)
    joined = {}
    for entity in ledger.get('publication_entities', []):
        if entity.get('doi') and (target_run is None or entity.get('run_id') == target_run):
            joined.setdefault(entity.get('run_id'), set()).add(entity['doi'])
    for directory in sorted((root / '_ZENODO_DEPOSITS').glob('*')):
        if not directory.is_dir() or directory.is_symlink():
            continue
        for filename in ('RELEASE_BINDING.json', 'LEDGER_BINDING.json', 'BUNDLE_MANIFEST.json'):
            path = directory / filename
            if not path.is_file():
                continue
            contained_file(root, path)
            item = json.loads(path.read_text())
            identity = item.get('run_id')
            if re.fullmatch(r'Run-[0-9]{3}', str(identity)) and (target_run is None or identity == target_run):
                pointer = directory / 'PUBLISHED_DOI.txt'
                if not pointer.is_file():
                    break
                contained_file(root, pointer)
                doi = pointer.read_text().strip()
                if re.fullmatch(r'10\.5281/zenodo\.[1-9][0-9]*', doi) is None:
                    raise ValueError('malformed published DOI pointer for ' + identity)
                joined.setdefault(identity, set()).add(doi)
                break
    return {identity: sorted(dois) for identity, dois in joined.items()}


def prepare_entry(root, identity, ledger, current, inspection, consumers, public_joins):
    """Pure preparation; the canonical loader supplies unchanged consumers in the CLI."""
    root, identity = Path(root).resolve(strict=True), run_id(identity)
    if ledger.get('tree_root') != str(root):
        raise ValueError('ledger tree root differs')
    matches = [row for row in ledger.get('run_entities', []) if row.get('id') == identity]
    if len(matches) != 1:
        raise ValueError('run must match exactly one SSOT entity')
    row = matches[0]
    relative = Path(row.get('path', ''))
    if relative.is_absolute() or relative.parent != PAPER_ROOT or not relative.name.startswith(identity + '_'):
        raise ValueError('run source DIR differs from declared mirror run path')
    directory = root / relative
    parity = row.get('parity', {})
    if parity.get('status') != 'MATCH' or parity.get('mirror') != str(directory):
        raise ValueError('ledger source/mirror parity is not MATCH for this DIR')
    files = full_directory_snapshot(root, directory)
    recorded = parity.get('mirror_hashes')
    if not isinstance(recorded, dict) or files != recorded:
        raise ValueError('mirror file inventory changed since parity scan')
    if not current:
        raise ValueError('no current existing certificate')
    certificate_path, certificate = current
    certificate_path = contained_file(root, certificate_path)
    store = root / 'RESEARCH_PIPELINE_v2/lean_certificates' / identity
    if certificate_path.parent != store:
        raise ValueError('current certificate is outside declared canonical run cert store')
    if inspection.get('valid') is not True or inspection.get('recorded_certificate_current') is not True:
        raise ValueError('existing certificate consumer rejected current evidence')
    if inspection.get('run_id') != identity or inspection.get('path') != str(certificate_path):
        raise ValueError('certificate inspection identity/path differs')
    certificate_hash = digest(certificate_path)
    if inspection.get('sha256') != certificate_hash:
        raise ValueError('certificate bytes changed after inspection')
    if certificate.get('status') != 'LEAN_ZERO_SORRY_CERTIFIED' or certificate.get('run_id') != identity:
        raise ValueError('certificate status or run differs')
    bindings = []
    for binding in inspection.get('bindings', []):
        path = contained_file(root, binding['resolved_path'])
        if digest(path) != binding.get('sha256'):
            raise ValueError('certified input changed after inspection')
        bindings.append({'label': binding['label'], 'path': str(path), 'sha256': binding['sha256']})
    labels = {binding['label'] for binding in bindings}
    required = {'bindings.candidate_proof', 'bindings.formal_statement', 'bindings.request',
                'bindings.independent_cloud_receipt', 'bindings.sealed_paper_inputs.SEALED_paper.tex',
                'bindings.sealed_paper_inputs.SEALED_paper.pdf'}
    if not required.issubset(labels):
        raise ValueError('current certificate lacks exact sealed inputs')
    disposition_path = contained_file(root, directory / 'DISPOSITION.json')
    disposition = json.loads(disposition_path.read_text())
    kind = disposition.get('disposition', disposition.get('status'))
    if kind not in ('METHODS_NOTE', 'PAPER', 'FULL_PAPER'):
        raise ValueError('missing or unknown paper/Methods-Note disposition')
    assigned_run = disposition.get('run_id', disposition.get('run'))
    if assigned_run is not None and str(assigned_run) not in (identity, str(int(identity[4:]))):
        raise ValueError('disposition belongs to a different run')
    try:
        issued = dt.datetime.fromisoformat(certificate['issued_at_utc'].replace('Z', '+00:00'))
        if issued.tzinfo is None:
            raise ValueError('timezone required')
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('certificate issue time cannot determine digest week') from exc
    year, week, _ = issued.astimezone(ZoneInfo('America/New_York')).isocalendar()
    digest_week = f'{year}-W{week:02d}'
    prior_dois = public_joins.get(identity, [])
    route = 'WEEKLY_METHODS_DIGEST' if kind == 'METHODS_NOTE' else 'SCOPED_SUCCESSOR_REVIEW' if prior_dois else 'STANDALONE_PAPER_REVIEW'
    stale = disposition.get('formal_status') == 'FROZEN_CANDIDATE_UNCERTIFIED'
    return {'schema': SCHEMA, 'mode': 'REPORT_ONLY', 'run_id': identity,
        'entry_id': identity + '-' + certificate_hash, 'certificate': {'path': str(certificate_path), 'sha256': certificate_hash},
        'candidate_sha256': inspection['candidate_sha256'], 'certified_inputs': sorted(bindings, key=lambda b:b['label']),
        'source_dir': str(directory), 'source_hashes': files,
        'source_inventory_sha256': hashlib.sha256(canonical_json(files)).hexdigest(),
        'parity_status': 'MATCH', 'ssot_status_observed': row.get('status'),
        'ssot_successor_reconciliation_needed': row.get('certificate') != str(certificate_path) or row.get('certificate_valid') is not True,
        'disposition': kind, 'disposition_binding': {'path': str(disposition_path), 'sha256': digest(disposition_path)},
        'append_only_disposition_correction_needed': stale, 'route': route, 'digest_week': digest_week,
        'existing_public_dois': prior_dois, 'duplicate_standalone_allowed': False,
        'state': 'PENDING_WHOLE_PAPER_SCOPE_REVIEW_AND_INDEPENDENT_AUDIT',
        'publish_time_binding_required': True, 'publication_enabled': False,
        'independent_review_required': 'Claude spot-audit of the exact consolidated release packet before first publication batch',
        'automatic_publication_calls': 0, 'verifier_of_record': 'Existing Viridis Comparator; queue cannot certify or approve claims',
        'consumer_bindings': consumers}


def write_immutable(path, value):
    path = Path(path)
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        raise ValueError('immutable queue output cannot traverse symlinks')
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_json(value)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if path.read_bytes() != raw:
            raise ValueError('existing immutable certificate-specific entry differs; HOLD, no overwrite')
        return False
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return True


def enqueue(root, identity, ledger_path, queue_dir=None):
    identity = run_id(identity)  # Validate before using the identity in any filename.
    root = Path(root).resolve(strict=True)
    ledger_path = contained_file(root, ledger_path)
    queue_dir = Path(queue_dir or root / 'RESEARCH_PIPELINE_v2/science_release_queue')
    if queue_dir.is_symlink() or not queue_dir.resolve().is_relative_to(root):
        raise ValueError('durable queue must stay inside canonical root')
    ledger_hash = digest(ledger_path)
    ledger = json.loads(ledger_path.read_text())
    try:
        modules = load_existing_consumers(root)
        current = modules['proof_track'].current_certificate(root, run_id(identity))
        inspection = modules['inspection'].inspect_certificate(current[0], root) if current else None
        entry = prepare_entry(root, identity, ledger, current, inspection,
            {'proof_track': modules['proof_track_binding'], 'inspection': modules['inspection_binding']},
            published_run_joins(root, ledger, identity))
        if digest(ledger_path) != ledger_hash:
            raise ValueError('ledger changed while preparing queue entry')
        if full_directory_snapshot(root, Path(entry['source_dir'])) != entry['source_hashes']:
            raise ValueError('source DIR changed while preparing queue entry')
        if digest(entry['certificate']['path']) != entry['certificate']['sha256'] or any(
                digest(binding['path']) != binding['sha256'] for binding in entry['certified_inputs']):
            raise ValueError('certificate or sealed input changed before queue persistence')
        filename = queue_dir / 'entries' / (entry['entry_id'] + '.json')
        created = write_immutable(filename, entry)
        return {'status':'ENQUEUED_REPORT_ONLY' if created else 'ALREADY_ENQUEUED_SAME_CERTIFICATE_AND_SOURCE_BYTES',
            'run_id': identity, 'entry':str(filename), 'entry_sha256':digest(filename), 'publication_enabled':False,
            'ledger_at_intake':{'path':str(ledger_path),'sha256':ledger_hash}, 'production_writes':0}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        hold = {'schema':SCHEMA,'status':'HOLD','run_id':str(identity),'cause':str(exc),'publication_enabled':False,
            'ledger_at_intake':{'path':str(ledger_path),'sha256':ledger_hash},'production_writes':0}
        hold_hash = hashlib.sha256(canonical_json(hold)).hexdigest()
        write_immutable(queue_dir / 'holds' / (str(identity) + '-' + hold_hash + '.json'), hold)
        return hold


def require_independent_packet_review(root, packet_path, review_path):
    """A pre-write prerequisite only; this never substitutes for publication_gate."""
    packet = contained_file(root, packet_path)
    review = contained_file(root, review_path)
    value = json.loads(review.read_text())
    if value.get('reviewer_system') != 'Claude' or value.get('status') != 'PASS':
        raise ValueError('independent Claude packet PASS required before publication')
    binding = value.get('release_packet', {})
    if binding.get('path') != str(packet) or binding.get('sha256') != digest(packet):
        raise ValueError('independent review must bind the exact release packet bytes')
    return {'status':'INDEPENDENT_REVIEW_PREREQUISITE_ONLY','packet_sha256':digest(packet),
            'review_sha256':digest(review),'publication_gate_still_required':True}


def require_canonical_cli_root(root):
    resolved = Path(root).resolve(strict=True)
    if resolved != DEFAULT_ROOT.resolve(strict=True):
        raise ValueError('production CLI accepts only the canonical Cowork certification root')
    return resolved



def scan_new_nightly(root, ledger_path, since, queue_dir=None, *, stage=False):
    """Catch every newly certified generated run, including delayed receipts."""
    minimum=int(run_id(since)[4:])
    if not 1 <= minimum < 899:raise ValueError('nightly cutover required; foundational runs are opt-in')
    root=Path(root).resolve(strict=True);ledger_path=contained_file(root,ledger_path)
    ledger=json.loads(ledger_path.read_text());modules=load_existing_consumers(root);rows=[]
    for row in ledger.get('run_entities',[]):
        identity=row.get('id')
        if not isinstance(identity,str) or not re.fullmatch(r'Run-[0-9]{3}',identity):continue
        if not minimum<int(identity[4:])<900:continue
        current=modules['proof_track'].current_certificate(root,identity)
        if not current:continue  # Intake handles certified runs; coverage retains proof debt.
        result=enqueue(root,identity,ledger_path,queue_dir)
        if stage and result['status']!='HOLD':
            try:
                from science_release_stage import stage_current_entry
                result['scope_package']=stage_current_entry(root,result['entry'],ledger_path)
            except Exception as exc:
                result.update(status='HOLD',cause=type(exc).__name__+': '+str(exc),publication_enabled=False)
        rows.append(result)
    return {'status':'HOLD' if any(r['status']=='HOLD'for r in rows)else'REPORT_ONLY_SCAN_COMPLETE',
        'since':since,'rows':rows,'publication_enabled':False,'production_writes':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    selection=parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--run')
    selection.add_argument('--scan-certified-since', help='report-only intake for generated nightly runs after the approved cutover')
    parser.add_argument('--ledger', type=Path)
    parser.add_argument('--queue-dir', type=Path)
    parser.add_argument('--stage', action='store_true', help='build the immutable narrowed review package; never publish')
    args = parser.parse_args()
    try:
        root = require_canonical_cli_root(args.root)
        ledger_path = args.ledger or root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        if args.scan_certified_since:
            result=scan_new_nightly(root,ledger_path,args.scan_certified_since,args.queue_dir,stage=args.stage)
        else:
            result=enqueue(root,args.run,ledger_path,args.queue_dir)
        if args.stage and not args.scan_certified_since and result['status'] != 'HOLD':
            from science_release_stage import stage_current_entry
            result['scope_package'] = stage_current_entry(root, result['entry'], ledger_path)
    except Exception as exc:
        result = {'status':'HOLD','cause':str(exc),'publication_enabled':False,'production_writes':0}
    print(json.dumps(result,indent=2,sort_keys=True))
    return 1 if result['status']=='HOLD' else 0


if __name__ == '__main__':
    raise SystemExit(main())
