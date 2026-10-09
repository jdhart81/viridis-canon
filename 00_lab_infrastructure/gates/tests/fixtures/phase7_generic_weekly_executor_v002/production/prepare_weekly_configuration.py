"""Root-only pure construction of genuine generic weekly executor inputs.

No API/credential access or automatic write. emit_inputs is explicit root work;
actual invoke_weekly_digest.prepare still reruns independent runtime/default gates.
"""
from pathlib import Path
import hashlib,json,os,re,types

ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
CORE={'weekly_pending_discovery.py','runtime_closure_view.py', 'weekly_digest_queue.py', 'digest_metadata.py', 'publisher_previews.py', 'publisher_recovery.py', 'invoke_weekly_digest.py', 'weekly_checkpoint_replay.py', 'weekly_digest_executor.py', 'digest_weekly_state.py', 'owned_legacy_preview_aliases.py', 'first_digest_publisher.py', 'owned_prior_legacy.py', 'owned_weekly_discovery.py', 'mutation_journal_writer.py', 'readonly_account.py', 'weekly_digest_boundary.py', 'weekly_digest_runtime.py', 'owned_journal_writer.py', 'prepare_weekly_digest_plan.py', 'prepare_weekly_configuration.py', 'weekly_archive_wait.py', 'owned_digest_machine.py', 'first_digest_state.py', 'capture_weekly_inputs.py'}
ROLES={'canonical_root','package','current_runtime_closure','registration_recovery','predecessor_registration','source_legacy_receipt','source_native_receipt','source_native_before_create','authority','community_mirror_proof','runtime_consumer','recovery_consumer','source_session_consumer','ordinary_cohort_consumer','account_discovery','start_kind'}
FIELDS=ROLES|{'standard','extra_purpose_sources','git_path_by_name','merged_pr','merged_commit','merged_tree'}
def need(v,r):
    if not v:raise ValueError('HOLD_'+r)
def raw(p):
    p=Path(p);need(p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'REGULAR_BOUND_SOURCE');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'SOURCE_READ_RACE');return b
def bound_raw(root,binding,*,relative=False):
    need(isinstance(binding,dict)and set(binding)=={'path','sha256'}and isinstance(binding['path'],str)and isinstance(binding['sha256'],str)and re.fullmatch('[0-9a-f]{64}',binding['sha256'])is not None,'EXACT_BINDING');p=Path(binding['path']);need((not p.is_absolute()and '..'not in p.parts)if relative else p.is_absolute(),'BINDING_PATH_REPRESENTATION');p=root/p if relative else p;b=raw(p);need(p.resolve(strict=True).is_relative_to(root)and hashlib.sha256(b).hexdigest()==binding['sha256'],'CURRENT_CANONICAL_BINDING');return p,b
def bound(root,binding,*,relative=False):
    p,b=bound_raw(root,binding,relative=relative);return p,json.loads(b)
def source_pin(root,row):
    need(isinstance(row,dict)and set(row)=={'name','path','sha256'},'EXACT_SOURCE_PIN');p=Path(row['path']);archive=re.fullmatch('archive_([0-9a-f]{64})_(.+[.]py)',row['name']);named=p.name==row['name']if archive is None else(p.name==archive[2]and p.parent.name==archive[1]and p.parent.parent.name=='policy_versions');need(named and p.resolve(strict=True).is_relative_to(root)and hashlib.sha256(raw(p)).hexdigest()==row['sha256'],'CURRENT_SOURCE_PIN');return dict(row)
