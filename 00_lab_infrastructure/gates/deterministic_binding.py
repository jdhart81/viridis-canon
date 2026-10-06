"""User-authorized manuscript review rules; never verifies or changes Lean evidence."""
from datetime import datetime,timezone
import hashlib,json,re,subprocess,tempfile,unicodedata
from pathlib import Path
from certificate_inspection import inspect_certificate
from manuscript_structure import structure,STATUS,SCIENTIFIC,classify
from publication_binding import assessment,validate_publication_binding


def normalized_pdf_text(text):
    return ' '.join(unicodedata.normalize('NFKC',text).split())


def strict_status_only(before,after):
    diff=classify(before,after)
    if diff['classification']!='VERIFICATION_STATUS_ONLY' or diff['status']!='CLASSIFIED':return False,diff
    a,b=structure(before),structure(after)
    for field in ('math','numbers','theorem_and_equation_blocks','scientific_macros'):
        if a[field]!=b[field]:return False,diff
    import difflib
    for op,i,j,k,l in difflib.SequenceMatcher(a=a['headings'],b=b['headings'],autojunk=False).get_opcodes():
        if op!='equal' and any(not (STATUS.search(x) or re.search(r'\bverification\s+status\b',x,re.I)) or SCIENTIFIC.search(x) for x in a['headings'][i:j]+b['headings'][k:l]):
            return False,{**diff,'deterministic_hold':'NON_STATUS_SECTION_TITLE_CHANGED'}
    return True,diff


def pdf_correspondence(tex,pdf,sealed_tex,sealed_pdf):
    if tex.read_bytes()==sealed_tex.read_bytes() and pdf.read_bytes()==sealed_pdf.read_bytes():
        return {'passed':True,'method':'EXACT_SEALED_TEX_AND_PDF_BYTES'}
    with tempfile.TemporaryDirectory(prefix='viridis-pdf-review-') as tmp:
        run=subprocess.run(['/opt/homebrew/bin/tectonic','-X','compile','--only-cached','--outdir',tmp,str(tex)],capture_output=True)
        if run.returncode:return {'passed':False,'method':'CACHED_TEX_RENDER_FAILED','exit_code':run.returncode}
        rendered=Path(tmp)/(tex.stem+'.pdf')
        def extract(path):
            run=subprocess.run(['/opt/homebrew/bin/pdftotext','-enc','UTF-8',str(path),'-'],capture_output=True)
            if run.returncode:raise ValueError('PDF extraction failed')
            return normalized_pdf_text(run.stdout.decode())
        expected,actual=extract(rendered),extract(pdf)
        return {'passed':bool(expected) and expected==actual,'method':'CACHED_FINAL_TEX_RENDER_TEXT_EQUALS_DEPOSITED_PDF_TEXT','rendered_text_sha256':hashlib.sha256(expected.encode()).hexdigest(),'deposited_text_sha256':hashlib.sha256(actual.encode()).hexdigest()}


def review(artifact,certificate,root):
    artifact,certificate,root=map(Path,(artifact,certificate,root))
    inspection=inspect_certificate(certificate,root)
    current=assessment(artifact,inspection,certificate,root)
    before=Path(current['sealed_manuscript']['tex']['path']);after=next(artifact.glob('*.tex'));pdf=next(artifact.glob('*.pdf'))
    passed,diff=strict_status_only(before.read_text(),after.read_text())
    correspondence=pdf_correspondence(after,pdf,before,Path(current['sealed_manuscript']['pdf']['path'])) if passed else {'passed':False,'method':'SCIENTIFIC_DIFF_HOLD'}
    return current,{'status':'RULE_PASS' if passed and correspondence['passed'] else 'HOLD','structure_rule_passed':passed,'protected_sets_identical':passed,'pdf_correspondence':correspondence,'classified_diff':diff,'proof_verifier':'UNCHANGED_COMPARATOR'}


def issue(artifact,certificate,root,authority_file,output_dir):
    artifact,certificate,root,authority_file,output_dir=map(Path,(artifact,certificate,root,authority_file,output_dir))
    authority=authority_file.read_text()
    if 'Gate 1 decisions & full-completion authorization — 2026-10-04' not in authority or '27 status-only bindings' not in authority:
        raise ValueError('missing explicit deterministic review authority')
    current,result=review(artifact,certificate,root)
    output_dir.mkdir(parents=True,exist_ok=False)
    (output_dir/'REPORT_ONLY_ASSESSMENT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    if result['status']!='RULE_PASS':return result
    timestamp=datetime.now(timezone.utc).isoformat()
    approved={'status':'APPROVED_PUBLICATION_BINDING','scope':'VERIFICATION_STATUS_TEXT_ONLY','reviewer':{'identity':'DETERMINISTIC_RULE_AUTHORIZED_BY_JUSTIN_20261004','kind':'AUTOMATED_RULE_NOT_INDEPENDENT_HUMAN_REVIEW'},'reviewed_at_utc':timestamp,'pdf_correspondence_reviewed':True,'pdf_correspondence_evidence':result['pdf_correspondence'],'authority':{'path':str(authority_file),'sha256':hashlib.sha256(authority_file.read_bytes()).hexdigest()},**{k:current[k] for k in ('certificate','final_manuscript','allowed_diff_sha256')}}
    ap=output_dir/'DETERMINISTIC_REVIEW.json';ap.write_text(json.dumps(approved,indent=2,ensure_ascii=False)+'\n');h=hashlib.sha256(ap.read_bytes()).hexdigest()
    receipt={**current,'status':'PUBLICATION_BOUND','review':{'path':str(ap),'sha256':h},'issued_at_utc':datetime.now(timezone.utc).isoformat(),'issued_after_certification':True,'publication_authorized':False,'review_rule_passed':True,'review_kind':'AUTHORIZED_DETERMINISTIC_RULE','mode':'ENFORCING','zenodo_writes':False}
    rp=artifact/'PUBLICATION_BINDING.json'
    if rp.exists():raise ValueError('preserve existing binding; use a new immutable release directory')
    rp.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n')
    inspection=inspect_certificate(certificate,root)
    validate_publication_binding(artifact,inspection,certificate,root,[h])
    result.update(binding_receipt=str(rp),binding_sha256=hashlib.sha256(rp.read_bytes()).hexdigest(),approved_review_sha256=h)
    (output_dir/'RESULT.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    return result
