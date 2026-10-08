"""Root-only close descendant; exact prospective catalog read, no policy edits.

Original daeb execution, registry, scientific consumers, protected sources and
post-CAS disk readback remain unchanged. This is an ordinary caller adapter.
"""
from pathlib import Path
from contextlib import contextmanager
import copy,hashlib,importlib,json,os,re,types,struct,__future__
ROOT=Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
PREFIX='RESEARCH_PIPELINE_v2/verification_coverage_gates/'
DRIVER=Path('/private/tmp/phase7-same-concept-runtime-successor-20261008-v001/runtime_successor.py')
DRIVER_SHA='daeb140dc581104127f2e9eeacf6efb56f016ab381c0202a52ea67a97f183599'
COMPILER_LOADER_SHA='99453df4fc6f62cab92e4604765a0ca492a0ad89903a21789a292874c417db5f'
VERSION_SHA='9eb67790edfab0760601133a3994dc1dbb24f7aa60c44661804525abf330859f'
METHODS_SHA='5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5'
HELPER_SHA='e37ed3d0fe05aa4ecd178c9fb0c3bbec0c49eba203c89bdfa4d2e07ee851e121'
GIT_PATH='00_lab_infrastructure/gates/production_snapshots/phase7-20261008-prospective-catalog-close/after/production_execution_dependencies/prospective_catalog_close.py'
CHECKS={'gitleaks','report-only-consumers','verify-catalog','verify','verify-functions','lean-build-current','lean-build-p0','deposit-verify'}
INPUT_NAMES=('CONFIG.json','INSTALLED_AWAITING_CLOSURE.json','BEFORE_LEDGER.json','BEFORE_FULL35_PUBLICATIONS.json','BEFORE_ACTIVATION.json','PR_MERGED_READBACK.json','RAW_PR_MERGED_READBACK.json','MERGED_COMMIT.json','COMPLETE_MERGED_TREE.json','POLICY_VERSION_CATALOG.json','SOURCE_ORIGIN_PROOF.json')
FIELDS={'standard','canonical_root','original_install','output','expected_before_ssot_sha256','reviewed_helper_sha256','protected_after','merged_pr','merged_commit','merged_tree'}
_DESCRIPTORS=[]
class CloseHold(ValueError):pass
def need(v,r):
 if not v:raise CloseHold('HOLD_PROSPECTIVE_CLOSE_'+r)
def digest(b):return hashlib.sha256(b).hexdigest()
def encode(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n'
def exact(a,b):return encode(a)==encode(b)
def raw(path):
 p=Path(path);need(p.is_absolute()and '..'not in p.parts and p.is_file()and not any(x.is_symlink()for x in(p,*p.parents)),'EXACT_REGULAR_PATH');a=p.stat();b=p.read_bytes();z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns),'READ_RACE');return b
def binding(path):return {'path':str(path),'sha256':digest(raw(path))}
def relative(path):return {'path':str(Path(path).relative_to(ROOT)),'sha256':digest(raw(path))}
def read_binding(v,*,relative_only=False):
 need(isinstance(v,dict)and set(v)=={'path','sha256'}and isinstance(v['path'],str)and isinstance(v['sha256'],str)and re.fullmatch('[a-f0-9]{64}',v['sha256'])is not None,'CLOSED_BINDING');p=Path(v['path']);need('..'not in p.parts and(not relative_only or not p.is_absolute()),'BINDING_REPRESENTATION');p=p if p.is_absolute()else ROOT/p;b=raw(p);need(digest(b)==v['sha256'],'BOUND_BYTES');return p,b

class _CatalogReader:
 """Delegate every member except this one exact ledger read to real methods."""
 def __init__(self,original,path,before,view):self._original=original;self._path=path;self._before=before;self._view=view;self.reads=0
 def __getattr__(self,name):return getattr(self._original,name)
 def read_regular(self,value):
  if Path(value)==self._path:
   need(self._original.read_regular(self._path)==self._before,'DISK_CHANGED_DURING_PROSPECTIVE_READ');self.reads+=1;return self._view
  return self._original.read_regular(value)

