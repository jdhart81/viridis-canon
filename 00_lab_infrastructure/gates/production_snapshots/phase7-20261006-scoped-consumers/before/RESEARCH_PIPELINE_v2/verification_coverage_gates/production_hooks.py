"""Installed production adapters: observation only, no enforcing option or network."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from publication_gate import evaluate_publication
from certificate_inspection import inspect_certificate
from mirror_parity import run_parity, GENERATION_ROOT


def publication_report(root, artifact, context):
    root, artifact = Path(root).resolve(), Path(artifact).resolve()
    try:
        if not artifact.is_relative_to(root):
            raise ValueError('artifact outside mirror/certification root')
        ledger = json.loads((root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_text())
        if Path(ledger['tree_root']).resolve() != root:
            raise ValueError('ledger root differs from installed root')
        entity = next((r for r in ledger['run_entities'] if (root/r['path']).resolve() == artifact), None)
        if entity is None:
            certpath = artifact/'LEAN_ZERO_SORRY_CERTIFICATE.json'
            inspection = inspect_certificate(certpath, root)
            rid = inspection.get('run_id')
            runs = [r for r in ledger['run_entities'] if r.get('id') == rid]
            parity_ok = len(runs)==1 and run_parity(root, runs[0]['path'], Path(ledger.get('generation_root_parity_only', str(GENERATION_ROOT))))['status']=='MATCH'
            entity = {'id': 'deposit:'+str(artifact.relative_to(root)), 'path': str(artifact.relative_to(root)),
                      'run_id': rid, 'kind': 'PUBLICATION', 'status': 'CERTIFIED' if inspection['valid'] and parity_ok else 'DEBT',
                      'certificate_valid': inspection['valid'] and parity_ok, 'certificate': str(certpath)}
            ledger = {**ledger, 'run_entities': ledger['run_entities']+[entity]}
        result = evaluate_publication(artifact, ledger, entity_id=entity['id'])
    except Exception as exc:
        result = {'artifact':str(artifact), 'mode':'REPORT_ONLY', 'status':'HOLD',
                  'label':'CONJECTURE — not machine-verified', 'verification_status':'CONJECTURE',
                  'reasons':[type(exc).__name__+': '+str(exc)]}
    result.update(context=context, enforcement=False, metadata_modified=False, zenodo_writes=False,
                  observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    return result


def log_publication(root, artifact, context):
    result = publication_report(root, artifact, context)
    print(json.dumps({'verification_coverage':result}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    try:
        output=Path(root)/'reports/verification-coverage'/dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')/'publication-hooks'
        output.mkdir(parents=True, exist_ok=True)
        content=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
        filename=hashlib.sha256(content.encode()).hexdigest()+'.json'
        (output/filename).write_text(content)
    except Exception as exc:
        print(json.dumps({'verification_coverage':{'mode':'REPORT_ONLY','status':'HOLD','label':'CONJECTURE — not machine-verified','report_error':str(exc)}}),file=sys.stderr)
    return result
