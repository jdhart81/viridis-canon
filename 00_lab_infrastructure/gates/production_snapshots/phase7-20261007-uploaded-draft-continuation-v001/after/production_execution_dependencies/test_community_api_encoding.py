"""Offline API spelling regressions; no scientific or live publication evidence."""
import ast,copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode=True
import digest_metadata as m
import first_digest_state as state
import first_digest_publisher as publisher
import test_publisher_guards as base
import test_coordinator as coordinator
from methods_digest_registration import source_custom_fields,RegistrationHold
from zenodo_transport import TransportHold

BAD_PUBLIC=[None,{},'viridis-canon',[{}],[{'identifier':'viridis-canon'}],[{'id':'x','title':'extra'}],[{'id':None}],[{'id':1}],[{'id':''}],[{'id':' x'}],[{'id':'x '}],[{'id':'x'},{'id':'x'}]]
BAD_REQUEST=[None,{},'viridis-canon',[{}],[{'id':'viridis-canon'}],[{'identifier':'x','title':'extra'}],[{'identifier':None}],[{'identifier':1}],[{'identifier':''}],[{'identifier':' x'}],[{'identifier':'x '}],[{'identifier':'x'},{'identifier':'x'}]]

class CommunityAPITests(unittest.TestCase):
 def test_actual_identifier_inverse_case(self):
  public=[{'id':'viridis-preservation-20261004'}]
  self.assertEqual(state.community_request(public),[{'identifier':'viridis-preservation-20261004'}])
  self.assertEqual(state.community_public(state.community_request(public)),public)
 def test_order_and_case_are_exact(self):
  rows=[{'id':'Exact-case'},{'id':'second_community'}]
  self.assertEqual(state.community_public(state.community_request(rows)),rows)
 def test_empty_membership_roundtrip(self):
  self.assertEqual(state.community_request([]),[]);self.assertEqual(state.community_public([]),[])
 def test_absent_membership_stays_absent(self):
  public,source,*_=base.fixture();public.pop('communities');source.pop('communities')
  self.assertNotIn('communities',state.encode_api_communities(m.closed_payload(public,source))['metadata'])
 def test_payload_only_community_key_changes(self):
  public,source,*_=base.fixture();before=copy.deepcopy((public,source));actual=state.encode_api_communities(m.closed_payload(public,source))['metadata']
  wanted=copy.deepcopy(public);typ=wanted.pop('resource_type');wanted.update(upload_type=typ['type'],publication_type=typ['subtype'],license=wanted['license']['id']);wanted['communities']=[{'identifier':'viridis-canon'}]
  self.assertEqual(actual,wanted);self.assertEqual((public,source),before)
 def test_source_membership_change_fails(self):
  public,source,*_=base.fixture();public['communities']=[{'id':'foreign'}]
  with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
 def test_source_presence_change_fails(self):
  public,source,*_=base.fixture();public.pop('communities')
  with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
 def test_definition_metadata_prediction_preserved(self):
  values=base.fixture();predicted=m.native_metadata(*values);self.assertNotIn('communities',predicted)
  self.assertEqual(predicted['rights'],values[3]['metadata']['rights']);self.assertEqual(predicted['creators'],values[3]['metadata']['creators'])
 def test_source_custom_fields_exact_inverse(self):
  f=coordinator.Fixture()
  try:
   converted=copy.deepcopy(f.api['metadata']);converted['communities']=state.community_public(converted['communities'])
   self.assertEqual(source_custom_fields(converted,f.source_legacy,f.source_native),{'legacy:communities':['viridis-canon']})
  finally:f.close()
 def test_foreign_request_membership_cannot_be_adopted(self):
  f=coordinator.Fixture()
  try:
   foreign=copy.deepcopy(f.api['metadata']);foreign['communities']=[{'id':'foreign'}]
   with self.assertRaises(RegistrationHold):source_custom_fields(foreign,f.source_legacy,f.source_native)
  finally:f.close()
 def test_creation_private_metadata_retains_identifier(self):
  f=coordinator.Fixture()
  try:
   now=f.now();created=f.creation(now);expected=state.private_metadata_expected(f.api,created,f.expected_native)
   self.assertEqual(expected['communities'],[{'identifier':'viridis-canon'}])
   actual,legacy=state.initial_expected(created,{'id':f.rid,'revision_id':0,'expires_at':now},f.expected_native,f.source_native,f.api,f.runtime.sm,coordinator.preserve,source_legacy=f.source_legacy)
   self.assertEqual(legacy['metadata']['communities'],expected['communities']);self.assertEqual(actual['custom_fields'],f.source_native['custom_fields'])
  finally:f.close()
 def test_initial_expected_rejects_foreign_request_after_exact_private_check(self):
  f=coordinator.Fixture()
  try:
   f.api['metadata']['communities']=[{'identifier':'foreign'}];now=f.now();created=f.creation(now)
   with self.assertRaises(RegistrationHold):state.initial_expected(created,{'id':f.rid,'revision_id':0,'expires_at':now},f.expected_native,f.source_native,f.api,f.runtime.sm,coordinator.preserve,source_legacy=f.source_legacy)
  finally:f.close()
 def test_initial_expected_rejects_old_id_request(self):
  f=coordinator.Fixture()
  try:
   f.api['metadata']['communities']=[{'id':'viridis-canon'}];now=f.now();created=f.creation(now)
   with self.assertRaises(m.MetadataHold):state.initial_expected(created,{'id':f.rid,'revision_id':0,'expires_at':now},f.expected_native,f.source_native,f.api,f.runtime.sm,coordinator.preserve,source_legacy=f.source_legacy)
  finally:f.close()
 def test_wrong_private_response_community_spelling_fails(self):
  f=coordinator.Fixture()
  try:
   now=f.now();created=f.creation(now);created['metadata']['communities']=[{'id':'viridis-canon'}]
   with self.assertRaises(TransportHold):state.initial_expected(created,{'id':f.rid,'revision_id':0,'expires_at':now},f.expected_native,f.source_native,f.api,f.runtime.sm,coordinator.preserve,source_legacy=f.source_legacy)
  finally:f.close()
 def test_nine_write_protocol_server_requires_documented_input(self):
  f=coordinator.Fixture(seven=True);original=coordinator.FakeTransport.request;seen=[]
  def strict(transport,method,url,body=None,*args,**kwargs):
   if method=='POST'and url=='https://zenodo.org/api/deposit/depositions'or method=='PUT'and url=='https://zenodo.org/api/deposit/depositions/'+f.rid:
    request=json.loads(body);self.assertEqual(request['metadata']['communities'],[{'identifier':'viridis-canon'}]);seen.append(method)
   return original(transport,method,url,body,*args,**kwargs)
  try:
   with patch.object(coordinator.FakeTransport,'request',strict):result=f.run()
   self.assertEqual(result['status'],'PUBLISHED_STRICT_READBACK_PASS',result);self.assertEqual(seen,['POST','PUT']);self.assertEqual(result['writes'],9)
   self.assertEqual(f.public_legacy['metadata']['communities'],[{'id':'viridis-canon'}]);self.assertEqual(f.public_native['custom_fields'],{'legacy:communities':['viridis-canon']})
  finally:f.close()
 def test_http400_still_consumes_slot_no_replay(self):
  f=coordinator.Fixture();f.uncertain_write=1;original=coordinator.FakeTransport.request
  def rejected(transport,*args,**kwargs):
   try:return original(transport,*args,**kwargs)
   except RuntimeError:
    receipt=f.output/'transport/003_POST.json';v=json.loads(receipt.read_bytes());v.update(http_status=400,error_type='HTTPError',error_response={'status':400,'errors':[{'field':'communities'}]});receipt.write_bytes(publisher.raw_json(v));raise
  try:
   with patch.object(coordinator.FakeTransport,'request',rejected):result=f.run()
   self.assertEqual(result['writes'],1);self.assertIsNone(result['record_id']);self.assertEqual(f.budget(f.root,'POST',f.now())['used'],1)
   with self.assertRaises(publisher.PublishHold):f.run()
   self.assertEqual(len(f.calls),1)
  finally:f.close()
 def test_publisher_driver_only_codec_and_request_identity_lines_change(self):
  text=Path(publisher.__file__).read_text();old="        operation_id='phase7-digest:'+manifest['release_week']+':'+hashlib.sha256(read_regular(package/'DIGEST_MANIFEST.json')).hexdigest()[:16]+':'+str(result['writes']+1)";new="        operation_id='phase7-digest:'+manifest['release_week']+':'+hashlib.sha256(read_regular(package/'DIGEST_MANIFEST.json')).hexdigest()[:16]+':'+hashlib.sha256(body).hexdigest()+':'+str(result['writes']+1)"
  self.assertEqual(text.count(new),1);self.assertNotIn(old+'\n',text);restored=text.replace(new,old).replace("api=state.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],before));","api=metadata.closed_payload(manifest['public_metadata'],before);")
  self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(),'6b838bc1ab12c0d66ef99e5e51c53181f1e0ba70ceb92b8f8d0506476005b345')

