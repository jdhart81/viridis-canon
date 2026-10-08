import copy, hashlib, json, unittest
from pathlib import Path
import owned_digest_machine as m

B={'path':'/tmp/genuine-bound.json','sha256':'a'*64}
FILES=[{'name':n,'path':'/tmp/package/'+n,'bytes':1,'sha256':'a'*64,'md5':'b'*32}for n in sorted(m.NAMES)]
INHERITED=[{'filename':n,'filesize':1,'checksum':'b'*32,'id':f'00000000-0000-0000-0000-{i:012d}','links':{}}for i,n in enumerate(sorted(m.NAMES))]
def new():return m.initial('c'*64,FILES)
def complete(s,step,ownership=None):
    s=m.reserve(s,step,B,'step:'+hashlib.sha256(step.encode()).hexdigest());return m.finish(s,B,B,ownership=ownership)
def owned():return complete(new(),'NEW_VERSION',{'record_id':'23299999','concept_id':'23226760','first_owned_draft':B,'first_owned_legacy_draft':B,'inherited_inventory':INHERITED})
class Tests(unittest.TestCase):
    def bad(self,f):self.assertRaises(m.MachineHold,f)
    def test_initial_has_no_child_identity(self):
        s=new();self.assertIsNone(s['record_id']);self.assertEqual(m.next_step(s),'NEW_VERSION')
    def test_owned_requires_real_bindings(self):self.assertEqual(owned()['phase'],'OWNED_DRAFT')
    def test_exact_all_six_then_metadata_then_upload(self):
        s=owned();order=[]
        while m.next_step(s)!='PUBLISH':
            step=m.next_step(s);order.append(step);s=complete(s,step)
        self.assertEqual(order[:6],['DROP:'+n for n in sorted(m.NAMES)]);self.assertEqual(order[6],'METADATA');self.assertEqual(order[7:13],['UPLOAD:'+n for n in sorted(m.NAMES)]);self.assertEqual(order[-1],'RESERVE_DOI')
        s=complete(s,'PUBLISH');self.assertTrue(s['published']);self.assertIsNone(m.next_step(s));self.assertEqual(len(s['attempts']),16)
    def test_first_week_exact_nine_steps(self):
        s=m.initial('c'*64,FILES,start_kind='CREATE_WEEK')
        s=complete(s,'CREATE_WEEK',{'record_id':'23399999','concept_id':'23399998','first_owned_draft':B,'first_owned_legacy_draft':B,'inherited_inventory':[]})
        while m.next_step(s)is not None:s=complete(s,m.next_step(s))
        self.assertEqual([a['step']for a in s['attempts']],m.step_order('CREATE_WEEK'));self.assertEqual(len(s['attempts']),9)
    def test_first_week_rejects_inherited_old_files(self):
        s=m.reserve(m.initial('c'*64,FILES,start_kind='CREATE_WEEK'),'CREATE_WEEK',B,'start')
        self.bad(lambda:m.finish(s,B,B,ownership={'record_id':'23399999','concept_id':'23399998','first_owned_draft':B,'first_owned_legacy_draft':B,'inherited_inventory':INHERITED}))
    def test_reordered_saved_steps_fail(self):
        s=owned();step=m.next_step(s);s=complete(s,step);s['completed']=list(reversed(s['completed']));self.bad(lambda:m.validate(s,'c'*64))
    def test_saved_early_upload_pass_fails(self):
        s=owned();s['completed'].append('UPLOAD:paper.pdf');s['attempts'].append({'operation_id':'fake','step':'UPLOAD:paper.pdf','reservation':B,'transport':B,'validation':B,'outcome':'STRICT_PASS'});self.bad(lambda:m.validate(s,'c'*64))
    def test_fake_published_phase_fails(self):
        s=owned();s['phase']='PUBLISHED';self.bad(lambda:m.validate(s,'c'*64))
    def test_hidden_failure_fails(self):
        s=owned();s['failure']='ignored';self.bad(lambda:m.validate(s,'c'*64))
    def test_initial_unknown_id_fails(self):
        s=new();s['record_id']='999';self.bad(lambda:m.validate(s,'c'*64))
    def test_five_file_inventory_fails(self):self.bad(lambda:m.initial('c'*64,FILES[:-1]))
    def test_duplicate_inventory_fails(self):self.bad(lambda:m.initial('c'*64,FILES[:-1]+FILES[:1]))
    def test_checksum_field_missing_fails(self):
        rows=copy.deepcopy(FILES);rows[0].pop('md5');self.bad(lambda:m.inventory(rows))
    def test_plan_hash_change_fails(self):self.bad(lambda:m.validate(new(),'d'*64))
    def test_first_start_reserved_is_not_replayed(self):
        s=m.reserve(new(),'NEW_VERSION',B,'start');self.bad(lambda:m.next_step(s))
    def test_uncertain_start_never_starts_twice(self):
        s=m.fail(m.reserve(new(),'NEW_VERSION',B,'start'),B,'uncertain',uncertain=True);self.bad(lambda:m.next_step(s));self.assertEqual(len(s['attempts']),1)
    def test_success_draft_step_reserved_not_replayed(self):
        s=owned();s=m.reserve(s,m.next_step(s),B,'drop');self.bad(lambda:m.next_step(s))
    def test_failed_slot_retained(self):
        s=owned();s=m.fail(m.reserve(s,m.next_step(s),B,'drop'),B,'main bytes mismatch',uncertain=False);self.assertEqual(s['attempts'][-1]['outcome'],'HOLD');self.bad(lambda:m.next_step(s))
    def test_no_late_identity_overwrite(self):
        s=owned();s=m.reserve(s,m.next_step(s),B,'drop');self.bad(lambda:m.finish(s,B,B,ownership={'record_id':'new'}))
    def test_publish_early_fails(self):self.bad(lambda:m.reserve(owned(),'PUBLISH',B,'publish'))
    def test_uploaded_file_before_drop_fails(self):self.bad(lambda:m.reserve(owned(),'UPLOAD:paper.pdf',B,'upload'))
    def test_ownership_requires_exact_fields(self):
        s=m.reserve(new(),'NEW_VERSION',B,'start');self.bad(lambda:m.finish(s,B,B,ownership={'record_id':'999'}))
    def test_fake_terminal_fails(self):
        s=owned();s['published']=True;s['phase']='PUBLISHED';self.bad(lambda:m.validate(s,'c'*64))
    def test_unknown_checkpoint_field_fails(self):
        s=new();s['allowed']=True;self.bad(lambda:m.validate(s,'c'*64))
    def test_unbound_validation_fails(self):
        s=m.reserve(new(),'NEW_VERSION',B,'start');self.bad(lambda:m.finish(s,B,{'status':'PASS'},ownership={}))
    def test_duplicate_attempt_id_fails(self):
        s=owned();self.bad(lambda:m.reserve(s,m.next_step(s),B,s['attempts'][0]['operation_id']))
    def test_duplicate_completed_step_fails(self):
        s=owned();s['completed'].append('NEW_VERSION');self.bad(lambda:m.validate(s,'c'*64))
    def test_original_initial_immutable(self):
        a=new();b=complete(a,'NEW_VERSION',{'record_id':'23299999','concept_id':'23226760','first_owned_draft':B,'first_owned_legacy_draft':B,'inherited_inventory':INHERITED});self.assertIsNone(a['record_id']);self.assertEqual(a['attempts'],[])
    def test_runtime_engine_four_attempt_constant(self):
        source=(Path(__file__).parent/'weekly_digest_executor.py').read_text();self.assertIn('MAX_ATTEMPTS=4',source);self.assertIn('while attempted<MAX_ATTEMPTS:',source);self.assertIn('attempted+=1',source)
    def test_no_auto_execution(self):
        source=(Path(__file__).parent/'weekly_digest_executor.py').read_text();self.assertIn("if __name__=='__main__':raise SystemExit",source);self.assertNotIn('keychain_token(',source)
if __name__=='__main__':unittest.main()
