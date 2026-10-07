import unittest
from unittest.mock import patch
from pathlib import Path
from copy import deepcopy
import tempfile,json,html
import publication_binding as pb
import publication_gate as pg

class ScopedIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.art=self.root/'release';self.art.mkdir();(self.art/'SCOPED_RELEASE_MANIFEST.json').write_text('{}')
  self.cert=self.root/'cert.json';self.cert.write_text('{}');self.ins={'valid':True}
  self.current={'status':'PUBLICATION_BOUND','certificate':{'path':str(self.cert),'sha256':pb.sha(self.cert)},'uploads':[{'filename':'paper.pdf','sha256':'a'*64}],'foundation_basis':'INDEPENDENT','statement_scope':[{'lean_theorem':'conditional_target','nonvacuity_obligation':'witness','evidence_class':'FORMALLY_VERIFIED'}],'review':{'path':str(self.art/'review.json'),'sha256':'b'*64}}
  self.entity={'id':'publication:test','path':'release','run_id':'Run-188','certificate':'cert.json','certificate_valid':True,'status':'CERTIFIED','approved_publication_binding_reviews':['b'*64]}
  self.ledger={'tree_root':str(self.root),'publication_entities':[self.entity],'run_entities':[],'file_entities':[]}
  self.before_metadata={'title':'Exact original title','description':'Original historical description','abstract':'Original historical abstract','keywords':['historical'],'doi':'10.5281/zenodo.123456','license':{'id':'cc-by-4.0'},'relations':{'version':[{'is_last':True}]}}
  self.final_metadata=pg.scoped_metadata_proposal(self.before_metadata,self.current)
  self.meta=self.art/'zenodo_metadata.json';self.meta.write_text(json.dumps(self.final_metadata))
  self.metadata_binding={'filename':self.meta.name,'sha256':pb.sha(self.meta)}
  self.current['uploads'].append(self.metadata_binding);self.current['metadata_binding']=self.metadata_binding;self.current['metadata_claim_completeness']=True
 def test_adapter_calls_exact_scope_receipt(self):
  with patch('scoped_release.require_publication_bound',return_value=self.current)as consume:
   result=pb.validate_publication_binding(self.art,self.ins,self.cert,self.root,['b'*64]);self.assertEqual(result,[{'path':str(self.art/v['filename']),'sha256':v['sha256']}for v in self.current['uploads']]);consume.assert_called_once_with(self.art,self.root,['b'*64])
 def test_wrong_registered_certificate_holds(self):
  current=deepcopy(self.current);current['certificate']['sha256']='0'*64
  with patch('scoped_release.require_publication_bound',return_value=current):
   with self.assertRaises(ValueError):pb.validate_publication_binding(self.art,self.ins,self.cert,self.root,['b'*64])
 def test_scope_hold_not_status_diff_fallback(self):
  with patch('scoped_release.require_publication_bound',side_effect=ValueError('HOLD')):
   with self.assertRaises(ValueError):pb.validate_publication_binding(self.art,self.ins,self.cert,self.root,[])
 def test_publication_gate_uses_ssot_review_not_caller_flag(self):
  with patch('scoped_release.require_publication_bound',return_value=self.current)as consume,patch('publication_gate.inspect_entity_certificate',return_value=self.ins):
   r=pg.evaluate_publication(self.art,self.ledger,entity_id=self.entity['id'],enforce=True);self.assertEqual(r['status'],'PASS',r['reasons']);self.assertTrue(r['exact_publication_binding']);self.assertIn('conditional_target',r['label']);self.assertTrue(r['premise_declaration_required']);self.assertIn('mathematical',r['label']);self.assertEqual(consume.call_args.args[2],['b'*64]);pg.require_new_artifact_publication(r)
 def test_missing_review_blocks_prewrite(self):
  with patch('scoped_release.require_publication_bound',side_effect=ValueError('no approved independent review')),patch('publication_gate.inspect_entity_certificate',return_value=self.ins):
   r=pg.evaluate_publication(self.art,self.ledger,entity_id=self.entity['id'],enforce=True);self.assertEqual(r['status'],'HOLD');self.assertTrue(r['blocking'])
   with self.assertRaises(pg.PublicationGateHold):pg.require_new_artifact_publication(r)
 def test_scoped_gate_registered_certificate_mismatch_blocks(self):
  current=deepcopy(self.current);current['certificate']['sha256']='0'*64
  with patch('scoped_release.require_publication_bound',return_value=current),patch('publication_gate.inspect_entity_certificate',return_value=self.ins):
   r=pg.evaluate_publication(self.art,self.ledger,entity_id=self.entity['id'],enforce=True);self.assertEqual(r['status'],'HOLD')
 def test_report_only_does_not_authorize_write(self):
  with patch('scoped_release.require_publication_bound',return_value=self.current),patch('publication_gate.inspect_entity_certificate',return_value=self.ins):
   r=pg.evaluate_publication(self.art,self.ledger,entity_id=self.entity['id']);self.assertEqual(r['status'],'PASS')
   with self.assertRaises(pg.PublicationGateHold):pg.require_new_artifact_publication(r)
