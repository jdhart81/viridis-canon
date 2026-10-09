import copy, hashlib, unittest
import own_prior_record as prior

class Preservation:
    @staticmethod
    def require_public_metadata(a,b):
        if not prior.exact(a,b):raise ValueError('metadata changed')
    @staticmethod
    def require_file_preservation(a,b):
        if {r['key']:r for r in a}!={r['key']:r for r in b}:raise ValueError('files changed')
def fixture():
    saved_n={'id':'23226761','parent':{'id':'23226760'},'metadata':{'title':'unchanged'},'pids':{'doi':{'identifier':'10.5281/zenodo.23226761'}},'files':{'entries':{'paper.tex':{'key':'paper.tex','size':10,'checksum':'md5:'+'a'*32}}},'versions':{'index':1,'is_latest':True,'is_latest_draft':True},'stats':{'views':100},'revision_id':5,'ui':{'something':'unchanged'}}
    saved_l={'id':23226761,'conceptrecid':'23226760','metadata':{'title':'unchanged','relations':{'version':[{'index':0,'is_last':True,'parent':{'pid_value':'23226760'}}]}},'files':[{'key':'paper.tex','size':10,'checksum':'md5:'+'a'*32}],'doi':'10.5281/zenodo.23226761','stats':{'views':100}}
    def receipt(method,url,response,status):return {'method':method,'url':url,'environment':'zenodo.org','http_status':status,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':response,'request_body_sha256':hashlib.sha256(b'{}').hexdigest()}
    created=receipt('POST','https://zenodo.org/api/deposit/depositions/23226761/actions/newversion',{'id':23246368,'conceptrecid':'23226760','submitted':False,'state':'unsubmitted'},201)
    published=receipt('POST','https://zenodo.org/api/deposit/depositions/23246368/actions/publish',{'id':23246368,'conceptrecid':'23226760','submitted':True,'state':'done','doi':'10.5281/zenodo.23246368'},201)
    return saved_l,saved_n,created,published
class PriorTests(unittest.TestCase):
    def setUp(self):self.sl,self.sn,self.created,self.published=fixture();self.l=copy.deepcopy(self.sl);self.n=copy.deepcopy(self.sn);self.n['versions']['is_latest_draft']=False
    def check(self,publish=None):return prior.require_pair(self.l,self.n,self.sl,self.sn,creation=self.created,publish=publish,preservation=Preservation)
    def test_created_flag_pass(self):self.created['response'].update({'submitted':True,'state':'own-server-housekeeping'});self.assertEqual(self.check()['chain_state'],'OWN_CREATED')
    def test_published_both_flags_pass(self):self.published['response'].update({'submitted':False,'state':'own-server-housekeeping'});self.n['versions']['is_latest']=False;self.l['metadata']['relations']['version'][0]['is_last']=False;self.assertEqual(self.check(self.published)['chain_state'],'OWN_PUBLISHED')
    def test_unchanged_pair_pass(self):self.assertEqual(prior.require_pair(self.sl,self.sn,self.sl,self.sn,preservation=Preservation)['chain_state'],'UNCHANGED')
    def test_prior_file_reorder_must_fail_under_latest_existing_record_rule(self):
        second={'key':'other.txt','size':11,'checksum':'md5:'+'b'*32};self.sl['files'].append(second);self.l['files'].append(copy.deepcopy(second));self.l['files'].reverse();self.assertRaises(ValueError,self.check)
    def test_prior_title_must_fail(self):self.l['metadata']['title']='changed';self.assertRaises(ValueError,self.check)
    def test_prior_number_must_fail(self):self.n['metadata']['n']=42;self.assertRaises(ValueError,self.check)
    def test_prior_native_file_checksum_must_fail(self):self.n['files']['entries']['paper.tex']['checksum']='md5:'+'b'*32;self.assertRaises(ValueError,self.check)
    def test_prior_legacy_file_size_must_fail(self):self.l['files'][0]['size']=11;self.assertRaises(ValueError,self.check)
    def test_prior_pid_must_fail(self):self.n['pids']['doi']['identifier']='10.5281/zenodo.9999';self.assertRaises(ValueError,self.check)
    def test_prior_stats_must_fail(self):self.n['stats']['views']=101;self.assertRaises(ValueError,self.check)
    def test_prior_ui_must_fail(self):self.n['ui']['something']='changed';self.assertRaises(ValueError,self.check)
    def test_prior_revision_must_fail(self):self.n['revision_id']=6;self.assertRaises(ValueError,self.check)
    def test_unlisted_prior_native_field_must_fail(self):self.n['new_housekeeping']='own-only rule does not apply';self.assertRaises(ValueError,self.check)
    def test_unlisted_prior_legacy_field_must_fail(self):self.l['new_housekeeping']='own-only rule does not apply';self.assertRaises(ValueError,self.check)
    def test_flag_without_creation_must_fail(self):self.assertRaises(ValueError,prior.require_pair,self.l,self.n,self.sl,self.sn,preservation=Preservation)
    def test_foreign_creation_must_fail(self):self.created['response']['conceptrecid']='9999';self.assertRaises(ValueError,self.check)
    def test_prior_index_change_must_fail(self):self.n['versions']['index']=2;self.assertRaises(ValueError,self.check)
    def test_prior_latest_false_before_publish_must_fail(self):self.n['versions']['is_latest']=False;self.assertRaises(ValueError,self.check)
    def test_published_flag_without_terminal_receipt_must_fail(self):self.n['versions']['is_latest']=False;self.l['metadata']['relations']['version'][0]['is_last']=False;self.published['response']['doi']='10.5281/zenodo.9999';self.assertRaises(ValueError,self.check,self.published)
    def test_minted_prior_version_field_must_fail(self):self.n['versions']['new_server_flag']=True;self.assertRaises(ValueError,self.check)

if __name__=='__main__':unittest.main()
