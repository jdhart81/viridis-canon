"""FIRST orchestration unit tests; fixtures never grant scientific admission."""
import copy,hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import owned_digest_machine as m
import test_weekly_executor_limits as f
import test_weekly_unused_checkpoint as unused
class FirstBoundary(f.FixtureBoundary):
 def command(self,state,step):
  method='POST';url='https://zenodo.org/api/deposit/depositions'
  if step=='METADATA':method='PUT';url+='/'+state['record_id']
  elif step.startswith('UPLOAD:'):method='PUT';url='https://zenodo.org/api/files/00000000-0000-0000-0000-000000000000/'+step[7:]
  elif step=='RESERVE_DOI':url='https://zenodo.org/api/records/'+state['record_id']+'/draft/pids/doi'
  elif step=='PUBLISH':url+='/'+state['record_id']+'/actions/publish'
  return {'method':method,'url':url,'body':b'{}','content_type':'application/json','delete_file':None}
 def after(self,state,step,response,own):
  if self.fail:raise ValueError('fixture main-byte mismatch')
  self.n+=1;p=self.out/f'fixture_validation{self.n}.json';e.immutable(p,e.raw_json({'fixture_only':True}));ownership=None
  if step=='CREATE_WEEK':ownership={'record_id':'23300001','concept_id':'23300000','first_owned_draft':own,'first_owned_legacy_draft':own,'inherited_inventory':[]}
  return e.binding(p),ownership
class FirstRuntime(f.FixtureRuntime):
 def boundary(self,plan,package,t,out):return FirstBoundary(t,out,self.files,self.fail)
 def replay_checkpoint(self,plan,state):
  if state['phase']=='NOT_STARTED':return unused.replay(plan,state,root=self.root)
  # Unit scheduling only: live full continuation replay is separately mandatory.
  return super().replay_checkpoint(plan,state)
class Tests(f.Tests):
 def setUp(self):
  super().setUp();self.plan.update(start_kind='CREATE_WEEK',release_week='2026-W42');self.p.write_bytes(e.raw_json(self.plan))
 # Inherited NEW_VERSION-only scheduling tests are disabled here; the originals
 # remain separately discovered and unchanged in test_weekly_executor_limits.
 test_never_more_than_four_actual_attempts=None
 test_next_invocation_reuses_owned_chain_not_start=None
 test_next_day_count_resets_but_attempt_history_remains=None
 test_daily_cap_stops_at_two_remaining_without_overdraw=None
 test_readback_failure_freezes_no_second_start=None
 test_journal_reservation_without_checkpoint_is_not_retried=None
 def test_create_four_then_four_then_one_exact_nine_no_second_start(self):
  r=FirstRuntime(self.root,self.files);a=self.run_engine('one',r);b=self.run_engine('two',r,a['checkpoint']);c=self.run_engine('three',r,b['checkpoint']);v=json.loads(Path(c['checkpoint']['path']).read_bytes());self.assertEqual([a['writes_attempted_this_invocation'],b['writes_attempted_this_invocation'],c['writes_attempted_this_invocation']],[4,4,1]);self.assertEqual(c['status'],'PUBLISHED_STRICT_READBACK_PASS');self.assertEqual([x['step']for x in v['attempts']].count('CREATE_WEEK'),1);self.assertFalse(any(x['step'].startswith('DROP:')for x in v['attempts']));self.assertEqual(v['concept_id'],'23300000');self.assertEqual(len(r.t.calls),1)
 def test_create_continuation_next_day_keeps_owned_concept(self):
  a=self.run_engine('one',FirstRuntime(self.root,self.files));r=FirstRuntime(self.root,self.files);b=self.run_engine('nextday',r,a['checkpoint'],day='2026-10-09');v=json.loads(Path(b['checkpoint']['path']).read_bytes());self.assertEqual(v['concept_id'],'23300000');self.assertEqual(sum(x['step']=='CREATE_WEEK'for x in v['attempts']),1);self.assertEqual(r.require_budget(self.root,'POST','2026-10-09T14:00:00+00:00')['used'],4)
 def test_failed_create_charged_and_never_restarted(self):
  r=FirstRuntime(self.root,self.files,fail=True);a=self.run_engine('one',r);self.assertEqual(a['status'],'HOLD');self.assertEqual(a['writes_attempted_this_invocation'],1);self.assertEqual(r.require_budget(self.root,'POST','2026-10-08T14:00:00+00:00')['used'],1);self.assertRaises(ValueError,self.run_engine,'two',FirstRuntime(self.root,self.files),a['checkpoint'])
 def test_create_daily_exhaustion_zero_initial_replays_next_day(self):
  r=FirstRuntime(self.root,self.files)
  with f.journal.JournalWriter(self.root,self.root/'used',r.require_events,r.require_budget)as writer:
   for i in range(10):writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'{}',self.root/f'used/response{i}.json','2026-10-08T12:00:00+00:00','fixture-used-'+str(i),f.d.require_write_budget)
  a=self.run_engine('wait',r);self.assertEqual(a['status'],'WAIT_NEXT_NEW_YORK_DAY');self.assertEqual(a['writes_attempted_this_invocation'],0);self.assertEqual(r.t.calls,[]);b=self.run_engine('nextday',FirstRuntime(self.root,self.files),a['checkpoint'],day='2026-10-09');v=json.loads(Path(b['checkpoint']['path']).read_bytes());self.assertEqual(sum(x['step']=='CREATE_WEEK'for x in v['attempts']),1)
 def test_reserved_create_without_checkpoint_not_retried(self):
  r=FirstRuntime(self.root,self.files);ph=m.digest(self.plan);op='phase7-owned:'+ph[:16]+':'+hashlib.sha256(b'CREATE_WEEK').hexdigest()[:16]
  with f.journal.JournalWriter(self.root,self.root/'crash',r.require_events,r.require_budget)as writer:writer.reserve('POST','https://zenodo.org/api/deposit/depositions',b'{}',self.root/'lost/001_POST.json','2026-10-08T13:00:00+00:00',op,f.d.require_write_budget)
  self.assertRaises(ValueError,self.run_engine,'resume',r);self.assertEqual(r.t.calls,[]);self.assertEqual(len(r.require_events(self.root,'2026-10-08T14:00:00+00:00')),1)
 def test_published_create_is_consumed_and_not_started_again(self):
  r=FirstRuntime(self.root,self.files);a=self.run_engine('one',r);b=self.run_engine('two',r,a['checkpoint']);c=self.run_engine('three',r,b['checkpoint']);self.assertRaises(ValueError,self.run_engine,'four',FirstRuntime(self.root,self.files),c['checkpoint'],day='2026-10-09')
 def test_first_initial_reserved_or_invented_ownership_fails_replay(self):
  initial=m.initial(m.digest(self.plan),self.files,start_kind='CREATE_WEEK');self.assertEqual(unused.replay(self.plan,initial,root=self.root)['steps'],0)
  for key,val in [('record_id','9'),('concept_id','8'),('published',True),('failure','fake')]:
   with self.subTest(key=key):s=copy.deepcopy(initial);s[key]=val;self.assertRaises(ValueError,unused.replay,self.plan,s,root=self.root)
  p=self.root/'res.json';p.write_bytes(b'{}');s=m.reserve(initial,'CREATE_WEEK',e.binding(p),'fixture-op');self.assertRaises(ValueError,unused.replay,self.plan,s,root=self.root)
if __name__=='__main__':unittest.main()
