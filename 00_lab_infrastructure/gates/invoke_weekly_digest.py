"""Light root-only entry using the unchanged exact source-session loader.

No token retrieval, automatic execution, hidden config or namespace bypass.
Root supplies actual canonical source-bound inputs and a memory-only token.
"""
import hashlib,json,types
from pathlib import Path

def read(path):
    p=Path(path)
    if not p.is_absolute()or not p.is_file()or any(q.is_symlink()for q in(p,*p.parents)):raise ValueError('HOLD_BOUND_INPUT_PATH')
    a=p.stat();raw=p.read_bytes();z=p.stat()
    if(a.st_ino,a.st_size,a.st_mtime_ns)!=(z.st_ino,z.st_size,z.st_mtime_ns):raise ValueError('HOLD_BOUND_INPUT_RACE')
    return raw

def checked(root,binding):
    if not isinstance(binding,dict)or set(binding)!={'path','sha256'}:raise ValueError('HOLD_EXACT_BOUND_INPUT')
    path=Path(binding['path']);raw=read(path)
    if not path.resolve(strict=True).is_relative_to(root)or hashlib.sha256(raw).hexdigest()!=binding['sha256']:raise ValueError('HOLD_CURRENT_BOUND_INPUT')
    return path,raw

def session(root,value):
    pins=value['purpose_source_pins'];binding=value['source_session_consumer'];p,raw=checked(root,binding)
    if not any(r['path']==str(p)and r['sha256']==binding['sha256']for r in pins):raise ValueError('HOLD_SOURCE_SESSION_NOT_PURPOSE_BOUND')
    m=types.ModuleType('_owned_exact_invocation_source_session');m.__file__=str(p);exec(compile(raw,str(p),'exec'),m.__dict__)
    m.verify_loaded(pins,root);return m.source_session(root,pins)

def prepare(root,config_binding,output):
    root=Path(root).resolve(strict=True);_,raw=checked(root,config_binding);value=json.loads(raw)
    with session(root,value):
        import prepare_weekly_digest_plan
        return prepare_weekly_digest_plan.prepare(root,config_binding,output)

def continue_owned(root,plan_binding,output,token):
    root=Path(root).resolve(strict=True);_,raw=checked(root,plan_binding);plan=json.loads(raw)
    with session(root,plan):
        import weekly_digest_executor as e
        import weekly_digest_queue as queue
        import weekly_digest_runtime as runtime
        checkpoint=queue.latest(root,plan_binding)
        return runtime.execute(plan_binding,output,token,checkpoint=checkpoint,reviewed_driver_sha256=next(r['sha256']for r in plan['purpose_source_pins']if r['name']=='weekly_digest_executor.py'))

def recover_owned_creation(root,*,plan_binding,old_plan_binding,old_hold_binding,first_legacy_binding,first_native_binding,output,token):
    """GET/download-only own-record re-admission; never retries the old POST.

    The output is a distinct current-plan queue seed. The held old checkpoint,
    its reservation and charged transport remain immutable historical evidence.
    The ordinary executor subsequently starts at the first inherited draft DROP.
    """
    root=Path(root).resolve(strict=True);_,raw=checked(root,plan_binding);plan=json.loads(raw)
    with session(root,plan):
        import weekly_digest_executor as e
        import weekly_digest_runtime as runtime
        import owned_creation_recovery as recovery
        out=Path(output)
        e.need(out.is_absolute()and out.parent==Path(plan['execution_directory'])and not out.exists()and not any(p.is_symlink()for p in(out,*out.parents)),'EXCLUSIVE_RECOVERY_SEED_DIRECTORY')
        _,old_hold=e.bound(root,old_hold_binding);original=old_hold['attempts'][0]['transport']
        actual=runtime.ActualRuntime(root,plan);package=e.require_plan(root,plan);actual.admission(plan,package)
        out.mkdir(parents=True,exist_ok=False)
        e.immutable(out/'PLAN.json',e.raw(Path(plan_binding['path'])))
        transport=actual.transport(token,out/'transport');boundary=actual.boundary(plan,package,transport,out)
        readmitted=boundary.readmit_creation(old_plan_binding=old_plan_binding,old_hold_binding=old_hold_binding,original_creation=original,first_legacy=first_legacy_binding,first_native=first_native_binding)
        state,receipt=recovery.recover(root,old_plan_binding=old_plan_binding,new_plan_binding=plan_binding,old_hold_binding=old_hold_binding,first_legacy_binding=first_legacy_binding,first_native_binding=first_native_binding,readmission_binding=readmitted)
        # This is retained read-only candidate evidence, not a checkpoint
        # recognized by the unchanged continuation queue or a success result.
        e.immutable(out/'RECOVERY_CANDIDATE.json',e.raw_json({'standard':recovery.STANDARD,'status':'READ_ONLY_RECOVERY_STAGED_PENDING_SOURCE_SESSION_EXIT','checkpoint':state,'recovery_receipt':receipt,'certifies':False}))
    # The unchanged source-session context performs final loaded/hash checks
    # on exit. Only successful exit may expose a queue seed or success receipt.
    e.immutable(out/'CHECKPOINT.json',e.raw_json(state));checkpoint=e.binding(out/'CHECKPOINT.json')
    e.immutable(out/'RECOVERY_RECEIPT.json',e.raw_json(receipt))
    result={'standard':recovery.STANDARD,'status':'EXPLICIT_EXISTING_OWN_DRAFT_RECOVERED_NO_MUTATION','record_id':state['record_id'],'concept_id':state['concept_id'],'old_hold':old_hold_binding,'plan':plan_binding,'checkpoint':checkpoint,'recovery_receipt':e.binding(out/'RECOVERY_RECEIPT.json'),'writes_attempted_this_invocation':0,'new_versions_created':0,'original_attempt_still_charged':True,'certifies':False,'ssot_writes':0}
    e.immutable(out/'RESULT.json',e.raw_json(result));return result
if __name__=='__main__':raise SystemExit('HOLD: explicit root call with actual installed closure and memory-only credential is required')
