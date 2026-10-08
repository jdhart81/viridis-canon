"""Portable synthetic lifecycle regressions. No transport/publication is run."""
from copy import deepcopy
from pathlib import Path
import json,tempfile,unittest
import digest_public_state as p
import methods_digest as d

UUID='f8748a51-f9c6-49ed-b6e9-9dc488f84419'
def save(q,v):
 q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(d.raw_json(v));return {'path':str(q),'sha256':d.sha(q)}
def receipt(q,method,url,response,accept='application/json',code=200):
 return save(q,{'environment':'zenodo.org','method':method,'url':url,'http_status':code,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':d.digest(d.raw_json(response)),'request_body_sha256':None if method=='GET'else d.digest(b'{}'),'response':response,'accept':accept})
def mirror_proof():
 return {'status':'SANDBOX_COMMUNITY_PURE_MIRROR_PROVEN','field':'custom_fields.legacy:communities','condition':p.MIRROR_CONDITION,'before_custom_fields':{},'existing_public_communities':[{'id':'synthetic-tested'}],'after_custom_fields':{'legacy:communities':['synthetic-tested']},'public_post_publish_exact_preservation':True,'production_writes_in_test':0,'checks':{'communities':True,'conceptdoi':True,'conceptrecid':True,'doi':True,'files':True,'native_membership':True},'transport_sha256':'a'*64}

class StateFixture:
 def __init__(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name).resolve();self.rid='999999';self.parent='999998';sid='21971052';sp='21968382'
  self.public={'title':'Synthetic exact science scope','communities':[{'id':'viridis-canon'}]}
  graph={'default':UUID,'ids':[UUID],'entries':[{'id':UUID,'slug':'viridis-canon','metadata':{'description':'Preserve entire object'}}]}
  self.native={'id':sid,'is_draft':False,'is_published':True,'pids':{'doi':{'identifier':'10.5281/zenodo.'+sid},'oai':{'identifier':'oai:zenodo.org:'+sid,'provider':'oai'}},'custom_fields':{'legacy:communities':['viridis-canon']},'parent':{'id':sp,'communities':graph},'versions':{'index':2,'is_latest':True},'links':p.canonical_links(sid,sp)}
  self.legacy={'id':int(sid),'doi':'10.5281/zenodo.'+sid,'conceptdoi':'10.5281/zenodo.'+sp,'conceptrecid':sp,'created':'2026-10-01T00:00:00Z','doi_url':'https://doi.org/10.5281/zenodo.'+sid,'metadata':{'communities':deepcopy(self.public['communities']),'relations':{'version':[{'index':1,'is_last':True,'parent':{'pid_type':'recid','pid_value':sp}}]}},'files':[],'links':deepcopy(self.native['links']),'modified':'2026-10-01T00:00:00Z','owners':[{'id':'3974'}],'recid':sid,'revision':1,'stats':{},'title':'Source title'}
  self.before={'id':self.rid,'is_draft':True,'is_published':False,'status':'draft','created':'2026-10-07T00:00:00Z','updated':'2026-10-07T00:01:00Z','revision_id':7,'versions':{'index':1,'is_latest':False,'is_latest_draft':True},'custom_fields':deepcopy(self.native['custom_fields']),'parent':{'id':self.parent,'communities':{},'pids':{},'access':{'owned_by':{'user':'3974'}}},'pids':{'doi':{'identifier':'10.5281/zenodo.'+self.rid,'provider':'datacite','client':'datacite'}},'metadata':{'title':self.public['title']},'access':{'record':'public'},'files':{'entries':{'paper.pdf':{'id':'11111111-1111-4111-8111-111111111111','key':'paper.pdf','checksum':'md5:'+'a'*32,'size':10,'links':{}}}}}
  self.before['links']=p.canonical_links(self.rid,self.parent)
  self.created={'id':int(self.rid),'conceptrecid':self.parent,'metadata':{'prereserve_doi':{'doi':'10.5281/zenodo.'+self.rid,'recid':int(self.rid)}}}
  self.reserved={'id':self.rid,'parent':{'id':self.parent},'pids':deepcopy(self.before['pids'])}
  self.published={'id':int(self.rid),'conceptrecid':self.parent,'state':'done','submitted':True,'doi':'10.5281/zenodo.'+self.rid,'conceptdoi':'10.5281/zenodo.'+self.parent}
  self.roles={'source_legacy_receipt':receipt(self.root/'source_legacy.json','GET','https://zenodo.org/api/records/'+sid,self.legacy),'source_native_receipt':receipt(self.root/'source_native.json','GET','https://zenodo.org/api/records/'+sid,self.native,p.NATIVE_ACCEPT),'before_publish_native_receipt':receipt(self.root/'transport/027_GET.json','GET','https://zenodo.org/api/records/'+self.rid+'/draft',self.before,p.NATIVE_ACCEPT),'creation_receipt':receipt(self.root/'create.json','POST','https://zenodo.org/api/deposit/depositions',self.created,code=201),'reservation_receipt':receipt(self.root/'reserve.json','POST','https://zenodo.org/api/records/'+self.rid+'/draft/pids/doi',self.reserved,p.NATIVE_ACCEPT,201),'publish_receipt':receipt(self.root/'transport/028_POST.json','POST','https://zenodo.org/api/deposit/depositions/'+self.rid+'/actions/publish',self.published,code=202),'mirror_proof':save(self.root/'mirror.json',mirror_proof())}
  self.context=p.assemble_context(record_id=self.rid,**self.roles);self.evidence={k:self.roles[k]for k in ('source_legacy_receipt','source_native_receipt')};self.evidence['own_publish_receipt']=self.roles['publish_receipt']
 def close(self):self.t.cleanup()
 def load(self,binding):return json.loads(d.bound_file(self.root,binding)[1])
 def consume(self):return p.consume_context(self.context,load=self.load,public=self.public,evidence_sources=self.evidence)
 def change(self,role,fn):
  q=Path(self.roles[role]['path']);v=json.loads(q.read_bytes());fn(v);self.roles[role]=save(q,v);self.context['source_bindings'][role]=self.roles[role]
  if role in self.evidence:self.evidence[role]=self.roles[role]
  if role=='publish_receipt':self.evidence['own_publish_receipt']=self.roles[role]

class PublicStateTests(unittest.TestCase):
 def setUp(self):self.f=StateFixture();self.addCleanup(self.f.close)
 def test_exact_native_prediction33links_graph_and_metadata_unchanged(self):
  v=self.f.consume();self.assertEqual(len(v['native']['links']),33);self.assertEqual(v['native']['links'],p.canonical_links(self.f.rid,self.f.parent));self.assertEqual(v['native']['parent']['communities'],self.f.native['parent']['communities']);self.assertEqual(v['native']['custom_fields'],{});self.assertEqual(v['native']['metadata'],self.f.before['metadata']);self.assertEqual(v['native']['access'],self.f.before['access']);self.assertEqual(v['legacy_relation']['version'][0]['index'],0)
 def test_real_supported202_is_provenance_only(self):self.assertEqual(self.f.consume()['record_id'],self.f.rid);self.assertNotIn('certifies',self.f.consume())
 def test_context_shape_phase_source_and_fakepass_mustfail(self):
  for key,value in [('standard','OLD'),('phase','DRAFT'),('producer_sha256','a'*64),('status','PASS'),('native_audit',{'status':'PASS'})]:
   with self.subTest(key=key):
    f=StateFixture();self.addCleanup(f.close);f.context[key]=value;self.assertRaises(ValueError,f.consume)
 def test_every_missing_source_role_mustfail(self):
  for key in p.ROLES:
   with self.subTest(key=key):
    f=StateFixture();self.addCleanup(f.close);f.context['source_bindings'].pop(key);self.assertRaises(ValueError,f.consume)
 def test_bytes_or_hash_change_mustfail(self):Path(self.f.roles['source_native_receipt']['path']).write_bytes(b'{}');self.assertRaises(ValueError,self.f.consume)
 def test_evidence_context_source_disagreement_mustfail(self):self.f.evidence['own_publish_receipt']=self.f.roles['creation_receipt'];self.assertRaises(ValueError,self.f.consume)
 def test_stale_equalbytes_prefinal_get_mustfail(self):
  q=self.f.root/'transport/023_GET.json';q.write_bytes(Path(self.f.roles['before_publish_native_receipt']['path']).read_bytes());self.f.context['source_bindings']['before_publish_native_receipt']={'path':str(q),'sha256':d.sha(q)};self.assertRaises(ValueError,self.f.consume)
 def test_own_identity_parent_doi_phase_and_receipt_contract_mustfails(self):
  cases=[('creation_receipt',lambda x:x['response'].__setitem__('conceptrecid','123456')),('reservation_receipt',lambda x:x['response'].__setitem__('id','123456')),('reservation_receipt',lambda x:x.__setitem__('accept','application/json')),('publish_receipt',lambda x:x['response'].__setitem__('conceptrecid','123456')),('publish_receipt',lambda x:x['response'].__setitem__('state','inprogress')),('publish_receipt',lambda x:x.__setitem__('http_status',True)),('publish_receipt',lambda x:x.__setitem__('http_status',None)),('publish_receipt',lambda x:x.__setitem__('request_body_sha256',None)),('before_publish_native_receipt',lambda x:x['response'].__setitem__('is_draft',False)),('source_native_receipt',lambda x:x['response'].__setitem__('id',self.f.rid)),('source_native_receipt',lambda x:x['response']['pids']['doi'].__setitem__('identifier','10.5281/zenodo.123456'))]
  for i,(role,fn) in enumerate(cases):
   with self.subTest(i=i):
    f=StateFixture();self.addCleanup(f.close);f.change(role,fn);self.assertRaises(ValueError,f.consume)
 def test_every_closed_nonpreview_link_wrongvalue_mustfail(self):
  for key in p.canonical_links('21971052','21968382'):
   with self.subTest(key=key):
    f=StateFixture();self.addCleanup(f.close);f.change('source_native_receipt',lambda x:x['response']['links'].__setitem__(key,'https://foreign.test/unknown'));self.assertRaises(ValueError,f.consume)
 def test_unknown_source_link_mustfail(self):self.f.change('source_native_receipt',lambda x:x['response']['links'].__setitem__('unknown','https://zenodo.org/api/records/21971052'));self.assertRaises(ValueError,self.f.consume)
 def test_source_credentials_protocol_port_query_mustfail(self):
  for url in ['https://u@zenodo.org/api/records/21971052','https://zenodo.org:443/api/records/21971052','http://zenodo.org/api/records/21971052','https://zenodo.org/api/records/21971052?extra=1']:
   with self.subTest(url=url):
    f=StateFixture();self.addCleanup(f.close);f.change('source_native_receipt',lambda x:x['response']['links'].__setitem__('self',url));self.assertRaises(ValueError,f.consume)
 def test_community_and_other_customfield_mustfails(self):
  cases=[('before_publish_native_receipt',lambda x:x['response']['custom_fields'].__setitem__('other:claim','PASS')),('before_publish_native_receipt',lambda x:x['response'].__setitem__('custom_fields',{})),('before_publish_native_receipt',lambda x:x['response']['parent'].__setitem__('communities',self.f.native['parent']['communities'])),('source_native_receipt',lambda x:x['response']['parent']['communities']['entries'][0].__setitem__('slug','wrong')),('source_native_receipt',lambda x:x['response']['parent']['communities']['entries'][0].__setitem__('id','wrong')),('source_native_receipt',lambda x:x['response']['parent']['communities']['ids'].append(UUID)),('source_native_receipt',lambda x:x['response']['parent']['communities'].__setitem__('default','wrong'))]
  for i,(role,fn) in enumerate(cases):
   with self.subTest(i=i):
    f=StateFixture();self.addCleanup(f.close);f.change(role,fn);self.assertRaises(ValueError,f.consume)
 def test_public_membership_changed_duplicate_empty_mustfails(self):
  for value in [[],[{'id':'other'}],[{'id':'viridis-canon'},{'id':'viridis-canon'}]]:
   with self.subTest(value=value):
    f=StateFixture();self.addCleanup(f.close);f.public['communities']=value;self.assertRaises(ValueError,f.consume)
 def test_tested_mirror_proof_all_decisive_conditions_mustfail(self):
  cases=[lambda x:x.pop('condition'),lambda x:x.__setitem__('condition','any community is allowed'),lambda x:x.pop('public_post_publish_exact_preservation'),lambda x:x.__setitem__('public_post_publish_exact_preservation',False),lambda x:x.__setitem__('production_writes_in_test',1),lambda x:x.__setitem__('production_writes_in_test',False),lambda x:x.__setitem__('before_custom_fields',{'legacy:communities':['wrong']}),lambda x:x.__setitem__('after_custom_fields',{'legacy:communities':['wrong']}),lambda x:x.__setitem__('transport_sha256',None)]
  cases += [lambda x,key=k:x['checks'].__setitem__(key,False) for k in mirror_proof()['checks']]
  for i,fn in enumerate(cases):
   with self.subTest(i=i):
    f=StateFixture();self.addCleanup(f.close);f.change('mirror_proof',fn);self.assertRaises(ValueError,f.consume)
 def test_source_index_missing_bool_noninteger_wrong_offset_parent_mustfails(self):
  cases=[('source_native_receipt',lambda x,value=v:x['response']['versions'].__setitem__('index',value)) for v in [None,True,1.0,'2',0,-1]]
  cases += [('source_legacy_receipt',lambda x,value=v:x['response']['metadata']['relations']['version'][0].__setitem__('index',value)) for v in [2,0,True,1.0,'1',None]]
  cases += [('source_legacy_receipt',lambda x:x['response']['metadata'].pop('relations')),('source_legacy_receipt',lambda x:x['response']['metadata']['relations']['version'][0]['parent'].__setitem__('pid_value','123456')),('source_legacy_receipt',lambda x:x['response']['metadata']['relations']['version'][0].__setitem__('is_last',False)),('before_publish_native_receipt',lambda x:x['response']['versions'].__setitem__('index',True))]
  for i,(role,fn) in enumerate(cases):
   with self.subTest(i=i):
    f=StateFixture();self.addCleanup(f.close);f.change(role,fn);self.assertRaises(ValueError,f.consume)
 def test_source_preview_can_be_absent(self):
  for role in ['source_legacy_receipt','source_native_receipt']:self.f.change(role,lambda x:x['response']['links'].pop('thumbnails'))
  self.assertEqual(self.f.consume()['native']['links']['thumbnails'],self.f.before['links']['thumbnails'])

if __name__=='__main__':unittest.main()

def complete_registration_fixture(f,old,native):
 """Upgrade the existing synthetic fixture to a real-shaped explicit lifecycle.

Existing certificate, package, parity and download cases remain unchanged.
The fixture's fake native auditor still compares every scientific/content field.
"""
 sf=StateFixture()
 try:
  source_legacy=deepcopy(sf.legacy);source_legacy['metadata']=deepcopy(old['metadata']);source_legacy['metadata']['relations']=deepcopy(sf.legacy['metadata']['relations'])
  source_native=deepcopy(sf.native);source_native.update({k:deepcopy(v)for k,v in native.items() if k not in {'id','pids'}})
  source_native['pids']=deepcopy(sf.native['pids'])
  before=deepcopy(sf.before);before['metadata']=deepcopy(f.expected_native['metadata']);before['files']['entries']={row['key']:{**deepcopy(row),'id':f'00000000-0000-4000-8000-{i:012d}','links':{}}for i,row in enumerate(f.legacy['files'],1)}
  before['files'].update(count=6,total_bytes=sum(x['size']for x in before['files']['entries'].values()),enabled=True,order=[])
  roles={'source_legacy_receipt':receipt(f.root/'source_legacy.json','GET','https://zenodo.org/api/records/'+sf.native['id'],source_legacy),'source_native_receipt':receipt(f.root/'source_native.json','GET','https://zenodo.org/api/records/'+sf.native['id'],source_native,p.NATIVE_ACCEPT),'before_publish_native_receipt':receipt(f.root/'transport/027_GET.json','GET','https://zenodo.org/api/records/'+f.rid+'/draft',before,p.NATIVE_ACCEPT),'creation_receipt':receipt(f.root/'create.json','POST','https://zenodo.org/api/deposit/depositions',sf.created,code=201),'reservation_receipt':receipt(f.root/'reserve.json','POST','https://zenodo.org/api/records/'+f.rid+'/draft/pids/doi',sf.reserved,p.NATIVE_ACCEPT,201),'publish_receipt':receipt(f.root/'transport/028_POST.json','POST','https://zenodo.org/api/deposit/depositions/'+f.rid+'/actions/publish',sf.published,code=202),'mirror_proof':save(f.root/'mirror.json',mirror_proof())}
  context=p.assemble_context(record_id=f.rid,**roles)
  e={'source_legacy_receipt':roles['source_legacy_receipt'],'source_native_receipt':roles['source_native_receipt'],'own_publish_receipt':roles['publish_receipt']}
  pred=p.consume_context(context,load=lambda binding:json.loads(d.bound_file(f.root,binding)[1]),public=f.public,evidence_sources=e)
  f.expected_native=pred['native'];actual=deepcopy(f.expected_native);actual['versions']['is_latest']=True;actual['pids']['oai']={'identifier':'oai:zenodo.org:'+f.rid,'provider':'oai'}
  f.actual_native=actual;f.legacy=p.predict_legacy(source_legacy,actual,f.public);f.legacy['metadata']['relations']=pred['legacy_relation']
  f.e.update(e);f.e.update(public_native_receipt=receipt(f.root/'public_native.json','GET','https://zenodo.org/api/records/'+f.rid,actual,p.NATIVE_ACCEPT),public_legacy_receipt=receipt(f.root/'public_legacy.json','GET','https://zenodo.org/api/records/'+f.rid,f.legacy),expected_native=save(f.root/'expected_native.json',f.expected_native),expected_legacy=save(f.root/'expected_legacy.json',f.legacy),public_state_context=save(f.root/'public_state_context.json',context))
 finally:sf.close()

class RealAuditContractTests(unittest.TestCase):
 def setUp(self):
  from test_server_managed_fields import ServerManagedFieldsTests
  import server_managed_fields as sm
  self.sm=sm;self.case=ServerManagedFieldsTests('runTest');self.case.setUp();self.addCleanup(self.case.doCleanups)
  self.report=self.case.check()
 def test_real_default_server_terminal_and_complete_named_rows(self):
  self.assertEqual(self.report['status'],'SERVER_MANAGED_READBACK_PASS');p.require_native_audit(self.report,record_id='1001',sm=self.sm)
 def test_genericpass_terminal_holding_reason_wrongid_or_phase_mustfail(self):
  for key,value in [('status','PASS'),('record_id','1002'),('phase','DRAFT'),('operation','AMENDMENT'),('reasons',['unexpected'])]:
   with self.subTest(key=key):
    r=deepcopy(self.report);r[key]=value;self.assertRaises(ValueError,p.require_native_audit,r,record_id='1001',sm=self.sm)
 def test_every_named_row_missing_or_hold_mustfail(self):
  for name in self.report['checks']:
   for change in ['missing','hold']:
    with self.subTest(name=name,change=change):
     r=deepcopy(self.report)
     if change=='missing':r['checks'].pop(name)
     else:r['checks'][name]['status']='HOLD'
     self.assertRaises(ValueError,p.require_native_audit,r,record_id='1001',sm=self.sm)
 def test_unknown_fakepass_row_mustfail(self):
  r=deepcopy(self.report);r['checks']['made_up']={'status':'PASS'};self.assertRaises(ValueError,p.require_native_audit,r,record_id='1001',sm=self.sm)
 def legacy_pair(self):
  f=StateFixture();self.addCleanup(f.close)
  n=deepcopy(self.case.expected);n['parent']['access']={'owned_by':{'user':'3974'}}
  n['links']=p.canonical_links('1001','77');n['links'].pop('thumbnails')
  entries={v['key']:deepcopy(v)for v in n['files']};n['files']={'entries':entries,'count':6,'total_bytes':sum(v['size']for v in entries.values()),'enabled':True,'order':[]}
  self.case.expected=deepcopy(n);self.case.actual=deepcopy(n);self.case.context['revision_evidence']=self.case.evidence(native=n)
  context=deepcopy(self.case.context);context.pop('host');context.pop('record_id');context.update(operation='NEW_VERSION',phase='PUBLISHED')
  m=deepcopy(n['metadata']);e=p.predict_legacy(f.legacy,n,m);e['metadata']['relations']=p.legacy_relation(f.legacy,f.native,n)
  return f,n,e,context
 def check_legacy(self,n,e,a,ctx,f):
  import publication_preservation as preservation
  return p.require_legacy(a,e,n,source_legacy=f.legacy,source_native=f.native,sm=self.sm,preservation=preservation,native_expected=self.case.expected,server_context=ctx)
 def test_legacy_file_projection_is_deterministic_across_native_entry_order(self):
  f,n,e,ctx=self.legacy_pair();rows=n['files']['entries'];base=deepcopy(next(iter(rows.values())))
  for i,key in enumerate(['paper.tex','metadata.json','METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json']):
   row=deepcopy(base);row.update(key=key,id='row-'+str(i));rows[key]=row
  forward=p.predict_legacy(f.legacy,n,n['metadata']);other=deepcopy(n);other['files']['entries']=dict(reversed(list(rows.items())))
  reverse=p.predict_legacy(f.legacy,other,n['metadata']);self.assertTrue(p.exact(forward,reverse));self.assertEqual([row['key']for row in forward['files']],sorted(rows));self.assertEqual({row['key']:row for row in forward['files']},{row['key']:row for row in reverse['files']})
  changed=deepcopy(other);changed['files']['entries']['paper.tex']['checksum']='md5:'+'f'*32
  self.assertFalse(p.exact(forward,p.predict_legacy(f.legacy,changed,n['metadata'])))
 def test_real_full_native_reaudit_and_complete_legacy_without_parent_url_bypass(self):
  f,n,e,ctx=self.legacy_pair();self.assertEqual(self.check_legacy(n,e,e,ctx,f)['status'],'STRICT_COMPLETE_PUBLIC_LEGACY_PASS')
 def test_legacy_submitted_revision_bool_number_type_mustfail(self):
  f,n,e,ctx=self.legacy_pair()
  for key,value in [('submitted',1),('revision',True)]:
   with self.subTest(key=key):
    a=deepcopy(e);a[key]=value;self.assertRaises(ValueError,self.check_legacy,n,e,a,ctx,f)
 def test_native_metadata_pid_main_checksum_fail_before_legacy_coupling(self):
  f,n,e,ctx=self.legacy_pair()
  cases=[lambda a:a['metadata'].__setitem__('description','stronger claim'),lambda a:a['pids']['doi'].__setitem__('identifier','10.5281/zenodo.9999'),lambda a:a['files']['entries']['file-0.txt'].__setitem__('checksum','md5:'+'f'*32)]
  for i,fn in enumerate(cases):
   with self.subTest(i=i):
    a=deepcopy(n);fn(a);self.assertRaises(ValueError,self.check_legacy,a,e,e,ctx,f)
 def test_legacy_wrong_links_parent_unknown_mainfile_or_science_mustfail(self):
  f,n,e,ctx=self.legacy_pair()
  from zenodo_transport import TransportHold
  cases=[(ValueError,lambda a:a['links'].__setitem__('parent','https://zenodo.org/api/records/88')),(ValueError,lambda a:a['links'].__setitem__('unknown','https://zenodo.org/api/records/1001')),(TransportHold,lambda a:a['files'][0].__setitem__('checksum','md5:'+'f'*32)),(TransportHold,lambda a:a['metadata'].__setitem__('description','stronger claim')),(ValueError,lambda a:a.__setitem__('unknown',True))]
  for i,(kind,fn) in enumerate(cases):
   with self.subTest(i=i):
    a=deepcopy(e);fn(a);self.assertRaises(kind,self.check_legacy,n,e,a,ctx,f)
 def test_fake_context_prior_or_foreign_own_publish_mustfail(self):
  f,n,e,ctx=self.legacy_pair()
  for value in ['PRIOR_VERSION','AMENDMENT']:
   c=deepcopy(ctx);c['operation']=value;self.assertRaises(ValueError,self.check_legacy,n,e,e,c,f)
  c=deepcopy(ctx);c['same_operation_reservation_id']='1002';self.assertRaises(ValueError,self.check_legacy,n,e,e,c,f)

class SourcePreservationTests(unittest.TestCase):
 def functions(self,path):
  import ast
  raw=path.read_text();return {n.name:ast.get_source_segment(raw,n)for n in ast.parse(raw).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 def test_original_draft_and_all_registration_science_parity_preservation_bodies_exact(self):
  here=Path(__file__).parent;old=self.functions(here/'testdata/digest_public_state/methods_digest_registration_v1.txt');new=self.functions(here/'methods_digest_registration.py')
  for name,body in old.items():
   if name not in {'assemble_evidence','_check_public'}:
    with self.subTest(name=name):self.assertEqual(new[name],body)
 def test_runtimehelper_only_closed_exactnamed_module_addition(self):
  import ast,hashlib
  here=Path(__file__).parent;old=(here/'testdata/digest_public_state/phase7_runtime_update_before.txt').read_text();new=(here/'phase7_runtime_update.py').read_text()
  pins={'audit_section': '3c9ca762aafde21e0a90c8f0e3d482436efda6a76222c703af6820842b23b578', 'corpus_preservation': '6141a5d6f94d0a61394b8ff1aed5276d46e10ee03077f7f1d533127f65357ab9'}
  def split_functions(raw):
   lines=raw.splitlines(keepends=True);tree=ast.parse(raw);functions={n.name:ast.get_source_segment(raw,n)for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};excluded=set()
   for node in tree.body:
    if isinstance(node,ast.FunctionDef)and node.name in pins:excluded.update(range(node.lineno-1,node.end_lineno))
   return functions,''.join(v for i,v in enumerate(lines)if i not in excluded)
  previous,outside=split_functions(old)
  expected=outside.replace("'phase7_policy_versions.py',\n})","'phase7_policy_versions.py', 'digest_public_state.py', 'registration_imports.py',\n    'digest_public_state_legacy_b5545.py', 'digest_successor_state.py', 'first_digest_state.py',\n})",1)
  self.assertNotEqual(expected,outside)
  def namespace_and_remaining(raw):
   lines=raw.splitlines(keepends=True);tree=ast.parse(raw);rows=[n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='POLICY_MODULE_NAMES'for t in n.targets)];self.assertEqual(len(rows),1);node=rows[0];self.assertIsInstance(node.value,ast.Call);self.assertIsInstance(node.value.func,ast.Name);self.assertEqual(node.value.func.id,'frozenset');self.assertEqual(len(node.value.args),1);self.assertEqual(node.value.keywords,[]);names=ast.literal_eval(node.value.args[0]);self.assertIsInstance(names,set);self.assertTrue(all(type(v)is str for v in names));return names,''.join(v for i,v in enumerate(lines)if not node.lineno-1<=i<node.end_lineno)
  oldnames,expectedoutside=namespace_and_remaining(expected);expectednames=oldnames|{'digest_weekly_state.py','nightly_minimal_policy.py'}
  def closed(candidate):
   current,remaining=split_functions(candidate);names,other=namespace_and_remaining(remaining);self.assertEqual(names,expectednames);self.assertEqual(other,expectedoutside);self.assertEqual(set(current),set(previous))
   for name,body in previous.items():
    if name not in pins:self.assertEqual(current[name],body)
   for name,pin in pins.items():self.assertEqual(hashlib.sha256(current[name].encode()).hexdigest(),pin)
  closed(new)
  # All five reviewed additions are closed: removal or replacement of any
  # one fails without relaxing the original function/global byte checks.
  additions=('digest_public_state_legacy_b5545.py','digest_successor_state.py','first_digest_state.py','digest_weekly_state.py','nightly_minimal_policy.py')
  for name in additions:
   self.assertEqual(new.count("'"+name+"'"),1)
   for candidate in (new.replace("'"+name+"'", "'foreign_unreviewed.py'",1),new.replace("'"+name+"', ","",1),new.replace("'"+name+"',\n","\n",1)):
    if candidate!=new:
     with self.subTest(closed_name=name),self.assertRaises(AssertionError):closed(candidate)
  for before,after in [("'registration_imports.py'","'unknown_imports.py'"),("CORPUS_SHA256 =","CHANGED_CORPUS_SHA256 ="),("raw = normalize_authority_plan(raw)","raw = raw"),("exact approved import caller/alias body required","body bypass")]:
   self.assertIn(before,new)
   with self.subTest(change=before),self.assertRaises(AssertionError):closed(new.replace(before,after,1))

class PreviewAndOaiPredictionTests(unittest.TestCase):
 setUp=PublicStateTests.setUp
 def test_before_absent_never_fabricates_source_thumbnail(self):
  self.f.change('before_publish_native_receipt',lambda x:x['response']['links'].pop('thumbnails'));self.assertNotIn('thumbnails',self.f.consume()['native']['links'])
 def test_before_foreign_thumbnail_rejected(self):
  from zenodo_transport import TransportHold
  self.f.change('before_publish_native_receipt',lambda x:x['response']['links']['thumbnails'].__setitem__('250','https://zenodo.org/api/iiif/record:123456:paper.pdf/full/250,/0/default.jpg'));self.assertRaises(TransportHold,self.f.consume)
 def test_before_wrong_source_key_thumbnail_rejected(self):
  from zenodo_transport import TransportHold
  self.f.change('before_publish_native_receipt',lambda x:x['response']['links']['thumbnails'].__setitem__('250','https://zenodo.org/api/iiif/record:999999:other.pdf/full/250,/0/default.jpg'));self.assertRaises(TransportHold,self.f.consume)
 def test_before_noncanonical_but_alreadyapproved_owned_preview_is_copied(self):
  self.f.change('before_publish_native_receipt',lambda x:x['response']['links'].__setitem__('thumbnails',{'small':'https://zenodo.org/api/iiif/record:999999:paper.pdf/full/max/0/default.jpg'}));self.assertEqual(self.f.consume()['native']['links']['thumbnails'],{'small':'https://zenodo.org/api/iiif/record:999999:paper.pdf/full/max/0/default.jpg'})
 def test_source_oai_bad_provider_or_ownid_rejected(self):
  for key,value in [('provider','other'),('identifier','oai:zenodo.org:123456')]:
   with self.subTest(key=key):
    f=StateFixture();self.addCleanup(f.close);f.change('source_native_receipt',lambda x:x['response']['pids']['oai'].__setitem__(key,value));self.assertRaises(ValueError,f.consume)
 def test_source_without_oai_doesnot_invent_mint(self):
  self.f.change('source_native_receipt',lambda x:x['response']['pids'].pop('oai'));self.assertNotIn('oai',self.f.consume()['native']['pids'])
 def test_existing_own_doi_changed_rejected(self):self.f.change('before_publish_native_receipt',lambda x:x['response']['pids']['doi'].__setitem__('identifier','10.5281/zenodo.123456'));self.assertRaises(ValueError,self.f.consume)
 def test_copied_boolean_proof_checks_rejected(self):self.f.change('mirror_proof',lambda x:x['checks'].__setitem__('doi',1));self.assertRaises(ValueError,self.f.consume)

class RealLegacyPreviewTests(unittest.TestCase):
 setUp=RealAuditContractTests.setUp
 check_legacy=RealAuditContractTests.check_legacy
 def pair(self,appear=False):
  f=StateFixture();self.addCleanup(f.close);expected,actual,preview=self.case.preview_fixture()
  expected['parent']['access']={'owned_by':{'user':'3974'}};expected['links']=p.canonical_links('1001','77');expected['links'].pop('thumbnails');actual=deepcopy(expected)
  if appear:actual['links']['thumbnails']={'small':'https://zenodo.org/api/iiif/record:1001:paper.pdf/full/max/0/default.jpg'}
  self.case.expected=expected;self.case.actual=actual;self.case.context['revision_evidence']=self.case.evidence(native=actual)
  ctx=deepcopy(self.case.context);ctx.pop('host');ctx.pop('record_id');ctx.update(operation='NEW_VERSION',phase='PUBLISHED',derived_preview_context=preview)
  legacy=p.predict_legacy(f.legacy,actual,actual['metadata']);legacy['metadata']['relations']=p.legacy_relation(f.legacy,f.native,actual)
  return f,actual,legacy,ctx
 def test_before_absent_public_absent_full_legacy_guards_pass(self):
  f,n,e,ctx=self.pair();self.assertNotIn('thumbnails',n['links']);self.assertEqual(self.check_legacy(n,e,e,ctx,f)['status'],'STRICT_COMPLETE_PUBLIC_LEGACY_PASS')
 def test_before_absent_public_sourcebound_appearance_full_legacy_guards_pass(self):
  f,n,e,ctx=self.pair(True);self.assertEqual(e['links']['thumbnails'],n['links']['thumbnails']);self.assertEqual(self.check_legacy(n,e,e,ctx,f)['status'],'STRICT_COMPLETE_PUBLIC_LEGACY_PASS')
 def test_appearance_foreign_preview_mainchecksum_or_sourceuuid_mustfail(self):
  f,n,e,ctx=self.pair(True)
  changes=[lambda a:a['links']['thumbnails'].__setitem__('small','https://zenodo.org/api/iiif/record:1002:paper.pdf/full/max/0/default.jpg'),lambda a:a['files']['entries']['paper.pdf'].__setitem__('checksum','md5:'+'f'*32),lambda a:a['files']['entries']['paper.pdf'].__setitem__('id','foreign')]
  for i,fn in enumerate(changes):
   with self.subTest(i=i):
    bad=deepcopy(n);fn(bad);self.assertRaises(ValueError,self.check_legacy,bad,e,e,ctx,f)
 def test_legacy_preview_must_equal_fully_checked_native(self):
  f,n,e,ctx=self.pair(True);bad=deepcopy(e);bad['links']['thumbnails']['small']='https://zenodo.org/api/iiif/record:1002:paper.pdf/full/max/0/default.jpg';self.assertRaises(ValueError,self.check_legacy,n,e,bad,ctx,f)
