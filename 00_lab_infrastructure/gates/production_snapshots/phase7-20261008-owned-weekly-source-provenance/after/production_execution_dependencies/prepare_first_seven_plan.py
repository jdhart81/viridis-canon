"""Root-only offline plan assembly from actual installed and merged sources.

No transport, credential lookup, certificate/note/SSOT write, or publication.
Only explicit --adopt copies the already reviewed executor, after Git blob
proof. This preparation is neither certification nor proof of publication.
"""
from __future__ import annotations
import argparse, ast, contextlib, hashlib, importlib.abc, importlib.machinery
import importlib.util, json, os, re, sys, types
from pathlib import Path
sys.dont_write_bytecode = True

ROOT = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
GATES = ROOT/'RESEARCH_PIPELINE_v2/verification_coverage_gates'
OUT = ROOT/'reports/verification-coverage/2026-10-07/phase7-decoupled-execution-v001'
SOURCE = Path('/private/tmp/viridis-phase7-community-serialization/00_lab_infrastructure/gates/production_snapshots/phase7-20261007-first-digest-community-api-v001/after/production_execution_dependencies')
REVIEWED_PRODUCTION_HELPER_DIR = Path('/private/tmp/viridis-f2f-delivery/00_lab_infrastructure/gates')
PR_NUMBER = 62
GIT_PREFIX = '00_lab_infrastructure/gates/production_snapshots/phase7-20261007-first-digest-community-api-v001/after/production_execution_dependencies/'
FREEZE_SHA = 'c8d5c371830c7ade86363e9274dd1a7b9d07bf4ee387ff4ae3c76117eaa41c4f'
DRIVER_SHA = '551674f989688a5076d49308044c46e3294421fadf2c205381f20e14544631ba'
POLICY_SHA = '053f9aa1184116ec59f381737649a3b09113f50f7c79fb8d6328a079aa8c19c7'
ORIGINAL_BINDING_SHA = '1fb3d5bc1d0df57445b8d7fed8a034e7bab7f1aeb0314db21e3cedd5e237df2e'
CHECKS = {'report-only-consumers','verify-catalog','verify-functions','verify','deposit-verify','lean-build-current','lean-build-p0','gitleaks'}
RUNS = ['Run-125','Run-126','Run-128','Run-129','Run-131','Run-134','Run-141']
HELPERS = {'first_digest_publisher.py','first_digest_state.py','readonly_account.py','mutation_journal_writer.py','publisher_previews.py','publisher_recovery.py','digest_metadata.py'}
FILES = HELPERS|{'test_coordinator.py','test_publisher_guards.py','INHERITED_SOURCES.json','TESTS.json','ROOT_EXECUTION_NOTES.md','API_ENCODING.md','API_PAYLOAD_PROJECTION_PROOF.json','CLOSURE_CONSUMER_FIXTURE.json','COMMUNITY_613086_FIXTURE.json','COMMUNITY_API_AUTHORITY.json','SOURCE_BASELINE_PROOF.json','SOURCE_CHANGE_PINS.json','UNCHANGED_BODY_PINS.json','test_community_api_encoding.py'}
PIN_REQUIRED = {'methods_digest.py','phase7_audit_policy.py','phase7_mutation_baseline.py','zenodo_transport.py','server_managed_fields.py','publication_preservation.py','file_byte_metadata.py','scoped_release.py','certificate_inspection.py','nonvacuity_tier0.py','probe_observations.py','phase7_claim_label_render.py','digest_metadata.py','first_digest_state.py','readonly_account.py','mutation_journal_writer.py','publisher_previews.py','publisher_recovery.py','phase7_policy_versions.py','methods_digest_registration.py','mirror_parity.py'}
HUB_HELPERS = ROOT/'reports/verification-coverage/2026-10-05/game-plan-completion/canon-hub-successor-execution-v003'
PRESERVATION = ROOT/'reports/verification-coverage/2026-10-04/game-plan-completion/late-version-chain-consolidated-review-v004/implementation/publication_preservation.py'
APPROVED_HELPERS = {
    'zenodo_transport.py': (HUB_HELPERS/'zenodo_transport.py','69bcfa0c7008f052a0c30d06d23e94a226c5b40707905550e41c40e16c379b65'),
    'server_managed_fields.py': (HUB_HELPERS/'server_managed_fields.py','ce8ad2002a11938966201a44d2714ee866bb922649cd572e36f09e8cc0f062a1'),
    'file_byte_metadata.py': (HUB_HELPERS/'file_byte_metadata.py','4a21de5efd74531b135682f92ce4d49b1d8ad71d044795548ea9877756fa50ef'),
    'publication_preservation.py': (PRESERVATION,'4fb48f40fd76cae1f973dca66253813bfd1c8edcdffa07c02945d28ddf170e2b'),
}

