import copy,hashlib,sys,unittest,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
from weekly_archive_wait import WeeklyArchiveWait
class Fixture:
    deadline=None
    def __init__(self):self.calls=[]
    def open(self,request,timeout=120):self.calls.append((request.full_url,request.get_method(),timeout));return timeout
class Tests(unittest.TestCase):
    def setUp(self):
        self.inner=Fixture();self.wait=WeeklyArchiveWait(self.inner);self.rid='23300000';self.src='23226761';self.bucket='https://zenodo.org/api/files/00000000-0000-0000-0000-000000000000';self.created={'method':'POST','url':'https://zenodo.org/api/deposit/depositions/'+self.src+'/actions/newversion','http_status':201,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':{'id':int(self.rid),'state':'unsubmitted','submitted':False,'links':{'bucket':self.bucket}}};self.first={'method':'GET','url':'https://zenodo.org/api/deposit/depositions/'+self.rid,'http_status':200,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response':copy.deepcopy(self.created['response'])};self.archive={'name':'METHODS_NOTES.zip','bytes':4,'sha256':hashlib.sha256(b'ZIP!').hexdigest()}
    def arm(self):self.wait.arm(self.rid,self.src,self.created,self.first,self.archive)
    def request(self,name='METHODS_NOTES.zip',method='PUT',body=b'ZIP!',bucket=None):return urllib.request.Request((bucket or self.bucket)+'/'+name,data=body,method=method)
    def test_exact_owned_archive_uses600(self):self.arm();self.assertEqual(self.wait.open(self.request()),600)
    def test_all_other_files_unchanged120(self):self.arm();self.assertEqual(self.wait.open(self.request('paper.pdf')),120)
    def test_wrong_method_never_receives600(self):self.arm();self.assertEqual(self.wait.open(self.request(method='POST')),120)
    def test_get_zip_never_receives600(self):self.arm();self.assertEqual(self.wait.open(self.request(method='GET')),120)
    def test_wrong_rid_cannot_arm(self):self.assertRaises(ValueError,self.wait.arm,'9999',self.src,self.created,self.first,self.archive)
    def test_wrong_source_cannot_arm(self):self.assertRaises(ValueError,self.wait.arm,self.rid,'9999',self.created,self.first,self.archive)
    def test_wrong_owned_get_cannot_arm(self):
        self.first['url']=self.first['url'].replace(self.rid,'9999');self.assertRaises(ValueError,self.arm)
    def test_wrong_bucket_cannot_receive600(self):self.arm();self.assertRaises(ValueError,self.wait.open,self.request(bucket=self.bucket.replace('000000000000','000000000999')))
    def test_wrong_zip_bytes_fails_before_sender(self):self.arm();self.assertRaises(ValueError,self.wait.open,self.request(body=b'ZIP?'));self.assertEqual(self.inner.calls,[])
    def test_wrong_size_fails_before_sender(self):self.arm();self.assertRaises(ValueError,self.wait.open,self.request(body=b'ZIP!!'))
    def test_nonzip_inventory_cannot_arm(self):self.archive['name']='paper.pdf';self.assertRaises(ValueError,self.arm)
    def test_unarmed_zip_fails(self):self.assertRaises(ValueError,self.wait.open,self.request())
    def test_default_must_remain120(self):self.arm();self.assertRaises(ValueError,self.wait.open,self.request(),300)
    def test_scope_cannot_be_reassigned(self):
        self.arm();self.archive['sha256']='a'*64;self.assertRaises(ValueError,self.arm)
    def test_deadline_forwards_to_original_pacer(self):self.wait.deadline=123.5;self.assertEqual(self.inner.deadline,123.5);self.assertEqual(self.wait.deadline,123.5)
if __name__=='__main__':unittest.main()
