import copy, hashlib, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import invoke_weekly_digest as invoke
import weekly_digest_executor as executor
import owned_creation_recovery as recovery
import owned_digest_machine as machine

def bind(path):return {'path':path,'sha256':hashlib.sha256(path.encode()).hexdigest()}
def fixture():
    root='/fixture';base=root+'/old/transport';rid='23246368';src='23226761';parent='23226760'
    inventory=[{'name':name,'path':root+'/package/'+name,'bytes':10,'sha256':'1'*64,'md5':'2'*32}for name in sorted(machine.NAMES)]
    old={'start_kind':'NEW_VERSION','canonical_root':root,'release_week':'2026-W41','predecessor_record_id':src,'expected_concept_id':parent,'source_concept_id':parent,'prior_run_ids':[125],'new_run_ids':[127],'predecessor_registration':bind(root+'/registered.json'),'registration_recovery':bind(root+'/registrations.json'),'source_legacy_receipt':bind(root+'/source_l.json'),'source_native_receipt':bind(root+'/source_n.json'),'source_native_before_create':bind(root+'/source_n.json'),'community_mirror_proof':bind(root+'/community.json'),'execution_directory':root+'/old','approved_inventory':inventory,'authority':bind(root+'/old-authority.json')}
    new=copy.deepcopy(old);new['execution_directory']=root+'/new';new['authority']=bind(root+'/new-authority.json')
    sources={'old_plan':bind(root+'/old-plan.json'),'new_plan':bind(root+'/new-plan.json'),'old_hold':bind(root+'/old/CHECKPOINT.json'),'first_legacy':bind(base+'/004_GET.json'),'first_native':bind(base+'/005_GET.json'),'readmission':bind(root+'/new/readmission.json'),'authority':new['authority']}
    reservation=bind(root+'/old/reservation.json');transport=bind(base+'/003_POST.json');op='phase7-owned:old:creation'
    state=machine.initial(machine.digest(old),inventory);state=machine.reserve(state,'NEW_VERSION',reservation,op);state=machine.fail(state,transport,'inherited creation metadata changed',uncertain=False)
    inherited=[{'filename':name,'filesize':10,'checksum':'2'*32,'id':'file-'+name,'links':{}}for name in sorted(machine.NAMES)]
    def receipt(method,url,response,status=200,native=False):return {'method':method,'url':url,'environment':'zenodo.org','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':status,'accept':'application/vnd.inveniordm.v1+json'if native else'application/json','response':response}
    created=receipt('POST','https://zenodo.org/api/deposit/depositions/'+src+'/actions/newversion',{'id':int(rid),'conceptrecid':parent,'created':'2026-10-08T19:08:21.178436+00:00','submitted':False,'state':'unsubmitted','files':inherited},status=201);created['request_body_sha256']=hashlib.sha256(b'{}').hexdigest()
    first_l=receipt('GET','https://zenodo.org/api/deposit/depositions/'+rid,{'id':int(rid),'conceptrecid':parent})
    first_n=receipt('GET','https://zenodo.org/api/records/'+rid+'/draft',{'id':rid,'parent':{'id':parent}},native=True)
    readmission={'standard':'VRS-OWNED-DIGEST-FULL-READBACK-1','record_id':rid,'step':'NEW_VERSION','transport':transport,'owned_legacy_get':bind(root+'/fresh_l.json'),'owned_native_get':bind(root+'/fresh_n.json'),'explicit_creation_recovery':{'standard':recovery.STANDARD,'status':'CURRENT_OWN_RECORD_RULE_READMISSION_ONLY','old_plan':sources['old_plan'],'old_hold':sources['old_hold'],'authority':new['authority'],'original_reservation':reservation,'original_operation_id':op,'no_network_write':True}}
    return old,new,state,dict(sources=sources,creation_receipt=created,first_legacy_receipt=first_l,first_native_receipt=first_n,readmission=readmission)

