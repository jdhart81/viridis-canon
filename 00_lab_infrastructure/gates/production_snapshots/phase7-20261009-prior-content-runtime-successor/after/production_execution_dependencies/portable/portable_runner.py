"""Fixture-only source routing; never runtime or publication evidence."""
from pathlib import Path
import hashlib,importlib.machinery,json,sys,unittest
from unittest.mock import patch

def run(snapshot):
 snapshot=Path(snapshot).resolve(strict=True);manifest=json.loads((snapshot/'PORTABLE_FIXTURE_MANIFEST.json').read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for row in manifest['files']:
  p=snapshot/row['filename'];assert p.is_file()and not p.is_symlink()and h(p)==row['sha256']and p.stat().st_size==row['bytes']
 routes={original:snapshot/row['filename']for original,row in manifest['manual_routes'].items()}
 for original,row in manifest['manual_routes'].items():assert h(routes[original])==row['sha256']

 # Directory symlink/race guards are routed to real regular fixture parents.
 # A production file body is never supplied from this directory-only map.
 for original in list(routes):
  for parent in Path(original).parents:
   if str(parent).startswith('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')and str(parent)not in routes:
    q=snapshot/'fixture_root'/'_ROUTED_REGULAR_PARENTS'/hashlib.sha256(str(parent).encode()).hexdigest();q.mkdir(parents=True,exist_ok=True);routes[str(parent)]=q
 original_read=Path.read_bytes;original_stat=Path.stat;original_file=Path.is_file;original_load=importlib.machinery.SourceFileLoader.exec_module
 forbidden='/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/'
 def target(path):
  result=routes.get(str(path),path)
  if str(result).startswith(forbidden):raise AssertionError('fixture attempted production-root read: '+str(result))
  return result
 def read(path):return original_read(target(path))
 def stat(path,*args,**kwargs):return original_stat(target(path),*args,**kwargs)
 def is_file(path):return original_file(target(path))
 def load(loader,module):
  original_load(loader,module)
  if module.__name__=='prior_content_runtime_test':
   queue=[module];seen=set()
   while queue:
    item=queue.pop()
    if id(item)in seen:continue
    seen.add(id(item))
    if hasattr(item,'ROOT'):item.ROOT=snapshot/'fixture_root'
    for key in ('e','u','v'):
     child=getattr(item,key,None)
     if child is not None:queue.append(child)
 with patch.object(Path,'read_bytes',read),patch.object(Path,'stat',stat),patch.object(Path,'is_file',is_file),patch.object(importlib.machinery.SourceFileLoader,'exec_module',load):
  sys.path.insert(0,str(snapshot))
  suite=unittest.defaultTestLoader.discover(str(snapshot),pattern='test_*.py');result=unittest.TextTestRunner(verbosity=2).run(suite)
  assert result.testsRun==manifest['test_methods_expected'];return result.wasSuccessful()
if __name__=='__main__':raise SystemExit(0 if run(sys.argv[1])else 1)
