"""Complete raw account and exact selector projection; no live requests."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
import owned_weekly_discovery as q

def record(rid='23226761',week='2026-W41',parent='23226760'):
    return {'id':rid,'metadata':{'title':'Viridis Methods Digest — '+week},'parent':{'id':parent},'versions':{'index':1,'is_latest':True,'is_latest_draft':True},'pids':{'doi':{'identifier':'10.5281/zenodo.'+rid}},'is_published':True,'is_draft':False,'status':'published'}
class Tests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.serial=0
    def tearDown(self):self.tmp.cleanup()
    def pages(self,rows):
        bindings=[]
        for page in range(max(1,(len(rows)+99)//100)):
            self.serial+=1;raw=e.raw_json({'hits':{'total':{'value':len(rows),'relation':'eq'},'hits':rows[page*100:(page+1)*100]}});p=self.root/f'{self.serial}.bin';p.write_bytes(raw);receipt={'standard':'VRS-PHASE7-READONLY-ACCOUNT-GET-1','method':'GET','url':f'https://zenodo.org/api/user/records?page={page+1}&size=100','status':'RAW_ACCOUNT_GET_CAPTURED_NOT_COMPLETE','http_status':200,'response_path':str(p),'response_sha256':hashlib.sha256(raw).hexdigest(),'response_bytes':len(raw)};r=self.root/f'{self.serial}.json';r.write_bytes(e.raw_json(receipt));bindings.append(e.binding(r))
        return bindings
    def proof(self,rows,week='2026-W41'):
        result=q.discover(rows,week);saved=self.root/'records.json';saved.write_bytes(e.raw_json({'records':rows}));return {'standard':'VRS-OWNED-WEEKLY-DISCOVERY-1','release_week':week,'record_id':result.get('record_id'),'concept_id':result.get('concept_id'),'passes':[self.pages(rows),self.pages(rows)],'records':e.binding(saved),'record_count':len(rows),'producer_sha256':q.source_sha(),'writes':0,'start_kind':'NEW_VERSION'if result['status']=='EXISTING_WEEKLY_RECORD'else'CREATE_WEEK'}
    def test_native_exact_pid_projection_pass(self):self.assertEqual(q.discover([record()],'2026-W41')['record_id'],'23226761')
    def test_input_native_object_is_unchanged(self):
        rows=[record()];before=copy.deepcopy(rows);q.discover(rows,'2026-W41');self.assertEqual(rows,before);self.assertNotIn('doi',rows[0])
    def test_conflicting_doi_scalar_fails(self):
        r=record();r['doi']='foreign';self.assertRaises(ValueError,q.discover,[r],'2026-W41')
    def test_foreign_native_doi_fails(self):
        r=record();r['pids']['doi']['identifier']='10.5281/zenodo.9999';self.assertRaises(ValueError,q.discover,[r],'2026-W41')
    def test_unpublished_latest_source_fails(self):
        r=record();r.update(is_draft=True,is_published=False,status='draft');self.assertRaises(ValueError,q.discover,[r],'2026-W41')
    def test_two_concepts_fails(self):self.assertRaises(ValueError,q.discover,[record(),record('23300000',parent='23299999')],'2026-W41')
    def test_unique_latest_successor_pass(self):
        old=record();old['versions']['is_latest']=False;new=record('23300000');new['versions']['index']=2;self.assertEqual(q.discover([old,new],'2026-W41')['record_id'],'23300000')
    def test_own_pending_draft_does_not_choose_new_source(self):
        pending=record('23300000');pending.update(is_draft=True,is_published=False,status='draft');pending['versions']['is_latest']=False;self.assertEqual(q.discover([record(),pending],'2026-W41')['record_id'],'23226761')
    def test_double_raw_successor_proof_pass(self):
        v=self.proof([record()]);self.assertEqual(q.require_discovery(v,root=self.root)['status'],'EXISTING_WEEKLY_RECORD')
    def test_complete_nextweek_no_existing_pass(self):
        v=self.proof([record()],week='2026-W42');self.assertEqual(q.require_discovery(v,root=self.root)['status'],'NO_EXISTING_WEEKLY_RECORD');self.assertIsNone(v['concept_id'])
    def test_no_independent_empty_W41_fails(self):
        v=self.proof([],week='2026-W41');self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_double_pass_race_fails(self):
        v=self.proof([record()]);v['passes'][1]=self.pages([record('23300000')]);self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_omitted_second_page_fails(self):
        rows=[dict(record(str(24000000+i),week='2026-W40',parent=str(25000000+i)))for i in range(101)];v=self.proof(rows,week='2026-W42');v['passes'][0]=v['passes'][0][:-1];self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_duplicate_account_identity_fails(self):
        v=self.proof([record(),dict(record(),metadata={'title':'unrelated'})]);self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_changed_raw_page_fails(self):
        v=self.proof([record()]);_,r=e.bound(self.root,v['passes'][0][0]);Path(r['response_path']).write_bytes(b'{}');self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_missing_whole_page_proof_fails(self):
        v=self.proof([record()]);v['passes'][0]=[];self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_marker_not_matching_actual_raw_fails(self):
        v=self.proof([record()]);v['record_id']='9999';self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_unknown_field_fails(self):
        v=self.proof([record()]);v['complete']=True;self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
    def test_wrong_operation_kind_fails(self):
        v=self.proof([record()]);v['start_kind']='CREATE_WEEK';self.assertRaises(ValueError,q.require_discovery,v,root=self.root)
if __name__=='__main__':unittest.main()
