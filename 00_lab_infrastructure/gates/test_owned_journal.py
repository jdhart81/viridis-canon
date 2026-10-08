import copy,hashlib,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
F=Path(__file__).parent/'test_fixtures'
sys.path.insert(0,str(F))
import mutation_journal_writer as original
import methods_digest as digest
from owned_journal_writer import OwnedJournalWriter

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.index=self.root/original.JOURNAL;self.index.parent.mkdir(parents=True);self.index.write_bytes(original.raw_json({'standard':'VRS_PHASE7_MUTATION_JOURNAL_INDEX_1','status':'ACTIVE','baseline':{},'reservations':[],'updated_at_utc':'2026-10-08T00:00:00+00:00'}));self.at='2026-10-08T14:00:00+00:00';self.file={'filename':'paper.pdf','filesize':2,'checksum':'a'*32,'id':'00000000-0000-0000-0000-000000000001','links':{}}
        v={'method':'POST','url':'https://zenodo.org/api/deposit/depositions/23226761/actions/newversion','status':'HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE','http_status':201,'response':{'id':23299999,'state':'unsubmitted','submitted':False,'files':[self.file]}};self.creation=self.root/'CREATE.json';self.creation.write_bytes(original.raw_json(v));self.cb={'path':str(self.creation),'sha256':original.sha(self.creation.read_bytes())}
    def tearDown(self):self.tmp.cleanup()
    def events(self,root,at):
        value=json.loads(self.index.read_bytes());return [json.loads(Path(row['path']).read_bytes())for row in value['reservations']]
    def budget(self,root,method,at):return digest.require_write_budget(self.events(root,at),method,at,complete=True)
    def writer(self):return OwnedJournalWriter(self.root,self.root/'out',self.events,self.budget)
    def drop(self,w,**kw):
        args=dict(draft_id='23299999',previous_record_id='23226761',expected_file=self.file,transport_path=self.root/'transport/003_DELETE.json',at_utc=self.at,operation_id='owned:drop',compute=digest.require_write_budget,creation_evidence=self.cb);args.update(kw);return w.reserve_drop(**args)
    def test_original_sources_byte_exact(self):
        self.assertEqual(hashlib.sha256((F/'mutation_journal_writer.py').read_bytes()).hexdigest(),'a2a72c49b5bc67a5c7535320bab5b6513b8cbfac3cf6c19d39b2e0c3d5d5c4e8');self.assertEqual(hashlib.sha256((F/'methods_digest.py').read_bytes()).hexdigest(),'5fcdc53f68d008357e0aef1dbb93f74695aa91119792f78151a8c61a0a9e05e5')
    def test_delete_reserved_before_network(self):
        with self.writer()as w:r=self.drop(w)
        self.assertEqual(r['used_before'],0);self.assertEqual(self.budget(self.root,'POST',self.at)['used'],1);self.assertFalse((self.root/'transport/003_DELETE.json').exists())
    def test_failed_or_uncertain_reservation_stays_charged(self):
        with self.writer()as w:self.drop(w)
        self.assertEqual(self.budget(self.root,'PUT',self.at)['used'],1)
    def test_second_invocation_uses_actual_current_count(self):
        with self.writer()as w:self.drop(w)
        with OwnedJournalWriter(self.root,self.root/'out2',self.events,self.budget)as w:
            r=w.reserve('PUT','https://zenodo.org/api/deposit/depositions/23299999',b'{}',self.root/'transport/004_PUT.json',self.at,'owned:metadata',digest.require_write_budget)
        self.assertEqual(r['used_before'],1)
    def test_new_day_preserves_yesterday_history_but_budget_resets(self):
        with self.writer()as w:self.drop(w)
        later='2026-10-09T14:00:00+00:00';self.assertEqual(self.budget(self.root,'PUT',later)['used'],0);self.assertEqual(len(self.events(self.root,later)),1)
    def test_lock_required(self):self.assertRaises(original.JournalHold,self.drop,self.writer())
    def test_parent_cannot_be_deleted(self):
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w,draft_id='23226761')
    def test_published_start_not_owned_draft(self):
        v=json.loads(self.creation.read_bytes());v['response']['submitted']=True;self.creation.write_bytes(original.raw_json(v));self.cb['sha256']=original.sha(self.creation.read_bytes())
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w)
    def test_changed_creation_hash_fails(self):
        self.creation.write_bytes(self.creation.read_bytes()+b'\n')
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w)
    def test_foreign_newversion_source_fails(self):
        v=json.loads(self.creation.read_bytes());v['url']='https://zenodo.org/api/deposit/depositions/1/actions/newversion';self.creation.write_bytes(original.raw_json(v));self.cb['sha256']=original.sha(self.creation.read_bytes())
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w)
    def test_changed_inherited_checksum_fails(self):
        f=copy.deepcopy(self.file);f['checksum']='b'*32
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w,expected_file=f)
    def test_unlisted_entry_field_fails(self):
        f=dict(self.file,public=True)
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w,expected_file=f)
    def test_existing_transport_cannot_be_reserved_again(self):
        p=self.root/'transport/003_DELETE.json';p.parent.mkdir();p.write_text('{}')
        with self.writer()as w:self.assertRaises(original.JournalHold,self.drop,w)
    def test_post_put_use_original_exact_method(self):self.assertIs(OwnedJournalWriter.reserve,original.JournalWriter.reserve)
    def test_original_generic_delete_still_rejected(self):
        with self.writer()as w:self.assertRaises(original.JournalHold,w.reserve,'DELETE','https://zenodo.org/api/deposit/depositions/23299999/files/1',b'',self.root/'transport/003_DELETE.json',self.at,'owned:drop',digest.require_write_budget)
    def test_daily_tenth_attempt_allowed_eleventh_refused(self):
        for i in range(10):
            with OwnedJournalWriter(self.root,self.root/f'out{i}',self.events,self.budget)as w:w.reserve('POST','https://zenodo.org/api/deposit/depositions/23299999/actions/publish',b'{}',self.root/f'transport/{i:03d}_POST.json',self.at,f'owned:attempt:{i}',digest.require_write_budget)
        with OwnedJournalWriter(self.root,self.root/'last',self.events,self.budget)as w:self.assertRaises(digest.DigestHold,w.reserve,'POST','https://zenodo.org/api/deposit/depositions/23299999/actions/publish',b'{}',self.root/'transport/099_POST.json',self.at,'owned:eleven',digest.require_write_budget)
        self.assertEqual(len(self.events(self.root,self.at)),10)
if __name__=='__main__':unittest.main()
