"""Exact source-only archive-absent successor and portable accounting closure."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
from test_digest_historical_adapter import historical_protocol
FREEZE='fb806d9259278a3900284054a6608da9d2f6aab3a966926f42adf5852777729c'
PREDECESSOR='934a460b1796495616f4c12cecdaf31d0159b78f5008555e0d784846bd282e0c'
DRIVER='d29358c61c86273e1857965a7c2b1a7ef39ddc53e62d553778b7d8f853dae82c'
HELPER='3ef52280d4be92d04e2047a54e100f258ec23d7ab6577928be8e35114540d316'
WAIT='6c55843295c9f3eca72d376afaca96032d19cac61fec335f401ed31f9b743f36'
class ThreeFileContinuationSnapshotTests(unittest.TestCase):
 def paths(self):
  gate=Path(__file__).resolve().parent;s=gate/'production_snapshots';return gate,s/'phase7-20261007-uploaded-draft-continuation-v001/after/production_execution_dependencies',s/'phase7-20261008-three-file-draft-continuation-v001/after/production_execution_dependencies'
 def test_exact_immutable_snapshot_preserves_every_predecessor_file(self):
  gate,old,new=self.paths();raw=(new/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FREEZE);f=json.loads(raw);self.assertEqual(f['standard'],'VRS_SOURCE_ONLY_THREE_FILE_DRAFT_CONTINUATION_FREEZE_1');self.assertEqual(f['status'],'SOURCE_ONLY_NOT_EXECUTED');self.assertEqual(len(f['files']),57);self.assertEqual(len({r['filename']for r in f['files']}),57);self.assertEqual({p.name for p in new.iterdir()if p.is_file()},{r['filename']for r in f['files']}|{'FREEZE.json'})
  for row in f['files']:
   with self.subTest(filename=row['filename']):
    p=new/row['filename'];self.assertFalse(p.is_symlink());raw=p.read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  raw=(old/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),PREDECESSOR);rows=json.loads(raw)['files'];self.assertEqual(len(rows),48)
  for row in rows:self.assertEqual((old/row['filename']).read_bytes(),(new/row['filename']).read_bytes(),row['filename'])
  self.assertEqual((new/'PREDECESSOR_FREEZE.json').read_bytes(),(old/'FREEZE.json').read_bytes());self.assertEqual(hashlib.sha256((new/'first_digest_three_file_draft.py').read_bytes()).hexdigest(),DRIVER);self.assertEqual(hashlib.sha256((new/'three_file_draft_continuation.py').read_bytes()).hexdigest(),HELPER);self.assertEqual(hashlib.sha256((new/'owned_archive_wait.py').read_bytes()).hexdigest(),WAIT);self.assertEqual((gate/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes());self.assertFalse(f['protected_changes']);self.assertFalse(f['activated_flat_modules_changed']);self.assertEqual(f['production_writes'],0)
  for p in new.glob('*.json'):
   obj=json.loads(p.read_bytes());self.assertFalse(obj.get('environment')=='zenodo.org'and obj.get('method')in{'POST','PUT','DELETE'},p.name)
 def test_portable_complete_accounting_and_four_write_protocol(self):
  gate,old,new=self.paths();env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gate);env['PYTHONDONTWRITEBYTECODE']='1';v=historical_protocol(gate,new);self.assertEqual(v.returncode,0,v.stdout+v.stderr);self.assertIn('Ran 315 tests',v.stderr)
if __name__=='__main__':unittest.main()