class PlanHold(ValueError): pass
def require(v, reason):
    if not v: raise PlanHold('HOLD_'+reason)
def raw_json(v): return json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False).encode()+b'\n'
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def read(p):
    p=Path(p); require(p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'REGULAR_UNSYMLINKED_FILE:'+str(p))
    a=p.stat(); raw=p.read_bytes(); z=p.stat()
    require((a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_ino,z.st_size,z.st_mtime_ns),'SOURCE_READ_RACE')
    return raw
def sha(p): return sha_bytes(read(p))
def binding(p): return {'path':str(Path(p).resolve(strict=True)),'sha256':sha(p)}
def bind_read(root,v):
    require(isinstance(v,dict)and set(v)=={'path','sha256'},'CLOSED_BINDING')
    p=Path(v['path']); p=p if p.is_absolute()else Path(root)/p
    require(p.resolve(strict=True).is_relative_to(Path(root).resolve(strict=True)),'SOURCE_CONTAINMENT')
    b=read(p); require(sha_bytes(b)==v['sha256'],'SOURCE_HASH_CHANGED'); return p.resolve(),b
def immutable(p,raw):
    p=Path(p);require(not any(x.is_symlink()for x in(p,*p.parents)),'OUTPUT_SYMLINK')
    p.parent.mkdir(parents=True,exist_ok=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb')as f:f.write(raw);f.flush();os.fsync(f.fileno())
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def prove_executor(source,pr,*,freeze_sha=FREEZE_SHA,git_prefix=GIT_PREFIX):
    """Every adopted byte must be the own merged PR's exact Git blob."""
    source=Path(source);fraw=read(source/'FREEZE.json');require(sha_bytes(fraw)==freeze_sha,'REVIEWED_FREEZE_HASH')
    frozen=json.loads(fraw);rows=frozen.get('files')
    require(frozen.get('standard')=='VRS-PHASE7-OFFLINE-PUBLISHER-FREEZE-1'and frozen.get('status')=='TESTED_OFFLINE_NOT_EXECUTED','REVIEWED_EXECUTOR_FREEZE')
    require(isinstance(rows,list)and len(rows)==21 and {r.get('filename')for r in rows}==FILES,'EXACT_TWENTYONE_EXECUTOR_FILES')
    require(pr.get('number')==PR_NUMBER and pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(PR_NUMBER)and re.fullmatch('[a-f0-9]{40}',str(pr.get('mergeCommit',{}).get('oid')))is not None,'OWN_MERGED_COMMUNITY_API_PR')
    checks=pr.get('statusCheckRollup');require(isinstance(checks,list)and CHECKS<={c.get('name')for c in checks if isinstance(c,dict)and c.get('status')=='COMPLETED'and c.get('conclusion')=='SUCCESS'}and all(isinstance(c,dict)and c.get('status')=='COMPLETED'and c.get('conclusion')in {'SUCCESS','SKIPPED'}for c in checks),'EXACT_HEAD_CHECKS_COMPLETE')
    files=pr.get('files');require(isinstance(files,list)and files and all(isinstance(r,dict)for r in files),'MERGED_GIT_FILES')
    mapping={r.get('path'):r for r in files};require(len(mapping)==len(files),'UNIQUE_MERGED_GIT_FILES')
    result=[]
    for row in rows:
        require(isinstance(row,dict)and set(row)=={'filename','bytes','sha256'},'CLOSED_FREEZE_ROW')
        name=row['filename'];raw=read(source/name)
        require(len(raw)==row['bytes']and sha_bytes(raw)==row['sha256'],'REVIEWED_EXECUTOR_BYTES:'+name)
        require(mapping.get(git_prefix+name,{}).get('sha')==blob(raw),'OWN_MERGED_EXECUTOR_BLOB:'+name)
        result.append({'filename':name,'sha256':row['sha256'],'git_path':git_prefix+name,'git_blob_sha':blob(raw)})
    require(mapping.get(git_prefix+'FREEZE.json',{}).get('sha')==blob(fraw),'OWN_MERGED_FREEZE_BLOB')
    require(next(r['sha256']for r in result if r['filename']=='first_digest_publisher.py')==DRIVER_SHA,'REVIEWED_DRIVER_SHA')
    return result

def adopt_executor(root,source,dest,pr_binding,*,adopt=False):
    _,raw=bind_read(root,pr_binding);pr=json.loads(raw);rows=prove_executor(source,pr)
    dest=Path(dest);require(dest.resolve().is_relative_to(Path(root).resolve(strict=True)),'EXECUTOR_DESTINATION_CONTAINMENT')
    expected={r['filename']:r['sha256']for r in rows};expected['FREEZE.json']=FREEZE_SHA
    if not dest.exists():
        require(adopt,'EXECUTOR_NOT_ADOPTED_AFTER_MERGE')
        # Source, all blob mappings, and checks are proved before first copy.
        for name,h in expected.items():require(sha(Path(source)/name)==h,'SOURCE_CHANGED_BEFORE_ADOPTION')
        dest.mkdir(parents=True,exist_ok=False)
        for name,h in expected.items():immutable(dest/name,read(Path(source)/name))
        receipt={'standard':'VRS-PHASE7-REVIEWED-EXECUTOR-ADOPTION-1','status':'OWN_MERGED_BLOBS_ADOPTED_NOT_EXECUTED','pull_request_readback':pr_binding,'reviewed_freeze_sha256':FREEZE_SHA,'files':rows,'network_writes':0,'certifies':False}
        immutable(dest/'ADOPTION_RECEIPT.json',raw_json(receipt))
    require({p.name for p in dest.iterdir()}==set(expected)|{'ADOPTION_RECEIPT.json'},'CLOSED_ADOPTED_EXECUTOR_DIRECTORY')
    for name,h in expected.items():require(sha(dest/name)==h,'ADOPTED_EXECUTOR_CHANGED:'+name)
    receipt=json.loads(read(dest/'ADOPTION_RECEIPT.json'))
    require(receipt.get('pull_request_readback')==pr_binding and receipt.get('files')==rows and receipt.get('reviewed_freeze_sha256')==FREEZE_SHA,'ADOPTION_PROVENANCE_DIFFERS')
    return rows

def own_imports(raw,index):
    names=set();tree=ast.parse(raw)
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):names.update(a.name.split('.')[0]for a in node.names)
        elif isinstance(node,ast.ImportFrom):
            require(node.level==0,'RELATIVE_OWN_IMPORT_UNSUPPORTED')
            if node.module:names.add(node.module.split('.')[0])
        elif isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=='import_module'and node.args and isinstance(node.args[0],ast.Constant)and isinstance(node.args[0].value,str):names.add(node.args[0].value.split('.')[0])
    return names&set(index)

