import datetime as dt, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import owned_digest_machine as machine
import weekly_digest_executor as executor

class PublicationDayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.manifest=self.root/'DIGEST_MANIFEST.json';self.manifest.write_text(json.dumps({'public_metadata':{'publication_date':'2026-10-10'}}))
        self.plan={'digest_manifest':executor.binding(self.manifest)}
    def tearDown(self):self.tmp.cleanup()
    def check(self,now):return executor.publication_day(self.root,self.plan,now)
    def test_intended_new_york_publish_day_ready(self):self.assertTrue(self.check('2026-10-10T12:00:00+00:00')['ready'])
    def test_utc_next_day_still_same_new_york_publish_day(self):self.assertTrue(self.check('2026-10-11T02:00:00+00:00')['ready'])
    def test_utc_same_date_earlier_new_york_day_waits(self):self.assertEqual(self.check('2026-10-10T02:00:00+00:00')['wait_status'],'WAIT_PLANNED_NEW_YORK_PUBLISH_DAY')
    def test_before_planned_day_never_publish(self):self.assertFalse(self.check('2026-10-09T12:00:00+00:00')['ready'])
    def test_missed_day_requires_immutable_rebinding(self):self.assertEqual(self.check('2026-10-11T12:00:00+00:00')['wait_status'],'WAIT_IMMUTABLE_PUBLICATION_DATE_REBINDING')
    def test_naive_clock_must_fail(self):self.assertRaises(executor.ExecutionHold,self.check,'2026-10-10T12:00:00')
    def test_missing_explicit_date_must_fail(self):
        self.manifest.write_text(json.dumps({'public_metadata':{}}));self.plan['digest_manifest']=executor.binding(self.manifest);self.assertRaises(executor.ExecutionHold,self.check,'2026-10-10T12:00:00+00:00')
    def test_payload_hash_changed_must_fail(self):
        self.manifest.write_text(json.dumps({'public_metadata':{'publication_date':'2026-10-11'}}));self.assertRaises(executor.ExecutionHold,self.check,'2026-10-10T12:00:00+00:00')

    def test_crosses_midnight_during_read_only_preparation_no_reservation_or_write(self):
        # This fixture isolates the real executor's clocks/stop boundary only;
        # scientific/source admission is deliberately a separate consumer.
        files=[{'name':name,'path':str(self.root/name),'bytes':1,'sha256':'a'*64,'md5':'b'*32}for name in sorted(machine.NAMES)]
        plan={**self.plan,'execution_directory':str(self.root/'reports/verification-coverage'),'start_kind':'NEW_VERSION','approved_inventory':files,'release_week':'2026-W41'}
        path=self.root/'PLAN.json';path.write_bytes(executor.raw_json(plan))
        counts={'admission':0,'before':0,'budget':0,'reserve':0,'network':0}
        class Writer:
            def __init__(self,*args):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def events_and_budget(self,*args):counts['budget']+=1;raise AssertionError('date mismatch must precede reservation budget')
            def reserve(self,*args):counts['reserve']+=1;raise AssertionError('must not reserve')
        class Boundary:
            def before(self,*args):counts['before']+=1
            def command(self,*args):return {'method':'POST','url':'https://zenodo.org/api/deposit/depositions/23246368/actions/publish','body':b'{}','content_type':'application/json','delete_file':None}
        class Runtime:
            d=SimpleNamespace(DigestHold=ValueError)
            require_events=None;require_budget=None
            def admission(self,*args):counts['admission']+=1
            def transport(self,*args):return object()
            def boundary(self,*args):return Boundary()
        clock=iter(['2026-10-11T03:59:59+00:00','2026-10-11T04:00:01+00:00'])
        with patch.object(executor,'require_plan',return_value=self.root),patch.object(executor,'require_command',side_effect=lambda *a:a[-1]),patch.object(machine,'next_step',return_value='PUBLISH'),patch.object(executor,'OwnedJournalWriter',Writer):
            result=executor.execute(self.root,executor.binding(path),self.root/'reports/verification-coverage/midnight','fixture-token-at-least-twenty-four-chars',Runtime(),reviewed_driver_sha256=executor.sha(Path(executor.__file__).resolve()),clock=lambda:next(clock))
        self.assertEqual(result['status'],'WAIT_IMMUTABLE_PUBLICATION_DATE_REBINDING')
        self.assertEqual(result['writes_attempted_this_invocation'],0)
        self.assertEqual(counts,{'admission':2,'before':1,'budget':0,'reserve':0,'network':0})
        checkpoint=json.loads(Path(result['checkpoint']['path']).read_bytes())
        self.assertEqual(checkpoint['phase'],'NOT_STARTED');self.assertEqual(checkpoint['attempts'],[])


class LivePublishBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.files=[{'name':name,'path':str(self.root/name),'bytes':1,'sha256':'a'*64,'md5':'b'*32}for name in sorted(machine.NAMES)]
        manifest=self.root/'DIGEST_MANIFEST.json';manifest.write_bytes(executor.raw_json({'public_metadata':{'publication_date':'2026-10-10'}}))
        self.plan={'digest_manifest':executor.binding(manifest),'execution_directory':str(self.root/'reports/verification-coverage'),'start_kind':'NEW_VERSION','approved_inventory':self.files,'release_week':'2026-W41'}
        self.plan_path=self.root/'PLAN.json';self.plan_path.write_bytes(executor.raw_json(self.plan))
        placeholder=self.root/'fixture-receipt.json';placeholder.write_bytes(executor.raw_json({'fixture':'pure state/order tests; no scientific or API admission'}));binding=executor.binding(placeholder)
        state=machine.initial(machine.digest(self.plan),self.files)
        for i,step in enumerate(machine.step_order('NEW_VERSION')[:-1]):
            state=machine.reserve(state,step,binding,'fixture-stage:'+str(i))
            owned={'record_id':'23246368','concept_id':'23226760','first_owned_draft':binding,'first_owned_legacy_draft':binding,'inherited_inventory':[{'filename':row['name'],'filesize':row['bytes'],'checksum':row['md5'],'id':'fixture-'+str(i),'links':{}}for i,row in enumerate(self.files)]}if step=='NEW_VERSION'else None
            state=machine.finish(state,binding,binding,ownership=owned)
        self.assertEqual(machine.next_step(state),'PUBLISH')
        self.ready_path=self.root/'READY_CHECKPOINT.json';self.ready_path.write_bytes(executor.raw_json(state))
    def tearDown(self):self.tmp.cleanup()
    def run_clock_case(self,timestamps):
        # Actual executor and actual closed machine; fixture only replaces
        # independent scientific admission, I/O and journal accounting.
        counts={'prewrite':0,'reserve':0,'network':0};test=self
        class Writer:
            def __init__(self,*args):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def events_and_budget(self,*args):return [],{'used':0,'remaining_including_next':10}
            def reserve(self,method,url,body,predicted,at,operation,compute):
                counts['reserve']+=1
                reservation=test.root/'CHARGED_RESERVATION.json';reservation.write_bytes(executor.raw_json({'fixture':'charged no-retry intent','operation_id':operation,'at_utc':at}))
                return {'reservation':executor.binding(reservation)}
        class Transport:
            def __init__(self,out):self.out=Path(out);self.out.mkdir();self.sequence=0
            def request(self,*args,**kwargs):counts['network']+=1;raise AssertionError('expired publish day must never reach network')
        class Boundary:
            def before(self,*args):pass
            def command(self,*args):return {'method':'POST','url':'https://zenodo.org/api/deposit/depositions/23246368/actions/publish','body':b'{}','content_type':'application/json','delete_file':None}
            def after(self,*args):raise AssertionError('must never reach readback without a request')
        def prewrite(*args,**kwargs):counts['prewrite']+=1
        class Runtime:
            d=SimpleNamespace(DigestHold=ValueError,prewrite=prewrite,require_write_budget=lambda *a,**kw:None)
            require_events=None;require_budget=None
            def admission(self,*args):pass
            def replay_checkpoint(self,*args):pass
            def transport(self,token,out):return Transport(out)
            def boundary(self,*args):return Boundary()
        clock=iter(timestamps)
        with patch.object(executor,'require_plan',return_value=self.root),patch.object(executor,'require_command',side_effect=lambda *a:a[-1]),patch.object(executor,'OwnedJournalWriter',Writer):
            result=executor.execute(self.root,executor.binding(self.plan_path),self.root/'reports/verification-coverage/execute','fixture-token-at-least-twenty-four-chars',Runtime(),checkpoint=executor.binding(self.ready_path),reviewed_driver_sha256=executor.sha(Path(executor.__file__).resolve()),clock=lambda:next(clock))
        return result,counts,json.loads(Path(result['checkpoint']['path']).read_bytes())
    def test_clock_advances_during_prewrite_no_charge_or_request(self):
        result,counts,state=self.run_clock_case(['2026-10-11T03:59:55+00:00','2026-10-11T03:59:56+00:00','2026-10-11T04:00:01+00:00'])
        self.assertEqual(result['status'],'WAIT_IMMUTABLE_PUBLICATION_DATE_REBINDING');self.assertEqual(result['writes_attempted_this_invocation'],0)
        self.assertEqual(counts,{'prewrite':1,'reserve':0,'network':0});self.assertFalse((self.root/'CHARGED_RESERVATION.json').exists())
        self.assertEqual(state,json.loads(self.ready_path.read_bytes()));self.assertEqual(machine.next_step(state),'PUBLISH')
    def test_clock_advances_during_reservation_charge_retained_known_unsent_hold(self):
        result,counts,state=self.run_clock_case(['2026-10-11T03:59:55+00:00','2026-10-11T03:59:56+00:00','2026-10-11T03:59:57+00:00','2026-10-11T04:00:01+00:00'])
        self.assertEqual(result['status'],'HOLD');self.assertEqual(result['writes_attempted_this_invocation'],1)
        self.assertEqual(counts,{'prewrite':1,'reserve':1,'network':0});self.assertTrue((self.root/'CHARGED_RESERVATION.json').exists())
        self.assertEqual(state['phase'],'HOLD');self.assertEqual(state['attempts'][-1]['step'],'PUBLISH');self.assertEqual(state['attempts'][-1]['outcome'],'HOLD');self.assertIsNone(state['attempts'][-1]['transport']);self.assertIn('HOLD_PUBLISH_DAY_CHANGED_AFTER_RESERVATION',state['failure'])
        self.assertRaises(machine.MachineHold,machine.next_step,state)

if __name__=='__main__':unittest.main()
