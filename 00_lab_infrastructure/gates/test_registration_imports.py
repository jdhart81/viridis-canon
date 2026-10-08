import ast,hashlib,importlib.util,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
D=Path(__file__).resolve().parent
PUBLIC_SOURCES={'file_byte_metadata':'production_snapshots/phase5-20261005-provenance-closure/after/production_execution_dependencies/file_byte_metadata.py'}
def public_source(name):return D/PUBLIC_SOURCES.get(name,name+'.py')
spec=importlib.util.spec_from_file_location('registration_imports',D/'registration_imports.py');subject=importlib.util.module_from_spec(spec);spec.loader.exec_module(subject)
class ImportTests(unittest.TestCase):
 def setUp(self):
  self.fixture=tempfile.TemporaryDirectory(prefix='registration-import-fixture-');self.root=Path(self.fixture.name).resolve();self.saved={name:sys.modules.get(name)for name,_,_ in subject.SOURCES}
  for name,relative,h in subject.SOURCES:
   p=self.root/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((public_source(name)).read_bytes());sys.modules.pop(name,None)
 def tearDown(self):
  for name,old in self.saved.items():
   if old is None:sys.modules.pop(name,None)
   else:sys.modules[name]=old
  self.fixture.cleanup()
 def test_four_actual_private_helpers_load_exact_bytes(self):
  before=list(sys.path);meta=list(sys.meta_path)
  with subject.source_session(self.root):
   import server_managed_fields,publication_preservation,file_byte_metadata,zenodo_transport
   for name,relative,h in subject.SOURCES:self.assertEqual(sys.modules[name].__file__,str(self.root/relative));self.assertEqual(hashlib.sha256(Path(sys.modules[name].__file__).read_bytes()).hexdigest(),h)
  self.assertEqual(sys.path,before);self.assertEqual(sys.meta_path,meta)
 def test_nested_scope_retains_module_objects(self):
  with subject.source_session(self.root):
   import server_managed_fields
   existing=server_managed_fields
   with subject.source_session(self.root):self.assertIs(sys.modules['server_managed_fields'],existing)
   self.assertIs(sys.modules['server_managed_fields'],existing)
 def test_foreign_cached_helper_blocked_before_body(self):
  fake=types.ModuleType('server_managed_fields');fake.__file__=str(self.root/'foreign.py');sys.modules['server_managed_fields']=fake
  with self.assertRaisesRegex(subject.NamespaceHold,'foreign cached'):
   with subject.source_session(self.root):self.fail('body reached')
 def test_cached_missing_origin_blocked(self):
  sys.modules['server_managed_fields']=types.ModuleType('server_managed_fields')
  with self.assertRaises(subject.NamespaceHold):
   with subject.source_session(self.root):self.fail('body reached')
 def test_missing_source_blocked(self):
  (self.root/subject.SOURCES[0][1]).unlink()
  with self.assertRaises(OSError):
   with subject.source_session(self.root):self.fail('body reached')
 def test_one_byte_divergence_blocked(self):
  p=self.root/subject.SOURCES[0][1];p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(subject.NamespaceHold,'hash differs'):
   with subject.source_session(self.root):self.fail('body reached')
 def test_symlinked_source_blocked(self):
  p=self.root/subject.SOURCES[0][1];target=self.root/'copied.py';target.write_bytes(p.read_bytes());p.unlink();p.symlink_to(target)
  with self.assertRaisesRegex(subject.NamespaceHold,'regular contained'):
   with subject.source_session(self.root):self.fail('body reached')
 def test_symlinked_parent_blocked(self):
  p=self.root/subject.SOURCES[0][1];parent=p.parent;renamed=parent.with_name('parent-real');parent.rename(renamed);parent.symlink_to(renamed)
  with self.assertRaisesRegex(subject.NamespaceHold,'regular contained'):
   with subject.source_session(self.root):self.fail('body reached')
 def test_mid_scope_source_drift_blocked_at_exit(self):
  with self.assertRaisesRegex(subject.NamespaceHold,'hash differs'):
   with subject.source_session(self.root):
    p=self.root/subject.SOURCES[0][1];p.write_bytes(p.read_bytes()+b' ')
 def test_foreign_replacement_blocked_at_exit(self):
  with self.assertRaisesRegex(subject.NamespaceHold,'foreign cached'):
   with subject.source_session(self.root):
    fake=types.ModuleType('server_managed_fields');fake.__file__=str(self.root/'foreign.py');sys.modules['server_managed_fields']=fake
 def test_existing_module_identity_change_blocked(self):
  with subject.source_session(self.root):__import__('server_managed_fields')
  with self.assertRaisesRegex(subject.NamespaceHold,'module identity'):
   with subject.source_session(self.root):
    replacement=types.ModuleType('server_managed_fields');replacement.__file__=str(self.root/subject.SOURCES[0][1]);sys.modules['server_managed_fields']=replacement
 def test_unrelated_module_not_intercepted(self):
  self.assertIsNone(subject._Finder(self.root).find_spec('irrelevant_module'))
 def test_exception_does_not_leak_finder(self):
  before=list(sys.meta_path)
  with self.assertRaisesRegex(RuntimeError,'delegate failed'):
   with subject.source_session(self.root):raise RuntimeError('delegate failed')
  self.assertEqual(sys.meta_path,before)
 def test_search_path_change_blocked(self):
  before=list(sys.path)
  try:
   with self.assertRaisesRegex(subject.NamespaceHold,'search paths'):
    with subject.source_session(self.root):sys.path.append(str(self.root/'foreign'))
  finally:sys.path[:]=before
 def test_read_race_blocked(self):
  real=Path.stat;target=self.root/subject.SOURCES[0][1];calls=0
  def fake(path,*a,**kw):
   nonlocal calls
   result=real(path,*a,**kw)
   if path==target:
    calls+=1
    if calls>=3:
     result=types.SimpleNamespace(st_ino=result.st_ino,st_size=result.st_size,st_mtime_ns=result.st_mtime_ns+calls,st_mode=result.st_mode)
   return result
  with patch.object(Path,'stat',fake):
   with self.assertRaisesRegex(subject.NamespaceHold,'hash differs'):
    with subject.source_session(self.root):self.fail('body reached')
 def test_original_acceptance_rejects_title_change(self):
  with subject.source_session(self.root):
   from publication_preservation import require_public_metadata
   from zenodo_transport import TransportHold
   same={'title':'Bound title','description':'claims'};require_public_metadata(same,same)
   with self.assertRaises(TransportHold):require_public_metadata({**same,'title':'changed'},same)
 def test_original_acceptance_rejects_claim_description_change(self):
  with subject.source_session(self.root):
   from publication_preservation import require_public_metadata
   from zenodo_transport import TransportHold
   same={'title':'Bound title','description':'Exact claim'}
   with self.assertRaises(TransportHold):require_public_metadata({**same,'description':'Other claim'},same)
class PublicSourceTests(unittest.TestCase):
 def test_all_four_helper_inputs_are_unchanged_public_sources(self):
  self.assertEqual(len(subject.SOURCES),4)
  for name,relative,h in subject.SOURCES:
   self.assertEqual(hashlib.sha256((public_source(name)).read_bytes()).hexdigest(),h)
   self.assertFalse(Path(relative).is_absolute())
if __name__=='__main__':unittest.main()
