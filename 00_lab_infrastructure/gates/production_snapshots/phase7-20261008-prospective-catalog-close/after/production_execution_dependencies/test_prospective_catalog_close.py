from pathlib import Path
import contextlib,copy,hashlib,json,sys,tempfile,types,unittest,__future__
from unittest import mock
import prospective_catalog_close as c

METHODS='''import hashlib,json\nfrom pathlib import Path\ndef digest(data):return hashlib.sha256(data).hexdigest()\ndef read_regular(path):return Path(path).read_bytes()\n'''
VERSION='''import json\nfrom pathlib import Path\ndef current_catalog(root,seen):\n p=Path(root)/'RESEARCH_PIPELINE_v2/corpus_ledger.json';b=d.read_regular(p);seen[str(p)]=d.digest(b);ledger=json.loads(b);a=json.loads(d.read_regular(Path(root)/ledger['enforcement_activation']['path']));r=json.loads(d.read_regular(Path(root)/a['authorized_runtime_update']['path']));catalog=json.loads(d.read_regular(Path(root)/r['policy_version_catalog']['path']));\n if catalog['last_policy']!='new':raise ValueError('current exact policy and unique archived versions required')\n return catalog\n'''
VERSION += '''
def implementation_for_note(note,root,current_module,*,catalog_consumer=current_catalog):
 seen={};result=catalog_consumer(root,seen)
 for p,h in seen.items():
  if d.digest(d.read_regular(p))!=h:raise ValueError('version source changed before return')
 return result
from contextlib import contextmanager
@contextmanager
def _exact_authority_framing(module,root):
 if module.d is d:raise ValueError('framing requires isolated exact archival reader')
 yield
'''
HELPER='''def validate(root,ledger,original,*,now=None):\n import json\n a=json.loads((root/ledger['enforcement_activation']['path']).read_bytes())\n if original!={'approved':True}:raise ValueError('original authority invalid')\n return {'profile':'PHASE7_SCOPED_POLICY','binding':a['authorized_runtime_update']}\n'''
class Fixture(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve(strict=True);self.gates=self.root/c.PREFIX;self.gates.mkdir(parents=True);self.stack=contextlib.ExitStack();self.addCleanup(self.stack.close);self.addCleanup(self.tmp.cleanup)
  self.stack.enter_context(mock.patch.object(c,'ROOT',self.root))
  def mod(name,text):
   p=self.gates/(name+'.py');p.write_text(text);m=types.ModuleType(name);m.__file__=str(p);exec(compile(text,str(p),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),m.__dict__);return m
  self.d=mod('methods_digest',METHODS);self.v=mod('phase7_policy_versions',VERSION);self.v.d=self.d;self.h=mod('phase7_runtime_update',HELPER)
  for n,m in(('VERSION_SHA',self.v),('METHODS_SHA',self.d),('HELPER_SHA',self.h)):self.stack.enter_context(mock.patch.object(c,n,c.digest(Path(m.__file__).read_bytes())))
  self.stack.enter_context(mock.patch.dict(sys.modules,{'phase7_runtime_update':self.h}))
  def put(n,v):
   p=self.root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(c.encode(v));return {'path':n,'sha256':c.digest(p.read_bytes())}
  self.put=put;orig=put('original.json',{'approved':True});oldcat=put('oldcat.json',{'last_policy':'old'});newcat=put('newcat.json',{'last_policy':'new'})
  oldrt=put('oldruntime.json',{'original_activation':orig,'policy_version_catalog':oldcat});newrt=put('newruntime.json',{'original_activation':orig,'policy_version_catalog':newcat})
  oldact=put('oldactivation.json',{'authorized_runtime_update':oldrt});newact=put('newactivation.json',{'authorized_runtime_update':newrt})
  self.ledger={'enforcement_activation':oldact,'publication_entities':[{'id':str(n),'enforcement_acceptable':True,'publication_registration_status':'PASS'if n<10 else'HOLD_NO_CLAIM_MAP'}for n in range(35)],'premise_declaration_cutover_run':'Run-188','unrelated':{'x':1}}
  self.path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';self.before=c.encode(self.ledger);self.path.write_bytes(self.before);self.sha=c.digest(self.before);self.proposed=copy.deepcopy(self.ledger);self.proposed['enforcement_activation']=newact;self.viewbinding=self.put('reports/verification-coverage/PROSPECTIVE_LEDGER.json',self.proposed)
 def scope(self,ledger=None,sha=None):return c.prospective_catalog_reader(self.v,self.proposed if ledger is None else ledger,expected_before_sha256=self.sha if sha is None else sha,prospective_binding=self.viewbinding)
 def test_old_disk_new_flat_mismatch_reproduced_then_exact_prospective_pass(self):
  with self.assertRaisesRegex(ValueError,'current exact policy'):self.v.implementation_for_note(None,self.root,None)
  with self.scope()as proof:
   self.assertEqual(self.v.implementation_for_note(None,self.root,None),{'last_policy':'new'});self.assertIs(self.v.d,self.d);self.assertEqual(self.d.read_regular(self.path),self.before);self.assertEqual(proof['mode'],'PROSPECTIVE_PRE_CAS')
  self.assertIs(self.v.d,self.d);self.assertEqual(self.path.read_bytes(),self.before);self.assertGreater(proof['redirected_reads'],0)
 def test_after_cas_reads_real_disk_without_facade(self):
  self.path.write_bytes(c.encode(self.proposed))
  with self.scope()as proof:self.assertIs(self.v.d,self.d);self.assertEqual(self.v.implementation_for_note(None,self.root,None),{'last_policy':'new'});self.assertEqual(proof['mode'],'REAL_DISK_UNWRAPPED')
 def test_foreign_path_exact_original_reader(self):
  p=self.root/'other.json';p.write_bytes(b'own-other-bytes')
  with self.scope():self.assertEqual(self.v.d.read_regular(p),b'own-other-bytes')
 def test_exception_restores_exact_reader(self):
  with self.assertRaisesRegex(RuntimeError,'body'):
   with self.scope():raise RuntimeError('body')
  self.assertIs(self.v.d,self.d)
 def test_wrong_pre_cas_hash_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'EXACT_PRE_CAS_DISK_HASH'):
   with self.scope(sha='0'*64):pass
 def test_all35_row_mutation_rejected(self):
  q=copy.deepcopy(self.proposed);q['publication_entities'][0]['publication_registration_status']='other'
  with self.assertRaisesRegex(c.CloseHold,'ONLY_ACTIVATION'):
   with self.scope(q):pass
 def test_unrelated_field_mutation_rejected(self):
  q=copy.deepcopy(self.proposed);q['unrelated']['x']=2
  with self.assertRaisesRegex(c.CloseHold,'ONLY_ACTIVATION'):
   with self.scope(q):pass
 def test_control_mutation_rejected(self):
  q=copy.deepcopy(self.proposed);q['premise_declaration_cutover_run']='Run-189'
  with self.assertRaises(c.CloseHold):
   with self.scope(q):pass
 def test_type_substitution_rejected(self):
  q=copy.deepcopy(self.proposed);q['unrelated']['x']=True
  with self.assertRaises(c.CloseHold):
   with self.scope(q):pass
 def test_nonacceptable_before_rejected(self):
  self.ledger['publication_entities'][0]['enforcement_acceptable']=False;self.path.write_bytes(c.encode(self.ledger));self.proposed['publication_entities'][0]['enforcement_acceptable']=False
  with self.assertRaisesRegex(c.CloseHold,'EXACT_ACCEPTABLE35_BEFORE'):
   with self.scope():pass
 def test_acceptable_truthy_integer_rejected(self):
  self.ledger['publication_entities'][0]['enforcement_acceptable']=1;self.path.write_bytes(c.encode(self.ledger));self.proposed['publication_entities'][0]['enforcement_acceptable']=1
  with self.assertRaises(c.CloseHold):
   with self.scope():pass
 def test_disk_change_during_read_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'DISK_CHANGED'):
   with self.scope():self.path.write_bytes(self.before+b' ');self.v.implementation_for_note(None,self.root,None)
  self.assertIs(self.v.d,self.d)
 def test_disk_change_during_body_finally_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'DISK_CHANGED'):
   with self.scope():self.path.write_bytes(self.before+b' ')
  self.assertIs(self.v.d,self.d)
 def test_reader_replacement_detected_and_original_restored(self):
  with self.assertRaisesRegex(c.CloseHold,'REGISTRY_IDENTITY_CHANGED'):
   with self.scope():self.v.d=types.SimpleNamespace()
  self.assertIsNot(self.v.d,self.d)
 def test_nested_view_rejected(self):
  with self.scope():
   with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:implementation_for_note'):
    with self.scope():pass
 def test_source_changed_during_body_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'SOURCE_CHANGED'):
   with self.scope():Path(self.h.__file__).write_text(HELPER+'\n')
  self.assertIs(self.v.d,self.d)
 def test_fake_runtime_success_function_rejected(self):
  self.h.validate=lambda *x:{'profile':'PHASE7_SCOPED_POLICY','binding':{}}
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:validate'):
   with self.scope():pass
 def test_reader_function_changed_before_scope_rejected(self):
  self.d.read_regular=lambda p:self.before
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:read_regular'):
   with self.scope():pass
 def test_version_function_changed_during_scope_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'REGISTRY_IDENTITY_CHANGED'):
   with self.scope():self.v.current_catalog=lambda *a:{}
 def test_flat_archive_delegate_identity_still_rejected(self):
  archive=types.SimpleNamespace(d=self.d)
  with self.scope():
   with self.assertRaisesRegex(ValueError,'isolated exact archival reader'):
    with self.v._exact_authority_framing(archive,self.root):pass
 def test_genuinely_isolated_archive_still_passes(self):
  archive=types.SimpleNamespace(d=types.ModuleType('isolated'))
  with self.scope():
   with self.v._exact_authority_framing(archive,self.root):pass
 def test_physical_proposal_changed_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'PROSPECTIVE_INPUT_CHANGED'):
   with self.scope():(self.root/self.viewbinding['path']).write_bytes(c.encode(self.proposed)+b' ')
 def test_wrong_proposal_byte_binding_rejected(self):
  self.viewbinding['sha256']='0'*64
  with self.assertRaisesRegex(c.CloseHold,'BOUND_BYTES'):
   with self.scope():pass
 def test_proposal_data_cannot_change_rows(self):
  self.viewbinding=self.put('reports/verification-coverage/PROSPECTIVE_LEDGER.json',{'other':'not proposed'})
  with self.assertRaisesRegex(c.CloseHold,'PHYSICAL_EXACT_PROSPECTIVE_LEDGER'):
   with self.scope():pass
 def test_original_digest_function_mutation_rejected(self):
  with self.assertRaisesRegex(c.CloseHold,'METHODS_FUNCTION_IDENTITY_CHANGED:digest'):
   with self.scope():self.d.digest=lambda x:'0'*64
 def test_unknown_explicit_catalog_provider_rejected(self):
  with self.scope():
   with self.assertRaisesRegex(c.CloseHold,'DEFAULT_CATALOG_CONSUMER_ONLY'):self.v.implementation_for_note(None,self.root,None,catalog_consumer=lambda *x:{})
 def test_source_hash_mismatch_rejected(self):
  Path(self.v.__file__).write_text(VERSION+'\n')
  with self.assertRaisesRegex(c.CloseHold,'EXACT_SOURCE'):
   with self.scope():pass
 def test_changed_activation_bytes_rejected(self):
  p=self.root/self.proposed['enforcement_activation']['path'];p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaisesRegex(c.CloseHold,'BOUND_BYTES'):
   with self.scope():pass
 def test_changed_default_catalog_function_rejected(self):
  self.v.implementation_for_note.__kwdefaults__={'catalog_consumer':lambda *a:{}}
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_KWDEFAULTS:implementation_for_note'):
   with self.scope():pass
 def test_changed_validate_now_default_rejected(self):
  self.h.validate.__kwdefaults__={'now':True}
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_KWDEFAULTS:validate'):
   with self.scope():pass
 def test_added_positional_default_rejected(self):
  self.d.digest.__defaults__=(b'foreign',)
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_DEFAULTS_CLOSURE:digest'):
   with self.scope():pass
 def test_changed_default_during_scope_rejected(self):
  original=self.v.implementation_for_note
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_KWDEFAULTS:implementation_for_note'):
   with self.scope():original.__kwdefaults__={'catalog_consumer':lambda *a:{}}
 def test_wrong_code_filename_rejected(self):
  self.d.digest.__code__=self.d.digest.__code__.replace(co_filename='foreign.py')
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:digest'):
   with self.scope():pass
 def test_code_mutation_same_function_object_rejected(self):
  self.d.digest.__code__=self.d.digest.__code__.replace(co_code=bytes([0])*len(self.d.digest.__code__.co_code))
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:digest'):
   with self.scope():pass
 def test_fixed_annotations_flag_cannot_be_removed(self):
  self.h.validate.__code__=self.h.validate.__code__.replace(co_flags=self.h.validate.__code__.co_flags^__future__.annotations.compiler_flag)
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:validate'):
   with self.scope():pass
 def test_global_namespace_replacement_rejected(self):
  old=self.d.digest;self.d.digest=types.FunctionType(old.__code__,dict(vars(self.d)),old.__name__)
  with self.assertRaisesRegex(c.CloseHold,'UNCHANGED_FUNCTION:digest'):
   with self.scope():pass
 def test_wrong_original_authority_default_validator_rejected(self):
  p=self.root/'original.json';p.write_bytes(c.encode({'approved':False}));r=self.root/'newruntime.json';v=json.loads(r.read_bytes());v['original_activation']=self.put('original.json',{'approved':False});br=self.put('newruntime.json',v);self.proposed['enforcement_activation']=self.put('newactivation.json',{'authorized_runtime_update':br});self.viewbinding=self.put('reports/verification-coverage/PROSPECTIVE_LEDGER.json',self.proposed)
  with self.assertRaisesRegex(ValueError,'original authority invalid'):
   with self.scope():pass

