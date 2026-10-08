import copy,datetime as dt,hashlib,importlib.util,json,os,sys,tempfile,unittest
from pathlib import Path
GATES=next((q for q in Path(__file__).resolve().parents if (q/'methods_digest.py').is_file()),None)
if GATES is None:GATES=Path(os.environ['PHASE7_TEST_GATES']).resolve(strict=True)
sys.path.insert(0,str(GATES))
sys.path.insert(0,str(Path(__file__).parent))
import readonly_account as a
import mutation_journal_writer as j
import digest_metadata as m
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
digest=load('test_actual_digest',GATES/'methods_digest.py')
mut=load('test_actual_mut',GATES/'phase7_mutation_baseline.py')
token='FAKE_TEST_TOKEN_NOT_A_CREDENTIAL_12345'
class Response:
    def __init__(self,value,url,status=200):self.body=value if isinstance(value,bytes)else json.dumps(value).encode();self.url=url;self.status=status
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def read(self,n=None):return self.body if n is None else self.body[:n]
class Opener:
    def __init__(self,values):self.values=list(values);self.calls=[]
    def open(self,request,timeout):
        self.calls.append(request)
        if not self.values:raise AssertionError('unexpected request')
        v=self.values.pop(0)
        if isinstance(v,Exception):raise v
        if isinstance(v,Response):return v
        return Response(v,request.full_url)
def account_rows(n,start=1,title='Other'):
    return [{'id':str(i),'metadata':{'title':title},'parent':{'id':str(i+1000)},'pids':{},'versions':{'index':1,'is_latest':True},'is_draft':False,'is_published':True}for i in range(start,start+n)]
def page(rows,total):return {'hits':{'hits':rows,'total':total}}
class AccountTests(unittest.TestCase):
    def setUp(self):self.t=tempfile.TemporaryDirectory();self.base=Path(self.t.name).resolve()
    def tearDown(self):self.t.cleanup()
    def run_scan(self,values):
        op=Opener(values);scan=a.AccountDiscovery(token,self.base/'account',op,pace=lambda:None);return scan.complete('2026-W41',digest.discover_weekly_record),op
    def test_complete_two_pages_two_passes(self):
        first=page(account_rows(100),101);last=page(account_rows(1,101),101)
        result,op=self.run_scan([first,last,first,last]);self.assertEqual(result['record_count'],101);self.assertTrue(all(r.method=='GET'for r in op.calls));self.assertEqual(len(op.calls),4)
    def test_zero_account_exact_total(self):self.assertEqual(self.run_scan([page([],0),page([],0)])[0]['record_count'],0)
    def test_object_eq_total(self):self.assertEqual(self.run_scan([page(account_rows(1),{'value':1,'relation':'eq'})]*2)[0]['record_count'],1)
    def test_raw_saved_before_decoding(self):
        with self.assertRaises(a.AccountHold):self.run_scan([b'not JSON'])
        self.assertEqual((self.base/'account/001_ACCOUNT_GET.response.bin').read_bytes(),b'not JSON')
    def test_no_token_in_evidence(self):
        self.run_scan([page([],0)]*2)
        self.assertFalse(any(token.encode()in p.read_bytes()for p in(self.base/'account').iterdir()))
    def test_unknown_total_relation_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page([],{'value':0,'relation':'gte'})])
    def test_bool_total_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page([],False)])
    def test_total_changes_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page(account_rows(100),101),page(account_rows(2,101),102)])
    def test_clamped_page_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page(account_rows(25),101)])
    def test_duplicate_record_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page(account_rows(100),101),page(account_rows(1),101)])
    def test_second_pass_title_race_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page(account_rows(1),1),page(account_rows(1,title='Changed'),1)])
    def test_existing_digest_draft_blocks(self):
        rows=account_rows(1,title='Viridis Methods Digest — 2026-W41');rows[0]['is_draft']=True
        with self.assertRaises(a.AccountHold):self.run_scan([page(rows,1)]*2)
    def test_existing_digest_public_blocks(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page(account_rows(1,title='Viridis Methods Digest — 2026-W41'),1)]*2)
    def test_malformed_record_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([page([{'id':'1'}],1)])
    def test_network_failure_has_no_retry(self):
        op=Opener([RuntimeError('fixture')]);scan=a.AccountDiscovery(token,self.base/'account',op,pace=lambda:None)
        with self.assertRaises(a.AccountHold):scan.complete('2026-W41',digest.discover_weekly_record)
        self.assertEqual(len(op.calls),1)
    def test_redirect_fails(self):
        with self.assertRaises(a.AccountHold):self.run_scan([Response(page([],0),'https://other.org/api/user/records')])
    def test_url_closed(self):self.assertEqual(a.require_url('https://zenodo.org/api/user/records?page=1&size=100'),1)
    def test_url_token_query_fails(self):
        with self.assertRaises(a.AccountHold):a.require_url('https://zenodo.org/api/user/records?page=1&size=100&access_token=x')
    def test_url_foreign_host_fails(self):
        with self.assertRaises(a.AccountHold):a.require_url('https://other.org/api/user/records?page=1&size=100')
    def test_url_duplicate_query_fails(self):
        with self.assertRaises(a.AccountHold):a.require_url('https://zenodo.org/api/user/records?page=1&page=2&size=100')
    def test_url_zero_page_fails(self):
        with self.assertRaises(a.AccountHold):a.require_url('https://zenodo.org/api/user/records?page=0&size=100')
    def test_url_userinfo_fails(self):
        with self.assertRaises(a.AccountHold):a.require_url('https://x@zenodo.org/api/user/records?page=1&size=100')

class JournalTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name).resolve();self.index=self.root/j.JOURNAL;self.index.parent.mkdir(parents=True)
        (self.index.parent/'existing.json').write_text('{"fixture":true}\n')
        self.now=lambda:dt.datetime.now(dt.timezone.utc).isoformat()
        baseline=mut.capture(self.root,self.now());bp=self.index.parent/'MUTATION_BASELINE.json';bp.write_bytes(j.raw_json(baseline))
        self.index.write_bytes(j.raw_json({'standard':mut.INDEX_STANDARD,'status':'ACTIVE','baseline':{'path':str(bp),'sha256':hashlib.sha256(bp.read_bytes()).hexdigest()},'reservations':[],'updated_at_utc':self.now()}))
        self.out=self.index.parent/'execution';self.out.mkdir();self.transport=self.out/'transport';self.transport.mkdir()
        self.budget=lambda root,method,when:digest.require_write_budget(mut.require_events(root,when),method,when,complete=True)
        self.writer=lambda:j.JournalWriter(self.root,self.out/'reservations',mut.require_events,self.budget)
    def tearDown(self):self.t.cleanup()
    def reserve(self,w,n=1,body=b'{}'):
        return w.reserve('POST','https://zenodo.org/api/deposit/depositions',body,self.transport/f'{n:03d}_POST.json',self.now(),'fixture:'+str(n),digest.require_write_budget)
    def test_actual_empty_capture_has_slot(self):self.assertEqual(self.budget(self.root,'POST',self.now())['used'],0)
    def test_reservation_before_network_costs_slot(self):
        with self.writer()as w:
            v=self.reserve(w);self.assertEqual(v['used_before'],0);self.assertFalse((self.transport/'001_POST.json').exists());self.assertEqual(self.budget(self.root,'POST',self.now())['used'],1)
    def test_full_cas_before_after_are_saved(self):
        old=self.index.read_bytes()
        with self.writer()as w:self.reserve(w)
        folder=next((self.out/'reservations').iterdir());self.assertEqual((folder/'BEFORE_INDEX.json').read_bytes(),old);self.assertEqual((folder/'AFTER_INDEX.json').read_bytes(),self.index.read_bytes())
    def test_matching_success_subsumes_only_one(self):
        with self.writer()as w:
            self.reserve(w);now=self.now();path=self.transport/'001_POST.json';path.write_bytes(j.raw_json({'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':j.sha(b'{}'),'environment':'zenodo.org','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':'f'*64,'response':{'modified':now}}));self.assertEqual(self.budget(self.root,'POST',self.now())['used'],1)
    def test_wrong_actual_path_does_not_subsume(self):
        with self.writer()as w:
            self.reserve(w);now=self.now();(self.transport/'002_POST.json').write_bytes(j.raw_json({'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':j.sha(b'{}'),'environment':'zenodo.org','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','response_sha256':'f'*64,'response':{'modified':now}}));self.assertEqual(self.budget(self.root,'POST',self.now())['used'],2)
    def test_uncertain_attempt_does_not_retry(self):
        with self.writer()as w:
            self.reserve(w);path=self.transport/'001_POST.json';path.write_bytes(j.raw_json({'method':'POST','url':'https://zenodo.org/api/deposit/depositions','request_body_sha256':j.sha(b'{}'),'environment':'zenodo.org','status':'HOLD_TRANSPORT_UNCERTAIN_NO_RETRY'}))
            with self.assertRaises(j.JournalHold):self.reserve(w)
    def test_tenth_slot_reserved_once_no_offbyone(self):
        with self.writer()as w:
            for n in range(1,11):v=self.reserve(w,n)
            self.assertEqual(v['used_before'],9);self.assertEqual(v['remaining_after_reservation'],0)
            with self.assertRaises(digest.DigestHold):self.reserve(w,11)
    def test_missing_capture_fails(self):
        (self.index.parent/'MUTATION_BASELINE.json').unlink()
        with self.writer()as w:
            with self.assertRaises(Exception):self.reserve(w)
    def test_concurrent_executor_fails(self):
        with self.writer():
            with self.assertRaises(j.JournalHold):
                with self.writer():pass
    def test_transport_file_exists_fails(self):
        (self.transport/'001_POST.json').write_text('{}')
        with self.writer()as w:
            with self.assertRaises(j.JournalHold):self.reserve(w)
    def test_foreign_url_fails_before_reservation(self):
        with self.writer()as w:
            with self.assertRaises(j.JournalHold):w.reserve('POST','https://other.org/api/deposit/depositions',b'{}',self.transport/'001_POST.json',self.now(),'fixture:1',digest.require_write_budget)
        self.assertEqual(json.loads(self.index.read_text())['reservations'],[])
    def test_unlocked_reservation_fails(self):
        with self.assertRaises(j.JournalHold):self.reserve(self.writer())

