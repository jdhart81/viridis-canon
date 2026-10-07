#!/usr/bin/env python3
"""Report-only v3 coverage of the canonical control plane; no new verification."""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
from certificate_inspection import inspect_certificate, pipeline_modules
from certificate_selection import certificate_selection_paths
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


def _review_hashes(value):
    if not isinstance(value, list) or not value or any(not isinstance(h, str) or re.fullmatch(r'[0-9a-f]{64}', h) is None for h in value):
        raise ValueError('explicit nonempty SHA-256 review approval list required')
    if len(set(value)) != len(value):
        raise ValueError('duplicate review approvals')
    return value


def validate_uncertified_readback(root, entity):
    """Read an exact authenticated public GET receipt; never infer a banner."""
    from release_packet import LABEL
    root = Path(root).resolve()
    proof = entity.get('public_uncertified_readback')
    if not isinstance(proof, dict) or proof.get('authenticated') is not True:
        raise ValueError('authenticated public UNCERTIFIED readback required')
    rid = proof.get('record_id')
    if not isinstance(rid, str) or re.fullmatch(r'[1-9][0-9]*', rid) is None:
        raise ValueError('canonical public readback record ID required')
    if entity.get('doi') != '10.5281/zenodo.' + rid:
        raise ValueError('public readback DOI/entity join differs')
    relative = proof.get('receipt_path')
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('tree-relative public readback receipt required')
    path = root / relative
    receipt_path = path.resolve(strict=True)
    if not receipt_path.is_relative_to(root) or path.is_symlink() or not receipt_path.is_file():
        raise ValueError('public readback receipt outside tree or a symlink')
    raw = receipt_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if proof.get('receipt_sha256') != digest:
        raise ValueError('public readback receipt SHA-256 changed')
    receipt = json.loads(raw)
    if not isinstance(receipt, dict):
        raise ValueError('public readback receipt object required')
    parsed = urlsplit(receipt.get('url', ''))
    if (receipt.get('method') != 'GET' or receipt.get('environment') != 'zenodo.org'
        or receipt.get('http_status') != 200 or receipt.get('status') != 'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'
        or parsed.scheme != 'https' or parsed.netloc != 'zenodo.org'
        or parsed.path != '/api/records/' + rid or parsed.query or parsed.fragment):
        raise ValueError('successful own-record public GET receipt required')
    response_hash = receipt.get('response_sha256')
    if not isinstance(response_hash, str) or re.fullmatch(r'[0-9a-f]{64}', response_hash) is None or proof.get('response_sha256') != response_hash:
        raise ValueError('hash-bound public response required')
    response = receipt.get('response')
    if not isinstance(response, dict) or type(response.get('id')) not in (str, int) or str(response['id']) != rid:
        raise ValueError('public readback record identity differs')
    if ('is_published' in response and response['is_published'] is not True) or ('is_published' not in response and not (response.get('state') == 'done' and response.get('submitted') is True)):
        raise ValueError('published public record readback required')
    metadata = response.get('metadata')
    description = metadata.get('description') if isinstance(metadata, dict) else None
    if not isinstance(description, str):
        raise ValueError('public readback description required')
    class Text(HTMLParser):
        def __init__(self):super().__init__();self.data=[]
        def handle_data(self, value):self.data.append(value)
    text = Text(); text.feed(description)
    plain = ' '.join(' '.join(text.data).split())
    label = ' '.join(LABEL.split())
    if not plain.startswith(label) or plain.count(label) != 1:
        raise ValueError('public record lacks exactly one leading UNCERTIFIED banner')
    return {'status': 'PUBLIC_UNCERTIFIED_BANNER_READBACK_PASS', 'record_id': rid,
            'receipt_sha256': digest, 'response_sha256': response_hash}


