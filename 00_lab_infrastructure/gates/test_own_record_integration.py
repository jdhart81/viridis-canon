"""Source-preservation/authority framing tests; no science admission fixtures."""
import ast,hashlib,importlib.util,os,sys,types,unittest
from pathlib import Path
from copy import deepcopy
HERE=Path(__file__).resolve().parent
OLD=HERE/'test_fixtures/own_record_comparison_old'
PLAN=HERE/'test_fixtures/own_record_comparison_authority.md'
# An explicit source directory wins; otherwise use the flat gate directory or
# adjacent gate sources. No user checkout, installed runtime, or canonical root.
_SOURCE_NAME='VIRIDIS_OWN_RECORD_SOURCE_DIR'
_requested=os.environ.get(_SOURCE_NAME) or os.environ.get('G')
_required=('own_record_comparison.py','phase7_policy_versions.py',
           'digest_public_state.py','methods_digest_registration.py',
           'methods_digest_registration_legacy_0fc739.py')
_candidates=[Path(_requested)] if _requested else [HERE/'tests/fixtures/phase7_prior_content_historical_v001',HERE,HERE.parent,HERE.parent/'gates']
_matches=[p.resolve() for p in _candidates if all((p/n).is_file() for n in _required)]
if not _matches:
 raise RuntimeError('Set VIRIDIS_OWN_RECORD_SOURCE_DIR to the operative flat gate source directory')
SOURCE=_matches[0]


def load_own():
 spec=importlib.util.spec_from_file_location('portable_own_record_comparison',SOURCE/'own_record_comparison.py')
 own=importlib.util.module_from_spec(spec);spec.loader.exec_module(own);return own


