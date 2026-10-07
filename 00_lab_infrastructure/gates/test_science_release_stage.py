"""Portable temporary-input staging/queue tests; no real verifier/renderer/network."""
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch
import contextlib,hashlib,io,json,sys,tempfile,unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
import science_release_stage as m, science_release_queue as q, certificate_inspection as ci, mirror_parity as parity
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def files(p):return {str(x.relative_to(p)):x.read_bytes() for x in p.rglob('*')if x.is_file()}

class Fixture:
    def __init__(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve();self.run='Run-141'
        self.source=self.root/q.PAPER_ROOT/'Run-141_synthetic';self.source.mkdir(parents=True)
        save(self.source/'DISPOSITION.json',{'disposition':'METHODS_NOTE','run_id':self.run});(self.source/'paper.tex').write_text('SYNTHETIC ORIGINAL SOURCE')
        self.certdir=self.root/'RESEARCH_PIPELINE_v2/lean_certificates'/self.run;self.certdir.mkdir(parents=True)
        labels={'bindings.candidate_proof':'candidate.lean','bindings.formal_statement':'statement.lean','bindings.request':'request.json','bindings.independent_cloud_receipt':'receipt.json','bindings.sealed_paper_inputs.SEALED_paper.tex':'SEALED_paper.tex','bindings.sealed_paper_inputs.SEALED_paper.pdf':'SEALED_paper.pdf'}
        self.inputs=[]
        for label,name in labels.items():
            p=self.certdir/name;p.write_bytes(('SYNTHETIC TEST INPUT '+label).encode());self.inputs.append({'label':label,'path':str(p),'sha256':sha(p)})
        self.candidate=self.certdir/'candidate.lean';self.formal=self.certdir/'statement.lean';self.receipt=self.certdir/'receipt.json'
        self.cert=self.certdir/'LEAN_ZERO_SORRY_CERTIFICATE.json';save(self.cert,{'run_id':self.run,'status':'SYNTHETIC_UNIT_STUB_NOT_CERTIFICATION'})
        self.consumers={}
        for key in ('proof_track','inspection'):
            p=self.root/'RESEARCH_PIPELINE_v2'/('SYNTHETIC_'+key+'.py');p.write_text('SYNTHETIC NEVER EXECUTED\n');self.consumers[key]={'path':str(p),'sha256':sha(p)}
        self.parity={'status':'MATCH','source':'SYNTHETIC GENERATION PARITY ONLY',
            'mirror':str(self.source),'purpose':'PARITY_ONLY_NOT_CERTIFICATION',
            'source_hashes':q.full_directory_snapshot(self.root,self.source),
            'mirror_hashes':q.full_directory_snapshot(self.root,self.source),
            'errors':[],'differences':[],'ignored_metadata_differences':[],'file_count':2}
        self.row={'id':self.run,'entity_type':'RUN','kind':'PAPER',
            'path':str(self.source.relative_to(self.root)),'status':'CERTIFIED',
            'certificate':str(self.cert.relative_to(self.root)),'certificate_valid':True,
            'certified_theorems':['SYNTHETIC_target'],'nonvacuity':['SYNTHETIC_witness'],'parity':deepcopy(self.parity)}
        self.ledger=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';save(self.ledger,{'tree_root':str(self.root),'run_entities':[self.row]})
        self.entry={'schema':q.SCHEMA,'mode':'REPORT_ONLY','run_id':self.run,'entry_id':self.run+'-'+sha(self.cert),'certificate':{'path':str(self.cert),'sha256':sha(self.cert)},'certified_inputs':self.inputs,'consumer_bindings':self.consumers,'source_dir':str(self.source),'source_hashes':q.full_directory_snapshot(self.root,self.source),'route':'WEEKLY_METHODS_DIGEST','digest_week':'2026-W41','existing_public_dois':[],'publication_enabled':False}
        self.entry_path=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/entries'/(self.entry['entry_id']+'.json');save(self.entry_path,self.entry)
        self.out=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/staged'/self.entry['entry_id']/self.run
        self.inspection={'valid':True,'recorded_certificate_current':True,'run_id':self.run,
            'path':str(self.cert),'sha256':sha(self.cert),'certified_theorems':['SYNTHETIC_target'],
            'nonvacuity':['SYNTHETIC_witness'],
            'bindings':[{'label':v['label'],'resolved_path':v['path'],'sha256':v['sha256']} for v in self.inputs]}
        self.current=(self.cert,{'status':'SYNTHETIC_UNIT_STUB_NOT_CERTIFICATION'})
        self.parity_hook=None;self.parity_calls=0;self.inspection_hook=None;self.inspection_calls=0
        self.render_returncode=0;self.render_hook=None;self.stage_hook=None;self.compile_calls=0
    def inspect(self,*a):
        self.inspection_calls+=1
        if self.inspection_hook:self.inspection_hook()
        return deepcopy(self.inspection)
    def fresh_parity(self,*a):
        self.parity_calls+=1
        if self.parity_hook:self.parity_hook()
        return deepcopy(self.parity)
    def existing(self,*a):
        return {'proof_track':SimpleNamespace(current_certificate=lambda *args:self.current),
            'inspection':SimpleNamespace(inspect_certificate=self.inspect),
            'proof_track_binding':deepcopy(self.consumers['proof_track']),
            'inspection_binding':deepcopy(self.consumers['inspection'])}
    def change_row(self,key,value):
        doc=json.loads(self.ledger.read_text());doc['run_entities'][0][key]=value;save(self.ledger,doc)
    def stage(self,row,out,*args):
        out=m._staging_output(self.root,out);out.mkdir(parents=True,exist_ok=False)
        (out/'paper.tex').write_text('SYNTHETIC STAGED TEX')
        for src,name in ((self.cert,'LEAN_ZERO_SORRY_CERTIFICATE.json'),(self.candidate,'VERIFICATION_CANDIDATE.lean'),(self.formal,'VERIFICATION_STATEMENT.lean')):(out/name).write_bytes(src.read_bytes())
        if self.stage_hook:self.stage_hook()
    def complete(self,out,root):
        for src,name in ((self.cert,'LEAN_ZERO_SORRY_CERTIFICATE.json'),(self.candidate,'VERIFICATION_CANDIDATE.lean'),(self.formal,'VERIFICATION_STATEMENT.lean')):
            if src.read_bytes()!=(out/name).read_bytes():raise ValueError('raw proof fixture changed')
        save(out/'SCOPED_RELEASE_MANIFEST.json',{'status':'SYNTHETIC DRAFT NOT APPROVED'})
    def render(self,command,**kwargs):
        self.compile_calls+=1
        if Path(command[0]).name!='tectonic':raise AssertionError('forbidden subprocess')
        if self.render_hook:self.render_hook()
        (Path(kwargs['cwd'])/'build/paper.pdf').write_bytes(b'%PDF-1.4\nSYNTHETIC_UNRENDERED_TEST_ONLY\n')
        return SimpleNamespace(returncode=self.render_returncode,stdout=b'SYNTHETIC RENDER STDOUT',stderr=b'SYNTHETIC RENDER STDERR')
    def call(self,**kwargs):
        with patch.object(q,'load_existing_consumers',side_effect=self.existing),patch.object(parity,'run_parity',side_effect=self.fresh_parity),patch.object(ci,'inspect_certificate',side_effect=self.inspect),patch.object(m,'stage_run',side_effect=self.stage),patch.object(m,'complete_package',side_effect=self.complete),patch('subprocess.run',side_effect=self.render):
            return m.stage_current_entry(self.root,self.entry_path,self.ledger,**kwargs)
    def close(self):self.tmp.cleanup()

class StagingTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def hold(self,**kwargs):
        with self.assertRaises((ValueError,KeyError,FileNotFoundError)):self.f.call(**kwargs)
    def test_positive_stage_is_only_pending_review(self):
        before=files(self.f.source);r=self.f.call();self.assertEqual(r['state'],'STAGED_PENDING_INDEPENDENT_CLAUDE_AUDIT');self.assertFalse(r['publication_enabled']);self.assertFalse(r['local_lean_execution']);self.assertEqual(r['zenodo_writes'],0);self.assertEqual(files(self.f.source),before);self.assertEqual(self.f.compile_calls,1)
    def test_raw_candidate_statement_certificate_uploads_exact(self):
        self.f.call()
        for p,n in((self.f.cert,'LEAN_ZERO_SORRY_CERTIFICATE.json'),(self.f.candidate,'VERIFICATION_CANDIDATE.lean'),(self.f.formal,'VERIFICATION_STATEMENT.lean')):self.assertEqual(p.read_bytes(),(self.f.out/n).read_bytes())
    def test_repeat_idempotent_no_render_or_overwrite(self):
        self.f.call();before=files(self.f.out);r=self.f.call();self.assertEqual(r['state'],'ALREADY_STAGED_IDENTICAL_BYTES');self.assertEqual(self.f.compile_calls,1);self.assertEqual(files(self.f.out),before)
    def test_existing_incomplete_attempt_no_overwrite(self):
        self.f.out.mkdir(parents=True);(self.f.out/'sentinel').write_bytes(b'KEEP');before=files(self.f.out);self.hold();self.assertEqual(files(self.f.out),before);self.assertEqual(self.f.compile_calls,0)
    def test_changed_source_before_stage_hold(self):(self.f.source/'paper.tex').write_bytes(b'CHANGED');self.hold();self.assertFalse(self.f.out.exists())
    def test_missing_input_before_stage_hold(self):self.f.receipt.unlink();self.hold();self.assertFalse(self.f.out.exists())
    def test_changed_receipt_before_stage_hold(self):self.f.receipt.write_bytes(b'CHANGED');self.hold();self.assertFalse(self.f.out.exists())
    def test_changed_certificate_before_stage_hold(self):self.f.cert.write_bytes(b'CHANGED');self.hold();self.assertFalse(self.f.out.exists())
    def test_changed_consumer_before_stage_hold(self):Path(self.f.consumers['inspection']['path']).write_bytes(b'CHANGED');self.hold();self.assertFalse(self.f.out.exists())
    def test_changed_receipt_after_stage_hold_without_overwrite(self):
        self.f.call();before=files(self.f.out);self.f.receipt.write_bytes(b'CHANGED');self.hold();self.assertEqual(files(self.f.out),before);self.assertEqual(self.f.compile_calls,1)
    def test_changed_source_after_stage_hold_without_overwrite(self):
        self.f.call();before=files(self.f.out);(self.f.source/'paper.tex').write_bytes(b'CHANGED');self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_entry_after_stage_hold_without_overwrite(self):
        self.f.call();before=files(self.f.out);self.f.entry['digest_week']='2026-W42';save(self.f.entry_path,self.f.entry);self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_ledger_after_stage_hold_without_overwrite(self):
        self.f.call();before=files(self.f.out);save(self.f.ledger,{'tree_root':str(self.f.root),'run_entities':[]});self.hold();self.assertEqual(files(self.f.out),before)
    def test_unrelated_ledger_refresh_pass_with_append_only_receipt(self):
        self.f.call();before=files(self.f.out);status_bytes=(self.f.out/'AUTO_STAGE_RESULT.json').read_bytes()
        doc=json.loads(self.f.ledger.read_text());doc['scanned_at_utc']='2026-10-07T01:00:00Z';doc['counts']={'CERTIFIED':999};doc['run_entities'].append({'id':'Run-140','status':'DEBT'});save(self.f.ledger,doc)
        result=self.f.call();self.assertEqual(result['state'],'ALREADY_STAGED_IDENTICAL_BYTES');self.assertEqual(self.f.compile_calls,1);self.assertEqual(files(self.f.out),before)
        receipt_path=Path(result['revalidation_receipt']['path']);self.assertFalse(receipt_path.is_relative_to(self.f.out));receipt=json.loads(receipt_path.read_text())
        self.assertEqual(receipt['current_ledger_binding']['sha256'],sha(self.f.ledger));self.assertNotEqual(receipt['historical_ledger_binding']['sha256'],sha(self.f.ledger));self.assertFalse(receipt['publication_enabled']);self.assertFalse(receipt['certificate_acceptance_changed']);self.assertEqual(receipt['source_reads'],'PARITY_ONLY_NOT_CERTIFICATION')
        self.assertEqual((self.f.out/'AUTO_STAGE_RESULT.json').read_bytes(),status_bytes);saved=receipt_path.read_bytes();self.f.call();self.assertEqual(receipt_path.read_bytes(),saved);self.assertEqual(len(list(receipt_path.parent.glob('*.json'))),1)
    def test_second_ordinary_refresh_creates_second_receipt_without_package_mutation(self):
        self.f.call();before=files(self.f.out)
        receipts=[]
        for time in ('01:00','02:00'):
            doc=json.loads(self.f.ledger.read_text());doc['scanned_at_utc']=time;save(self.f.ledger,doc);receipts.append(Path(self.f.call()['revalidation_receipt']['path']))
        self.assertNotEqual(receipts[0],receipts[1]);self.assertTrue(all(p.is_file()for p in receipts));self.assertEqual(files(self.f.out),before);self.assertEqual(self.f.compile_calls,1)
    def test_legacy_closed_status_refresh_preserves_original_without_fabricated_projection(self):
        self.f.call();p=self.f.out/'AUTO_STAGE_RESULT.json';status=json.loads(p.read_text());status.pop('target_projection');save(p,status);before=files(self.f.out)
        doc=json.loads(self.f.ledger.read_text());doc['scanned_at_utc']='new';save(self.f.ledger,doc);r=self.f.call();self.assertIn('revalidation_receipt',r);self.assertEqual(files(self.f.out),before);self.assertNotIn('target_projection',json.loads(p.read_text()))
    def test_duplicate_target_row_hold_after_refresh(self):
        self.f.call();before=files(self.f.out);doc=json.loads(self.f.ledger.read_text());doc['run_entities'].append(deepcopy(doc['run_entities'][0]));save(self.f.ledger,doc);self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_target_kind_status_path_or_validity_holds(self):
        self.f.call();before=files(self.f.out);original=self.f.ledger.read_bytes()
        for key,value in (('kind','SYNTHESIS'),('status','HAS_SORRY'),('certificate_valid',False),('path','science-engine/other'),('entity_type','FILE')):
            with self.subTest(key=key):
                self.f.ledger.write_bytes(original);self.f.change_row(key,value);self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_target_certificate_holds(self):
        self.f.call();before=files(self.f.out);other=self.f.certdir/'OTHER_CERTIFICATE.json';other.write_bytes(self.f.cert.read_bytes());self.f.change_row('certificate',str(other));self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_target_theorem_or_witness_inventory_holds(self):
        self.f.call();before=files(self.f.out);original=self.f.ledger.read_bytes()
        for key in ('certified_theorems','nonvacuity'):
            with self.subTest(key=key):self.f.ledger.write_bytes(original);self.f.change_row(key,[]);self.hold();self.assertEqual(files(self.f.out),before)
    def test_changed_target_semantic_artifact_binding_holds(self):
        self.f.call();before=files(self.f.out);self.f.change_row('certificate_artifacts',{'changed':{'sha256':'0'*64}});self.hold();self.assertEqual(files(self.f.out),before)
    def test_current_selector_changed_after_stage_holds(self):
        self.f.call();before=files(self.f.out);other=self.f.certdir/'OTHER_CERTIFICATE.json';other.write_bytes(self.f.cert.read_bytes());self.f.current=(other,{});self.hold();self.assertEqual(files(self.f.out),before)
    def test_current_selector_missing_holds(self):self.f.current=None;self.hold();self.assertFalse(self.f.out.exists())
    def test_inspection_input_contract_changed_holds(self):self.f.inspection['bindings'][0]['sha256']='0'*64;self.hold();self.assertFalse(self.f.out.exists())
    def test_fresh_generation_divergence_holds_despite_stale_match_ledger(self):
        self.f.parity['status']='MIRROR_DRIFT';self.f.parity['differences']=[{'path':'paper.tex','source_sha256':'0'*64,'mirror_sha256':'1'*64}];self.hold();self.assertFalse(self.f.out.exists())
    def test_generation_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:self.f.parity.update(status='MIRROR_DRIFT');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_generation_change_during_repeat_hold_without_overwrite(self):
        self.f.call();before=files(self.f.out)
        self.f.parity_hook=lambda:self.f.parity.update(status='MIRROR_DRIFT')if self.f.parity_calls>=4 else None
        self.hold();self.assertEqual(files(self.f.out),before);self.assertEqual(self.f.compile_calls,1)
    def test_selector_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:setattr(self.f,'current',None);self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_ledger_changes_while_revalidating_holds_no_receipt(self):
        self.f.call();before=files(self.f.out)
        self.f.inspection_hook=lambda:self.f.ledger.write_bytes(self.f.ledger.read_bytes()+b'\n') if self.f.inspection_calls>=4 else None
        self.hold();self.assertEqual(files(self.f.out),before);self.assertFalse((self.f.root/'RESEARCH_PIPELINE_v2/science_release_queue/revalidations').exists())
    def test_missing_historical_ledger_binding_holds(self):
        self.f.call();p=self.f.out/'AUTO_STAGE_RESULT.json';status=json.loads(p.read_text());status['input_bindings'].pop(str(self.f.ledger));save(p,status);self.hold()
    def test_historical_nonledger_binding_change_holds(self):
        self.f.call();p=self.f.out/'AUTO_STAGE_RESULT.json';status=json.loads(p.read_text());status['input_bindings'][str(self.f.receipt)]='0'*64;save(p,status);self.hold()
    def test_publication_is_still_disabled_after_refresh(self):
        self.f.call();doc=json.loads(self.f.ledger.read_text());doc['updated_at']='new';save(self.f.ledger,doc);result=self.f.call();self.assertFalse(result['publication_enabled']);self.assertEqual(result['zenodo_writes'],0);self.assertFalse(result['local_lean_execution']);self.assertIn('PENDING_INDEPENDENT',json.loads((self.f.out/'AUTO_STAGE_RESULT.json').read_text())['state'])
    def test_corrupt_staged_file_hold_without_overwrite(self):
        self.f.call();p=self.f.out/'paper.pdf';p.write_bytes(b'CORRUPTED');before=files(self.f.out);self.hold();self.assertEqual(files(self.f.out),before)
    def test_extra_staged_file_hold(self):self.f.call();(self.f.out/'untracked').write_bytes(b'EXTRA');self.hold()
    def test_deleted_staged_file_hold(self):self.f.call();(self.f.out/'paper.pdf').unlink();self.hold()
    def test_staged_symlink_hold(self):self.f.call();(self.f.out/'untracked').symlink_to(self.f.cert);self.hold()
    def test_status_publication_flag_cannot_authorize(self):
        self.f.call();p=self.f.out/'AUTO_STAGE_RESULT.json';v=json.loads(p.read_text());v['publication_enabled']=True;save(p,v);self.hold()
    def test_renderer_failure_is_immutable_hold(self):
        self.f.render_returncode=1;self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists());self.assertEqual(json.loads((self.f.out/'AUTO_STAGE_HOLD.json').read_text())['state'],'HOLD');before=files(self.f.out);self.hold();self.assertEqual(files(self.f.out),before);self.assertEqual(self.f.compile_calls,1)
    def test_foreign_lean_executable_forbidden(self):self.hold(renderer='/usr/bin/lean');self.assertFalse(self.f.out.exists());self.assertEqual(self.f.compile_calls,0)
    def test_foreign_python_executable_forbidden(self):self.hold(renderer='/usr/bin/python');self.assertFalse(self.f.out.exists());self.assertEqual(self.f.compile_calls,0)
    def test_same_renderer_basename_elsewhere_forbidden(self):self.hold(renderer='/private/tmp/tectonic');self.assertFalse(self.f.out.exists());self.assertEqual(self.f.compile_calls,0)
    def test_relative_renderer_basename_forbidden(self):self.hold(renderer='tectonic');self.assertFalse(self.f.out.exists());self.assertEqual(self.f.compile_calls,0)
    def test_source_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:(self.f.source/'paper.tex').write_bytes(b'CHANGED');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_entry_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:self.f.entry_path.write_bytes(self.f.entry_path.read_bytes()+b'\n');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_ledger_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:self.f.ledger.write_bytes(self.f.ledger.read_bytes()+b'\n');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_receipt_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:self.f.receipt.write_bytes(b'CHANGED');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_consumer_change_during_render_immutable_hold(self):
        self.f.render_hook=lambda:Path(self.f.consumers['inspection']['path']).write_bytes(b'CHANGED');self.hold();self.assertFalse((self.f.out/'AUTO_STAGE_RESULT.json').exists())
    def test_wrong_current_inspection_run_hold(self):self.f.inspection['run_id']='Run-140';self.hold();self.assertFalse(self.f.out.exists())
    def test_not_recorded_current_certificate_hold(self):self.f.inspection['recorded_certificate_current']=False;self.hold();self.assertFalse(self.f.out.exists())
    def test_wrong_current_inspection_hash_hold(self):self.f.inspection['sha256']='0'*64;self.hold();self.assertFalse(self.f.out.exists())
    def test_entry_id_traversal_hold(self):self.f.entry['entry_id']='../../escaped';save(self.f.entry_path,self.f.entry);self.hold();self.assertFalse(self.f.out.exists())
    def test_run_id_traversal_hold(self):self.f.entry['run_id']='../../escaped';save(self.f.entry_path,self.f.entry);self.hold();self.assertFalse(self.f.out.exists())
    def test_missing_certified_input_contract_hold(self):self.f.entry['certified_inputs']=[];save(self.f.entry_path,self.f.entry);self.hold();self.assertFalse(self.f.out.exists())
    def test_missing_consumer_contract_hold(self):self.f.entry['consumer_bindings']={};save(self.f.entry_path,self.f.entry);self.hold();self.assertFalse(self.f.out.exists())