def _publication_registration_status(ledger, entity):
    """Claim eligibility is separate from the existing proof-qualified status."""
    from publication_gate import evaluate_publication
    entity.update(publication_registration_status='HOLD', enforcement_acceptable=False)
    if entity.get('status') != 'CERTIFIED' or entity.get('certificate_valid') is not True or entity.get('publication_binding_status') != 'PUBLICATION_BOUND':
        entity['publication_registration_reasons'] = ['proof or manuscript binding is held']
        return
    root = Path(ledger['tree_root']).resolve()
    artifact = root / entity['path']
    claim_map = artifact / 'claim_binding.json'
    if (not claim_map.exists() and not claim_map.is_symlink()
            and not (artifact/'SCOPED_RELEASE_MANIFEST.json').exists()
            and not (artifact/'SCOPED_RELEASE_MANIFEST.json').is_symlink()):
        entity.update(publication_registration_status='HOLD_NO_CLAIM_MAP',
                      publication_registration_reasons=['claim_binding.json is absent; manuscript binding is not claim approval'])
        try:
            entity['public_uncertified_banner'] = validate_uncertified_readback(root, entity)
            entity['enforcement_acceptable'] = True
        except Exception as exc:
            entity['public_uncertified_banner'] = {'status':'HOLD', 'reason':type(exc).__name__ + ': ' + str(exc)}
        return
    result = evaluate_publication(artifact, ledger, entity_id=entity['id'], inspector=inspect_certificate)
    entity['publication_registration_reasons'] = list(result.get('reasons', []))
    if result.get('status') == 'PASS' and result.get('exact_publication_binding') is True:
        entity.update(publication_registration_status='PASS', enforcement_acceptable=True)


