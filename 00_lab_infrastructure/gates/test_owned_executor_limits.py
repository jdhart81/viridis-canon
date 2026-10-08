"""TMP-only transport fixtures test scheduling; never scientific admission."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import methods_digest as d
import mutation_journal_writer as journal
import owned_digest_machine as m
import owned_digest_executor as e

class FixtureTransport:
    def __init__(self,out):self.out=Path(out);self.out.mkdir();self.sequence=0;self.calls=[]
    def request(self,method,url,body=None,expected_sha256=None,content_type=None,authorized=False,accept=None):
        self.sequence+=1;self.calls.append((method,url));value={'environment':'zenodo.org','method':method,'url':url,'status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'request_body_sha256':expected_sha256,'response_sha256':'a'*64,'response':{'fixture':True}};e.immutable(self.out/f'{self.sequence:03d}_{method}.json',e.raw_json(value));return value['response']
class FixtureBoundary:
    def __init__(self,t,out,files,fail=False):self.t=t;self.out=out;self.files=files;self.n=0;self.fail=fail
    def before(self,state):pass
    def command(self,state,step):return {'method':'POST','url':'https://zenodo.org/api/deposit/depositions/23226761/actions/newversion','body':b'{}','content_type':'application/json','delete_file':None}
    def after(self,state,step,response,own):
        if self.fail:raise ValueError('fixture main bytes mismatch')
        self.n+=1;p=self.out/f'fixture_validation{self.n}.json';e.immutable(p,e.raw_json({'fixture_only':True}));ownership=None
        if step=='NEW_VERSION':ownership={'record_id':'23299999','concept_id':'23226760','first_owned_draft':own,'first_owned_legacy_draft':own,'inherited_inventory':[{'filename':x['name'],'filesize':x['bytes'],'checksum':x['md5'],'id':f'00000000-0000-0000-0000-{i:012d}','links':{}}for i,x in enumerate(self.files)]}
        return e.binding(p),ownership
class FixtureRuntime:
    def __init__(self,root,files,fail=False):self.root=root;self.files=files;self.d=d;self.fail=fail;self.t=None
    def admission(self,*args):pass
    def replay_checkpoint(self,*args):pass
    def require_events(self,root,at):
        a=json.loads((self.root/journal.JOURNAL).read_bytes());return [json.loads(Path(r['path']).read_bytes())for r in a['reservations']]
    def require_budget(self,root,method,at):return d.require_write_budget(self.require_events(root,at),method,at,complete=True)
    def transport(self,token,out):self.t=FixtureTransport(out);return self.t
    def boundary(self,plan,package,t,out):return FixtureBoundary(t,out,self.files,self.fail)
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();p=self.root/journal.JOURNAL;p.parent.mkdir(parents=True);p.write_bytes(journal.raw_json({'standard':'VRS_PHASE7_MUTATION_JOURNAL_INDEX_1','status':'ACTIVE','baseline':{},'reservations':[],'updated_at_utc':'2026-10-08T00:00:00+00:00'}));self.files=[{'name':n,'path':str(self.root/n),'bytes':1,'sha256':'a'*64,'md5':'b'*32}for n in sorted(m.NAMES)];self.plan={'execution_directory':str(self.root/'reports/verification-coverage'),'start_kind':'NEW_VERSION','approved_inventory':self.files,'release_week':'2026-W41','predecessor_record_id':'23226761'};self.p=self.root/'PLAN.json';self.p.write_bytes(e.raw_json(self.plan))
    def tearDown(self):self.tmp.cleanup()
    def run_engine(self,out,runtime,checkpoint=None,day='2026-10-08'):
        # Production source/origin/readback admission is a separate required
        # integration proof. Fixture tests isolate only limit/accounting code.
        with patch.object(e,'require_plan',return_value=self.root),patch.object(e,'require_command',side_effect=lambda *a:a[-1]),patch.object(d,'require_publication_bound',return_value=None):
            return e.execute(self.root,e.binding(self.p),self.root/'reports/verification-coverage'/out,'fixture-token-at-least-twenty-four-chars',runtime,checkpoint=checkpoint,reviewed_driver_sha256=e.sha(Path(e.__file__).resolve()),clock=lambda:day+'T14:00:00+00:00')
    def test_never_more_than_four_actual_attempts(self):
        r=FixtureRuntime(self.root,self.files);v=self.run_engine('one',r);self.assertEqual(v['writes_attempted_this_invocation'],4);self.assertEqual(len(r.t.calls),4);self.assertFalse(v['published']);self.assertEqual(v['status'],'SAFE_NONTERMINAL')
    def test_next_invocation_reuses_owned_chain_not_start(self):
        r=FixtureRuntime(self.root,self.files);a=self.run_engine('one',r);r2=FixtureRuntime(self.root,self.files);b=self.run_engine('two',r2,a['checkpoint']);checkpoint=json.loads(Path(b['checkpoint']['path']).read_bytes());self.assertEqual(checkpoint['record_id'],'23299999');self.assertEqual(sum(x['step']=='NEW_VERSION'for x in checkpoint['attempts']),1);self.assertEqual(len(checkpoint['attempts']),8)
    def test_next_day_count_resets_but_attempt_history_remains(self):
        r=FixtureRuntime(self.root,self.files);a=self.run_engine('one',r);r2=FixtureRuntime(self.root,self.files);b=self.run_engine('two',r2,a['checkpoint'],day='2026-10-09');self.assertEqual(r2.require_budget(self.root,'POST','2026-10-09T14:00:00+00:00')['used'],4);self.assertEqual(len(json.loads(Path(b['checkpoint']['path']).read_bytes())['attempts']),8)
    def test_daily_cap_stops_at_two_remaining_without_overdraw(self):
        r=FixtureRuntime(self.root,self.files);a=self.run_engine('one',r);b=self.run_engine('two',r,a['checkpoint']);c=self.run_engine('three',r,b['checkpoint']);self.assertEqual(c['writes_attempted_this_invocation'],2);self.assertEqual(c['status'],'WAIT_NEXT_NEW_YORK_DAY');self.assertEqual(len(r.require_events(self.root,'2026-10-08T14:00:00+00:00')),10)
    def test_readback_failure_freezes_no_second_start(self):
        r=FixtureRuntime(self.root,self.files,fail=True);a=self.run_engine('one',r);self.assertEqual(a['writes_attempted_this_invocation'],1);self.assertEqual(a['status'],'HOLD');self.assertEqual(r.require_budget(self.root,'POST','2026-10-08T14:00:00+00:00')['used'],1)
        self.assertRaises(m.MachineHold,self.run_engine,'two',FixtureRuntime(self.root,self.files),a['checkpoint'])
    def test_journal_reservation_without_checkpoint_is_not_retried(self):
        runtime=FixtureRuntime(self.root,self.files);ph=m.digest(self.plan);operation='phase7-owned:'+ph[:16]+':'+hashlib.sha256(b'NEW_VERSION').hexdigest()[:16]
        with journal.JournalWriter(self.root,self.root/'crash-reservations',runtime.require_events,runtime.require_budget)as writer:
            writer.reserve('POST','https://zenodo.org/api/deposit/depositions/23226761/actions/newversion',b'{}',self.root/'lost/001_POST.json','2026-10-08T13:00:00+00:00',operation,d.require_write_budget)
        self.assertRaises(e.ExecutionHold,self.run_engine,'resume-after-crash',runtime)
        self.assertEqual(runtime.t.calls,[]);self.assertEqual(len(runtime.require_events(self.root,'2026-10-08T14:00:00+00:00')),1)
    def test_binary_bound_source_is_not_forced_to_json(self):
        p=self.root/'source.py';p.write_bytes(b'import json\n');self.assertEqual(e.source(self.root,e.binding(p))[1],b'import json\n')
if __name__=='__main__':unittest.main()
