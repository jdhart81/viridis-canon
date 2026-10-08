"""Crash/branch selection tests; live checkpoint readback remains mandatory."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import owned_digest_executor as e
import owned_digest_queue as q
import owned_digest_machine as m
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.dir=self.root/'reports/verification-coverage/queue/executions';self.dir.mkdir(parents=True);self.files=[{'name':n,'path':str(self.root/n),'bytes':1,'sha256':'a'*64,'md5':'b'*32}for n in sorted(m.NAMES)];self.plan={'execution_directory':str(self.dir),'approved_inventory':self.files};self.p=self.root/'plan.json';self.p.write_bytes(e.raw_json(self.plan));self.pb=e.binding(self.p);self.ph=m.digest(self.plan);self.binding={'path':str(self.root/'receipt.json'),'sha256':'a'*64};self.initial=m.initial(self.ph,self.files);self.first=m.reserve(self.initial,'NEW_VERSION',self.binding,'start');self.owned=m.finish(self.first,self.binding,self.binding,ownership={'record_id':'23300001','concept_id':'23226760','first_owned_draft':self.binding,'first_owned_legacy_draft':self.binding,'inherited_inventory':[{'filename':x['name'],'filesize':1,'checksum':'b'*32,'id':f'00000000-0000-0000-0000-{i:012d}','links':{}}for i,x in enumerate(self.files)]})
    def tearDown(self):self.tmp.cleanup()
    def add(self,name,state):
        folder=self.dir/name;folder.mkdir();(folder/'PLAN.json').write_bytes(self.p.read_bytes());p=folder/'CHECKPOINT.json';p.write_bytes(e.raw_json(state));return e.binding(p)
    def test_no_owned_execution_selects_none(self):self.assertIsNone(q.latest(self.root,self.pb))
    def test_reserved_then_actual_strict_ownership_selects_strict(self):
        self.add('reserved',self.first);expected=self.add('finished',self.owned);self.assertEqual(q.latest(self.root,self.pb),expected)
    def test_next_reserved_step_is_never_skipped_for_older_pass(self):
        self.add('a',self.owned);reserved=m.reserve(self.owned,m.next_step(self.owned),self.binding,'drop');b=self.add('b',reserved);self.assertEqual(q.latest(self.root,self.pb),b);self.assertRaises(m.MachineHold,m.next_step,reserved)
    def test_uncertain_attempt_selects_hard_stop(self):
        self.add('a',self.first);failed=m.fail(self.first,self.binding,'timeout',uncertain=True);b=self.add('b',failed);self.assertEqual(q.latest(self.root,self.pb),b)
    def test_failed_marker_cannot_be_promoted_to_pass(self):
        failed=m.fail(self.first,self.binding,'content',uncertain=False);self.add('a',failed);self.add('b',self.owned);self.assertRaises(ValueError,q.latest,self.root,self.pb)
    def test_second_child_fork_fails(self):
        self.add('a',self.owned);fork=copy.deepcopy(self.owned);fork['record_id']='23300002';self.add('b',fork);self.assertRaises(ValueError,q.latest,self.root,self.pb)
    def test_reservation_fork_fails(self):
        self.add('a',self.owned);fork=copy.deepcopy(self.owned);fork['attempts'][0]['reservation']['sha256']='b'*64;self.add('b',fork);self.assertRaises(ValueError,q.latest,self.root,self.pb)
    def test_changed_execution_plan_fails(self):
        self.add('a',self.owned);(self.dir/'a/PLAN.json').write_bytes(b'{}');self.assertRaises(ValueError,q.latest,self.root,self.pb)
    def test_partial_execution_without_checkpoint_fails(self):
        folder=self.dir/'a';folder.mkdir();(folder/'PLAN.json').write_bytes(self.p.read_bytes());self.assertRaises(ValueError,q.latest,self.root,self.pb)
    def test_foreign_queue_file_fails(self):
        (self.dir/'foreign.json').write_bytes(b'{}');self.assertRaises(ValueError,q.latest,self.root,self.pb)
if __name__=='__main__':unittest.main()