def collect_closure(root,seeds,search_dirs,*,extra_sources=(),required=PIN_REQUIRED):
    """Resolve own flat imports once; conflicting own basenames fail closed."""
    root=Path(root).resolve(strict=True);index={};duplicates={}
    candidates=[]
    for folder in search_dirs:
        folder=Path(folder);require(folder.resolve(strict=True).is_relative_to(root),'OWN_SEARCH_DIRECTORY')
        candidates.extend(p for p in sorted(folder.glob('*.py'))if not p.name.startswith('test_'))
    candidates.extend(Path(p)for p in extra_sources)
    for p in candidates:
        require(p.resolve(strict=True).is_relative_to(root),'OWN_EXTRA_SOURCE')
        row={'name':p.name,**binding(p)};old=index.get(p.stem)
        if old is not None:
            require(old['sha256']==row['sha256'],'CONFLICTING_OWN_MODULE:'+p.stem)
            if old['path']!=row['path']:duplicates.setdefault(p.name,[]).append(row)
        else:index[p.stem]=row
    pending={Path(p).stem for p in seeds};require(all(n in index for n in pending),'MISSING_OWN_SEED_MODULE')
    selected={};edges={}
    while pending:
        name=sorted(pending)[0];pending.remove(name)
        if name in selected:continue
        row=index[name];selected[name]=row
        imports=own_imports(read(row['path']),index);edges[row['name']]=sorted(n+'.py'for n in imports)
        pending|=imports-set(selected)
    pins=[selected[n]for n in sorted(selected)]
    require(required<={r['name']for r in pins},'ACTUAL_COMPLETE_CONSUMER_CLOSURE_REQUIRED')
    for row in pins:require(sha(row['path'])==row['sha256'],'CLOSURE_CHANGED_BEFORE_RETURN')
    return pins,edges,duplicates

