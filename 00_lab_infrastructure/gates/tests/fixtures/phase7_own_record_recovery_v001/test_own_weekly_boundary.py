"""Current source boundary tests with real own policy and isolated I/O.

No fixture transport is publication evidence. The real boundary.full_draft and
controlled constructors invoke the real own checker; downloads are isolated.
"""
import builtins,copy,types,unittest
from pathlib import Path
import weekly_digest_executor as engine
import own_record_comparison as policy
import own_prior_record
from test_own_record_comparison import fixture

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.native,self.legacy,self.c,self.o=fixture()
        for value in(self.native['metadata'],self.c['native_metadata']):
            for row in value.get('related_identifiers',[]):row['relation_type']={'id':'issupplementto'};row.pop('relation',None)
        modules={name:types.ModuleType(name)for name in('digest_weekly_state','digest_metadata','first_digest_state','digest_public_state','publisher_previews','server_managed_fields','publication_preservation','methods_digest','owned_legacy_preview_aliases','owned_prior_legacy','first_digest_publisher')}
        modules.update(weekly_digest_executor=engine,own_record_comparison=policy,own_prior_record=own_prior_record)
        modules['owned_prior_legacy'].require_prior_legacy=lambda *a,**k:None
        modules['first_digest_publisher'].Downloads=object;modules['first_digest_publisher'].PacedOpener=object
        original_import=builtins.__import__
        def isolated(name,globals=None,locals=None,fromlist=(),level=0):return modules[name]if level==0 and name in modules else original_import(name,globals,locals,fromlist,level)
        module=types.ModuleType('source_bound_current_boundary_fixture');module.__file__=str(Path(__file__).parent/'weekly_digest_boundary.py');module.__dict__['__builtins__']=dict(vars(builtins),__import__=isolated)
        exec(compile(Path(module.__file__).read_bytes(),module.__file__,'exec'),module.__dict__)
        self.b=module.WeeklyDigestBoundary.__new__(module.WeeklyDigestBoundary)
        self.b.plan={'start_kind':'NEW_VERSION','predecessor_record_id':'101','source_concept_id':'100'}
        self.b.native_metadata=copy.deepcopy(self.c['native_metadata']);self.b.payload={'metadata':copy.deepcopy(self.c['legacy_metadata'])};self.b.manifest={'public_metadata':copy.deepcopy(self.c['legacy_metadata'])};self.b.saved_native={'parent':{'communities':{'ids':copy.deepcopy(self.c['native_community_ids'])}}}
        self.b.ownership=lambda state:copy.deepcopy(self.o)
        self.state={'record_id':'102','concept_id':'100','completed':['NEW_VERSION','METADATA','UPLOAD:evidence.json','UPLOAD:paper.pdf'],'inherited_inventory':[]}
        self.b.inventory={row['name']:{'name':row['name'],'bytes':row['bytes'],'md5':row['md5'],'sha256':'f'*64}for row in self.c['files']}
        self.downloads=[];self.b.downloads=types.SimpleNamespace(get=lambda name,*a,**kw:self.downloads.append(name))
        self.expected=copy.deepcopy(self.native);self.wanted=copy.deepcopy(self.legacy)
    def call(self):return self.b.full_draft(self.state,self.expected,self.wanted,self.legacy,self.native,chain=None)
    def test_sent_controlled_draft_pass_downloads_each_file(self):
        self.call();self.assertEqual(set(self.downloads),{'evidence.json','paper.pdf'});self.assertEqual(self.b.last_draft_audit['status'],'OWN_RECORD_CONTROLLED_READBACK_PASS')
    def test_unknown_server_housekeeping_logged_not_gated(self):
        self.native.update(ui={'totally_new':True},revision_id=7000,new_future_server_field={'new':True});self.legacy.update(stats={'views':10000},new_future_server_field=42)
        self.call();self.assertIn('new_future_server_field',self.b.last_draft_audit['housekeeping']['native'])
    def test_preview_failure_not_gated(self):self.native['media_files']={'entries':{'broken-preview':{'status':'failed'}}};self.call()
    def test_native_scientific_description_must_fail_before_download(self):self.native['metadata']['description']='changed claim';self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_legacy_description_must_fail_before_download(self):self.legacy['metadata']['description']='changed claim';self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_control_expected_afterbody_does_not_override_sent_target(self):
        self.native['metadata']['description']='changed claim';self.expected['metadata']['description']='changed claim';self.assertRaises(ValueError,self.call)
    def test_filename_must_fail_before_download(self):self.native['files']['entries']['renamed']=self.native['files']['entries'].pop('paper.pdf');self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_checksum_must_fail_before_download(self):self.native['files']['entries']['paper.pdf']['checksum']='md5:'+'0'*32;self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_file_size_must_fail_before_download(self):self.legacy['files'][0]['filesize']+=1;self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_pid_identity_must_fail_before_download(self):self.native['pids']={'doi':{'identifier':'10.5281/zenodo.666'}};self.assertRaises(ValueError,self.call);self.assertEqual(self.downloads,[])
    def test_reserved_own_pid_housekeeping_logged(self):
        self.state['completed'].append('RESERVE_DOI');self.native['pids']={'doi':{'identifier':'10.5281/zenodo.102','provider':'new-server-provider'},'minted_other':{'provider':'other'}};self.legacy['doi']='10.5281/zenodo.102';self.call()
    def test_community_identity_must_fail(self):self.legacy['metadata']['communities']=[{'identifier':'wrong-community'}];self.assertRaises(ValueError,self.call)
    def test_metadata_date_must_equal_explicit_payload(self):self.legacy['metadata']['publication_date']='2026-10-09';self.assertRaises(ValueError,self.call)

if __name__=='__main__':unittest.main()
