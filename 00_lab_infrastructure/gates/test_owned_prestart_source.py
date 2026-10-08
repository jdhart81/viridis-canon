"""Pure TMP tests prove ineligible sources fail before reservation/transport."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import owned_digest_executor as e
class NeverRuntime:
    def __getattr__(self,name):raise AssertionError('runtime touched before source refusal: '+name)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.package=self.root/'package';self.package.mkdir();self.plan={}
        def put(name,value):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(e.raw_json(value));return e.binding(p)
        shared=put('shared.json',{'fixture':'no clearance'});self.manifest={'release_week':'2026-W41','notes':[{'run_id':'Run-142'}],'public_metadata':{'title':'Viridis Methods Digest — 2026-W41'}}
        (self.package/'DIGEST_MANIFEST.json').write_bytes(e.raw_json(self.manifest));(self.package/'PUBLICATION_BINDING.json').write_bytes(e.raw_json({'fixture':'no clearance'}));inventory=[]
        for n in sorted(e.machine.NAMES):
            p=self.package/n
            if not p.exists():p.write_bytes(b'fixture byte')
            b=p.read_bytes();inventory.append(dict(name=n,path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),md5=hashlib.md5(b).hexdigest()))
        self.native={'environment':'zenodo.org','method':'GET','url':'https://zenodo.org/api/records/23226761','accept':'application/vnd.inveniordm.v1+json','http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':{'id':'23226761','parent':{'id':'23226760'},'versions':{'index':1,'is_latest':True,'is_latest_draft':True}}}
        legacy=dict(self.native,accept='application/json',response={'id':23226761,'conceptrecid':'23226760','metadata':{'title':self.manifest['public_metadata']['title']}})
        native_b=put('native.json',self.native);pre_b=put('pre.json',self.native);legacy_b=put('legacy.json',legacy);closure=put('closure.json',{'fixture':'no clearance'});closure['path']='closure.json';names={'owned_digest_executor.py','owned_digest_machine.py','owned_journal_writer.py','owned_digest_boundary.py','digest_successor_state.py','methods_digest.py','methods_digest_registration.py','server_managed_fields.py','zenodo_transport.py','phase7_mutation_baseline.py','mutation_journal_writer.py'};pins=[]
        for n in names:
            p=self.root/'sources'/n;p.parent.mkdir(exist_ok=True);p.write_bytes(b'# fixture: not operative source\n');pins.append(dict(name=n,**e.binding(p)))
        keys={'registration_recovery','predecessor_registration','source_origin','authority','community_mirror_proof','runtime_consumer','recovery_consumer','source_session_consumer','ordinary_cohort_consumer','account_discovery'}
        self.plan={k:shared for k in keys};self.plan.update(standard='VRS-METHODS-DIGEST-OWNED-SUCCESSOR-PLAN-1',status='ACTUAL_CURRENT_SOURCE_BOUND_NOT_EXECUTED',canonical_root=str(self.root),package=str(self.package),digest_manifest=e.binding(self.package/'DIGEST_MANIFEST.json'),publication_binding=e.binding(self.package/'PUBLICATION_BINDING.json'),current_runtime_closure=closure,before_ssot_sha256='a'*64,source_legacy_receipt=legacy_b,source_native_receipt=native_b,source_native_before_create=pre_b,purpose_source_pins=pins,approved_inventory=inventory,release_week='2026-W41',predecessor_record_id='23226761',expected_concept_id='23226760',source_concept_id='23226760',prior_run_ids=['Run-125'],new_run_ids=['Run-142'],boundary_module='owned_digest_boundary.py',start_kind='NEW_VERSION',execution_directory=str(self.root/'reports/verification-coverage/executions'))
    def tearDown(self):self.tmp.cleanup()
    def modify(self,key,fn):
        p=Path(self.plan[key]['path']);x=json.loads(p.read_bytes());fn(x);p.write_bytes(e.raw_json(x));self.plan[key]=e.binding(p)
    def no_write(self):
        p=self.root/'PLAN.json';p.write_bytes(e.raw_json(self.plan));out=Path(self.plan['execution_directory'])/'invocation';before={str(x):x.read_bytes()for x in self.root.rglob('*')if x.is_file()}
        with self.assertRaises(e.ExecutionHold):e.execute(self.root,e.binding(p),out,'fixture-token-at-least-twenty-four-chars',NeverRuntime(),reviewed_driver_sha256=e.sha(Path(e.__file__).resolve()))
        self.assertFalse(out.exists());self.assertEqual(before,{str(x):x.read_bytes()for x in self.root.rglob('*')if x.is_file()});self.assertFalse(any('reservation' in str(x)for x in self.root.rglob('*')))
    def test_typed_latest_source_passes_plan_parser_only(self):self.assertEqual(e.require_plan(self.root,self.plan),self.package)
    def test_existing_pending_child_fails_before_reservation_or_transport(self):self.modify('source_native_before_create',lambda x:x['response']['versions'].update(is_latest_draft=False));self.no_write()
    def test_nonlatest_source_fails_before_write(self):self.modify('source_native_receipt',lambda x:x['response']['versions'].update(is_latest=False));self.no_write()
    def test_boolean_integer_string_zero_negative_null_indexes_fail(self):
        for v in [True,False,'1',0,-1,None]:
            with self.subTest(v=v):self.modify('source_native_before_create',lambda x:x['response']['versions'].update(index=v));self.no_write()
    def test_nonboolean_latest_flags_fail(self):
        for key in ['is_latest','is_latest_draft']:
            for v in [1,'true',None]:
                with self.subTest(key=key,v=v):self.modify('source_native_before_create',lambda x:x['response']['versions'].update({'index':1,'is_latest':True,'is_latest_draft':True}|{key:v}));self.no_write()
    def test_wrong_accept_fails(self):self.modify('source_native_before_create',lambda x:x.update(accept='application/json'));self.no_write()
    def test_wrong_method_status_environment_url_or_identity_fail(self):
        for key,v in [('method','POST'),('http_status',201),('status','PASS'),('environment','sandbox.zenodo.org'),('url','https://zenodo.org/api/records/9')]:
            with self.subTest(key=key):self.modify('source_native_before_create',lambda x:(x.clear(),x.update(copy.deepcopy(self.native)),x.update(**{key:v})));self.no_write()
    def test_other_record_or_parent_fails(self):
        for key in ['id','parent']:
            with self.subTest(key=key):self.modify('source_native_before_create',lambda x:(x.clear(),x.update(copy.deepcopy(self.native)),x['response'].update(**{key:'9'if key=='id'else{'id':'9'}})));self.no_write()
    def test_different_science_revision_files_or_typed_body_fails_before_write(self):
        for key,value in [('metadata',{'title':'changed'}),('revision_id',2),('files',{'entries':{}}),('own_typed_scalar',True)]:
            with self.subTest(key=key):self.modify('source_native_before_create',lambda x:(x.clear(),x.update(copy.deepcopy(self.native)),x['response'].update(**{key:value})));self.no_write()
    def test_differing_ordinal_fails(self):self.modify('source_native_before_create',lambda x:x['response']['versions'].update(index=2));self.no_write()
    def test_missing_versions_or_flag_fails(self):
        for key in ['index','is_latest','is_latest_draft']:
            with self.subTest(key=key):self.modify('source_native_before_create',lambda x:(x.clear(),x.update(copy.deepcopy(self.native)),x['response']['versions'].pop(key)));self.no_write()
if __name__=='__main__':unittest.main()