_CODE_FIELDS=('co_argcount','co_posonlyargcount','co_kwonlyargcount','co_nlocals','co_stacksize','co_flags','co_code','co_consts','co_names','co_varnames','co_filename','co_name','co_qualname','co_firstlineno','co_linetable','co_lnotab','co_exceptiontable','co_freevars','co_cellvars')
def _code_value_exact(left,right):
 """Compare typed code values, independent of marshal interning/reference flags."""
 if type(left)is not type(right):return False
 if type(left)is types.CodeType:return all(_code_value_exact(getattr(left,n),getattr(right,n))for n in _CODE_FIELDS)
 if type(left)is tuple:return len(left)==len(right)and all(_code_value_exact(a,b)for a,b in zip(left,right))
 if type(left)is frozenset:
  unmatched=list(right)
  for a in left:
   hits=[i for i,b in enumerate(unmatched)if _code_value_exact(a,b)]
   if len(hits)!=1:return False
   unmatched.pop(hits[0])
  return not unmatched
 if type(left)is float:return struct.pack('!d',left)==struct.pack('!d',right)
 if type(left)is complex:return struct.pack('!dd',left.real,left.imag)==struct.pack('!dd',right.real,right.imag)
 if type(left)in(type(None),type(Ellipsis),bool,int,str,bytes):return left==right
 return False
def _compiled_function(module,source,name):
 # The unchanged 994 fresh-gates loader inherits this one fixed future flag.
 fn=getattr(module,name);code=compile(source,str(module.__file__),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True);expected=[c for c in code.co_consts if isinstance(c,types.CodeType)and c.co_name==name]
 need(len(expected)==1 and type(fn)is types.FunctionType and fn.__globals__ is vars(module)and _code_value_exact(fn.__code__,expected[0]),'UNCHANGED_FUNCTION:'+name)
 need(fn.__defaults__ is None and fn.__closure__ is None,'UNCHANGED_DEFAULTS_CLOSURE:'+name)
 if name=='implementation_for_note':need(type(fn.__kwdefaults__)is dict and set(fn.__kwdefaults__)=={'catalog_consumer'}and fn.__kwdefaults__['catalog_consumer']is module.current_catalog,'UNCHANGED_KWDEFAULTS:'+name)
 elif name=='validate':need(type(fn.__kwdefaults__)is dict and set(fn.__kwdefaults__)=={'now'}and fn.__kwdefaults__['now']is None,'UNCHANGED_KWDEFAULTS:'+name)
 else:need(fn.__kwdefaults__ is None,'UNCHANGED_KWDEFAULTS:'+name)

def _checked_source(module,name,sha):
 p=ROOT/(PREFIX+name);need(Path(module.__file__)==p and digest(raw(p))==sha,'EXACT_SOURCE:'+name)
 return raw(p)