class RebaseTests(unittest.TestCase):
 def setUp(self):
  self.old=c.ROOT/'reports/verification-coverage/old';self.new=c.ROOT/'reports/verification-coverage/new';self.cfg={'output':str(self.old),'other':{'same':True}};self.rows=[{'path':str(n),'sha256':f'{n:064x}','source':{'path':str((self.old/'after-additional'/f'{n}.py').relative_to(c.ROOT)),'sha256':f'{n:064x}'}}for n in range(14)];self.pend={'additional_modules':self.rows,'policy_version_catalog':{'path':str((self.old/'POLICY_VERSION_CATALOG.json').relative_to(c.ROOT)),'sha256':'a'*64},'pull_request_readback':{'path':'old','sha256':'b'*64},'installed_at_utc':'unchanged','runtime_writes':14,'publication_entities':[{'full':'exact'}]};self.cat={'versions':[{'old':n}for n in range(3)]+[{'execution_consumer_sha256':'91910a8ca95f4af920c175bb8f20e368f897f8eca7e5526dfd0a1ab0fde6cd7e','files':[{'byte':'same'}],'pull_request_readback':{'path':'old','sha256':'b'*64}}]};self.copies={f'{n}.py':{'path':str((self.new/'after-additional'/f'{n}.py').relative_to(c.ROOT)),'sha256':f'{n:064x}'}for n in range(14)};self.pr={'path':'newpr','sha256':'b'*64};self.cb={'path':'newcat','sha256':'c'*64}
 def go(self):return c.rebased_inputs(self.cfg,self.pend,self.cat,self.old,self.new,self.copies,self.pr,self.cb)
 def test_exact14_pointers_rebased_originals_unchanged(self):
  old=copy.deepcopy((self.cfg,self.pend,self.cat));a,b,z=self.go();self.assertEqual((self.cfg,self.pend,self.cat),old);self.assertEqual(a['other'],self.cfg['other']);self.assertEqual(b['publication_entities'],self.pend['publication_entities']);self.assertEqual(b['installed_at_utc'],'unchanged');self.assertEqual(b['runtime_writes'],14);self.assertEqual(z['versions'][:3],self.cat['versions'][:3]);self.assertEqual(z['versions'][-1]['files'],self.cat['versions'][-1]['files'])
 def test_missing_source_copy_rejected(self):
  del self.copies['0.py']
  with self.assertRaises(c.CloseHold):self.go()
 def test_changed_source_byte_rejected(self):
  self.copies['0.py']['sha256']='f'*64
  with self.assertRaises(c.CloseHold):self.go()
 def test_foreign_source_row_rejected(self):
  self.pend['additional_modules'][0]['source']['path']='foreign/0.py'
  with self.assertRaises(c.CloseHold):self.go()
 def test_wrong_fourth_archive_rejected(self):
  self.cat['versions'][-1]['execution_consumer_sha256']='f'*64
  with self.assertRaises(c.CloseHold):self.go()
 def test_wrong_original_namespace_rejected(self):
  self.cfg['output']=str(self.new)
  with self.assertRaises(c.CloseHold):self.go()

