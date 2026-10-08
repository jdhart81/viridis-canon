from pathlib import Path
import contextlib,hashlib,importlib.machinery,json,sys,unittest
from unittest.mock import patch

def run(snapshot,gates):
 snapshot=Path(snapshot).resolve();gates=Path(gates).resolve();manifest=json.loads((snapshot/'PORTABLE_FIXTURE_MANIFEST.json').read_bytes());h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 for r in manifest['fixture_files']:
  p=snapshot/r['filename'];assert p.is_file()and not p.is_symlink()and h(p)==r['sha256']
 assert h(snapshot/'FREEZE.json')==manifest['source_freeze_sha256']
 for r in json.loads((snapshot/'FREEZE.json').read_bytes())['files']:assert h(snapshot/r['filename'])==r['sha256']
 routes={}
 for r in manifest['manual_routes']:
  p=(snapshot/r['git_path'])if r['git_path']in {'runtime_successor.py','generic_prospective_catalog.py'}else(gates/r['git_path']);assert h(p)==r['sha256'];routes[r['original']]=p
 orig_read=Path.read_bytes;orig_stat=Path.stat;orig_file=Path.is_file;orig_exec=importlib.machinery.SourceFileLoader.exec_module
 def target(p):return routes.get(str(p),p)
 def read(p):return orig_read(target(p))
 def stat(p,*a,**k):return orig_stat(target(p),*a,**k)
 def is_file(p):return orig_file(target(p))
 def load(loader,module):
  orig_exec(loader,module)
  if module.__name__=='generic_runtime_candidate':
   for v in [module,module.e,module.e.e,module.u,module.v]:v.ROOT=snapshot/'fixture_root'
 # Routes apply only to exact immutable historical code leaves and are
 # verified before use. No source bytes/predicates/hash pins are rewritten.
 # The production ROOT is replaced only inside unit fixtures, never a live
 # invocation. Every compiled actual source profile and strict field test runs.
 with patch.object(Path,'read_bytes',read),patch.object(Path,'stat',stat),patch.object(Path,'is_file',is_file),patch.object(importlib.machinery.SourceFileLoader,'exec_module',load):
  sys.path.insert(0,str(snapshot));suite=unittest.defaultTestLoader.discover(str(snapshot),pattern='test_generic_*.py');result=unittest.TextTestRunner(verbosity=2).run(suite);assert result.testsRun==75;return result.wasSuccessful()
if __name__=='__main__':sys.exit(0 if run(sys.argv[1],sys.argv[2])else 1)