@contextmanager
def prospective_catalog_reader(versions,ledger,*,expected_before_sha256,prospective_binding=None):
 """Local current_catalog clone plus original keyword consumer contract.

 Global versions.d and archival framing are never changed. The unchanged
 registry sees the physical old disk hash and exact physical proposal file.
 After CAS the original registry is used without a wrapper or facade.
 """
 path=ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json';before=raw(path);current=json.loads(before)
 need(isinstance(ledger,dict)and isinstance(current,dict),'LEDGER_OBJECTS');need(exact({k:v for k,v in ledger.items()if k!='enforcement_activation'},{k:v for k,v in current.items()if k!='enforcement_activation'}),'ONLY_ACTIVATION_DIFF_ALLOWED')
 need(isinstance(current.get('publication_entities'),list)and len(current['publication_entities'])==35 and len({r.get('id')for r in current['publication_entities']})==35 and all(r.get('enforcement_acceptable')is True for r in current['publication_entities']),'EXACT_ACCEPTABLE35_BEFORE')
 original=versions.d;need(isinstance(original,types.ModuleType),'UNWRAPPED_REAL_METHODS_MODULE');version_raw=_checked_source(versions,'phase7_policy_versions.py',VERSION_SHA);methods_raw=_checked_source(original,'methods_digest.py',METHODS_SHA)
 for n in('current_catalog','implementation_for_note'):_compiled_function(versions,version_raw,n)
 for n in('read_regular','digest'):_compiled_function(original,methods_raw,n)
 need(versions.current_catalog.__globals__ is vars(versions)and versions.current_catalog.__globals__.get('d')is original,'REAL_VERSION_READER_GLOBALS')
 helper=importlib.import_module('phase7_runtime_update');helper_raw=_checked_source(helper,'phase7_runtime_update.py',HELPER_SHA);_compiled_function(helper,helper_raw,'validate')
 _,actraw=read_binding(ledger.get('enforcement_activation'),relative_only=True);activation=json.loads(actraw);_,rt=read_binding(activation.get('authorized_runtime_update'),relative_only=True);runtime=json.loads(rt);_,orig=read_binding(runtime.get('original_activation'),relative_only=True)
 checked=helper.validate(ROOT,ledger,json.loads(orig));need(checked.get('profile')=='PHASE7_SCOPED_POLICY'and exact(checked.get('binding'),activation.get('authorized_runtime_update')),'ACTUAL_PROPOSED_RUNTIME_VALIDATION')
 different=not exact(ledger.get('enforcement_activation'),current.get('enforcement_activation'))
 original_impl=versions.implementation_for_note;original_catalog=versions.current_catalog;original_framing=versions._exact_authority_framing
 identities={('methods',n):getattr(original,n)for n in('read_regular','digest')};identities[('helper','validate')]=helper.validate
 view=encode(ledger);viewpath=None;viewraw=None;proxy=None;wrapper=None
 note={'mode':'PROSPECTIVE_PRE_CAS'if different else'REAL_DISK_UNWRAPPED','before_disk_sha256':digest(before),'view_sha256':digest(view),'global_methods_reader_changed':False,'global_framing_changed':False,'canonical_writes':0,'scientific_acceptance_changed':False}
 if different:
  need(isinstance(expected_before_sha256,str)and re.fullmatch('[a-f0-9]{64}',expected_before_sha256)is not None and digest(before)==expected_before_sha256,'EXACT_PRE_CAS_DISK_HASH')
  viewpath,viewraw=read_binding(prospective_binding);need(viewpath!=path and viewraw==view,'PHYSICAL_EXACT_PROSPECTIVE_LEDGER');note['prospective_ledger']=prospective_binding
  proxy=_CatalogReader(original,path,before,view)
  clone=types.FunctionType(original_catalog.__code__,{**vars(versions),'d':proxy},original_catalog.__name__,original_catalog.__defaults__,original_catalog.__closure__)
  def catalog_provider(tree,seen):
   need(Path(tree).resolve(strict=True)==ROOT.resolve(strict=True)and original.read_regular(path)==before and raw(viewpath)==viewraw,'PHYSICAL_INPUTS_CHANGED_DURING_CATALOG')
   result=clone(tree,seen)
   need(seen.get(str(path))==digest(view)and str(viewpath)not in seen,'EXACT_PROSPECTIVE_SEEN_INPUTS')
   seen[str(path)]=digest(before);seen[str(viewpath)]=digest(viewraw)
   need(original.read_regular(path)==before and raw(viewpath)==viewraw,'PHYSICAL_INPUTS_CHANGED_AFTER_CATALOG');return result
  def wrapped(note_path,tree,current_module,*,catalog_consumer=original_catalog):
   need(catalog_consumer is original_catalog,'DEFAULT_CATALOG_CONSUMER_ONLY')
   return original_impl(note_path,tree,current_module,catalog_consumer=catalog_provider)
  wrapper=wrapped;versions.implementation_for_note=wrapper
 try:yield note
 finally:
  changed=versions.implementation_for_note is not(wrapper if different else original_impl)
  versions.implementation_for_note=original_impl
  need(not changed and versions.d is original and versions.current_catalog is original_catalog and versions._exact_authority_framing is original_framing,'REGISTRY_IDENTITY_CHANGED')
  for n in('current_catalog','implementation_for_note'):_compiled_function(versions,version_raw,n)
  for n in('read_regular','digest'):
   need(getattr(original,n)is identities[('methods',n)],'METHODS_FUNCTION_IDENTITY_CHANGED:'+n);_compiled_function(original,methods_raw,n)
  need(helper.validate is identities[('helper','validate')],'HELPER_FUNCTION_IDENTITY_CHANGED');_compiled_function(helper,helper_raw,'validate')
  need(raw(path)==before,'DISK_CHANGED_BEFORE_READER_RETURN');need(raw(ROOT/(PREFIX+'phase7_policy_versions.py'))==version_raw and raw(ROOT/(PREFIX+'methods_digest.py'))==methods_raw and raw(ROOT/(PREFIX+'phase7_runtime_update.py'))==helper_raw,'SOURCE_CHANGED_BEFORE_READER_RETURN')
  if different:need(raw(viewpath)==viewraw,'PROSPECTIVE_INPUT_CHANGED_BEFORE_RETURN');note['redirected_reads']=proxy.reads

