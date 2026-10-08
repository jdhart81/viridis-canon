"""Ordinary checkpoint integration, no HTTP, certification or SSOT write.

Invoke only inside the actual complete measured purpose-source session.
Source staging and later deterministic review are separate calls/invocations.
The unchanged default consumers supply every eventual admission verdict.
"""
from pathlib import Path
from copy import deepcopy
import datetime as dt,hashlib,json
import nightly_minimal_policy as policy
import prepare_nightly_note as generator
import methods_digest as digest

STANDARD='VRS-NIGHTLY-MINIMAL-CHECKPOINT-PREPARATION-1'

def source_for_cycle(root,run,prior_cycle,before_metadata,source_pins,*,selection_invocation,selected_theorems=None,selection_at_utc=None):
    """Choose only the actual current certified row and exact exported statements."""
    root=Path(root).resolve(strict=True);run=policy.canonical_run(run);seen={}
    ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_raw=digest.read_regular(ledger_path);ledger=json.loads(ledger_raw)
    policy.need(ledger.get('tree_root')==str(root),'CURRENT_CANONICAL_TREE')
    rows=[r for r in ledger.get('run_entities',[])if r.get('id')==run]
    policy.need(len(rows)==1 and rows[0].get('status')=='CERTIFIED'and rows[0].get('certificate_valid')is True,'ELIGIBLE_CURRENT_MAIN_CERTIFICATE_ONLY')
    row=rows[0];cp=Path(row['certificate']);cp=cp if cp.is_absolute()else root/cp
    certificate,inspection=policy.snapshot_certificate(root,policy.binding(cp),run,seen)
    policy.fresh_target(root,run,policy.binding(cp),inspection,seen)
    names=[n['name']if isinstance(n,dict)else n for n in inspection['certified_theorems']]
    selected=names if selected_theorems is None else selected_theorems
    source_dir=Path(row['path']);source_dir=source_dir if source_dir.is_absolute()else root/source_dir
    policy.need(source_dir.resolve(strict=True).is_relative_to(root),'MIRROR_SOURCE_ONLY')
    basis=certificate.get('foundation_basis');policy.need(basis in{'INDEPENDENT','THEOREM','CONDITIONAL_PL_PD'},'CERTIFICATE_EXPLICIT_BASIS')
    source={'standard':policy.SOURCE_STANDARD,'status':'STAGED_SOURCE_NOT_REVIEW_OR_PUBLICATION_BOUND','run_id':run,'certificate':policy.binding(cp),'source_manuscript':policy.binding(source_dir/'paper.tex'),'before_metadata':deepcopy(before_metadata),'selected_theorems':deepcopy(selected),'foundation_basis':basis,'selection_at_utc':selection_at_utc or dt.datetime.now(dt.timezone.utc).isoformat(),'selection_invocation':selection_invocation,'prior_cycle':deepcopy(prior_cycle),'source_pins':deepcopy(source_pins),'source_generator_sha256':policy.source_sha(),'certifies':False}
    policy.source_values(root,source,seen)
    policy.need(digest.read_regular(ledger_path)==ledger_raw,'SSOT_CHANGED_DURING_SELECTION');policy.finish(seen)
    return source

def stage_checkpoint(root,note_path,run,prior_cycle,before_metadata,source_pins,*,selection_invocation,render,selected_theorems=None):
    source=source_for_cycle(root,run,prior_cycle,before_metadata,source_pins,selection_invocation=selection_invocation,selected_theorems=selected_theorems)
    result=generator.prepare_source(root,note_path,source,render=render)
    policy.need(result['status']=='EXACT_NIGHTLY_SCOPE_SOURCE_AND_PDF_STAGED_NOT_ADMITTED'and result['run_id']==run,'ACTUAL_SOURCE_STAGE_ONLY')
    return result