def verify_loaded(pins,root):
    byname={r['name'][:-3]:r for r in pins};bypath={r['path']:r for r in pins};root=Path(root).resolve(strict=True)
    for name,module in list(sys.modules.items()):
        source=getattr(module,'__file__',None)
        if name in byname:
            require(source is not None and str(Path(source).resolve())==byname[name]['path'],'FOREIGN_OR_CONFLICTING_OWN_IMPORT:'+name)
            require(sha(source)==byname[name]['sha256'],'IMPORTED_OWN_SOURCE_CHANGED:'+name)
        elif source and Path(source).resolve().is_relative_to(root):
            own=bypath.get(str(Path(source).resolve()));require(own is not None,'UNPINNED_OWN_IMPORT:'+name)
            require(sha(source)==own['sha256'],'DYNAMIC_OWN_SOURCE_CHANGED:'+name)

class SourceLoader(importlib.abc.Loader):
    def __init__(self,path,expected):self.path=Path(path);self.expected=expected
    def create_module(self,spec):return None
    def exec_module(self,module):
        raw=read(self.path);require(sha_bytes(raw)==self.expected,'PINNED_IMPORT_CHANGED');module.__file__=str(self.path)
        exec(compile(raw,str(self.path),'exec'),module.__dict__)
        require(sha(self.path)==self.expected,'PINNED_IMPORT_CHANGED_DURING_LOAD')
class SourceFinder(importlib.abc.MetaPathFinder):
    def __init__(self,root,pins):self.root=Path(root);self.byname={r['name'][:-3]:r for r in pins}
    def find_spec(self,name,path=None,target=None):
        if name in self.byname:
            row=self.byname[name];return importlib.util.spec_from_loader(name,SourceLoader(row['path'],row['sha256']),origin=row['path'])
        spec=importlib.machinery.PathFinder.find_spec(name,path);origin=getattr(spec,'origin',None)
        if origin and origin not in {'built-in','frozen'}and Path(origin).resolve().is_relative_to(self.root):raise PlanHold('HOLD_UNPINNED_OWN_SOURCE_IMPORT:'+name)
        return None

