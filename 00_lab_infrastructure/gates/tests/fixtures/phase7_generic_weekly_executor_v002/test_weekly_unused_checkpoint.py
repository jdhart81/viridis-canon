"""Pure initial replay and TMP accounting; scientific admission stays separate."""
import ast,copy,sys,tempfile,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import owned_digest_machine as m
import test_weekly_executor_limits as fixtures
from pathlib import Path
# Extract the real function, without importing unrelated full-readback helpers.
# This tests only its closed zero-attempt branch, never a scientific PASS.
t=ast.parse((Path(__file__).parent/'weekly_checkpoint_replay.py').read_bytes());fn=next(x for x in t.body if isinstance(x,ast.FunctionDef)and x.name=='require_checkpoint');scope={'Path':Path,'machine':m,'e':e};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual-replay-function>','exec'),scope);replay=scope['require_checkpoint']
class Runtime(fixtures.FixtureRuntime):
 def replay_checkpoint(self,plan,state):return replay(plan,state,root=self.root)
class Tests(fixtures.Tests):
 # Inherit fixture construction only; scheduling tests are explicitly separate.
 def test_zero_initial_replay_pass(self):
  state=m.initial(m.digest(self.plan),self.files,start_kind='NEW_VERSION');v=replay(self.plan,state,root=self.root);self.assertEqual(v['steps'],0);self.assertIsNone(v['record_id']);self.assertFalse(v['certifies'])
 def test_wait_before_start_continues_next_day_without_second_start(self):
  r=Runtime(self.root,self.files)
  with fixtures.journal.JournalWriter(self.root,self.root/'baseline',r.require_events,r.require_budget)as w:
   for i in range(10):w.reserve('POST','https://zenodo.org/api/deposit/depositions/23226761/actions/newversion',b'{}',self.root/f'baseline/response{i}.json','2026-10-08T12:00:00+00:00','fixture-used'+str(i),fixtures.d.require_write_budget)
  a=self.run_engine('wait',r);self.assertEqual(a['status'],'WAIT_NEXT_NEW_YORK_DAY');self.assertEqual(a['writes_attempted_this_invocation'],0);self.assertEqual(r.t.calls,[])
  b=self.run_engine('next-day',Runtime(self.root,self.files),a['checkpoint'],day='2026-10-09');v=fixtures.json.loads(Path(b['checkpoint']['path']).read_bytes());self.assertEqual(b['writes_attempted_this_invocation'],4);self.assertEqual(sum(x['step']=='NEW_VERSION'for x in v['attempts']),1)
 def test_modified_ownership_or_phase_is_not_initial(self):
  state=m.initial(m.digest(self.plan),self.files,start_kind='NEW_VERSION')
  for key,val in [('record_id','9'),('concept_id','8'),('published',True),('failure','fake'),('phase','HOLD'),('phase','UNCERTAIN')]:
   with self.subTest(key=key,val=val):v=copy.deepcopy(state);v[key]=val;self.assertRaises(ValueError,replay,self.plan,v,root=self.root)
 def test_reserved_initial_is_never_retryable(self):
  state=m.initial(m.digest(self.plan),self.files,start_kind='NEW_VERSION');p=self.root/'reservation.json';p.write_bytes(b'{}');state=m.reserve(state,'NEW_VERSION',e.binding(p),'operation-test');self.assertRaises(ValueError,replay,self.plan,state,root=self.root)
 def test_changed_approved_inventory_is_not_unused(self):
  state=m.initial(m.digest(self.plan),self.files,start_kind='NEW_VERSION');plan=copy.deepcopy(self.plan);plan['approved_inventory'][0]['sha256']='c'*64;self.assertRaises(ValueError,replay,plan,state,root=self.root)
 def test_original_draft_replay_tail_exact(self):
  source=(Path(__file__).parent/'weekly_checkpoint_replay.py').read_text();marker="e.need(state['phase']=='OWNED_DRAFT'and not state['published'],'OWNED_NONTERMINAL_CHECKPOINT')";old=(Path(__file__).parent/'test_fixtures/checkpoint_replay_before.py').read_text()
  projected=source.replace("    if plan['start_kind']=='NEW_VERSION':expected,wanted=successor.initial_newversion_projection(prior_l,prior_n,created,first_l['response'],first_n['response'])\n    else:expected,wanted=successor.first_week_projection(prior_l,prior_n,created,first_l['response'],first_n['response'],manifest['public_metadata'],relation_template=relation)","    expected,wanted=successor.initial_newversion_projection(prior_l,prior_n,created,first_l['response'],first_n['response'])")
  projected=projected.replace("        if step in{'NEW_VERSION','CREATE_WEEK'}:\n            e.need(step==plan['start_kind'],'EXACT_APPROVED_OWN_START_KIND');endpoint=base+'/api/deposit/depositions/'+plan['predecessor_record_id']+'/actions/newversion'if step=='NEW_VERSION'else base+'/api/deposit/depositions';ack=require_receipt(own,'POST',endpoint);body=b'{}'if step=='NEW_VERSION'else e.raw_json(payload);e.need(own==created and intent['request_body_sha256']==hashlib.sha256(body).hexdigest(),'ONE_EXACT_START')","        if step=='NEW_VERSION':ack=require_receipt(own,'POST',base+'/api/deposit/depositions/'+plan['predecessor_record_id']+'/actions/newversion');e.need(own==created and intent['request_body_sha256']==hashlib.sha256(b'{}').hexdigest(),'ONE_EXACT_START')")
  projected=projected.replace("    relation=successor.registered_relation_template(plan['predecessor_registration'],root=root,source_native=prior_n,source_legacy=prior_l)\n","")
  projected=projected.replace("    payload=original.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],prior_l['metadata']));native_meta=metadata.native_metadata(manifest['public_metadata'],prior_l['metadata'],prior_l,prior_n,relation);inventory={x['name']:dict(x,size=x['bytes'])for x in plan['approved_inventory']}","    templates=[x['relation_type']for x in prior_n['metadata'].get('related_identifiers',[])if x.get('relation_type',{}).get('id')=='issupplementto'];e.need(templates and all(metadata.exact(x,templates[0])for x in templates),'SOURCE_VOCABULARY');payload=original.encode_api_communities(metadata.closed_payload(manifest['public_metadata'],prior_l['metadata']));native_meta=metadata.native_metadata(manifest['public_metadata'],prior_l['metadata'],prior_l,prior_n,templates[0]);inventory={x['name']:dict(x,size=x['bytes'])for x in plan['approved_inventory']}")
  projected=projected.replace("        elif step=='RESERVE_DOI':\n            ack=require_receipt(own,'POST',base+'/api/records/'+rid+'/draft/pids/doi');e.need(ack.get('id')==rid and ack.get('parent',{}).get('id')==state['concept_id']and ack.get('pids',{}).get('doi')=={'identifier':'10.5281/zenodo.'+rid,'provider':'datacite','client':'datacite'}and intent['request_body_sha256']==hashlib.sha256(b'{}').hexdigest(),'EXACT_OWN_RESERVATION')\n            expected['pids']=successor.reserved_native_pid(own,record_id=rid,concept_id=state['concept_id'])\n            wanted=successor.reserved_private_legacy_projection(wanted,own,record_id=rid,concept_id=state['concept_id'])", "        elif step=='RESERVE_DOI':ack=require_receipt(own,'POST',base+'/api/records/'+rid+'/draft/pids/doi');e.need(ack.get('id')==rid and ack.get('parent',{}).get('id')==state['concept_id']and ack.get('pids',{}).get('doi')=={'identifier':'10.5281/zenodo.'+rid,'provider':'datacite','client':'datacite'}and intent['request_body_sha256']==hashlib.sha256(b'{}').hexdigest(),'EXACT_OWN_RESERVATION')")
  self.assertEqual(projected[projected.index(marker)+len(marker):],old[old.index(marker)+len(marker):])
if __name__=='__main__':unittest.main()
