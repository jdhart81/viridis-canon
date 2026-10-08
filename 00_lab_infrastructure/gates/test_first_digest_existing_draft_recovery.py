"""Exact source-only recovery snapshot and portable offline protocol closure."""
import hashlib,json,os,subprocess,sys,unittest
from pathlib import Path
FREEZE='bea96ef33711568612d1439f2b2be6ae9866e0e73f018b8e516ce0c16168ee69'
PREDECESSOR='c8d5c371830c7ade86363e9274dd1a7b9d07bf4ee387ff4ae3c76117eaa41c4f'
DRIVER='eec6af9af33ecc65f782f76bcabd48dd9ed0e97038862414f8ab6b3532916f5a'
RESERVATION='5916611b496e4a9b14bdfb27ad3f2c2d6914d7a8f8d546bc23597adbc726fbc9'

class OwnDraftRecoverySnapshotTests(unittest.TestCase):
 def paths(self):
  gate=Path(__file__).resolve().parent;s=gate/'production_snapshots'
  return gate,s/'phase7-20261007-first-digest-community-api-v001/after/production_execution_dependencies',s/'phase7-20261007-existing-draft-doi-recovery-v002/after/production_execution_dependencies'
 def test_exact_immutable_source_snapshot_preserves_every_inherited_file(self):
  gate,old,new=self.paths();raw=(new/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),FREEZE);freeze=json.loads(raw);rows=freeze['files'];self.assertEqual(len(rows),31);self.assertEqual(len({r['filename']for r in rows}),31)
  self.assertEqual({p.name for p in new.iterdir()if p.is_file()},{r['filename']for r in rows}|{'FREEZE.json'})
  for row in rows:
   with self.subTest(filename=row['filename']):
    p=new/row['filename'];self.assertFalse(p.is_symlink());value=p.read_bytes();self.assertEqual(len(value),row['bytes']);self.assertEqual(hashlib.sha256(value).hexdigest(),row['sha256'])
  oldraw=(old/'FREEZE.json').read_bytes();self.assertEqual(hashlib.sha256(oldraw).hexdigest(),PREDECESSOR)
  oldrows=json.loads(oldraw)['files'];self.assertEqual(len(oldrows),21)
  for row in oldrows:self.assertEqual((old/row['filename']).read_bytes(),(new/row['filename']).read_bytes(),row['filename'])
  self.assertEqual(hashlib.sha256((new/'first_digest_existing_draft.py').read_bytes()).hexdigest(),DRIVER);self.assertEqual(hashlib.sha256((new/'draft_reservation.py').read_bytes()).hexdigest(),RESERVATION)
  self.assertEqual((gate/'digest_metadata.py').read_bytes(),(new/'digest_metadata.py').read_bytes())
  self.assertEqual(freeze['production_writes'],0);self.assertFalse(freeze['protected_changes']);self.assertFalse(freeze['automatic_retry'])
  # Newly adopted JSON source must not masquerade as another actual attempt.
  for p in new.glob('*.json'):
   obj=json.loads(p.read_bytes());self.assertFalse(obj.get('environment')=='zenodo.org'and obj.get('method')in{'POST','PUT','DELETE'},p.name)
 def test_portable_real_accounting_and_closed_eight_write_protocol(self):
  gate,old,new=self.paths();env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gate);env['PYTHONDONTWRITEBYTECODE']='1'
  result=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',str(new),'-p','test*.py'],cwd=new,env=env,capture_output=True,text=True,timeout=600)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('Ran 204 tests',result.stderr)

if __name__=='__main__':unittest.main()
