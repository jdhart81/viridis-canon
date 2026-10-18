"""Real evidence, exact threshold, durable state, and checkpoint-boundary checks."""
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checkpoint_advisory as advisory
import scheduler_liveness as lane_module
from scheduler_liveness import LivenessHold, RequestIdentity, SchedulerLane, file_digest
import test_checkpoint_advisory as fixture
import test_checkpoint_adapter as adapter_fixture
from liveness_fixtures import write_rejection


class AuditAdvisoryTests(unittest.TestCase):
    setUp = fixture.AdvisoryCheckpointTests.setUp
    patched_namespace = fixture.AdvisoryCheckpointTests.patched_namespace

    def head(self, current, **kwargs):
        try:
            return advisory.fifo_head(self.root,current,**kwargs)
        except Exception as error:
            self.fail("canonical FIFO report raised instead of retaining all required fields: "+type(error).__name__)

    def test_B1_all_five_fields_are_explicit_without_input_producer(self):
        result = self.head( json.loads(self.checkpoint.read_text()))
        self.assertEqual(result['run_id'], 'Run-194')
        for key in ('held_since_utc', 'failing_goal', 'candidate_sha256', 'provider_receipt'):
            self.assertEqual(result[key], 'UNAVAILABLE')
        self.assertIsNone(result['held_hours'])
        self.assertIsNone(result['held_seconds'])

    def test_B1_hash_bound_premise_hold_derives_production_head_without_slo_inputs(self):
        folder = self.pipeline / 'lean_certificates/Run-194'
        (folder / 'ENGINE3_VERIFICATION_REQUEST.json').write_text('{}')
        (folder / 'VERIFICATION_STATEMENT.lean').write_text('sealed statement')
        checker = self.pipeline / 'verification_coverage_gates/premise_declaration.py'
        checker.parent.mkdir(); checker.write_text('pure checker source')
        hold = {'schema_version':'VRS-CERTIFICATION-PREMISE-HOLD-1','run_id':'Run-194',
            'recorded_at_utc':'2026-10-15T00:00:00Z','status':'HOLD_PREMISE_DECLARATION',
            'terminal_for_sealed_object':True,'certificate_issued':False,'checker_result':{'status':'HOLD'},
            'bindings':{key:file_digest(path) for key,path in (
                ('request_sha256', folder/'ENGINE3_VERIFICATION_REQUEST.json'),
                ('formal_statement_sha256',folder/'VERIFICATION_STATEMENT.lean'),
                ('candidate_sha256',folder/'VERIFICATION_CANDIDATE.lean'),('premise_checker_sha256',checker))}}
        (folder/'PREMISE_DECLARATION_HOLD_FIXTURE.json').write_text(json.dumps(hold))
        now=datetime(2026,10,16,tzinfo=timezone.utc)
        result=self.head(json.loads(self.checkpoint.read_text()),as_of=now)
        self.assertEqual(result['status'],'ALERT');self.assertEqual(result['held_seconds'],86400)
        self.assertEqual(result['candidate_sha256'],hold['bindings']['candidate_sha256'])
        self.assertEqual(result['evidence_basis'],'HASH_BOUND_PREMISE_HOLD')
        self.assertEqual(result['provider_receipt'],'UNAVAILABLE')
        self.assertEqual(result['failing_goal'],'UNAVAILABLE')
        (folder/'VERIFICATION_CANDIDATE.lean').write_text('changed')
        result=self.head(json.loads(self.checkpoint.read_text()),as_of=now)
        self.assertEqual(result['status'],'UNAVAILABLE');self.assertIsNone(result['held_hours'])

    def test_exact_seconds_do_not_alert_on_rounded_23_9999_hours(self):
        (self.pipeline/'PIPELINE_SLO_INPUTS.json').write_text(json.dumps({'fifo_head':{
            'run_id':'Run-194','held_since_utc':'2026-10-15T00:00:00Z'}}))
        current=json.loads(self.checkpoint.read_text());edge=datetime(2026,10,16,tzinfo=timezone.utc)
        before=self.head(current,as_of=edge-timedelta(microseconds=1))
        self.assertEqual(before['held_hours'],24.0)
        self.assertEqual(before['status'],'BELOW_ALERT_THRESHOLD')
        self.assertEqual(self.head(current,as_of=edge)['status'],'ALERT')
        (self.pipeline/'PIPELINE_SLO_INPUTS.json').write_text(json.dumps({'fifo_head':{'run_id':'Run-194'}}))
        self.assertIsNone(self.head(current,as_of=edge)['held_hours'])

    def test_R14_linter_receives_two_debts_only(self):
        current=json.loads(self.checkpoint.read_text())
        current['science']['certification']['backlog_runs']=['Run-194','Run-195','Run-196']
        self.checkpoint.write_text(json.dumps(current))
        for run in ('Run-195','Run-196'):
            path=self.pipeline/'lean_certificates'/run/'VERIFICATION_CANDIDATE.lean'
            path.parent.mkdir();path.write_text('theorem fixture : 1 = 1 := rfl')
        with patch.object(advisory,'PLAYBOOK_SHA256',file_digest(self.playbook)):
            advisory.observe(self.root,self.checkpoint)
        rows=json.loads((self.checkpoint.parent/'LEAN_REPAIR_LINT_ADVISORY.json').read_text())['results']
        self.assertEqual([row['run_id'] for row in rows],['Run-194','Run-195'])

    def test_report_refuses_symlink_parent_and_output_without_touching_target(self):
        outside=self.root/'outside';outside.mkdir();victim=outside/'victim';victim.write_text('original')
        link=self.pipeline/'link';link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(OSError): advisory.report(link/'victim',{'changed':True},self.root)
        output=self.pipeline/'output';output.symlink_to(victim)
        with self.assertRaises(ValueError): advisory.report(output,{'changed':True},self.root)
        self.assertEqual(victim.read_text(),'original')

    def test_R16_hook_subprocess_has_exact_15_second_bound(self):
        namespace=self.patched_namespace();calls=[]
        with patch('subprocess.run',side_effect=lambda *a,**kw:calls.append(kw)):
            namespace['checkpoint_advisory_after_checkpoint'](self.checkpoint)
        self.assertEqual(len(calls),1);self.assertEqual(calls[0]['timeout'],15)

    def test_R17_hold_exit_and_advisory_after_drain(self):
        from types import SimpleNamespace
        namespace=self.patched_namespace();calls=[]
        namespace['checkpoint_advisory_after_checkpoint']=lambda path:calls.append('advisory')
        def drain(*args): calls.append('drain');return {'status':'HOLD'}
        with patch.dict(sys.modules,{'checkpoint_certification_lane':SimpleNamespace(drain_checkpoint=drain)}), \
             patch.object(sys,'argv',['checkpoint','--drain-certification',str(self.checkpoint),'--certification-queue','queue.json']):
            self.assertEqual(namespace['main'](),2)
        self.assertEqual(calls,['drain','advisory'])

    def test_actual_reconcile_cli_uses_inactive_action_then_advisory(self):
        from types import SimpleNamespace
        namespace=self.patched_namespace();calls=[]
        namespace['checkpoint_advisory_after_checkpoint']=lambda path:calls.append('advisory')
        def reconcile(*args): calls.append('reconcile');return {'status':'HOLD'}
        with patch.dict(sys.modules,{'checkpoint_certification_lane':SimpleNamespace(reconcile_checkpoint=reconcile)}), \
             patch.object(sys,'argv',['checkpoint','--reconcile-certification',str(self.checkpoint),'--certification-queue','queue.json']):
            self.assertEqual(namespace['main'](),2)
        self.assertEqual(calls,['reconcile','advisory'])


