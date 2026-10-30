"""Prospective fixed linked109 first installer, never the old fc58 installer.

Normal exact-head review/CI/merge/main gates and a separately reviewed bounded
Root whole-writer action precede --go. This module does not attest a source
session, all writers, process quiescence, scientific admission or publication.
The installed outer guard transition is a separate exact-source S4 operation;
old815 and every historical source/receipt are preserved, not patched in memory.
"""
from __future__ import annotations
import argparse,hashlib,json,os,stat,sys,types
from pathlib import Path

RUNTIME_SHA256 = 'f2da1589444d71821bcab46bfa7ade9c3af5893e2bb6521f565fb638a01b2445'
SUFFIX=('00_lab_infrastructure','gates','standalone_pdf_release','tools')


def need(value,reason):
    if not value:raise ValueError('HOLD_LINKED109_INSTALL_'+reason)


def read_regular(path,limit=4_000_000):
    p=Path(path).absolute();fds=[]
    try:
        d=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(d)
        for part in p.parts[1:-1]:
            d=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=d);fds.append(d)
        fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=d);fds.append(fd)
        first=os.fstat(fd);need(stat.S_ISREG(first.st_mode) and first.st_size<=limit,'REGULAR_BOUNDED_SOURCE')
        chunks=[];size=0
        while True:
            raw=os.read(fd,min(65536,limit+1-size))
            if not raw:break
            chunks.append(raw);size+=len(raw);need(size<=limit,'BOUNDED_SOURCE')
        raw=b''.join(chunks);last=os.fstat(fd);named=os.stat(p.name,dir_fd=d,follow_symlinks=False)
        frame=lambda s:(s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        need(frame(first)==frame(last)==frame(named) and size==last.st_size,'SOURCE_NAMED_FD_RACE')
        return raw
    finally:
        for fd in reversed(fds):os.close(fd)


def runtime_source():
    here=Path(__file__).absolute();need(here.parent.parts[-len(SUFFIX):]==SUFFIX,'FIXED_SOURCE_LAYOUT')
    path=here.parent.parent/'runtime/packaging_runtime.py';raw=read_regular(path)
    need(hashlib.sha256(raw).hexdigest()==RUNTIME_SHA256,'EXACT_EXECUTED_RUNTIME_DEPENDENCY')
    need('packaging_runtime' not in sys.modules,'NO_AMBIENT_RUNTIME_MODULE')
    module=types.ModuleType('_fixed_linked109_installer_runtime');module.__file__=str(path)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    need(read_regular(path)==raw,'RUNTIME_SOURCE_POSTLOAD_RACE');return module


def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def preflight(runtime,root,plan_binding):
    root=runtime.checked_root(root)
    runtime.need(root==runtime.SCIENTIFIC_ALIAS_PATH.parent/runtime.SCIENTIFIC_ALIAS_READLINK,'LINKED109_FIXED_CANONICAL_INSTALL_ROOT')
    _,raw,plan=runtime.object_at(root,plan_binding)
    proof=runtime.linked109_plan_proof(root,plan)
    row=plan['external_installer'];self_path=Path(__file__).absolute()
    runtime.need(Path(row['path'])==self_path and row['git_path']==runtime.LINKED109_INSTALLER_GIT_PATH
                 and row['sha256']==hashlib.sha256(read_regular(self_path)).hexdigest(),'LINKED109_GENUINE_EXECUTED_EXTERNAL_INSTALLER')
    target=root/runtime.PROFILE_PATH
    runtime.need(not target.parent.exists() and not target.parent.is_symlink(),'LINKED109_FIRST_INSTALL_TARGET_ABSENT')
    expected={'path':str(target.parent/runtime.LINKED109_DATA_NAME),'sha256':plan['adoption_source']['sha256']}
    runtime.need(plan['linked109_adoption']==expected,'LINKED109_PRECOMMITTED_INSTALLED_ADOPTION_BINDING')
    admission=runtime.linked109_admission(root,plan['adoption_source'],plan['source_origin'],installed=False)
    runtime.predecessor_installation(root)
    runtime.require_data_alias_observation(root,plan['data_alias_observation'])
    runtime.require_platform_timezone_observation(root,plan['platform_timezone_observation'])
    runtime.need(plan['historical_publisher']==runtime.HISTORICAL_PUBLISHER,'LINKED109_ORIGINAL_PUBLISHER_BINDING')
    publisher=runtime.read(root,plan['historical_publisher'])[1]
    authority=runtime.object_at(root,plan['user_authority'])[2]
    runtime.need(set(authority)=={'standard','source','user_text','captured_at_utc','scientific_scope_changes','provider_instruction'}
                 and authority['standard']=='VRS-DIRECT-USER-PDF-STANDARD-AUTHORITY-1'
                 and authority['source']=='Current user message in this Codex chat'
                 and authority['user_text']==runtime.USER_DIRECTIVE and authority['scientific_scope_changes'] is False,
                 'LINKED109_ORIGINAL_USER_AUTHORITY')
    runtime.need(runtime.sha(runtime.read(root,authority['provider_instruction'])[1])==runtime.PROVIDER_SHA,
                 'LINKED109_ORIGINAL_PROVIDER_AUTHORITY')
    installed=runtime.dt.datetime.fromisoformat(plan['installed_at_utc'].replace('Z','+00:00'))
    captured=runtime.dt.datetime.fromisoformat(authority['captured_at_utc'].replace('Z','+00:00'))
    runtime.need(installed.tzinfo is not None and captured.tzinfo is not None
                 and captured<=installed<=runtime.dt.datetime.now(runtime.dt.timezone.utc),'LINKED109_PREFLIGHT_TIME')
    runtime.read(root,plan['access_registry'])
    runtime.need(runtime.read(root,plan_binding)[1]==raw,'LINKED109_FINAL_PLAN_RACE')
    return plan,proof,admission,publisher


def open_directory(path):
    path=Path(path).absolute();fds=[]
    try:
        fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);fds.append(fd)
        for part in path.parts[1:]:
            fd=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);fds.append(fd)
        return fds
    except BaseException:
        for fd in reversed(fds):os.close(fd)
        raise