def write_guarded_ledger(path, ledger, expected_sha256):
    """Atomically replace only the exact recorded predecessor, never a live edit."""
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('existing non-symlink authoritative ledger required')
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError('concurrent authoritative ledger SHA-256 changed')
    payload = (json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()
    descriptor, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    temporary = Path(name)
    try:
        os.fchmod(descriptor, path.stat().st_mode & 0o777)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(payload); stream.flush(); os.fsync(stream.fileno())
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
            raise ValueError('concurrent authoritative ledger SHA-256 changed before replace')
        os.replace(temporary, path)
        digest = hashlib.sha256(payload).hexdigest()
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('authoritative ledger post-write readback mismatch')
        return digest
    finally:
        temporary.unlink(missing_ok=True)


def preserve_publication_registrations(ledger, previous):
    """Revalidate exact approved releases; never infer approval from a Run join.

    The authoritative ledger carries approval hashes between coverage scans. A
    current certificate, manuscript or receipt alone cannot create an approval.
    Invalid registrations stay visible as held entities rather than disappearing.
    """
    root = Path(ledger['tree_root']).resolve()
    publications = []
    ledger['publication_entities'] = publications
    ledger['publication_holds'] = []
    ledger['publication_registration_summary'] = {}
    ledger['publication_registration_enforcement_acceptable'] = False
    ledger['publication_registration_defects'] = []
    if isinstance(previous, dict) and 'premise_declaration_cutover_run' in previous:
        value = previous['premise_declaration_cutover_run']
        if not isinstance(value, str) or re.fullmatch(r'Run-\d+', value) is None or value != f'Run-{int(value[4:]):03d}' or not 1 <= int(value[4:]) < 900:
            raise ValueError('invalid recorded premise-declaration nightly cutover')
        ledger['premise_declaration_cutover_run'] = value
    if isinstance(previous, dict) and 'enforcement_activation' in previous:
        from nightly_coverage import activation_binding, _source_path, _load_source, ACTIVATION_STANDARD
        evidence = activation_binding(previous['enforcement_activation'])
        if not Path(evidence['path']).is_relative_to('reports/verification-coverage'):
            raise ValueError('recorded activation outside canonical reports root')
        _source_path(root, evidence)
        receipt = _load_source(root, evidence)
        if (receipt.get('standard') != ACTIVATION_STANDARD or receipt.get('status') != 'ENFORCEMENT_ACTIVATED'
                or receipt.get('tree_root') != str(root)
                or receipt.get('premise_declaration_cutover_run') != ledger.get('premise_declaration_cutover_run')):
            raise ValueError('recorded activation receipt identity/cutover changed')
        ledger['enforcement_activation'] = evidence
    if previous is None:
        return ledger
    if not isinstance(previous, dict) or Path(str(previous.get('tree_root', ''))).resolve() != root:
        raise ValueError('prior authoritative ledger has a different tree root')
    prior_entities = previous.get('publication_entities', [])
    if not isinstance(prior_entities, list) or any(not isinstance(e, dict) for e in prior_entities):
        raise ValueError('malformed prior publication entity table')
    from publication_binding import validate_publication_binding
    identities = {e['id'] for table in ('file_entities', 'run_entities') for e in ledger[table]}
    paths = {(root / e['path']).resolve() for table in ('file_entities', 'run_entities') for e in ledger[table]}
    for original in prior_entities:
        entity = dict(original)
        eid, relative = entity.get('id'), entity.get('path')
        if not isinstance(eid, str) or not eid or eid in identities:
            raise ValueError('missing or duplicate publication entity identity')
        if not isinstance(relative, str) or not relative:
            raise ValueError('publication entity has no exact artifact path')
        artifact_path = root / relative
        artifact = artifact_path.resolve()
        if not artifact.is_relative_to(root) or artifact in paths:
            raise ValueError('publication entity path is outside the tree or ambiguous')
        identities.add(eid); paths.add(artifact)
        entity.update(kind='PUBLICATION', entity_type='PUBLICATION')
        try:
            if original.get('status') != 'CERTIFIED' or original.get('certificate_valid') is not True:
                raise ValueError('registration is held; an explicit approved re-registration is required')
            if not artifact.is_dir() or artifact_path.is_symlink():
                raise ValueError('registered publication artifact is missing or a symlink')
            reviews = _review_hashes(original.get('approved_publication_binding_reviews'))
            value = original.get('certificate')
            if not isinstance(value, str) or not value:
                raise ValueError('registered publication certificate path required')
            certificate_path = root / value
            certificate = certificate_path.resolve(strict=True)
            if not certificate.is_relative_to(root) or certificate_path.is_symlink():
                raise ValueError('registered certificate is outside the tree or a symlink')
            inspected = inspect_certificate(certificate, root)
            if inspected.get('valid') is not True:
                raise ValueError('registered certificate failed fresh inspection')
            if original.get('certificate_sha256') != hashlib.sha256(certificate.read_bytes()).hexdigest():
                raise ValueError('registered certificate SHA-256 is missing or changed')
            rid = original.get('run_id')
            if not isinstance(rid, str) or re.fullmatch(r'Run-\d+', rid) is None or inspected.get('run_id') != rid:
                raise ValueError('registered Run join differs from the certificate')
            candidate = scan(Path(inspected['candidate_path']))
            if candidate.get('static_pass') is not True:
                raise ValueError('registered certified candidate fails static pre-gate')
            if int(rid[4:]) < 900:
                runs = [r for r in ledger['run_entities'] if r['id'] == rid]
                if len(runs) != 1 or runs[0]['status'] != 'CERTIFIED':
                    raise ValueError('registered publication Run has no current parity-qualified certificate')
            papers = validate_publication_binding(artifact, inspected, certificate, root, reviews)
            entity.update(certificate_valid=True, publication_binding_status='PUBLICATION_BOUND', paper_bindings=papers,
                          certified_theorems=inspected.get('certified_theorems', []), nonvacuity=inspected.get('nonvacuity', []),
                          registration_revalidated=True, reasons=[])
        except Exception as exc:
            entity.update(status='DEBT', certificate_valid=False, publication_binding_status='HOLD', registration_revalidated=False,
                          reasons=[type(exc).__name__ + ': ' + str(exc)])
            ledger['publication_holds'].append({'id':eid, 'reasons':entity['reasons']})
        publications.append(entity)
    for entity in publications:
        _publication_registration_status(ledger, entity)
    ledger['publication_registration_summary'] = dict(Counter(e['publication_registration_status'] for e in publications))
    ledger['publication_registration_enforcement_acceptable'] = bool(publications) and all(e.get('enforcement_acceptable') is True for e in publications)
    ledger['publication_registration_defects'] = [e['id'] for e in publications if e.get('enforcement_acceptable') is not True]
    # A run's own approval is retained only for exactly the same artifact and
    # certificate, and only when its independently bound receipt still validates.
    prior_runs = previous.get('run_entities', [])
    if not isinstance(prior_runs, list):
        raise ValueError('malformed prior run entity table')
    for entity in ledger['run_entities']:
        matches = [old for old in prior_runs if isinstance(old, dict) and old.get('id') == entity['id']]
        if len(matches) != 1 or not matches[0].get('approved_publication_binding_reviews'):
            continue
        old = matches[0]
        if old.get('path') != entity.get('path') or old.get('certificate') != entity.get('certificate'):
            entity['publication_binding_status'] = 'HOLD_REGISTRATION_CHANGED'
            continue
        try:
            if entity.get('status') != 'CERTIFIED':
                raise ValueError('run certificate/parity no longer qualified')
            reviews = _review_hashes(old['approved_publication_binding_reviews'])
            certificate = (root / entity['certificate']).resolve(strict=True)
            if old.get('publication_certificate_sha256') != hashlib.sha256(certificate.read_bytes()).hexdigest():
                raise ValueError('run publication certificate hash is missing or changed')
            inspection = inspect_certificate(certificate, root)
            validate_publication_binding(root / entity['path'], inspection, certificate, root, reviews)
            entity['approved_publication_binding_reviews'] = list(reviews)
            entity['publication_certificate_sha256'] = old['publication_certificate_sha256']
            entity['publication_binding_status'] = 'PUBLICATION_BOUND'
        except Exception as exc:
            entity['publication_binding_status'] = 'HOLD'
            entity['publication_binding_reasons'] = [type(exc).__name__ + ': ' + str(exc)]
    return ledger


def build(root, cert_root, generation_root=GENERATION_ROOT, previous_ledger=None):
    root, cert_root = Path(root).resolve(), Path(cert_root).resolve()
    if not root.is_dir() or not cert_root.is_dir():
        raise ValueError('missing canonical root or certificate root')
    if previous_ledger is None:
        authoritative = root / 'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        if authoritative.is_file():
            if authoritative.is_symlink():
                raise ValueError('authoritative ledger symlink refused')
            previous_ledger = json.loads(authoritative.read_text())
    papers = root / 'science-engine/07_nightly_engine/compound research papers'
    if not papers.is_dir():
        raise ValueError('missing canonical nightly paper root: ' + str(papers))
    certs = [inspect_certificate(p, root) for p in certificate_selection_paths(
        root, cert_root, lambda tree, rid: pipeline_modules(tree)[0].current_certificate(tree, rid))]
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
    ledger = {'schema_version': 'verification-coverage-v4', 'mode': 'REPORT_ONLY', 'tree_root': str(root),
        'cert_root': str(cert_root), 'generation_root_parity_only': str(generation_root), 'priority': list(PRIORITY), 'errors': errors, 'excluded_latest': excluded,
        'trust_boundary': 'Existing hash-bound Comparator certificates only; static scans cannot certify.',
        'run_scope': 'Immutable certified envelope when available; original WIP/challenge copies remain separate FILE entities.',
        'file_counts': counts(file_entities), 'run_counts': counts(rows), 'synthesis_count': sum(r['kind']=='SYNTHESIS' for r in run_entities),
        'eligible_paper_runs': sum(r['status']!='MIRROR_DRIFT' for r in rows),
        'mirror_drift': [r['id'] for r in rows if r['status']=='MIRROR_DRIFT'],
        'receipt_era': {'certified': sum(r['status']=='CERTIFIED' for r in receipt), 'total': len(receipt)},
        'recorded_certificate_counts': {'present': len(certs), 'current_existing_consumer': sum(c.get('recorded_certificate_current', False) for c in certs), 'current_witness_evidence_pass': sum(c['valid'] for c in certs)},
        'certificates': certs, 'file_entities': file_entities, 'run_entities': run_entities}
    return preserve_publication_registrations(ledger, previous_ledger)


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
    lines += ['', '## Registered publication entities', '', '| Entity | Proof-qualified status | Binding status | Claim registration | Enforcement acceptable | Reasons |', '|---|---|---|---|---|---|']
    lines += [f"| {p['id']} | {p['status']} | {p.get('publication_binding_status', 'HOLD')} | {p.get('publication_registration_status', 'HOLD')} | {p.get('enforcement_acceptable', False)} | {'; '.join(p.get('reasons', []) + p.get('publication_registration_reasons', []))} |" for p in ledger.get('publication_entities', [])]
    lines += ['', 'Publication entities have a separate denominator; approved review hashes are revalidated and never inferred from a Run join.']
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
        if args.out.is_symlink():
            raise ValueError('ledger output symlink refused')
        predecessor = hashlib.sha256(args.out.read_bytes()).hexdigest() if args.out.is_file() else None
        ledger = build(args.root, cert_root, args.generation_root)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        if predecessor is None:
            with args.out.open('x', encoding='utf-8') as stream:
                stream.write(json.dumps(ledger, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
        else:
            write_guarded_ledger(args.out, ledger, predecessor)
        args.out.with_name('LEDGER.md').write_text(render_markdown(ledger))
    except Exception as exc:
        print(json.dumps({'status': 'HOLD', 'mode': 'REPORT_ONLY', 'reasons': [type(exc).__name__ + ': ' + str(exc)]}))
        return 1
    print(json.dumps({k: ledger[k] for k in ('file_counts','run_counts','receipt_era','synthesis_count','errors')}, indent=2))
    return 1 if ledger['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
