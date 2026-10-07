"""Issue manuscript bookkeeping only from an exact passing existing post-Lean review.

No proof submission, Lean execution, certificate issuance or publication occurs.
Missing scope/model mappings and unknown sealed claim classes remain HOLD.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

from certificate_inspection import inspect_certificate
from claim_binding import check_bindings, read_object
from corpus_ledger import preserve_publication_registrations
from publication_binding import assessment, validate_publication_binding
from publication_gate import evaluate_publication, _premise_required


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _time(value):
    result = dt.datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('review chronology requires a timezone')
    return result


def _review_validator(root, artifact):
    """Reuse the installed publisher's existing exact-artifact review consumer."""
    path = root/'_ZENODO_DEPOSITS/weekend_canon_lockstep.py'
    sys.path.insert(0, str(path.parent))
    name = '_viridis_existing_post_lean_review_consumer'
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        papers = list(artifact.glob('*.pdf'))
        if len(papers) != 1:
            raise ValueError('one exact final PDF required')
        module.load_post_aristotle_review(artifact, papers[0],
            [artifact/'VERIFICATION_CANDIDATE.lean', artifact/'VERIFICATION_STATEMENT.lean'],
            [artifact/'COMPARATOR_SUMMARY.md'])
    finally:
        sys.modules.pop(name, None)
        sys.path.remove(str(path.parent))


def prepare(root, run_id, artifact, *, inspector=None, review_validator=None, require_premise_declaration=False):
    """Read-only exact-input plan. Never creates a semantic claim map."""
    root, artifact = Path(root).resolve(), Path(artifact).resolve()
    result = {'standard': 'VRS-NIGHTLY-PUBLICATION-INTAKE-1', 'run_id': run_id,
              'status': 'HOLD', 'reasons': [], 'artifact': str(artifact),
              'local_lean_execution': False, 'zenodo_writes': False, 'certificate_issued': False}
    try:
        if re.fullmatch(r'Run-\d+', run_id) is None or not artifact.is_relative_to(root):
            raise ValueError('canonical nightly Run artifact required')
        ledger_path = root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
        ledger = read_object(ledger_path)
        if Path(ledger['tree_root']).resolve() != root:
            raise ValueError('ledger tree root mismatch')
        require_premise_declaration = _premise_required(ledger, {'run_id': run_id}, require_premise_declaration)
        runs = [r for r in ledger['run_entities'] if r['id'] == run_id]
        if len(runs) != 1 or runs[0].get('status') != 'CERTIFIED':
            raise ValueError('Run lacks one current parity-qualified certificate')
        certificate = (root/runs[0]['certificate']).resolve(strict=True)
        inspection = (inspector or inspect_certificate)(certificate, root)
        if inspection.get('valid') is not True or inspection.get('run_id') != run_id:
            raise ValueError('certificate failed current Run/hash inspection')
        from premise_declaration import validate_artifact
        premise=validate_artifact(artifact,inspection,certificate,root,required=require_premise_declaration)
        if premise['status'] not in {'PASS','EXEMPT'}:
            raise ValueError('INV-9 HOLD: '+'; '.join(premise['reasons']))
        review_path, map_path = artifact/'POST_ARISTOTLE_REVIEW.json', artifact/'claim_binding.json'
        review = read_object(review_path)
        if review.get('verdict') != 'pass':
            raise ValueError('post-Lean review is not passing: '+str(review.get('hold', {}).get('code', 'verdict')))
        (review_validator or _review_validator)(root, artifact)
        independent = review.get('independent_checks', {})
        if independent.get('review_complete') is not True or independent.get('rendering_defects') != 0:
            raise ValueError('exact final PDF correspondence review is incomplete')
        if not review.get('reviewer_system') or not review.get('reviewer_model'):
            raise ValueError('reviewer provenance required')
        evidence = review.get('reviewed_evidence_sha256', {})
        if evidence.get('LEAN_ZERO_SORRY_CERTIFICATE.json') != sha(certificate):
            raise ValueError('post-Lean review does not bind the current certificate')
        # A review must explicitly bind the supplied scope/model assignments;
        # matching theorem names alone cannot establish manuscript completeness.
        if evidence.get('claim_binding.json') != sha(map_path):
            raise ValueError('post-Lean review does not bind the explicit claim map')
        if evidence.get('paper.tex') != sha(next(artifact.glob('*.tex'))):
            raise ValueError('post-Lean review does not bind the exact final TeX')
        issued = _time(read_object(certificate)['issued_at_utc'])
        reviewed = _time(review['reviewed_at_utc'])
        if not issued <= reviewed <= dt.datetime.now(dt.timezone.utc):
            raise ValueError('post-Lean review chronology invalid')
        entry = {'id': 'publication:nightly-'+run_id, 'kind': 'PUBLICATION', 'entity_type': 'PUBLICATION',
                 'path': str(artifact.relative_to(root)), 'run_id': run_id, 'status': 'CERTIFIED',
                 'certificate_valid': True, 'certificate': str(certificate.relative_to(root)),
                 'certificate_sha256': sha(certificate)}
        if premise['status']=='PASS':entry['foundation_basis']=premise['foundation_basis']
        claims = check_bindings(read_object(map_path), entry, ledger, inspector=inspector)
        if claims['status'] != 'PASS':
            raise ValueError('claim-binding HOLD: '+'; '.join(claims['reasons']))
        current = assessment(artifact, inspection, certificate, root)
        diff = current['classified_diff']
        if diff['classification'] != 'VERIFICATION_STATUS_ONLY' or diff['status'] != 'CLASSIFIED' or diff.get('protected_changes'):
            raise ValueError('final manuscript differs beyond verification-status text')
        result.update(status='READY_FOR_AUTHORIZED_REGISTRATION', ledger_sha256=sha(ledger_path),
                      certificate=current['certificate'], post_lean_review={'path': str(review_path), 'sha256': sha(review_path)},
                      claim_map={'path': str(map_path), 'sha256': sha(map_path)}, assessment=current,
                      claim_gate=claims, entry=entry, reviewer={'identity': review['reviewer_system'], 'model': review['reviewer_model']},
                      reviewed_at_utc=review['reviewed_at_utc'])
        if premise['status']=='PASS':result['foundation_basis']=premise['foundation_basis']
    except Exception as exc:
        result['reasons'].append(type(exc).__name__+': '+str(exc))
    return result


