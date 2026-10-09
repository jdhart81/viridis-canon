from pathlib import Path
import hashlib,importlib.machinery,json,sys,unittest
from unittest.mock import patch

def run(snapshot,gates):
 snapshot=Path(snapshot).resolve();gates=Path(gates).resolve();manifest=json.loads((snapshot/'PORTABLE_FIXTURE_MANIFEST.json').read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for row in manifest['fixture_files']:
  p=snapshot/row['filename'];assert p.is_file()and not p.is_symlink()and h(p)==row['sha256']
 routes={}
 for row in manifest['manual_routes']:
  p=(snapshot if row['scope']=='snapshot'else gates)/row['git_path'];assert h(p)==row['sha256'];routes[row['original']]=p
 orig_read=Path.read_bytes;orig_stat=Path.stat;orig_file=Path.is_file;orig_exec=importlib.machinery.SourceFileLoader.exec_module
 production='/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/'
 def target(p):
  actual=routes.get(str(p),p)
  if str(actual).startswith(production):raise AssertionError('portable fixture attempted production-root read')
  return actual
 def read(p):return orig_read(target(p))
 def stat(p,*args,**kwargs):return orig_stat(target(p),*args,**kwargs)
 def is_file(p):return orig_file(target(p))
 def load(loader,module):
  orig_exec(loader,module)
  if module.__name__=='own_runtime_scaffold':
   queue=[module];seen=set()
   while queue:
    current=queue.pop()
    if id(current)in seen:continue
    seen.add(id(current))
    if hasattr(current,'ROOT'):current.ROOT=snapshot/'fixture_root'
    for name in ['e','u','v']:
     child=getattr(current,name,None)
     if child is not None:queue.append(child)
 # Fixture-only exact manual source routing and ROOT projection. Original
 # source bytes, functions, guards, pins and acceptance predicates are unchanged.
 paths=[snapshot,snapshot/'fixture_root/RESEARCH_PIPELINE_v2/verification_coverage_gates',snapshot/'fixture_root/RESEARCH_PIPELINE_v2',snapshot/'fixture_root/_ZENODO_DEPOSITS']
 with patch.object(Path,'read_bytes',read),patch.object(Path,'stat',stat),patch.object(Path,'is_file',is_file),patch.object(importlib.machinery.SourceFileLoader,'exec_module',load):
  sys.path[:0]=[str(p)for p in paths]
  suite=unittest.defaultTestLoader.discover(str(snapshot),pattern='test_*.py');result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.testsRun==manifest['test_methods_expected'];return result.wasSuccessful()
if __name__=='__main__':sys.exit(0 if run(sys.argv[1],sys.argv[2])else 1)
