"""Pure request-denial tests; no live API or future closure PASS claimed."""
import ast,sys,unittest,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import capture_weekly_inputs as capture
class Inner:
 def __init__(self):self.calls=[]
 def open(self,request,timeout=120):self.calls.append((request.full_url,timeout));return 'fixture GET result'
class Tests(unittest.TestCase):
 def setUp(self):self.inner=Inner();self.opener=capture.GetOnlyOpener(self.inner,'23226761')
 def test_own_public_get_only_passes(self):self.assertEqual(self.opener.open(urllib.request.Request('https://zenodo.org/api/records/23226761',method='GET')),'fixture GET result')
 def test_account_exact_page_get_passes(self):self.opener.open(urllib.request.Request('https://zenodo.org/api/user/records?page=1&size=100',method='GET'));self.assertEqual(len(self.inner.calls),1)
 def test_all_mutation_methods_denied(self):
  for method in ['POST','PUT','DELETE','PATCH']:
   with self.subTest(method=method):self.assertRaises(ValueError,self.opener.open,urllib.request.Request('https://zenodo.org/api/records/23226761',method=method));self.assertEqual(self.inner.calls,[])
 def test_get_body_denied(self):self.assertRaises(ValueError,self.opener.open,urllib.request.Request('https://zenodo.org/api/records/23226761',data=b'{}',method='GET'));self.assertEqual(self.inner.calls,[])
 def test_foreign_record_host_or_query_denied(self):
  for url in ['https://zenodo.org/api/records/9','https://sandbox.zenodo.org/api/records/23226761','https://zenodo.org/api/records/23226761?x=1','https://zenodo.org/api/deposit/depositions/23226761']:
   with self.subTest(url=url):self.assertRaises(ValueError,self.opener.open,urllib.request.Request(url,method='GET'));self.assertEqual(self.inner.calls,[])
 def test_modified_account_page_size_token_or_omitted_page_denied(self):
  for url in ['https://zenodo.org/api/user/records?page=1&size=10','https://zenodo.org/api/user/records?size=100','https://zenodo.org/api/user/records?page=1&size=100&access_token=x']:
   with self.subTest(url=url):self.assertRaises(ValueError,self.opener.open,urllib.request.Request(url,method='GET'));self.assertEqual(self.inner.calls,[])
 def test_no_credential_lookup_or_mutation_request_in_capture(self):
  text=Path(capture.__file__).read_text();self.assertNotIn('keychain_token(',text);self.assertNotIn('subprocess',text);self.assertNotIn('Zenodo_token.md',text)
  tree=ast.parse(text);calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='request'];self.assertEqual([n.args[0].value for n in calls],['GET','GET'])
if __name__=='__main__':unittest.main()