@contextlib.contextmanager
def source_session(root,pins):
    """Reject foreign cached own modules; source-load even direct-file aliases."""
    verify_loaded(pins,root);finder=SourceFinder(root,pins);sys.meta_path.insert(0,finder)
    oldspec=importlib.util.spec_from_file_location;byfile={r['path']:r for r in pins}
    def exact_spec(name,location,*,loader=None,submodule_search_locations=None):
        p=Path(location).resolve();row=byfile.get(str(p))
        if p.is_relative_to(Path(root).resolve()):
            require(row is not None,'UNPINNED_DIRECT_OWN_IMPORT:'+name)
            require(loader is None,'FOREIGN_DIRECT_OWN_LOADER')
            return importlib.util.spec_from_loader(name,SourceLoader(p,row['sha256']),origin=str(p))
        return oldspec(name,location,loader=loader,submodule_search_locations=submodule_search_locations)
    importlib.util.spec_from_file_location=exact_spec
    try:yield
    finally:
        importlib.util.spec_from_file_location=oldspec
        if finder in sys.meta_path:sys.meta_path.remove(finder)
        verify_loaded(pins,root)
        for row in pins:require(sha(row['path'])==row['sha256'],'RUNTIME_CLOSURE_CHANGED')

def runtime_inputs(root):
    root=Path(root);ledger=json.loads(read(root/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))
    _,raw=bind_read(root,ledger['enforcement_activation']);wrapper=json.loads(raw)
    _,raw=bind_read(root,wrapper['authorized_runtime_update']);update=json.loads(raw)
    require(update.get('profile')=='PHASE7_SCOPED_POLICY','CURRENT_POLICY_NOT_INSTALLED')
    _,raw=bind_read(root,update['original_activation']);original=json.loads(raw)
    require(isinstance(update.get('runtime_targets'),list)and len(update['runtime_targets'])==22,'ORIGINAL_TWENTYTWO_RUNTIME_TARGETS')
    seeds=[]
    for row in update['runtime_targets']:
        p,_=bind_read(root,{'path':row['path'],'sha256':row['after_sha256']});seeds.append(p)
    require(len(set(seeds))==22,'UNIQUE_ORIGINAL_RUNTIME_TARGETS')
    # Archived version files are proved by the current installed catalog, never
    # substituted for the current basename import sources.
    for row in update['additional_modules']:
        p,_=bind_read(root,{'path':row['path'],'sha256':row['sha256']})
        if p.suffix=='.py'and p.parent==root/'RESEARCH_PIPELINE_v2/verification_coverage_gates':seeds.append(p)
    require(sha(root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/phase7_audit_policy.py')==POLICY_SHA,'CURRENT_MINIMAL_POLICY_SHA')
    require(sha(root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py')==ORIGINAL_BINDING_SHA,'ACTUAL_ORIGINAL_PUBLICATION_BINDING_SHA')
    return ledger,update,original,seeds

def production_helper_proof():
    """Bind the existing executed Hub's source pins; never execute its driver."""
    driver=read(HUB_HELPERS/'DRIVER.py');helpers=read(HUB_HELPERS/'REVIEWED_HELPERS.py');result=json.loads(read(HUB_HELPERS/'RESULT.json'))
    require(result.get('status')=='HUB_SUCCESSOR_PUBLISHED_STRICT_READBACK_PASS'and result.get('publication_verified')is True and result.get('driver_sha256')==sha_bytes(driver),'EXISTING_EXECUTION_DRIVER_PROVENANCE')
    require(sha_bytes(helpers)=='7efab194f3d6ade1744f7fdbd2bce798fee080ce6d33fc19e4ac25b45cf61182'and b"ENGINE_SHA='7efab194f3d6ade1744f7fdbd2bce798fee080ce6d33fc19e4ac25b45cf61182'"in driver,'EXISTING_EXECUTED_HELPER_PIN')
    pins=[ast.literal_eval(node.value)for node in ast.parse(helpers).body if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PINNED'for t in node.targets)]
    require(len(pins)==1,'EXACT_EXISTING_HELPER_PIN_DICTIONARY')
    for name,(path,h)in APPROVED_HELPERS.items():
        require(sha(path)==h,'APPROVED_EXISTING_HELPER_BYTES:'+name)
        require(sha(REVIEWED_PRODUCTION_HELPER_DIR/name)==h,'CURRENT_REVIEWED_HELPER_DIFFERS:'+name)
        if name!='publication_preservation.py':require(pins[0].get(name)==h,'EXISTING_EXECUTED_HELPER_SHA:'+name)
        else:require(("check(sha(G/'publication_preservation.py')=='"+h+"'").encode()in driver,'EXISTING_EXECUTED_PRESERVATION_PIN')
    return {'executed_hub_result':binding(HUB_HELPERS/'RESULT.json'),'executed_driver':binding(HUB_HELPERS/'DRIVER.py'),'executed_reviewed_helpers':binding(HUB_HELPERS/'REVIEWED_HELPERS.py'),'actual_approved_sources':[binding(p)for p,h in APPROVED_HELPERS.values()]}

def prepare(root=ROOT,*,merged_pr,merged_pr_sha,adopt=False,dependency_bindings=None):
    root=Path(root).resolve(strict=True);require(root==ROOT,'CANONICAL_ROOT_ONLY')
    pr_binding={'path':str(Path(merged_pr).resolve(strict=True)),'sha256':merged_pr_sha}
    dest=OUT/'first-digest-executor-v002';adopt_executor(root,SOURCE,dest,pr_binding,adopt=adopt)
    ledger,update,original,seeds=runtime_inputs(root)
    gates=root/'RESEARCH_PIPELINE_v2/verification_coverage_gates';pipeline=root/'RESEARCH_PIPELINE_v2'
    # All current actual flat gate modules are admitted as pinned inputs; G's
    # prepared successors are never used as installed runtime substitutes.
    seeds.extend(p for p in gates.glob('*.py')if not p.name.startswith('test_'))
    seeds.extend(dest/n for n in HELPERS);seeds.append(pipeline/'nightly_proof_track.py')
    require(isinstance(dependency_bindings,list)and {Path(v.get('path','')).name for v in dependency_bindings}=={'zenodo_transport.py','server_managed_fields.py','file_byte_metadata.py','publication_preservation.py'}and len(dependency_bindings)==4,'FOUR_ACTUAL_PRODUCTION_HELPER_BINDINGS')
    helper_proof=production_helper_proof();extras=[]
    for value in dependency_bindings:
        p,_=bind_read(root,value);approved,h=APPROVED_HELPERS[p.name]
        require(p==approved and value['sha256']==h,'EXACT_APPROVED_EXISTING_HELPER_BINDING:'+p.name)
        seeds.append(p);extras.append(p)
    # Preferred order selects the actual flat gate copy of identical helpers.
    search_dirs=list(dict.fromkeys([gates,pipeline,root/'_ZENODO_DEPOSITS',dest]))
    pins,edges,duplicates=collect_closure(root,seeds,search_dirs,extra_sources=extras)
    package=pipeline/'science_release_queue/digests/2026-W41-first-v002'
    manifest=json.loads(read(package/'DIGEST_MANIFEST.json'));before=manifest.get('source_metadata')
    sourcepair=OUT/'digest-source-readback-v002';vocab=OUT/'relation-vocabulary-readback-v002/RELATION_VOCABULARY_NATIVE.json'
    mirror=root/'reports/verification-coverage/2026-10-05/game-plan-completion/canon-hub-successor-execution-v003/COMMUNITY_MIRROR_PROOF.json'
    source_legacy=json.loads(read(sourcepair/'SOURCE_LEGACY.json'));source_native=json.loads(read(sourcepair/'SOURCE_NATIVE.json'));vocabulary=json.loads(read(vocab));community=json.loads(read(mirror))
    require(str(source_legacy.get('id'))=='21971052'and source_native.get('id')=='21971052','ACTUAL_SOURCE_21971052')
    require(vocabulary.get('id')=='1160576','ACTUAL_RELATION_VOCABULARY_1160576')
    require(community.get('record_id')=='613086','ACTUAL_COMMUNITY_FIXTURE_613086')
    plan={'standard':'VRS-PHASE7-FIRST-DIGEST-PUBLISH-PLAN-1','status':'FROZEN_READY_NOT_EXECUTED','canonical_root':str(root),'package_path':str(package),'digest_manifest':binding(package/'DIGEST_MANIFEST.json'),'digest_publication_binding':binding(package/'PUBLICATION_BINDING.json'),'source_before_metadata':before,'source_legacy':binding(sourcepair/'SOURCE_LEGACY.json'),'source_native':binding(sourcepair/'SOURCE_NATIVE.json'),'relation_vocabulary_source':binding(vocab),'community_mirror_proof':binding(mirror),'runtime_pins':pins,'expected_writes':9,'first_notes':RUNS}
    with source_session(root,pins):
        import phase7_runtime_update as runtime,phase7_policy_versions as versions,first_digest_publisher as executor
        current=runtime.validate(root,ledger,original);require(current.get('profile')=='PHASE7_SCOPED_POLICY','FRESH_INSTALLED_CLOSURE')
        versions.current_catalog(root,{})
        admitted=executor.Runtime(root,plan)
        try:
            prepared=executor.require_plan(root,package,plan)
            fresh=admitted.fresh(package,plan)
            require(isinstance(fresh,tuple)and len(fresh)==2,'ACTUAL_BOUND_DIGEST_CONSUMPTION')
        finally:admitted.close()
        executor.require_module_pins(root,pins)
    final=OUT/'first-seven-publication-plan-v003';require(not final.exists(),'IMMUTABLE_PLAN_EXISTS')
    final.mkdir(parents=True,exist_ok=False);immutable(final/'PLAN.json',raw_json(plan))
    closure={'standard':'VRS-PHASE7-ACTUAL-RUNTIME-IMPORT-CLOSURE-1','status':'ACTUAL_INSTALLED_SOURCES_PINS_PASS','enforcement_activation':binding(root/ledger['enforcement_activation']['path']),'runtime_update':{'path':str((root/json.loads(read(root/ledger['enforcement_activation']['path']))['authorized_runtime_update']['path']).resolve()),'sha256':json.loads(read(root/ledger['enforcement_activation']['path']))['authorized_runtime_update']['sha256']},'pins':pins,'edges':edges,'identical_own_copies':duplicates,'actual_production_helper_provenance':helper_proof,'executor_adoption':binding(dest/'ADOPTION_RECEIPT.json'),'builder':binding(__file__),'certifies':False}
    immutable(final/'RUNTIME_CLOSURE.json',raw_json(closure))
    result={'standard':'VRS-PHASE7-FIRST-SEVEN-PLAN-PREFLIGHT-1','status':'STRICT_REQUIRE_PLAN_AND_ACTUAL_DIGEST_BOUND_PASS_NOT_EXECUTED','plan':binding(final/'PLAN.json'),'runtime_closure':binding(final/'RUNTIME_CLOSURE.json'),'notes':RUNS,'expected_writes':9,'source_id':prepared['source_id'],'runtime_module_count':len(pins),'executor_driver_sha256':DRIVER_SHA,'network_writes':0,'certificates_issued':0,'notes_written':0,'ssot_writes':0,'certifies':False}
    immutable(final/'RESULT.json',raw_json(result));return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--merged-pr',required=True);parser.add_argument('--merged-pr-sha256',required=True);parser.add_argument('--production-helper-bindings',required=True);parser.add_argument('--adopt',action='store_true');args=parser.parse_args()
    deps=json.loads(read(args.production_helper_bindings))
    result=prepare(merged_pr=args.merged_pr,merged_pr_sha=args.merged_pr_sha256,adopt=args.adopt,dependency_bindings=deps)
    print(json.dumps(result,sort_keys=True))
