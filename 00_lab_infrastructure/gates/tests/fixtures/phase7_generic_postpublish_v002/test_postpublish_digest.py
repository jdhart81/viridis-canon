"""Portable pure composition regressions; no runtime/publication verdict.

Synthetic rows are TEST_FIXTURES, never imported into a runtime admission.
"""
from copy import deepcopy
import contextlib, hashlib, importlib.util, json, tempfile, types, unittest
from unittest.mock import patch
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

HERE=Path(__file__).parent
p=load('postpublish_digest',HERE/'postpublish_digest.py')
v=load('coverage_provenance',HERE/'coverage_provenance.py')
RECEIPT={'path':'test/registration.json','sha256':'1'*64}

class Rows(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
        self.before={'tree_root':str(self.root),'file_entities':[],'run_entities':[],
            'publication_entities':[{'id':'old:'+str(n),'path':'old/'+str(n),'enforcement_acceptable':True,'opaque':{'n':n}} for n in range(35)],
            'enforcement_activation':{'exact':'original'},'premise_declaration_cutover_run':'Run-188'}
        gid='new:group';notes=[]
        for n in range(49):
            path='notes/'+str(n);(self.root/path).mkdir(parents=True)
            notes.append({'id':'new:'+str(n),'path':path,'entity_type':'METHODS_DIGEST_NOTE','group_id':gid,'certifies':'LISTED_NOTE_SCOPE_ONLY','registration_receipt':deepcopy(RECEIPT),'enforcement_acceptable':True,'registration_revalidated':True,'publication_registration_status':'PASS'})
        (self.root/'digest').mkdir()
        self.rows=[{'id':gid,'path':'digest','entity_type':'METHODS_DIGEST_GROUP','certifies':False,'certificate_valid':False,'note_ids':[r['id'] for r in notes],'registration_receipt':deepcopy(RECEIPT),'enforcement_acceptable':True,'registration_revalidated':True,'publication_registration_status':'PASS'},*notes]
    def stage(self):return p.append_rows(self.root,self.before,self.rows,RECEIPT)
    def test_35_plus_50_is_85(self):
        staged=self.stage();out=p.check_scan(self.before,self.rows,staged);self.assertEqual((out['old_rows'],out['new_rows'],out['total_rows']),(35,50,85))
    def test_future_population_counts_are_derived(self):
        self.before['publication_entities'].append({'id':'old:35','path':'old/35','enforcement_acceptable':True});self.assertEqual(p.check_scan(self.before,self.rows,self.stage())['total_rows'],86)
    def test_prior_rows_preserved_type_exact(self):
        staged=self.stage();staged['publication_entities'][0]['opaque']['n']=False
        with self.assertRaisesRegex(ValueError,'PRIOR_FULL_ROW_CHANGED'):p.check_scan(self.before,self.rows,staged)
    def test_prior_missing(self):
        staged=self.stage();staged['publication_entities'].pop(0)
        with self.assertRaisesRegex(ValueError,'MEMBERSHIP'):p.check_scan(self.before,self.rows,staged)
    def test_new_missing(self):
        staged=self.stage();staged['publication_entities'].pop()
        with self.assertRaisesRegex(ValueError,'MEMBERSHIP'):p.check_scan(self.before,self.rows,staged)
    def test_new_changed(self):
        staged=self.stage();staged['publication_entities'][-1]['certifies']='AGGREGATE'
        with self.assertRaisesRegex(ValueError,'NEW_FULL_ROW_CHANGED'):p.check_scan(self.before,self.rows,staged)
    def test_extra_row(self):
        staged=self.stage();staged['publication_entities'].append({'id':'rogue'})
        with self.assertRaisesRegex(ValueError,'MEMBERSHIP'):p.check_scan(self.before,self.rows,staged)
    def test_control_changed(self):
        staged=self.stage();staged['enforcement_activation']['exact']='changed'
        with self.assertRaisesRegex(ValueError,'CONTROL_CHANGED'):p.check_scan(self.before,self.rows,staged)
    def test_cutover_changed(self):
        staged=self.stage();staged['premise_declaration_cutover_run']='Run-190'
        with self.assertRaisesRegex(ValueError,'CONTROL_CHANGED'):p.check_scan(self.before,self.rows,staged)
    def test_hold_scan(self):
        staged=self.stage();staged['publication_entities'][0]['enforcement_acceptable']=False
        with self.assertRaises(ValueError):p.check_scan(self.before,self.rows,staged)
    def test_duplicate_old(self):
        self.before['publication_entities'].append(deepcopy(self.before['publication_entities'][0]))
        with self.assertRaisesRegex(ValueError,'UNIQUE_ROWS'):self.stage()
    def test_duplicate_new(self):
        self.rows.append(deepcopy(self.rows[-1]))
        with self.assertRaisesRegex(ValueError,'UNIQUE_ROWS'):self.stage()
    def test_corpus_id_collision(self):
        self.before['file_entities'].append({'id':self.rows[1]['id'],'path':'a'})
        with self.assertRaisesRegex(ValueError,'CORPUS_ID_COLLISION'):self.stage()
    def test_corpus_path_collision(self):
        self.before['run_entities'].append({'id':'run','path':self.rows[1]['path']})
        with self.assertRaisesRegex(ValueError,'PATH_COLLISION'):self.stage()
    def test_new_id_collision(self):
        self.rows[1]['id']=self.before['publication_entities'][0]['id']
        with self.assertRaisesRegex(ValueError,'NEW_ID_COLLISION'):self.stage()
    def test_new_path_collision(self):
        self.rows[1]['path']=self.rows[2]['path']
        with self.assertRaisesRegex(ValueError,'PATH_COLLISION'):self.stage()
    def test_foreign_receipt(self):
        self.rows[1]['registration_receipt']['sha256']='2'*64
        with self.assertRaisesRegex(ValueError,'DEFAULT_NEW_ROW_HOLD'):self.stage()
    def test_new_hold(self):
        self.rows[1]['enforcement_acceptable']=False
        with self.assertRaisesRegex(ValueError,'DEFAULT_NEW_ROW_HOLD'):self.stage()
    def test_missing_revalidation(self):
        self.rows[1]['registration_revalidated']=False
        with self.assertRaisesRegex(ValueError,'DEFAULT_NEW_ROW_HOLD'):self.stage()
    def test_aggregate_certified(self):
        self.rows[0]['certifies']=True
        with self.assertRaisesRegex(ValueError,'NO_AGGREGATE_CERTIFICATE'):self.stage()
    def test_note_aggregate_scope(self):
        self.rows[1]['certifies']=True
        with self.assertRaisesRegex(ValueError,'EXACT_CHILD_SCOPE'):self.stage()
    def test_missing_child_list(self):
        self.rows[0]['note_ids'].pop()
        with self.assertRaisesRegex(ValueError,'NO_AGGREGATE_CERTIFICATE'):self.stage()
    def test_symlink_read_fails(self):
        f=self.root/'x';f.write_text('x');s=self.root/'s';s.symlink_to(f)
        with self.assertRaisesRegex(ValueError,'REGULAR_INPUT'):p.raw(s)
    def test_hash_mismatch(self):
        f=self.root/'x';f.write_text('x')
        with self.assertRaisesRegex(ValueError,'BOUND_HASH'):p.bound(self.root,{'path':str(f),'sha256':'0'*64})
    def test_immutable_no_replay(self):
        f=self.root/'x';p.immutable(f,b'x')
        with self.assertRaisesRegex(ValueError,'EXCLUSIVE_OUTPUT'):p.immutable(f,b'x')

class Catalog(unittest.TestCase):
    def setUp(self):
        self.oldgroup={'entity_id':'g0','certifies':False,'notes':[{'entity_id':'n0','certifies':'LISTED_NOTE_SCOPE_ONLY'}]}
        self.newgroup={'entity_id':'g1','certifies':False,'notes':[{'entity_id':'n'+str(n+1),'certifies':'LISTED_NOTE_SCOPE_ONLY'} for n in range(49)]}
        self.before={'records':[{'record_id':'historical','metadata':{'verification_coverage':{'ledger_sha256':'a'*64}}}], 'publications':[{'entity_id':'original-publication'}], 'methods_digests':[deepcopy(self.oldgroup)],'opaque':{'never':'rewritten'}}
        def row(identity,typ):return {'id':identity,'entity_type':typ,'publication_registration_status':'PASS','registration_revalidated':True,'publication_binding_status':'PUBLICATION_BOUND','enforcement_acceptable':True,'reasons':[],'publication_registration_reasons':[],'status':'SCOPED_DIGEST' if typ=='METHODS_DIGEST_GROUP' else 'CERTIFIED','certifies':False if typ=='METHODS_DIGEST_GROUP' else 'LISTED_NOTE_SCOPE_ONLY','certificate_valid':typ!='METHODS_DIGEST_GROUP'}
        self.ledger={'publication_entities':[row('g0','METHODS_DIGEST_GROUP'),row('n0','METHODS_DIGEST_NOTE')]};prior_raw=p.encoded(self.ledger)
        self.before['coverage_provenance']=v.construct_provenance(self.before,prior_raw,historical_name='historical',current_name='first-current')
        self.before['catalog_digest']=v.fingerprint({k:x for k,x in self.before.items() if k!='catalog_digest'})
        self.ledger['publication_entities'] += [row('g1','METHODS_DIGEST_GROUP'),*[row('n'+str(n+1),'METHODS_DIGEST_NOTE') for n in range(49)]]
        self.groups=[self.oldgroup,self.newgroup]
    def candidate(self):return p.catalog_projection(self.before,self.groups,p.encoded(self.ledger),v,snapshot_name='successor-current')
    def test_additive_50_provenance_preserves_old_prefix(self):
        c,a=self.candidate();self.assertEqual(a['new_groups'],1);self.assertEqual(len(c['coverage_provenance']['current_entities']),52);self.assertEqual(c['coverage_provenance']['current_entities'][:2],self.before['coverage_provenance']['current_entities']);self.assertEqual(c['records'],self.before['records'])
    def test_prior_catalog_digest_mismatch(self):
        self.before['catalog_digest']='f'*64
        with self.assertRaisesRegex(ValueError,'PRIOR_CATALOG_DIGEST'):self.candidate()
    def test_prior_group_mutation(self):
        self.groups[0]['unknown']='changed'
        with self.assertRaisesRegex(ValueError,'PRIOR_DIGEST_CONTENT_REWRITTEN'):self.candidate()
    def test_removed_prior_group(self):
        self.groups=self.groups[1:]
        with self.assertRaises(ValueError):self.candidate()
    def test_new_row_missing(self):
        self.ledger['publication_entities'].pop()
        with self.assertRaisesRegex(ValueError,'CURRENT_ENTITY_MISSING'):self.candidate()
    def test_new_row_hold(self):
        self.ledger['publication_entities'][-1]['enforcement_acceptable']=False
        with self.assertRaisesRegex(ValueError,'CURRENT_REGISTRATION_HOLD'):self.candidate()
    def test_prior_metadata_guard(self):
        c,a=self.candidate();c['opaque']['never']='changed'
        with self.assertRaisesRegex(ValueError,'EXISTING_FIELD_CHANGED'):v.audit_additive_update(self.before,c,c['coverage_provenance'],p.encoded(self.ledger),p.whole_catalog_guard)
    def test_type_exact_record(self):
        c,a=self.candidate();c['records'][0]['record_id']=False
        with self.assertRaises(ValueError):v.audit_additive_update(self.before,c,c['coverage_provenance'],p.encoded(self.ledger),p.whole_catalog_guard)
    def test_no_additive_group(self):
        with self.assertRaisesRegex(ValueError,'EXACT_ADDITIVE_DIGEST_PREFIX'):p.whole_catalog_guard(self.before,self.before,[self.oldgroup])
    def test_past_provenance_rewritten(self):
        c,a=self.candidate();c['coverage_provenance']['current_snapshots'][0]['sha256']='f'*64
        with self.assertRaises(ValueError):v.audit_additive_update(self.before,c,c['coverage_provenance'],p.encoded(self.ledger),p.whole_catalog_guard)
    def test_new_aggregate_certification(self):
        self.groups[1]['certifies']=True
        with self.assertRaisesRegex(ValueError,'NO_AGGREGATE_CERTIFICATION'):self.candidate()
    def test_leaf_scope_expansion(self):
        self.groups[1]['notes'][0]['certifies']='SOURCE_ADMITTED'
        with self.assertRaisesRegex(ValueError,'LISTED_SCOPES_ONLY'):self.candidate()

class CatalogEarlyAdmission(unittest.TestCase):
    """Control-flow fixtures only: no fake consumer is runtime evidence."""
    def run_rejection(self, *, forged_origin=False, malformed_plan=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();ledger_path=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_path.parent.mkdir();ledger_path.write_bytes(p.encoded({'publication_entities':[]}))
            checkout=root/'checkout';(checkout/'docs/data').mkdir(parents=True);(checkout/'catalog').mkdir();(checkout/'docs/data/catalog.json').write_bytes(b'{}');(checkout/'catalog/config.json').write_bytes(b'{}')
            output=root/'never-created'
            pins=[{'name':'invoke_weekly_digest.py','path':str(root/'invoke_weekly_digest.py'),'sha256':'1'*64}]
            plan={'purpose_source_pins':pins,'runtime_consumer':{'path':str(root/'runtime.py'),'sha256':'2'*64},'current_runtime_closure':{'path':'closure.json','sha256':'3'*64},'source_origin':{'path':'forged.json' if forged_origin else 'origin.json','sha256':'4'*64},'malformed':malformed_plan}
            config={'plan':{'path':'plan.json','sha256':'5'*64},'merged_tree':{'path':'tree.json','sha256':'6'*64},'expected_ssot_sha256':p.digest(p.raw(ledger_path))}
            calls=[]
            def origin(actual_root,binding,actual_pins):
                calls.append('origin')
                self.assertEqual(actual_root,root);self.assertEqual(actual_pins,pins)
                if binding['path']=='forged.json':raise ValueError('HOLD_FORGED_ORIGIN')
            def require_plan(actual_root,actual_plan):
                calls.append('plan')
                self.assertEqual(actual_root,root)
                if actual_plan['malformed']:raise ValueError('HOLD_MALFORMED_PLAN')
            live=types.ModuleType('weekly_digest_runtime');live.require_origin=origin
            engine=types.ModuleType('weekly_digest_executor');engine.require_plan=require_plan
            current=types.SimpleNamespace(require_current_closure=lambda *_:None)
            invoke=types.SimpleNamespace(session=lambda *_:contextlib.nullcontext())
            # Mock only admission plumbing to isolate failure ordering; neither
            # a real population nor a PASS receipt is constructed by this test.
            baselines={'docs/data/catalog.json':{'sha256':p.digest(b'{}')},'catalog/config.json':{'sha256':p.digest(b'{}')}}
            path_route=lambda value:root if value=='/private/tmp' else Path(value)
            with patch.object(p,'ROOT',root),patch.object(p,'Path',side_effect=path_route),patch.object(p,'verify_config'),patch.object(p,'object_value',return_value=(root/'plan.json',plan)),patch.object(p,'load',side_effect=[current,invoke]),patch.object(p,'checkout_materials',return_value={}),patch.object(p,'checkout_baselines',return_value=baselines),patch.dict('sys.modules',{'weekly_digest_runtime':live,'weekly_digest_executor':engine}),patch.object(p.importlib,'import_module',side_effect=AssertionError('renderer reached before rejection')):
                with self.assertRaisesRegex(ValueError,'HOLD_FORGED_ORIGIN' if forged_origin else 'HOLD_MALFORMED_PLAN'):
                    p.prepare_catalog(config,checkout,output)
            self.assertFalse(output.exists())
            self.assertEqual(calls,['origin'] if forged_origin else ['origin','plan'])
    def test_forged_origin_fails_before_pointer_import_and_output(self):self.run_rejection(forged_origin=True)
    def test_malformed_plan_fails_before_pointer_import_and_output(self):self.run_rejection(malformed_plan=True)

class CatalogBoundBaselines(unittest.TestCase):
    def test_changed_prior_record_with_recomputed_fingerprint_fails(self):
        self.run_change('catalog')
    def test_changed_before_config_fails(self):
        self.run_change('config')
    def run_change(self,kind):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();checkout=root/'checkout';(checkout/'docs/data').mkdir(parents=True);(checkout/'catalog').mkdir()
            catalog={'records':[{'record_id':'prior','title':'original'}]};catalog['catalog_digest']=v.fingerprint(catalog)
            config={'release':'v1'}
            (checkout/'docs/data/catalog.json').write_bytes(p.encoded(catalog));(checkout/'catalog/config.json').write_bytes(p.encoded(config))
            nodes=[]
            for name in ('docs/data/catalog.json','catalog/config.json'):
                data=p.raw(checkout/name);nodes.append({'path':name,'type':'blob','mode':'100644','sha':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()})
            tree=root/'tree.json';tree.write_bytes(p.encoded({'tree':nodes,'truncated':False}));tb=p.binding(tree)
            proof=p.checkout_baselines(root,checkout,tb);self.assertEqual(len(proof),2)
            if kind=='catalog':
                catalog['records'][0]['title']='changed';catalog['catalog_digest']=v.fingerprint({k:x for k,x in catalog.items() if k!='catalog_digest'});(checkout/'docs/data/catalog.json').write_bytes(p.encoded(catalog))
            else:
                config['release']='changed';(checkout/'catalog/config.json').write_bytes(p.encoded(config))
            with self.assertRaisesRegex(ValueError,'OWN_PRIOR_CATALOG_DATA_BLOB'):
                p.checkout_baselines(root,checkout,tb)
            ledger=root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger.parent.mkdir();ledger.write_bytes(b'{}')
            plan_binding={'path':'plan.json','sha256':'1'*64};plan={'runtime_consumer':{'path':'runtime.py','sha256':'2'*64},'current_runtime_closure':{'path':'closure.json','sha256':'3'*64}}
            cfg={'plan':plan_binding,'merged_tree':tb,'expected_ssot_sha256':p.digest(b'{}')};real_object=p.object_value
            route_object=lambda actual_root,value:(root/'plan.json',plan) if value==plan_binding else real_object(actual_root,value)
            route_path=lambda value:root if value=='/private/tmp' else Path(value)
            current=types.SimpleNamespace(require_current_closure=lambda *_:None)
            with patch.object(p,'ROOT',root),patch.object(p,'Path',side_effect=route_path),patch.object(p,'verify_config'),patch.object(p,'object_value',side_effect=route_object),patch.object(p,'load',return_value=current),patch.object(p,'checkout_materials',return_value={}):
                with self.assertRaisesRegex(ValueError,'OWN_PRIOR_CATALOG_DATA_BLOB'):
                    p.prepare_catalog(cfg,checkout,root/'output')
            self.assertFalse((root/'output').exists())

if __name__=='__main__':unittest.main()
