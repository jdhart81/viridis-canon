"""Publication observation and explicit new-artifact enforcement; no network."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
from publication_gate import evaluate_publication, require_new_artifact_publication, UNCERTIFIED_LABEL
from certificate_inspection import inspect_certificate
from claim_binding import find_entity


def publication_report(root, artifact, context, *, enforce_new_artifacts=False):
    root, artifact = Path(root).resolve(), Path(artifact).resolve()
    try:
        if not artifact.is_relative_to(root):
            raise ValueError('artifact outside mirror/certification root')
        ledger = json.loads((root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').read_text())
        if Path(ledger['tree_root']).resolve() != root:
            raise ValueError('ledger root differs from installed root')
        entity = find_entity(ledger, artifact)
        result = evaluate_publication(artifact, ledger, entity_id=entity['id'], enforce=enforce_new_artifacts)
    except Exception as exc:
        result = {'artifact':str(artifact), 'mode':'REPORT_ONLY', 'status':'HOLD',
                  'label':UNCERTIFIED_LABEL, 'verification_status':'UNCERTIFIED',
                  'reasons':[type(exc).__name__+': '+str(exc)]}
    result.update(context=context, mode="ENFORCING" if enforce_new_artifacts else "REPORT_ONLY",
                  enforcement=enforce_new_artifacts, blocking=enforce_new_artifacts and result["status"] != "PASS",
                  metadata_modified=False, zenodo_writes=False,
                  observed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    return result


def log_publication(root, artifact, context, *, enforce_new_artifacts=False):
    result = publication_report(root, artifact, context, enforce_new_artifacts=enforce_new_artifacts)
    print(json.dumps({'verification_coverage':result}, ensure_ascii=False, sort_keys=True), file=sys.stderr)
    try:
        output=Path(root)/'reports/verification-coverage'/dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d')/'publication-hooks'
        output.mkdir(parents=True, exist_ok=True)
        content=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
        filename=hashlib.sha256(content.encode()).hexdigest()+'.json'
        (output/filename).write_text(content)
    except Exception as exc:
        print(json.dumps({'verification_coverage':{'mode':'ENFORCING' if enforce_new_artifacts else 'REPORT_ONLY','status':'HOLD','label':UNCERTIFIED_LABEL,'report_error':str(exc)}}),file=sys.stderr)
        result.update(status='HOLD', reasons=result.get('reasons', []) + ['coverage report persistence failed: ' + str(exc)], blocking=enforce_new_artifacts)
    if enforce_new_artifacts:
        require_new_artifact_publication(result)
    return result
