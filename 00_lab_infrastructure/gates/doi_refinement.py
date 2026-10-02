"""Local, report-only DOI refinement. No publisher or network operations."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
from certificate_inspection import inspect_certificate, resolve_binding
from claim_binding import inspect_entity_certificate
from manuscript_structure import classify

BUCKETS=('CURABLE_BY_NEW_VERSION','TRUE_CONJECTURE','VERIFICATION_STATUS_ONLY','CONTENT_CHANGED')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,obj):Path(p).write_text(json.dumps(obj,indent=2,sort_keys=True,ensure_ascii=False)+'\n')

def repair_join(item, records, root):
    root=Path(root).resolve()
    paths=item['deposit_paths']
    if len(paths)!=1:raise ValueError('repair provenance requires one exact deposit')
    p=Path(paths[0]);mp=p/'CORRECTION_MANIFEST.json';m=json.loads(mp.read_text())
    original=Path(m['source_bundle']).resolve(strict=True)
    if not original.is_relative_to(root) or m.get('science_changed') is not False:raise ValueError('unsafe repair provenance')
    parent=records[m['predecessor_doi']]
    if str(original) not in parent['deposit_paths'] or len(parent['run_ids'])!=1:raise ValueError('ambiguous repair Run join')
    protected=m['protected_unchanged_files'];lean=[n for n in protected if n.endswith('.lean')]
    if not lean:raise ValueError('repair has no protected proof')
    checks=[]
    for name in protected:
        a,b=original/name,p/name
        if not a.resolve().is_relative_to(original) or not b.resolve().is_relative_to(p) or a.is_symlink() or b.is_symlink():raise ValueError('unsafe protected path')
        expected=m['original_sha256'][name]
        if sha(a)!=expected or sha(b)!=expected or m['candidate_sha256'][name]!=expected:raise ValueError('repair protected bytes changed: '+name)
        checks.append({'file':name,'sha256':expected})
    return parent['run_ids'],{'manifest':str(mp),'sha256':sha(mp),'predecessor_doi':m['predecessor_doi'],'source_bundle':str(original),'protected_bytes':checks,'purpose':'PROVENANCE_JOIN_ONLY'}

def prepare_bundle(row, cert, root, output):
    target=output/'new-version-bundles'/row['doi'].split('.')[-1]
    if target.exists():
        mp=target/'NEW_VERSION_PROPOSAL.json';existing=json.loads(mp.read_text())
        if existing['predecessor_doi']!=row['doi'] or existing['run_ids']!=row['run_ids'] or existing['certificate']['sha256']!=sha(cert['path']):raise ValueError('existing draft provenance changed')
        for name,digest in existing['files'].items():
            p=target/name
            if not p.resolve().is_relative_to(target.resolve()) or p.is_symlink() or sha(p)!=digest:raise ValueError('existing draft bytes changed')
        row['bundle']=str(target);row['bundle_manifest_sha256']=sha(mp);return
    target.mkdir(parents=True,exist_ok=False)
    raw=json.loads(Path(cert['path']).read_text());bound=[]
    def visit(value):
        if isinstance(value,dict):
            if 'path' in value and 'sha256' in value:
                p=resolve_binding(value,root);bound.append(p)
            else:
                for v in value.values():visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    visit(raw['bindings'])
    envelope=target/'certification-evidence';envelope.mkdir()
    for p in sorted(set(bound+[Path(cert['path'])])):
        dest=envelope/p.name
        if dest.exists() and sha(dest)!=sha(p):raise ValueError('ambiguous certificate evidence basename')
        shutil.copy2(p,dest)
    candidate=resolve_binding(raw['bindings']['candidate_proof'],root)
    statement=resolve_binding(raw['bindings']['formal_statement'],root)
    for p,name in ((candidate,'VERIFICATION_CANDIDATE.lean'),(statement,'VERIFICATION_STATEMENT.lean'),(Path(cert['path']),'LEAN_ZERO_SORRY_CERTIFICATE.json')):
        shutil.copy2(p,target/name)
    # Exact sealed manuscript is a provisional starting point. It is never an
    # approved final publication and does not silently inherit public metadata.
    for suffix in ('pdf','tex'):
        shutil.copy2(resolve_binding(raw['bindings']['sealed_paper_inputs']['SEALED_paper.'+suffix],root),target/('paper.'+suffix))
    comparisons=[]
    historical=target/'historical';historical.mkdir()
    for i,deposit in enumerate(row['deposit_paths']):
        p=Path(deposit)
        for name in ('paper.tex','paper.pdf'):
            if (p/name).is_file():shutil.copy2(p/name,historical/(str(i)+'-'+name))
        if (p/'paper.tex').is_file():
            diff=classify((target/'paper.tex').read_text(),(p/'paper.tex').read_text());write(historical/(str(i)+'-manuscript-classified-diff.json'),diff);comparisons.append(diff['classification'])
    manifest={'standard':'VRS-LOCAL-NEW-VERSION-PROPOSAL-1','status':'DRAFT_HOLD','predecessor_doi':row['doi'],'run_ids':row['run_ids'],
        'certificate':{'path':cert['path'],'sha256':sha(cert['path'])},'certified_candidate_sha256':sha(candidate),'certified_statement_sha256':sha(statement),
        'manuscript_status':'PROVISIONAL_EXACT_SEALED_INPUTS_REQUIRES_REVIEW','historical_manuscript_comparisons':comparisons,
        'required_before_publish':['Independent scientific/manuscript reconciliation','PUBLICATION_BINDING review and receipt','Complete claim/fidelity binding','Explicit exact-hash new-version authorization'],
        'mode':'REPORT_ONLY','zenodo_writes':False,'publication_authorized':False,'files':{str(p.relative_to(target)):sha(p) for p in sorted(target.rglob('*')) if p.is_file()}}
    write(target/'NEW_VERSION_PROPOSAL.json',manifest)
    (target/'README.md').write_text('Local unpublished new-version proposal for '+row['doi']+'.\n\nDRAFT / HOLD. Certified proof, statement and certificate are copied unchanged from the Cowork store. paper.tex/pdf are provisional exact sealed inputs, not an approved final manuscript. Historical deposited manuscripts and classified diffs are retained for reconciliation. No DOI reservation, public label, publication approval or release binding is created.\n')
    row['bundle']=str(target);row['bundle_manifest_sha256']=sha(target/'NEW_VERSION_PROPOSAL.json')

def build(root,ledger,audit,output):
    root=Path(root).resolve();output=Path(output);output.mkdir(parents=True,exist_ok=True);diffdir=output/'classified-doi-diffs';diffdir.mkdir(exist_ok=True)
    records={r['doi']:r for r in audit['published_records']};certs={c['run_id']:c for c in ledger['certificates'] if c.get('valid')};entities={r['id']:r for r in ledger['run_entities']};rows=[]
    for item in records.values():
        row={k:item[k] for k in ('doi','title','run_ids','deposit_paths','proof_certificate_present_valid')};row.update(mode='REPORT_ONLY',status='HOLD',evidence=[],reasons=[])
        row['bucket']='TRUE_CONJECTURE'
        if not item['proof_certificate_present_valid']:
            if not row['run_ids'] and any('REPAIR_STAGING' in p for p in row['deposit_paths']):
                try:row['run_ids'],join=repair_join(item,records,root);row['evidence'].append(join)
                except Exception as exc:row['reasons'].append('Repair join unavailable: '+str(exc))
            candidates=[]
            for rid in row['run_ids']:
                if rid not in certs:continue
                try:
                    cert=inspect_entity_certificate(entities[rid],ledger)
                    cert['path']=certs[rid]['path'];candidates.append(cert)
                except Exception as exc:row['reasons'].append(rid+': '+str(exc))
            if len(candidates)==1 and row['deposit_paths']:
                cert=candidates[0];candidate=Path(cert['candidate_path']);raw=json.loads(Path(cert['path']).read_text());statement=resolve_binding(raw['bindings']['formal_statement'],root);checks=[]
                for deposit in row['deposit_paths']:
                    files=[p for p in sorted(Path(deposit).rglob('*.lean')) if not p.is_symlink() and '.lake' not in p.parts]
                    checks.append({'deposit':deposit,'deposited_lean_files':[{'path':str(p),'sha256':sha(p)} for p in files], 'candidate_present':any(sha(p)==sha(candidate) for p in files), 'statement_present':any(sha(p)==sha(statement) for p in files)})
                row['evidence'].append({'certificate':cert['path'],'certificate_sha256':sha(cert['path']),'certified_candidate_sha256':sha(candidate),'deposited_proofs':checks})
                if all(c['deposited_lean_files'] and not (c['candidate_present'] and c['statement_present']) for c in checks):
                    row['bucket']='CURABLE_BY_NEW_VERSION';row['subtype']='CANDIDATE_BYTES_DIFFER' if all(not c['candidate_present'] for c in checks) else 'CANDIDATE_MATCHES_STATEMENT_MISSING';row['reasons'].append('Valid Run certificate and parity, but certified candidate bytes differ.' if row['subtype']=='CANDIDATE_BYTES_DIFFER' else 'Candidate already matches exactly; certificate-bound statement is missing. This is an incomplete proof package, not a candidate-byte mismatch.');row['reasons'].append('Local new-version proposal only; no join silently confers certification.')
                    prepare_bundle(row,cert,root,output)
                else:row['reasons'].append('Unexpected missing/already matching proof: HOLD for join review; never silently promote.')
            if row['bucket']=='TRUE_CONJECTURE':row['reasons'].append('No currently usable exact proof certificate for deposited bytes; unavailable evidence is HOLD, not a falsity assertion.')
        else:
            row['bucket']='CONTENT_CHANGED';comparisons=[]
            for deposit in row['deposit_paths']:
                try:
                    p=Path(deposit);cert=inspect_certificate(p/'LEAN_ZERO_SORRY_CERTIFICATE.json',root)
                    if not cert['valid']:raise ValueError('; '.join(cert['reasons']))
                    sealed=resolve_binding(cert['sealed_paper_inputs']['SEALED_paper.tex'],root)
                    result=classify(sealed.read_text(),(p/'paper.tex').read_text());result.update(doi=row['doi'],sealed_path=str(sealed),published_path=str(p/'paper.tex'))
                    stem=row['doi'].split('.')[-1]+'-'+p.name
                    dp=diffdir/(stem+'.diff');dp.write_text(result.pop('diff'));result.update(diff_path=str(dp),diff_sha256=sha(dp));jp=diffdir/(stem+'.json');write(jp,result)
                    row['evidence'].append({'classified_diff':str(jp),'sha256':sha(jp),'raw_diff':str(dp),'classification':result['classification']});comparisons.append(result)
                except Exception as exc:row['reasons'].append(str(exc))
            if comparisons and all(c['classification']=='VERIFICATION_STATUS_ONLY' and c['status']=='CLASSIFIED' for c in comparisons) and not row['reasons']:row['bucket']='VERIFICATION_STATUS_ONLY'
            row['reasons']+=sorted({c['reason'] for c in comparisons}) or ['Missing manuscript evidence: HOLD']
        rows.append(row)
    counts=Counter(r['bucket'] for r in rows)
    return {'schema_version':2,'mode':'REPORT_ONLY','tree_root':str(root),'counts':{b:counts[b] for b in BUCKETS},'records':rows,'zenodo_writes':False,
        'policy':'All 98 remain publication HOLD. Structure classifications are conservative implementer triage, not independent approval. CONTENT_CHANGED also includes non-status metadata or ambiguous mixed scientific disclaimers, which cannot safely be cleared as status-only. TRUE_CONJECTURE includes unavailable evidence and does not assert falsity. No production publication wiring changed.',
        'public_bytes_evidence':'Prior 2026-10-02 public GET readback matched all 46 deposited TeX/PDF MD5 values. See PUBLIC_METADATA_READBACK.json; no new Zenodo mutation.'}

def markdown(report):
    lines=['# DOI triage — refinement','','Report-only. No Zenodo writes, public relabeling, publication or enforcement.','',report['policy'],'',report['public_bytes_evidence'],'','| Bucket | DOI count |','|---|---:|']+[f"| {b} | {report['counts'][b]} |" for b in BUCKETS]
    lines+=['','The previous 52 without deposited certificates split into 16 new-version proposals and 36 conjecture/unknown holds. Of those 16, 11 have different candidate bytes; 5 already have the exact candidate but lack the certificate-bound statement (Runs 128, 131, 141 and repair versions for 128/131). The latter are included as incomplete proof packages, not claimed proof-byte mismatches. The previous 46 manuscript mismatches are split below. CURABLE_BY_JOIN and COSMETIC remain zero in the prior census.','', 'See [PUBLICATION_BINDING_SPEC.md](PUBLICATION_BINDING_SPEC.md) and [MIRROR_DRIFT_DIAGNOSIS.md](MIRROR_DRIFT_DIAGNOSIS.md). New-version proposals are outside publisher discovery.']
    for bucket in BUCKETS:
        lines+=['','## '+bucket,'','| DOI | Run join | Evidence / local proposal | Reason |','|---|---|---|---|']
        for r in report['records']:
            if r['bucket']!=bucket:continue
            links=[]
            if r.get('bundle'):links.append('[Draft bundle]('+r['bundle']+'/NEW_VERSION_PROPOSAL.json)')
            for e in r['evidence']:
                if e.get('classified_diff'):links.extend(('[Classified diff]('+e['classified_diff']+')','[Raw diff]('+e['raw_diff']+')'))
            lines.append(f"| [{r['doi']}](https://doi.org/{r['doi']}) | {', '.join(r['run_ids']) or 'Unavailable'} | {'; '.join(links) or 'See exact hashes/provenance in DOI_TRIAGE.json'} | {'; '.join(r['reasons']).replace('|','/')} |")
    return '\n'.join(lines)+'\n'
def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    report=build(a.root,json.loads(a.ledger.read_text()),json.loads(a.audit.read_text()),a.out);write(a.out/'DOI_TRIAGE.json',report);(a.out/'DOI_TRIAGE.md').write_text(markdown(report));print(json.dumps(report['counts']))
if __name__=='__main__':main()