def apply(root, run_id, artifact, output, *, expected_ledger_sha256, inspector=None, review_validator=None,
          require_premise_declaration=False):
    """Explicit local registration. Refuse overwrites and any input drift."""
    root, output = Path(root).resolve(), Path(output).resolve()
    if not output.is_relative_to(root/'RESEARCH_PIPELINE_v2/publication_releases') or output.exists():
        raise ValueError('new immutable canonical publication release directory required')
    plan = prepare(root, run_id, artifact, inspector=inspector, review_validator=review_validator,
                   require_premise_declaration=require_premise_declaration)
    if plan['status'] != 'READY_FOR_AUTHORIZED_REGISTRATION':
        return plan
    if plan['ledger_sha256'] != expected_ledger_sha256:
        raise ValueError('authoritative ledger changed before registration')
    ledger_path = root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'
    old = read_object(ledger_path)
    if any(e.get('id') == plan['entry']['id'] for e in old.get('publication_entities', [])):
        raise ValueError('nightly publication identity already registered; validate existing entry instead')
    output.mkdir(parents=True, exist_ok=False)
    artifact = Path(artifact).resolve()
    # Preserve immutable source and proof inputs; no .lake/cache, credentials,
    # mutable draft or production evidence is copied.
    for path in artifact.iterdir():
        if path.is_file() and (path.suffix in {'.pdf', '.tex'} or path.name in {
            'claim_binding.json', 'VERIFICATION_CANDIDATE.lean', 'VERIFICATION_STATEMENT.lean',
            'COMPARATOR_SUMMARY.md', 'POST_ARISTOTLE_REVIEW.json'}):
            if path.is_symlink():
                raise ValueError('release input symlink refused')
            shutil.copyfile(path, output/path.name)
    certificate = Path(plan['certificate']['path'])
    inspection = (inspector or inspect_certificate)(certificate, root)
    current = assessment(output, inspection, certificate, root)
    for key in ('certificate', 'sealed_manuscript', 'final_manuscript', 'final_pdf_sha256', 'final_tex_sha256', 'allowed_diff_sha256', 'diff_classification'):
        if current[key] != plan['assessment'][key]:
            raise ValueError('release input changed while copying: '+key)
    if sha(output/'claim_binding.json') != plan['claim_map']['sha256'] or sha(output/'POST_ARISTOTLE_REVIEW.json') != plan['post_lean_review']['sha256']:
        raise ValueError('reviewed claim map or post-Lean review changed while copying')
    review = {key: current[key] for key in ('certificate', 'final_manuscript', 'allowed_diff_sha256')}
    review.update(status='APPROVED_PUBLICATION_BINDING', scope='VERIFICATION_STATUS_TEXT_ONLY', pdf_correspondence_reviewed=True,
                  reviewer=plan['reviewer'], reviewed_at_utc=plan['reviewed_at_utc'],
                  source_post_lean_review=plan['post_lean_review'], authorized_rule='GAME_PLAN.md full-completion authorization')
    rp = output/'PUBLICATION_BINDING_REVIEW.json'; rp.write_text(json.dumps(review, sort_keys=True, indent=2)+'\n')
    receipt = {**current, 'status': 'PUBLICATION_BOUND', 'issued_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
               'review': {'path': str(rp), 'sha256': sha(rp)}, 'issued_after_certification': True,
               'publication_authorized': False, 'proof_verifier': 'UNCHANGED_COMPARATOR', 'zenodo_writes': False}
    (output/'PUBLICATION_BINDING.json').write_text(json.dumps(receipt, sort_keys=True, indent=2)+'\n')
    validate_publication_binding(output, inspection, certificate, root, [sha(rp)])
    entry = {**plan['entry'], 'path': str(output.relative_to(root)), 'approved_publication_binding_reviews': [sha(rp)]}
    proposed = {**old, 'publication_entities': old.get('publication_entities', [])+[entry]}
    fresh = preserve_publication_registrations(json.loads(json.dumps(old)), proposed)
    gate = evaluate_publication(output, fresh, entity_id=entry['id'], inspector=inspector, enforce=True)
    if gate['status'] != 'PASS':
        raise ValueError('new registration fails publication gate: '+'; '.join(gate['reasons']))
    if sha(ledger_path) != expected_ledger_sha256:
        raise ValueError('authoritative ledger changed during registration')
    audit = output/'registration_audit'; audit.mkdir()
    shutil.copyfile(ledger_path, audit/'corpus_ledger_before.json')
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=ledger_path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(json.dumps(fresh, ensure_ascii=False, sort_keys=True, indent=2)+'\n'); handle.flush(); os.fsync(handle.fileno())
    os.replace(temporary, ledger_path)
    return {**plan, 'status': 'PUBLICATION_BOUND_REGISTERED', 'release': str(output),
            'publication_binding_sha256': sha(output/'PUBLICATION_BINDING.json'), 'publication_gate': gate}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True); parser.add_argument('--run-id', required=True)
    parser.add_argument('--artifact', type=Path, required=True)
    parser.add_argument('--apply-authorized-registration', action='store_true')
    parser.add_argument('--output', type=Path); parser.add_argument('--expected-ledger-sha256')
    parser.add_argument('--require-premise-declaration', action='store_true')
    args = parser.parse_args()
    try:
        if args.apply_authorized_registration:
            if args.output is None or args.expected_ledger_sha256 is None:
                raise ValueError('explicit registration requires immutable output and expected ledger SHA-256')
            result = apply(args.root, args.run_id, args.artifact, args.output, expected_ledger_sha256=args.expected_ledger_sha256,
                           require_premise_declaration=args.require_premise_declaration)
        else:
            result = prepare(args.root, args.run_id, args.artifact, require_premise_declaration=args.require_premise_declaration)
    except Exception as exc:
        result = {'status': 'HOLD', 'reasons': [type(exc).__name__+': '+str(exc)], 'zenodo_writes': False, 'local_lean_execution': False}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result['status'] in {'READY_FOR_AUTHORIZED_REGISTRATION', 'PUBLICATION_BOUND_REGISTERED'} else 2


if __name__ == '__main__': raise SystemExit(main())