def load_versions():
 prior=sys.modules.get('methods_digest');sys.modules['methods_digest']=types.ModuleType('methods_digest')
 try:
  spec=importlib.util.spec_from_file_location('own_record_proposed_versions',SOURCE/'phase7_policy_versions.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
 finally:
  if prior is None:sys.modules.pop('methods_digest',None)
  else:sys.modules['methods_digest']=prior

def functions(raw):return {node.name:ast.dump(node,include_attributes=False)for node in ast.parse(raw).body if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}

class AuthorityTests(unittest.TestCase):
 def setUp(self):self.v=load_versions();self.raw=PLAN.read_bytes()
 def test_actual_new_authority_preserves_old_view(self):
  own=self.raw.index(self.v.OWN_RECORD_HEADER.encode());prefix=self.raw[:own-1]
  self.assertEqual(self.v.normalize_authority_plan(self.raw),self.v._normalize_authority_pre_own_record(prefix))
 def test_catalog_and_both_old_scientific_sections_still_exact(self):
  for token in('APPENDIX_HEADER','SIMPLIFICATION_HEADER','DECOUPLING_HEADER'):
   with self.subTest(token=token):
    at=self.raw.index(getattr(self.v,token).encode())+len(getattr(self.v,token).encode())+5;changed=self.raw[:at]+b'X'+self.raw[at+1:]
    with self.assertRaises(ValueError):self.v.normalize_authority_plan(changed)
 def test_changed_own_rule_fails(self):
  with self.assertRaises(ValueError):self.v.normalize_authority_plan(self.raw.replace(b'Everything else Zenodo sets',b'Everywhere else Zenodo sets'))
 def test_unknown_later_appendix_fails(self):
  with self.assertRaises(ValueError):self.v.normalize_authority_plan(self.raw+b'\n## Unapproved\ncontents\n')
 def test_duplicate_own_rule_fails(self):
  with self.assertRaises(ValueError):self.v.normalize_authority_plan(self.raw+self.v.OWN_RECORD_HEADER.encode())
 def test_different_boundary_fails(self):
  token=b'\n---\n\n'+self.v.OWN_RECORD_HEADER.encode()
  with self.assertRaises(ValueError):self.v.normalize_authority_plan(self.raw.replace(token,b'\n--- \n\n'+self.v.OWN_RECORD_HEADER.encode()))
 def test_unknown_bytes_type_fails(self):
  with self.assertRaises(ValueError):self.v.normalize_authority_plan(self.raw.decode())
 def test_prior_plan_without_new_rule_remains_old_code(self):
  before=self.raw[:self.raw.index(self.v.OWN_RECORD_HEADER.encode())-1]
  self.assertEqual(self.v.normalize_authority_plan(before),self.v._normalize_authority_pre_own_record(before))

class PreservationTests(unittest.TestCase):
 def test_dispatcher_exact_old_prefix(self):self.assertTrue((SOURCE/'digest_public_state.py').read_bytes().startswith((OLD/'digest_public_state.py').read_bytes()))
 def test_versions_exact_old_prefix(self):self.assertTrue((SOURCE/'phase7_policy_versions.py').read_bytes().startswith((OLD/'phase7_policy_versions.py').read_bytes()))
 def test_historical_registrar_raw_bytes(self):
  raw=(SOURCE/'methods_digest_registration_legacy_0fc739.py').read_bytes();self.assertEqual(raw,(OLD/'methods_digest_registration.py').read_bytes());self.assertEqual(hashlib.sha256(raw).hexdigest(),'0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9')
 def test_every_other_registrar_function_unchanged(self):
  old=functions((OLD/'methods_digest_registration.py').read_bytes());new=functions((SOURCE/'methods_digest_registration.py').read_bytes())
  for name,body in old.items():
   if name not in{'_check_public','require_registration'}:self.assertEqual(body,new[name],name)
 def test_two_changed_entry_bodies_preserve_old_tail(self):
  old=ast.parse((OLD/'methods_digest_registration.py').read_bytes());new=ast.parse((SOURCE/'methods_digest_registration.py').read_bytes())
  originals={x.name:x for x in old.body if isinstance(x,ast.FunctionDef)};changed={x.name:x for x in new.body if isinstance(x,ast.FunctionDef)}
  for name,n in(('_check_public',6),('require_registration',4)):
   if name=='_check_public':
    guard=ast.parse("if not isinstance(evidence,dict):raise RegistrationHold('closed own published digest evidence required')").body[0]
    self.assertEqual(ast.dump(changed[name].body[0],include_attributes=False),ast.dump(guard,include_attributes=False))
    self.assertEqual([ast.dump(x,include_attributes=False)for x in changed[name].body[1:4]],[ast.dump(x,include_attributes=False)for x in originals[name].body[:3]])
   node=deepcopy(changed[name]);node.body=node.body[n:]
   self.assertEqual(ast.dump(node,include_attributes=False),ast.dump(originals[name],include_attributes=False),name)
 def test_new_current_context_does_not_call_old_server_audit(self):
  raw=(SOURCE/'methods_digest_registration.py').read_text();tree=ast.parse(raw);new=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='_check_public_own_record')
  source=ast.get_source_segment(raw,new)
  self.assertNotIn('audit_readback',source);self.assertIn('strict_consumer(package,root,actual_legacy',source);self.assertIn('own_policy.require_own_readback',source)
 def test_strict_scientific_default_and_evidence_abi_unchanged(self):
  old=ast.parse((OLD/'methods_digest_registration.py').read_bytes());new=ast.parse((SOURCE/'methods_digest_registration.py').read_bytes())
  names={'STANDARD','EVIDENCE_STANDARD','EVIDENCE_FIELDS','RECEIPT_FIELDS'}
  def values(tree):return {x.targets[0].id:ast.dump(x,include_attributes=False)for x in tree.body if isinstance(x,ast.Assign)and isinstance(x.targets[0],ast.Name)and x.targets[0].id in names}
  self.assertEqual(values(old),values(new))