def review_checkpoint(root,note_path,authority,*,review_invocation):
    """Run later; actual generator/default reader creates binding or HOLD."""
    source=json.loads(digest.read_regular(Path(note_path)/'NIGHTLY_SCOPE_SOURCE.json'))
    policy.need(review_invocation!=source['selection_invocation'],'LATER_REVIEW_INVOCATION')
    return generator.admit(root,note_path,authority,review_invocation=review_invocation)

def new_note_specs(root,notes,authority,*,week,account_discovery,predecessor_registration=None):
    """Prepare an eligible cohort from real current default-admitted notes."""
    root=Path(root).resolve(strict=True)
    import digest_weekly_state as weekly
    proof=json.loads(digest.bound_file(root,account_discovery)[1]);discovery=weekly.require_account_discovery(proof,root=root)
    policy.need(proof['release_week']==week,'EXACT_DISCOVERED_WEEK')
    if discovery['status']=='EXISTING_WEEKLY_RECORD':
        policy.need(predecessor_registration is not None and proof['start_kind']=='NEW_VERSION','ACTUAL_LATEST_DEFAULT_PREDECESSOR_REQUIRED')
        import methods_digest_registration as registration
        admitted=registration.require_registration(root,predecessor_registration)
        policy.need(admitted['receipt']['record_id']==discovery['record_id']and admitted['receipt']['release_week']==week,'EXACT_DEFAULT_LATEST_WEEKLY_PREDECESSOR')
        prior=weekly.registered_lineage_runs(admitted,root=root)
    else:
        policy.need(discovery['status']=='NO_EXISTING_WEEKLY_RECORD'and proof['start_kind']=='CREATE_WEEK'and predecessor_registration is None and week!='2026-W41','FIRST_WEEK_COMPLETE_ABSENCE_ONLY');prior=set()
    policy.need(isinstance(notes,list)and notes,'NONEMPTY_NEW_NOTES')
    specs=[];seen=set()
    for note in notes:
        p=Path(note);policy.need(p.resolve(strict=True).is_relative_to(root),'CANONICAL_CURRENT_NOTE')
        # The default consumer must be called without an alternate admission
        # seam. No cached status or optional supplemental certificate is used.
        actual=digest.current_note_consumer(p,root,authority);run=policy.canonical_run(actual['run_id'])
        policy.need(actual['status']=='PUBLICATION_BOUND'and actual.get('exact_publication_binding')is True and run not in seen and run not in prior,'NEW_DEFAULT_ADMITTED_DISJOINT_NOTE')
        seen.add(run);specs.append({'run_id':run,'path':str(p)})
    return specs,discovery

def stage_weekly_package(root,out,week,notes,authority,source_metadata,publication_date,*,account_discovery,predecessor_registration=None,render):
    specs,discovery=new_note_specs(root,notes,authority,week=week,account_discovery=account_discovery,predecessor_registration=predecessor_registration)
    title=digest.week_title(week)if discovery['status']=='EXISTING_WEEKLY_RECORD'else None
    manifest=digest.prepare(root,out,week,specs,authority,source_metadata,publication_date,render=render,existing_title=title)
    current=digest.require_current(out,root)
    policy.need(current==manifest,'FRESH_UNCHANGED_METHODS_DIGEST_PACKAGE')
    return {'standard':STANDARD,'status':'ACTUAL_DEFAULT_NOTE_COHORT_AND_METHODS_PACKAGE_STAGED_NOT_PUBLISHED','package_path':str(out),'digest_manifest':digest.binding(Path(out)/'DIGEST_MANIFEST.json'),'release_week':week,'notes':[r['run_id']for r in specs],'start_kind':'NEW_VERSION'if discovery['status']=='EXISTING_WEEKLY_RECORD'else'CREATE_WEEK','account_discovery':deepcopy(account_discovery),'predecessor_registration':deepcopy(predecessor_registration),'certifies':False,'zenodo_writes':0,'ssot_writes':0}

if __name__=='__main__':raise SystemExit('HOLD: explicit actual measured checkpoint/root calls; no automatic credential, certification or publish')