def exclusive(directory_fd,name,raw):
    need('/' not in name and name not in {'','.','..'},'CLOSED_OUTPUT_NAME')
    fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=directory_fd)
    try:
        frame=os.fstat(fd);remaining=memoryview(raw)
        while remaining:
            n=os.write(fd,remaining);need(n>0,'WRITE_PROGRESS');remaining=remaining[n:]
        os.fsync(fd);named=os.stat(name,dir_fd=directory_fd,follow_symlinks=False)
        need((named.st_dev,named.st_ino)==(frame.st_dev,frame.st_ino),'OWNED_OUTPUT_NAMED_INODE')
    finally:os.close(fd)
    os.fsync(directory_fd)
    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory_fd)
    try:
        first=os.fstat(fd);data=b''
        while len(data)<=len(raw):
            chunk=os.read(fd,min(65536,len(raw)+1-len(data)))
            if not chunk:break
            data+=chunk
        last=os.fstat(fd);named=os.stat(name,dir_fd=directory_fd,follow_symlinks=False)
        need(data==raw and (first.st_dev,first.st_ino)==(last.st_dev,last.st_ino)==(frame.st_dev,frame.st_ino)==(named.st_dev,named.st_ino),
             'EXACT_OWN_OUTPUT_READBACK')
    finally:os.close(fd)