def blob_sha(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def collect_extra_sources(root,current_runtime_closure,source_session_consumer,extra_paths):
    """Use the unchanged real collector, preserving measured primary paths.

    extra_paths is the exact root-adopted executor/original publisher/consumer
    pool, not inferred helpers. All flat runtime rows enter first; archived
    aliases stay exactly the current receipt table outside flat resolution.
    """
    root=Path(root).resolve(strict=True);need(root==ROOT.resolve(strict=True),'CANONICAL_ROOT_ONLY')
    _,closure=bound(root,current_runtime_closure,relative=True);runtime=closure['source_pins'];flat=[Path(r['path'])for r in runtime if not r['name'].startswith('archive_')]
    p,b=bound_raw(root,source_session_consumer);need(source_session_consumer['sha256']=='da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740','UNCHANGED_SOURCE_SESSION_BUILDER')
    builder=types.ModuleType('_root_unchanged_closure_collector');builder.__file__=str(p);exec(compile(b,str(p),'exec'),builder.__dict__)
    extras=[Path(v)for v in extra_paths];need(all(x.is_absolute()and x.resolve(strict=True).is_relative_to(root)for x in extras),'EXPLICIT_CANONICAL_PURPOSE_POOL')
    pins,edges,duplicates=builder.collect_closure(root,flat+extras,[],extra_sources=flat+extras,required=CORE|{'prepare_first_seven_plan.py','runtime_successor.py'})
    by={r['name']:r for r in runtime};need(all(by.get(r['name'],r)==r for r in pins),'EXACT_MEASURED_PRIMARY_PATHS')
    return [r for r in pins if r['name']not in by],edges,duplicates

def suggest_git_paths(root,pins,merged_tree,preferred_by_name=None):
    """Choose only actual complete-tree matching blob paths, never invent one.

    Returns a reviewable table for source_materials. Canonical gate/archive
    names are preferred; otherwise existing production snapshots precede
    tests. The subsequent complete own-merge consumer validates every byte.
    """
    _,tree=bound(Path(root),merged_tree);need(tree.get('truncated')is False,'COMPLETE_MERGED_TREE_REQUIRED');nodes=tree.get('tree');need(isinstance(nodes,list)and all(isinstance(n,dict)and isinstance(n.get('path'),str)for n in nodes)and len({n['path']for n in nodes})==len(nodes),'UNIQUE_COMPLETE_TREE_PATHS');preferred_by_name={}if preferred_by_name is None else preferred_by_name;need(isinstance(preferred_by_name,dict)and set(preferred_by_name)<={r['name']for r in pins},'EXPLICIT_SOURCE_PREFERENCES')
    out={}
    for row in pins:
        pin=source_pin(Path(root),row);name=pin['name'];blob=blob_sha(raw(pin['path']));paths=[n['path']for n in nodes if n.get('type')=='blob'and n.get('mode')in{'100644','100755'}and n.get('sha')==blob];need(paths,'OWN_MERGED_BLOB_MISSING:'+name)
        prefer=preferred_by_name.get(name)
        if prefer is not None:need(prefer in paths,'PREFERRED_PATH_IS_REAL_EXACT_BLOB:'+name);out[name]=prefer;continue
        archive=re.fullmatch('archive_([0-9a-f]{64})_(.+[.]py)',name);canonical='00_lab_infrastructure/gates/'+(f'policy_versions/{archive[1]}/{archive[2]}'if archive else name)
        out[name]=canonical if canonical in paths else sorted(paths,key=lambda p:('/production_snapshots/'not in p,'/test_fixtures/'in p,len(p),p))[0]
    return out

SOURCE_FIELDS={'canonical_root','current_runtime_closure','extra_purpose_sources','git_path_by_name','merged_pr','merged_commit','merged_tree','runtime_consumer','source_session_consumer'}
def source_materials(root,inputs):
    root=Path(root).resolve(strict=True);need(root==ROOT.resolve(strict=True)and isinstance(inputs,dict)and set(inputs)==SOURCE_FIELDS and inputs['canonical_root']==str(root),'CLOSED_PRE_CREDENTIAL_SOURCE_INPUTS')
    _,closure=bound(root,inputs['current_runtime_closure'],relative=True);runtime=closure.get('source_pins');need(isinstance(runtime,list)and runtime,'ACTUAL_MEASURED_TABLE_REQUIRED')
    extras=inputs['extra_purpose_sources'];need(isinstance(extras,list),'EXACT_PURPOSE_EXTRA_TABLE');byname={};paths={}
    for row in runtime+extras:
        row=source_pin(root,row);name=row['name'];need(name not in byname or byname[name]==row,'NO_SOURCE_NAMESPACE_CONFLICT');need(row['path']not in paths or paths[row['path']]==row,'NO_DUPLICATE_PATH_ALIAS');byname[name]=row;paths[row['path']]=row
    need(CORE<=set(byname),'COMPLETE_EXECUTOR_PURPOSE_GRAPH')
    for key in('runtime_consumer','source_session_consumer'):
        b=inputs[key];need(any(r['path']==b['path']and r['sha256']==b['sha256']for r in byname.values()),'BOUND_CONSUMER_HAS_OWN_SOURCE_ORIGIN:'+key)
    need(inputs['source_session_consumer']['sha256']=='da1856adeb85c36677fa5ff7ab91045bf606c1bebc3bc3943586ad6a38b1d740','UNCHANGED_SOURCE_SESSION_BUILDER')
    _,pr=bound(root,inputs['merged_pr']);_,commit=bound(root,inputs['merged_commit']);_,tree=bound(root,inputs['merged_tree']);need(pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr.get('number'))and re.fullmatch('[0-9a-f]{40}',str(pr.get('headRefOid')))is not None and pr.get('mergeCommit',{}).get('oid')==commit.get('sha')and commit.get('tree',{}).get('sha')==tree.get('sha')and tree.get('truncated')is False,'ACTUAL_COMPLETE_OWN_MERGE_TREE');nodes=tree.get('tree');need(isinstance(nodes,list)and all(isinstance(n,dict)for n in nodes),'ACTUAL_GIT_TREE');index={n['path']:n for n in nodes};need(len(index)==len(nodes),'UNIQUE_GIT_PATHS');mapping=inputs['git_path_by_name'];need(isinstance(mapping,dict)and set(mapping)==set(byname),'EXPLICIT_ALL_SOURCE_GIT_MAP')
    rows=[]
    for name,pin in sorted(byname.items()):
        git_path=mapping[name];need(isinstance(git_path,str)and not Path(git_path).is_absolute()and '..'not in Path(git_path).parts,'CANONICAL_GIT_PATH');node=index.get(git_path,{});sha=blob_sha(raw(pin['path']));need(node.get('type')=='blob'and node.get('mode')in{'100644','100755'}and node.get('sha')==sha,'EXACT_OWN_MERGED_GIT_BLOB:'+name);rows.append(dict(pin,git_path=git_path,git_blob_sha=sha))
    origin={'standard':'VRS-OWNED-DIGEST-MERGED-PURPOSE-SOURCE-1','status':'EXACT_MERGED_BLOBS_NOT_PUBLICATION_CLEARANCE','merged_pr':inputs['merged_pr'],'merged_commit':inputs['merged_commit'],'merged_tree':inputs['merged_tree'],'source_rows':rows}
    return [byname[name]for name in sorted(byname)],origin

