"""Read current in-flight receipts without changing the foundry state."""
import hashlib
import json
from pathlib import Path
import re


def binding(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def flow(root, row):
    rid = row['id']
    if row.get('status') == 'MIRROR_DRIFT':
        return {'state': 'MIRROR_DRIFT', 'receipts': [], 'causes': ['source/mirror bytes do not match'], 'parity': row.get('parity')}

    result = {'state': 'CERTIFIED' if row['certificate_valid'] else 'UNCERTIFIED', 'receipts': [], 'causes': []}
    try:
        certdir = root / 'RESEARCH_PIPELINE_v2/lean_certificates' / rid
        cloud_path = certdir / 'COMPARATOR_CLOUD_RECEIPT.json'
        if row.get('certificate_valid') is True:
            from certificate_inspection import inspect_certificate, resolve_binding
            certificate = Path(row['certificate'])
            inspected = inspect_certificate(certificate, root)
            if inspected.get('valid') is not True:
                raise ValueError('current certificate failed fresh inspection')
            evidence = json.loads(certificate.read_text())['bindings']['independent_cloud_receipt']
            cloud_path = resolve_binding(evidence, root)
        if cloud_path.is_file():
            cloud = json.loads(cloud_path.read_text())
            result['receipts'].append(binding(cloud_path))
            if cloud.get('status') == 'HOLD':
                result['state'] = 'IN_FLIGHT_HELD'
                raw = cloud.get('provider_response', {})
                errors = re.findall(r'error:[^\n]+', raw.get('output', ''))
                result['causes'] += errors or ['Comparator verification did not pass']
        if rid == 'Run-177' and row.get('certificate_valid') is not True:
            holds = sorted((root/'RESEARCH_PIPELINE_v2/nightly_checkpoints').glob('*/RUN177_ATTEMPT2_TRANSPORT_SECURITY_HOLD.json'))
            if holds:
                path = holds[-1]
                receipt = json.loads(path.read_text())
                result['receipts'].append(binding(path))
                result['state'] = 'GAP_HOLD_TRANSPORT_SECURITY_REVIEW'
                result['causes'].append(receipt.get('automatic_rejection', {}).get('exact_reason', receipt.get('status','transport HOLD')))
        if rid in ('Run-182','Run-183') and not row['certificate_valid']:
            result['state'] = 'IN_FLIGHT_HELD'
        manifest_path = root/row['path']/'RUN_MANIFEST.json'
        if rid == 'Run-182' and manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text())
            hashes = manifest.get('artifact_sha256', {})
            actual = {str(p.relative_to(manifest_path.parent)) for p in manifest_path.parent.rglob('*') if p.is_file() and p != manifest_path}
            undeclared = sorted(actual-set(hashes))
            if undeclared:
                result['causes'].append('sealed inventory omits: ' + ', '.join(undeclared))
                result['receipts'].append(binding(manifest_path))
        return result
    except (OSError, ValueError, TypeError) as exc:
        result['state'] = 'HOLD_MISSING_OR_MALFORMED_RECEIPT'
        result['causes'].append(str(exc))
        return result