class ReservationIdentityTests(unittest.TestCase):
 def test_old_spent_request_retained_new_body_distinct_and_total_ten(self):
  f=coordinator.Fixture(seven=True)
  try:
   old_api=copy.deepcopy(f.api);old_api['metadata']['communities']=[{'id':'viridis-canon'}];old_body=publisher.raw_json(old_api)
   manifest_hash=hashlib.sha256((f.package/'DIGEST_MANIFEST.json').read_bytes()).hexdigest();old_id='phase7-digest:'+f.manifest['release_week']+':'+manifest_hash[:16]+':1'
   old_out=f.root/'reports/verification-coverage/2026-10-07/old-failed';receipt=old_out/'transport/003_POST.json'
   with publisher.JournalWriter(f.root,old_out/'reservations',coordinator.mut.require_events,f.budget)as writer:
    reservation=writer.reserve('POST','https://zenodo.org/api/deposit/depositions',old_body,receipt,f.now(),old_id,coordinator.actual_digest.require_write_budget)
   coordinator.write(receipt,{'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':hashlib.sha256(old_body).hexdigest(),'environment':'zenodo.org','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY','http_status':400,'error_type':'HTTPError'})
   preserved=Path(reservation['reservation']['path']).read_bytes();self.assertEqual(f.budget(f.root,'POST',f.now())['used'],1)
   result=f.run();self.assertEqual(result['status'],'PUBLISHED_STRICT_READBACK_PASS',result);self.assertEqual(result['writes'],9);self.assertEqual(len(coordinator.mut.require_events(f.root,f.now())),10)
   with self.assertRaises(coordinator.actual_digest.DigestHold):f.budget(f.root,'POST',f.now())
   self.assertEqual(Path(reservation['reservation']['path']).read_bytes(),preserved)
   first=json.loads((f.output/'WRITE_01_PRECHECK.json').read_bytes())['reservation'];new_id=first['operation_id'];expected='phase7-digest:'+f.manifest['release_week']+':'+manifest_hash[:16]+':'+hashlib.sha256(publisher.raw_json(f.api)).hexdigest()+':1'
   self.assertEqual(new_id,expected);self.assertNotEqual(new_id,old_id)
   self.assertEqual(len(f.calls),9)
  finally:f.close()
 def test_repeated_exact_body_same_id_is_rejected_by_unchanged_consumer(self):
  f=coordinator.Fixture();f.uncertain_write=1
  try:
   f.run();index=json.loads(f.index.read_bytes());old=index['reservations'][0]
   # Corrupt only this isolated synthetic index to demonstrate closed consumer
   # rejection. Never call reserve/network or alter any real journal.
   index['reservations'].append(copy.deepcopy(old));coordinator.write(f.index,index)
   with self.assertRaisesRegex(ValueError,'closed unique mutation reservation'):coordinator.mut.require_events(f.root,f.now())
   self.assertEqual(len(f.calls),1)
  finally:f.close()
 def test_corrected_body_same_manifest_has_stable_exact_identity(self):
  prefix='phase7-digest:2026-W41:88102cd5aa2c72b9:'
  old=publisher.raw_json({'metadata':{'communities':[{'id':'viridis-canon'}]}});new=publisher.raw_json({'metadata':{'communities':[{'identifier':'viridis-canon'}]}})
  identity=lambda body:prefix+hashlib.sha256(body).hexdigest()+':1'
  self.assertNotEqual(identity(old),identity(new));self.assertEqual(identity(new),identity(bytes(new)))

