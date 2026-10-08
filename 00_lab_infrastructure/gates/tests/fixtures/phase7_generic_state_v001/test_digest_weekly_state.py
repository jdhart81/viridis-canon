"""Generic constructors/discovery unit fixtures only, never live admission."""
from pathlib import Path
from copy import deepcopy
import ast,hashlib,importlib.util,json,sys,tempfile,types,unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
OLD=HERE/'test_fixtures'
G=HERE
sys.path[:0]=[str(HERE),str(OLD)]
import digest_weekly_state as w
import digest_public_state as dispatch
import digest_public_state_legacy_b5545 as old
import digest_successor_state as previous
import methods_digest as d
from fixture_successor import InitialCreationTests,CompleteContextTests,SuccessorFixture
class GenericTests(CompleteContextTests):
 def fixture_context(self):
  root,c,public,e,load,a=self.context_fixture()
  c['standard']=w.STANDARD;c['producer_sha256']=w.source_sha()
  first=c['source_bindings']['first_own_native_draft'];obj=load(first);obj['response']['pids']={};Path(first['path']).write_bytes(d.raw_json(obj));first['sha256']=d.sha(first['path'])
  b=c['source_bindings']['successor_digest_manifest'];m=json.loads(Path(b['path']).read_bytes());m['notes']=[{'run_id':'Run-189'}];Path(b['path']).write_bytes(d.raw_json(m));b['sha256']=d.sha(b['path'])
  contextfile=root/'priorpubliccontext.json';contextfile.write_bytes(d.raw_json({'standard':old.STANDARD}))
  evidence=root/'priorpublicevidence.json';evidence.write_bytes(d.raw_json({'public_state_context':{k:d.binding(contextfile)[k]for k in('path','sha256')}}));a['receipt']['public_evidence']={k:d.binding(evidence)[k]for k in('path','sha256')}
  return root,c,public,e,load,a
 def generic(self,root,c,public,e,load,a):
  with patch('methods_digest_registration.require_registration',return_value=a):return w.consume_context(c,load=load,public=public,evidence_sources=e,root=root)
 def test_generic_sameweek_run189_retains_parent_plusone_and_all_source_fields(self):
  root,c,public,e,load,a=self.fixture_context();v=self.generic(root,c,public,e,load,a);self.assertEqual(v['record_id'],'999999');self.assertEqual(v['native']['versions']['index'],2);self.assertEqual(v['native']['parent']['id'],v['source_native']['parent']['id']);self.assertEqual(v['native']['metadata'],v['before_native']['metadata']);self.assertNotIn('status',v)
 def test_ancestral_duplicate_new_claim_or_changed_week_or_title_hold(self):
  for mutation in['collision','duplicate','week','title']:
   root,c,pub,e,load,a=self.fixture_context();b=c['source_bindings']['successor_digest_manifest'];m=json.loads(Path(b['path']).read_bytes())
   if mutation=='collision':m['notes']=[{'run_id':'Run-125'}]
   elif mutation=='duplicate':m['notes']*=2
   elif mutation=='week':m['release_week']='2026-W42'
   else:m['public_metadata']['title']='New science title';pub['title']='New science title'
   Path(b['path']).write_bytes(d.raw_json(m));b['sha256']=d.sha(b['path']);self.assertRaises(ValueError,self.generic,root,c,pub,e,load,a)
 def test_wrong_genuine_source_pair_firstchecksum_or_publishurl_hold(self):
  for role,key,val in[('source_native_before_create','id','888888'),('first_own_native_draft','metadata',{'title':'Stronger physics'}),('publish_receipt','url','https://zenodo.org/api/deposit/depositions/1/actions/publish')]:
   root,c,pub,e,load,a=self.fixture_context();b=c['source_bindings'][role];o=json.loads(Path(b['path']).read_bytes());target=o if key=='url'else o['response'];target[key]=val;Path(b['path']).write_bytes(d.raw_json(o));b['sha256']=d.sha(b['path']);self.assertRaises(ValueError,self.generic,root,c,pub,e,load,a)
 def test_old49_producer_identity_and_source_bytes_unchanged(self):self.assertEqual(previous.source_sha(),'11a173b3781301cb6070ebc5d37763f5aca8558972351abfb2cf546c73369567');self.assertNotEqual(w.source_sha(),previous.source_sha())
 def test_dispatcher_oldprefix_and_all_first_definitions_byteexact(self):
  before=(HERE/'BEFORE_digest_public_state.py').read_text();after=(HERE/'digest_public_state.py').read_text();self.assertTrue(after.startswith(before));oldnodes=[n for n in ast.parse(before).body if isinstance(n,ast.FunctionDef)];newnodes=[n for n in ast.parse(after).body if isinstance(n,ast.FunctionDef)]
  self.assertEqual(len(newnodes[:len(oldnodes)]),len(oldnodes))
  for oldnode,newnode in zip(oldnodes,newnodes):
   self.assertEqual(oldnode.name,newnode.name);self.assertEqual(ast.get_source_segment(before,oldnode),ast.get_source_segment(after,newnode))
 def test_old_context_is_routed_to_unchanged_old_consumer(self):
  with patch.object(dispatch,'_consume_context_49_original',return_value={'old':'unit_route'})as fn:
   self.assertEqual(dispatch.consume_context({'standard':previous.STANDARD},load=None,public={},evidence_sources={}),{'old':'unit_route'});fn.assert_called_once()
 def test_newcontext_closed_dispatch_routes_only_newstandards(self):
  for standard in[w.STANDARD,w.FIRST_WEEK_STANDARD]:
   with patch.object(w,'consume_context',return_value={'constructor':'not acceptance'})as fn:self.assertEqual(dispatch.consume_context({'standard':standard},load=None,public={},evidence_sources={}),{'constructor':'not acceptance'});fn.assert_called_once()
 def test_source_no_purpose_engine_network_or_proof_execution_dependencies(self):
  text=(HERE/'digest_weekly_state.py').read_text()
  for forbidden in['import owned_digest','import owned_weekly','urlopen(', 'subprocess','local_lean_fallback','issue_lean_zero_sorry_certificate(']:self.assertNotIn(forbidden,text)
class LineageTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(prefix='lineagefixture-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.serial=0
 def saved(self,v):
  self.serial+=1;p=self.root/f'{self.serial}.json';p.write_bytes(d.raw_json(v));return{k:d.binding(p)[k]for k in('path','sha256')}
 def admitted(self,rid,runs,standard,predecessor=None,week='2026-W41'):
  context={'standard':standard,'source_bindings':{'predecessor_registration':predecessor}};return{'receipt':{'record_id':rid,'release_week':week,'children':[{'run_id':r}for r in runs],'public_evidence':self.saved({'public_state_context':self.saved(context)})}}
 def test_all_old7_old49_and_current_ancestors_are_default_reconsumed(self):
  a=self.admitted('23226761',['Run-125'],old.STANDARD);bind_a=self.saved({'unit':'registration A'});b=self.admitted('23300000',['Run-127'],previous.STANDARD,bind_a);bind_b=self.saved({'unit':'registration B'});c=self.admitted('23400000',['Run-189'],w.STANDARD,bind_b)
  def consume(root,value):return a if value==bind_a else b
  with patch('methods_digest_registration.require_registration',side_effect=consume)as fn:self.assertEqual(w.registered_lineage_runs(c,root=self.root),{'Run-125','Run-127','Run-189'});self.assertEqual(fn.call_count,2)
 def test_duplicate_ancestor_run_and_cycle_and_changed_week_hold(self):
  for changed in['duplicate','cycle','week','unknown']:
   a=self.admitted('23226761',['Run-125'],old.STANDARD);ba=self.saved({'fixture':'a'});b=self.admitted('23300000',['Run-127'],previous.STANDARD,ba)
   if changed=='duplicate':a['receipt']['children']=[{'run_id':'Run-127'}]
   elif changed=='cycle':a=b
   elif changed=='week':a['receipt']['release_week']='2026-W42'
   else:b=self.admitted('23300000',['Run-127'],'UNKNOWN',ba)
   with patch('methods_digest_registration.require_registration',return_value=a):self.assertRaises(ValueError,w.registered_lineage_runs,b,root=self.root)
class FirstWeekTests(InitialCreationTests):
 def initial(self):
  f,r,n=self.fixture();public={k:deepcopy(v)for k,v in f.legacy['metadata'].items()if k not in('doi','relations')};public.update(title='Viridis Methods Digest — 2026-W42',related_identifiers=[{'identifier':'10.5281/zenodo.22222222','relation':'isSupplementTo','scheme':'doi'}])
  f.native['metadata'].update(creators=[{'affiliations':[], 'person_or_org':{'family_name':'Hart','given_name':'Justin D.','identifiers':[],'name':'Hart, Justin D.','type':'personal'}}],rights=[{'id':'cc-by-4.0'}],resource_type={'id':'publication-preprint'},languages=[{'id':'eng'}])
  f.native['access']={'record':'public','files':'public','status':'open','embargo':{'active':False,'reason':None}}
  f.native['metadata']['related_identifiers']=[{'identifier':'10.5281/zenodo.22222222','relation_type':{'id':'issupplementto','title':{'en':'Is supplement to'}},'scheme':'doi'}]
  n['pids']={}
  r['url']='https://zenodo.org/api/deposit/depositions';created=r['response'];created.pop('conceptdoi');created['conceptrecid']='999997';created['files']=[];created['title']=public['title'];created['links']['latest_draft']='https://zenodo.org/api/deposit/depositions/'+str(created['id'])
  from first_digest_state import encode_api_communities,private_metadata_expected
  from digest_metadata import closed_payload,native_metadata
  source={k:v for k,v in f.legacy['metadata'].items()if k not in('doi','relations')};payload=encode_api_communities(closed_payload(public,source));nm=native_metadata(public,source,f.legacy,f.native,f.native['metadata']['related_identifiers'][0]['relation_type'])
  # This mirrors a hypothetical genuine201ACK fixture; it is not evidence of a
  # live own CREATE. The constructor still consumes every exact ACK field.
  created['metadata']=private_metadata_expected(payload,created,nm)
  return f,r,n,public
 def test_firstweek_only_new_ids_and_ordinal_one_source_derived_science(self):
  f,r,n,pub=self.initial();v,l=w.first_week_projection(f.legacy,f.native,r,r['response'],n,pub);self.assertEqual(v['versions']['index'],1);self.assertEqual(v['parent']['id'],'999997');self.assertEqual(v['metadata']['title'],pub['title']);self.assertEqual(v['files']['entries'],{});self.assertEqual(v['custom_fields'],{'legacy:communities':['viridis-canon']})
 def test_firstweek_science_parent_owner_unknowninherited_file_or_ackshape_hold(self):
  for fn in[lambda r,n,p:r['response']['metadata'].__setitem__('description','changed science'),lambda r,n,p:r['response'].__setitem__('conceptrecid','999998x'),lambda r,n,p:r['response'].__setitem__('owner',1),lambda r,n,p:r['response'].__setitem__('files',[{'filename':'oldproof.lean'}]),lambda r,n,p:r.__setitem__('http_status',200),lambda r,n,p:r['response'].__setitem__('unknown','extra'),lambda r,n,p:n.__setitem__('expires_at','2026-10-08T12:02:00Z')]:
   f,r,n,pub=self.initial();fn(r,n,pub);self.assertRaises(ValueError,w.first_week_projection,f.legacy,f.native,r,r['response'],n,pub)
 def test_firstweek_distinct_parent_community_equality_and_unknown_fields_hold(self):
  f,r,n,pub=self.initial();v,_=w.first_week_projection(f.legacy,f.native,r,r['response'],n,pub);custom,graph=w.first_week_community_fields(pub,f.legacy,f.native,v);self.assertEqual(custom,{});self.assertEqual(graph,f.native['parent']['communities']);self.assertEqual(dispatch.community_fields(pub,f.legacy,f.native,v),(custom,graph))
  for fn in[lambda x:x.__setitem__('custom_fields',{}),lambda x:x['parent'].__setitem__('communities',deepcopy(graph)),lambda x:x['parent']['access']['owned_by'].__setitem__('user','wrong')]:
   v0=deepcopy(v);fn(v0);self.assertRaises(ValueError,w.first_week_community_fields,pub,f.legacy,f.native,v0)

class FirstWeekContextTests(FirstWeekTests):
 def first_context(self):
  from test_digest_public_state import save,receipt,mirror_proof
  from test_weekly_account_discovery import Tests as AccountTests,record
  f,r,n,pub=self.initial();root=f.f.root;rid=f.f.rid;sid=f.native['id'];initial,fl=w.first_week_projection(f.legacy,f.native,r,r['response'],n,pub)
  before=deepcopy(initial);before['files']={'enabled':True,'count':6,'total_bytes':60,'order':[],'entries':{name:{'key':name,'id':f'00000000-0000-4000-8000-{i:012d}','size':10,'checksum':'md5:'+'a'*32,'links':{}}for i,name in enumerate(('paper.tex','paper.pdf','metadata.json','METHODS_NOTES.zip','DIGEST_MANIFEST.json','PUBLICATION_BINDING.json'),1)}}
  reserved={'id':rid,'parent':{'id':initial['parent']['id']},'pids':{'doi':{'identifier':'10.5281/zenodo.'+rid,'provider':'datacite','client':'datacite'}}};before['pids']=deepcopy(reserved['pids']);published=deepcopy(f.f.published);published.update(conceptrecid=initial['parent']['id'],conceptdoi='10.5281/zenodo.'+initial['parent']['id'])
  account=AccountTests('runTest');account.root=root;account.serial=0;proof=account.proof([record(sid,week='2026-W41',parent=f.native['parent']['id'])],week='2026-W42')
  roles={'source_legacy_receipt':receipt(root/'source_legacy.json','GET','https://zenodo.org/api/records/'+sid,f.legacy),'source_native_receipt':receipt(root/'source_native.json','GET','https://zenodo.org/api/records/'+sid,f.native,w.NATIVE_ACCEPT),'source_native_before_create':receipt(root/'source_precreate.json','GET','https://zenodo.org/api/records/'+sid,f.native,w.NATIVE_ACCEPT),'first_own_native_draft':receipt(root/'transport/003_GET.json','GET','https://zenodo.org/api/records/'+rid+'/draft',initial,w.NATIVE_ACCEPT),'first_own_legacy_draft':receipt(root/'transport/002_GET.json','GET','https://zenodo.org/api/deposit/depositions/'+rid,fl),'before_publish_native_receipt':receipt(root/'transport/027_GET.json','GET','https://zenodo.org/api/records/'+rid+'/draft',before,w.NATIVE_ACCEPT),'creation_receipt':save(root/'transport/001_POST.json',r),'reservation_receipt':receipt(root/'reserve.json','POST','https://zenodo.org/api/records/'+rid+'/draft/pids/doi',reserved,w.NATIVE_ACCEPT,201),'publish_receipt':receipt(root/'transport/028_POST.json','POST','https://zenodo.org/api/deposit/depositions/'+rid+'/actions/publish',published,code=202),'mirror_proof':save(root/'mirror.json',mirror_proof()),'account_discovery':save(root/'ACCOUNT_PROOF.json',proof),'successor_digest_manifest':save(root/'DIGEST.json',{'release_week':'2026-W42','public_metadata':pub,'notes':[{'run_id':'Run-189'}]})}
  relation=save(root/'REGISTERED_RELATION.json',f.native['metadata']['related_identifiers'][0]['relation_type']);registered_evidence=save(root/'REGISTERED_EVIDENCE.json',{'relation_template':relation});roles['metadata_source_registration']=save(root/'METADATA_SOURCE_REGISTRATION.json',{'unit_fixture_only':True})
  admitted={'receipt':{'record_id':sid,'release_week':'2026-W41','public_evidence':registered_evidence},'public_native':deepcopy(f.native),'public_legacy':deepcopy(f.legacy)}
  default=patch('methods_digest_registration.require_registration',return_value=admitted);default.start();self.addCleanup(default.stop)
  context=w.assemble_context(record_id=rid,start_kind='CREATE_WEEK',**roles);e={k:roles[k]for k in('source_legacy_receipt','source_native_receipt')};e['own_publish_receipt']=roles['publish_receipt']
  def load(b):return json.loads(d.bound_file(root,b)[1])
  return f,root,context,pub,e,load
 def apply(self,c,pub,e,load,root):return w.consume_context(c,load=load,public=pub,evidence_sources=e,root=root)
 def test_complete_firstweek_context_genuine_account_and_own_ids_no_admissionflag(self):
  f,root,c,pub,e,load=self.first_context();v=self.apply(c,pub,e,load,root);self.assertEqual(v['record_id'],f.f.rid);self.assertEqual(v['native']['versions']['index'],1);self.assertEqual(v['legacy_relation']['version'][0]['index'],0);self.assertEqual(len(v['native']['files']['entries']),6);self.assertEqual(v['native']['pids']['oai'],{'identifier':'oai:zenodo.org:'+f.f.rid,'provider':'oai'});self.assertEqual(v['native']['parent']['communities'],f.native['parent']['communities']);self.assertNotIn('status',v);self.assertNotIn('certifies',v)
 def test_firstweek_every_missing_role_and_evidence_substitution_hold(self):
  for role in w.FIRST_WEEK_ROLES:
   f,root,c,pub,e,load=self.first_context();c['source_bindings'].pop(role);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
  f,root,c,pub,e,load=self.first_context();e['own_publish_receipt']=c['source_bindings']['creation_receipt'];self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_firstweek_every_scientific_initial_and_beforefield_changes_hold(self):
  for role,key,value in[('first_own_native_draft','metadata',{'title':'stronger science'}),('first_own_native_draft','files',{'enabled':True,'entries':{'proof.lean':{}}}),('first_own_native_draft','parent',{'id':'123456'}),('first_own_native_draft','pids',{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'}}),('first_own_native_draft','access',{'record':'restricted'}),('first_own_native_draft','custom_fields',{}),('before_publish_native_receipt','metadata',{'description':'stronger claim'}),('before_publish_native_receipt','parent',{'id':'123456'}),('before_publish_native_receipt','pids',{}),('before_publish_native_receipt','custom_fields',{}),('before_publish_native_receipt','access',{'record':'restricted'})]:
   f,root,c,pub,e,load=self.first_context();b=c['source_bindings'][role];v=load(b);v['response'][key]=value;Path(b['path']).write_bytes(d.raw_json(v));b['sha256']=d.sha(b['path']);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_firstweek_changed_source_science_precreate_or_versionroles_hold(self):
  for role,key,value in[('source_native_before_create','metadata',{'title':'other'}),('source_native_before_create','versions',{'index':2,'is_latest':False}),('source_legacy_receipt','doi','10.5281/zenodo.1'),('publish_receipt','conceptrecid','123456'),('reservation_receipt','id','123456')]:
   f,root,c,pub,e,load=self.first_context();b=c['source_bindings'][role];v=load(b);v['response'][key]=value;Path(b['path']).write_bytes(d.raw_json(v));b['sha256']=d.sha(b['path']);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_firstweek_sameoperation_adjacent_finalget_required(self):
  f,root,c,pub,e,load=self.first_context();b=c['source_bindings']['before_publish_native_receipt'];p=Path(b['path']).with_name('023_GET.json');p.write_bytes(Path(b['path']).read_bytes());c['source_bindings']['before_publish_native_receipt']={'path':str(p),'sha256':d.sha(p)};self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_firstweek_wrong_week_title_duplicate_notes_and_unknown_proof_hold(self):
  for mutation in('week','duplicate','W41','fakePASS','unknown'):
   f,root,c,pub,e,load=self.first_context();role='successor_digest_manifest'if mutation in('week','duplicate')else'account_discovery';b=c['source_bindings'][role];v=load(b)
   if mutation=='week':v['release_week']='2026-W43'
   elif mutation=='duplicate':v['notes']*=2
   elif mutation=='W41':v['release_week']='2026-W41'
   elif mutation=='fakePASS':v['standard']='ACCOUNT_PASS'
   else:v['unchecked']=True
   Path(b['path']).write_bytes(d.raw_json(v));b['sha256']=d.sha(b['path']);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_firstweek_public_projection_reservation_links_ordinal_or_PIDs_hold(self):
  f,root,c,pub,e,load=self.first_context();v=self.apply(c,pub,e,load,root);before=v['before_native'];created=load(c['source_bindings']['creation_receipt'])['response'];reserve=load(c['source_bindings']['reservation_receipt'])['response'];published=load(c['source_bindings']['publish_receipt'])['response']
  for where,key,value in[('before','versions',{'index':2}),('before','pids',{}),('source','links',{'self':'https://foreign.test/'}),('reserve','id','123456'),('published','doi','10.5281/zenodo.1'),('published','conceptdoi','10.5281/zenodo.1')]:
   a,b,r,p=deepcopy(before),deepcopy(f.native),deepcopy(reserve),deepcopy(published);{'before':a,'source':b,'reserve':r,'published':p}[where][key]=value;self.assertRaises(ValueError,w.predict_first_week_native,pub,f.legacy,b,a,created,r,p)
 def test_firstweek_public_thumbnail_and_all_filefield_values_preserved(self):
  f,root,c,pub,e,load=self.first_context();v=self.apply(c,pub,e,load,root);before=v['before_native'];created=load(c['source_bindings']['creation_receipt'])['response'];reserve=load(c['source_bindings']['reservation_receipt'])['response'];published=load(c['source_bindings']['publish_receipt'])['response'];before['links']['thumbnails']={'250':'https://zenodo.org/api/records/'+f.f.rid+'/files/paper.pdf/preview?size=250'}
  predicted=w.predict_first_week_native(pub,f.legacy,f.native,before,created,reserve,published);self.assertEqual(predicted['links']['thumbnails'],before['links']['thumbnails'])
  for name,row in before['files']['entries'].items():self.assertEqual({k:v for k,v in predicted['files']['entries'][name].items()if k!='links'},{k:v for k,v in row.items()if k!='links'})
  for url in('https://foreign.test/preview','https://zenodo.org/api/records/123456/files/paper.pdf/preview?size=250','https://zenodo.org/api/records/'+f.f.rid+'/files/proof.lean/preview?size=250'):
   bad=deepcopy(before);bad['links']['thumbnails']['250']=url;from zenodo_transport import TransportHold;self.assertRaises(TransportHold,w.predict_first_week_native,pub,f.legacy,f.native,bad,created,reserve,published)

class ExactProducerPreservationTests(unittest.TestCase):
 def test_generic_sameweek_scientific_and_byte_codecs_remain_exact11a(self):
  before=(HERE/'test_fixtures/digest_successor_state.py').read_text();after=(HERE/'digest_weekly_state.py').read_text();bd={n.name:n for n in ast.parse(before).body if isinstance(n,ast.FunctionDef)};ad={}
  for n in ast.parse(after).body:
   if isinstance(n,ast.FunctionDef):ad.setdefault(n.name,n)
  for name in('community_fields','private_metadata_projection','_inherited','initial_newversion_projection','first_legacy_receipt_from_creation','inherited_download_spec','predict_native','require_mirror_proof'):self.assertEqual(ast.get_source_segment(before,bd[name]),ast.get_source_segment(after,ad[name]))
  oldbody=ast.get_source_segment(before,bd['predecessor_inventory']);newbody=ast.get_source_segment(after,ad['predecessor_inventory'])
  oldpredicate="admitted['receipt']['record_id']=='23226761'and admitted['receipt']['release_week']=='2026-W41'and{v['run_id']for v in admitted['receipt']['children']}==OLD_SEVEN,'exact default-admitted predecessor seven required'"
  newpredicate="admitted['receipt']['release_week']==plan['release_week'],'exact default-admitted same-week predecessor required'"
  self.assertIn(oldpredicate,oldbody);self.assertEqual(oldbody.replace(oldpredicate,newpredicate),newbody)
 def test_closed_raw_account_predicates_are_original_AST_under_only_named_renames(self):
  mapping={'source_sha':'_account_source_sha','need':'_account_need','raw':'_account_raw','bound':'_account_bound','decode_pass':'_account_decode_pass','discover':'_account_discover','require_discovery':'require_account_discovery','FIELDS':'_account_FIELDS','DiscoveryHold':'_account_DiscoveryHold','total':'_account_total','identity':'_account_identity','discovery_signature':'_account_discovery_signature','require_url':'_account_require_url','AccountHold':'_account_AccountHold','HOST':'_account_HOST','SIZE':'_account_SIZE'}
  class Names(ast.NodeTransformer):
   def visit_Name(self,n):n.id=mapping.get(n.id,n.id);return n
   def visit_FunctionDef(self,n):n.name=mapping.get(n.name,n.name);return self.generic_visit(n)
  target={n.name:n for n in ast.parse((HERE/'digest_weekly_state.py').read_text()).body if isinstance(n,ast.FunctionDef)}
  for filename,names in [('BEFORE_owned_weekly_discovery.py',('need','raw','bound','decode_pass','discover','require_discovery')),('BEFORE_readonly_account.py',('require_url','total','identity','discovery_signature'))]:
   text=(HERE/filename).read_text();original={n.name:n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)}
   for name in names:self.assertEqual(ast.dump(Names().visit(original[name]),include_attributes=False),ast.dump(target[mapping[name]],include_attributes=False))
 def test_pure_account_consumer_binds_exact_producer_not_itself_or_engine(self):
  self.assertEqual(hashlib.sha256((HERE/'BEFORE_owned_weekly_discovery.py').read_bytes()).hexdigest(),w.OWNED_DISCOVERY_PRODUCER_SHA);self.assertEqual(hashlib.sha256((HERE/'BEFORE_readonly_account.py').read_bytes()).hexdigest(),'daa36ca7fa4c40d923be5b411cf47463f5ef61162bf7fb6e50b6a27ebb638720');self.assertNotEqual(w._account_source_sha(),w.source_sha())
 def test_operation_assembly_absent_or_extra_kind_never_creates_ids(self):
  roles={k:{'path':'/private/tmp/fixture/'+k,'sha256':'a'*64}for k in w.ROLES};same=w.assemble_context(record_id='999999',**roles);self.assertEqual(same['standard'],w.STANDARD);self.assertRaises(ValueError,w.assemble_context,record_id='999999',start_kind='OTHER',**roles);roles['account_discovery']={'path':'/private/tmp/account.json','sha256':'a'*64};self.assertRaises(ValueError,w.assemble_context,record_id='999999',**roles)


class RegisteredVocabularyTests(FirstWeekTests):
 def vocab(self,*,empty=False):
  from test_digest_public_state import save
  f,r,n,pub=self.initial();root=f.f.root
  template=deepcopy(f.native['metadata']['related_identifiers'][0]['relation_type'])
  if empty:f.native['metadata'].pop('related_identifiers');f.legacy['metadata']['related_identifiers']=[]
  rb=save(root/'VOCAB.json',template);eb=save(root/'EVIDENCE.json',{'relation_template':rb});binding=save(root/'REG.json',{'unit_fixture_only':True})
  admitted={'receipt':{'record_id':f.native['id'],'release_week':'2026-W41','public_evidence':eb},'public_native':deepcopy(f.native),'public_legacy':deepcopy(f.legacy)}
  return f,r,n,pub,root,template,binding,rb,eb,admitted
 def apply_v(self,parts):
  f,r,n,pub,root,t,b,rb,eb,a=parts
  with patch('methods_digest_registration.require_registration',return_value=a):return w.registered_relation_template(b,root=root,source_native=f.native,source_legacy=f.legacy)
 def test_empty_scientific_relations_use_exact_bound_registered_vocabulary(self):
  p=self.vocab(empty=True);self.assertEqual(self.apply_v(p),p[5]);self.assertNotIn('related_identifiers',p[0].native['metadata'])
 def test_existing_source_vocabulary_is_byte_identical(self):
  p=self.vocab();self.assertEqual(self.apply_v(p),p[5])
 def test_registered_default_source_fields_identity_week_and_legacy_science_must_fail(self):
  for field,value in [('record_id','123456'),('release_week','2026-W40')]:
   p=self.vocab();p[-1]['receipt'][field]=value;self.assertRaises(ValueError,self.apply_v,p)
  for field,value in [('metadata',{'title':'changed claim'}),('files',{'entries':{}}),('pids',{}),('parent',{}),('access',{}),('custom_fields',{'legacy:communities':['other']}),('media_files',{'entries':{'proof.lean':{}}})]:
   p=self.vocab();p[-1]['public_native'][field]=value;self.assertRaises(ValueError,self.apply_v,p)
  p=self.vocab();p[-1]['public_legacy']['metadata']['description']='stronger claim';self.assertRaises(ValueError,self.apply_v,p)
 def test_missing_changed_hash_unbound_template_and_wrong_vocabulary_must_fail(self):
  for change in ['missing','hash','unbound','id','title','extra','source']:
   p=self.vocab();f,r,n,pub,root,t,b,rb,eb,a=p
   if change=='missing':Path(rb['path']).unlink()
   elif change=='hash':Path(rb['path']).write_bytes(b'changed')
   elif change=='unbound':a['receipt']['public_evidence']={'path':str(root/'NO.json'),'sha256':'a'*64}
   elif change=='source':f.native['metadata']['related_identifiers'][0]['relation_type']['title']['en']='Other'
   else:
    value=deepcopy(t)
    if change=='id':value['id']='isversionof'
    elif change=='title':value['title']['en']='Other'
    else:value['scientific_claim']='stronger'
    Path(rb['path']).write_bytes(d.raw_json(value));rb['sha256']=d.sha(rb['path']);Path(eb['path']).write_bytes(d.raw_json({'relation_template':rb}));eb['sha256']=d.sha(eb['path'])
   self.assertRaises((ValueError,FileNotFoundError),self.apply_v,p)
 def test_source_without_relations_constructs_no_spurious_relation(self):
  p=self.vocab(empty=True);f,r,n,pub,root,t,b,rb,eb,a=p;pub['related_identifiers']=[]
  from first_digest_state import encode_api_communities,private_metadata_expected
  from digest_metadata import native_metadata,closed_payload
  source={k:v for k,v in f.legacy['metadata'].items()if k not in('doi','relations')};nm=native_metadata(pub,source,f.legacy,f.native,t);r['response']['metadata']=private_metadata_expected(encode_api_communities(closed_payload(pub,source)),r['response'],nm)
  expected,_=w.first_week_projection(f.legacy,f.native,r,r['response'],n,pub,relation_template=self.apply_v(p));self.assertNotIn('related_identifiers',expected['metadata'])
 def test_relation_template_never_admits_unknown_or_wrong_existing_enum(self):
  f,r,n,pub=self.initial()
  for t in [{'id':'other','title':{'en':'Is supplement to'}},{'id':'issupplementto','title':{'en':'wrong'}},{'id':'issupplementto','title':{'en':'Is supplement to'},'extra':1}]:self.assertRaises(ValueError,w.first_week_projection,f.legacy,f.native,r,r['response'],n,pub,relation_template=t)
 def test_operation_assembly_forbids_metadata_source_in_same_concept(self):
  roles={k:{'path':'/private/tmp/fixture/'+k,'sha256':'a'*64}for k in w.ROLES};self.assertRaises(ValueError,w.assemble_context,record_id='999999',metadata_source_registration={'path':'/private/tmp/fixture/source','sha256':'a'*64},**roles)

class VocabularyMaterialClosureTests(RegisteredVocabularyTests):
 def test_registered_template_outside_root_or_symlink_must_fail(self):
  for change in ['outside','symlink']:
   p=self.vocab();f,r,n,pub,root,t,b,rb,eb,a=p
   if change=='outside':
    ext=tempfile.NamedTemporaryFile(delete=False);ext.write(d.raw_json(t));ext.close();self.addCleanup(lambda:Path(ext.name).unlink());rb={'path':ext.name,'sha256':d.sha(ext.name)}
   else:
    target=Path(rb['path']);alias=root/'ALIAS.json';alias.symlink_to(target);rb={'path':str(alias),'sha256':d.sha(target)}
   Path(eb['path']).write_bytes(d.raw_json({'relation_template':rb}));eb['sha256']=d.sha(eb['path']);self.assertRaises(ValueError,self.apply_v,p)
 def test_template_modified_during_default_admission_must_fail(self):
  p=self.vocab();f,r,n,pub,root,t,b,rb,eb,a=p
  def changed(*args):Path(b['path']).write_bytes(d.raw_json({'changed':True}));return a
  with patch('methods_digest_registration.require_registration',side_effect=changed):self.assertRaises(ValueError,w.registered_relation_template,b,root=root,source_native=f.native,source_legacy=f.legacy)
 def test_default_registration_hold_is_never_replaced_by_template(self):
  p=self.vocab();f,r,n,pub,root,t,b,rb,eb,a=p
  with patch('methods_digest_registration.require_registration',side_effect=ValueError('genuine default HOLD')):self.assertRaises(ValueError,w.registered_relation_template,b,root=root,source_native=f.native,source_legacy=f.legacy)
 def test_source_relation_enum_conflict_with_registered_template_must_fail(self):
  p=self.vocab();p[0].native['metadata']['related_identifiers'][0]['relation_type']['title']['en']='Changed';p[-1]['public_native']=deepcopy(p[0].native);self.assertRaises(ValueError,self.apply_v,p)
 def test_server_flag_transition_does_not_change_scientific_vocabulary(self):
  p=self.vocab();p[0].native['versions'].update(is_latest=False,is_latest_draft=False);self.assertEqual(self.apply_v(p),p[5])


class FirstPidLifecycleTests(FirstWeekContextTests):
 def test_first_native_pid_is_exact_empty_and_legacy_prereserve_is_only_legacy(self):
  f,r,n,pub=self.initial();expected,legacy=w.first_week_projection(f.legacy,f.native,r,r['response'],n,pub);self.assertEqual(expected['pids'],{});self.assertEqual(legacy['metadata']['prereserve_doi'],{'doi':'10.5281/zenodo.'+f.f.rid,'recid':int(f.f.rid)})
 def test_native_early_doi_oai_unknown_missing_or_foreign_pid_must_fail(self):
  for value in [{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'}},{'oai':{'identifier':'oai:zenodo.org:999999','provider':'oai'}},{'unknown':{}},None]:
   f,r,n,pub=self.initial();n['pids']=value;self.assertRaises(ValueError,w.first_week_projection,f.legacy,f.native,r,r['response'],n,pub)
 def test_complete_context_reservation_is_the_only_native_doi_source(self):
  f,root,c,pub,e,load=self.first_context();value=self.apply(c,pub,e,load,root);self.assertEqual(value['before_native']['pids'],load(c['source_bindings']['reservation_receipt'])['response']['pids']);self.assertEqual(load(c['source_bindings']['first_own_native_draft'])['response']['pids'],{})
 def test_reserve_empty_foreign_extra_wrong_provider_or_client_must_fail(self):
  for value in [{},{'doi':{'identifier':'10.5281/zenodo.123456','provider':'datacite','client':'datacite'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'other','client':'datacite'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'other'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'},'oai':{'identifier':'oai:zenodo.org:999999','provider':'oai'}}]:
   f,root,c,pub,e,load=self.first_context();binding=c['source_bindings']['reservation_receipt'];v=load(binding);v['response']['pids']=value;Path(binding['path']).write_bytes(d.raw_json(v));binding['sha256']=d.sha(binding['path']);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_prepublish_before_reservation_and_extra_unknown_pid_must_fail(self):
  for value in [{},{'doi':{'identifier':'10.5281/zenodo.123456','provider':'datacite','client':'datacite'}},{'doi':{'identifier':'10.5281/zenodo.999999','provider':'datacite','client':'datacite'},'unknown':{}}]:
   f,root,c,pub,e,load=self.first_context();binding=c['source_bindings']['before_publish_native_receipt'];v=load(binding);v['response']['pids']=value;Path(binding['path']).write_bytes(d.raw_json(v));binding['sha256']=d.sha(binding['path']);self.assertRaises(ValueError,self.apply,c,pub,e,load,root)
 def test_same_concept_constructor_and_generic_same_context_are_byte_identical_v003(self):
  before=(HERE/'BEFORE_V003_digest_weekly_state.py').read_text();after=(HERE/'digest_weekly_state.py').read_text();bd={n.name:n for n in ast.parse(before).body if isinstance(n,ast.FunctionDef)};ad={}
  for n in ast.parse(after).body:
   if isinstance(n,ast.FunctionDef):ad.setdefault(n.name,n)
  for name in bd:
   if name not in {'first_week_projection','consume_first_week_context'}:self.assertEqual(ast.get_source_segment(before,bd[name]),ast.get_source_segment(after,ad[name]))
