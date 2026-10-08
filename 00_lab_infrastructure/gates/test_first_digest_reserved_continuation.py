"""Exact source-only reserved continuation and portable protocol closure."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
from test_digest_historical_adapter import historical_protocol
FREEZE='41d96e8f52a19b77df80e91579620f9abf00127c7b1987d109eaa824635d32ed'
PREDECESSOR='bea96ef33711568612d1439f2b2be6ae9866e0e73f018b8e516ce0c16168ee69'
DRIVER='da56918eb1a4a21ab912c8c98ca87e98e80e589b4e5d9212ce812db806ddfd79'
HELPER='31cd5b5cc9b708ae9ed78fa4c469bc3e74008e365dc7ffdc76f9b0ccda458d3c'
class ReservedContinuationSnapshotTests(unittest.TestCase):
 def paths(self):
  gate=Path(__file__).resolve().parent;s=gate/'production_snapshots';return gate,s/'phase7-20261007-existing-draft-doi-recovery-v002/after/production_execution_dependencies',s/'phase7-20261007-reserved-draft-continuation-v001/after/production_execution_dependencies'
 def test_exact_immutable_snapshot_preserves_every_predecessor_file(self):
  gate,old,new=self.paths();raw=(new/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FREEZE);f=json.loads(raw);self.assertEqual(len(f['files']),39);self.assertEqual(len({r['filename']for r in f['files']}),39);self.assertEqual({p.name for p in new.iterdir()if p.is_file()},{r['filename']for r in f['files']}|{'FREEZE.json'})
  for row in f['files']:
   with self.subTest(filename=row['filename']):
    p=new/row['filename'];self.assertFalse(p.is_symlink());raw=p.read_bytes();self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  raw=(old/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),PREDECESSOR);rows=json.loads(raw)['files'];self.assertEqual(len(rows),31)
  for row in rows:self.assertEqual((old/row['filename']).read_bytes(),(new/row['filename']).read_bytes(),row['filename'])
  self.assertEqual(hashlib.sha256((new/'first_digest_reserved_draft.py').read_bytes()).hexdigest(),DRIVER);self.assertEqual(hashlib.sha256((new/'reserved_draft_continuation.py').read_bytes()).hexdigest(),HELPER);self.assertEqual((gate/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes());self.assertFalse(f['protected_changes']);self.assertEqual(f['production_writes'],0)
  for p in new.glob('*.json'):
   obj=json.loads(p.read_bytes());self.assertFalse(obj.get('environment')=='zenodo.org'and obj.get('method')in{'POST','PUT','DELETE'},p.name)
 def test_portable_complete_accounting_and_seven_write_protocol(self):
  gate,old,new=self.paths();env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gate);env['PYTHONDONTWRITEBYTECODE']='1';v=historical_protocol(gate,new);self.assertEqual(v.returncode,0,v.stdout+v.stderr);self.assertIn('Ran 248 tests',v.stderr)
if __name__=='__main__':unittest.main()
