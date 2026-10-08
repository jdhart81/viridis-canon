"""Read-only independent scientific holds. A package refresh cannot erase a counterexample."""
from pathlib import Path
import re
from scientific_reconciliation import obj, local, digest, validate_review, ReconciliationError
HERE=Path(__file__).resolve().parent
class ScientificHoldError(ValueError):
    pass

def check_scientific_advisory(run_id, *, pipeline_root=HERE):
    registry_path=pipeline_root/'SCIENTIFIC_ADVISORIES.json'
    try:
        if registry_path.is_symlink() or not registry_path.is_file():
            raise ScientificHoldError('Scientific advisory registry is missing or unsafe')
        registry=obj(registry_path)
        if registry.get('standard')!='VRS-SCIENTIFIC-ADVISORIES-1' or registry.get('automatic_clearance') is not False or not isinstance(registry.get('records'),list):
            raise ScientificHoldError('Invalid scientific advisory registry')
        seen=set()
        for row in registry['records']:
            if (not isinstance(row,dict) or row.get('status')!='HOLD'
                or not re.fullmatch(r'Run-[1-9][0-9]*',str(row.get('run_id','')))
                or row['run_id'] in seen):
                raise ScientificHoldError('Malformed or duplicate scientific hold')
            seen.add(row['run_id'])
            if row['run_id']!=run_id:continue
            if not re.fullmatch('[a-f0-9]{64}',str(row.get('request_sha256',''))):
                raise ScientificHoldError('Scientific request pin required')
            review=local(pipeline_root,row.get('review_path'))
            if not review.is_file() or digest(review.read_bytes())!=row.get('review_sha256'):
                raise ScientificHoldError('Scientific hold review changed or is missing')
            packet=pipeline_root/'scientific_reconciliations'/run_id/row['request_sha256']
            verified=validate_review(packet,review)
            if verified['review_verdict']!='HOLD':
                raise ScientificHoldError('Scientific advisory is not backed by a held independent review')
            reasons=', '.join(str(x.get('code','review finding')) for x in verified['findings'] if x.get('severity') not in {'info'})
            raise ScientificHoldError(f'{run_id}: independent scientific HOLD ({reasons or "inspect bound review"}); corrected source and a later independent resolution are required. Existing proof certificates do not clear this paper-scope finding.')
        return {'status':'NO_REGISTERED_SCIENTIFIC_HOLD','run_id':run_id,'scientific_validation_claimed':False}
    except (OSError,KeyError,TypeError,ValueError) as error:
        if isinstance(error,ScientificHoldError):raise
        raise ScientificHoldError('Scientific advisory integrity HOLD: '+str(error)) from error