class SourcePreservationTests(unittest.TestCase):
 def test_original_driver_still_exact(self):self.assertEqual(c.digest(c.DRIVER.read_bytes()),c.DRIVER_SHA)
 def test_closed_no_installer_or_zenodo_capability(self):
  import ast
  t=ast.parse(Path(c.__file__).read_bytes());attrs={n.attr for n in ast.walk(t)if isinstance(n,ast.Attribute)};self.assertNotIn('install',attrs);self.assertNotIn('request',attrs);self.assertNotIn('urlopen',attrs);self.assertNotIn('ZenodoTransport',attrs)

class CodeValueTests(unittest.TestCase):
 def code(self):return compile('def f(a):\n def inner():return (True, 1, -0.0)\n return inner\n','same.py','exec').co_consts[0]
 def test_storage_reconstruction_equal_all_fields(self):
  import marshal
  a=self.code();b=marshal.loads(marshal.dumps(a));self.assertTrue(c._code_value_exact(a,b));self.assertEqual(a.co_filename,b.co_filename)
 def test_fresh_source_load_and_compilation_equal(self):
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder).resolve(strict=True)/'real_load.py';p.write_text(METHODS);m=types.ModuleType('actual_load');m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec',flags=__future__.annotations.compiler_flag,dont_inherit=True),vars(m))
   c._compiled_function(m,p.read_bytes(),'read_regular');c._compiled_function(m,p.read_bytes(),'digest')
 def test_all_code_field_changes_rejected(self):
  a=self.code();changes={'co_filename':'other.py','co_qualname':'other.f','co_name':'g','co_firstlineno':19,'co_flags':a.co_flags^1,'co_code':bytes([0])*len(a.co_code),'co_linetable':b'','co_exceptiontable':b'changed','co_names':('foreign',),'co_varnames':('other','inner'),'co_stacksize':a.co_stacksize+1,'co_argcount':0,'co_consts':(None,False)}
  for field,value in changes.items():
   with self.subTest(field=field):self.assertFalse(c._code_value_exact(a,a.replace(**{field:value})))
 def test_nested_code_constant_changed_rejected(self):
  a=self.code();nested=next(x for x in a.co_consts if type(x)is types.CodeType);b=a.replace(co_consts=tuple(x.replace(co_consts=(None,('changed',)))if x is nested else x for x in a.co_consts));self.assertFalse(c._code_value_exact(a,b))
 def test_bool_int_and_float_bits_not_equal(self):
  self.assertFalse(c._code_value_exact(True,1));self.assertFalse(c._code_value_exact((True,),(1,)));self.assertFalse(c._code_value_exact(0.0,-0.0));self.assertFalse(c._code_value_exact(complex(0.0,0.0),complex(-0.0,0.0)))
 def test_nan_payload_bits_exact(self):
  import struct
  a=struct.unpack('!d',bytes.fromhex('7ff8000000000001'))[0];b=struct.unpack('!d',bytes.fromhex('7ff8000000000002'))[0];self.assertTrue(c._code_value_exact(a,a));self.assertFalse(c._code_value_exact(a,b))
 def test_unknown_typed_value_fails_closed(self):self.assertFalse(c._code_value_exact(object(),object()));self.assertFalse(c._code_value_exact([1],[1]))
if __name__=='__main__':unittest.main()
