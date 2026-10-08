"""Portable source-inventory integration: fixture consumers are not admission.

The real boundary.before/prior and real generic predecessor_inventory run;
only transport/default-registration fixture boundaries are isolated here.
"""
import builtins,copy,hashlib,json,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import digest_weekly_state as successor
import digest_metadata as metadata
import owned_prior_legacy as prior_guard

class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.package=self.root/'source-package';self.package.mkdir();self.out=self.root/'out';self.out.mkdir();self.calls=[];self.gets=[];self.capture_calls=[]
  self.rid='23226761';self.parent='23226760';self.rows=[]
  for name in ['paper.pdf','paper.tex','METHODS_NOTES.zip','README.md','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json']:
   p=self.package/name;p.write_bytes(('fixture '+name).encode());raw=p.read_bytes();self.rows.append({'filename':name,'sha256':hashlib.sha256(raw).hexdigest(),'md5':hashlib.md5(raw).hexdigest(),'bytes':len(raw)})
  self.admitted={'receipt':{'record_id':self.rid,'release_week':'2026-W41','package_path':'source-package'},'manifest':{'uploads':copy.deepcopy(self.rows[:4])}}
  self.registrar=types.ModuleType('methods_digest_registration')
  def require_registration(root,binding):
   self.assertEqual(root,self.root);self.assertEqual(binding,self.registration_binding);self.calls.append(copy.deepcopy(binding));return copy.deepcopy(self.admitted)
  self.registrar.require_registration=require_registration
  self.registration_binding={'path':str(self.root/'fixture-registration.json'),'sha256':'a'*64}
  self.plan={'start_kind':'CREATE_WEEK','release_week':'2026-W42','predecessor_record_id':self.rid,'predecessor_registration':self.registration_binding,'expected_concept_id':None}
  self.native={'id':self.rid,'versions':{'index':1,'is_latest':True,'is_latest_draft':True},'parent':{'id':self.parent},'links':{},'pids':{'doi':{'identifier':'10.5281/zenodo.'+self.rid}}}
  self.legacy={'id':int(self.rid),'metadata':{'title':'Fixture W41','relations':{'version':[{'index':0,'is_last':True,'parent':{'pid_type':'recid','pid_value':self.parent}}]}},'files':[{'key':r['filename'],'checksum':r['md5'],'size':r['bytes']}for r in self.rows],'links':{},'stats':{}}
  def equal(a,b,*args,**kwargs):
   if not metadata.exact(a,b):raise ValueError('fixture strict equality failure')
  self.sm=types.ModuleType('server_managed_fields');self.sm.validate_prior_version=equal;self.sm.require_links_stats=lambda *a,**kw:None
  self.pres=types.ModuleType('publication_preservation');self.pres.require_public_metadata=equal;self.pres.require_file_preservation=equal
  self.discovery=types.ModuleType('owned_weekly_discovery')
  def capture(root,week,token,out,opener):
   self.capture_calls.append((root,week));out.mkdir(parents=True);p=out/'DISCOVERY.json';p.write_bytes(e.raw_json({'start_kind':'CREATE_WEEK','record_id':None,'concept_id':None}));return e.binding(p)
  self.discovery.capture=capture
  self.pending=types.ModuleType('weekly_pending_discovery');self.pending_calls=[]
  def pending_capture(root,plan,state,token,out,opener):
   self.pending_calls.append((root,plan,state));raise ValueError('unit foreign pending week fixture')
  self.pending.capture=pending_capture
  modules={'weekly_digest_executor':e,'digest_weekly_state':successor,'digest_metadata':metadata,'first_digest_state':types.ModuleType('first_digest_state'),'digest_public_state':types.ModuleType('digest_public_state'),'publisher_previews':types.ModuleType('publisher_previews'),'server_managed_fields':self.sm,'publication_preservation':self.pres,'methods_digest':types.ModuleType('methods_digest'),'owned_legacy_preview_aliases':types.ModuleType('owned_legacy_preview_aliases'),'owned_prior_legacy':prior_guard,'methods_digest_registration':self.registrar,'owned_weekly_discovery':self.discovery,'weekly_pending_discovery':self.pending}
  publisher=types.ModuleType('first_digest_publisher');publisher.Downloads=object;publisher.PacedOpener=object;modules['first_digest_publisher']=publisher
  old_import=builtins.__import__
  def controlled(name,globals=None,locals=None,fromlist=(),level=0):return modules[name]if level==0 and name in modules else old_import(name,globals,locals,fromlist,level)
  self.mod=types.ModuleType('fixture_loaded_boundary');self.mod.__file__=str(Path(__file__).parent/'weekly_digest_boundary.py');self.mod.__dict__['__builtins__']=dict(vars(builtins),__import__=controlled);exec(compile(Path(self.mod.__file__).read_bytes(),self.mod.__file__,'exec'),self.mod.__dict__)
  self.b=self.mod.WeeklyDigestBoundary.__new__(self.mod.WeeklyDigestBoundary);self.b.plan=self.plan;self.b.root=self.root;self.b.saved_legacy=copy.deepcopy(self.legacy);self.b.saved_native=copy.deepcopy(self.native);self.b.discovery_count=0;self.b.token='fixture memory only';self.b.out=self.out;self.b.opener=None
  def get(rid,published,native=False):
   self.assertEqual(rid,self.rid);self.assertIs(published,True);self.gets.append((rid,published,native));return copy.deepcopy(self.native if native else self.legacy),{'path':'fixture-only','sha256':'a'*64}
  self.b.get=get;self.download_calls=[]
  def download(name,rid,spec,**kwargs):
   self.assertEqual(rid,self.rid);raw=(self.package/name).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),spec['sha256']);self.assertEqual(len(raw),spec['size']);self.download_calls.append(name)
  self.b.downloads=types.SimpleNamespace(get=download)
 def tearDown(self):self.tmp.cleanup()
 def call(self):
  with patch.dict(sys.modules,{'methods_digest_registration':self.registrar}):return self.b.before({'record_id':None})
 def test_real_boundary_before_sourceW41_newW42_pass(self):
  own=copy.deepcopy(self.plan);self.call();self.assertEqual(self.plan,own);self.assertEqual(set(self.download_calls),{r['filename']for r in self.rows});self.assertEqual(len(self.download_calls),6);self.assertEqual(self.capture_calls,[(self.root,'2026-W42')]);self.assertEqual(len(self.calls),2);self.assertEqual(self.gets,[(self.rid,True,False),(self.rid,True,True)])
 def test_substituted_default_source_record_fails(self):
  self.admitted['receipt']['record_id']='23999999';self.assertRaises(ValueError,self.call);self.assertEqual(self.download_calls,[])
 def test_same_week_source_cannot_masquerade_as_first_week(self):
  self.admitted['receipt']['release_week']='2026-W42';self.assertRaises(ValueError,self.call);self.assertEqual(self.download_calls,[])
 def test_substituted_upload_inventory_checksum_fails(self):
  self.admitted['manifest']['uploads'][0]['sha256']='0'*64;self.assertRaises(ValueError,self.call);self.assertEqual(self.download_calls,[])
 def test_changed_source_file_byte_fails(self):
  (self.package/self.rows[0]['filename']).write_bytes(b'changed');self.assertRaises(ValueError,self.call);self.assertEqual(self.download_calls,[])
 def test_missing_public_mainfile_fails(self):
  self.legacy['files'].pop();self.assertRaises(ValueError,self.call);self.assertEqual(self.download_calls,[])
 def test_owned_first_continuation_duplicate_week_fails_before_any_own_get(self):
  with patch.dict(sys.modules,{'methods_digest_registration':self.registrar}):self.assertRaises(ValueError,self.b.before,{'record_id':'23300001'})
  self.assertEqual(len(self.pending_calls),1);self.assertEqual(self.pending_calls[0][2]['record_id'],'23300001');self.assertEqual(self.gets,[]);self.assertEqual(self.download_calls,[]);self.assertEqual(self.calls,[])
 def test_same_week_uses_original_plan_without_projection(self):
  self.plan['start_kind']='NEW_VERSION';self.plan['release_week']='2026-W41';self.assertIs(self.b.source_inventory_plan(),self.plan)
if __name__=='__main__':unittest.main()