def fixture():
    source={'creators':[{'name':'Hart, Justin D.','affiliation':'Viridis LLC','orcid':'0009-0008-3082-2482'}],'license':{'id':'cc-by-4.0'},'access_right':'open','communities':[{'id':'viridis-canon'}],'language':'eng','resource_type':{'type':'publication','subtype':'preprint','title':'Preprint'}}
    public=copy.deepcopy(source);public.update(title='Viridis Methods Digest — 2026-W41',description='<p>Scope only</p>',publication_date='2026-10-07',keywords=['Methods Digest'],related_identifiers=[{'identifier':'10.5281/zenodo.21971052','relation':'isSupplementTo','scheme':'doi'}])
    legacy={'id':21971052,'doi':'10.5281/zenodo.21971052','metadata':copy.deepcopy(source)}
    native={'id':'21971052','pids':{'doi':{'identifier':legacy['doi']}},'access':{'record':'public','files':'public','status':'open','embargo':{'active':False,'reason':None}},'metadata':{'creators':[{'affiliations':[{'name':'Viridis LLC'}],'person_or_org':{'family_name':'Hart','given_name':'Justin D.','name':'Hart, Justin D.','type':'personal','identifiers':[{'identifier':'0009-0008-3082-2482','scheme':'orcid'}]}}],'rights':[{'id':'cc-by-4.0','title':{'en':'CC BY 4.0'}}],'resource_type':{'id':'publication-preprint','title':{'en':'Preprint'}},'languages':[{'id':'eng','title':{'en':'English'}}],'publisher':'Zenodo'}}
    template={'id':'issupplementto','title':{'en':'Is supplement to','de':'Ergänzt'}}
    return public,source,legacy,native,template
class MetadataTests(unittest.TestCase):
    def test_closed_documented_api_encoding(self):
        public,source,*_=fixture();p=m.closed_payload(public,source)['metadata'];self.assertEqual(p['license'],'cc-by-4.0');self.assertEqual(p['upload_type'],'publication');self.assertEqual(p['publication_type'],'preprint');self.assertNotIn('resource_type',p);self.assertEqual(p['title'],public['title'])
    def test_native_creator_rights_template_exact(self):
        public,source,legacy,native,template=fixture();v=m.native_metadata(public,source,legacy,native,template);self.assertEqual(v['creators'],native['metadata']['creators']);self.assertEqual(v['rights'],native['metadata']['rights']);self.assertNotIn('version',v);self.assertNotIn('additional_descriptions',v)
    def test_changed_license_fails(self):
        public,source,*_=fixture();public['license']={'id':'apache-2.0'}
        with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
    def test_changed_creator_fails(self):
        public,source,*_=fixture();public['creators'][0]['orcid']='different'
        with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
    def test_unknown_field_fails(self):
        public,source,*_=fixture();public['doi']='10.5281/zenodo.999'
        with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
    def test_resource_type_conflict_fails(self):
        public,source,*_=fixture();public['publication_type']='article'
        with self.assertRaises(m.MetadataHold):m.closed_payload(public,source)
    def test_fresh_source_license_mismatch_fails(self):
        values=list(fixture());values[2]['metadata']['license']={'id':'wrong'}
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_native_source_creator_mismatch_fails(self):
        values=list(fixture());values[3]['metadata']['creators'][0]['person_or_org']['identifiers'][0]['identifier']='wrong'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_native_given_family_mismatch_fails(self):
        values=list(fixture());values[3]['metadata']['creators'][0]['person_or_org']['given_name']='wrong'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_custom_unknown_creator_field_fails(self):
        values=list(fixture());values[3]['metadata']['creators'][0]['role']='owner'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_native_rights_mismatch_fails(self):
        values=list(fixture());values[3]['metadata']['rights'][0]['id']='wrong'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_native_resource_mismatch_fails(self):
        values=list(fixture());values[3]['metadata']['resource_type']['id']='publication-article'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_wrong_source_record_id_fails(self):
        values=list(fixture());values[3]['id']='123'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_wrong_source_doi_fails(self):
        values=list(fixture());values[3]['pids']['doi']['identifier']='wrong'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_wrong_relation_vocabulary_fails(self):
        values=list(fixture());values[4]['id']='isderivedfrom'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_changed_relation_claim_fails(self):
        values=list(fixture());values[0]['related_identifiers'][0]['relation']='isIdenticalTo'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
    def test_restricted_access_fails(self):
        values=list(fixture());values[3]['access']['files']='restricted'
        with self.assertRaises(m.MetadataHold):m.native_metadata(*values)
if __name__=='__main__':unittest.main()
