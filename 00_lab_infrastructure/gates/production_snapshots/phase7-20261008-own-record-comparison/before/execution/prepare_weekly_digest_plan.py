"""Root-only immutable plan preparer inside the actual measured purpose session.

All source/API/merge/runtime bindings must already be genuine inputs. This
preparer does not discover IDs, publish, install, nominate or modify the SSOT.
"""
from pathlib import Path
import hashlib,json
import weekly_digest_executor as e
from weekly_digest_runtime import ActualRuntime
import methods_digest_registration as registrar
import digest_weekly_state as successor

CONFIG_FIELDS={'standard','canonical_root','package','current_runtime_closure','registration_recovery','predecessor_registration','source_legacy_receipt','source_native_receipt','source_native_before_create','source_origin','purpose_source_pins','authority','community_mirror_proof','runtime_consumer','recovery_consumer','source_session_consumer','ordinary_cohort_consumer','account_discovery','start_kind'}
def prepare(root,config_binding,output):
    root=Path(root).resolve(strict=True);_,config=e.bound(root,config_binding)
    e.need(isinstance(config,dict)and set(config)==CONFIG_FIELDS and config['standard']=='VRS-OWNED-DIGEST-ACTUAL-INPUTS-1'and config['canonical_root']==str(root),'ACTUAL_CLOSED_CONFIG')
    package=Path(config['package']);e.need(package.resolve(strict=True).is_relative_to(root),'OWN_ACTUAL_PACKAGE');manifest_binding=e.binding(package/'DIGEST_MANIFEST.json');_,manifest=e.bound(root,manifest_binding)
    _,legacy=e.bound(root,config['source_legacy_receipt']);_,native=e.bound(root,config['source_native_receipt']);source_id=str(legacy['response']['id']);parent=native['response']['parent']['id'];ledger=json.loads(e.raw(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))
    prior=registrar.require_registration(root,config['predecessor_registration'],ledger)
    rows=[]
    for name in sorted(e.machine.NAMES):
        p=package/name;raw=e.raw(p);rows.append({'name':name,'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'md5':hashlib.md5(raw).hexdigest()})
    plan={k:v for k,v in config.items()if k!='standard'}
    plan.update(standard='VRS-METHODS-DIGEST-GENERIC-WEEKLY-PLAN-1',status='ACTUAL_CURRENT_SOURCE_BOUND_NOT_EXECUTED',digest_manifest=manifest_binding,publication_binding=e.binding(package/'PUBLICATION_BINDING.json'),before_ssot_sha256=e.sha(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'),approved_inventory=rows,release_week=manifest['release_week'],predecessor_record_id=source_id,source_concept_id=parent,expected_concept_id=parent if config['start_kind']=='NEW_VERSION'else None,prior_run_ids=sorted(successor.registered_lineage_runs(prior,root=root))if config['start_kind']=='NEW_VERSION'else[],new_run_ids=[x['run_id']for x in manifest['notes']],boundary_module='weekly_digest_boundary.py',execution_directory=str(Path(output).parent/'executions'))
    e.require_plan(root,plan)
    ActualRuntime(root,plan).admission(plan,package)
    output=Path(output);e.need(output.is_absolute()and output.resolve().is_relative_to(root/'reports/verification-coverage')and not output.exists(),'NEW_IMMUTABLE_PLAN_OUTPUT')
    e.immutable(output,e.raw_json(plan));return e.binding(output)
if __name__=='__main__':raise SystemExit('HOLD: explicit root call inside actual merged purpose-source session only')
