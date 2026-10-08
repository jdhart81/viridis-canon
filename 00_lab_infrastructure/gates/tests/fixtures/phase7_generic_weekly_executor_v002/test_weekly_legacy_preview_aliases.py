import copy,importlib.util,sys,types,unittest
from pathlib import Path
P=Path(__file__).parent
fixture=types.ModuleType('digest_metadata')
class Hold(ValueError):pass
def check(v,r):
    if not v:raise Hold(r)
fixture.check=check
old=sys.modules.get('digest_metadata');sys.modules['digest_metadata']=fixture
spec=importlib.util.spec_from_file_location('owned_alias_fixture',P/'owned_legacy_preview_aliases.py');aliases=importlib.util.module_from_spec(spec);spec.loader.exec_module(aliases)
if old is None:sys.modules.pop('digest_metadata')
else:sys.modules['digest_metadata']=old
class SM:
    @staticmethod
    def _preview_url(url,*,host,record_id,allowed_keys):
        check(url.startswith('https://'+host+'/api/iiif/record:'+record_id+':paper.pdf/'),'FOREIGN_URL');return'paper.pdf'
class Tests(unittest.TestCase):
    def setUp(self):
        self.rid='23299999';self.expected={'id':int(self.rid),'links':{'bucket':'exact-own-bucket','thumb250':'old','thumbs':{'250':'old'}}};self.native={'id':self.rid,'links':{'thumbnails':{s:'https://zenodo.org/api/iiif/record:'+self.rid+':paper.pdf/full/'+s for s in aliases.SIZES}},'files':{'entries':{'paper.pdf':{}}}};self.audit={'status':'SERVER_MANAGED_READBACK_PASS','operation':'NEW_VERSION','phase':'DRAFT','record_id':self.rid,'checks':{k:{'status':'PASS'}for k in aliases.REQUIRED_CHECKS}}
    def project(self):return aliases.project(self.native,self.expected,self.audit,SM,record_id=self.rid)
    def test_own_new_id_exact_native_alias_projection(self):
        a=self.project();self.assertEqual(a['links']['bucket'],'exact-own-bucket');self.assertEqual(a['links']['thumb250'],'https://zenodo.org/record/'+self.rid+'/thumb250')
    def test_source_proven_absence_removes_only_two_derived_aliases(self):
        self.native['links']={};a=self.project();self.assertEqual(a,{'id':int(self.rid),'links':{'bucket':'exact-own-bucket'}})
    def test_missing_full_audit_row_fails(self):self.audit['checks'].pop('unlisted_fields');self.assertRaises(Hold,self.project)
    def test_any_failed_native_row_fails(self):self.audit['checks']['content_metadata']['status']='HOLD';self.assertRaises(Hold,self.project)
    def test_wrong_record_audit_fails(self):self.audit['record_id']='1';self.assertRaises(Hold,self.project)
    def test_foreign_preview_url_fails(self):self.native['links']['thumbnails']['250']='https://zenodo.org/api/iiif/record:1:paper.pdf/full/250';self.assertRaises(Hold,self.project)
    def test_extra_size_fails(self):self.native['links']['thumbnails']['999']='x';self.assertRaises(Hold,self.project)
    def test_missing_main_pdf_fails(self):self.native['files']['entries']={};self.assertRaises(Hold,self.project)
    def test_unknown_native_guard_cannot_grant_projection(self):self.audit['checks']['new_rule']={'status':'PASS'};self.assertRaises(Hold,self.project)
if __name__=='__main__':unittest.main()
