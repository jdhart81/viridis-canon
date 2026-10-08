"""Immutable API-spelling successor and portable offline execution regressions."""
import ast,hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
from test_digest_historical_adapter import historical_protocol
OLD_FREEZE='f4468f5380fae88304c31c61494f43f97551fc279484a7756966a7e91c819c4b'
NEW_FREEZE='c8d5c371830c7ade86363e9274dd1a7b9d07bf4ee387ff4ae3c76117eaa41c4f'
OLD_DRIVER='6b838bc1ab12c0d66ef99e5e51c53181f1e0ba70ceb92b8f8d0506476005b345'
NEW_DRIVER='551674f989688a5076d49308044c46e3294421fadf2c205381f20e14544631ba'
METADATA_SHA='e5c5cd3b7ca80d9c31c4adcafacc9bd357e440965a25baed291c99f70a4781fe'
NEW_STATE='cbd6aa9034e8d2e775c3b2f3226c9c41dbb39ccce1d7a59150ca52414ca8dfb2'

class FirstDigestCommunitySuccessorTests(unittest.TestCase):
 def paths(self):
  gate=Path(__file__).resolve().parent
  old=gate/'production_snapshots/phase7-20261007-first-digest/after/production_execution_dependencies'
  new=gate/'production_snapshots/phase7-20261007-first-digest-community-api-v001/after/production_execution_dependencies'
  return gate,old,new
 def test_exact_immutable_successor_and_closed_function_delta(self):
  gate,old,new=self.paths();oldraw=(old/'FREEZE.json').read_bytes();newraw=(new/'FREEZE.json').read_bytes()
  self.assertEqual(hashlib.sha256(oldraw).hexdigest(),OLD_FREEZE);self.assertEqual(hashlib.sha256(newraw).hexdigest(),NEW_FREEZE)
  oldrows=json.loads(oldraw)['files'];newrows=json.loads(newraw)['files']
  self.assertEqual(len({r['filename']for r in newrows}),len(newrows))
  self.assertEqual({p.name for p in new.iterdir()if p.is_file()},{r['filename']for r in newrows}|{'FREEZE.json'})
  for folder,rows in((old,oldrows),(new,newrows)):
   for row in rows:
    with self.subTest(snapshot=folder.name,filename=row['filename']):
     p=folder/row['filename'];self.assertFalse(p.is_symlink());raw=p.read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  original_production={r['filename']for r in oldrows if r['filename'].endswith('.py')and not r['filename'].startswith('test_')}
  changed={name for name in original_production if(old/name).read_bytes()!=(new/name).read_bytes()}
  self.assertEqual(changed,{'first_digest_state.py','first_digest_publisher.py'})
  self.assertEqual(hashlib.sha256((old/'first_digest_publisher.py').read_bytes()).hexdigest(),OLD_DRIVER)
  self.assertEqual(hashlib.sha256((new/'first_digest_publisher.py').read_bytes()).hexdigest(),NEW_DRIVER)
  self.assertEqual(hashlib.sha256((new/'first_digest_state.py').read_bytes()).hexdigest(),NEW_STATE)
  self.assertEqual((old/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes())
  self.assertEqual(hashlib.sha256((gate/'digest_metadata.py').read_bytes()).hexdigest(),METADATA_SHA)
  self.assertEqual((gate/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes())
  oldpub=(old/'first_digest_publisher.py').read_bytes();wanted=oldpub.replace(b"api=metadata.closed_payload(manifest['public_metadata'],before)",b"api=state.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],before))")
  wanted=wanted.replace(b".hexdigest()[:16]+':'+str(result['writes']+1)",b".hexdigest()[:16]+':'+hashlib.sha256(body).hexdigest()+':'+str(result['writes']+1)")
  self.assertEqual((new/'first_digest_publisher.py').read_bytes(),wanted)
  def bodies(p):
   text=p.read_text();return{n.name:ast.get_source_segment(text,n)for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
  before=bodies(old/'first_digest_state.py');after=bodies(new/'first_digest_state.py')
  self.assertEqual(set(after)-set(before),{'_community_rows','community_request','community_public','encode_api_communities'})
  for name,body in before.items():
   if name!='initial_expected':self.assertEqual(after[name],body,name)
 def test_portable_offline_successor_protocol_and_all_must_fail_cases(self):
  gates,old,new=self.paths();env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gates);env['PYTHONDONTWRITEBYTECODE']='1'
  result=historical_protocol(gates,new)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('Ran 146 tests',result.stderr)

if __name__=='__main__':unittest.main()
