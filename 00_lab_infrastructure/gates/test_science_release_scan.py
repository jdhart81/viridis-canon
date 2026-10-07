import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch,Mock
import science_release_queue as q
class ScanTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name).resolve();self.ledger=self.root/'ledger.json'
  self.ledger.write_text(json.dumps({'run_entities':[{'id':x}for x in ['Run-188','Run-189','Run-190','Run-900','Run-META-001']]}))
  self.track=Mock();self.track.current_certificate.side_effect=lambda root,rid: (Path('certificate'),{})if rid=='Run-190'else None
  self.consumer={'proof_track':self.track}
 def test_delayed_certified_run_after_cutover_is_intaken(self):
  with patch.object(q,'load_existing_consumers',return_value=self.consumer),patch.object(q,'enqueue',return_value={'status':'ENQUEUED_REPORT_ONLY','entry':'entry'})as enq:
   r=q.scan_new_nightly(self.root,self.ledger,'Run-188');self.assertEqual(r['status'],'REPORT_ONLY_SCAN_COMPLETE');enq.assert_called_once_with(self.root,'Run-190',self.ledger,None);self.assertFalse(r['publication_enabled'])
 def test_every_certificate_not_only_latest(self):
  self.track.current_certificate.side_effect=lambda root,rid:(Path('certificate'),{})
  with patch.object(q,'load_existing_consumers',return_value=self.consumer),patch.object(q,'enqueue',return_value={'status':'ENQUEUED_REPORT_ONLY','entry':'entry'})as enq:
   r=q.scan_new_nightly(self.root,self.ledger,'Run-188');self.assertEqual(enq.call_count,2);self.assertEqual(len(r['rows']),2)
 def test_foundational_cutover_and_bad_run_hold(self):
  for value in ['Run-999','Run-899','../Run-188','188']:
   with self.subTest(value=value),self.assertRaises(ValueError):q.scan_new_nightly(self.root,self.ledger,value)
 def test_enqueue_hold_propagates_no_stage(self):
  with patch.object(q,'load_existing_consumers',return_value=self.consumer),patch.object(q,'enqueue',return_value={'status':'HOLD'}),patch('science_release_stage.stage_current_entry')as stage:
   r=q.scan_new_nightly(self.root,self.ledger,'Run-188',stage=True);self.assertEqual(r['status'],'HOLD');stage.assert_not_called()
 def test_renderer_hold_propagates(self):
  with patch.object(q,'load_existing_consumers',return_value=self.consumer),patch.object(q,'enqueue',return_value={'status':'ENQUEUED_REPORT_ONLY','entry':'entry'}),patch('science_release_stage.stage_current_entry',side_effect=ValueError('bad PDF')):
   r=q.scan_new_nightly(self.root,self.ledger,'Run-188',stage=True);self.assertEqual(r['status'],'HOLD');self.assertIn('bad PDF',r['rows'][0]['cause'])
 def test_stage_same_package_path(self):
  with patch.object(q,'load_existing_consumers',return_value=self.consumer),patch.object(q,'enqueue',return_value={'status':'ENQUEUED_REPORT_ONLY','entry':'entry'}),patch('science_release_stage.stage_current_entry',return_value={'state':'STAGED_PENDING_INDEPENDENT_CLAUDE_AUDIT'})as stage:
   r=q.scan_new_nightly(self.root,self.ledger,'Run-188',stage=True);stage.assert_called_once_with(self.root,'entry',self.ledger);self.assertFalse(r['publication_enabled'])
if __name__=='__main__':unittest.main()