def rebased_inputs(config,pending,catalog,old_output,new_output,source_copies,pr_binding,catalog_binding):
 """Truthful descendant pointers; all original material and install facts exact."""
 old_output=Path(old_output);new_output=Path(new_output)
 need(config.get('output')==str(old_output)and pending.get('policy_version_catalog',{}).get('path')==str((old_output/'POLICY_VERSION_CATALOG.json').relative_to(ROOT)),'ORIGINAL_NAMESPACE')
 need(isinstance(source_copies,dict)and len(source_copies)==14,'EXACT14_SOURCE_COPIES');newconfig=copy.deepcopy(config);newconfig['output']=str(new_output);newpending=copy.deepcopy(pending);changed=[]
 for row in newpending['additional_modules']:
  if row['source']['path'].startswith(str((old_output/'after-additional').relative_to(ROOT))+'/'):
   name=str(Path(row['source']['path']).relative_to((old_output/'after-additional').relative_to(ROOT)));need(name in source_copies and source_copies[name]['sha256']==row['sha256'],'SOURCE_COPY_BYTE_IDENTITY');row['source']=source_copies[name];changed.append(name)
 need(len(changed)==14 and set(changed)==set(source_copies),'ONLY14_CHANGED_SOURCE_BINDINGS')
 newpending['pull_request_readback']=pr_binding;newpending['policy_version_catalog']=catalog_binding
 newcatalog=copy.deepcopy(catalog);need(len(newcatalog['versions'])==4 and newcatalog['versions'][-1]['execution_consumer_sha256']=='91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e','EXACT_FOURTH_CATALOG')
 newcatalog['versions'][-1]['pull_request_readback']=pr_binding
 need(exact(newcatalog['versions'][:-1],catalog['versions'][:-1]),'ORIGINAL_THREE_ARCHIVES_EXACT')
 return newconfig,newpending,newcatalog

