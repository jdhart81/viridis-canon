"""Exact source-only uploaded continuation and portable protocol closure."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
FREEZE='934a460b1796495616f4c12cecdaf31d0159b78f5008555e0d784846bd282e0c'
PREDECESSOR='41d96e8f52a19b77df80e91579620f9abf00127c7b1987d109eaa824635d32ed'
DRIVER='284a4ed37232cdae6b695e5eaab9a35ddc616511791f10cc45f2aaf8db12eb25'
HELPER='35c3ec3101f9b8026d7355c984e0bf31b194811f9aeab23800efabecdbf17306'
ALIASES='8459ac27550c35376a38bd32a5254bd301ebdc9800d99ffb38ea9b27f0460e24'
class UploadedContinuationSnapshotTests(unittest.TestCase):
 def paths(self):
  gate=Path(__file__).resolve().parent;s=gate/'production_snapshots';return gate,s/'phase7-20261007-reserved-draft-continuation-v001/after/production_execution_dependencies',s/'phase7-20261007-uploaded-draft-continuation-v001/after/production_execution_dependencies'
 def test_exact_immutable_snapshot_preserves_every_predecessor_file(self):
  gate,old,new=self.paths();raw=(new/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FREEZE);f=json.loads(raw);self.assertEqual(len(f['files']),48);self.assertEqual(len({r['filename']for r in f['files']}),48);self.assertEqual({p.name for p in new.iterdir()if p.is_file()},{r['filename']for r in f['files']}|{'FREEZE.json'})
  for row in f['files']:
   with self.subTest(filename=row['filename']):
    p=new/row['filename'];self.assertFalse(p.is_symlink());raw=p.read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  raw=(old/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),PREDECESSOR);rows=json.loads(raw)['files'];self.assertEqual(len(rows),39)
  for row in rows:self.assertEqual((old/row['filename']).read_bytes(),(new/row['filename']).read_bytes(),row['filename'])
  self.assertEqual(hashlib.sha256((new/'first_digest_uploaded_draft.py').read_bytes()).hexdigest(),DRIVER);self.assertEqual(hashlib.sha256((new/'uploaded_draft_continuation.py').read_bytes()).hexdigest(),HELPER);self.assertEqual(hashlib.sha256((new/'legacy_preview_aliases.py').read_bytes()).hexdigest(),ALIASES);self.assertEqual((gate/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes());self.assertFalse(f['protected_changes']);self.assertEqual(f['production_writes'],0)
  for p in new.glob('*.json'):
   obj=json.loads(p.read_bytes());self.assertFalse(obj.get('environment')=='zenodo.org'and obj.get('method')in{'POST','PUT','DELETE'},p.name)
 def test_portable_complete_accounting_and_five_write_protocol(self):
  gate,old,new=self.paths();env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gate);env['PYTHONDONTWRITEBYTECODE']='1';v=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(new),'-p','test*.py'],cwd=new,env=env,capture_output=True,text=True,timeout=600);self.assertEqual(v.returncode,0,v.stdout+v.stderr);self.assertIn('Ran 277 tests',v.stderr)
if __name__=='__main__':unittest.main()