class CurrentPolicyContractTests(unittest.TestCase):
 def test_later_appendix_does_not_rebind_original_own_authority(self):
  own=load_own()
  raw=PLAN.read_bytes();expected=own.require_authority(raw)['section_sha256']
  self.assertEqual(own.require_authority(raw+b'\n---\n\n## Later approved decision\nFuture text.\n')['section_sha256'],expected)
 def test_put_uses_planned_ny_publish_day_not_put_day(self):
  own=load_own()
  payload={'metadata':{'publication_date':'2026-10-10'}}
  self.assertEqual(own.require_metadata_put(payload,publish_at='2026-10-11T01:00:00+00:00'),payload)
  with self.assertRaises(own.OwnRecordHold):own.require_metadata_put(payload,publish_at='2026-10-10T01:00:00+00:00')
 def test_initial_date_uses_authenticated_utc_creation_date(self):
  own=load_own()
  self.assertEqual(own.creation_date('2026-10-08T01:00:00+00:00'),'2026-10-08')
  self.assertEqual(own.publication_date('2026-10-08T01:00:00+00:00'),'2026-10-07')
 def test_native_vocabulary_labels_are_logged_not_controlled(self):
  own=load_own()
  projected={'title':'x','description':'b','publication_date':'2026-10-10','publisher':'Zenodo','rights':[{'id':'cc-by-4.0','description':'old'}],'resource_type':{'id':'publication-preprint','title':{'en':'Preprint'}},'languages':[{'id':'eng','title':{'en':'English'}}]}
  expected=own.native_sent_metadata(projected)
  self.assertNotIn('publisher',expected);self.assertEqual(expected['rights'],[{'id':'cc-by-4.0'}]);self.assertEqual(expected['resource_type'],{'id':'publication-preprint'})
  actual=deepcopy(projected);actual['rights'][0]['description']='new';actual['publisher']='different server display';actual['resource_type']['title']={'en':'New label'}
  own._metadata(actual,expected,'NATIVE')
  actual['rights'][0]['id']='wrong-license'
  with self.assertRaises(own.OwnRecordHold):own._metadata(actual,expected,'NATIVE')

class AccessContradictionTests(unittest.TestCase):
 def test_explicit_open_payload_requires_public_record_and_file_access(self):
  own=load_own()
  c={'legacy_metadata':{'access_right':'open'}}
  own._access({'access':{'record':'public','files':'public','embargo':{'active':False},'status':'server_display'}},c)
  for actual in({'record':'restricted','files':'public'},{'record':'public','files':'restricted'},{'record':'public','files':'public','embargo':{'active':True}},{'record':'public','files':'public','embargo':{'active':0}}):
   with self.subTest(actual=actual):
    with self.assertRaises(own.OwnRecordHold):own._access({'access':actual},c)

class FixtureIntegrityTests(unittest.TestCase):
 def test_all_old_sources_are_exact_frozen_bytes(self):
  expected={'methods_digest_registration.py': '0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9', 'digest_public_state.py': '7c9497ed6001cb6aa797fe39ab5198fde72653c6e406a14cccde420094b862bc', 'phase7_policy_versions.py': '567841ad67a8fe8c8239be3bc5b922eb73975fc2650086e2b0c0cfdd6e4b0576'}
  for name,digest in expected.items():
   with self.subTest(name=name):self.assertEqual(hashlib.sha256((OLD/name).read_bytes()).hexdigest(),digest)
 def test_authority_contains_only_four_exact_approved_sections(self):
  raw=PLAN.read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'eae8a67135cbcdcb43b73c074c9a54ec6341455a178d7c66d0ce68a839d0f9e3')
  self.assertTrue(raw.startswith(b'## Phase 7 Gate 3 resolution: decouple probes from witnesses'))
  self.assertEqual(raw.count(b'\n## '),3)


class ClosedEvidenceGuardTests(unittest.TestCase):
 def test_non_dict_evidence_is_typed_hold_before_every_downstream_consumer(self):
  # Execute the actual current AST, retaining its complete body. Placeholder
  # defaults/consumers only raise; no fake scientific or publication PASS exists.
  tree=ast.parse((SOURCE/'methods_digest_registration.py').read_bytes())
  hold=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='RegistrationHold')
  function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='_check_public')
  reached=[]
  def forbidden(*args,**kwargs):
   reached.append('downstream');raise AssertionError('non-dict evidence reached downstream consumer')
  namespace={'current_digest':forbidden,'d':types.SimpleNamespace(strict_readback=forbidden),
             '_record_id':forbidden,'_object':forbidden,'_check_public_own_record':forbidden}
  code=ast.Module(body=[deepcopy(hold),deepcopy(function)],type_ignores=[])
  exec(compile(code,'<actual-current-registrar-early-guard>','exec'),namespace)
  for evidence in (None,False,'unbound evidence',[],[{'public_state_context':None}],0):
   with self.subTest(evidence=evidence):
    with self.assertRaisesRegex(namespace['RegistrationHold'],'^closed own published digest evidence required$'):
     namespace['_check_public'](None,None,None,evidence,{})
    self.assertEqual(reached,[])

if __name__=='__main__':unittest.main()
