"""Isolated synthetic caller regressions; never scientific/publication admission.

The original fixture consumers assert immutable bytes. Every current registrar
call still executes those consumers, the actual registration structure and
actual parity checks. No fixture can authorize a live record or certificate.
"""
from pathlib import Path
from copy import deepcopy
import ast, hashlib, importlib, json, unittest
from unittest.mock import patch
import methods_digest as d
import methods_digest_registration as g
from test_fixtures.prior_processing_registration_old import Fixture, save

OLD_SHA='21b813c527566c12a06b15426c4a49370fd1e5ccbdcf9ca441bf5d305011d21c'
OLDER_SHA='0fc7393010cbc96d74b1fb6135cfb78cea88dd8ba692ba44c511242d5a89bdf9'

class PriorRegistrationFixtureTests(unittest.TestCase):
 def setUp(self):
  self.f=Fixture();self.addCleanup(self.f.close);self.r=self.f.prepare();self.b=save(self.f.root/'registration.json',self.r)
  self.saved=self.f.consume(self.f.root,self.b,self.f.ledger)
 def consume(self,views=None,**kw):return self.f.consume(self.f.root,self.b,self.f.ledger,views=views,**kw)
 def views(self):return deepcopy(self.saved['public_legacy']),deepcopy(self.saved['public_native'])
 def processing_views(self):
  legacy,native=self.views();native['ui']={'preview_status':'finished','observed':'actual fixture'};native['media_files']={'entries':{'preview.png':{'status':'finished'}}};native['revision_id']=999;native['updated']='2026-10-09T12:00:00Z';native['stats']={'downloads':101};legacy['revision']=999;legacy['updated']='2026-10-09T12:00:00Z';legacy['stats']={'downloads':101}
  return legacy,native
 def historical(self,sha):self.r['consumer_sha256']=sha;self.b=save(self.f.root/'registration.json',self.r)
 def test_current_saved_default_result_unmodified(self):
  result=self.consume();self.assertEqual(result,self.saved);self.assertNotIn('prior_processing_audit',result)
 def test_current_processing_views_pass_and_full_actual_observations_return(self):
  views=self.processing_views();result=self.consume(views)
  self.assertEqual(result['public_legacy'],views[0]);self.assertEqual(result['public_native'],views[1]);self.assertEqual(result['strict_readback'],self.saved['strict_readback']);self.assertEqual(result['receipt'],self.saved['receipt']);self.assertEqual(result['registered_public_views'],{'legacy':self.saved['public_legacy'],'native':self.saved['public_native']});self.assertEqual(result['prior_processing_audit']['route'],'UNCHANGED_PRIOR_CHAIN_IDENTITIES')
 def test_exact_old21_saved_default_source_dispatch(self):
  self.historical(OLD_SHA);result=self.consume();self.assertEqual(result['receipt']['consumer_sha256'],OLD_SHA)
 def test_exact_old0fc_saved_default_source_dispatch(self):
  self.historical(OLDER_SHA);result=self.consume();self.assertEqual(result['receipt']['consumer_sha256'],OLDER_SHA)
 def test_old21_processing_views_accepted_only_after_saved_default_admission(self):
  self.historical(OLD_SHA);original=importlib.import_module('methods_digest_registration_legacy_21b813');seen=[];call=original.require_registration
  def observed(*a,**kw):seen.append(kw['views']);return call(*a,**kw)
  with patch.object(original,'require_registration',side_effect=observed):result=self.consume(self.processing_views())
  self.assertEqual(seen,[None]);self.assertEqual(result['receipt']['consumer_sha256'],OLD_SHA)
 def test_old0fc_processing_views_accepted_only_after_saved_default_admission(self):
  self.historical(OLDER_SHA);original=importlib.import_module('methods_digest_registration_legacy_0fc739');seen=[];call=original.require_registration
  def observed(*a,**kw):seen.append(kw['views']);return call(*a,**kw)
  with patch.object(original,'require_registration',side_effect=observed):result=self.consume(self.processing_views())
  self.assertEqual(seen,[None]);self.assertEqual(result['receipt']['consumer_sha256'],OLDER_SHA)
 def test_saved_certificate_byte_change_not_rescued_by_processing(self):
  Path(self.f.notes[0]['certificate']['path']).write_bytes(b'changed');self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_saved_public_download_byte_change_not_rescued_by_processing(self):
  Path(self.f.downloads[0]['binding']['path']).write_bytes(b'changed');self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_saved_main_archive_byte_change_not_rescued_by_processing(self):
  (self.f.pkg/'METHODS_NOTES.zip').write_bytes(b'changed');self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_saved_binding_byte_change_not_rescued_by_processing(self):
  (self.f.pkg/'PUBLICATION_BINDING.json').write_bytes(b'{}');self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_saved_current_parity_failure_not_rescued_by_processing(self):
  run=self.f.runs[0];(self.f.generation/Path(run['path']).relative_to('science-engine')/'candidate.lean').write_bytes(b'changed');self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_saved_current_run_hold_not_rescued_by_processing(self):
  self.f.ledger['run_entities'][0]['status']='MIRROR_DRIFT';self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_missing_native_pid_hard_stop(self):
  legacy,native=self.processing_views();native['pids'].pop('doi');self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_changed_oai_pid_hard_stop(self):
  legacy,native=self.processing_views();native['pids']['oai']['identifier']='oai:zenodo.org:123456';self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_lost_oai_pid_hard_stop(self):
  legacy,native=self.processing_views();native['pids'].pop('oai');self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_foreign_parent_hard_stop(self):
  legacy,native=self.processing_views();native['parent']['id']='123456';self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_unknown_consumer_cannot_reuse_saved_evidence(self):
  self.historical('a'*64);self.assertRaises(ValueError,self.consume,self.processing_views())
 def test_bad_views_shapes_hard_stop(self):
  for value in ({},(),(self.saved['public_legacy'],),(None,None),(self.saved['public_legacy'],self.saved['public_native'],{})):
   with self.subTest(shape=str(type(value)),size=len(value)):self.assertRaises(ValueError,self.consume,value)
 def test_chain_claim_without_fresh_views_hard_stop(self):self.assertRaises(ValueError,self.consume,None,prior_chain_receipts={'creation':None,'publish':None})
 def test_chain_unlisted_key_hard_stop(self):self.assertRaises(ValueError,self.consume,self.views(),prior_chain_receipts={'creation':None,'publish':None,'fake_pass':True})
 def test_chain_raw_receipt_instead_of_bound_operation_hard_stop(self):self.assertRaises(ValueError,self.consume,self.views(),prior_chain_receipts={'creation':{'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE'},'publish':None})
 def test_chain_missing_bound_operation_hard_stop(self):self.assertRaises(Exception,self.consume,self.views(),prior_chain_receipts={'creation':{'path':str(self.f.root/'missing.json'),'sha256':'a'*64},'publish':None})
 def test_native_latest_flip_without_genuine_receipt_hard_stop(self):
  legacy,native=self.views();native['versions']['is_latest']=not native['versions']['is_latest'];self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_legacy_last_flip_without_genuine_receipt_hard_stop(self):
  legacy,native=self.views();legacy['metadata']['relations']['version'][0]['is_last']=not legacy['metadata']['relations']['version'][0]['is_last'];self.assertRaises(ValueError,self.consume,(legacy,native))
 def test_default_consumers_are_new_wrapper_not_captured_predecessor(self):
  for name in('entity_rows','preserve','augment_audit','public_label_read_record'):
   fn=getattr(g,name);self.assertIs(fn.__kwdefaults__['consume'],g.require_registration)
 def chain_bindings(self):
  rid=self.saved['public_native']['id'];parent=self.saved['public_native']['parent']['id'];child='999997'
  def operation(name,url,code,response):
   return save(self.f.root/name,{'environment':'zenodo.org','method':'POST','url':url,'http_status':code,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'response_sha256':d.digest(d.raw_json(response)),'response':response,'fixture_only':True})
  created=operation('synthetic_new_version.json','https://zenodo.org/api/deposit/depositions/'+rid+'/actions/newversion',201,{'id':int(child),'conceptrecid':parent})
  published=operation('synthetic_successor_publish.json','https://zenodo.org/api/deposit/depositions/'+child+'/actions/publish',200,{'id':int(child),'conceptrecid':parent,'doi':'10.5281/zenodo.'+child})
  return {'creation':created,'publish':published}
 def test_bound_creation_exact_allowed_flag_and_processing_pass(self):
  legacy,native=self.processing_views();native['versions']['is_latest_draft']=False;chain=self.chain_bindings();chain['publish']=None
  result=self.consume((legacy,native),prior_chain_receipts=chain);self.assertEqual(result['prior_processing_audit']['route'],'GENUINE_RECEIPT_BOUND_PRIOR_PAIR');self.assertEqual(result['public_native'],native)
 def test_bound_publish_exact_allowed_flags_and_processing_pass(self):
  legacy,native=self.processing_views();native['versions'].update(is_latest=False,is_latest_draft=False);legacy['metadata']['relations']['version'][0]['is_last']=False
  result=self.consume((legacy,native),prior_chain_receipts=self.chain_bindings());self.assertEqual(result['public_native'],native);self.assertEqual(result['public_legacy'],legacy)
 def test_bound_creation_does_not_allow_latest_publish_flag(self):
  legacy,native=self.processing_views();native['versions'].update(is_latest=False,is_latest_draft=False);chain=self.chain_bindings();chain['publish']=None;self.assertRaises(ValueError,self.consume,(legacy,native),prior_chain_receipts=chain)
 def test_bound_publish_requires_same_created_child(self):
  chain=self.chain_bindings();p=Path(chain['publish']['path']);v=json.loads(p.read_bytes());v['response']['id']=888887;chain['publish']=save(p,v);self.assertRaises(ValueError,self.consume,self.views(),prior_chain_receipts=chain)
 def test_bound_creation_requires_same_parent(self):
  chain=self.chain_bindings();p=Path(chain['creation']['path']);v=json.loads(p.read_bytes());v['response']['conceptrecid']='888888';chain['creation']=save(p,v);self.assertRaises(ValueError,self.consume,self.views(),prior_chain_receipts=chain)
 def test_bound_operation_bytes_are_rechecked_after_pair(self):
  import own_prior_record
  chain=self.chain_bindings();chain['publish']=None;legacy,native=self.views();native['versions']['is_latest_draft']=False;original=own_prior_record.require_pair
  def changed(*a,**kw):result=original(*a,**kw);Path(chain['creation']['path']).write_bytes(b'{}');return result
  with patch.object(own_prior_record,'require_pair',side_effect=changed):self.assertRaises(ValueError,self.consume,(legacy,native),prior_chain_receipts=chain)
 def public_row(self):
  rows=g.entity_rows(self.f.root,self.b,self.f.ledger,consume=self.f.consume);result=g.augment_audit(self.f.root,{**self.f.ledger,'publication_entities':rows},{'published_records':[],'counts':{}},consume=self.f.consume);return result['methods_digest_groups'][0]
 def test_public_label_ordinary_arbitrary_return_identity_preserved(self):
  row={'doi':'ordinary'};sentinel=object();calls=[]
  def legacy(value):calls.append(value);return sentinel
  def not_called(*a,**kw):raise AssertionError('ordinary row cannot call digest admission or getter')
  self.assertIs(g.public_label_read_record(row,legacy=legacy,getter=not_called,consume=not_called),sentinel);self.assertEqual(calls,[row])
 def test_public_label_ordinary_read_dict_return_identity_preserved(self):
  row={'doi':'ordinary'};result={'status':'READ','ordinary':'unchanged'};calls=[]
  def legacy(value):calls.append(value);return result
  def not_called(*a,**kw):raise AssertionError('ordinary row cannot call digest admission or getter')
  self.assertIs(g.public_label_read_record(row,legacy=legacy,getter=not_called,consume=not_called),result);self.assertEqual(calls,[row])
 def test_public_label_processing_audit_and_actual_pair_retained(self):
  views=self.processing_views();calls=[]
  def consume(*a,**kw):calls.append(deepcopy(kw.get('views')));return self.f.consume(*a,**kw)
  result=g.public_label_read_record(self.public_row(),legacy=lambda row:None,getter=lambda rid,accept:(deepcopy(views[1]if'inveniordm'in accept else views[0]),'a'*64),consume=consume)
  self.assertEqual(result['status'],'READ');self.assertEqual(calls,[None,views]);self.assertEqual(result['prior_processing_observations'],{'legacy':views[0],'native':views[1]});self.assertEqual(result['prior_processing_audit']['route'],'UNCHANGED_PRIOR_CHAIN_IDENTITIES')
 def test_public_label_metadata_mismatch_is_not_logged_as_success(self):
  views=self.processing_views();views[0]['metadata']['title']='changed'
  result=g.public_label_read_record(self.public_row(),legacy=lambda row:None,getter=lambda rid,accept:(deepcopy(views[1]if'inveniordm'in accept else views[0]),'a'*64),consume=self.f.consume)
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertNotIn('prior_processing_observations',result)
 def test_public_label_consumer_returned_observation_must_equal_real_view(self):
  views=self.processing_views()
  def changed(*a,**kw):
   result=self.f.consume(*a,**kw)
   if kw.get('views')is not None:result['public_native']['ui']={'different':'not actual'}
   return result
  result=g.public_label_read_record(self.public_row(),legacy=lambda row:None,getter=lambda rid,accept:(deepcopy(views[1]if'inveniordm'in accept else views[0]),'a'*64),consume=changed)
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertNotIn('prior_processing_observations',result)
 def test_public_label_missing_audit_cannot_report_checked_processing(self):
  views=self.processing_views()
  def missing(*a,**kw):
   result=self.f.consume(*a,**kw)
   if kw.get('views')is not None:result.pop('prior_processing_audit')
   return result
  result=g.public_label_read_record(self.public_row(),legacy=lambda row:None,getter=lambda rid,accept:(deepcopy(views[1]if'inveniordm'in accept else views[0]),'a'*64),consume=missing)
  self.assertEqual(result['status'],'UNAVAILABLE');self.assertNotIn('prior_processing_observations',result)
 def test_source_input_rechecked_after_semantics(self):
  import own_record_comparison as own
  actual=own.require_prior_semantics
  def changed(*a,**kw):result=actual(*a,**kw);Path(self.b['path']).write_bytes(b'{}');return result
  with patch.object(own,'require_prior_semantics',side_effect=changed):self.assertRaises(ValueError,self.consume,self.processing_views())