class RecoveryTests(unittest.TestCase):
    def setUp(self):self.old,self.new,self.hold,self.kw=fixture()
    def candidate(self):return recovery.candidate_seed(self.old,self.new,self.hold,**self.kw)
    def fail(self):
        with self.assertRaises((recovery.RecoveryHold,machine.MachineHold)):self.candidate()
    def test_existing_creation_retained_original_hold_not_modified(self):
        before=machine.encode(self.hold);state,receipt=self.candidate()
        self.assertEqual(before,machine.encode(self.hold));self.assertEqual(state['record_id'],'23246368');self.assertTrue(machine.next_step(state).startswith('DROP:'));self.assertNotEqual(machine.next_step(state),'NEW_VERSION');self.assertEqual(state['attempts'][0]['reservation'],self.hold['attempts'][0]['reservation']);self.assertEqual(state['attempts'][0]['transport'],self.hold['attempts'][0]['transport']);self.assertTrue(receipt['original_attempt_still_charged']);self.assertFalse(receipt['certifies']);self.assertEqual(receipt['status'],'SOURCE_BOUND_RECOVERY_CANDIDATE_NOT_ADMITTED')
    def test_unknown_hold_not_admitted(self):self.hold['failure']='another content mismatch';self.fail()
    def test_uncertain_not_admitted(self):self.hold['phase']='UNCERTAIN';self.hold['attempts'][0]['outcome']='UNCERTAIN';self.fail()
    def test_reserved_not_admitted(self):self.hold['phase']='NOT_STARTED';self.hold['failure']=None;self.hold['attempts'][0]['outcome']='RESERVED';self.fail()
    def test_old_hold_wrong_plan_not_admitted(self):self.hold['plan_sha256']='f'*64;self.fail()
    def test_same_history_not_admitted(self):self.new['execution_directory']=self.old['execution_directory'];self.fail()
    def test_old_authority_not_admitted(self):self.new['authority']=self.old['authority'];self.fail()
    def test_foreign_creation_id_not_admitted(self):self.kw['creation_receipt']['response']['id']=23226761;self.fail()
    def test_foreign_concept_not_admitted(self):self.kw['creation_receipt']['response']['conceptrecid']='99999';self.fail()
    def test_first_native_foreign_id_not_admitted(self):self.kw['first_native_receipt']['response']['id']='99999';self.fail()
    def test_first_pair_not_original_sequence_not_admitted(self):self.kw['sources']['first_native']=bind('/fixture/fresh/005_GET.json');self.fail()
    def test_first_native_wrong_accept_not_admitted(self):self.kw['first_native_receipt']['accept']='application/json';self.fail()
    def test_unsuccessful_creation_not_admitted(self):self.kw['creation_receipt']['http_status']=202;self.fail()
    def test_creation_body_not_empty_not_admitted(self):self.kw['creation_receipt']['request_body_sha256']='3'*64;self.fail()
    def test_new_cohort_not_admitted(self):self.new['new_run_ids']=[130];self.fail()
    def test_new_source_pair_not_admitted(self):self.new['source_native_receipt']=bind('/fixture/other.json');self.fail()
    def test_minted_plan_identity_not_admitted(self):self.new['expected_concept_id']='99999';self.fail()
    def test_readmission_wrong_transport_not_admitted(self):self.kw['readmission']['transport']=bind('/fixture/another201.json');self.fail()
    def test_readmission_rewrites_reservation_not_admitted(self):self.kw['readmission']['explicit_creation_recovery']['original_reservation']=bind('/fixture/recharged.json');self.fail()
    def test_readmission_network_write_not_admitted(self):self.kw['readmission']['explicit_creation_recovery']['no_network_write']=False;self.fail()
    def test_readmission_authority_not_new_plan_not_admitted(self):self.kw['readmission']['explicit_creation_recovery']['authority']=self.old['authority'];self.fail()
    def test_missing_fresh_pair_not_admitted(self):self.kw['readmission'].pop('owned_native_get');self.fail()


class RecoveryExitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
        self.history=self.root/'reports/verification-coverage/history';self.out=self.history/'readmission'
        plan={'execution_directory':str(self.history)}
        self.plan_path=self.root/'PLAN.json';self.plan_path.write_bytes(executor.raw_json(plan));self.plan_binding=executor.binding(self.plan_path)
        self.hold_path=self.root/'OLD_HOLD.json';self.hold_path.write_bytes(executor.raw_json({'attempts':[{'transport':{'path':str(self.root/'original201.json'),'sha256':'a'*64}}]}));self.hold_binding=executor.binding(self.hold_path);self.original_hold=self.hold_path.read_bytes()
        self.readmission=self.root/'readmission.json';self.readmission.write_bytes(executor.raw_json({'fixture':'read-only order test, not admission'}))
        self.exited=False;self.result_written_after_exit=False
    def tearDown(self):self.tmp.cleanup()
    def run_entry(self,fail_exit):
        # Real invoke control flow and immutable file operations; scientific
        # admission/transport are isolated fixtures, never a production PASS.
        test=self
        class Session:
            def __enter__(self):return self
            def __exit__(self,*args):
                test.exited=True
                if fail_exit:raise ValueError('HOLD_FINAL_VERIFY_LOADED')
        class Boundary:
            def readmit_creation(self,**kwargs):return executor.binding(test.readmission)
        class Runtime:
            def __init__(self,*args):pass
            def admission(self,*args):pass
            def transport(self,*args):return object()
            def boundary(self,*args):return Boundary()
        state={'record_id':'23246368','concept_id':'23226760','phase':'OWNED_DRAFT','published':False}
        recovery_fixture=SimpleNamespace(STANDARD=recovery.STANDARD,recover=lambda *a,**kw:(state,{'fixture':'read-only source-order test, not admission'}))
        original_immutable=executor.immutable
        def checked_immutable(path,data):
            if Path(path).name in{'CHECKPOINT.json','RECOVERY_RECEIPT.json','RESULT.json'}:
                self.assertTrue(self.exited,'success receipt precedes fallible session exit')
                if Path(path).name=='RESULT.json':self.result_written_after_exit=True
            return original_immutable(path,data)
        with patch.object(invoke,'session',return_value=Session()),patch.object(executor,'require_plan',return_value=self.root),patch.object(executor,'immutable',side_effect=checked_immutable),patch.dict(sys.modules,{'weekly_digest_runtime':SimpleNamespace(ActualRuntime=Runtime),'owned_creation_recovery':recovery_fixture}):
            return invoke.recover_owned_creation(self.root,plan_binding=self.plan_binding,old_plan_binding=self.plan_binding,old_hold_binding=self.hold_binding,first_legacy_binding=self.plan_binding,first_native_binding=self.plan_binding,output=self.out,token='fixture-memory-token-never-sent')
    def test_failing_session_exit_never_emits_success_result_or_returns(self):
        with self.assertRaisesRegex(ValueError,'HOLD_FINAL_VERIFY_LOADED'):self.run_entry(True)
        self.assertTrue(self.exited);self.assertFalse((self.out/'RESULT.json').exists());self.assertFalse(self.result_written_after_exit)
        self.assertTrue((self.out/'RECOVERY_CANDIDATE.json').exists());self.assertFalse((self.out/'CHECKPOINT.json').exists());self.assertFalse((self.out/'RECOVERY_RECEIPT.json').exists());self.assertEqual(json.loads((self.out/'RECOVERY_CANDIDATE.json').read_bytes())['status'],'READ_ONLY_RECOVERY_STAGED_PENDING_SOURCE_SESSION_EXIT')
        self.assertEqual(self.hold_path.read_bytes(),self.original_hold)
    def test_success_result_is_emitted_after_successful_session_exit(self):
        result=self.run_entry(False)
        self.assertTrue(self.exited);self.assertTrue(self.result_written_after_exit)
        self.assertEqual(result['status'],'EXPLICIT_EXISTING_OWN_DRAFT_RECOVERED_NO_MUTATION')
        self.assertEqual(json.loads((self.out/'RESULT.json').read_bytes()),result)
        self.assertEqual(result['writes_attempted_this_invocation'],0);self.assertEqual(result['new_versions_created'],0)
        self.assertEqual(self.hold_path.read_bytes(),self.original_hold)

if __name__=='__main__':unittest.main()