def own_merge(config):
 _,prraw=read_binding(config['merged_pr']);pr=json.loads(prraw);_,cr=read_binding(config['merged_commit']);commit=json.loads(cr);_,tr=read_binding(config['merged_tree']);tree=json.loads(tr)
 need(pr.get('state')=='MERGED'and pr.get('baseRefName')=='main'and type(pr.get('number'))is int and pr['number']>0 and pr.get('url')=='https://github.com/jdhart81/viridis-canon/pull/'+str(pr['number'])and re.fullmatch('[a-f0-9]{40}',str(pr.get('headRefOid')))is not None and pr.get('mergeCommit',{}).get('oid')==commit.get('sha')and commit.get('tree',{}).get('sha')==tree.get('sha')and tree.get('truncated')is False,'ACTUAL_OWN_MERGED_TREE')
 checks=pr.get('statusCheckRollup');need(isinstance(checks,list)and CHECKS<={r.get('name')for r in checks if r.get('status')=='COMPLETED'and r.get('conclusion')=='SUCCESS'}and all(r.get('status')=='COMPLETED'and r.get('conclusion')in{'SUCCESS','SKIPPED'}for r in checks),'ALL_EXACT_HEAD_CHECKS')
 nodes=tree.get('tree');need(isinstance(nodes,list)and all(isinstance(r,dict)and isinstance(r.get('path'),str)for r in nodes)and len({r['path']for r in nodes})==len(nodes),'UNIQUE_MERGED_TREE_PATHS');rows={r['path']:r for r in nodes};source=raw(__file__);blob=hashlib.sha1(b'blob '+str(len(source)).encode()+b'\0'+source).hexdigest();need(rows.get(GIT_PATH,{}).get('type')=='blob'and rows[GIT_PATH].get('mode')in{'100644','100755'}and rows[GIT_PATH].get('sha')==blob,'EXACT_NEW_HELPER_MERGED_BLOB')
 return pr

def _write(path,data):
 p=Path(path);need(not p.exists()and not any(x.is_symlink()for x in(p,*p.parents)),'UNUSED_PRIVATE_EVIDENCE_PATH');p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb')as f:f.write(data);f.flush();os.fsync(f.fileno())
 need(raw(p)==data,'PRIVATE_COPY_READBACK')
def _seal(path,data):
 p=Path(path);stage=p.with_name(p.name+'.sealed-stage');_write(stage,data);fd=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);_DESCRIPTORS.append(fd)
 try:os.link(stage.name,p.name,src_dir_fd=fd,dst_dir_fd=fd,follow_symlinks=False)
 except BaseException:_DESCRIPTORS.remove(fd);os.close(fd);raise