class ScopedMetadataIntegrationTests(ScopedIntegrationTests):
 def metadata(self,name='zenodo_metadata.json',bound=True,reviewed=True,canonical=True,original=None):
  p=self.art/name;before=original or {'title':'Exact original title','description':'This theorem empirically establishes an unrestricted vector conclusion.','abstract':'Broader empirical abstract','keywords':['vector','historical'],'doi':'10.5281/zenodo.123456','resource_type':{'type':'publication','subtype':'article'},'license':{'id':'cc-by-4.0'}}
  v=pg.scoped_metadata_proposal(before,self.current)if canonical else deepcopy(before);p.write_text(json.dumps(v));binding={'filename':name,'sha256':pb.sha(p)}
  self.current['uploads']=[u for u in self.current['uploads']if u['filename']not in {'metadata.json','zenodo_metadata.json'}]
  self.current.pop('metadata_binding',None)
  if bound:self.current['uploads'].append(binding);self.current['metadata_binding']=binding
  self.current['metadata_claim_completeness']=reviewed
  return p,v,before
 def rebind(self,p):
  binding={'filename':p.name,'sha256':pb.sha(p)};self.current['metadata_binding']=binding;self.current['uploads']=[u for u in self.current['uploads']if u['filename']not in {'metadata.json','zenodo_metadata.json'}]+[binding]
 def mutate(self,fn):
  p,v,_=self.metadata();fn(v);p.write_text(json.dumps(v));self.rebind(p);return self.evaluate()
 def evaluate(self):
  with patch('scoped_release.require_publication_bound',return_value=self.current),patch('publication_gate.inspect_entity_certificate',return_value=self.ins):return pg.evaluate_publication(self.art,self.ledger,entity_id=self.entity['id'],enforce=True)
 def test_final_bound_reviewed_metadata_pass_is_pure_and_qualifies_all_history(self):
  p,v,original=self.metadata();before_bytes=p.read_bytes();r=self.evaluate();self.assertEqual(r['status'],'PASS',r['reasons']);after=r['proposed_metadata'];self.assertEqual(after['title'],original['title']);neutral,history=after['description'].split('Historical metadata — UNCERTIFIED provenance:',1)
  self.assertNotIn(original['description'],neutral);self.assertNotIn(original['abstract'],neutral);self.assertIn(original['description'],history);self.assertIn(original['abstract'],history);self.assertIn(original['title'],history);self.assertIn('historical',history);self.assertIn('logical validity given the model, not empirical validation of its assumptions',neutral);self.assertIn('Foundation basis: INDEPENDENT',neutral)
  self.assertEqual(len(r['claim_gate']['unverified_claims']),1);self.assertEqual(r['claim_gate']['unverified_claims'][0]['metadata_fields'],{k:original[k]for k in('title','description','abstract','keywords')});self.assertEqual(after['historical_metadata_verification_status'],'UNCERTIFIED_PROVENANCE_NOT_CERTIFIED_SCOPE')
  self.assertEqual(r['public_metadata'],v);self.assertTrue(r['public_metadata_unchanged']);self.assertEqual(p.read_bytes(),before_bytes)
  for key,value in v.items():self.assertEqual(after[key],value)
  bookkeeping={'verification_status','verification_banner','verification_scope','unverified_claims','model_validity_disclaimer','historical_metadata_verification_status'};self.assertEqual(set(after)-set(v),bookkeeping)
 def test_repeat_pass_is_byte_identical_and_does_not_nest_history(self):
  p,v,_=self.metadata();before=p.read_bytes();first=self.evaluate();second=self.evaluate();self.assertEqual(first['status'],'PASS');self.assertEqual(second,first);self.assertEqual(first['proposed_metadata']['description'],v['description']);self.assertEqual(first['proposed_metadata']['abstract'],v['abstract']);self.assertEqual(p.read_bytes(),before);self.assertEqual(v['description'].count(pg.SCOPED_HISTORICAL_SEPARATOR),1)
 def test_report_only_proposal_constructor_is_idempotent_and_preserves_original(self):
  original=deepcopy(self.before_metadata);once=pg.scoped_metadata_proposal(original,self.current);twice=pg.scoped_metadata_proposal(once,self.current);self.assertEqual(once,twice);self.assertEqual(original,self.before_metadata);self.assertEqual(once['title'],original['title']);self.assertEqual(once['keywords'],original['keywords']);self.assertNotIn('status',once);self.assertEqual(set(once),set(original))
 def test_added_unbound_metadata_holds(self):self.metadata(bound=False);self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_broader_unreviewed_metadata_holds(self):self.metadata(reviewed=False,canonical=False);self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_broader_metadata_holds_even_with_review_boolean_true(self):self.metadata(reviewed=True,canonical=False);self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_missing_final_metadata_holds(self):self.meta.unlink();self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_metadata_hash_changed_holds(self):p,_,_=self.metadata();p.write_bytes(p.read_bytes()+b' ');self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_both_metadata_names_holds(self):self.metadata();self.metadata('metadata.json');self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_metadata_binding_must_be_in_exact_uploads(self):
  self.metadata();self.current['uploads']=[v for v in self.current['uploads']if v['filename']!='zenodo_metadata.json'];self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_metadata_binding_wrong_name_holds(self):self.metadata();self.current['metadata_binding']['filename']='other.json';self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_metadata_symlink_holds(self):p,_,_=self.metadata();p.unlink();p.symlink_to(self.cert);self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_html_in_history_is_escaped_and_cannot_escape_region(self):
  original=deepcopy(self.before_metadata);original['description']='</pre><h1>Unqualified certified vector claim</h1>';p,v,_=self.metadata(original=original);r=self.evaluate();self.assertEqual(r['status'],'PASS');self.assertNotIn(original['description'],r['proposed_metadata']['description']);self.assertIn('&lt;/pre&gt;&lt;h1&gt;',r['proposed_metadata']['description'])
 def test_any_text_before_neutral_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description='Scientific claim'+v['description']))['status'],'HOLD')
 def test_any_text_between_neutral_and_history_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace(pg.SCOPED_HISTORICAL_SEPARATOR,'Scientific claim'+pg.SCOPED_HISTORICAL_SEPARATOR,1)))['status'],'HOLD')
 def test_any_text_between_neutral_paragraphs_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace('</strong></p><p>','</strong></p>Scientific claim<p>',1)))['status'],'HOLD')
 def test_any_text_after_history_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description']+'Scientific claim'))['status'],'HOLD')
 def test_html_injection_before_archive_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace(pg.SCOPED_HISTORICAL_SEPARATOR,'<h1>Certified empirical conclusion</h1>'+pg.SCOPED_HISTORICAL_SEPARATOR,1)))['status'],'HOLD')
 def test_one_character_change_to_affirmative_scope_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace('conditional_target','conditional_targetX',1)))['status'],'HOLD')
 def test_abstract_must_equal_closed_description(self):self.assertEqual(self.mutate(lambda v:v.update(abstract='Stronger empirical abstract'))['status'],'HOLD')
 def test_edited_final_title_holds_even_with_fresh_hash_stub(self):self.assertEqual(self.mutate(lambda v:v.update(title='Edited title'))['status'],'HOLD')
 def test_missing_final_title_holds(self):self.assertEqual(self.mutate(lambda v:v.pop('title'))['status'],'HOLD')
 def test_empty_final_title_holds(self):self.assertEqual(self.mutate(lambda v:v.update(title=''))['status'],'HOLD')
 def test_historical_title_mismatch_holds(self):
  self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace('Exact original title','Edited archival title',1)))['status'],'HOLD')
 def test_historical_keywords_mismatch_holds(self):self.assertEqual(self.mutate(lambda v:v.update(keywords=['different']))['status'],'HOLD')
 def test_removed_historical_separator_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=v['description'].replace(pg.SCOPED_HISTORICAL_SEPARATOR,'')))['status'],'HOLD')
 def test_duplicate_wrapper_holds(self):self.assertEqual(self.mutate(lambda v:v.update(description=pg._scoped_metadata_prefix(self.current)+v['description']))['status'],'HOLD')
 def test_noncanonical_unescaped_json_archive_holds(self):
  original=deepcopy(self.before_metadata);original['description']='<h1>Old claim</h1>';p,v,_=self.metadata(original=original);v['description']=v['description'].replace('&lt;','<',1);p.write_text(json.dumps(v));self.rebind(p);self.assertEqual(self.evaluate()['status'],'HOLD')
 def test_unknown_archived_claim_field_holds(self):
  p,v,_=self.metadata();head,encoded=v['description'].split(pg.SCOPED_HISTORICAL_SEPARATOR);historical=json.loads(html.unescape(encoded[:-6]));historical['unclassified_scientific_claim']='new claim';v['description']=head+pg.SCOPED_HISTORICAL_SEPARATOR+pg._encode_scoped_history(historical)+'</pre>';p.write_text(json.dumps(v));self.rebind(p);self.assertEqual(self.evaluate()['status'],'HOLD')


class ScopedRegistrationTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.art=self.root/'release';self.art.mkdir()
  self.ledger={'tree_root':str(self.root)}
  self.entity={'id':'publication:scoped','path':'release','status':'CERTIFIED','certificate_valid':True,'publication_binding_status':'PUBLICATION_BOUND'}
 def test_manifest_without_legacy_map_reaches_fresh_scope_consumer(self):
  import corpus_ledger as cl
  (self.art/'SCOPED_RELEASE_MANIFEST.json').write_text('{}')
  with patch('publication_gate.evaluate_publication',return_value={'status':'PASS','exact_publication_binding':True,'reasons':[]})as gate:
   cl._publication_registration_status(self.ledger,self.entity);gate.assert_called_once();self.assertEqual(self.entity['publication_registration_status'],'PASS');self.assertTrue(self.entity['enforcement_acceptable'])
 def test_held_scope_does_not_inherit_certificate_approval(self):
  import corpus_ledger as cl
  (self.art/'SCOPED_RELEASE_MANIFEST.json').write_text('{}')
  with patch('publication_gate.evaluate_publication',return_value={'status':'HOLD','exact_publication_binding':False,'reasons':['no reviewed binding']}):
   cl._publication_registration_status(self.ledger,self.entity);self.assertEqual(self.entity['publication_registration_status'],'HOLD');self.assertFalse(self.entity['enforcement_acceptable'])
 def test_no_map_or_manifest_remains_banner_only_hold(self):
  import corpus_ledger as cl
  with patch.object(cl,'validate_uncertified_readback',return_value={'status':'PUBLIC_UNCERTIFIED_BANNER_READBACK_PASS'}),patch('publication_gate.evaluate_publication')as gate:
   cl._publication_registration_status(self.ledger,self.entity);gate.assert_not_called();self.assertEqual(self.entity['publication_registration_status'],'HOLD_NO_CLAIM_MAP');self.assertTrue(self.entity['enforcement_acceptable'])

if __name__=='__main__':unittest.main()
