"""Pure policy/fake-clock regressions; no network/Core/science admission."""
from pathlib import Path
from copy import deepcopy
import importlib.util
import sys
import time
import threading
import unittest
from unittest.mock import patch
from types import SimpleNamespace

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import owner_content_worker as worker


def content(size):
    return {'role':'content','record_id':'900000','filename':'METHODS_NOTES.zip',
        'url':worker._url('900000','METHODS_NOTES.zip'),'accept':'*/*',
        'max_bytes':size,'expected_bytes':size,'expected_sha256':'0'*64,'expected_md5':'0'*32}


def hello(request,started=1000.0,first=900.0):
    return {'request':request,'request_started_monotonic':started,
        **worker.request_budget(request,started,first,first+900)}


class SizeDeadlinePolicy(unittest.TestCase):
    def test_integer_threshold_archive_size_and_cap(self):
        for size,expected in [(1,120),(5898240,120),(5898241,121),(30500744,496),
                              (37355520,600),(37355521,600),(10**30,600)]:
            with self.subTest(size=size):self.assertEqual(worker.request_allowance(content(size)),expected)
        self.assertEqual(worker.request_allowance(worker.metadata_request('900000','application/json')),120)

    def test_invalid_or_untrusted_request_sizes_are_rejected(self):
        for value in (True,False,0,-1,1.0,'30500744',None):
            with self.subTest(value=value),self.assertRaises(worker.TransportHold):
                worker.request_allowance(content(value))
        for key,value in [('max_bytes',30500745),('expected_sha256','bad'),('accept','application/octet-stream')]:
            request=content(30500744);request[key]=value
            with self.subTest(key=key),self.assertRaises(worker.TransportHold):worker.request_allowance(request)

    def test_long_science_phase_does_not_start_or_reset_owner_clock(self):
        first=None
        def start():
            nonlocal first
            if first is None:first=worker.time.monotonic()
        broker=worker.TransportBroker(operation_nonce='a'*32,token='synthetic-secret',
            source_manifest={'synthetic':True},source_guard=lambda:{'synthetic':True},
            start_get_clock=start,observation_started=lambda:first,
            observation_deadline=lambda:None if first is None else first+900,
            deadline_guard=lambda:None,journal=lambda value:None)
        self.assertIsNone(first) # constructor/scientific waiting starts no OWNER clock
        def no_child(nonce,request,started,deadline):
            return SimpleNamespace(deadline=deadline,request=request)
        with patch.object(broker,'_spawn_child',side_effect=no_child):
            with patch.object(worker.time,'monotonic',return_value=5000.0):
                self.assertEqual(broker._launch(worker.metadata_request('900000','application/json')).deadline,5120)
                self.assertEqual(first,5000)
            with patch.object(worker.time,'monotonic',return_value=5600.0):
                self.assertEqual(broker._launch(content(30500744)).deadline,5900)
                self.assertEqual(first,5000)
        broker.close()

    def test_parent_and_child_exact_deadline_share_first_invocation(self):
        value=hello(content(30500744))
        self.assertEqual(value['absolute_deadline'],1496)
        with patch.object(worker.time,'monotonic',return_value=1100):
            self.assertEqual(worker.validate_job_deadline(value,child_started=1001),1496)
        self.assertEqual(worker.request_budget(content(30500744),1750,900,1800)['absolute_deadline'],1800)

    def test_policy_allowance_operation_and_deadline_forgery_fail_closed(self):
        base=hello(content(30500744))
        variants=[]
        for key,value in [('request_allowance_seconds',497),('request_allowance_seconds',496.0),
                          ('absolute_deadline',1497),('owner_operation_deadline',1801),
                          ('owner_operation_started_monotonic',899),('request_started_monotonic',899)]:
            changed=deepcopy(base);changed[key]=value;variants.append(changed)
        changed=deepcopy(base);changed['request_deadline_policy']['content_max_seconds']=601;variants.append(changed)
        changed=deepcopy(base);changed['request_deadline_policy']['metadata_seconds']=120.0;variants.append(changed)
        changed=deepcopy(base);changed['request']['expected_bytes']+=1;variants.append(changed)
        with patch.object(worker.time,'monotonic',return_value=1100):
            for value in variants:
                with self.subTest(value=value),self.assertRaises(worker.TransportHold):worker.validate_job_deadline(value,child_started=1001)

    def test_exact_cap_does_not_refresh_child_deadline(self):
        value=hello(content(100000000),started=1100,first=1000)
        self.assertEqual(value['absolute_deadline'],1700)
        with patch.object(worker.time,'monotonic',return_value=1699):
            self.assertEqual(worker.validate_job_deadline(value,child_started=1101),1700)
        with patch.object(worker.time,'monotonic',return_value=1700.001),self.assertRaises(worker.TransportHold):
            worker.deadline_check(worker.validate_job_deadline(value,child_started=1101))

    def test_remaining900_and_expiry_are_never_extended(self):
        value=hello(content(30500744),started=1799,first=900)
        self.assertEqual(value['absolute_deadline'],1800)
        with patch.object(worker.time,'monotonic',return_value=1800.001),self.assertRaises(worker.TransportHold):
            worker.deadline_check(worker.validate_job_deadline(value,child_started=1799.5))
        for started,first,end in [(1000,None,1900),(1000,1100,2000),(1000,900,1801),
                                  (float('nan'),900,1800),(1000,900,float('inf'))]:
            with self.subTest(started=started,first=first),self.assertRaises(worker.TransportHold):
                worker.request_budget(content(30500744),started,first,end)

    def test_trusted_closed_allowlist_size_tamper_before_transport(self):
        spec=importlib.util.spec_from_file_location('v013_budget_fixture',HERE/'tests/test_owner_content_worker.py')
        fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
        with fixture.fixture()as f:
            altered=deepcopy(f.descriptors);altered[0]['bytes']+=1
            with self.assertRaises(worker.TransportHold):worker.validate_content_allowlist(altered,f.pairs)
            altered=deepcopy(f.descriptors);altered[0]['source_bindings']=[]
            with self.assertRaises(worker.TransportHold):worker.validate_content_allowlist(altered,f.pairs)

    def test_delayed_hello_cannot_mint_a_post_spawn_request_start(self):
        value=hello(content(100000000),started=1599,first=1000)
        with patch.object(worker.time,'monotonic',return_value=1600),self.assertRaises(worker.TransportHold):
            worker.validate_job_deadline(value,child_started=1000)
        valid=hello(content(100000000),started=999,first=999)
        with patch.object(worker.time,'monotonic',return_value=1598):
            self.assertEqual(worker.validate_job_deadline(valid,child_started=1000),1599)
        with patch.object(worker.time,'monotonic',return_value=1600),self.assertRaises(worker.TransportHold):
            worker.deadline_check(worker.validate_job_deadline(valid,child_started=1000))

    def test_public_child_rejects_forged_allowance_before_bootstrap(self):
        incoming,send=worker.pipe_pair();receive,outgoing=worker.pipe_pair();errors,child_errors=worker.pipe_pair()
        outcome=[];started=time.monotonic();request=content(30500744)
        value={'standard':'VRS-SOURCE-BOUND-OWNER-HTTP-JOB-2','operation_nonce':'a'*32,
            'request_nonce':'b'*32,'request':request,'source_manifest':{},'request_started_monotonic':started,
            **worker.request_budget(request,started,started,started+900)}
        value['request_allowance_seconds']=497
        with patch.object(worker,'bootstrap_sources')as bootstrap:
            thread=threading.Thread(target=lambda:outcome.append(worker.child_main(incoming.fd,outgoing.fd,child_errors.fd)))
            thread.start()
            try:
                worker.write_frame(send,worker.encode_json(value),kind='HELLO',deadline=time.monotonic()+3)
                kind,payload=worker.read_frame(receive,tagged=True,deadline=time.monotonic()+3)
                self.assertEqual(kind,'ERROR')
                self.assertEqual(worker.decode_json(payload),{'exception_type':'TransportHold','infrastructure_hold':True})
                thread.join(3);self.assertFalse(thread.is_alive());self.assertEqual(outcome,[1])
                bootstrap.assert_not_called()
            finally:
                for endpoint in (send,receive,errors):endpoint.close()


if __name__=='__main__':unittest.main()
