import copy,hashlib,io,json,tempfile,unittest,urllib.error
from pathlib import Path
from publication_inventory import inventory_plan,require_approved_inventory
from zenodo_transport import ZenodoTransport,TransportHold


def md5(data):return hashlib.md5(data).hexdigest()


class InventoryTests(unittest.TestCase):
 def setUp(self):
  self.approved=[{'name':'keep.txt','size':3,'md5':md5(b'abc')},{'name':'replace.txt','size':4,'md5':md5(b'new!')}]
  self.inherited=[{'filename':'keep.txt','filesize':3,'checksum':md5(b'abc'),'id':'a'},{'filename':'replace.txt','filesize':3,'checksum':md5(b'old'),'id':'b'},{'filename':'LICENSE','filesize':3,'checksum':md5(b'zzz'),'id':'c'}]
  self.entries={f['name']:{'key':f['name'],'size':f['size'],'checksum':'md5:'+f['md5'],'id':f['name'],'mimetype':'text/plain','metadata':{},'links':{'self':'https://sandbox.zenodo.org/api/records/2/files/'+f['name']}} for f in self.approved}
 def test_keep_replace_and_explicit_drop(self):
  p=inventory_plan(self.inherited,self.approved)
  self.assertEqual([x['name'] for x in p['drop']],['replace.txt','LICENSE']);self.assertEqual([x['name'] for x in p['upload']],['replace.txt']);self.assertEqual(p['keep'],self.inherited[:1])
  self.assertEqual(p['drop'][0]['original_entry'],self.inherited[1])
 def test_exact_approved_inventory_and_reordered_entry_mapping_pass(self):
  self.assertEqual(require_approved_inventory(self.entries,self.approved)['count'],2)
  reordered=dict(reversed(list(self.entries.items())))
  self.assertEqual(require_approved_inventory(reordered,self.approved,exact_entries=self.entries)['count'],2)
 def test_unapproved_inherited_file_must_fail(self):
  self.entries['LICENSE']={'key':'LICENSE','size':3,'checksum':'md5:'+md5(b'zzz')}
  with self.assertRaisesRegex(TransportHold,'FILENAME_SET'):require_approved_inventory(self.entries,self.approved)
 def test_every_per_file_field_identical(self):
  changes=[('id','changed-id'),('mimetype','application/pdf'),('metadata',{'description':'changed'}),('links',{'self':'https://sandbox.zenodo.org/api/records/99/files/keep.txt'}),('unlisted_field',True)]
  for field,value in changes:
   with self.subTest(field=field):
    actual=copy.deepcopy(self.entries);actual['keep.txt'][field]=value
    with self.assertRaisesRegex(TransportHold,'PER_FILE_FIELDS'):require_approved_inventory(actual,self.approved,exact_entries=self.entries)
 def test_per_file_field_disappearance_must_fail(self):
  actual=copy.deepcopy(self.entries);del actual['keep.txt']['metadata']
  with self.assertRaisesRegex(TransportHold,'PER_FILE_FIELDS'):require_approved_inventory(actual,self.approved,exact_entries=self.entries)
 def test_checksum_change_must_fail(self):
  self.entries['keep.txt']['checksum']='md5:'+md5(b'bad')
  with self.assertRaisesRegex(TransportHold,'FILE_BYTES'):require_approved_inventory(self.entries,self.approved)
 def test_size_and_key_change_must_fail(self):
  for field,value in [('size',4),('key','other.txt')]:
   with self.subTest(field=field):
    actual=copy.deepcopy(self.entries);actual['keep.txt'][field]=value
    with self.assertRaisesRegex(TransportHold,'FILE_BYTES'):require_approved_inventory(actual,self.approved)
 def test_duplicate_inventory_and_inherited_names_rejected(self):
  for old,new in [(self.inherited+self.inherited[:1],self.approved),(self.inherited,self.approved+self.approved[:1])]:
   with self.assertRaises(TransportHold):inventory_plan(old,new)
 def test_empty_inventory_not_clearance(self):
  with self.assertRaises(TransportHold):require_approved_inventory({},[])
 def test_missing_hash_and_size_are_not_equal_evidence(self):
  with self.assertRaises(TransportHold):inventory_plan([{'filename':'x','id':'a'}],[{'name':'x'}])
  with self.assertRaises(TransportHold):require_approved_inventory({'x':{'key':'x','size':None,'checksum':'md5:None'}},[{'name':'x','size':None,'md5':'None'}])
 def test_malformed_approved_inventory_fails_closed(self):
  for bad in [None,{},[None],[{'name':'x','size':3,'md5':None}],[{'name':'x','size':True,'md5':md5(b'abc')}],[{'name':'x','size':-1,'md5':md5(b'abc')}],[{'name':'x','size':3,'md5':'abc'}],[{'name':'','size':3,'md5':md5(b'abc')}],[{'name':'../x','size':3,'md5':md5(b'abc')}],[{'name':'x\x00','size':3,'md5':md5(b'abc')}]]:
   with self.subTest(approved=bad):
    with self.assertRaises(TransportHold):inventory_plan(self.inherited,bad)
    with self.assertRaises(TransportHold):require_approved_inventory(self.entries,bad)
 def test_malformed_inherited_entries_fail_closed(self):
  for bad in [None,{},[None],[True],[{}],[{'filename':'x','id':'a','filesize':True,'checksum':md5(b'abc')}],[{'filename':'x','id':'a','filesize':3,'checksum':'abc'}]]:
   with self.subTest(inherited=bad):
    with self.assertRaises(TransportHold):inventory_plan(bad,self.approved)
 def test_malformed_native_entries_fail_closed(self):
  for bad in [None,[],{'keep.txt':None,'replace.txt':self.entries['replace.txt']}]:
   with self.subTest(entries=bad):
    with self.assertRaises(TransportHold):require_approved_inventory(bad,self.approved)
 def test_malformed_exact_entries_cannot_clear_full_field_check(self):
  for bad in [[],{}, {'wrong':self.entries['keep.txt'],'replace.txt':self.entries['replace.txt']},{'keep.txt':None,'replace.txt':self.entries['replace.txt']}]:
   with self.subTest(exact_entries=bad):
    with self.assertRaises(TransportHold):require_approved_inventory(self.entries,self.approved,exact_entries=bad)
  wrong=copy.deepcopy(self.entries);wrong['keep.txt']['key']='replace.txt'
  with self.assertRaises(TransportHold):require_approved_inventory(self.entries,self.approved,exact_entries=wrong)


class DraftDeleteTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();checksum=md5(b'abc')
  self.old={'id':1,'doi':'10.test/1','conceptrecid':99,'files':[{'id':'abc-123','key':'old.txt','size':3,'checksum':'md5:'+checksum}]}
  self.file={'id':'abc-123','filename':'old.txt','filesize':3,'checksum':checksum,'links':{}}
  self.draft={'id':2,'conceptrecid':99,'state':'unsubmitted','submitted':False,'files':[copy.deepcopy(self.file)]}
  self.calls=[];self.delete_status=204;self.delete_body=b'';self.delete_error=None;outer=self
  class Opener:
   def open(self,req,timeout):
    outer.calls.append((req.method,req.full_url))
    if req.method=='DELETE' and outer.delete_error:raise outer.delete_error
    class R:
     status=outer.delete_status if req.method=='DELETE' else 200
     def __enter__(self):return self
     def __exit__(self,*args):pass
     def read(self):return outer.delete_body if req.method=='DELETE' else json.dumps(outer.old if '/api/records/' in req.full_url else outer.draft).encode()
    return R()
  self.t=ZenodoTransport('sandbox.zenodo.org','test-never-print',self.tmp.name,Opener());self.h=hashlib.sha256(b'').hexdigest()
 def tearDown(self):self.tmp.cleanup()
 def remove(self):return self.t.remove_inherited_draft_file(2,1,self.file,expected_sha256=self.h,authorized=True)
 def assert_no_delete(self):self.assertFalse(any(m=='DELETE' for m,u in self.calls))
 def test_exact_unpublished_successor_file_204(self):
  self.assertTrue(self.remove()['draft_file_removed']);self.assertEqual(self.calls[-1],('DELETE','https://sandbox.zenodo.org/api/deposit/depositions/2/files/abc-123'))
  receipt=json.loads((Path(self.tmp.name)/'003_DELETE.json').read_text())
  self.assertEqual(receipt['request_body_sha256'],self.h);self.assertEqual(receipt['response_sha256'],self.h);self.assertEqual(receipt['http_status'],204)
 def test_canonical_string_ids_match_integer_response_ids(self):
  self.assertTrue(self.t.remove_inherited_draft_file('2','1',self.file,expected_sha256=self.h,authorized=True)['draft_file_removed'])
 def test_published_or_edit_draft_not_removable(self):
  for change in ({'submitted':True},{'state':'done'},{'submitted':None}):
   self.draft.update(change)
   with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_original_record_id_cannot_be_removed(self):
  with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(1,1,self.file,expected_sha256=self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_noncanonical_requested_ids_rejected_before_network(self):
  for value in ['01','02','0','-1','+1',' 1','1 ','١',True,False,1.0,None,{},[]]:
   for did,pid in [(value,1),(2,value)]:
    with self.subTest(draft_id=did,parent_id=pid):
     with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(did,pid,self.file,expected_sha256=self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_wrong_fresh_published_parent_identity_rejected(self):
  for value in [3,'01',None,True]:
   with self.subTest(parent_id=value):
    self.old['id']=value
    with self.assertRaisesRegex(TransportHold,'PARENT_IDENTITY'):self.remove()
  self.assert_no_delete();self.assertTrue(all('/api/records/1' in url for method,url in self.calls))
 def test_wrong_fresh_draft_identity_rejected(self):
  for value in [3,'02',None,True]:
   with self.subTest(draft_id=value):
    self.draft['id']=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_foreign_or_noncanonical_concept_rejected(self):
  for value in [123,'099',None,True]:
   with self.subTest(concept=value):
    self.draft['conceptrecid']=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_malformed_public_parent_shape_fails_closed(self):
  for value in [[],[{}],None,True,'not a record']:
   with self.subTest(parent=value):
    self.old=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_malformed_draft_shape_fails_closed(self):
  for value in [[],[{}],None,True,'not a record']:
   with self.subTest(draft=value):
    self.draft=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_malformed_public_parent_file_lists_fail_closed(self):
  for value in [None,{},'files',[None],[False],[{}],[{'id':'abc-123','key':'old.txt','size':True,'checksum':'md5:'+md5(b'abc')}]]:
   with self.subTest(files=value):
    self.old['files']=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_malformed_draft_file_lists_fail_closed(self):
  for value in [None,{},'files',[None],[False],[{}],[{'id':'abc-123','filename':'old.txt','filesize':True,'checksum':md5(b'abc')}]]:
   with self.subTest(files=value):
    self.draft['files']=value
    with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_malformed_expected_file_rejected_before_network(self):
  bads=[None,[],{},dict(self.file,checksum='abc'),dict(self.file,filesize=True),dict(self.file,filesize=-1),dict(self.file,filename='../old.txt'),dict(self.file,id='abc/123'),dict(self.file,id='-')]
  for value in bads:
   with self.subTest(expected=value):
    with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(2,1,value,expected_sha256=self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_every_fresh_draft_file_field_matches_before_delete(self):
  for field,value in [('filename','other.txt'),('filesize',4),('checksum',md5(b'bad')),('id','abc-124'),('links',{'self':'changed'}),('new_server_field','changed')]:
   with self.subTest(field=field):
    self.draft['files']=[dict(self.file,**{field:value})]
    with self.assertRaisesRegex(TransportHold,'MISMATCH'):self.remove()
  self.assert_no_delete()
 def test_fresh_draft_file_field_disappearance_rejected(self):
  del self.draft['files'][0]['links']
  with self.assertRaisesRegex(TransportHold,'MISMATCH'):self.remove()
  self.assert_no_delete()
 def test_nested_bool_integer_alias_does_not_match_full_entry(self):
  self.file['metadata']={'nested':[{'flag':True}]}
  self.draft['files'][0]['metadata']={'nested':[{'flag':1}]}
  with self.assertRaisesRegex(TransportHold,'MISMATCH'):self.remove()
  self.assert_no_delete()
 def test_float_integer_alias_does_not_match_full_entry(self):
  self.file['metadata']={'value':1.0}
  self.draft['files'][0]['metadata']={'value':1}
  with self.assertRaisesRegex(TransportHold,'MISMATCH'):self.remove()
  self.assert_no_delete()
 def test_full_entry_object_key_order_is_not_a_field_change(self):
  self.draft['files'][0]=dict(reversed(list(self.file.items())))
  self.assertTrue(self.remove()['draft_file_removed'])
 def test_non_json_expected_optional_fields_rejected_before_network(self):
  for value in [float('nan'),float('inf'),{1:'integer key'},('tuple',),{'set'},b'bytes']:
   with self.subTest(value=repr(value)):
    malformed=dict(self.file,metadata={'value':value})
    with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(2,1,malformed,expected_sha256=self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_nonfinite_fresh_file_fields_rejected(self):
  self.draft['files'][0]['metadata']={'value':float('nan')}
  with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_file_not_in_published_parent_rejected(self):
  self.old['files'][0]['checksum']='md5:'+md5(b'bad')
  with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_duplicate_selected_identity_in_either_list_rejected(self):
  self.old['files']*=2
  with self.assertRaises(TransportHold):self.remove()
  self.old['files']=self.old['files'][:1];self.draft['files']*=2
  with self.assertRaises(TransportHold):self.remove()
  self.assert_no_delete()
 def test_general_delete_still_rejected(self):
  for url in ('/api/records/1','/api/deposit/depositions/1','/api/deposit/depositions/2/files/abc-123'):
   with self.assertRaises(TransportHold):self.t.request('DELETE','https://sandbox.zenodo.org'+url,b'',self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_authorization_and_hash_required_before_network(self):
  for auth,h in [(False,self.h),(1,self.h),(True,'wrong')]:
   with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(2,1,self.file,expected_sha256=h,authorized=auth)
  self.assertEqual(self.calls,[])
 def test_path_injection_rejected(self):
  for did,pid in [('2/files/x','1'),('2','1?x')]:
   with self.assertRaises(TransportHold):self.t.remove_inherited_draft_file(did,pid,self.file,expected_sha256=self.h,authorized=True)
  self.assertEqual(self.calls,[])
 def test_delete_200_response_not_success_and_never_retried(self):
  self.delete_status=200;self.delete_body=b'{}'
  with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.remove()
  self.assertEqual(sum(m=='DELETE' for m,u in self.calls),1)
 def test_delete_202_pending_not_success_and_never_retried(self):
  self.delete_status=202;self.delete_body=b'{"pending":true}'
  with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.remove()
  self.assertEqual(sum(m=='DELETE' for m,u in self.calls),1)
 def test_nonempty_204_not_success_and_never_retried(self):
  self.delete_body=b' '
  with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.remove()
  self.assertEqual(sum(m=='DELETE' for m,u in self.calls),1)
  receipt=json.loads((Path(self.tmp.name)/'003_DELETE.json').read_text())
  self.assertEqual(receipt['status'],'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY');self.assertNotIn('response',receipt)
 def test_delete_timeout_is_uncertain_and_not_retried(self):
  self.delete_error=TimeoutError('do not expose this error text')
  with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.remove()
  self.assertEqual(sum(m=='DELETE' for m,u in self.calls),1)
  self.assertNotIn('do not expose', (Path(self.tmp.name)/'003_DELETE.json').read_text())
 def test_delete_http_error_credential_redacted_and_not_retried(self):
  self.delete_error=urllib.error.HTTPError('https://sandbox.zenodo.org/api/x',409,'conflict',{},io.BytesIO(b'{"message":"test-never-print"}'))
  with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.remove()
  self.assertEqual(sum(m=='DELETE' for m,u in self.calls),1)
  raw=(Path(self.tmp.name)/'003_DELETE.json').read_text();receipt=json.loads(raw)
  self.assertNotIn('test-never-print',raw);self.assertEqual(receipt['error_response']['message'],'[REDACTED_CREDENTIAL]')


if __name__=='__main__':unittest.main()
