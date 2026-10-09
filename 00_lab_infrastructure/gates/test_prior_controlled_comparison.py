"""Current approved prior semantics; pure synthetic fixtures, no admission."""
from copy import deepcopy
from pathlib import Path
import ast, hashlib, importlib.util, json, sys, types, unittest
import own_record_comparison as own
import own_prior_record as prior

HERE=Path(__file__).resolve().parent

def native():
 return {'id':'101','parent':{'id':'100','pids':{'doi':{'identifier':'10.5281/zenodo.100'}}},'metadata':{'title':'paper','description':'banner','creators':[{'person_or_org':{'name':'Author'}}],'publication_date':'2026-10-07','subjects':[{'subject':'science'}],'rights':[{'id':'cc-by'}],'related_identifiers':[],'resource_type':{'id':'publication-article'},'communities':[{'id':'community'}],'unknown_semantic':{'value':1}},'custom_fields':{'meaning':'exact'},'access':{'record':'public'},'pids':{'doi':{'identifier':'10.5281/zenodo.101','provider':'datacite'},'oai':{'identifier':'oai:zenodo.org:101','provider':'oai'}},'versions':{'index':1,'is_latest':True,'is_latest_draft':True},'is_published':True,'is_draft':False,'status':'published','files':{'count':2,'entries':{'paper.pdf':{'key':'paper.pdf','size':17,'checksum':'md5:'+'a'*32,'id':'uuid-main','links':{'self':'mainbytes','preview':'old-preview'}},'data.csv':{'key':'data.csv','size':9,'checksum':'md5:'+'b'*32,'id':'uuid-data'}}},'links':{'self':'record','self_iiif_manifest':'manifest-old','thumbnails':{'250':'oldthumb'}},'media_files':{'entries':{'paper.pdf.ptif':{'processor':{'status':'init'}}}},'updated':'old','revision_id':1,'stats':{'downloads':0},'ui':{'preview':{}},'swh':{},'processing_status':'pending','unknown_semantic':{'exact':True}}

def legacy():
 n=native()
 return {'id':101,'conceptrecid':'100','doi':'10.5281/zenodo.101','conceptdoi':'10.5281/zenodo.100','metadata':deepcopy(n['metadata'])|{'relations':{'version':[{'index':0,'parent':{'pid_type':'recid','pid_value':'100'},'is_last':True}]}},'files':[deepcopy(v)for v in n['files']['entries'].values()],'updated':'old','modified':'old','revision':1,'stats':{},'links':{'self':'record','self_iiif_manifest':'old'},'submitted':True,'state':'done'}