class DurableAndTerminalTests(unittest.TestCase):
    setUp=adapter_fixture.CheckpointAdapterTests.setUp
    write_queue=adapter_fixture.CheckpointAdapterTests.write_queue

    def test_mac_full_flush_is_used_when_available(self):
        with patch.object(lane_module.sys,'platform','darwin'), patch.object(lane_module.fcntl,'F_FULLFSYNC',999,create=True), \
             patch.object(lane_module.os,'fsync') as fsync, patch.object(lane_module.fcntl,'fcntl') as full:
            lane_module.durable_file_sync(17)
        fsync.assert_called_once_with(17);full.assert_called_once_with(17,999)

    def test_R11_rejection_goal_must_be_in_authenticated_provider_output(self):
        import checkpoint_certification_lane as adapter
        identity,paths=adapter.identity_for(self.entries[0],self.pipeline)
        receipt=Path(self.entries[0]['receipt_output']);write_rejection(identity,self.entries[0])
        with SchedulerLane(self.pipeline/'lane').checkpoint() as lane:
            lane.reserve(identity)
            with self.assertRaisesRegex(LivenessHold,'REJECTION_GOAL_BINDING'):
                lane.record_rejection(identity,provider_receipt=receipt,provider_receipt_sha256=file_digest(receipt),failing_goal='different invented goal')

    def test_forged_terminal_row_cannot_free_capacity_on_resume(self):
        import checkpoint_certification_lane as adapter
        identities=[adapter.identity_for(entry,self.pipeline)[0] for entry in self.entries]
        root=self.pipeline/'lane'
        with SchedulerLane(root).checkpoint() as lane:
            for identity in identities: lane.reserve(identity)
        terminal=root/'terminal';terminal.mkdir()
        (terminal/(identities[0].key+'.json')).write_text(json.dumps({
            'identity':asdict(identities[0]),'standard':'VRS-IMMUTABLE-REJECTED-REQUEST-1',
            'provider_receipt_sha256':'f'*64,'failing_goal':'forged'}))
        third=RequestIdentity('Run-196','c'*64,'d'*64,'e'*64,'f'*64,'a'*64)
        with SchedulerLane(root).checkpoint() as lane:
            with self.assertRaisesRegex(LivenessHold,'TERMINAL_RECEIPT'):lane.reserve(third)

    def test_hash_consistent_forged_terminal_receipt_cannot_free_capacity(self):
        import checkpoint_certification_lane as adapter
        identities=[adapter.identity_for(entry,self.pipeline)[0] for entry in self.entries]
        root=self.pipeline/'lane'
        with SchedulerLane(root).checkpoint() as lane:
            for identity in identities:lane.reserve(identity)
        receipt=self.pipeline/'fake-provider.json'
        receipt.write_text(json.dumps({'status':'HOLD','provider_response':{'output':'forged goal'}}))
        terminal=root/'terminal';terminal.mkdir()
        (terminal/(identities[0].key+'.json')).write_text(json.dumps({
            'identity':asdict(identities[0]),'standard':'VRS-IMMUTABLE-REJECTED-REQUEST-1',
            'provider_receipt':str(receipt),'provider_receipt_sha256':file_digest(receipt),'failing_goal':'forged goal'}))
        third=RequestIdentity('Run-196','c'*64,'d'*64,'e'*64,'f'*64,'a'*64)
        with SchedulerLane(root).checkpoint() as lane:
            with self.assertRaises(LivenessHold):lane.reserve(third)

    def test_immutable_json_replay_refuses_an_identical_symlink(self):
        value={'exact':'immutable'}
        target=self.pipeline/'real.json'
        lane_module.immutable_json(target,value)
        link=self.pipeline/'link.json';link.symlink_to(target)
        with self.assertRaisesRegex(LivenessHold,'RECEIPT_SYMLINK'):
            lane_module.immutable_json(link,value)
