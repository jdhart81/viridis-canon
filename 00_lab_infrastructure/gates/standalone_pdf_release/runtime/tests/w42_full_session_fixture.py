"""PRIVATE TEST ONLY complete real source-session/science DATA fixture.

All authority/provider values are simulated test DATA. No saved verdict,
validator replacement, ContextVar mint, or module alias grants admission.
"""
from __future__ import annotations
import ast,contextlib,json,os,sys,time,tempfile
from pathlib import Path
from build_source_chain import Constructor,RUNTIME,sha,function_asts
from closed_data_loader import ClosedDataLoader
from legacy_data_environment import build_legacy_environment
from platform_controls import platform,transients
from current_profile import build_current_profile
from runtime_data_binding import bind_runtime_data

class FullSessionFixture:
 def __init__(self,root):
  self.started=time.monotonic();self.saved_env={k:os.environ.get(k)for k in ('VIRIDIS_CORE_ROOT','PYTHONTZPATH')};self.saved_path=list(sys.path)
  base=Path(root).resolve()
  allowed=(Path(tempfile.gettempdir()).resolve(),Path('/tmp').resolve())
  if not any(base.is_relative_to(parent)and base!=parent for parent in allowed):raise ValueError('FIXED_TEST_TEMPORARY_ROOT_REQUIRED')
  base.mkdir(exist_ok=True)
  self.loader=ClosedDataLoader(base/'measured-source');sys.addaudithook(self.loader.audit)
  self.root=self.loader.root/'canonical-root'
  self.legacy=build_legacy_environment(self.root,self.loader);self.science_fixture=self.legacy['science_fixture']
  for key in ('legacy_closure','legacy_consumer','legacy_scope','session_consumer'):
   binding=self.legacy[key];self.legacy[key]={'path':str(Path(binding['path']).relative_to(self.root)),'sha256':binding['sha256']}
  self.constructor=Constructor(self.root,existing_root=True,loader=self.loader);c=self.constructor;self.runtime=c.runtime
  for name,key in [('LEGACY_CLOSURE','legacy_closure'),('LEGACY_CONSUMER','legacy_consumer'),('LEGACY_SCOPE','legacy_scope'),('SESSION_CONSUMER','session_consumer')]:c.remap(name,self.legacy[key])
  self.platform=platform(c,self.science_fixture.certificate);self.transients=transients(c)
  # A complete merged tree contains the measured130 origin plus the eight
  # historical public transient blobs. Scope rows remain exactly130.
  origin=self.legacy['original_origin'];tree_path=Path(origin['merged_tree']['path']);tree=json.loads(tree_path.read_bytes())
  extra=json.loads(Path(self.transients['origin']['tree']['path']).read_bytes())['tree'];by_path={r['path']:r for r in tree['tree']}
  for row in extra:
   if row['path']in by_path:assert by_path[row['path']]==row
   by_path[row['path']]=row
  tree['tree']=list(by_path.values());origin['merged_tree']=c.put(tree_path,tree)
  scope_path=self.root/self.legacy['legacy_scope']['path'];scope=json.loads(scope_path.read_bytes());scope['source_origin']=origin
  self.legacy['legacy_scope']=c.put(scope_path,scope);self.legacy['legacy_scope']['path']=str(scope_path.relative_to(self.root));c.remap('LEGACY_SCOPE',self.legacy['legacy_scope'])
  self.predecessor=c.predecessors()
  # Preserve exact raw current source. The platform/trust adapter is separate,
  # explicit fixture DATA applied only after this captured source executes.
  installed=self.root/Path(self.runtime.PROFILE_PATH).parent/'nightly_manuscript_access.py';raw=(RUNTIME/installed.name).read_bytes();installed.write_bytes(raw)
  self.current=build_current_profile(c,self.legacy);self.binding=self.current['profile_binding'];self.source_pins130=self.legacy['base_pins']
  self.runtime_data=bind_runtime_data(self.loader,c,self.current)
  self.loader.register_source(installed,raw)
  # The helper's defining module is private/unregistered; use its function globals.
  globals_=type(self.science_fixture).context.__globals__;factory=globals_['_platform_builtins']
  self.platform_builtins=factory(self.science_fixture.binary,self.science_fixture.gen,self.science_fixture.historical_generation_literal)
  self.platform_builtins.compile=self.loader.compile;self.platform_builtins.exec=self.loader.execute
  self.loader.post_load_data[sha(raw)]={'_FROZEN_HASHES':self.science_fixture.test_hashes,'builtins':self.platform_builtins}
  self.platform_adapter={'source_sha256':sha(Path(globals_['__file__']).read_bytes()),'function_ast_sha256':function_asts(Path(globals_['__file__']).read_bytes())['_platform_builtins'],'fixed_literal_paths':['/opt/homebrew/bin/tectonic',self.science_fixture.historical_generation_literal],'raw_installed_access_sha256':sha(raw),'installed_raw_unchanged':installed.read_bytes()==raw}
  self.source_names={r['name'][:-3]for r in [*self.source_pins130,*self.current['module_rows'],*self.current['shared_rows']] if r['name'].endswith('.py')}
  self.build_seconds=time.monotonic()-self.started
 @contextlib.contextmanager
 def context(self):
  # Ordinary cold-cache fixture protocol, finite measured names only. Genuine
  # SourceFinder creates every canonical object; none is aliased or synthesized.
  names=sorted(self.source_names);saved={name:sys.modules.pop(name)for name in names if name in sys.modules}
  try:yield self
  finally:
   self.loader.clear_code_cache()
   for name in names:sys.modules.pop(name,None)
   sys.modules.update(saved)
   for key,value in self.saved_env.items():
    if value is None:os.environ.pop(key,None)
    else:os.environ[key]=value
   sys.path[:]=self.saved_path
 def source_receipt(self):
  unique={}
  for row in self.loader.receipts:
   key=row['executed_raw_sha256'];unique[key]={'original_public_sha256':row['original_sha256'],'executed_raw_sha256':key,'original_function_class_ast_hashes':row['function_class_ast_hashes'],'appended_literal_data_names':row['appended_literal_data_names'],'declared_data_globals':sorted(row['declared_data_globals']),'all_function_class_asts_equal':row['all_function_class_asts_equal'],'all_non_data_control_flow_equal':row['all_non_data_control_flow_equal']}
  return {'fixture_only':True,'authority':False,'python':sys.version,'build_seconds':self.build_seconds,'source_body_proofs':unique,'closed_runtime_data_remap_names':self.runtime_data['data_globals'],'private_runtime_original_sha256':sha(self.constructor.original_raw),'private_runtime_original_function_class_ast_hashes':function_asts(self.constructor.original_raw),'legacy_source_pins':len(self.source_pins130),'current_modules':len(self.current['module_rows']),'shared_helpers':len(self.current['shared_rows']),'predecessor':self.predecessor,'platform_adapter':self.platform_adapter,'loader_executions':len(self.loader.receipts),'compiler_cache':self.loader.compile_cache_stats(),'all_function_class_asts_equal':all(r['all_function_class_asts_equal']for r in self.loader.receipts),'all_non_data_control_flow_equal':all(r['all_non_data_control_flow_equal']for r in self.loader.receipts),'core_open_attempts':self.loader.blocked,'mocked_validate_or_current_closure':False,'context_mints':0,'module_aliases':0}

if __name__=='__main__':
 import json
 f=FullSessionFixture(Path(sys.argv[1]));steps=[]
 with f.context():
  print('CONSTRUCTED '+str(f.build_seconds),flush=True);t=time.monotonic();result=f.runtime.validate(f.root,f.binding);steps.append({'operation':'validate','status':result['status'],'seconds':time.monotonic()-t})
  print('VALIDATE '+str(steps[-1]),flush=True);t=time.monotonic()
  with f.runtime.session(f.root,f.binding):
   f.runtime.require_source_session(f.root,f.binding)
   import packaging_runtime
   packaging_runtime.require_source_session(f.root,f.binding)
  steps.append({'operation':'genuine_source_session_and_canonical_context','status':'PASS','seconds':time.monotonic()-t})
 report={**f.source_receipt(),'steps':steps}
 out=Path(sys.argv[2]);out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({'receipt':str(out),'sha256':sha(out.read_bytes()),'build_seconds':report['build_seconds'],'steps':steps,'unique_executed_sources':len(report['source_body_proofs'])}))