def receipt(method,url,response,code=201):
 return {'environment':'zenodo.org','method':method,'url':url,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':code,'request_body_sha256':hashlib.sha256(b'{}').hexdigest(),'response':response}

class PriorControlledTests(unittest.TestCase):
 def check(self,a,b,r='NATIVE'):return own.require_prior_semantics(a,b,representation=r)
 def test_exact_preserved(self):self.assertEqual(self.check(native(),native())['differences'],[])
 def test_every_approved_root_processing_field_change_logged(self):
  for key in own._PROCESSING_ROOTS:
   with self.subTest(key=key):
    b=native();a=deepcopy(b);a[key]={'processing':'different','typed':False};v=self.check(a,b);self.assertEqual(v['after'],a);self.assertEqual(v['before'],b);self.assertTrue(v['processing_differences']);self.assertEqual(v['processing_differences'],v['differences'])
 def test_every_approved_root_processing_field_absence_logged(self):
  for key in own._PROCESSING_ROOTS:
   with self.subTest(key=key):
    b=native();b[key]=1;a=deepcopy(b);del a[key];self.assertTrue(self.check(a,b)['differences'])
 def test_every_preview_link_appearance_change_removal_logged(self):
  for key in own._PROCESSING_LINKS:
   with self.subTest(key=key):
    b=native();a=deepcopy(b);a['links'][key]=['asynchronous',False];self.check(a,b);b=deepcopy(a);del a['links'][key];self.check(a,b)
 def test_file_preview_links_and_processing_logged(self):
  b=native();a=deepcopy(b);row=a['files']['entries']['paper.pdf'];row['links']['preview']='new';row['links']['self_iiif_manifest']='new';row['processing_status']={'finished':True};row['updated']='new';self.assertTrue(self.check(a,b)['differences'])
 def test_parent_processing_logged_identity_still_protected(self):
  b=native();a=deepcopy(b);a['parent']['updated']='new';a['parent']['ui']={};self.check(a,b);a['parent']['id']='foreign';self.assertRaises(ValueError,self.check,a,b)
 def test_media_entire_shape_and_presence_never_gated(self):
  for value in (None,False,[],{'foreign-preview':{'status':'finished','links':{'unpredictable':'derived'}}}):
   with self.subTest(value=value):
    b=native();a=deepcopy(b);a['media_files']=value;self.check(a,b)
 def test_semantic_metadata_every_leaf_protected(self):
  for key in native()['metadata']:
   with self.subTest(key=key):
    b=native();a=deepcopy(b);a['metadata'][key]='changed';self.assertRaises(ValueError,self.check,a,b)
 def test_metadata_processing_named_fields_are_semantic(self):
  for key in ('updated','stats','ui','processing_status'):
   with self.subTest(key=key):
    b=native();b['metadata'][key]='sent';a=deepcopy(b);a['metadata'][key]='changed';self.assertRaises(ValueError,self.check,a,b)
 def test_all_pids_and_providers_protected(self):
  for path in ('identifier','provider'):
   for kind in ('doi','oai'):
    with self.subTest(kind=kind,path=path):
     b=native();a=deepcopy(b);a['pids'][kind][path]='foreign';self.assertRaises(ValueError,self.check,a,b)
 def test_missing_and_added_pid_protected(self):
  b=native();a=deepcopy(b);a['pids'].pop('oai');self.assertRaises(ValueError,self.check,a,b);a=deepcopy(b);a['pids']['unknown']={};self.assertRaises(ValueError,self.check,a,b)
 def test_parent_pid_protected(self):
  b=native();a=deepcopy(b);a['parent']['pids']['doi']['identifier']='foreign';self.assertRaises(ValueError,self.check,a,b)
 def test_file_name_size_checksum_count_protected(self):
  for mutation in ('name','size','checksum','count','remove','add','uuid','unknown'):
   with self.subTest(mutation=mutation):
    b=native();a=deepcopy(b);row=a['files']['entries']['paper.pdf']
    if mutation=='name':a['files']['entries']['other.pdf']=a['files']['entries'].pop('paper.pdf');row['key']='other.pdf'
    elif mutation=='count':a['files']['count']=3
    elif mutation=='remove':a['files']['entries'].pop('paper.pdf')
    elif mutation=='add':a['files']['entries']['new']={'key':'new','size':0,'checksum':'md5:'+'c'*32}
    elif mutation=='uuid':row['id']='changed'
    elif mutation=='unknown':row['new_semantic']=True
    else:row[mutation]='changed'
    self.assertRaises(ValueError,self.check,a,b)
 def test_protected_types_bool_vs_int(self):
  b=native();a=deepcopy(b);a['files']['entries']['paper.pdf']['size']=True;self.assertRaises(ValueError,self.check,a,b);a=deepcopy(b);a['versions']['index']=True;self.assertRaises(ValueError,self.check,a,b)
 def test_unknown_top_fields_change_or_appearance_holds(self):
  b=native();a=deepcopy(b);a['unknown_semantic']['exact']=1;self.assertRaises(ValueError,self.check,a,b);a=deepcopy(b);a['other_semantic']='x';self.assertRaises(ValueError,self.check,a,b)
 def test_unknown_link_is_not_ignored(self):
  b=native();a=deepcopy(b);a['links']['foreign_semantic']='url';self.assertRaises(ValueError,self.check,a,b)
 def test_unknown_file_link_is_not_ignored(self):
  b=native();a=deepcopy(b);a['files']['entries']['paper.pdf']['links']['self']='differentbytes';self.assertRaises(ValueError,self.check,a,b)
 def test_publication_state_is_not_processing_status(self):
  b=native();a=deepcopy(b);a['status']='draft';self.assertRaises(ValueError,self.check,a,b)
 def test_legacy_metadata_doi_concept_and_relations_protected(self):
  for key in ('metadata','doi','conceptdoi','conceptrecid','submitted','state'):
   with self.subTest(key=key):
    b=legacy();a=deepcopy(b);a[key]='changed';self.assertRaises(ValueError,self.check,a,b,'LEGACY')
 def test_legacy_order_logged_names_bytes_hash_count_preserved(self):
  b=legacy();a=deepcopy(b);a['files'].reverse();v=self.check(a,b,'LEGACY');self.assertEqual(v['after']['files'],a['files']);self.assertTrue(v['differences'])
 def test_legacy_duplicates_missing_names_or_contradictory_aliases_hold(self):
  for kind in ('duplicate','missing','contradictory'):
   with self.subTest(kind=kind):
    b=legacy();a=deepcopy(b)
    if kind=='duplicate':a['files'].append(deepcopy(a['files'][0]))
    elif kind=='missing':a['files'][0].pop('key')
    else:a['files'][0]['filename']='foreign'
    self.assertRaises(ValueError,self.check,a,b,'LEGACY')
 def test_failure_preserves_complete_diagnostic(self):
  b=native();a=deepcopy(b);a['metadata']['title']='changed';a['ui']={'new':'view'}
  with self.assertRaises(own.OwnRecordHold)as caught:self.check(a,b)
  audit=caught.exception.audit;self.assertEqual(audit['before'],b);self.assertEqual(audit['after'],a);self.assertTrue(audit['protected_differences']);self.assertTrue(any(x['path'].startswith('$.ui')for x in audit['differences']))
 def test_unproved_flag_change_holds(self):
  b=native();a=deepcopy(b);a['versions']['is_latest_draft']=False;self.assertRaises(ValueError,self.check,a,b)
 def test_existing_flag_scope_stays_exact(self):
  b=native();a=deepcopy(b);a['versions']['is_latest_draft']=False;a['media_files']={'status':'finished'};v=own.require_prior_exact(a,b,representation='NATIVE',boundary='CREATE');self.assertEqual(v['changed_flags'],['versions.is_latest_draft']);self.assertTrue(v['processing_differences']);self.assertEqual(v['observed_after'],a)
 def test_other_native_flags_or_index_stay_protected(self):
  for key in ('is_latest','index'):
   with self.subTest(key=key):
    b=native();a=deepcopy(b);a['versions'][key]=False if key=='is_latest' else 2;self.assertRaises(ValueError,own.require_prior_exact,a,b,representation='NATIVE',boundary='CREATE')
 def test_boolean_flag_type_holds(self):
  b=native();a=deepcopy(b);a['versions']['is_latest_draft']=0;self.assertRaises(ValueError,own.require_prior_exact,a,b,representation='NATIVE',boundary='CREATE')

class ChainReceiptTests(unittest.TestCase):
 def setUp(self):
  self.n=native();self.l=legacy();self.c=receipt('POST','https://zenodo.org/api/deposit/depositions/101/actions/newversion',{'id':102,'conceptrecid':'100'});self.p=receipt('POST','https://zenodo.org/api/deposit/depositions/102/actions/publish',{'id':102,'conceptrecid':'100','doi':'10.5281/zenodo.102'},202)
  import publication_preservation as preservation
  self.preservation=preservation
 def check(self,l,n,**kw):return prior.require_pair(l,n,self.l,self.n,preservation=self.preservation,**kw)
 def test_genuine_create_and_preview_processing_pass(self):
  n=deepcopy(self.n);n['versions']['is_latest_draft']=False;n['media_files']['entries']['paper.pdf.ptif']['processor']['status']='finished';v=self.check(self.l,n,creation=self.c);self.assertEqual(v['chain_state'],'OWN_CREATED');self.assertTrue(v['native_audit']['processing_differences']);self.assertEqual(v['observed_before']['native'],self.n)
 def test_genuine_publish_and_both_processing_pass(self):
  n=deepcopy(self.n);n['versions'].update(is_latest_draft=False,is_latest=False);n['ui']={'fresh':True};l=deepcopy(self.l);l['metadata']['relations']['version'][0]['is_last']=False;l['revision']=9;v=self.check(l,n,creation=self.c,publish=self.p);self.assertEqual(v['chain_state'],'OWN_PUBLISHED')
 def test_no_genuine_create_cannot_adopt_flag(self):
  n=deepcopy(self.n);n['versions']['is_latest_draft']=False;self.assertRaises(ValueError,self.check,self.l,n)
 def test_wrong_creation_identity_parent_status_or_body(self):
  for key in ('id','parent','http','body'):
   with self.subTest(key=key):
    c=deepcopy(self.c)
    if key=='id':c['response']['id']=101
    elif key=='parent':c['response']['conceptrecid']='foreign'
    elif key=='http':c['http_status']=True
    else:c['request_body_sha256']='a'*64
    n=deepcopy(self.n);n['versions']['is_latest_draft']=False;self.assertRaises(ValueError,self.check,self.l,n,creation=c)
 def test_protected_mutation_with_genuine_create_still_holds(self):
  n=deepcopy(self.n);n['versions']['is_latest_draft']=False;n['metadata']['title']='changed';self.assertRaises(ValueError,self.check,self.l,n,creation=self.c)
 def test_processing_alone_does_not_need_creation_claim(self):
  n=deepcopy(self.n);n['revision_id']=9;self.assertEqual(self.check(self.l,n)['chain_state'],'UNCHANGED')
 def test_publish_requires_creation_and_correct_own_doi(self):
  self.assertRaises(ValueError,self.check,self.l,self.n,publish=self.p);p=deepcopy(self.p);p['response']['doi']='foreign';self.assertRaises(ValueError,self.check,self.l,self.n,creation=self.c,publish=p)

class SourceProfileTests(unittest.TestCase):
 def test_two_exact_archive_bytes(self):
  pins={'own_record_comparison_legacy_cf74da.py':own.LEGACY_OWN_SOURCE_SHA256,'methods_digest_registration_legacy_21b813.py':'21b813c527566c12a06b15426c4a49370fd1e5ccbdcf9ca441bf5d305011d21c'}
  for name,sha in pins.items():self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),sha)
 def test_no_transport_or_mutation_capability(self):
  tree=ast.parse((HERE/'own_record_comparison.py').read_bytes());names={node.func.attr for node in ast.walk(tree)if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)};self.assertFalse(names&{'urlopen','write_bytes','write_text','post','put','delete','unlink','mkdir'})
 def test_authority_section_requires_exact_hash_not_status(self):
  raw=(HERE/'test_fixtures/prior_content_authority.md').read_bytes();self.assertEqual(own.require_prior_authority(raw)['section_sha256'],own.PRIOR_AUTHORITY_SECTION_SHA256)
  with self.assertRaises(ValueError):own.require_prior_authority(raw.replace(b'Nothing in the processing list ever is.',b'Nothing in the processing list sometimes is.'))
 def test_unknown_later_section_does_not_change_permanent_section_proof(self):
  raw=(HERE/'test_fixtures/prior_content_authority.md').read_bytes();own.require_prior_authority(raw+b'\n---\n\n## Future independent authority\nnew text\n')
 def test_missing_prior_authority_for_new_context_holds(self):
  raw=(HERE/'test_fixtures/prior_content_authority.md').read_bytes();raw=raw[:raw.index(own.PRIOR_AUTHORITY_HEADER.encode())-1];self.assertRaises(ValueError,own.require_prior_authority,raw)

if __name__=='__main__':unittest.main()
