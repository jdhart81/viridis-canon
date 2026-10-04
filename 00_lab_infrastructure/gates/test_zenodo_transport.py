import hashlib,json,tempfile,unittest
from zenodo_transport import ZenodoTransport,TransportHold,NoRedirect,require_metadata
class Response:
    status=200
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self):return b'{"ok":true}'
class Opener:
    def __init__(self):self.calls=[]
    def open(self,req,timeout):self.calls.append(req);return Response()
class TransportTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.fake=Opener();self.t=ZenodoTransport('sandbox.zenodo.org','test-secret-never-logged',self.tmp.name,self.fake)
    def tearDown(self):self.tmp.cleanup()
    def test_exact_bytes_preserved_and_hash_checked(self):
        b=b'{ "metadata": {} }';h=hashlib.sha256(b).hexdigest();self.t.request('PUT','https://sandbox.zenodo.org/api/deposit/depositions/1',b,h,authorized=True)
        self.assertEqual(self.fake.calls[0].data,b)
    def test_wrong_hash_no_network(self):
        with self.assertRaises(TransportHold):self.t.request('PUT','https://sandbox.zenodo.org/api/x',b'{}','wrong',authorized=True)
        self.assertEqual(self.fake.calls,[])
    def test_no_implicit_authorization(self):
        with self.assertRaises(TransportHold):self.t.request('POST','https://sandbox.zenodo.org/api/x',b'{}',hashlib.sha256(b'{}').hexdigest())
        self.assertEqual(self.fake.calls,[])
    def test_credential_never_in_logs(self):
        self.t.request('GET','https://sandbox.zenodo.org/api/x')
        from pathlib import Path
        self.assertNotIn('test-secret',next(Path(self.tmp.name).iterdir()).read_text())
    def test_host_query_and_scheme_rejected(self):
        for url in ['https://zenodo.org/api/x','http://sandbox.zenodo.org/api/x','https://sandbox.zenodo.org/api/x?access_token=abc','https://sandbox.zenodo.org.evil/api/x']:
            with self.assertRaises(TransportHold):self.t.request('GET',url)
    def test_no_deletion(self):
        with self.assertRaises(TransportHold):self.t.request('DELETE','https://sandbox.zenodo.org/api/x')
    def test_redirect_refused(self):
        with self.assertRaises(TransportHold):NoRedirect().redirect_request(None,None,302,'',None,'https://example.org')
    def test_readback_mismatch_never_passes(self):
        with self.assertRaises(TransportHold):require_metadata({'title':'changed'},{'title':'original'})
    def test_no_retry_after_error(self):
        class Failed:
            count=0
            def open(self,*args,**kwargs):self.count+=1;raise TimeoutError()
        fail=Failed();self.t.opener=fail
        with self.assertRaises(TransportHold):self.t.request('GET','https://sandbox.zenodo.org/api/x')
        self.assertEqual(fail.count,1)
    def test_http_error_detail_is_saved_without_credential(self):
        import urllib.error,io
        class Bad:
            def open(self,*args,**kwargs):raise urllib.error.HTTPError('https://sandbox.zenodo.org/api/x',400,'invalid',{},io.BytesIO(b'{"message":"test-secret-never-logged"}'))
        self.t.opener=Bad()
        with self.assertRaises(TransportHold):self.t.request('GET','https://sandbox.zenodo.org/api/x')
        from pathlib import Path
        receipt=json.loads(next(Path(self.tmp.name).iterdir()).read_text())
        self.assertEqual(receipt['http_status'],400)
        self.assertEqual(receipt['error_response']['message'],'[REDACTED_CREDENTIAL]')
    def test_native_media_type_preserves_transport_and_is_recorded(self):
        self.t.request('GET','https://sandbox.zenodo.org/api/x',accept='application/vnd.inveniordm.v1+json')
        self.assertEqual(self.fake.calls[0].get_header('Accept'),'application/vnd.inveniordm.v1+json')
    def test_unrecognized_media_type_rejected_before_network(self):
        with self.assertRaises(TransportHold):self.t.request('GET','https://sandbox.zenodo.org/api/x',accept='unexpected')
        self.assertEqual(self.fake.calls,[])
