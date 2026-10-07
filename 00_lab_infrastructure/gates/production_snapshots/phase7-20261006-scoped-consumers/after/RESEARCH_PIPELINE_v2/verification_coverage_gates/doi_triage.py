"""Report-only refinement of locally evidenced DOI artifacts; never inherits proof by title."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
from certificate_inspection import inspect_certificate, resolve_binding

BUCKETS=('CURABLE_BY_JOIN','TRUE_CONJECTURE','COSMETIC','SUBSTANTIVE')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manuscript_diff(sealed, published):
    """Only formatting/comments and preamble/rights metadata may count as cosmetic.

    Changed certification assertions in the manuscript body are changed claims,
    even if the mathematics is untouched. Unavailable evidence is substantive HOLD.
    """
    before=Path(sealed).read_text(); after=Path(published).read_text()
    def scientific_body(text):
        text=re.sub(r'(?<!\\)%[^\n]*','',text)
        body=text.split(r'\begin{document}',1)[-1]
        body=re.sub(r'\\(?:maketitle|title|author|date|thanks)\b(?:\{[^{}]*\})?', '', body)
        return re.sub(r'\s+','',body)
    bucket='COSMETIC' if scientific_body(before)==scientific_body(after) else 'SUBSTANTIVE'
    delta=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),
                   fromfile=str(sealed),tofile=str(published)))
    return {'bucket':bucket,'sealed_path':str(sealed),'published_path':str(published),
            'sealed_sha256':digest(Path(sealed)),'published_sha256':digest(Path(published)), 'diff':delta,
            'reason':'Only formatting/preamble metadata differs' if bucket=='COSMETIC' else
                     'Manuscript body assertions changed; certification assertions count as claims'}


def build_triage(root, ledger, audit, diff_dir):
    root=Path(root).resolve(); diff_dir=Path(diff_dir);diff_dir.mkdir(parents=True,exist_ok=True)
    certs={c['run_id']:c for c in ledger['certificates'] if c.get('valid')}
    parity={r['id']:r for r in ledger['run_entities']}
    rows=[]
    for item in audit['published_records']:
        row={'doi':item['doi'],'title':item['title'],'run_ids':item['run_ids'],
             'deposit_paths':item['deposit_paths'],'mode':'REPORT_ONLY','status':'HOLD',
             'proof_certificate_present_valid':item['proof_certificate_present_valid'],'evidence':[], 'reasons':[]}
        if not item['proof_certificate_present_valid']:
            # A provenance run join is a search key only. Require both actual
            # deposited proof/statement bytes to bind one current certificate.
            candidates=[certs[rid] for rid in item['run_ids'] if rid in certs]
            row['bucket']='TRUE_CONJECTURE'
            for cert in candidates:
                rid=cert['run_id']
                if parity.get(rid,{}).get('status')=='MIRROR_DRIFT':
                    row['reasons'].append(rid+': source/mirror drift')
                    continue
                proof=resolve_binding({'path':cert['candidate_path'],'sha256':cert['candidate_sha256']},root)
                raw=json.loads(Path(cert['path']).read_text()); statement=resolve_binding(raw['bindings']['formal_statement'],root)
                for deposit in item['deposit_paths']:
                    path=Path(deposit)
                    checks=[]
                    for bound in (proof,statement):
                        matches=[{'path':str(p),'sha256':digest(p)} for p in sorted(path.rglob('*.lean'))
                                 if not p.is_symlink() and '.lake' not in p.parts and digest(p)==digest(bound)]
                        checks.append({'certificate_binding':str(bound),'sha256':digest(bound),'deposited_matches':matches})
                    row['evidence'].append({'run_id':rid,'certificate':cert['path'],'lean_bindings':checks})
                    if all(c['deposited_matches'] for c in checks):
                        row['bucket']='CURABLE_BY_JOIN'
            row['reasons'].append('Exact deposited proof and statement bind an existing Run certificate; join repair remains a proposal' if row['bucket']=='CURABLE_BY_JOIN' else
                                  'No valid Run-join certificate binds both deposited proof and statement; unavailable joins remain conjecture HOLD')
        else:
            row['bucket']='SUBSTANTIVE'
            comparisons=[]
            for deposit in item['deposit_paths']:
                path=Path(deposit);certpath=path/'LEAN_ZERO_SORRY_CERTIFICATE.json'
                cert=inspect_certificate(certpath,root)
                if not cert['valid']:
                    row['reasons']+=cert['reasons'];continue
                try:
                    sealed=resolve_binding(cert['sealed_paper_inputs']['SEALED_paper.tex'],root)
                    published=path/'paper.tex'
                    if not published.is_file():
                        options=sorted(path.glob('*.tex'))
                        if len(options)!=1:raise ValueError('missing or ambiguous deposited manuscript')
                        published=options[0]
                    comparison=manuscript_diff(sealed,published)
                    diff=diff_dir/(item['doi'].split('.')[-1]+'-'+path.name+'.diff')
                    diff.write_text(comparison.pop('diff'))
                    comparison.update(diff_path=str(diff),diff_sha256=digest(diff))
                    comparisons.append(comparison)
                except Exception as exc:row['reasons'].append(type(exc).__name__+': '+str(exc))
            if comparisons and all(c['bucket']=='COSMETIC' for c in comparisons) and not row['reasons']:
                row['bucket']='COSMETIC'
            row['evidence']=comparisons
            row['reasons'] += sorted({c['reason'] for c in comparisons}) or ['Unavailable manuscript diff; conservative SUBSTANTIVE HOLD']
        rows.append(row)
    count=Counter(r['bucket'] for r in rows)
    return {'mode':'REPORT_ONLY','tree_root':str(root),'counts':{b:count[b] for b in BUCKETS},'records':rows,
            'evidence_scope':'Local DOI receipts/registry and deposited manuscript copies. Public readback recorded separately; no Zenodo writes.',
            'policy':'TRUE_CONJECTURE includes missing/unavailable binding evidence; it does not assert mathematical falsity. COSMETIC requires unchanged manuscript-body assertions. All buckets remain publication HOLD pending claim binding and exact manuscript certification.'}


def markdown(report):
    lines=['# DOI triage','','Report-only; no public labels or Zenodo objects changed.','',report['evidence_scope'],'',report['policy'],'',
           '| Bucket | Count |','|---|---:|']+[f"| {b} | {report['counts'][b]} |" for b in BUCKETS]
    for bucket in BUCKETS:
        lines+=['','## '+bucket,'','| DOI | Run join | Cause | Evidence |','|---|---|---|---|']
        for r in report['records']:
            if r['bucket']!=bucket:continue
            paths=[e.get('diff_path',e.get('certificate','')) for e in r['evidence']]
            lines.append(f"| [{r['doi']}](https://doi.org/{r['doi']}) | {', '.join(r['run_ids']) or 'Unavailable'} | {'; '.join(r['reasons']).replace('|','/')} | {'; '.join(paths) or '; '.join(r['deposit_paths']) or 'Registry only; deposited bytes unavailable'} |")
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=build_triage(a.root,json.loads(a.ledger.read_text()),json.loads(a.audit.read_text()),a.out.parent/'doi-diffs')
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');a.out.with_suffix('.md').write_text(markdown(report));print(json.dumps(report['counts']))

if __name__=='__main__':main()