class OutputGuardTests(unittest.TestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name).resolve()
    def tearDown(self):self.tmp.cleanup()
    def test_queue_attempt_allowed(self):self.assertEqual(m._staging_output(self.root,self.root/'RESEARCH_PIPELINE_v2/science_release_queue/staged/attempt/Run-141').name,'Run-141')
    def test_dated_phase7_reports_attempt_allowed(self):self.assertEqual(m._staging_output(self.root,self.root/'reports/verification-coverage/2026-10-06/phase-7-scope-v001/Run-141').name,'Run-141')
    def test_unclassified_reports_path_denied(self):
        with self.assertRaises(ValueError):m._staging_output(self.root,self.root/'reports/verification-coverage/Run-141')
    def test_canonical_sealed_dir_denied(self):
        d=self.root/'RESEARCH_PIPELINE_v2/lean_certificates/Run-141';d.mkdir(parents=True);(d/'sentinel').write_text('KEEP');before=files(d)
        with self.assertRaises(ValueError):m.complete_package(d,self.root)
        self.assertEqual(files(d),before)
    def test_canonical_finalized_dir_denied(self):
        d=self.root/'RESEARCH_PIPELINE_v2/finalized_runs/Run-141';d.mkdir(parents=True)
        with self.assertRaises(ValueError):m.complete_package(d,self.root)
        self.assertEqual(files(d),{})
    def test_canonical_source_dir_and_new_child_denied(self):
        d=self.root/q.PAPER_ROOT/'Run-141_synthetic';d.mkdir(parents=True)
        for out in (d,d/'new-attempt'):
            with self.assertRaises(ValueError):m.stage_run({},out,self.root,HERE,{})
        self.assertFalse((d/'new-attempt').exists())
    def test_origin_dir_denied(self):
        with self.assertRaises(ValueError):m._staging_output(self.root,self.root/'00_ORIGIN/proof/new-attempt')
    def test_symlink_output_denied(self):
        d=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/staged';d.mkdir(parents=True);link=d/'link';link.symlink_to(d,target_is_directory=True)
        with self.assertRaises(ValueError):m._staging_output(self.root,link/'Run-141')
    def test_existing_stage_run_output_not_overwritten(self):
        d=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/staged/attempt/Run-141';d.mkdir(parents=True);(d/'sentinel').write_text('KEEP');before=files(d)
        with self.assertRaises(FileExistsError):m.stage_run({},d,self.root,HERE,{})
        self.assertEqual(files(d),before)
    def test_complete_existing_generated_output_not_overwritten(self):
        d=self.root/'RESEARCH_PIPELINE_v2/science_release_queue/staged/attempt/Run-141';d.mkdir(parents=True);(d/'SCOPED_CLAIM_MAP.json').write_text('KEEP');before=files(d)
        with self.assertRaises(ValueError):m.complete_package(d,self.root)
        self.assertEqual(files(d),before)