# Each independent controlled mutation remains a separate counted regression.
def native_metadata_change(field,value):
 def test(self):
  legacy,native=self.processing_views();native['metadata'][field]=deepcopy(value);self.assertRaises(ValueError,self.consume,(legacy,native))
 return test
for field,value in [('title','changed'),('description','stronger scientific claim'),('publication_date','2099-01-01'),('creators',[]),('subjects',[]),('rights',[]),('related_identifiers',[]),('resource_type',{'id':'other'})]:
 setattr(PriorRegistrationFixtureTests,'test_native_'+field+'_hard_stop',native_metadata_change(field,value))
def legacy_metadata_change(field,value):
 def test(self):
  legacy,native=self.processing_views();legacy['metadata'][field]=deepcopy(value);self.assertRaises(ValueError,self.consume,(legacy,native))
 return test
for field,value in [('title','changed'),('description','stronger scientific claim'),('publication_date','2099-01-01'),('creators',[]),('keywords',[]),('license',{'id':'other'}),('related_identifiers',[]),('communities',[]),('resource_type',{'type':'other'})]:
 setattr(PriorRegistrationFixtureTests,'test_legacy_'+field+'_hard_stop',legacy_metadata_change(field,value))
def file_change(kind):
 def test(self):
  legacy,native=self.processing_views();row=legacy['files'][0]
  if kind=='checksum':row['checksum']='md5:'+'a'*32
  elif kind=='size':row['size']+=1
  elif kind=='count':legacy['files'].pop()
  else:row['key']='different.pdf'
  self.assertRaises(ValueError,self.consume,(legacy,native))
 return test