def install(runtime,root,plan_binding,*,go=False):
    plan,proof,admission,publisher=preflight(runtime,root,plan_binding)
    if not go:return {'status':'LINKED109_PREFLIGHT_ONLY_NOT_INSTALLED','writes':0,'certifies':False}
    root=Path(root);target=root/runtime.PROFILE_PATH;fds=[];owned_fd=None
    # Whole-session writer exclusion and <=600 surviving action are REQUIRED
    # external Root operator preconditions. No DATA receipt impersonates them.
    try:
        fds=open_directory(target.parent.parent);parent_fd=fds[-1]
        os.mkdir(target.parent.name,0o700,dir_fd=parent_fd)
        owned_fd=os.open(target.parent.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=parent_fd);fds.append(owned_fd)
        created=os.fstat(owned_fd)
        def named_directory_current():
            current=open_directory(target.parent)
            try:
                final=os.fstat(current[-1]);need((final.st_dev,final.st_ino)==(created.st_dev,created.st_ino),'OWNED_INSTALL_DIRECTORY_FRAME')
            finally:
                for fd in reversed(current):os.close(fd)
        named_directory_current()
        exclusive(owned_fd,'INSTALL_PLAN.json',runtime.read(root,plan_binding)[1])
        exclusive(owned_fd,runtime.LINKED109_DATA_NAME,admission['adoption_raw'])
        installed=[]
        for row in plan['source_modules']:
            named_directory_current();raw=runtime.read(root,{k:row[k]for k in ('path','sha256')})[1]
            exclusive(owned_fd,row['name'],raw);installed.append({**row,'path':str(target.parent/row['name'])})
        os.mkdir('common',0o700,dir_fd=owned_fd)
        common=os.open('common',os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=owned_fd);fds.append(common);shared=[]
        for row in plan['shared_dependencies']:
            named_directory_current();raw=runtime.read(root,{k:row[k]for k in ('path','sha256')})[1]
            exclusive(common,row['name'],raw);shared.append({**row,'path':str(target.parent/'common'/row['name'])})
        again=runtime.linked109_admission(root,plan['adoption_source'],plan['source_origin'],installed=False)
        runtime.need(again['frames']==admission['frames'] and again['adoption_raw']==admission['adoption_raw'],
                     'LINKED109_PRENOMINATION_CURRENT_SOURCE_RACE')
        profile={k:v for k,v in plan.items()if k not in {'root_review','source_modules','historical_publisher','adoption_source'}}
        profile.update(standard=runtime.LINKED109_PROFILE,status=runtime.STATUS,modules=installed,shared_dependencies=shared,
            legacy_closure=runtime.LEGACY_CLOSURE,legacy_consumer=runtime.LEGACY_CONSUMER,legacy_scope=runtime.LEGACY_SCOPE,
            source_session_consumer=runtime.SESSION_CONSUMER,default_routes=runtime.DEFAULT_ROUTES)
        named_directory_current();profile_raw=encoded(profile);exclusive(owned_fd,target.name,profile_raw)
        bound={'path':str(target),'sha256':runtime.sha(profile_raw)}
        nomination={'standard':runtime.LINKED109_NOMINATION,'status':'EXACT_SOURCE_AND_DEFAULT_BINDINGS_INSTALLED_RUNTIME_READBACK_PENDING',
            'profile':bound,'installer_source':{k:plan['external_installer'][k]for k in ('path','sha256')},
            'merged_source_commit':proof['merge_commit'],'root_review_receipt':plan['root_review'],
            'linked109_adoption':plan['linked109_adoption']}
        runtime.need(runtime.read(root,plan['historical_publisher'])[1]==publisher,'LINKED109_HISTORICAL_PUBLISHER_PRESERVATION')
        named_directory_current();exclusive(owned_fd,Path(runtime.NOMINATION_PATH).name,encoded(nomination));named_directory_current()
        return {'status':'LINKED109_INSTALLED_PENDING_COLD_DEFAULT_GUARD_SCIENCE_READBACK','profile':bound,
                'executed_installer':nomination['installer_source'],'merged_source_commit':proof['merge_commit'],
                'current_source_counts':{'runtime':100,'purpose':131,'combined':152},'certifies':False,
                'zenodo_writes':0,'science_writes':0,'clean_night_credit':False}
    except BaseException:
        # Retain unknown/partial state, including constructor/binding failure.
        # No recursive cleanup, automatic replay or rollback of109/old sources.
        if owned_fd is not None:
            try:exclusive(owned_fd,'INSTALL_HOLD.json',encoded({'status':'PARTIAL_LINKED109_INSTALL_HOLD_RECONCILE_NO_RETRY','certifies':False}))
            except BaseException:pass
        raise
    finally:
        for fd in reversed(fds):os.close(fd)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',required=True,type=Path)
    parser.add_argument('--expected-plan-sha256',required=True);parser.add_argument('--go',action='store_true');args=parser.parse_args()
    need(os.environ.get('VIRIDIS_CORE_ROOT'),'EXPLICIT_CANONICAL_ROOT_REQUIRED')
    runtime=runtime_source();result=install(runtime,Path(os.environ['VIRIDIS_CORE_ROOT']),
       {'path':str(args.plan.absolute()),'sha256':args.expected_plan_sha256},go=args.go)
    print(json.dumps(result,sort_keys=True,indent=2));return 0


if __name__=='__main__':raise SystemExit(main())
