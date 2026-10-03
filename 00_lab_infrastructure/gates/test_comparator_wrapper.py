"""Delivery wrapper tests with fake URLs/streams/clocks; no network or Lean."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import urllib.error

PATH=Path(__file__).resolve().parents[2]/'comparator-deploy/viridis-comparator-verify'
loader=importlib.machinery.SourceFileLoader('delivery_wrapper_under_test',str(PATH))
spec=importlib.util.spec_from_loader(loader.name,loader);wrapper=importlib.util.module_from_spec(spec);loader.exec_module(wrapper)
JOB='00000000-0000-4000-8000-000000000001'
PAYLOAD={'challenge':'frozen challenge','solution':'frozen solution','theoremNames':['theorem','witness']}


class Clock:
    value=0
    def now(self):return self.value
    def sleep(self,n):self.value+=n


class Body(io.BytesIO):
    def __init__(self,value):super().__init__(json.dumps(value).encode())


class Stream:
    def __init__(self,clock,events):self.clock=clock;self.events=events;self.closed=False
    def __enter__(self):return self
    def __exit__(self,*args):self.closed=True
    def __iter__(self):
        for wait,line in self.events:
            self.clock.sleep(wait)
            if isinstance(line,Exception):raise line
            yield line


class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.clock=Clock();self.calls=[];self.messages=[];self.events=[];self.polls=[];self.default_poll={'type':'in-progress'}
    def success(self):
        return {'type':'verification-ok','theoremNames':['theorem','witness'],
                'output':'fixture kernels only', 'executionEvidence':{'cacheEligible':False,
                'delivery':{'mode':'FRESH_EXECUTION','servedForRequestId':JOB}}}
    def open(self,request,timeout):
        url=request.full_url if hasattr(request,'full_url') else request
        self.calls.append((url,timeout,request))
        if url.endswith('/start'):
            self.assertEqual(request.get_method(),'POST')
            self.assertEqual(json.loads(request.data),dict(PAYLOAD,project=wrapper.PROJECT))
            return Body({'type':'ready','requestId':JOB})
        if '/track/' in url:
            self.stream=Stream(self.clock,self.events);return self.stream
        if '/result/' in url:
            value=self.polls.pop(0) if self.polls else self.default_poll
            if isinstance(value,Exception):raise value
            return Body(value)
        raise AssertionError('unexpected URL')
    def run_wrapper(self,**kw):
        return wrapper.verify_request(PAYLOAD,open_url=self.open,clock=self.clock.now,
            sleep=self.clock.sleep,operation_seconds=20,stream_seconds=5,
            diagnostic=self.messages.append,**kw)
    def assert_same_id_once(self):
        self.assertEqual(sum(u.endswith('/start') for u,_,_ in self.calls),1)
        self.assertEqual(sum('/track/' in u for u,_,_ in self.calls),1)
        for u,_,_ in self.calls:
            if '/result/' in u or '/track/' in u:self.assertTrue(u.endswith('/'+JOB))

    def test_keepalive_only_deadline_checked_on_every_line(self):
        self.events=[(1,b':\n')]*100
        self.polls=[self.success()]
        rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assertEqual(self.clock.value,5)
        self.assertTrue(self.stream.closed);self.assertTrue(result['recoveredFromTerminalJournal']);self.assert_same_id_once()

    def test_delayed_terminal_polled_until_ready(self):
        self.polls=[{'type':'in-progress'},{'type':'in-progress'},self.success()]
        rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assertEqual(self.clock.value,4)
        self.assertEqual(result['requestId'],JOB);self.assert_same_id_once()

    def test_dropped_stream_polls_same_request(self):
        self.events=[(1,OSError('fixture connection lost'))];self.polls=[self.success()]
        rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assertTrue(self.messages)
        self.assert_same_id_once()

    def test_malformed_line_not_admitted_and_valid_poll_used(self):
        for line in [b'data: {bad}\n',b'\xff\n']:
            with self.subTest(line=line):
                self.setUp();self.events=[(1,line)];self.polls=[self.success()]
                rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assertTrue(self.messages)
                self.assertTrue(result['recoveredFromTerminalJournal']);self.assert_same_id_once()

    def test_pending_until_deadline_is_failure(self):
        rc,result=self.run_wrapper();self.assertEqual(rc,2);self.assertEqual(result['type'],'client-error')
        self.assertEqual(self.clock.value,20);self.assertIn('deadline',result['description']);self.assert_same_id_once()

    def test_http_404_and_malformed_poll_do_not_pass(self):
        self.polls=[urllib.error.HTTPError('fixture',404,'pending',{},None),ValueError('fixture corrupt'),self.success()]
        rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assert_same_id_once()
        self.assertEqual(len(self.messages),2)

    def test_immediate_stream_terminal_preserves_result(self):
        event=self.success();self.events=[(1,('data: '+json.dumps(event)+'\n').encode())]
        rc,result=self.run_wrapper();self.assertEqual(rc,0);self.assertNotIn('recoveredFromTerminalJournal',result)
        self.assertEqual(result,dict(event,requestId=JOB,project=wrapper.PROJECT));self.assert_same_id_once()
        self.assertFalse(any('/result/' in u for u,_,_ in self.calls))

    def test_other_id_and_disk_cache_never_admitted(self):
        for mutation in ['other-request','cache-mode','cache-flag']:
            self.setUp();event=self.success()
            if mutation=='other-request':event['requestId']='00000000-0000-4000-8000-000000000002'
            if mutation=='cache-mode':event['executionEvidence']['delivery']['mode']='CACHE_REUSE'
            if mutation=='cache-flag':event['executionEvidence']['cacheEligible']=True
            self.polls=[event];rc,result=self.run_wrapper();self.assertEqual(rc,2)
            self.assertEqual(result['type'],'client-error');self.assert_same_id_once()

    def test_terminal_verification_failure_remains_failure(self):
        self.polls=[{'type':'verification-failed','output':'fixture failed proof'}]
        rc,result=self.run_wrapper();self.assertEqual(rc,2);self.assertEqual(result['type'],'verification-failed')
        self.assert_same_id_once()

    def test_cli_exactly_one_json_object_on_stdout(self):
        data=io.BytesIO(json.dumps(PAYLOAD).encode())
        stdin=type('Input',(),{'buffer':data})();out=io.StringIO();err=io.StringIO()
        def deliver(payload):
            print('fixture delivery diagnostic',file=wrapper.sys.stderr)
            return 2,{'type':'client-error','description':'fixture failure'}
        with patch.object(wrapper.sys,'stdin',stdin),patch.object(wrapper,'verify_request',side_effect=deliver),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            self.assertEqual(wrapper.verify(),2)
        self.assertEqual(json.loads(out.getvalue())['type'],'client-error');self.assertEqual(len(out.getvalue().splitlines()),1)
        self.assertEqual(err.getvalue(),'fixture delivery diagnostic\n')
