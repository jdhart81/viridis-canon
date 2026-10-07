"""Consume a separately approved manuscript binding. Never issue a proof certificate.

New receipts are drafts until an independent review hash is approved in the ledger.
This module is not installed in the production adapters.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from manuscript_structure import classify
from certificate_inspection import resolve_binding

STANDARD='VRS-PUBLICATION-BINDING-1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assessment(artifact, inspection, certificate, root):
    artifact=Path(artifact).resolve();root=Path(root).resolve();certificate=Path(certificate).resolve()
    if not artifact.is_relative_to(root) or not certificate.is_relative_to(root):raise ValueError('binding outside certification root')
    if inspection.get('valid') is not True:raise ValueError('proof certificate is not valid')
    sealed=inspection['sealed_paper_inputs']
    originals={name:resolve_binding(sealed['SEALED_paper.'+name],root) for name in ('tex','pdf')}
    files=sorted(p for p in artifact.iterdir() if p.is_file() and p.suffix in ('.tex','.pdf'))
    if any(p.is_symlink() for p in files):raise ValueError('manuscript symlink refused')
    if sorted(p.suffix for p in files)!=['.pdf','.tex']:raise ValueError('one final PDF and one final TeX required')
    final={p.suffix[1:]:p for p in files}
    before,after=originals['tex'].read_text(),final['tex'].read_text()
    if before==after:
        diff={'classification':'VERIFICATION_STATUS_ONLY','status':'CLASSIFIED','edits':[], 'protected_changes':[],
              'diff':'','classifier_version':'VRS-MANUSCRIPT-STRUCTURE-1','reason':'IDENTICAL_TEX'}
    else:diff=classify(before,after)
    encoded=json.dumps(diff,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    result={'standard':STANDARD,'certificate':{'path':str(certificate),'sha256':sha(certificate)},
            'sealed_manuscript':{name:{'path':str(p),'sha256':sha(p)} for name,p in originals.items()},
            'final_manuscript':{p.name:sha(p) for p in files},'final_pdf_sha256':sha(final['pdf']),
            'final_tex_sha256':sha(final['tex']),'allowed_diff_sha256':hashlib.sha256(encoded).hexdigest(),
            'diff_classification':diff['classification'],'classified_diff':diff,'mode':'REPORT_ONLY'}
    if 'foundation_basis' in json.loads(certificate.read_text()):
        from premise_declaration import validate_artifact
        premises=validate_artifact(artifact,inspection,certificate,root,required=True)
        if premises['status']!='PASS':raise ValueError('INV-9 HOLD: '+'; '.join(premises['reasons']))
        result['foundation_basis']=premises['foundation_basis']
    return result


def draft_binding(artifact, inspection, certificate, root):
    result=assessment(artifact,inspection,certificate,root)
    result.update(status='DRAFT_AWAITING_INDEPENDENT_REVIEW',review=None,issued_after_certification=True,
                  publication_authorized=False,proof_verifier='UNCHANGED_COMPARATOR',zenodo_writes=False)
    return result


def validate_publication_binding(artifact, inspection, certificate, root, approved_review_hashes):
    current=assessment(artifact,inspection,certificate,root)
    path=Path(artifact)/'PUBLICATION_BINDING.json'
    if path.is_symlink():raise ValueError('binding receipt symlink refused')
    receipt=json.loads(path.read_text())
    if receipt.get('standard')!=STANDARD or receipt.get('status')!='PUBLICATION_BOUND':raise ValueError('publication binding is missing, draft or held')
    if 'foundation_basis' in current or 'foundation_basis' in receipt:
        if 'foundation_basis' not in current or receipt.get('foundation_basis')!=current['foundation_basis']:
            raise ValueError('publication binding mismatch: foundation_basis')
    for key in ('certificate','sealed_manuscript','final_manuscript','final_pdf_sha256','final_tex_sha256','allowed_diff_sha256','diff_classification'):
        if receipt.get(key)!=current[key]:raise ValueError('publication binding mismatch: '+key)
    if current['diff_classification']!='VERIFICATION_STATUS_ONLY' or current['classified_diff']['status']!='CLASSIFIED':
        raise ValueError('content changes require fresh scientific certification/reconciliation')
    review=receipt.get('review')
    if not isinstance(review,dict):raise ValueError('missing independent publication review')
    review_path=resolve_binding(review,Path(root))
    if review['sha256'] not in approved_review_hashes:raise ValueError('review hash has no ledger approval')
    approved=json.loads(review_path.read_text())
    if approved.get('status')!='APPROVED_PUBLICATION_BINDING' or approved.get('scope')!='VERIFICATION_STATUS_TEXT_ONLY':
        raise ValueError('review does not approve the allowed diff')
    if approved.get('pdf_correspondence_reviewed') is not True:raise ValueError('final PDF correspondence not reviewed')
    if not approved.get('reviewer',{}).get('identity') or not approved.get('reviewed_at_utc'):
        raise ValueError('reviewer provenance missing')
    for key in ('certificate','final_manuscript','allowed_diff_sha256'):
        if approved.get(key)!=current[key]:raise ValueError('review hash binding mismatch: '+key)
    # Chronology is part of the receipt contract, not a self-asserted flag.
    def time(value):
        t=datetime.fromisoformat(value.replace('Z','+00:00'))
        if t.tzinfo is None:raise ValueError('timestamp must include UTC offset')
        return t
    issued=time(json.loads(Path(certificate).read_text())['issued_at_utc'])
    reviewed=time(approved['reviewed_at_utc']);bound=time(receipt['issued_at_utc'])
    if not issued <= reviewed <= bound <= datetime.now(timezone.utc):raise ValueError('publication binding chronology invalid')
    return [{'path':str(Path(artifact)/name),'sha256':value} for name,value in current['final_manuscript'].items()]