for kind in ('checksum','size','count','name'):setattr(PriorRegistrationFixtureTests,'test_legacy_file_'+kind+'_hard_stop',file_change(kind))

class OriginalSourcePreservationTests(unittest.TestCase):
 def test_archived_exact21_and_cf74_sources(self):
  parent=Path(g.__file__).parent
  for name,sha in [('methods_digest_registration_legacy_21b813.py',OLD_SHA),('own_record_comparison_legacy_cf74da.py','cf74da23ea7208260cee70f74f282b2b57a209d1347f14d4c47b465f2b50ebd8')]:self.assertEqual(hashlib.sha256((parent/name).read_bytes()).hexdigest(),sha)
 def test_original_function_bodies_and_defaults_preserved(self):
  parent=Path(g.__file__).parent;old=ast.parse((parent/'methods_digest_registration_legacy_21b813.py').read_text());new=ast.parse((parent/'methods_digest_registration.py').read_text());mapping={n.name:n for n in new.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  for node in old.body:
   if not isinstance(node,(ast.FunctionDef,ast.ClassDef)):continue
   aliases={'require_registration':'_require_registration_pre_prior_processing','public_label_read_record':'_public_label_read_record_pre_prior_processing'}
   current=mapping[aliases.get(node.name,node.name)]
   current=deepcopy(current);current.name=node.name
   self.assertEqual(ast.dump(node,include_attributes=False),ast.dump(current,include_attributes=False),node.name)
 def test_wrapper_has_no_acceptance_or_after_body_normalizer(self):
  node=next(n for n in ast.parse(Path(g.__file__).read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='require_registration');text=ast.unparse(node)
  self.assertNotIn('audit_readback',text);self.assertNotIn('require_own_readback',text);self.assertIn('views=None',text);self.assertIn('require_prior_semantics',text);self.assertIn('_finish(snapshots)',text)

if __name__=='__main__':unittest.main()