class SourceClosureTests(unittest.TestCase):
 def test_every_unchanged_function_body_matches_old_frozen_bytes(self):
  pins={'digest_metadata.py': {'MetadataHold': 'e34a195509b27b08c623db5bcb038322702447ca789ce4de8b2a7bf14754b767', 'exact': '0351084614c9374e244051f3dc40495343ce0c753ba29ae8584ed9ce32b0ae7e', 'check': 'e52fbd0f1fdf8c486ecd3afcc7aa20bc07d7a643a5066dccb2cb03d8cecb97c8', 'license_id': 'ec2019f10eb834b060fd9bca97e6fbda43d4775b820ab09edeab084b8338949e', 'closed_payload': 'a7c94fbf7e067b855c59e9d33074b4586d2a763e6ae404a607c71ddeb1b7ff97', 'creator_projection': '9cd120c9acee694bf5fd8f21d3a44b19405749a6863a503e8aea2949fe147ac5', 'native_metadata': '7ba0195ca7449c97fccff190ef27b916eb5c5847cc2993be3d4a5fbb0eca02c6'}, 'first_digest_state.py': {'identifier': 'e6ef932f7d2bb11feec8580483c30eb4f94fae5227334e2a073fb4b3682630ad', 'private_metadata_expected': '52444cad3b8db228746e7aa0b5e0b28dd29232afd8c5305f4297ab97e714d3ee', 'private_file_compare_rows': '51223230c359d14165f2f6053f4cf5ea75825bc0ccc89302ece40a3e8d1f1b9c', 'require_private_source': '384201ca1acfcd44c3f95f560273e52f3fd0fbb2f1ba0fcad0a7df22bd146b90', 'file_from_upload': 'a98cb91b793f47e2cdedfb7f3e888a751911a96e80efa5ecafa8581af06a691c', 'refresh_totals': '81bab633a4c3950542474e159cf693a42c3262eba32a8dc0463c80ebae13a967', 'public_projection': 'daea3779879e1c0cfa0ea348ca260bc9b088efcee16f0d5551e050b48c3f205e', 'public_legacy_projection': '9b166c4c2b6051fbc00c9ac7a4af3705c3011549b40bb567274a9b806e9bc82f', 'require_public_legacy': '40e5573fbdeb652028f75f4e54afd1436ded44a52f806d1e2be97e0221784731'}}
  for name,module in [('digest_metadata.py',m),('first_digest_state.py',state)]:
   text=Path(module.__file__).read_text();defs={n.name:ast.get_source_segment(text,n)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
   for key,digest in pins[name].items():self.assertEqual(hashlib.sha256(defs[key].encode()).hexdigest(),digest,(name,key))
 def test_exact_saved_613086_put_body_and_preserved_public_membership(self):
  fixture=json.loads((Path(__file__).parent/'COMMUNITY_613086_FIXTURE.json').read_bytes());rows=fixture['source_raw_json'];pins=fixture['original_source_pins']
  for key,raw in rows.items():self.assertEqual(hashlib.sha256(raw.encode()).hexdigest(),pins[key]['sha256'])
  request=json.loads(rows['mirror_reviewed_amendment_payload.json']);put=json.loads(rows['mirror-proof/012_PUT.json']);self.assertEqual(put['request_body_sha256'],pins['mirror_reviewed_amendment_payload.json']['sha256']);self.assertEqual(put['http_status'],200)
  before=json.loads(rows['mirror_before_public.json'])['metadata'];after=json.loads(rows['mirror_after_public.json'])['metadata'];public=state.community_public(request['metadata']['communities'])
  self.assertEqual(before['communities'],public);self.assertEqual(after['communities'],public)
  self.assertEqual({k:v for k,v in before.items()if k not in {'description','keywords'}},{k:v for k,v in after.items()if k not in {'description','keywords'}})
  native=json.loads(rows['mirror_after_native_public.json']);self.assertEqual(native['custom_fields'],{'legacy:communities':[v['id']for v in public]})
  proof=json.loads(rows['MIRROR_PROOF_RESULT.json']);self.assertTrue(proof['public_post_publish_exact_preservation']);self.assertTrue(all(proof['checks'].values()))
 def test_fixture_request_membership_tamper_is_not_equal(self):
  fixture=json.loads((Path(__file__).parent/'COMMUNITY_613086_FIXTURE.json').read_bytes());rows=fixture['source_raw_json'];request=json.loads(rows['mirror_reviewed_amendment_payload.json']);before=json.loads(rows['mirror_before_public.json'])['metadata'];request['metadata']['communities'][0]['identifier']='foreign'
  self.assertNotEqual(state.community_public(request['metadata']['communities']),before['communities'])

class ActivatedMetadataClosureTests(unittest.TestCase):
 def test_activated_metadata_stays_exact_original_flat_source(self):
  self.assertEqual(hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest(),'e5c5cd3b7ca80d9c31c4adcafacc9bd357e440965a25baed291c99f70a4781fe')
 def test_encoder_preserves_input_object_and_requires_closed_wrapper(self):
  public,source,*_=base.fixture();before=m.closed_payload(public,source);frozen=copy.deepcopy(before);encoded=state.encode_api_communities(before)
  self.assertEqual(before,frozen);self.assertEqual(before['metadata']['communities'],[{'id':'viridis-canon'}]);self.assertEqual(encoded['metadata']['communities'],[{'identifier':'viridis-canon'}])
  for bad in [None,{},[],{'metadata':[]},{'metadata':{},'extra':True}]:
   with self.assertRaises(m.MetadataHold):state.encode_api_communities(bad)
 def test_require_plan_really_uses_codec_without_source_change(self):
  f=coordinator.Fixture(seven=True)
  try:
   with patch.object(publisher,'require_module_pins',return_value=[]):prepared=publisher.require_plan(f.root,f.package,f.plan)
   self.assertEqual(prepared['api_payload']['metadata']['communities'],[{'identifier':'viridis-canon'}]);self.assertEqual(f.manifest['public_metadata']['communities'],[{'id':'viridis-canon'}])
  finally:f.close()
 def actual_closure(self):
  fixture=json.loads((Path(__file__).parent/'CLOSURE_CONSUMER_FIXTURE.json').read_bytes());parts=fixture['source_parts']
  for source,pin in zip(parts,fixture['source_part_pins'],strict=True):self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),pin)
  namespace={'Path':Path,'ast':ast,'hashlib':hashlib,'PIN_REQUIRED':set()};exec(compile('\n'.join(parts),'<exact-frozen-closure-consumer>','exec'),namespace);return namespace
 def run_duplicate_case(self,tamper):
  closure=self.actual_closure()
  with tempfile.TemporaryDirectory()as temp:
   root=Path(temp).resolve();flat=root/'activated-flat';helper=root/'new-helper';flat.mkdir();helper.mkdir();metadata=Path(m.__file__).read_bytes();(flat/'digest_metadata.py').write_bytes(metadata)
   for name in ['digest_metadata.py','first_digest_state.py','first_digest_publisher.py','readonly_account.py','mutation_journal_writer.py','publisher_previews.py','publisher_recovery.py']:(helper/name).write_bytes((Path(__file__).parent/name).read_bytes())
   if tamper:(helper/'digest_metadata.py').write_bytes(metadata+b'\n# unactivated replacement\n')
   return closure['collect_closure'](root,[helper/'first_digest_publisher.py',helper/'first_digest_state.py'],[flat,helper],required={'digest_metadata.py','first_digest_state.py','first_digest_publisher.py'})
 def test_actual_closure_duplicate_same_flat_metadata_passes(self):
  pins,edges,duplicates=self.run_duplicate_case(False);metadata=next(row for row in pins if row['name']=='digest_metadata.py');self.assertEqual(metadata['sha256'],'e5c5cd3b7ca80d9c31c4adcafacc9bd357e440965a25baed291c99f70a4781fe');self.assertIn('activated-flat',metadata['path']);self.assertIn('digest_metadata.py',duplicates)
 def test_actual_closure_duplicate_modified_metadata_must_fail(self):
  with self.assertRaisesRegex(ValueError,'CONFLICTING_OWN_MODULE:digest_metadata'):self.run_duplicate_case(True)

for direction,cases,method in [('public',BAD_PUBLIC,state.community_request),('request',BAD_REQUEST,state.community_public)]:
 for index,value in enumerate(cases):
  def case(self,value=value,method=method):
   with self.assertRaises(m.MetadataHold):method(value)
  setattr(CommunityAPITests,'test_bad_'+direction+'_'+str(index),case)

if __name__=='__main__':unittest.main()
