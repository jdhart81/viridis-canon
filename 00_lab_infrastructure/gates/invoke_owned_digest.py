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
        import prepare_owned_digest_plan
        return prepare_owned_digest_plan.prepare(root,config_binding,output)

def continue_owned(root,plan_binding,output,token):
    root=Path(root).resolve(strict=True);_,raw=checked(root,plan_binding);plan=json.loads(raw)
    with session(root,plan):
        import owned_digest_executor as e
        import owned_digest_queue as queue
        import owned_digest_runtime as runtime
        checkpoint=queue.latest(root,plan_binding)
        return runtime.execute(plan_binding,output,token,checkpoint=checkpoint,reviewed_driver_sha256=next(r['sha256']for r in plan['purpose_source_pins']if r['name']=='owned_digest_executor.py'))
if __name__=='__main__':raise SystemExit('HOLD: explicit root call with actual installed closure and memory-only credential is required')