class QueueStageTests(unittest.TestCase):
    def setUp(self):self.f=Fixture()
    def tearDown(self):self.f.close()
    def cli(self,stage,status='ENQUEUED_REPORT_ONLY'):
        argv=['science_release_queue.py','--run',self.f.run,'--root',str(self.f.root)]+(['--stage']if stage else [])
        result={'status':status,'entry':str(self.f.entry_path),'publication_enabled':False}
        with patch.object(sys,'argv',argv),patch.object(q,'require_canonical_cli_root',return_value=self.f.root),patch.object(q,'enqueue',return_value=result),patch.object(m,'stage_current_entry',return_value={'state':'SYNTHETIC_DRAFT','publication_enabled':False})as spy,contextlib.redirect_stdout(io.StringIO())as output:
            code=q.main();return code,json.loads(output.getvalue()),spy.call_count
    def test_stage_flag_calls_helper(self):code,result,n=self.cli(True);self.assertEqual(code,0);self.assertEqual(n,1);self.assertEqual(result['scope_package']['state'],'SYNTHETIC_DRAFT');self.assertFalse(result['publication_enabled'])
    def test_no_stage_flag_never_calls_helper(self):code,result,n=self.cli(False);self.assertEqual(code,0);self.assertEqual(n,0);self.assertNotIn('scope_package',result)
    def test_intake_hold_never_calls_helper(self):code,result,n=self.cli(True,'HOLD');self.assertEqual(code,1);self.assertEqual(n,0)
    def test_stage_failure_cli_hold_not_weaker_pass(self):
        with patch.object(sys,'argv',['science_release_queue.py','--run',self.f.run,'--stage']),patch.object(q,'require_canonical_cli_root',return_value=self.f.root),patch.object(q,'enqueue',return_value={'status':'ENQUEUED_REPORT_ONLY','entry':str(self.f.entry_path)}),patch.object(m,'stage_current_entry',side_effect=ValueError('SYNTHETIC STAGE FAILURE')),contextlib.redirect_stdout(io.StringIO())as output:
            code=q.main();self.assertEqual(code,1);r=json.loads(output.getvalue());self.assertEqual(r['status'],'HOLD');self.assertFalse(r['publication_enabled'])

if __name__=='__main__':
    print('REVIEWED_STAGE_MODULE_SHA256',sha(Path(m.__file__)))
    unittest.main(verbosity=2)
