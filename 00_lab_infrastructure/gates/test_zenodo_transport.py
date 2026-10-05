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
    def test_authorization_must_be_literal_true(self):
        body=b'{}'
        with self.assertRaises(TransportHold):self.t.request('PUT','https://sandbox.zenodo.org/api/x',body,hashlib.sha256(body).hexdigest(),authorized=1)
        self.assertEqual(self.fake.calls,[])
    def test_ordinary_delete_rejected_even_with_exact_hash_and_authorization(self):
        for url in ('/api/records/1','/api/deposit/depositions/2','/api/deposit/depositions/2/files/abc-123'):
            with self.assertRaises(TransportHold):self.t.request('DELETE','https://sandbox.zenodo.org'+url,b'',hashlib.sha256(b'').hexdigest(),authorized=True)
        self.assertEqual(self.fake.calls,[])
    def test_get_body_rejected_before_network(self):
        with self.assertRaises(TransportHold):self.t.request('GET','https://sandbox.zenodo.org/api/x',b'{}')
        self.assertEqual(self.fake.calls,[])
    def test_invalid_json_or_scalar_response_not_retried(self):
        for raw in (b'not json',b'null',b'true',b'42',b'"text"'):
            with self.subTest(response=raw):
                class InvalidResponse(Response):
                    def read(self):return raw
                class InvalidOpener(Opener):
                    def open(self,req,timeout):self.calls.append(req);return InvalidResponse()
                invalid=InvalidOpener();self.t.opener=invalid
                with self.assertRaisesRegex(TransportHold,'NO_RETRY'):self.t.request('GET','https://sandbox.zenodo.org/api/x')
                self.assertEqual(len(invalid.calls),1)
    def test_success_response_token_is_redacted_in_receipt(self):
        class EchoResponse(Response):
            def read(self):return b'{"unexpected":"test-secret-never-logged"}'
        class EchoOpener(Opener):
            def open(self,req,timeout):self.calls.append(req);return EchoResponse()
        self.t.opener=EchoOpener()
        self.t.request('GET','https://sandbox.zenodo.org/api/x')
        from pathlib import Path
        raw=next(Path(self.tmp.name).iterdir()).read_text();receipt=json.loads(raw)
        self.assertNotIn('test-secret-never-logged',raw)
        self.assertEqual(receipt['response']['unexpected'],'[REDACTED_CREDENTIAL]')
        self.assertEqual(receipt['status'],'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE')
