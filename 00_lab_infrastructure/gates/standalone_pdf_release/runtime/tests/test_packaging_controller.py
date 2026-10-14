"""Portable synthetic HTTP-shaped fixtures; no network or science PASS claims."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parents[1]
GATES=HERE.parents[1] if (HERE.parents[1]/'own_record_comparison.py').exists()else Path('/private/tmp/viridis-standalone-pdf-standard-20261012/00_lab_infrastructure/gates')
sys.path.insert(0,str(HERE));sys.path.insert(0,str(GATES))
import digest_controller_v2 as controller
import packaging_runtime as runtime
import test_own_record_comparison as fixtures
spec=importlib.util.spec_from_file_location('actual_current_own_policy',GATES/'own_record_comparison.py')
own=importlib.util.module_from_spec(spec);spec.loader.exec_module(own)


def binding(path):return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def write(root,name,value):
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,sort_keys=True)+'\n');return binding(p)


class DynamicInventory(unittest.TestCase):
 def test_all_note_pdfs_not_fixed_six_are_in_current_inventory(self):
  with tempfile.TemporaryDirectory()as folder:
   package=Path(folder).resolve();uploads=[]
   for name in ['paper.pdf','METHODS_NOTES.zip',*[f'Run-{i:03d}-Paper.pdf'for i in range(191,195)]]:
    raw=b'%PDF-1.7\n'+name.encode();(package/name).write_bytes(raw)
    uploads.append({'filename':name,'bytes':len(raw),'md5':hashlib.md5(raw).hexdigest(),'sha256':hashlib.sha256(raw).hexdigest()})
   for name in ['DIGEST_MANIFEST.json','PUBLICATION_BINDING.json']:(package/name).write_bytes(b'{}')
   result=controller.approved_inventory(package,{'uploads':uploads})
   self.assertEqual(len(result),8);self.assertIn('Run-194-Paper.pdf',result)
   (package/'Run-194-Paper.pdf').write_bytes(b'changed')
   with self.assertRaisesRegex(controller.Hold,'DECLARED_UPLOAD_BYTES'):controller.approved_inventory(package,{'uploads':uploads})
 def test_declared_filename_alias_or_extra_manifest_masquerade_holds(self):
  for filename in ['../paper.pdf','sub/paper.pdf','DIGEST_MANIFEST.json']:
   with self.subTest(filename=filename),tempfile.TemporaryDirectory()as folder:
    with self.assertRaises(controller.Hold):controller.approved_inventory(Path(folder),{'uploads':[{'filename':filename}]})
 def test_cleanup_accepts_actual_admitted_run_pdf_and_holds_unknown_extra(self):
  entry={'filename':'Run-167-Paper.pdf','id':'01234567-1234-1234-1234-012345678901','filesize':42,'checksum':'a'*32}
  legacy={'id':102,'conceptrecid':'100','state':'unsubmitted','submitted':False,'files':[entry]}
  native={'id':'102','parent':{'id':'100'},'is_published':False,'files':{'entries':{entry['filename']:{'id':entry['id'],'key':entry['filename'],'size':42,'checksum':'md5:'+'a'*32}}}}
  args=(legacy,native,entry,{'record_id':'102','concept_id':'100'})
  self.assertTrue(controller.draft_cleanup_entry(*args,allowed_names={entry['filename']}).endswith('/files/'+entry['id']))
  with self.assertRaisesRegex(controller.Hold,'EXACT_CLEANUP_ENTRY'):controller.draft_cleanup_entry(*args,allowed_names={'paper.pdf'})
 def test_cleanup_cannot_delete_published_or_changed_file(self):
  entry={'filename':'paper.pdf','id':'01234567-1234-1234-1234-012345678901','filesize':42,'checksum':'a'*32}
  legacy={'id':102,'conceptrecid':'100','state':'done','submitted':True,'files':[entry]}
  with self.assertRaisesRegex(controller.Hold,'UNPUBLISHED_DRAFT_ONLY'):
   controller.draft_cleanup_entry(legacy,{},entry,{'record_id':'102','concept_id':'100'},allowed_names={'paper.pdf'})


class FirstWeekExistingPolicyIntegration(unittest.TestCase):
 def case(self):
  native,legacy,controls,ownership=fixtures.fixture()
  payload={'metadata':deepcopy(controls['legacy_metadata'])};payload['metadata']['title']='Viridis Methods Digest — 2026-W42'
  native_md=deepcopy(controls['native_metadata']);native_md['title']=payload['metadata']['title'];native_md['related_identifiers']=[{'identifier':'10.5281/zenodo.101','scheme':'doi','relation_type':{'id':'issupplementto','title':{'en':'Is supplement to'}}}]
  native['metadata']=deepcopy(native_md);native['files']={'entries':{},'count':0,'total_bytes':0}
  legacy['metadata']=deepcopy(payload['metadata']);legacy['title']=payload['metadata']['title'];legacy['files']=[]
  created=deepcopy(ownership['creation_receipt']);created['url']=own.BASE+'/api/deposit/depositions';created['request_body_sha256']=controller.sha(controller.encoded(payload));created['response']['metadata']=deepcopy(payload['metadata']);created['response']['files']=[]
  first_n=deepcopy(ownership['first_native_receipt']);first_n['response']=native
  first_l=deepcopy(ownership['first_legacy_receipt']);first_l['response']=legacy
  source_native=fixtures.prior_native();source_native['parent']['id']='999'
  return source_native,payload,native_md,created,first_l,first_n
 def test_real_unchanged_current_own_consumer_admits_new_week_create(self):
  args=self.case();controls=controller.initial_week_controls(own,*args,'101')
  self.assertEqual(controls['files'],[]);self.assertEqual(controls['native_metadata']['title'],'Viridis Methods Digest — 2026-W42')
  self.assertEqual(own.require_ownership(args[3],args[5],args[4],prior_ids=['101'])['start_kind'],'CREATE_WEEK')
  self.assertIs(own.require_own_readback(args[5]['response'],args[4]['response'],controlled=controls,
              ownership={'creation_receipt':args[3],'first_native_receipt':args[5],'first_legacy_receipt':args[4],'prior_ids':['101']})['certifies'],False)
 def test_creation_cannot_inherit_files_or_change_new_week_metadata(self):
  for mode in ['files','metadata','request','sameconcept']:
   args=list(self.case())
   if mode=='files':args[5]['response']['files']['entries']['buried.pdf']={'key':'buried.pdf','size':1,'checksum':'md5:'+'a'*32}
   if mode=='metadata':args[5]['response']['metadata']['description']='rewritten'
   if mode=='request':args[3]['request_body_sha256']='0'*64
   if mode=='sameconcept':args[0]['parent']['id']='100'
   with self.subTest(mode=mode),self.assertRaises(ValueError):controller.initial_week_controls(own,*args,'101')
 def test_no_week_record_is_required_not_an_existing_or_pending_week(self):
  scope={'predecessor_record_id':'101','concept_id':None,'release_week':'2026-W42','run_ids':['Run-194'],'start_kind':'CREATE_WEEK'}
  receipt={'record_id':'101','release_week':'2026-W41'}
  legacy={'id':101,'conceptrecid':'100','metadata':{'title':'Viridis Methods Digest — 2026-W41'}}
  native={'id':'101','parent':{'id':'100'},'is_published':True,'is_draft':False,'status':'published','versions':{'is_latest':True}}
  discovery={'status':'NO_EXISTING_WEEKLY_RECORD','release_week':'2026-W42','record_id':None,'concept_id':None}
  self.assertEqual(controller.require_predecessor(scope,discovery,receipt,legacy,native)['start_kind'],'CREATE_WEEK')
  with self.assertRaises(controller.Hold):controller.require_predecessor(scope,{**discovery,'status':'EXISTING_WEEKLY_RECORD','record_id':'205'},receipt,legacy,native)
  with self.assertRaises(controller.Hold):controller.require_predecessor(scope,discovery,{**receipt,'release_week':'2026-W42'},legacy,native)


class ScopeAuthority(unittest.TestCase):
 def case(self,root,text='Publish exactly the reviewed W42 digest cohort.'):
  predecessor={'path':'old-registration.json','sha256':'a'*64}
  release={'standard':'VRS-EXACT-DIGEST-RELEASE-SCOPE-2','canonical_root':str(root),'release_week':'2026-W42','batch_label':'W42-a',
     'run_ids':['Run-194'],'predecessor_registration':predecessor,'predecessor_record_id':'101','concept_id':None,
     'publication_route':'First Methods Digest of an explicitly authorized new ISO week','start_kind':'CREATE_WEEK','new_scientific_or_runtime_authority':False}
  scope=write(root,'scope.json',release)
  provider=write(root,'provider.json',{'standard':'VRS-PROVIDER-ATTRIBUTED-USER-INSTRUCTION-EXCERPT-1','provider_tool':'mcp__codex_app__read_thread',
        'thread_id':'fixture-thread','turn_id':'fixture-turn','user_messages':[{'type':'userMessage','id':'fixture-user','content':[{'type':'text','text':text}]}]})
  review=write(root,'review.json',{'standard':'VRS-REVIEWED-PROVIDER-DIGEST-PUBLICATION-SCOPE-1','status':'EXACT_USER_INSTRUCTION_RELEASE_SCOPE_REVIEW_PASS',
      'reviewer':'Fixture reviewer, not a production approval','provider_instruction':provider,'provider_user_message_id':'fixture-user','user_text':text,
      'release_scope':scope,'authorized_run_ids':['Run-194'],'publication_route':release['publication_route'],'start_kind':'CREATE_WEEK',
      'scientific_admission_changed':False,'new_runtime_authority':False})
  authority=write(root,'authorization.json',{'standard':'VRS-PROVIDER-BOUND-EXACT-DIGEST-PUBLICATION-AUTHORITY-1','captured_at_utc':'2026-10-01T00:00:00Z',
     'provider_instruction':provider,'provider_user_message_id':'fixture-user','release_scope':scope,'scope_review':review})
  return {'batch_label':'W42-a','predecessor_registration':predecessor,'release_scope':scope,'user_authorization':authority},release
 def test_fresh_provider_scope_is_not_hardcoded_to_old_quote(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();config,value=self.case(root);self.assertEqual(controller.require_release_scope(root,config,value),value)
 def test_packaging_directive_cannot_publish_science(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();config,value=self.case(root,runtime.USER_DIRECTIVE)
   with self.assertRaisesRegex(controller.Hold,'PACKAGING_IS_NOT_PUBLICATION_AUTHORITY'):controller.require_release_scope(root,config,value)
 def test_extending_cohort_or_changing_route_cannot_reuse_old_scope_review(self):
  for field,value in [('run_ids',['Run-194','Run-195']),('start_kind','NEW_VERSION')]:
   with self.subTest(field=field),tempfile.TemporaryDirectory()as folder:
    root=Path(folder).resolve();config,scope=self.case(root);scope[field]=value
    with self.assertRaises(controller.Hold):controller.require_release_scope(root,config,scope)
 def test_provider_agent_message_cannot_be_publication_authority(self):
  with tempfile.TemporaryDirectory()as folder:
   root=Path(folder).resolve();config,value=self.case(root);authority=json.loads(Path(config['user_authorization']['path']).read_bytes());provider_path=Path(authority['provider_instruction']['path'])
   provider=json.loads(provider_path.read_bytes());provider['user_messages'][0]['type']='assistantMessage';authority['provider_instruction']=write(root,'provider.json',provider)
   config['user_authorization']=write(root,'authorization.json',authority)
   with self.assertRaisesRegex(controller.Hold,'ACTUAL_PUBLICATION_USER_MESSAGE'):controller.require_release_scope(root,config,value)


if __name__=='__main__':unittest.main()
