"""Portable serializer tests; full production native admission is separate."""
import copy,sys,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
from owned_prior_legacy import require_prior_legacy
from digest_metadata import exact
class Preservation:
    @staticmethod
    def require_public_metadata(a,b):
        if not exact(a,b):raise ValueError('metadata mismatch')
    require_file_preservation=require_public_metadata
class NativeFixture:
    @staticmethod
    def require_links_stats(actual,expected,**kwargs):
        if actual['links']!=expected['links']or set(actual['stats'])!={'downloads'}or type(actual['stats']['downloads'])is not int or actual['stats']['downloads']<0:raise ValueError('fixture closed stats failed')
    @staticmethod
    def validate_prior_version(actual,expected,**kwargs):
        a,b=copy.deepcopy(actual),copy.deepcopy(expected)
        a.pop('versions');b.pop('versions')
        if not exact(a,b):raise ValueError('fixture prior native content mismatch')
class Tests(unittest.TestCase):
    def setUp(self):
        self.native={'id':'23226761','parent':{'id':'23226760'},'versions':{'index':1,'is_latest':True},'updated':'2026-10-08T12:00:00','revision_id':10,'links':{'self':'own'},'stats':{'downloads':2},'metadata':{'title':'untouched'},'pids':{'doi':{'identifier':'10.5281/zenodo.23226761'}}}
        self.legacy={'id':23226761,'doi':'10.5281/zenodo.23226761','metadata':{'title':'untouched','relations':{'version':[{'index':0,'is_last':True,'parent':{'pid_type':'recid','pid_value':'23226760'}}]}},'files':[{'key':'paper.pdf','checksum':'md5:bound'}],'modified':self.native['updated'],'updated':self.native['updated'],'revision':10,'links':{'self':'own'},'stats':{'downloads':2},'owners':[{'id':1}]}
    def call(self,a,n,chain=None):return require_prior_legacy(a,self.legacy,n,self.native,sm=NativeFixture,preservation=Preservation,chain=chain)
    def test_precreate_exact_pass(self):self.call(self.legacy,self.native)
    def test_complete_latest_flag_transition_pass(self):
        n=copy.deepcopy(self.native);n['versions']['is_latest']=False;a=copy.deepcopy(self.legacy);a['metadata']['relations']['version'][0]['is_last']=False;self.call(a,n,{'successor_record_id':'23300001'})
    def test_flat_legacy_counters_use_original_guard_not_native_shape(self):
        a=copy.deepcopy(self.legacy);a['stats']['downloads']=5;self.call(a,self.native)
    def test_unknown_legacy_counter_fails(self):
        a=copy.deepcopy(self.legacy);a['stats']['unknown']=1;self.assertRaises(ValueError,self.call,a,self.native)
    def test_negative_legacy_counter_fails(self):
        a=copy.deepcopy(self.legacy);a['stats']['downloads']=-1;self.assertRaises(ValueError,self.call,a,self.native)
    def test_unknown_legacy_key_fails(self):
        a=copy.deepcopy(self.legacy);a['unknown']='silently ignored';self.assertRaises(ValueError,self.call,a,self.native)
    def test_missing_legacy_key_fails(self):
        a=copy.deepcopy(self.legacy);a.pop('owners');self.assertRaises(ValueError,self.call,a,self.native)
    def test_legacy_doi_change_fails(self):
        a=copy.deepcopy(self.legacy);a['doi']='foreign';self.assertRaises(ValueError,self.call,a,self.native)
    def test_file_checksum_change_fails(self):
        a=copy.deepcopy(self.legacy);a['files'][0]['checksum']='changed';self.assertRaises(ValueError,self.call,a,self.native)
    def test_native_science_change_fails_before_legacy_projection(self):
        n=copy.deepcopy(self.native);n['metadata']['title']='stronger';self.assertRaises(ValueError,self.call,self.legacy,n,{'successor_record_id':'23300001'})
    def test_wrong_native_ordinal_fails(self):
        n=copy.deepcopy(self.native);n['versions']['index']=2;self.assertRaises(ValueError,self.call,self.legacy,n,{'successor_record_id':'23300001'})
    def test_foreign_relation_parent_fails(self):
        self.legacy['metadata']['relations']['version'][0]['parent']['pid_value']='foreign';self.assertRaises(ValueError,self.call,self.legacy,self.native,{'successor_record_id':'23300001'})
if __name__=='__main__':unittest.main()