def linked_close(config):
 """Explicit root operation after own source PR; no install/Zenodo capability."""
 need(isinstance(config,dict)and set(config)==FIELDS and config['standard']=='VRS-SAME-CONCEPT-PROSPECTIVE-CLOSE-CONFIG-1'and config['canonical_root']==str(ROOT),'CLOSED_ROOT_CONFIGURATION');need(config['reviewed_helper_sha256']==digest(raw(__file__)),'REVIEWED_NEW_HELPER');pr=own_merge(config)
 oldout=Path(config['original_install']);out=Path(config['output']);base=ROOT/'reports/verification-coverage/2026-10-08/first-digest-audited-catalog-backlog-v001';need(oldout==base/'same-concept-runtime-install-v001'and out==base/'same-concept-runtime-close-v002'and not out.exists(),'OWN_LINKED_DESCENDANT_NAMESPACE')
 before=raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json');need(digest(before)==config['expected_before_ssot_sha256'],'INITIAL_SSOT_CAS');originals={n:raw(oldout/n)for n in INPUT_NAMES};hold=raw(oldout/'CLOSURE_HOLD.json');h=json.loads(hold);need(h.get('status')=='HOLD_CLOSURE_NOT_ADMISSION'and h.get('failure')=='HOLD_RUNTIME_SUCCESSOR_ALL35_ACTUAL_ACCEPTABLE'and h.get('ssot_changed')is False,'EXACT_PRESERVED_FAILED_CLOSE')
 driverraw=raw(DRIVER);need(digest(driverraw)==DRIVER_SHA,'UNCHANGED_ORIGINAL_DRIVER');m=types.ModuleType('_root_original_close_driver');m.__file__=str(DRIVER);exec(compile(driverraw,str(DRIVER),'exec'),m.__dict__)
 oldconfig=json.loads(originals['CONFIG.json']);pending=json.loads(originals['INSTALLED_AWAITING_CLOSURE.json']);catalog=json.loads(originals['POLICY_VERSION_CATALOG.json']);_,prev=m.closed_relative_binding(oldconfig['predecessor_runtime']);m.require_pending(oldconfig,pending,json.loads(prev),oldout);need(pending['predecessor_ssot_sha256']==digest(before),'EXACT_INSTALLED_PREDECESSOR')
 m.closed_relative_binding(config['protected_after']);need(digest(raw(__file__))==config['reviewed_helper_sha256'],'HELPER_CHANGED_BEFORE_COPY')
 copies={}
 for name in m.INSTALL_NAMES:
  r=next(r for r in pending['additional_modules']if r['path']==m.PREFIX+name);_,b=m.closed_relative_binding(r['source']);need(digest(b)==r['sha256']and b==raw(ROOT/r['path']),'INSTALLED14_SOURCE_BYTES');copies[name]=b
 # No output exists until all provenance/material predicates above pass.
 out.mkdir(mode=0o700,exist_ok=False)
 def unchanged():
  need(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json')==before,'SSOT_CHANGED_BEFORE_LINKED_CLOSE');need(raw(DRIVER)==driverraw and digest(raw(__file__))==config['reviewed_helper_sha256'],'DRIVER_CHANGED');need(raw(oldout/'CLOSURE_HOLD.json')==hold and all(raw(oldout/n)==b for n,b in originals.items()),'OLD_EVIDENCE_CHANGED')
  for name,b in copies.items():need(raw(ROOT/(m.PREFIX+name))==b,'RUNTIME_CHANGED_DURING_EVIDENCE_COPY')
 for n,b in originals.items():
  if n not in{'CONFIG.json','INSTALLED_AWAITING_CLOSURE.json','POLICY_VERSION_CATALOG.json'}:unchanged();_write(out/n,b)
 for n,b in copies.items():unchanged();_write(out/'after-additional'/n,b)
 source_bindings={n:relative(out/'after-additional'/n)for n in copies};prbinding=relative(out/'PR_MERGED_READBACK.json')
 # Compute the exact successor catalog before its binding enters the pending.
 newcat=copy.deepcopy(catalog);newcat['versions'][-1]['pull_request_readback']=prbinding;catraw=encode(newcat);catbinding={'path':str((out/'POLICY_VERSION_CATALOG.json').relative_to(ROOT)),'sha256':digest(catraw)}
 newconfig,newpending,newcat=rebased_inputs(oldconfig,pending,catalog,oldout,out,source_bindings,prbinding,catbinding)
 for n,v in(('CONFIG.json',newconfig),('INSTALLED_AWAITING_CLOSURE.json',newpending),('POLICY_VERSION_CATALOG.json',newcat)):
  unchanged();_write(out/n,encode(v))
 proof={'status':'EXACT_LINKED_CLOSE_INPUTS_NO_RUNTIME_REINSTALL','original_install':str(oldout),'original_hold':binding(oldout/'CLOSURE_HOLD.json'),'original_input_bindings':{n:binding(oldout/n)for n in INPUT_NAMES},'descendant_input_bindings':{n:binding(out/n)for n in INPUT_NAMES},'changed_metadata_pointers':['CONFIG.output','fourth_catalog.pull_request_readback','pending.pull_request_readback','pending.policy_version_catalog','pending14.source'], 'original_install_timestamp_retained':True,'all14_material_bytes_equal':True,'runtime_writes_this_execution':0,'zenodo_writes':0,'certifies':False,'helper_source':binding(Path(__file__)),'helper_merged_pr':config['merged_pr'],'helper_merged_commit':config['merged_commit'],'helper_merged_tree':config['merged_tree']}
 unchanged();_write(out/'LINKED_INPUT_PROVENANCE.json',encode(proof));wrapped_calls=[];original_fresh=m.fresh35
 def scoped_fresh(corpus,ledger,rows,helper,original):
  versions=importlib.import_module('phase7_policy_versions')
  viewbinding=None
  disk=json.loads(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'))
  if not exact(disk.get('enforcement_activation'),ledger.get('enforcement_activation')):
   viewpath=out/'prospective-ledgers'/('view-'+str(len(wrapped_calls)+1)+'.json');_write(viewpath,encode(ledger));viewbinding=relative(viewpath)
  with prospective_catalog_reader(versions,ledger,expected_before_sha256=config['expected_before_ssot_sha256'],prospective_binding=viewbinding)as note:
   result=original_fresh(corpus,ledger,rows,helper,original)
  wrapped_calls.append(dict(note));return result
 m.fresh35=scoped_fresh
 try:result=m.close(out,config['protected_after'],reviewed_driver_sha256=DRIVER_SHA)
 finally:
  changed=m.fresh35 is not scoped_fresh;m.fresh35=original_fresh;need(not changed,'CLOSE_FUNCTION_REPLACED')
 need([r['mode']for r in wrapped_calls]==['PROSPECTIVE_PRE_CAS','PROSPECTIVE_PRE_CAS','REAL_DISK_UNWRAPPED'],'EXACT_PRECAS_AND_REAL_POSTCAS_ROUTE');need(all(raw(oldout/n)==b for n,b in originals.items())and raw(oldout/'CLOSURE_HOLD.json')==hold,'ORIGINAL_FAILURE_RETAINED');need(raw(DRIVER)==driverraw and digest(raw(__file__))==config['reviewed_helper_sha256'],'FINAL_SOURCE_RECHECK');own_merge(config)
 after=json.loads(raw(ROOT/'RESEARCH_PIPELINE_v2/corpus_ledger.json'));old=json.loads(before);need(exact(after['publication_entities'],old['publication_entities'])and after['premise_declaration_cutover_run']==old['premise_declaration_cutover_run'],'EXACT35_AND_CONTROL_AFTER_CAS');need(result['status']=='INSTALLED_ACTUAL_SOURCE_VALIDATOR_FRESH35_PROTECTED22_PASS'and type(result['ssot_writes'])is int and result['ssot_writes']==1,'ORIGINAL_CLOSE_REAL_PASS')
 receipt={'standard':'VRS-SAME-CONCEPT-PROSPECTIVE-CLOSE-EXECUTION-1','status':'ORIGINAL_DRIVER_REAL_FRESH35_POSTCAS_DISK_AND_CLOSURE_PASS','original_driver':binding(DRIVER),'new_helper':binding(Path(__file__)),'own_merged_pr':config['merged_pr'],'own_merged_commit':config['merged_commit'],'own_merged_tree':config['merged_tree'],'linked_input_provenance':binding(out/'LINKED_INPUT_PROVENANCE.json'),'preserved_original_hold':binding(oldout/'CLOSURE_HOLD.json'),'original_install':binding(oldout/'INSTALLED_AWAITING_CLOSURE.json'),'original_close_receipt':binding(out/'INSTALL_RECEIPT.json'),'current_runtime_closure':relative(out/'CURRENT_RUNTIME_CLOSURE.json'),'reader_calls':wrapped_calls,'all35_full_rows_preserved':True,'protected22_unchanged':True,'runtime_writes_this_execution':0,'original_runtime_writes':14,'ssot_writes':1,'zenodo_writes':0,'certificates_issued':0,'clean_nights_credited':0,'certifies':False}
 _seal(out/'CLOSE_EXECUTION_RECEIPT.json',encode(receipt));return receipt
if __name__=='__main__':raise SystemExit('HOLD: explicit root configuration, exact merged source PR and genuine installed/protected bindings required')
