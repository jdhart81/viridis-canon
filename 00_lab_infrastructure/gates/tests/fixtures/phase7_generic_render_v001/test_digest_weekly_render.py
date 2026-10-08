"""Portable type-setting tests; fixture scopes never claim admission."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest,subprocess
from unittest.mock import patch
from types import SimpleNamespace
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
sys.path[:0]=[str(HERE)]
import digest_weekly_render as r
class RenderTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix='genericrender-fixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.cache=self.root/'cache';self.cache.mkdir();self.binary=self.root/'tectonic';self.binary.write_bytes(b'fixture renderer bytes');self.manifest=self.root/'cache-manifest.json'
  for n in range(556):(self.cache/f'file-{n:03}.raw').write_bytes(f'fixture-{n}'.encode())
  self.save_cache();self.note={'run_id':'Run-189','foundation_basis':'INDEPENDENT','section':'MAIN_NOTES','claim_table':[{'lean_theorem':'fixture_theorem','semantic_tier':'DEPTH_NOT_ASSESSED','nonvacuity_label':'certified; nonvacuity not demonstrated','headline_eligible':False}]};self.consumed={'notes':[self.note],'fixture':'not admission'}
  self.paper=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/digests/fixture/paper.tex';self.paper.parent.mkdir(parents=True);self.paper.write_bytes(r.d.wrapper_tex('2026-W41',[self.note]));self.mocks=[patch.object(r,'ROOT',self.root),patch.object(r,'MANIFEST',self.manifest),patch.object(r,'MANIFEST_SHA',r.sha(self.manifest.read_bytes())),patch.object(r,'EXECUTABLE',self.binary),patch.object(r,'BINARY_SHA',r.sha(self.binary.read_bytes())),patch.object(r.d,'consume_notes',return_value=self.consumed)]
  for mock in self.mocks:mock.start();self.addCleanup(mock.stop)
 def save_cache(self):self.manifest.write_bytes(r.d.raw_json({'cache_root':str(self.cache),'files':{p.name:r.sha(p.read_bytes())for p in self.cache.iterdir()}}))
 def callback(self):return r.render_for_package(self.root,'2026-W41',[{'run_id':'Run-189','path':'fixture-only'}],{})
 def execute(self,command,**kwargs):
  (self.paper.parent/'render-observation/render_driver.pdf').write_bytes(b'%PDF-1.4\nfixture\n%%EOF\n');return SimpleNamespace(returncode=0,stdout=b'fixture rendering log',stderr=b'')
 def test_exact_current_wrapper_and_closed_cache_returns_pdf_only(self):
  callback=self.callback()
  with patch.object(r.subprocess,'run',side_effect=self.execute)as proc:self.assertTrue(callback(self.paper).startswith(b'%PDF-'));self.assertIn('--only-cached',proc.call_args.args[0]);self.assertEqual(proc.call_args.kwargs['timeout'],180)
  observed=json.loads((self.paper.parent/'render-observation/RENDERER_OBSERVATION.json').read_bytes());self.assertFalse(observed['certifies']);self.assertEqual(observed['run_ids'],['Run-189']);self.assertEqual(observed['cache_file_count'],556);self.assertEqual(observed['ssot_writes'],0)
 def test_default_scope_consumer_used_without_alternate_consumer(self):
  with patch.object(r.d,'consume_notes',return_value=self.consumed)as consumer:self.callback();self.assertEqual(consumer.call_args.args[0],self.root);self.assertFalse(consumer.call_args.kwargs)
 def test_arbitrary_note_counts_recompute_same_unchanged_renderer(self):
  self.consumed['notes']=[self.note,{**self.note,'run_id':'Run-191'}];self.paper.write_bytes(r.d.wrapper_tex('2026-W41',self.consumed['notes']));callback=self.callback()
  with patch.object(r.subprocess,'run',side_effect=self.execute):self.assertTrue(callback(self.paper).startswith(b'%PDF-'))
 def test_changed_current_default_scope_holds_before_render(self):
  callback=self.callback()
  with patch.object(r.d,'consume_notes',return_value={'changed':'scope'}),patch.object(r.subprocess,'run')as proc:self.assertRaises(ValueError,callback,self.paper);proc.assert_not_called()
 def test_wrapper_recompute_mismatch_holds_before_render(self):
  callback=self.callback()
  with patch.object(r.d,'wrapper_tex',return_value=b'changed recompute'),patch.object(r.subprocess,'run')as proc:self.assertRaises(ValueError,callback,self.paper);proc.assert_not_called()
 def test_changed_source_byte_holds_before_render(self):
  callback=self.callback();self.paper.write_bytes(self.paper.read_bytes()+b'!')
  with patch.object(r.subprocess,'run')as proc:self.assertRaises(ValueError,callback,self.paper);proc.assert_not_called()
 def test_foreign_root_wrong_week_or_output_path_hold(self):
  self.assertRaises(ValueError,r.render_for_package,self.root/'cache','2026-W41',[],{});self.assertRaises(ValueError,r.render_for_package,self.root,'not-a-week',[],{})
  callback=self.callback();wrong=self.root/'paper.tex';wrong.write_bytes(self.paper.read_bytes());self.assertRaises(ValueError,callback,wrong)
 def test_wrong_basename_holds(self):
  callback=self.callback();wrong=self.paper.with_name('other.tex');wrong.write_bytes(self.paper.read_bytes());self.assertRaises(ValueError,callback,wrong)
 def test_exact_prologue_required(self):
  with patch.object(r,'PROLOGUE',b'changed marker'):self.assertRaises(ValueError,self.callback)
 def test_wrong_cache_manifest_holds(self):
  self.manifest.write_bytes(b'{}');self.assertRaises(ValueError,self.callback)
 def test_missing_changed_extra_cache_resource_holds(self):
  for kind in('missing','changed','extra'):
   p=self.cache/'file-000.raw';original=p.read_bytes()
   if kind=='missing':p.unlink()
   elif kind=='changed':p.write_bytes(b'wrong')
   else:(self.cache/'extra.raw').write_bytes(b'wrong')
   self.assertRaises(ValueError,self.callback)
   if kind=='extra':(self.cache/'extra.raw').unlink()
   else:p.write_bytes(original)
 def test_cache_symlink_holds(self):
  (self.cache/'bad-link').symlink_to(self.binary);self.assertRaises(ValueError,self.callback)
 def test_source_symlink_holds(self):
  callback=self.callback();link=self.paper.with_name('link');link.symlink_to(self.paper);self.assertRaises(ValueError,callback,link)
 def test_binary_changed_before_render_holds(self):
  callback=self.callback();self.binary.write_bytes(b'changed')
  with patch.object(r.subprocess,'run')as proc:self.assertRaises(ValueError,callback,self.paper);proc.assert_not_called()
 def test_manifest_changed_after_factory_holds(self):
  callback=self.callback();self.manifest.write_bytes(self.manifest.read_bytes()+b' ');self.assertRaises(ValueError,callback,self.paper)
 def test_original_digest_source_hash_required(self):
  with patch.object(r,'DIGEST_SOURCE_SHA','0'*64):self.assertRaises(ValueError,self.callback)
 def test_one_use_render_observation_directory_is_exclusive(self):
  callback=self.callback()
  with patch.object(r.subprocess,'run',side_effect=self.execute):callback(self.paper);self.assertRaises(FileExistsError,callback,self.paper)
 def test_nonzero_or_nonpdf_or_absent_pdf_never_return(self):
  for kind in('exit','notpdf','absent'):
   target=self.paper.parent/f'render-{kind}';target.mkdir();p=target/'paper.tex';p.write_bytes(self.paper.read_bytes());callback=self.callback()
   def run(*a,**k):
    build=p.parent/'render-observation'
    if kind!='absent':(build/'render_driver.pdf').write_bytes(b'not PDF'if kind=='notpdf'else b'%PDF-')
    return SimpleNamespace(returncode=1 if kind=='exit'else 0,stdout=b'',stderr=b'')
   with patch.object(r.subprocess,'run',side_effect=run):self.assertRaises(ValueError,callback,p)
 def test_timeout_never_returns_pdf(self):
  callback=self.callback()
  with patch.object(r.subprocess,'run',side_effect=subprocess.TimeoutExpired(['fixture'],180)):self.assertRaises(subprocess.TimeoutExpired,callback,self.paper)
 def test_source_binary_cache_driver_copiedcache_and_scope_changes_after_render_hold(self):
  for kind in('source','binary','cache','driver','copiedcache','scope'):
   target=self.paper.parent/f'changed-{kind}';target.mkdir();p=target/'paper.tex';p.write_bytes(self.paper.read_bytes());callback=self.callback();old_bin=self.binary.read_bytes();old_cache=(self.cache/'file-000.raw').read_bytes()
   def run(*a,**k):
    build=p.parent/'render-observation';(build/'render_driver.pdf').write_bytes(b'%PDF-')
    if kind=='source':p.write_bytes(b'changed')
    elif kind=='binary':self.binary.write_bytes(b'changed')
    elif kind=='cache':(self.cache/'file-000.raw').write_bytes(b'changed')
    elif kind=='driver':(build/'render_driver.tex').write_bytes(b'changed')
    elif kind=='copiedcache':(build/'cache/file-000.raw').write_bytes(b'changed')
    return SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
   if kind=='scope':
    original=r.d.consume_notes;counter=[0]
    def consume(*a,**k):counter[0]+=1;return self.consumed if counter[0]==1 else{'changed':'scope'}
    with patch.object(r.d,'consume_notes',side_effect=consume),patch.object(r.subprocess,'run',side_effect=run):self.assertRaises(ValueError,callback,p)
   else:
    with patch.object(r.subprocess,'run',side_effect=run):self.assertRaises(ValueError,callback,p)
   self.binary.write_bytes(old_bin);(self.cache/'file-000.raw').write_bytes(old_cache)
 def test_adapter_changes_hold(self):
  callback=self.callback();original=r.read
  def read(p):return b'wrong source'if Path(p).resolve()==Path(r.__file__).resolve()else original(p)
  with patch.object(r,'read',side_effect=read):self.assertRaises(ValueError,callback,self.paper)
 def test_observation_is_rendering_not_acceptance(self):
  text=(HERE/'digest_weekly_render.py').read_text()
  for name in('comparator_cloud_lean_verifier','issue_lean_zero_sorry_certificate','keychain','urllib','publish(','enforcement_activation'):self.assertNotIn(name,text)