def construct(root,inputs):
    root=Path(root).resolve(strict=True);need(root==ROOT.resolve(strict=True),'CANONICAL_ROOT_ONLY');need(isinstance(inputs,dict)and set(inputs)==FIELDS and inputs['standard']=='VRS-OWNED-DIGEST-CONFIG-CONSTRUCTION-1'and inputs['canonical_root']==str(root)and inputs['start_kind']in{'NEW_VERSION','CREATE_WEEK'},'EXACT_ACTUAL_WEEKLY_INPUTS')
    pins,origin=source_materials(root,{k:inputs[k]for k in SOURCE_FIELDS})
    for k in ROLES-{'canonical_root','package','current_runtime_closure','start_kind'}:bound_raw(root,inputs[k])
    for key in('recovery_consumer','ordinary_cohort_consumer'):
        b=inputs[key];need(any(r['path']==b['path']and r['sha256']==b['sha256']for r in pins),'BOUND_CONSUMER_HAS_OWN_SOURCE_ORIGIN:'+key)
    config={k:inputs[k]for k in ROLES};config.update(standard='VRS-OWNED-DIGEST-ACTUAL-INPUTS-1',purpose_source_pins=pins)
    return config,origin

def immutable(p,data):
    p=Path(p);need(not any(x.is_symlink()for x in(p,*p.parents)),'OUTPUT_SYMLINK');p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_EXCL|os.O_CREAT|os.O_WRONLY,0o600)
    with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
def encode(v):return json.dumps(v,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()+b'\n'
def binding(p):return {'path':str(p),'sha256':hashlib.sha256(raw(p)).hexdigest()}
def emit_inputs(root,inputs,out):
    root=Path(root).resolve(strict=True);out=Path(out);need(out.is_absolute()and out.resolve().is_relative_to(root/'reports/verification-coverage')and not out.exists(),'NEW_CANONICAL_INPUT_OUTPUT');config,origin=construct(root,inputs);out.mkdir(parents=True,exist_ok=False);origin_path=out/'MERGED_PURPOSE_SOURCE.json';immutable(origin_path,encode(origin));config['source_origin']=binding(origin_path);p=out/'ACTUAL_INPUTS.json';immutable(p,encode(config));return binding(p)
if __name__=='__main__':raise SystemExit('HOLD: explicit root call after actual merge/runtime/source readbacks only')
