"""Additive REPORT_ONLY builder. Original science/certificate helpers unchanged.

This is not an installed source closure or scientific admission. The full old
historical closure may HOLD additional owned modules; never hide them to pass.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import types

GATES = Path(__file__).resolve().parent.parent
LEGACY_PINS = {
    'corpus_ledger.py':'497aa58f686c48389ef5b4d62e00fa2621cdf45eff45ace4d8e79202076e94cf',
    'run_flow.py':'00a6d309360aabda0e27f37a0cd757e103c1c502497b3f2553e28d2070b98b04',
}

def checked_source(path, expected):
    path=Path(path)
    if any(p.is_symlink()for p in(path,*path.parents)):raise ValueError('source symlink')
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    try:
        before=os.fstat(fd)
        if not stat.S_ISREG(before.st_mode)or before.st_size>2_000_000:raise ValueError('bounded regular source')
        raw=b''
        while len(raw)<=2_000_000:
            part=os.read(fd,min(65536,2_000_001-len(raw)))
            if not part:break
            raw+=part
        after=os.fstat(fd)
    finally:os.close(fd)
    frame=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
    if frame(before)!=frame(after)or frame(after)!=frame(path.lstat())or len(raw)!=before.st_size or hashlib.sha256(raw).hexdigest()!=expected:
        raise ValueError('source hash or identity changed')
    return raw

@contextmanager
def helper_search_path():
    before=list(sys.path)
    if str(GATES)not in sys.path:sys.path.insert(0,str(GATES))
    try:yield
    finally:sys.path[:]=before

def original_helpers():
    materials={n:checked_source(GATES/n,h)for n,h in LEGACY_PINS.items()}
    # Refuse a conflicting existing flow BEFORE Python can import it. No
    # canonical module object/function is replaced or patched by this module.
    cached=sys.modules.get('run_flow')
    if cached is not None and getattr(cached,'__file__',None)!=str(GATES/'run_flow.py'):
        raise ValueError('foreign cached original run_flow')
    module=types.ModuleType('_report_only_exact_original_corpus')
    module.__file__=str(GATES/'corpus_ledger.py')
    with helper_search_path():
        exec(compile(materials['corpus_ledger.py'],module.__file__,'exec'),module.__dict__)
    for n,h in LEGACY_PINS.items():checked_source(GATES/n,h)
    return module

_ORIGINAL=original_helpers()
GENERATION_ROOT=_ORIGINAL.GENERATION_ROOT
PRIORITY=_ORIGINAL.PRIORITY
inspect_certificate=_ORIGINAL.inspect_certificate
certificate_selection_paths=_ORIGINAL.certificate_selection_paths
pipeline_modules=_ORIGINAL.pipeline_modules
discover=_ORIGINAL.discover
scan=_ORIGINAL.scan
run_id=_ORIGINAL.run_id
file_status=_ORIGINAL.file_status
partition_status=_ORIGINAL.partition_status
run_parity=_ORIGINAL.run_parity
counts=_ORIGINAL.counts
flow=_ORIGINAL.flow
preserve_publication_registrations=_ORIGINAL.preserve_publication_registrations
render_markdown=_ORIGINAL.render_markdown

def lexical_membership_index(file_entities):
    """Same lexical Path.is_relative_to relation; preserve references/repeats.

    No resolve/stat/certificate caching, prefix strings, sorting or deduplication.
    Equal paths count as members, exactly as the original predicate does.
    """
    indexed={}
    for entity in file_entities:
        path=Path(entity['absolute_path'])
        for ancestor in (path,*path.parents):
            indexed.setdefault(ancestor,[]).append(entity)
    return indexed

def _indexed_build(root, cert_root, generation_root=GENERATION_ROOT, previous_ledger=None):
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
    membership = lexical_membership_index(file_entities)
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
        members = membership.get(path, [])
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


def build(root,cert_root,generation_root=GENERATION_ROOT,previous_ledger=None):
    # Only the new function runs; no old function or globals are monkeypatched.
    for name,pin in LEGACY_PINS.items():checked_source(GATES/name,pin)
    with helper_search_path():
        result=_indexed_build(root,cert_root,generation_root,previous_ledger)
    for name,pin in LEGACY_PINS.items():checked_source(GATES/name,pin)
    return result