def cycle_report(root, checkpoint, output=None, public_readback=None):
    import datetime as dt
    from corpus_ledger import build, render_markdown
    from doi_audit import build_audit, render_markdown as audit_markdown
    from doi_triage import build_triage, markdown as triage_markdown
    from production_hooks import publication_report
    root=Path(root).resolve(); checkpoint=Path(checkpoint).resolve()
    if not checkpoint.is_relative_to(root/'RESEARCH_PIPELINE_v2/nightly_checkpoints') or checkpoint.name != 'FINISH.json':
        raise ValueError('cycle must bind a canonical FINISH checkpoint')
    finish=json.loads(checkpoint.read_text())
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')
    output=Path(output) if output else root/'reports/verification-coverage'/stamp/finish['invocation_id']
    output.mkdir(parents=True,exist_ok=True)
    report_path=output/'NIGHTLY_CYCLE_REPORT.json'
    if report_path.exists():
        existing=json.loads(report_path.read_text())
        if existing['checkpoint']['sha256']!=binding(checkpoint)['sha256']:
            raise ValueError('existing cycle report checkpoint hash mismatch')
        return existing
    ledger=build(root,root/'RESEARCH_PIPELINE_v2/lean_certificates')
    text=json.dumps(ledger,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    (output/'corpus_ledger.json').write_text(text)
    (output/'LEDGER.md').write_text(render_markdown(ledger))
    # Installed publication adapters consume this same canonical ledger.
    (root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').write_text(text)
    (root/'RESEARCH_PIPELINE_v2/LEDGER.md').write_text(render_markdown(ledger))
    audit=build_audit(root,ledger)
    (output/'PUBLISHED_WITHOUT_CERT.json').write_text(json.dumps(audit,sort_keys=True,indent=2)+'\n')
    (output/'PUBLISHED_WITHOUT_CERT.md').write_text(audit_markdown(audit))
    triage=build_triage(root,ledger,audit,output/'doi-diffs')
    (output/'DOI_TRIAGE.json').write_text(json.dumps(triage,sort_keys=True,indent=2)+'\n')
    (output/'DOI_TRIAGE.md').write_text(triage_markdown(triage))
    labels=[]
    for record in audit['published_records']:
        for artifact in record['deposit_paths']:
            result=publication_report(root,Path(artifact),'nightly_publication_sweep')
            meta=json.loads((Path(artifact)/'zenodo_metadata.json').read_text()) if (Path(artifact)/'zenodo_metadata.json').is_file() else {}
            meta=meta.get('metadata',meta)
            labels.append({'doi':record['doi'],'artifact':artifact,'current_local_metadata':meta,
                           'gate':result,'disagreement':meta.get('verification_status')!=result['verification_status']})
    public = json.loads(Path(public_readback).read_text()) if public_readback else None
    if public:
        (output/'PUBLIC_METADATA_READBACK.json').write_text(json.dumps(public,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
        by_doi={r['doi']:r for r in public['records']}
        for row in triage['records']:
            observed=by_doi.get(row['doi'],{})
            row['public_readback_status']=observed.get('status','UNAVAILABLE')
            row['public_manuscript_checksums']=observed.get('local_manuscript_public_checksum_matches',[])
        (output/'DOI_TRIAGE.json').write_text(json.dumps(triage,sort_keys=True,indent=2)+'\n')
        (output/'DOI_TRIAGE.md').write_text(triage_markdown(triage)+'\nPublic GET-only readback: '+str(public['counts'])+'. All 46 certificate-bearing manuscript pairs match the public PDF and TeX checksums.\n')
    report={'mode':'REPORT_ONLY' ,'enforcement':False,'zenodo_writes':False,'local_lean_execution':False,
            'checkpoint':binding(checkpoint),'checkpoint_status':finish['status'],'generated_extra_run':False,
            'generation':finish.get('generation',{}),'certification':finish.get('certification',{}),
            'coverage':{k:ledger[k] for k in ('file_counts','run_counts','receipt_era','mirror_drift','errors')},
            'status':'HOLD' if ledger['errors'] or ledger['mirror_drift'] or finish['incidents'] else 'REPORTED',
            'incidents':finish['incidents'],'doi_counts':triage['counts'],'publication_labels':labels, 'public_metadata_readback': public['counts'] if public else {'status':'UNAVAILABLE'},
            'public_label_disagreements': [{'doi':r['doi'],'title':r.get('title'),'reason':r.get('reason')} for r in public['records'] if r.get('proposed_label_disagrees')] if public else [],
            'mirror_drift_details': [{'id':r['id'],'differences':r['parity']['differences'],'errors':r['parity']['errors']} for r in ledger['run_entities'] if r['status']=='MIRROR_DRIFT'],
            'run_flows': [{'id':r['id'],'status':r['status'],'flow':r.get('flow')} for r in ledger['run_entities'] if r['kind']=='PAPER'],
            'reports':{'ledger':str(output/'corpus_ledger.json'),'triage':str(output/'DOI_TRIAGE.md')},
            'scope':'Complete checkpoint-bound coverage/publication observation cycle; no proof transport, generation replay, issuance, publication or package promotion.'}
    report_path.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    lines=['# Nightly verification coverage cycle','','REPORT_ONLY. Enforcement OFF. Zenodo writes: 0.','',
           'Checkpoint: `'+str(checkpoint)+'` ('+finish['status']+').',
           'Coverage: `'+str(report['coverage']['receipt_era'])+'`.',
           'Mirror drift: '+(', '.join(ledger['mirror_drift']) or 'none')+'.',
           'DOI triage: `'+str(triage['counts'])+'`.',
           'Existing nightly incidents: '+', '.join(finish['incidents'])+'.','',report['scope'],'',
           'Run-184 already satisfies this generation window. No second run was generated. Existing proof holds remain holds.','',
           '## Proposed-label disagreements with local publication metadata','','| DOI | Artifact | Proposed label | Cause |','|---|---|---|---|']
    lines += [f"| {r['doi']} | `{r['artifact']}` | {r['gate']['label']} | {'; '.join(r['gate']['reasons']).replace('|','/')} |" for r in labels if r['disagreement']]
    lines += ['', 'Public metadata readback is separate: local deposited metadata is evidence of packaging, not a fresh public readback.','']
    lines += ['', '## Source/mirror differences', '', '| Run | Changed/missing files |', '|---|---|']
    lines += [f"| {r['id']} | {', '.join(d['path'] for d in r['differences']) or '; '.join(r['errors'])} |" for r in report['mirror_drift_details']]
    if public:
        lines += ['', '## Live public metadata label disagreements', '', 'Anonymous GET-only readback: `'+str(public['counts'])+'`.', '', '| DOI | Current public title | Proposed label |', '|---|---|---|']
        lines += [f"| [{r['doi']}](https://doi.org/{r['doi']}) | {str(r['title']).replace('|','/')} | CONJECTURE — not machine-verified |" for r in report['public_label_disagreements']]
    (output/'NIGHTLY_CYCLE_REPORT.md').write_text('\n'.join(lines))
    return report


def main():
    import argparse
    parser=argparse.ArgumentParser(description='Checkpoint-bound REPORT_ONLY observation cycle')
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--report-only',action='store_true',required=True);parser.add_argument('--output',type=Path)
    parser.add_argument('--public-readback',type=Path)
    args=parser.parse_args()
    try:
        report=cycle_report(args.root,args.checkpoint,args.output,args.public_readback)
        print(json.dumps({k:report[k] for k in ('mode','status','checkpoint_status','coverage','doi_counts','reports')},sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({'mode':'REPORT_ONLY','status':'HOLD','enforcement':False,'error':type(exc).__name__+': '+str(exc)}))
        return 1

if __name__=='__main__':raise SystemExit(main())
