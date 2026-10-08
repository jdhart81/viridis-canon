"""Lifecycle constructors only. Complete original consumers remain mandatory."""
from pathlib import Path
from copy import deepcopy
import ast,hashlib,json,unittest
from unittest.mock import patch
import test_digest_weekly_state as base
import digest_weekly_state as w
from fixture_successor import InitialCreationTests

class SameInitialTests(InitialCreationTests):
 def pair(self):
  f,r,n=self.fixture();n['pids']={};return f,r,n
 def test_same_initial_changes_only_pids_from_original(self):
  f,r,n=self.pair();old,legacy=w._initial_newversion_projection_pre_reserve_original(f.legacy,f.native,r,r['response'],n);new,newlegacy=w.initial_newversion_projection(f.legacy,f.native,r,r['response'],n)
  self.assertEqual(legacy,newlegacy);self.assertEqual(new['pids'],{});old['pids']={};self.assertEqual(old,new)
 def test_early_foreign_missing_extra_doi_oai_or_bool_native_pid_fail(self):
  for value in [None,True,{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'}},{'oai':{}},{'unknown':{}}]:
   f,r,n=self.pair();n['pids']=value;self.assertRaises(ValueError,w.initial_newversion_projection,f.legacy,f.native,r,r['response'],n)
 def test_source_science_owner_file_hash_or_ack_changes_still_fail(self):
  for fn in [lambda f,r,n:r['response']['metadata'].__setitem__('description','changed scientific claim'),lambda f,r,n:r['response'].__setitem__('owner',99),lambda f,r,n:r['response']['files'][0].__setitem__('checksum','f'*32),lambda f,r,n:r.__setitem__('http_status',200),lambda f,r,n:r['response'].__setitem__('unknown','extra')]:
   f,r,n=self.pair();fn(f,r,n);self.assertRaises(ValueError,w.initial_newversion_projection,f.legacy,f.native,r,r['response'],n)

class ReserveProjectionTests(unittest.TestCase):
 def fixture(self):
  rid='999999';parent='999997';doi='10.5281/zenodo.'+rid
  legacy={'id':int(rid),'record_id':int(rid),'conceptrecid':parent,'conceptdoi':'10.5281/zenodo.'+parent,'created':'2026-10-08T12:00:00Z','modified':'2026-10-08T12:00:00Z','owner':3974,'state':'unsubmitted','submitted':False,'title':'Viridis Methods Digest — 2026-W42','metadata':{'title':'Viridis Methods Digest — 2026-W42','description':'Exact scoped claims','license':{'id':'cc-by-4.0'},'prereserve_doi':{'doi':doi,'recid':int(rid)}},'files':[],'links':{'badge':'https://zenodo.org/badge/doi/.svg','latest_draft':'https://zenodo.org/api/deposit/depositions/'+rid,'bucket':'https://zenodo.org/api/files/11111111-1111-4111-8111-111111111111'}}
  native={'id':rid,'parent':{'id':parent},'pids':{'doi':{'identifier':doi,'provider':'datacite','client':'datacite'}},'created':legacy['created'],'updated':'2026-10-08T12:01:00Z'}
  receipt={'environment':'zenodo.org','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','method':'POST','url':'https://zenodo.org/api/records/'+rid+'/draft/pids/doi','accept':w.NATIVE_ACCEPT,'http_status':201,'request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'response_sha256':'a'*64,'response':native}
  return legacy,receipt,rid,parent
 def apply(self,parts):
  l,r,rid,parent=parts;return w.reserved_private_legacy_projection(l,r,record_id=rid,concept_id=parent)
 def test_five_derived_paths_only_all_unrelated_values_retained(self):
  p=self.fixture();before=deepcopy(p[0]);after=self.apply(p);doi='10.5281/zenodo.'+p[2];self.assertEqual(after['doi'],doi);self.assertEqual(after['doi_url'],'https://doi.org/'+doi);self.assertEqual(after['metadata']['doi'],doi);self.assertEqual(after['links']['doi'],'https://doi.org/'+doi);self.assertEqual(after['links']['badge'],'https://zenodo.org/badge/doi/10.5281%2Fzenodo.'+p[2]+'.svg');self.assertEqual(after['metadata']['prereserve_doi'],before['metadata']['prereserve_doi'])
  after.pop('doi');after.pop('doi_url');after['metadata'].pop('doi');after['links'].pop('doi');after['links']['badge']=before['links']['badge'];self.assertEqual(after,before);self.assertEqual(p[0],before)
 def test_every_unrelated_field_including_unknown_is_preserved_for_full_consumer(self):
  p=self.fixture();p[0]['unknown_science']={'statement':'must remain subject to full guard'};p[0]['metadata']['extra_claim']='no dropping';p[0]['links']['foreign']='https://foreign.example/';out=self.apply(p);self.assertEqual(out['unknown_science'],p[0]['unknown_science']);self.assertEqual(out['metadata']['extra_claim'],p[0]['metadata']['extra_claim']);self.assertEqual(out['links']['foreign'],p[0]['links']['foreign'])
 def test_native_reserved_pid_exact_solo_own_doi_only(self):
  for value in [{},{'doi':{'identifier':'10.5281/zenodo.123456','provider':'datacite','client':'datacite'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'other','client':'datacite'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'other'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'},'oai':{'provider':'oai'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite','extra':1}}]:
   p=self.fixture();p[1]['response']['pids']=value;self.assertRaises(ValueError,self.apply,p)
 def test_native_reserve_transport_method_url_status_accept_env_body_and_ids_fail(self):
  for key,value in [('method','GET'),('url','https://zenodo.org/api/records/123456/draft/pids/doi'),('http_status',200),('http_status',True),('accept','application/json'),('environment','sandbox.zenodo.org'),('status','PASS'),('request_body_sha256','a'*64),('response_sha256','not-hash')]:
   p=self.fixture();p[1][key]=value;self.assertRaises(ValueError,self.apply,p)
  for key,value in [('id','123456'),('parent',{'id':'123456'})]:
   p=self.fixture();p[1]['response'][key]=value;self.assertRaises(ValueError,self.apply,p)
 def test_missing_every_transport_provenance_field_fails(self):
  for key in ['environment','method','url','accept','status','http_status','request_body_sha256','response_sha256','response']:
   p=self.fixture();p[1].pop(key);self.assertRaises(ValueError,self.apply,p)
 def test_constructor_returns_independent_copies_without_admission_fields(self):
  p=self.fixture();pid=w.reserved_native_pid(p[1],record_id=p[2],concept_id=p[3]);pid['doi']['identifier']='modified';self.assertNotEqual(pid,p[1]['response']['pids']);out=self.apply(p);out['metadata']['description']='modified';self.assertEqual(p[0]['metadata']['description'],'Exact scoped claims');self.assertNotIn('certifies',out)
 def test_wrong_output_scientific_values_or_main_file_checksums_fail_unchanged_guard(self):
  from first_digest_state import require_private_source
  import server_managed_fields as sm
  import publication_preservation as preservation
  from zenodo_transport import TransportHold
  p=self.fixture();p[0]['files']=[{'filename':'proof.lean','checksum':'a'*32,'filesize':10,'links':{}}];wanted=self.apply(p);actual=deepcopy(wanted);actual['modified']=p[1]['response']['updated'];require_private_source(actual,wanted,p[1]['response'],sm,preservation)
  for key,value in [('checksum','b'*32),('filesize',11),('filename','other.lean')]:
   bad=deepcopy(actual);bad['files'][0][key]=value;self.assertRaises((ValueError,TransportHold),require_private_source,bad,wanted,p[1]['response'],sm,preservation)
 def test_legacy_identity_state_prereg_badge_already_reserved_or_unknown_doi_fail(self):
  for key,value in [('id',123456),('record_id',123456),('conceptrecid','123456'),('state','done'),('submitted',True),('doi','10.5281/zenodo.999999'),('doi_url','https://doi.org/10.5281/zenodo.999999')]:
   p=self.fixture();p[0][key]=value;self.assertRaises(ValueError,self.apply,p)
  for key,value in [('prereserve_doi',{'doi':'10.5281/zenodo.123456','recid':123456}),('prereserve_doi',{'doi':'10.5281/zenodo.999999','recid':True}),('doi','10.5281/zenodo.999999')]:
   p=self.fixture();p[0]['metadata'][key]=value;self.assertRaises(ValueError,self.apply,p)
  for key,value in [('badge','https://zenodo.org/badge/doi/foreign.svg'),('doi','https://doi.org/10.5281/zenodo.999999')]:
   p=self.fixture();p[0]['links'][key]=value;self.assertRaises(ValueError,self.apply,p)
 def test_unchanged_full_private_guard_pass_and_must_fail_any_content_or_link_change(self):
  from first_digest_state import require_private_source
  import server_managed_fields as sm
  import publication_preservation as preservation
  from zenodo_transport import TransportHold
  p=self.fixture();wanted=self.apply(p);actual=deepcopy(wanted);actual['modified']=p[1]['response']['updated'];require_private_source(actual,wanted,p[1]['response'],sm,preservation)
  for mutate in [lambda x:x['metadata'].__setitem__('description','stronger claim'),lambda x:x['metadata'].__setitem__('license',{'id':'other'}),lambda x:x.__setitem__('owner',99),lambda x:x['links'].__setitem__('doi','https://doi.org/10.5281/zenodo.123456'),lambda x:x['links'].__setitem__('badge','https://zenodo.org/badge/doi/foreign.svg'),lambda x:x['files'].append({'filename':'foreign.lean','checksum':'a'*32,'filesize':1})]:
   bad=deepcopy(actual);mutate(bad);self.assertRaises((ValueError,TransportHold),require_private_source,bad,wanted,p[1]['response'],sm,preservation)

class ExactPreservationTests(unittest.TestCase):
 def test_entire_v004_producer_is_byte_exact_prefix_and_only_named_additions(self):
  old=(base.HERE/'BEFORE_V004_digest_weekly_state.py').read_text();new=(base.HERE/'digest_weekly_state.py').read_text();self.assertTrue(new.startswith(old));prior=[n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)];allnodes=[n for n in ast.parse(new).body if isinstance(n,ast.FunctionDef)];self.assertEqual([n.name for n in allnodes[len(prior):]],['initial_newversion_projection','reserved_native_pid','reserved_private_legacy_projection','_require_reserved_public_pid','predict_native','predict_first_week_native'])
  for a,b in zip(prior,allnodes):self.assertEqual(ast.get_source_segment(old,a),ast.get_source_segment(new,b))
 def test_dispatcher_and_archived_producers_and_primitives_unchanged(self):
  self.assertEqual(hashlib.sha256((base.HERE/'digest_public_state.py').read_bytes()).hexdigest(),'7c9497ed6001cb6aa797fe39ab5198fde72653c6e406a14cccde420094b862bc');self.assertEqual(w.old.source_sha(),'b5545e923092f281bb865c24c8ff0b311aa9a2d290592da5e3ad3ef0d537cf38');self.assertEqual(base.previous.source_sha(),'11a173b3781301cb6070ebc5d37763f5aca8558972351abfb2cf546c73369567')
 def test_public_prediction_extra_own_oai_unknown_or_unreserved_pid_fails(self):
  for method in ['predict_native','predict_first_week_native']:
   for value in [{},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'},'oai':{}}]:
    before={'id':'999999','parent':{'id':'999997'},'pids':value};reserve={'id':'999999','parent':{'id':'999997'},'pids':value};self.assertRaises(ValueError,getattr(w,method),{}, {}, {},before,{},reserve,{})
if __name__=='__main__':unittest.main()
