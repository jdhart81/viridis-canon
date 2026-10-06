import unittest
import json
from pathlib import Path
from copy import deepcopy
from publication_preservation import *
class PreservationTests(unittest.TestCase):
 def test_only_proven_html_sanitization(self):
  require_public_metadata({'title':'Canon v5','description':'<p>A &mdash; B</p>\n<p>C</p>'},{'title':'Canon v5','description':'<p>A — B</p><hr/><p>C</p>'})
 def test_claim_number_and_attribute_changes_hold(self):
  for actual in ('<p>2 bits</p>','<p>1 byte</p>','<p class="changed">1 bit</p>'):
   with self.assertRaises(TransportHold):require_public_metadata({'description':actual},{'description':'<p>1 bit</p>'})
 def test_every_other_public_field_exact(self):
  for key in ('title','doi','relations','license','resource_type'):
   with self.assertRaises(TransportHold):require_public_metadata({key:'changed'},{key:'original'})
 def test_pid_repair_changes_no_other_fields(self):
  public={'pids':{'doi':{'identifier':'10.5281/zenodo.1','provider':'datacite'}}}
  draft={'pids':{'doi':{'identifier':'10.5281/zenodo.1','provider':'external'}},'metadata':{'title':'Canon'},'custom_fields':{},'access':{},'files':{}}
  result=managed_pid_payload(public,draft)
  self.assertEqual(result['pids'],public['pids'])
  for key in ('metadata','custom_fields','access','files'):self.assertEqual(result[key],draft[key])
  self.assertEqual(draft['pids']['doi']['provider'],'external')
 def test_changed_doi_never_repaired(self):
  with self.assertRaises(TransportHold):managed_pid_payload({'pids':{'doi':{'identifier':'original','provider':'datacite'}}},{'pids':{'doi':{'identifier':'changed','provider':'external'}}})
 def test_native_protected_changes_hold(self):
  before={'metadata':{'title':'original','description':'old','subjects':[]},'custom_fields':{},'access':{},'files':{}}
  after=deepcopy(before);after['metadata'].update(title='changed',description='new',subjects=[{'subject':'uncertified'}])
  with self.assertRaises(TransportHold):require_native_preservation(before,after,'new',['uncertified'])

class CommunityMirrorTests(unittest.TestCase):
 def setUp(self):
  self.proof={'status':'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN','public_post_publish_exact_preservation':True}
  self.before={'custom_fields':{'other':'keep'}};self.after={'custom_fields':{'other':'keep','legacy:communities':['already-member']}}
 def test_exact_existing_member_mirror_after_real_proof_allowed(self):
  from publication_preservation import _require_custom_fields
  _require_custom_fields(self.before,self.after,[{'id':'already-member'}],self.proof)
 def test_unproven_field_never_ignored(self):
  from publication_preservation import _require_custom_fields
  for proof in (None,{},dict(self.proof,public_post_publish_exact_preservation=False)):
   with self.assertRaises(TransportHold):_require_custom_fields(self.before,self.after,[{'id':'already-member'}],proof)
 def test_membership_change_other_field_or_missing_member_hold(self):
  from publication_preservation import _require_custom_fields
  for after in ({'custom_fields':{'other':'keep','legacy:communities':['new-member']}},{'custom_fields':{'other':'changed','legacy:communities':['already-member']}},{'custom_fields':{'legacy:communities':['already-member']}}):
   with self.assertRaises(TransportHold):_require_custom_fields(self.before,after,[{'id':'already-member'}],self.proof)
 def test_unknown_shapes_hold(self):
  from publication_preservation import _require_custom_fields
  for members in (None,[],[{'id':'already-member','extra':'field'}]):
   with self.assertRaises(TransportHold):_require_custom_fields(self.before,self.after,members,self.proof)

class FilePreservationTests(unittest.TestCase):
 def setUp(self):
  self.files=[{'key':f'fixture-{i}.txt','id':str(i),'checksum':f'md5:{i:032x}',
               'size':10+i,'mimetype':'text/plain','links':{'self':f'https://example.org/{i}'},
               'extra':{'preserve':True}} for i in range(6)]
 def test_five_plus_files_forced_reorder_passes(self):
  self.assertEqual(require_file_preservation(list(reversed(self.files)),self.files),
                   {'mode':'FILENAME_KEYED_SET','count':6})
 def test_one_checksum_change_must_fail(self):
  actual=deepcopy(self.files);actual.reverse();actual[0]['checksum']='md5:'+'0'*32
  with self.assertRaisesRegex(TransportHold,'PER_FILE_FIELDS'):require_file_preservation(actual,self.files)
 def test_every_field_and_nested_field_preserved(self):
  for key,value in [('id','new'),('size',999),('mimetype','application/pdf'),
                    ('links',{'self':'changed'}),('extra',{'preserve':False})]:
   actual=deepcopy(self.files);actual[0][key]=value
   with self.subTest(key=key),self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_unknown_field_addition_or_removal_fails(self):
  for add in (True,False):
   actual=deepcopy(self.files)
   if add:actual[0]['new_server_field']='must be reviewed'
   else:del actual[0]['extra']
   with self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_filename_set_missing_extra_or_renamed_fails(self):
  renamed=deepcopy(self.files);renamed[0]['key']='renamed.txt'
  for actual in (self.files[:-1],self.files+[dict(self.files[0],key='extra.txt')],renamed):
   with self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_duplicates_unchanged_pass_strict_ordered(self):
  files=self.files+[deepcopy(self.files[0])]
  self.assertEqual(require_file_preservation(deepcopy(files),files)['mode'],
                   'STRICT_ORDERED_DUPLICATE_FILENAMES')
 def test_duplicates_reordered_fail_strict_ordered(self):
  files=self.files+[dict(self.files[0],id='different-id')]
  with self.assertRaisesRegex(TransportHold,'STRICT_ORDERED'):require_file_preservation(list(reversed(files)),files)
 def test_duplicate_on_only_one_side_fails(self):
  actual=deepcopy(self.files);actual[1]['key']=actual[0]['key']
  with self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_malformed_input_fails_closed(self):
  for actual in (None,{},[{}],[{'key':None}],[{'key':''}],['filename'],[{'key':5}]):
   with self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_json_type_changes_are_not_identical_fields(self):
  actual=deepcopy(self.files);actual[0]['extra']['preserve']=1
  with self.assertRaises(TransportHold):require_file_preservation(actual,self.files)
 def test_real_sandbox_six_file_roundtrip_and_forced_response_reorder(self):
  fixture=json.loads((Path(__file__).parent/'fixtures/sandbox_file_order_613098.json').read_text())
  self.assertGreaterEqual(len(fixture['before_files']),5)
  self.assertNotEqual(fixture['before_files'],fixture['after_files'])
  for key in ('after_files','forced_reordered_files'):
   self.assertEqual(require_file_preservation(fixture[key],fixture['before_files'])['mode'],'FILENAME_KEYED_SET')
 def test_real_sandbox_checksum_corruption_must_fail(self):
  fixture=json.loads((Path(__file__).parent/'fixtures/sandbox_file_order_613098.json').read_text())
  actual=deepcopy(fixture['forced_reordered_files']);actual[0]['checksum']='md5:'+'0'*32
  with self.assertRaisesRegex(TransportHold,'PER_FILE_FIELDS'):require_file_preservation(actual,fixture['before_files'])
