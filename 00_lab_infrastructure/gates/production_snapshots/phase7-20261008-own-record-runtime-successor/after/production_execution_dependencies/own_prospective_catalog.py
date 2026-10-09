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
VERSION_SHA='964878bfa230615108c620b0b6b5eab863b0879d343c151db0ffa06a117ad882'
METHODS_SHA='5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5'
HELPER_SHA='517adb25a3073296b8aabd2267706beef602f7307bf390ebaa5d2db91ab89d6e'
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

if __name__=='__main__':raise SystemExit('HOLD: pure exact prospective reader; no automatic operation')
