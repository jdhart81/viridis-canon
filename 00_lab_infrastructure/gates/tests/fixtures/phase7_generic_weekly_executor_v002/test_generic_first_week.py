"""Source-only FIRST tests: no marker is scientific or runtime admission."""
import copy,json,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import owned_digest_machine as machine
import test_weekly_prestart_source as previous
import test_weekly_commands as commands
import test_weekly_successor_archive_wait as wait
class FirstPlan(previous.Tests):
 def setUp(self):
  super().setUp();self.manifest['release_week']='2026-W42';self.manifest['public_metadata']['title']='Viridis Methods Digest — 2026-W42'
  p=self.package/'DIGEST_MANIFEST.json';p.write_bytes(e.raw_json(self.manifest));self.plan['digest_manifest']=e.binding(p)
  self.plan.update(release_week='2026-W42',start_kind='CREATE_WEEK',expected_concept_id=None,prior_run_ids=[])
  for row in self.plan['approved_inventory']:
   b=Path(row['path']).read_bytes();row.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),md5=hashlib.md5(b).hexdigest())
 def test_create_plan_parser_only_pass(self):self.assertEqual(e.require_plan(self.root,self.plan),self.package)
 def test_first_week_duplicate_W41_no_output_no_reservation(self):self.plan['release_week']='2026-W41';self.no_write()
 def test_first_week_invented_parent_no_output_no_reservation(self):self.plan['expected_concept_id']='23999999';self.no_write()
 def test_first_week_source_same_as_concept_no_write(self):self.plan['source_concept_id']=self.plan['predecessor_record_id'];self.no_write()
 def test_source_receipt_equality_remains_mandatory_for_create(self):self.modify('source_native_before_create',lambda x:x['response'].update(metadata={'title':'after changed'}));self.no_write()
 def test_every_generic_purpose_module_is_required_before_write(self):
  originals=copy.deepcopy(self.plan['purpose_source_pins'])
  for name in ['weekly_digest_executor.py','weekly_digest_boundary.py','weekly_digest_runtime.py','weekly_checkpoint_replay.py','prepare_weekly_digest_plan.py','invoke_weekly_digest.py','weekly_archive_wait.py','weekly_digest_queue.py','weekly_pending_discovery.py']:
   with self.subTest(name=name):self.plan['purpose_source_pins']=[x for x in originals if x['name']!=name];self.no_write()
class CreateCommand(commands.Tests):
 def test_create_payload_has_exact_single_metadata_envelope(self):
  c=self.cmd('CREATE_WEEK');decoded=json.loads(c['body']);self.assertEqual(set(decoded),{'metadata'});self.assertNotIn('metadata',decoded['metadata']);self.call('CREATE_WEEK',c)
 def test_other_title_cannot_reach_transport(self):
  c=self.cmd('CREATE_WEEK');x=json.loads(c['body']);x['metadata']['title']='foreign';c['body']=e.raw_json(x);self.assertRaises(ValueError,self.call,'CREATE_WEEK',c)
 def test_omitted_or_added_field_fails_exact_command(self):
  for key in ['creators','license','resource_type','unknown']:
   with self.subTest(key=key):
    c=self.cmd('CREATE_WEEK');x=json.loads(c['body']);x['metadata'].pop(key,None);x['metadata']['unknown']=True;c['body']=e.raw_json(x);self.assertRaises(ValueError,self.call,'CREATE_WEEK',c)
 def test_newversion_cannot_substitute_for_first_week(self):
  self.plan['start_kind']='CREATE_WEEK';self.assertRaises(ValueError,self.call,'NEW_VERSION',self.cmd('NEW_VERSION'))
 def test_create_cannot_substitute_for_newversion(self):
  self.plan['start_kind']='NEW_VERSION';self.assertRaises(ValueError,self.call,'CREATE_WEEK',self.cmd('CREATE_WEEK'))
class ExactMetadata(commands.Tests):
 def test_metadata_exact_science_envelope_pass(self):self.call('METADATA',self.cmd('METADATA'))
 def test_metadata_changed_title_claim_license_or_extra_fails(self):
  for key,value in [('title','foreign'),('description','stronger claim'),('license','cc-zero'),('extra',True)]:
   with self.subTest(key=key):
    c=self.cmd('METADATA');x=json.loads(c['body']);x['metadata'][key]=value;c['body']=e.raw_json(x);self.assertRaises(ValueError,self.call,'METADATA',c)
 def test_metadata_dropped_field_fails(self):
  c=self.cmd('METADATA');x=json.loads(c['body']);x['metadata'].pop('creators');c['body']=e.raw_json(x);self.assertRaises(ValueError,self.call,'METADATA',c)
 def test_metadata_native_type_difference_fails(self):
  c=self.cmd('METADATA');x=json.loads(c['body']);x['metadata']['publication_date']=20261010;c['body']=e.raw_json(x);self.assertRaises(ValueError,self.call,'METADATA',c)
class FirstArchive(wait.Tests):
 def test_create201_exact_owned_zip_profile(self):
  c=copy.deepcopy(self.created);c['url']='https://zenodo.org/api/deposit/depositions';c['response']['files']=[];self.wait.arm(self.rid,self.src,c,self.first,self.archive);self.wait.open(self.request());self.assertEqual(self.inner.calls[-1][2],600)
 def test_create_with_inherited_files_fails_before_sender(self):
  c=copy.deepcopy(self.created);c['url']='https://zenodo.org/api/deposit/depositions';c['response']['files']=[{'filename':'old'}];self.assertRaises(ValueError,self.wait.arm,self.rid,self.src,c,self.first,self.archive);self.assertEqual(self.inner.calls,[])
if __name__=='__main__':unittest.main()
