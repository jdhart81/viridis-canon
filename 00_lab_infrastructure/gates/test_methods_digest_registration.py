"""Synthetic preservation/readback tests; no publication or genuine cert approval."""
from pathlib import Path
from copy import deepcopy
import json,tempfile,unittest,types,hashlib
from unittest.mock import patch
import methods_digest as d
import methods_digest_registration as g
import digest_metadata

def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(d.raw_json(obj));return {'path':str(p),'sha256':d.sha(p)}
def receipt(p,method,url,response,accept='application/json'):
 return save(p,{'environment':'zenodo.org','method':method,'url':url,'http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':d.digest(d.raw_json(response)),'request_body_sha256':None if method=='GET'else d.digest(b'{}'),'response':response,'accept':accept})

class Fixture:
 def __init__(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name).resolve();self.pkg=self.root/'digest';self.pkg.mkdir();self.rid='999999';self.doi='10.5281/zenodo.'+self.rid;self.notes=[];self.runs=[]
  for n in(125,126):
   run=f'Run-{n:03d}';p=self.root/run;p.mkdir();cert=save(p/'certificate.json',{'run_id':run,'synthetic':True});pb=save(p/'PUBLICATION_BINDING.json',{'synthetic':True});self.notes.append({'run_id':run,'path':str(p),'certificate':cert,'publication_binding':pb});self.runs.append({'id':run,'path':'science-engine/07_nightly_engine/compound research papers/'+run,'status':'CERTIFIED','certificate_valid':True,'certificate':str(Path(cert['path']).relative_to(self.root))})
  self.source={'creators':[{'name':'Hart, Justin D.','affiliation':'Viridis LLC','orcid':'0009-0008-3082-2482'}],'license':{'id':'cc-by-4.0'},'access_right':'open','communities':[{'id':'viridis-canon'}],'language':'eng','resource_type':{'type':'publication','subtype':'preprint','title':'Preprint'}};self.public={**deepcopy(self.source),'title':'Viridis Methods Digest — 2026-W41','description':'<p>Approved exact scope</p>','publication_date':'2026-10-07','keywords':['Methods Digest'],'related_identifiers':[{'identifier':'10.5281/zenodo.21971052','relation':'isSupplementTo','scheme':'doi'}]}
  old={'id':21971052,'doi':'10.5281/zenodo.21971052','metadata':deepcopy(self.source)};native={'id':'21971052','pids':{'doi':{'identifier':old['doi']}},'access':{'record':'public','files':'public','status':'open','embargo':{'active':False,'reason':None}},'metadata':{'creators':[{'affiliations':[{'name':'Viridis LLC'}],'person_or_org':{'family_name':'Hart','given_name':'Justin D.','name':'Hart, Justin D.','type':'personal','identifiers':[{'identifier':'0009-0008-3082-2482','scheme':'orcid'}]}}],'rights':[{'id':'cc-by-4.0','title':{'en':'CC BY 4.0'}}],'resource_type':{'id':'publication-preprint','title':{'en':'Preprint'}},'languages':[{'id':'eng','title':{'en':'English'}}],'publisher':'Zenodo'}};template={'id':'issupplementto','title':{'en':'Is supplement to','de':'Ergänzt'}}
  self.expected_native={'id':self.rid,'is_published':True,'custom_fields':{},'metadata':digest_metadata.native_metadata(self.public,self.source,old,native,template),'pids':{'doi':{'identifier':self.doi},'oai':{'identifier':'oai:zenodo.org:'+self.rid,'provider':'oai'}}}
  self.legacy={'id':int(self.rid),'doi':self.doi,'state':'done','submitted':True,'metadata':deepcopy(self.public),'files':[]}
  members=[('notes/test.txt',b'Explicit synthetic archive')];self.uploads=[]
  for name,raw in(('paper.tex',b'Exact synthetic scope wrapper'),('paper.pdf',b'%PDF-SYNTHETIC'),('metadata.json',d.raw_json(self.public)),('METHODS_NOTES.zip',d.archive_bytes(members))):
   p=self.pkg/name;p.write_bytes(raw);self.uploads.append({'filename':name,'sha256':d.sha(p),'md5':hashlib.md5(raw).hexdigest(),'bytes':len(raw)})
  self.manifest={'standard':d.STANDARD,'release_week':'2026-W41','source_metadata':save(self.root/'source.json',self.source),'public_metadata':self.public,'notes':self.notes,'archive_members':d.member_inventory(members),'authority':save(self.root/'authority.json',{'synthetic':True}),'uploads':self.uploads}
  save(self.pkg/'DIGEST_MANIFEST.json',self.manifest);self.pb={'standard':d.BINDING_STANDARD,'synthetic':True};save(self.pkg/'PUBLICATION_BINDING.json',self.pb)
  self.downloads=[]
  for name in('paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'):
   raw=d.read_regular(self.pkg/name);url='https://zenodo.org/api/records/'+self.rid+'/files/'+name+'/content';p=self.root/'downloads'/name;p.parent.mkdir(exist_ok=True);p.write_bytes(raw);self.downloads.append({'filename':name,'binding':{'path':str(p),'sha256':d.sha(p)},'url':url});self.legacy['files'].append({'key':name,'checksum':'md5:'+hashlib.md5(raw).hexdigest(),'size':len(raw),'links':{'self':url}})
  self.e={'standard':g.EVIDENCE_STANDARD,'status':'SOURCE_BOUND_READBACK_INPUTS','record_id':self.rid,'doi':self.doi,'public_legacy_receipt':receipt(self.root/'public_legacy.json','GET','https://zenodo.org/api/records/'+self.rid,self.legacy),'public_native_receipt':receipt(self.root/'public_native.json','GET','https://zenodo.org/api/records/'+self.rid,self.expected_native,'application/vnd.inveniordm.v1+json'),'own_publish_receipt':receipt(self.root/'publish.json','POST','https://zenodo.org/api/deposit/depositions/'+self.rid+'/actions/publish',self.legacy),'expected_legacy':save(self.root/'expected_legacy.json',self.legacy),'expected_native':save(self.root/'expected_native.json',self.expected_native),'source_legacy_receipt':receipt(self.root/'source_legacy.json','GET','https://zenodo.org/api/records/21971052',old),'source_native_receipt':receipt(self.root/'source_native.json','GET','https://zenodo.org/api/records/21971052',native,'application/vnd.inveniordm.v1+json'),'relation_template':save(self.root/'relation.json',template),'server_context':save(self.root/'context.json',{'operation':'NEW_VERSION','phase':'PUBLISHED'}),'downloads':self.downloads,'strict_readback_result':save(self.root/'strict.json',{'status':'STRICT_OWN_PUBLIC_READBACK_PASS','record_id':self.rid,'doi':self.doi,'files':6,'notes':['Run-125','Run-126'],'binding_sha256':d.sha(self.pkg/'PUBLICATION_BINDING.json'),'certifies':False})}
  self.e_binding=save(self.root/'evidence.json',self.e);self.originals={str(p):d.sha(p)for p in self.root.rglob('*')if p.is_file()and p.is_relative_to(self.pkg)or p.is_file()and p.name=='certificate.json'}
  self.ledger={'tree_root':str(self.root),'run_entities':self.runs,'file_entities':[],'publication_entities':[]}
  save(self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json',self.ledger)
  self.generation=self.root/'generation'
  for run in self.runs:
   mirror=self.root/run['path'];source=self.generation/Path(run['path']).relative_to('science-engine');mirror.mkdir(parents=True);source.mkdir(parents=True);(source/'candidate.lean').write_bytes(b'Exact synthetic parity-only source');(mirror/'candidate.lean').write_bytes(b'Exact synthetic parity-only source')
 def parity(self,root,path):
  from mirror_parity import run_parity
  return run_parity(root,path,generation_root=self.generation)
 def close(self):self.t.cleanup()
 def digest(self,package,root,**kwargs):
  for p,h in self.originals.items():
   if d.sha(p)!=h:raise ValueError('changed bound input')
  return deepcopy(self.manifest),deepcopy(self.pb)
 def audit(self,actual,expected,**kwargs):return {'status':'PASS'if actual==expected else'HOLD','reasons':['synthetic full readback differs']if actual!=expected else[]}
 def prepare(self):
  with patch.object(d,'require_publication_bound',side_effect=self.digest):return g.prepare_registration(self.root,self.pkg,self.e_binding,digest_consumer=self.digest,audit_consumer=self.audit,issued_at_utc='2026-10-07T12:00:00Z')
 def consume(self,root,binding,ledger=None,**kwargs):
  with patch.object(d,'require_publication_bound',side_effect=self.digest):return g.require_registration(root,binding,ledger,digest_consumer=self.digest,audit_consumer=self.audit,parity_consumer=self.parity,**kwargs)

class RegistrationTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.addCleanup(self.f.close);self.receipt=self.f.prepare();self.binding=save(self.f.root/'registration.json',self.receipt)
 def call(self):return self.f.consume(self.f.root,self.binding,self.f.ledger)
 def change(self,key,value):self.receipt[key]=value;self.binding=save(self.f.root/'registration.json',self.receipt)
 def evidence(self):self.f.e_binding=save(self.f.root/'evidence.json',self.f.e);self.change('public_evidence',self.f.e_binding)
 def test_exact_own_public_digest_pass_is_not_whole_certificate(self):v=self.call();self.assertFalse(v['receipt']['certifies']);self.assertEqual(len(v['receipt']['children']),2)
 def test_periodic_route_loads_actual_ssot_when_no_ledger_supplied(self):self.assertEqual(len(self.f.consume(self.f.root,self.binding)['receipt']['children']),2)
 def test_periodic_missing_current_ssot_holds(self):(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json').unlink();self.assertRaises(Exception,lambda:self.f.consume(self.f.root,self.binding))
 def test_periodic_wrong_tree_ssot_holds(self):v=deepcopy(self.f.ledger);v['tree_root']=str(self.f.root.parent);save(self.f.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json',v);self.assertRaises(ValueError,lambda:self.f.consume(self.f.root,self.binding))
 def test_fresh_parity_catches_stale_certified_ledger_source_byte_divergence(self):
  source=self.f.generation/Path(self.f.runs[0]['path']).relative_to('science-engine')/'candidate.lean';source.write_bytes(source.read_bytes()+b'x');self.assertEqual(self.f.ledger['run_entities'][0]['status'],'CERTIFIED');self.assertRaises(ValueError,self.call)
 def test_default_unchanged_parity_consumer_is_called_again_before_return(self):
  from mirror_parity import run_parity
  real_parity=run_parity
  with patch.object(d,'require_publication_bound',side_effect=self.f.digest),patch('mirror_parity.run_parity',side_effect=lambda root,path:real_parity(root,path,generation_root=self.f.generation))as parity:
   result=g.require_registration(self.f.root,self.binding,digest_consumer=self.f.digest,audit_consumer=self.f.audit);self.assertEqual(len(result['receipt']['children']),2);self.assertEqual(parity.call_count,4)
 def test_parity_inventory_race_holds(self):
  count=0
  def changing(root,path):
   nonlocal count
   result=self.f.parity(root,path);count+=1
   if count==3:result['source_hashes']['injected.lean']='a'*64
   return result
  with patch.object(d,'require_publication_bound',side_effect=self.f.digest):self.assertRaises(ValueError,lambda:g.require_registration(self.f.root,self.binding,self.f.ledger,digest_consumer=self.f.digest,audit_consumer=self.f.audit,parity_consumer=changing))
 def test_same_doi_distinct_notes_one_main_certificate_each(self):rows=g.entity_rows(self.f.root,self.binding,self.f.ledger,consume=self.f.consume);self.assertEqual(len(rows),3);self.assertEqual(len({r['id']for r in rows}),3);self.assertEqual(len({r['doi']for r in rows}),1);self.assertFalse(rows[0]['certificate_valid']);self.assertNotIn('certificate',rows[0]);self.assertEqual([r['run_id']for r in rows[1:]],['Run-125','Run-126'])
 def test_future_registration_hold(self):self.change('issued_at_utc','2099-01-01T00:00:00Z');self.assertRaises(ValueError,self.call)
 def test_self_reviewer_field_hold(self):self.change('reviewer',{'approved':True});self.assertRaises(ValueError,self.call)
 def test_unknown_consumer_hold(self):self.change('consumer_sha256','a'*64);self.assertRaises(ValueError,self.call)
 def test_wrong_doi_hold(self):self.change('doi','10.5281/zenodo.888888');self.assertRaises(ValueError,self.call)
 def test_wrong_note_certificate_hold(self):self.receipt['children'][0]['certificate']=self.receipt['children'][1]['certificate'];self.binding=save(self.f.root/'registration.json',self.receipt);self.assertRaises(ValueError,self.call)
 def test_wrong_note_artifact_hold(self):self.receipt['children'][0]['path']=self.receipt['children'][1]['path'];self.binding=save(self.f.root/'registration.json',self.receipt);self.assertRaises(ValueError,self.call)
 def test_mirror_drift_is_not_bypassed_by_public_digest(self):self.f.ledger['run_entities'][0]['status']='MIRROR_DRIFT';self.assertRaises(ValueError,self.call)
 def test_current_certificate_switch_hold(self):self.f.ledger['run_entities'][0]['certificate']=self.f.ledger['run_entities'][1]['certificate'];self.assertRaises(ValueError,self.call)
 def test_main_file_one_byte_hold(self):(self.f.pkg/'paper.pdf').write_bytes(b'%PDF-CHANGED');self.assertRaises(ValueError,self.call)
 def test_main_archive_one_byte_hold(self):(self.f.pkg/'METHODS_NOTES.zip').write_bytes(b'changed archive');self.assertRaises(ValueError,self.call)
 def test_note_certificate_one_byte_hold(self):Path(self.f.notes[0]['certificate']['path']).write_bytes(b'{}');self.assertRaises(ValueError,self.call)
 def test_metadata_one_byte_hold(self):(self.f.pkg/'metadata.json').write_bytes(b'{}');self.assertRaises(ValueError,self.call)
 def test_missing_public_binding_hold(self):(self.f.pkg/'PUBLICATION_BINDING.json').unlink();self.assertRaises(Exception,self.call)
 def test_missing_own_public_download_hold(self):Path(self.f.downloads[0]['binding']['path']).unlink();self.assertRaises(Exception,self.call)
 def test_foreign_public_get_cannot_clear(self):r=json.loads(Path(self.f.e['public_native_receipt']['path']).read_bytes());r['url']='https://zenodo.org/api/records/888888';self.f.e['public_native_receipt']=save(Path(self.f.e['public_native_receipt']['path']),r);self.evidence();self.assertRaises(ValueError,self.call)
 def test_public_oai_pid_loss_is_hold(self):new=deepcopy(self.f.expected_native);new['pids'].pop('oai');self.assertRaises(ValueError,lambda:self.f.consume(self.f.root,self.binding,views=(self.f.legacy,new)))
 def test_public_native_claim_metadata_change_hold(self):new=deepcopy(self.f.expected_native);new['metadata']['description']+='Unconditional stronger claim';self.assertRaises(ValueError,lambda:self.f.consume(self.f.root,self.binding,views=(self.f.legacy,new)))
 def test_public_legacy_title_change_hold(self):new=deepcopy(self.f.legacy);new['metadata']['title']='Changed';self.assertRaises(Exception,lambda:self.f.consume(self.f.root,self.binding,views=(new,self.f.expected_native)))
 def test_public_main_checksum_change_hold(self):new=deepcopy(self.f.legacy);new['files'][0]['checksum']='md5:'+'a'*32;self.assertRaises(Exception,lambda:self.f.consume(self.f.root,self.binding,views=(new,self.f.expected_native)))
 def test_extra_download_hold(self):self.f.e['downloads'].append(self.f.e['downloads'][0]);self.evidence();self.assertRaises(ValueError,self.call)
 def test_unlisted_server_context_field_hold(self):self.f.e['server_context']=save(self.f.root/'context.json',{'operation':'NEW_VERSION','phase':'PUBLISHED','force_pass':True});self.evidence();self.assertRaises(ValueError,self.call)
 def test_source_preserved_rights_mismatch_hold(self):new=deepcopy(self.f.expected_native);new['metadata']['rights'][0]['id']='wrong';self.f.e['expected_native']=save(self.f.root/'expected_native.json',new);self.evidence();self.assertRaises(ValueError,self.call)

class PreservationTests(unittest.TestCase):
 setUp=RegistrationTests.setUp
 def rows(self):return g.entity_rows(self.f.root,self.binding,self.f.ledger,consume=self.f.consume)
 def legacy(self,ledger,previous):
  ledger=deepcopy(ledger);ledger['publication_entities']=deepcopy(previous['publication_entities']);ledger['publication_holds']=[];ledger['publication_registration_summary']={};return ledger
 def preserve(self,rows):return g.preserve(deepcopy(self.f.ledger),{**self.f.ledger,'publication_entities':rows},legacy=self.legacy,consume=self.f.consume)
 def test_old27_plus_digest_notes_survive_fresh_scan(self):
  old=[{'id':'legacy-'+str(i),'path':'legacy/'+str(i),'status':'CERTIFIED','publication_registration_status':'PASS'if i<2 else'HOLD_NO_CLAIM_MAP','enforcement_acceptable':True}for i in range(27)];rows=self.rows();out=self.preserve(old+rows);self.assertEqual(len(out['publication_entities']),30);self.assertEqual(out['publication_entities'][:27],old);self.assertTrue(out['publication_registration_enforcement_acceptable']);self.assertEqual(self.preserve(out['publication_entities'])['publication_entities'],out['publication_entities'])
 def test_missing_child_held_not_disappeared(self):rows=self.rows();out=self.preserve(rows[:-1]);self.assertEqual(len(out['publication_entities']),2);self.assertTrue(all(v['publication_registration_status']=='HOLD'for v in out['publication_entities']))
 def test_changed_child_identity_is_visible_hold(self):rows=self.rows();rows[1]['certificate_sha256']='a'*64;out=self.preserve(rows);self.assertTrue(all(v['publication_registration_status']=='HOLD'for v in out['publication_entities']))
 def test_orphaned_child_hard_hold(self):self.assertRaises(ValueError,self.preserve,self.rows()[1:])
 def test_duplicate_group_hard_hold(self):rows=self.rows();self.assertRaises(ValueError,self.preserve,rows+[rows[0]])
 def test_held_registration_does_not_auto_upgrade(self):rows=self.rows();rows[0]['enforcement_acceptable']=False;out=self.preserve(rows);self.assertFalse(out['publication_registration_enforcement_acceptable'])
 def test_ordinary_only_delegates_exact_existing_consumer(self):called=[];old={'publication_entities':[{'id':'ordinary'}]};result=g.preserve(self.f.ledger,old,legacy=lambda l,p:called.append(p)or l);self.assertEqual(called,[old]);self.assertIs(result,self.f.ledger)
 def test_periodic_scan_single_group_has_no_unexplained_label_mismatch(self):
  rows=self.rows();ledger={**self.f.ledger,'publication_entities':rows};out=g.augment_audit(self.f.root,ledger,{'published_records':[],'counts':{}},consume=self.f.consume);self.assertEqual(out['published_records'],[]);self.assertEqual(len(out['methods_digest_groups']),1);row=out['methods_digest_groups'][0]
  def getter(rid,accept):return (deepcopy(self.f.expected_native)if 'inveniordm'in accept else deepcopy(self.f.legacy),'a'*64)
  result=g.public_label_read_record(row,legacy=lambda x:None,getter=getter,consume=self.f.consume);self.assertEqual(result['status'],'READ');self.assertFalse(result['proposed_label_disagrees']);self.assertEqual(result['public_verification_status'],'SCOPED_DIGEST')
 def test_periodic_scan_native_pid_loss_is_disagreement(self):
  rows=self.rows();out=g.augment_audit(self.f.root,{**self.f.ledger,'publication_entities':rows},{'published_records':[],'counts':{}},consume=self.f.consume);bad=deepcopy(self.f.expected_native);bad['pids'].pop('oai');result=g.public_label_read_record(out['methods_digest_groups'][0],legacy=lambda x:None,getter=lambda rid,accept:(bad if 'inveniordm'in accept else self.f.legacy,'a'*64),consume=self.f.consume);self.assertTrue(result['proposed_label_disagrees']);self.assertEqual(result['status'],'UNAVAILABLE')
 def test_generic_doi_collision_hard_hold(self):rows=self.rows();self.assertRaises(ValueError,g.augment_audit,self.f.root,{**self.f.ledger,'publication_entities':rows},{'published_records':[{'doi':self.f.doi}],'counts':{}},consume=self.f.consume)
 def test_public_scan_appends_group_without_changing_legacy_shape(self):
  row={'doi':self.f.doi};self.assertEqual(g.public_label_readback({'published_records':[{'doi':'old'}],'methods_digest_groups':[row]},legacy=lambda a:a)['published_records'],[{'doi':'old'},row])
 def test_generic_and_group_same_doi_ambiguous_holds(self):self.assertRaises(ValueError,g.public_label_readback,{'published_records':[{'doi':'same'}],'methods_digest_groups':[{'doi':'same'}]},legacy=lambda a:a)

if __name__=='__main__':unittest.main()

class AdapterAndExistingCommunityTests(unittest.TestCase):
 def setUp(self):self.f=Fixture();self.addCleanup(self.f.close)
 def args(self):return {k:deepcopy(self.f.e[k])for k in g.EVIDENCE_FIELDS-{'standard','status','doi'}}
 def test_adapter_emits_exact_closed_evidence_fields(self):self.assertEqual(g.assemble_evidence(**self.args()),self.f.e)
 def test_adapter_extra_binding_field_rejected(self):v=self.args();v['public_native_receipt']['certified']=True;self.assertRaises(ValueError,g.assemble_evidence,**v)
 def test_adapter_unbound_download_rejected(self):v=self.args();v['downloads'][0]['binding']['sha256']='invalid';self.assertRaises(ValueError,g.assemble_evidence,**v)
 def test_adapter_duplicate_download_rejected(self):v=self.args();v['downloads'][1]=deepcopy(v['downloads'][0]);self.assertRaises(ValueError,g.assemble_evidence,**v)
 def test_empty_source_custom_fields_preserved(self):old=json.loads(Path(self.f.e['source_legacy_receipt']['path']).read_bytes())['response'];new=json.loads(Path(self.f.e['source_native_receipt']['path']).read_bytes())['response'];self.assertEqual(g.source_custom_fields(self.f.public,old,new),{})
 def pair(self):
  old=json.loads(Path(self.f.e['source_legacy_receipt']['path']).read_bytes())['response'];new=json.loads(Path(self.f.e['source_native_receipt']['path']).read_bytes())['response'];new['custom_fields']={'legacy:communities':['viridis-canon']};return old,new
 def test_exact_existing_community_mirror_preserved(self):old,new=self.pair();self.assertEqual(g.source_custom_fields(self.f.public,old,new),new['custom_fields'])
 def test_changed_existing_community_holds(self):old,new=self.pair();new['custom_fields']['legacy:communities']=['other'];self.assertRaises(ValueError,g.source_custom_fields,self.f.public,old,new)
 def test_unlisted_custom_field_holds(self):old,new=self.pair();new['custom_fields']['arbitrary:evidence']='PASS';self.assertRaises(ValueError,g.source_custom_fields,self.f.public,old,new)
 def test_public_membership_changed_holds(self):old,new=self.pair();public=deepcopy(self.f.public);public['communities']=[{'id':'other'}];self.assertRaises(ValueError,g.source_custom_fields,public,old,new)
 def test_malformed_membership_holds(self):old,new=self.pair();old['metadata']['communities']=[{'id':'viridis-canon','claims':'all certified'}];public=deepcopy(self.f.public);public['communities']=old['metadata']['communities'];self.assertRaises(ValueError,g.source_custom_fields,public,old,new)
 def test_full_registration_existing_mirror_source_passes_strict_readback(self):
  old,new=self.pair();self.f.e['source_native_receipt']=receipt(self.f.root/'source_native.json','GET','https://zenodo.org/api/records/21971052',new,'application/vnd.inveniordm.v1+json');self.f.expected_native['custom_fields']=deepcopy(new['custom_fields']);self.f.e['expected_native']=save(self.f.root/'expected_native.json',self.f.expected_native);self.f.e['public_native_receipt']=receipt(self.f.root/'public_native.json','GET','https://zenodo.org/api/records/'+self.f.rid,self.f.expected_native,'application/vnd.inveniordm.v1+json');self.f.e_binding=save(self.f.root/'evidence.json',self.f.e);self.assertEqual(self.f.prepare()['status'],'PUBLISHED_GROUP_BOUND')
 def test_after_state_cannot_invent_source_custom_field(self):
  self.f.expected_native['custom_fields']={'legacy:communities':['viridis-canon']};self.f.e['expected_native']=save(self.f.root/'expected_native.json',self.f.expected_native);self.f.e['public_native_receipt']=receipt(self.f.root/'public_native.json','GET','https://zenodo.org/api/records/'+self.f.rid,self.f.expected_native,'application/vnd.inveniordm.v1+json');self.f.e_binding=save(self.f.root/'evidence.json',self.f.e);self.assertRaises(ValueError,self.f.prepare)
