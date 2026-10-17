"""PRIVATE TEST ONLY loader: closed top-level DATA remaps; bodies/control flow exact."""
from __future__ import annotations
import ast,builtins,copy,hashlib,json,os,sys,types
from pathlib import Path
from build_source_chain import REPO,RUNTIME,sha,encoded,function_asts

LEGACY='00_lab_infrastructure/gates/production_snapshots/phase7-20261009-prior-content-runtime-successor/after/production_execution_dependencies/runtime_successor.py'
E9='00_lab_infrastructure/gates/production_snapshots/phase7-20261008-own-record-comparison/after-v005/runtime_successor.py'

class ClosedDataLoader:
 def __init__(self,root):
  self.root=Path(root).resolve();self.root.mkdir(exist_ok=False)
  self.known={};self.source_paths={};self.source_baselines={};self.remaps={};self.receipts=[];self.blocked=[]
  self.post_load_data={}
  self.explicit_extra_allowlist={'a15ef655091ebd72910a060cdef1d0f727d18b7a7223dcbbc2192c18e39fe57c':frozenset({'CONTROL_ROOT'}),'b63c3866db0e3538f6462ca32f0bbf916a6e80081d1bdf74514b1fa6c7dc2b06':frozenset({'LIVE_ROOT'}),'b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317':frozenset({'PRIOR_RUNTIME_SHA','PRIOR_CLOSURE_SHA'})}
  tree=ast.parse((RUNTIME/'packaging_runtime.py').read_bytes())
  rows=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(v,ast.Name)and v.id=='LEGACY_TRANSIENT_SOURCES'for v in n.targets))
  literal_map={}
  self.forbidden_legacy_roots=tuple(Path(row['target']).parent for row in rows)
  for row in rows:
   raw=(REPO/row['git_path']).read_bytes();assert sha(raw)==row['source']['sha256']
   target=self.capture(row['name'],raw);literal_map[row['target']]=target
  e9raw=(REPO/E9).read_bytes();legacyraw=(REPO/LEGACY).read_bytes()
  assert sha(e9raw)=='e9ad9d196fb6e384b96151226733ea5db42f490adb489bc265b02f58e135f498'
  assert sha(legacyraw)=='b52ad25d05298a6b3c166669e178df1f6f460665a9cc52816c899e1b28b88317'
  e9=self.capture('legacy_e9.py',e9raw)
  literal_map[self.path_literal(legacyraw,'PRIOR')]=e9
  rootrow=next(row for row in rows if row['name']=='manual_99453df4.py')
  rootraw=(REPO/rootrow['git_path']).read_bytes();assert sha(rootraw)==rootrow['source']['sha256']
  self.forbidden_core_root=Path(self.path_literal(rootraw,'ROOT'))
  self.forbidden_cowork_root=self.forbidden_core_root.parent
  self.legacy=self.capture('legacy_b52.py',legacyraw)
  for digest,(path,raw) in self.known.items():
   declared={}
   for n in ast.parse(raw).body:
    if not isinstance(n,ast.Assign)or len(n.targets)!=1 or not isinstance(n.targets[0],ast.Name):continue
    name=n.targets[0].id;value=n.value
    if name not in {'ROOT','PRIOR','LEGACY','BUILDER','PROSPECTIVE'}:continue
    if not(isinstance(value,ast.Call)and isinstance(value.func,ast.Name)and value.func.id=='Path'and len(value.args)==1 and isinstance(value.args[0],ast.Constant)and isinstance(value.args[0].value,str)):continue
    literal=value.args[0].value
    if name=='ROOT':replacement=str(self.root/'canonical-root')
    elif literal in literal_map:replacement=str(literal_map[literal])
    else:raise ValueError('UNDECLARED_LITERAL_DATA_PATH:'+literal)
    declared[name]="Path("+repr(replacement)+")"
   self.remaps[digest]=declared
  (self.root/'canonical-root').mkdir()
  self.real_compile=builtins.compile;self.real_exec=builtins.exec
  self.fixture_builtins=dict(vars(builtins));self.fixture_builtins.update(compile=self.compile,exec=self.execute)
 @staticmethod
 def path_literal(raw,name):
  selected=[n.value for n in ast.parse(raw).body if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id==name]
  if len(selected)!=1:raise ValueError('CLOSED_PUBLIC_PATH_DATA_NAME')
  value=selected[0]
  if not(isinstance(value,ast.Call)and isinstance(value.func,ast.Name)and value.func.id=='Path'and len(value.args)==1 and not value.keywords and isinstance(value.args[0],ast.Constant)and type(value.args[0].value)is str):raise ValueError('CLOSED_PUBLIC_LITERAL_PATH_DATA')
  return value.args[0].value
 def capture(self,name,raw):
  path=self.root/'exact-public-sources'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
  self.register_source(path,raw);return path
 def register_source(self,path,raw,original_raw=None,declared_data_suffix=None):
  path=Path(path).resolve(strict=True)
  if not(path.is_relative_to(self.root)or path.is_relative_to(REPO)):
   raise ValueError('REGISTERED_SOURCE_OUTSIDE_FIXED_TEST_OR_PUBLIC_ROOT')
  if path.read_bytes()!=raw:raise ValueError('REGISTERED_SOURCE_BYTES_DRIFT')
  original=raw if original_raw is None else original_raw
  before=ast.parse(original);after=ast.parse(raw)
  names=[]
  if original!=raw:
   if not raw.startswith(original):raise ValueError('ORIGINAL_PUBLIC_PREFIX_CHANGED')
   if ast.dump(ast.Module(body=after.body[:len(before.body)],type_ignores=[]),include_attributes=False)!=ast.dump(before,include_attributes=False):
    raise ValueError('ORIGINAL_SOURCE_AST_CHANGED')
   declared={}if declared_data_suffix is None else declared_data_suffix
   for node in after.body[len(before.body):]:
    if not(isinstance(node,ast.Assign)and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)):
     raise ValueError('NON_DATA_APPENDED_FIXTURE_NODE')
    name=node.targets[0].id
    if name not in declared or ast.literal_eval(node.value)!=declared[name]:raise ValueError('UNDECLARED_APPENDED_TRUST_DATA')
    names.append(name)
   if set(names)!=set(declared):raise ValueError('CLOSED_APPENDED_TRUST_DATA_SET')
  digest=sha(raw);self.known.setdefault(digest,(path,raw));self.source_paths.setdefault(digest,set()).add(str(path))
  self.source_baselines.setdefault(digest,{'original_sha256':sha(original),'original_function_class_asts':function_asts(original),'appended_literal_data_names':names})
  self.remaps.setdefault(digest,{})
  return digest
 def transform(self,raw,filename):
  digest=sha(raw)
  if digest not in self.known:raise ValueError('UNDECLARED_SOURCE_HASH:'+digest)
  expected_path,expected_raw=self.known[digest]
  if str(Path(filename).resolve())not in self.source_paths[digest] or raw!=expected_raw:raise ValueError('SOURCE_PATH_OR_BYTES_DRIFT')
  expected_path=Path(filename).resolve()
  tree=ast.parse(raw);original=copy.deepcopy(tree);changed=[]
  for n in tree.body:
   if isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in self.remaps[digest]:
    name=n.targets[0].id;assert name in ({'ROOT','PRIOR','LEGACY','BUILDER','PROSPECTIVE'}|self.explicit_extra_allowlist.get(digest,frozenset()))
    value=ast.parse(self.remaps[digest][name],mode='eval').body
    if not self.data_expression(value):raise ValueError('CLOSED_LITERAL_DATA_EXPRESSION_REQUIRED')
    n.value=value;changed.append(name)
  assert set(changed)==set(self.remaps[digest])
  def nondata(t):return ast.dump(ast.Module(body=[n for n in t.body if not(isinstance(n,ast.Assign)and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id in self.remaps[digest])],type_ignores=[]),include_attributes=False)
  assert nondata(original)==nondata(tree),'NON_DATA_CONTROL_FLOW_CHANGED'
  before=function_asts(raw);after={n.name:sha(ast.dump(n,include_attributes=False).encode())for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
  assert before==after,'VALIDATOR_OR_CLASS_BODY_CHANGED'
  self.receipts.append({'source_path':str(expected_path),'original_sha256':self.source_baselines[digest]['original_sha256'],'executed_raw_sha256':digest,'registered_exact_paths':sorted(self.source_paths[digest]),'appended_literal_data_names':self.source_baselines[digest]['appended_literal_data_names'],'declared_data_globals':self.remaps[digest],'function_class_ast_hashes':before,'all_function_class_asts_equal':True,'all_non_data_control_flow_equal':True})
  return ast.fix_missing_locations(tree)
 def data_expression(self,node):
  if isinstance(node,ast.Constant):return type(node.value)in(str,bytes,bool,int,float,type(None))
  if isinstance(node,(ast.Tuple,ast.List,ast.Set)):return all(self.data_expression(n)for n in node.elts)
  if isinstance(node,ast.Dict):return all(k is not None and self.data_expression(k)and self.data_expression(v)for k,v in zip(node.keys,node.values))
  if isinstance(node,ast.UnaryOp)and isinstance(node.op,ast.USub):return isinstance(node.operand,ast.Constant)and type(node.operand.value)in(int,float)
  return (isinstance(node,ast.Call)and isinstance(node.func,ast.Name)and node.func.id=='Path'and not node.keywords and len(node.args)==1 and isinstance(node.args[0],ast.Constant)and type(node.args[0].value)is str)
 def compile(self,source,filename,mode,flags=0,dont_inherit=False,optimize=-1,**kwargs):
  raw=source.encode()if isinstance(source,str)else source
  if isinstance(raw,bytes):source=self.transform(raw,filename)
  else:raise ValueError('TEST_LOADER_REQUIRES_CAPTURED_RAW_SOURCE')
  return self.real_compile(source,filename,mode,flags=flags,dont_inherit=dont_inherit,optimize=optimize,**kwargs)
 def execute(self,code,globals=None,locals=None,**kwargs):
  if globals is None:raise ValueError('EXPLICIT_SOURCE_MODULE_GLOBALS_REQUIRED')
  globals.setdefault('__builtins__',self.fixture_builtins)
  result=self.real_exec(code,globals,globals if locals is None else locals,**kwargs)
  filename=str(Path(code.co_filename).resolve())
  for digest,paths in self.source_paths.items():
   if filename in paths and digest in self.post_load_data:
    data=self.post_load_data[digest]
    if set(data)!={'_FROZEN_HASHES','builtins'}:raise ValueError('CLOSED_ACCESS_PLATFORM_DATA_KEYS')
    if Path(filename).name!='nightly_manuscript_access.py':raise ValueError('FIXED_ACCESS_PLATFORM_DATA_SOURCE')
    globals.update(data)
  return result
 def load(self,path):
  raw=Path(path).read_bytes();module=types.ModuleType('_private_exact_legacy_fixture');module.__file__=str(path)
  self.execute(self.compile(raw,str(path),'exec'),module.__dict__);return module
 def audit(self,event,args):
  if event.startswith('socket.'):
   raise ValueError('HOLD_TEST_FIXTURE_NETWORK_FORBIDDEN')
  if event=='exec' and args and Path(getattr(args[0],'co_filename','')).is_relative_to(self.forbidden_cowork_root):
   raise ValueError('HOLD_REAL_CORE_EXECUTION_FORBIDDEN')
  if event in {'open','os.listdir','os.scandir','os.mkdir','os.remove','os.rename'} and args and isinstance(args[0],(str,bytes,os.PathLike)):
   path=os.fsdecode(args[0])
   if Path(path).is_relative_to(self.forbidden_cowork_root)or any(Path(path).is_relative_to(parent)for parent in self.forbidden_legacy_roots):
    self.blocked.append({'event':event,'path':path});raise ValueError('HOLD_FORBIDDEN_REAL_CORE_OR_LEGACY_PATH_BEFORE_OPEN')

def main():
 loader=ClosedDataLoader(sys.argv[1]);sys.addaudithook(loader.audit)
 module=loader.load(loader.legacy)
 assert module.ROOT==loader.root/'canonical-root'
 assert callable(module.current_closure)and callable(module.read_bound_closure)
 negatives=[]
 raw=Path(loader.legacy).read_bytes()
 try:loader.compile(raw+b'\n# source drift\n',str(loader.legacy),'exec')
 except ValueError as error:negatives.append({'probe':'source_hash_drift','result':'HOLD','reason':str(error)})
 else:raise AssertionError('source drift accepted')
 digest=sha(raw);saved=loader.remaps[digest];loader.remaps[digest]={}
 try:
  try:loader.load(loader.legacy)
  except ValueError as error:negatives.append({'probe':'unmapped_core_path','result':'HOLD_BEFORE_READ','reason':str(error)})
  else:raise AssertionError('unmapped Core path accepted')
 finally:loader.remaps[digest]=saved
 report={'standard':'VRS-PRIVATE-W42-CLOSED-DATA-LEGACY-IMPORT-POC-1','fixture_only':True,'no_source_verdict':True,'status':'UNCHANGED_LEGACY_IMPORT_AND_NESTED_HELPERS_SAFE_WITH_CLOSED_DATA_ONLY_REMAPS','captured_source_count':len(loader.known),'executed_source_count':len(loader.receipts),'original_legacy_sha256':sha(raw),'legacy_root':str(module.ROOT),'receipts':loader.receipts,'negative_probes':negatives,'blocked_path_attempts':loader.blocked,'actual_core_bytes_read':0,'actual_core_code_executed':0,'module_aliases':0,'mocked_validate_or_current_closure':False,'contextvar_mints':0,'full_current_closure_or_source_session_claim':False}
 out=Path(sys.argv[2]);out.write_bytes(encoded(report));print(json.dumps({'report':str(out),'sha256':sha(out.read_bytes()),'executed_source_count':len(loader.receipts),'negative_count':len(negatives)}))
if __name__=='__main__':main()
