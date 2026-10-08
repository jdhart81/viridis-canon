"""Own exact URL/method/body guard; no full scientific admission claim."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'test_fixtures'))
import weekly_digest_executor as e
class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.files=[]
        for name in sorted(e.machine.NAMES):
            p=self.root/name;p.write_bytes(b'approved');self.files.append({'name':name,'path':str(p),'bytes':8,'sha256':hashlib.sha256(b'approved').hexdigest(),'md5':hashlib.md5(b'approved').hexdigest()})
        self.plan={'predecessor_record_id':'23226761','approved_inventory':self.files,'start_kind':'CREATE_WEEK'};manifest={'public_metadata':{'title':'approved','creators':[{'name':'Fixture'}],'description':'Fixture science, not clearance','upload_type':'publication','publication_type':'preprint','access_right':'open','license':'cc-by-4.0','publication_date':'2026-10-10','keywords':['methods'],'resource_type':{'type':'publication','subtype':'preprint','title':'Preprint'}}};source={'response':{'metadata':dict(manifest['public_metadata'])}}
        for key,value in [('digest_manifest',manifest),('source_legacy_receipt',source)]:
            f=self.root/(key+'.json');f.write_bytes(e.raw_json(value));self.plan[key]=e.binding(f)
        p=self.root/'last.json';p.write_bytes(e.raw_json({'expected_legacy':{'links':{'bucket':'https://zenodo.org/api/files/00000000-0000-0000-0000-000000000000'}}}));self.state={'record_id':'23300000','inherited_inventory':[{'filename':n,'id':'00000000-0000-0000-0000-000000000001','checksum':'a'*32,'filesize':8,'links':{}}for n in e.machine.NAMES],'last_validation':e.binding(p)}
    def tearDown(self):self.tmp.cleanup()
    def cmd(self,step):
        root='https://zenodo.org';method='POST';body=b'{}';kind='application/json';delete=None
        if step=='NEW_VERSION':url=root+'/api/deposit/depositions/23226761/actions/newversion'
        elif step=='CREATE_WEEK':
            url=root+'/api/deposit/depositions'
            from digest_metadata import closed_payload
            from first_digest_state import encode_api_communities
            _,m=e.bound(self.root,self.plan['digest_manifest']);_,s=e.bound(self.root,self.plan['source_legacy_receipt']);body=e.raw_json(encode_api_communities(closed_payload(m['public_metadata'],s['response']['metadata'])))
        elif step=='METADATA':
            url=root+'/api/deposit/depositions/23300000';method='PUT'
            from digest_metadata import closed_payload
            from first_digest_state import encode_api_communities
            _,m=e.bound(self.root,self.plan['digest_manifest']);_,s=e.bound(self.root,self.plan['source_legacy_receipt']);body=e.raw_json(encode_api_communities(closed_payload(m['public_metadata'],s['response']['metadata'])))
        elif step.startswith('DROP:'):
            delete=next(x for x in self.state['inherited_inventory']if x['filename']==step[5:]);url=root+'/api/deposit/depositions/23300000/files/'+delete['id'];method='DELETE';body=b''
        elif step.startswith('UPLOAD:'):url=root+'/api/files/00000000-0000-0000-0000-000000000000/'+step[7:];method='PUT';body=b'approved';kind='application/octet-stream'
        elif step=='RESERVE_DOI':url=root+'/api/records/23300000/draft/pids/doi'
        else:url=root+'/api/deposit/depositions/23300000/actions/publish'
        return {'method':method,'url':url,'body':body,'content_type':kind,'delete_file':delete}
    def call(self,step,c):return e.require_command(self.root,self.plan,self.state,step,c)
    def test_all_closed_steps_pass(self):
        for step in ['NEW_VERSION','CREATE_WEEK','METADATA','DROP:paper.pdf','UPLOAD:paper.pdf','RESERVE_DOI','PUBLISH']:
            with self.subTest(step=step):self.plan['start_kind']='NEW_VERSION'if step=='NEW_VERSION'else'CREATE_WEEK';self.call(step,self.cmd(step))
    def test_each_foreign_record_url_fails(self):
        for step in ['NEW_VERSION','METADATA','DROP:paper.pdf','RESERVE_DOI','PUBLISH']:
            self.plan['start_kind']='NEW_VERSION'if step=='NEW_VERSION'else'CREATE_WEEK'
            c=self.cmd(step);c['url']=c['url'].replace('23226761','9999').replace('23300000','9999');self.assertRaises(ValueError,self.call,step,c)
    def test_start_not_reused_as_other_step(self):self.assertRaises(ValueError,self.call,'DROP:paper.pdf',self.cmd('NEW_VERSION'))
    def test_wrong_method_fails(self):
        c=self.cmd('PUBLISH');c['method']='PUT';self.assertRaises(ValueError,self.call,'PUBLISH',c)
    def test_changed_upload_byte_fails(self):
        c=self.cmd('UPLOAD:paper.pdf');c['body']=b'altered';self.assertRaises(ValueError,self.call,'UPLOAD:paper.pdf',c)
    def test_changed_upload_source_file_fails(self):
        c=self.cmd('UPLOAD:paper.pdf');(self.root/'paper.pdf').write_bytes(b'altered');self.assertRaises(ValueError,self.call,'UPLOAD:paper.pdf',c)
    def test_changed_bucket_uuid_fails(self):
        c=self.cmd('UPLOAD:paper.pdf');c['url']=c['url'].replace('000000000000','000000000999');self.assertRaises(ValueError,self.call,'UPLOAD:paper.pdf',c)
    def test_delete_another_entry_fails(self):
        c=self.cmd('DROP:paper.pdf');c['delete_file']=dict(c['delete_file'],filename='paper.tex');self.assertRaises(ValueError,self.call,'DROP:paper.pdf',c)
    def test_nonempty_delete_body_fails(self):
        c=self.cmd('DROP:paper.pdf');c['body']=b'{}';self.assertRaises(ValueError,self.call,'DROP:paper.pdf',c)
    def test_nonempty_publish_body_fails(self):
        c=self.cmd('PUBLISH');c['body']=b'{"override":true}';self.assertRaises(ValueError,self.call,'PUBLISH',c)
    def test_empty_create_metadata_fails(self):
        c=self.cmd('CREATE_WEEK');c['body']=b'{}';self.assertRaises(ValueError,self.call,'CREATE_WEEK',c)
    def test_unknown_command_field_fails(self):
        c=self.cmd('PUBLISH');c['retry']=True;self.assertRaises(ValueError,self.call,'PUBLISH',c)
    def test_wrong_upload_content_type_fails(self):
        c=self.cmd('UPLOAD:paper.pdf');c['content_type']='application/json';self.assertRaises(ValueError,self.call,'UPLOAD:paper.pdf',c)
if __name__=='__main__':unittest.main()
