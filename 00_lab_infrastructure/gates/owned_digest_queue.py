"""Read-only crash-aware selection of one genuine immutable owned checkpoint.

Every partial reserved operation is retained. A status marker or a shorter
older success cannot replace a later failed/uncertain/reserved attempt.
"""
from pathlib import Path
from copy import deepcopy
import owned_digest_executor as e
import owned_digest_machine as m

def compatible(prefix,current):
    e.need(prefix['plan_sha256']==current['plan_sha256']and prefix['approved_inventory']==current['approved_inventory']and prefix['start_kind']==current['start_kind'],'ONE_EXACT_QUEUE_PLAN')
    if prefix['record_id']is not None:e.need(all(prefix[k]==current[k]for k in('record_id','concept_id','creation_receipt','first_owned_draft','first_owned_legacy_draft','inherited_inventory')),'ONE_GENUINE_QUEUE_OWNERSHIP')
    e.need(len(prefix['attempts'])<=len(current['attempts']),'QUEUE_PREFIX_LENGTH')
    for a,b in zip(prefix['attempts'],current['attempts']):
        e.need(all(a[k]==b[k]for k in('operation_id','step','reservation')),'QUEUE_OPERATION_FORK')
        for k in('transport','validation'):
            if a[k]is not None:e.need(a[k]==b[k],'QUEUE_RECEIPT_FORK')
        if a['outcome']!='RESERVED':e.need(a['outcome']==b['outcome'],'NO_FAILED_OR_UNCERTAIN_PROMOTION')
    return True

def latest(root,plan_binding):
    root=Path(root).resolve(strict=True);_,plan=e.bound(root,plan_binding);ph=m.digest(plan);directory=Path(plan['execution_directory']);e.need(directory.is_absolute()and directory.resolve().is_relative_to(root/'reports/verification-coverage')and not any(p.is_symlink()for p in(directory,*directory.parents)),'CANONICAL_OWNED_QUEUE')
    if not directory.exists():return None
    candidates=[]
    for run in sorted(directory.iterdir()):
        e.need(run.is_dir()and not run.is_symlink(),'CLOSED_EXECUTION_DIRECTORY')
        saved=run/'PLAN.json';e.need(saved.is_file()and e.sha(saved)==plan_binding['sha256'],'EXACT_EXECUTION_PLAN_BYTES')
        paths=[p for p in(run/'BEFORE_CHECKPOINT.json',run/'CHECKPOINT.json')if p.exists()]
        folder=run/'checkpoints'
        if folder.exists():
            e.need(folder.is_dir()and not folder.is_symlink(),'CLOSED_CHECKPOINT_DIRECTORY');paths+=sorted(folder.glob('*.json'))
        e.need(paths,'PARTIAL_EXECUTION_REQUIRES_CHECKPOINT')
        for path in paths:
            own=e.binding(path);_,state=e.bound(root,own);m.validate(state,ph);candidates.append((own,state))
    if not candidates:return None
    rank=lambda pair:(len(pair[1]['attempts']),sum(a['outcome']=='STRICT_PASS'for a in pair[1]['attempts']))
    candidates.sort(key=rank);chosen=candidates[-1]
    for _,state in candidates:compatible(state,chosen[1])
    # Failure/uncertainty may not hide behind same-rank lexicographic selection.
    if any(s['phase']in{'HOLD','UNCERTAIN'}for _,s in candidates):e.need(chosen[1]['phase']in{'HOLD','UNCERTAIN'},'NO_HIDDEN_TERMINAL_HOLD')
    return chosen[0]
