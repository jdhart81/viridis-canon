"""Exact reviewed publisher source closure and portable offline protocol tests.

These tests grant no scientific admission or live Zenodo publication evidence.
"""
from pathlib import Path
from test_digest_historical_adapter import historical_protocol
import hashlib,json,os,subprocess,sys,unittest

FREEZE_SHA256 = 'f4468f5380fae88304c31c61494f43f97551fc279484a7756966a7e91c819c4b'
NAMES = frozenset(['readonly_account.py', 'mutation_journal_writer.py', 'digest_metadata.py', 'first_digest_state.py', 'first_digest_publisher.py', 'publisher_previews.py', 'publisher_recovery.py', 'test_coordinator.py', 'test_publisher_guards.py', 'INHERITED_SOURCES.json', 'TESTS.json', 'ROOT_EXECUTION_NOTES.md', 'API_ENCODING.md'])

class FirstMethodsDigestPublisherTests(unittest.TestCase):
 def test_reviewed_snapshot_closure_and_portable_offline_protocol(self):
  gates=Path(__file__).resolve().parent
  source=gates/'production_snapshots/phase7-20261007-first-digest/after/production_execution_dependencies'
  raw=(source/'FREEZE.json').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),FREEZE_SHA256)
  frozen=json.loads(raw)
  self.assertEqual(frozen['status'],'TESTED_OFFLINE_NOT_EXECUTED')
  self.assertEqual({row['filename']for row in frozen['files']},NAMES)
  self.assertEqual(len(frozen['files']),len(NAMES))
  self.assertEqual({p.name for p in source.iterdir()if p.is_file()},NAMES|{'FREEZE.json'})
  for row in frozen['files']:
   with self.subTest(source=row['filename']):
    path=source/row['filename'];self.assertFalse(path.is_symlink());data=path.read_bytes()
    self.assertEqual(len(data),row['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
  env=os.environ.copy();env['PHASE7_TEST_GATES']=str(gates);env['PYTHONDONTWRITEBYTECODE']='1'
  result=historical_protocol(gates,source)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn('Ran 94 tests',result.stderr)

if __name__=='__main__':unittest.main()
