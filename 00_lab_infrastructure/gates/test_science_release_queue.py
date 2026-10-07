import copy
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import science_release_queue as queue
from certificate_selection import certificate_selection_paths

SOURCE = Path(__file__).parent / 'CURRENT_CERTIFICATE_CONSUMER_SOURCE.txt'
SOURCE_BINDING = json.loads((Path(__file__).parent / 'CURRENT_CERTIFICATE_CONSUMER_SOURCE.json').read_text())
if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_BINDING['sha256']:
    raise ValueError('immutable unchanged consumer test source changed')
# Execute only the four unchanged Python bookkeeping functions. No transport,
# local Lean, issuance or proof acceptance is executed by these selection tests.
source_tree = ast.parse(SOURCE.read_text())
required_functions = set(SOURCE_BINDING['executed_ast_nodes_in_tests'])
nodes = [node for node in source_tree.body if isinstance(node, ast.FunctionDef) and node.name in required_functions]
if {node.name for node in nodes} != required_functions:
    raise ValueError('unchanged consumer functions missing from source snapshot')
namespace = {'Path':Path,'hashlib':hashlib,'json':json,'Any':Any,'CERTIFIED_STATUS':'LEAN_ZERO_SORRY_CERTIFIED'}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), 'exec'), namespace)
UNCHANGED_CURRENT_CERTIFICATE = namespace['current_certificate']


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.identity = 'Run-188'
        self.relative = queue.PAPER_ROOT / 'Run-188_example'
        self.source = self.root / self.relative
        self.source.mkdir(parents=True)
        (self.source / 'paper.tex').write_text('exact source bytes\n')
        (self.source / 'paper.pdf').write_bytes(b'pdf')
        (self.source / 'DISPOSITION.json').write_text(json.dumps({'run_id':self.identity,'disposition':'METHODS_NOTE'}))
        self.store = self.root / 'RESEARCH_PIPELINE_v2/lean_certificates' / self.identity
        self.store.mkdir(parents=True)
        self.cert = {'status':'LEAN_ZERO_SORRY_CERTIFIED','run_id':self.identity,'issued_at_utc':'2026-10-06T05:14:00+00:00'}
        self.cpath = self.store / 'LEAN_ZERO_SORRY_CERTIFICATE.json'
        self.cpath.write_text(json.dumps(self.cert))
        bindings = []
        for name in ('candidate_proof','formal_statement','request','independent_cloud_receipt','sealed_paper_inputs.SEALED_paper.tex','sealed_paper_inputs.SEALED_paper.pdf'):
            path = self.store / name.replace('.', '_')
            path.write_text('bound bytes:' + name)
            bindings.append({'label':'bindings.'+name,'resolved_path':str(path),'sha256':queue.digest(path)})
        self.inspection = {'valid':True,'recorded_certificate_current':True,'run_id':self.identity,'path':str(self.cpath),
            'sha256':queue.digest(self.cpath),'candidate_sha256':bindings[0]['sha256'],'bindings':bindings}
        self.row = {'id':self.identity,'path':str(self.relative),'status':'CERTIFIED','certificate_valid':True,'certificate':str(self.cpath),
            'parity':{'status':'MATCH','mirror':str(self.source),'mirror_hashes':queue.full_directory_snapshot(self.root,self.source)}}
        self.ledger = {'tree_root':str(self.root),'run_entities':[self.row],'publication_entities':[]}

    def prepare(self, **kwargs):
        return queue.prepare_entry(kwargs.get('root',self.root),kwargs.get('identity',self.identity),kwargs.get('ledger',self.ledger),
            kwargs.get('current',(self.cpath,self.cert)),kwargs.get('inspection',self.inspection),{},kwargs.get('joins',{}))

    def fail(self, **kwargs):
        with self.assertRaises((ValueError,FileNotFoundError)):
            self.prepare(**kwargs)

    def test_methods_note_routes_to_certificate_week_digest(self):
        entry=self.prepare();self.assertEqual(entry['route'],'WEEKLY_METHODS_DIGEST');self.assertEqual(entry['digest_week'],'2026-W41');self.assertFalse(entry['publication_enabled'])

    def test_same_exact_entry_idempotent(self):
        entry=self.prepare();p=self.root/'queue'/f"{entry['entry_id']}.json"
        self.assertTrue(queue.write_immutable(p,entry));self.assertFalse(queue.write_immutable(p,entry))

    def test_different_certificate_same_run_has_different_key(self):
        first=self.prepare();self.cert['issued_at_utc']='2026-10-06T05:15:00+00:00';self.cpath.write_text(json.dumps(self.cert));self.inspection['sha256']=queue.digest(self.cpath)
        second=self.prepare();self.assertNotEqual(first['entry_id'],second['entry_id'])

    def test_existing_key_content_changed_must_fail(self):
        entry=self.prepare();p=self.root/'queue'/'entry.json';queue.write_immutable(p,entry);entry['candidate_sha256']='0'*64
        with self.assertRaises(ValueError):queue.write_immutable(p,entry)

    def test_absent_current_certificate_must_fail(self):self.fail(current=None)
    def test_inspection_hold_must_fail(self):self.inspection['valid']=False;self.fail()
    def test_noncurrent_variant_must_fail(self):self.inspection['recorded_certificate_current']=False;self.fail()
    def test_ledger_tree_drift_must_fail(self):self.ledger['tree_root']=str(self.root/'wrong');self.fail()
    def test_parity_hold_must_fail(self):self.row['parity']['status']='MIRROR_DRIFT';self.fail()
    def test_wrong_parity_directory_must_fail(self):self.row['parity']['mirror']=str(self.root/'other');self.fail()
    def test_duplicate_entity_must_fail(self):self.ledger['run_entities'].append(copy.deepcopy(self.row));self.fail()
    def test_source_path_override_must_fail(self):self.row['path']=str(self.root);self.fail()
    def test_one_byte_source_change_must_fail(self):(self.source/'paper.tex').write_text('exact source byte!\n');self.fail()
    def test_added_source_file_must_fail(self):(self.source/'extra.txt').write_text('extra');self.fail()
    def test_missing_source_file_must_fail(self):(self.source/'paper.pdf').unlink();self.fail()
    def test_source_symlink_must_fail(self):(self.source/'link').symlink_to(self.cpath);self.fail()
    def test_one_byte_bound_input_change_must_fail(self):Path(self.inspection['bindings'][0]['resolved_path']).write_text('changed');self.fail()
    def test_missing_bound_input_must_fail(self):Path(self.inspection['bindings'][0]['resolved_path']).unlink();self.fail()
    def test_certificate_hash_change_must_fail(self):self.cpath.write_text('changed');self.fail()
    def test_wrong_certificate_run_must_fail(self):self.cert['run_id']='Run-187';self.cpath.write_text(json.dumps(self.cert));self.inspection['sha256']=queue.digest(self.cpath);self.fail()
    def test_missing_sealed_input_contract_must_fail(self):self.inspection['bindings'].pop();self.fail()
    def test_wrong_cert_root_must_fail(self):other=self.root/'wrong';other.mkdir();path=other/self.cpath.name;path.write_bytes(self.cpath.read_bytes());self.inspection['path']=str(path);self.fail(current=(path,self.cert))
    def test_unknown_disposition_must_fail(self):(self.source/'DISPOSITION.json').write_text('{}');self.row['parity']['mirror_hashes']=queue.full_directory_snapshot(self.root,self.source);self.fail()
    def test_stale_disposition_requires_append_only_correction(self):(self.source/'DISPOSITION.json').write_text(json.dumps({'disposition':'METHODS_NOTE','formal_status':'FROZEN_CANDIDATE_UNCERTIFIED'}));self.row['parity']['mirror_hashes']=queue.full_directory_snapshot(self.root,self.source);self.assertTrue(self.prepare()['append_only_disposition_correction_needed'])
    def test_successor_ssot_discrepancy_recorded_not_forged(self):self.row.update(status='HAS_SORRY',certificate=None,certificate_valid=False);entry=self.prepare();self.assertTrue(entry['ssot_successor_reconciliation_needed']);self.assertEqual(entry['ssot_status_observed'],'HAS_SORRY')
    def test_missing_issue_time_must_fail(self):del self.cert['issued_at_utc'];self.cpath.write_text(json.dumps(self.cert));self.inspection['sha256']=queue.digest(self.cpath);self.fail()
    def test_known_published_methods_note_never_standalone(self):entry=self.prepare(joins={self.identity:['10.5281/zenodo.42']});self.assertEqual(entry['route'],'WEEKLY_METHODS_DIGEST');self.assertFalse(entry['duplicate_standalone_allowed'])
    def test_published_full_paper_requires_successor_review(self):(self.source/'DISPOSITION.json').write_text(json.dumps({'disposition':'FULL_PAPER'}));self.row['parity']['mirror_hashes']=queue.full_directory_snapshot(self.root,self.source);self.assertEqual(self.prepare(joins={self.identity:['10.5281/zenodo.42']})['route'],'SCOPED_SUCCESSOR_REVIEW')
    def test_unpublished_full_paper_routes_to_paper_review(self):(self.source/'DISPOSITION.json').write_text(json.dumps({'disposition':'FULL_PAPER'}));self.row['parity']['mirror_hashes']=queue.full_directory_snapshot(self.root,self.source);self.assertEqual(self.prepare()['route'],'STANDALONE_PAPER_REVIEW')
    def test_deposited_publication_does_not_require_ssot_registration(self):
        d=self.root/'_ZENODO_DEPOSITS'/'bundle';d.mkdir(parents=True);(d/'RELEASE_BINDING.json').write_text(json.dumps({'run_id':self.identity}));(d/'PUBLISHED_DOI.txt').write_text('10.5281/zenodo.42\n')
        self.assertEqual(queue.published_run_joins(self.root,self.ledger)[self.identity],['10.5281/zenodo.42'])
    def test_malformed_current_run_public_pointer_must_fail(self):
        d=self.root/'_ZENODO_DEPOSITS'/'bundle';d.mkdir(parents=True);(d/'RELEASE_BINDING.json').write_text(json.dumps({'run_id':self.identity}));(d/'PUBLISHED_DOI.txt').write_text('unknown')
        self.assertRaises(ValueError,queue.published_run_joins,self.root,self.ledger,self.identity)
    def test_unrelated_legacy_format_pointer_does_not_override_target_run(self):
        d=self.root/'_ZENODO_DEPOSITS'/'old';d.mkdir(parents=True);(d/'RELEASE_BINDING.json').write_text(json.dumps({'run_id':'Run-010'}));(d/'PUBLISHED_DOI.txt').write_text('historical descriptive pointer')
        self.assertEqual(queue.published_run_joins(self.root,self.ledger,self.identity),{})
    def test_enqueue_creates_only_report_entry_with_existing_consumer(self):
        ledger_path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_path.write_text(json.dumps(self.ledger))
        fake_track=type('T',(),{'current_certificate':lambda _,root,run:(self.cpath,self.cert)})();fake_inspector=type('I',(),{'inspect_certificate':lambda _,path,root:self.inspection})()
        with patch.object(queue,'load_existing_consumers',return_value={'proof_track':fake_track,'inspection':fake_inspector,'proof_track_binding':{},'inspection_binding':{}}):
            result=queue.enqueue(self.root,self.identity,ledger_path);self.assertEqual(result['status'],'ENQUEUED_REPORT_ONLY');self.assertFalse(result['publication_enabled']);self.assertEqual(result['production_writes'],0)
            result=queue.enqueue(self.root,self.identity,ledger_path);self.assertEqual(result['status'],'ALREADY_ENQUEUED_SAME_CERTIFICATE_AND_SOURCE_BYTES')
    def test_enqueue_failed_consumer_persists_hold_and_no_entry(self):
        ledger_path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_path.write_text(json.dumps(self.ledger))
        with patch.object(queue,'load_existing_consumers',side_effect=ValueError('consumer missing')):
            result=queue.enqueue(self.root,self.identity,ledger_path);self.assertEqual(result['status'],'HOLD');self.assertFalse(result['publication_enabled']);self.assertTrue(list((self.root/'RESEARCH_PIPELINE_v2/science_release_queue/holds').glob('*.json')));self.assertFalse((self.root/'RESEARCH_PIPELINE_v2/science_release_queue/entries').exists())
    def test_invalid_run_identity_cannot_escape_queue_or_create_hold_path(self):
        ledger_path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_path.write_text(json.dumps(self.ledger))
        self.assertRaises(ValueError,queue.enqueue,self.root,'../../escape',ledger_path)
        self.assertFalse((self.root/'RESEARCH_PIPELINE_v2/science_release_queue').exists())
    def test_production_cli_accepts_only_canonical_root(self):
        with patch.object(queue,'DEFAULT_ROOT',self.root):self.assertEqual(queue.require_canonical_cli_root(self.root),self.root)
    def test_production_cli_generation_root_must_fail(self):
        generation=self.root/'generation';generation.mkdir()
        with patch.object(queue,'DEFAULT_ROOT',self.root):self.assertRaises(ValueError,queue.require_canonical_cli_root,generation)
    def test_outside_tree_queue_must_fail(self):
        ledger_path=self.root/'RESEARCH_PIPELINE_v2/corpus_ledger.json';ledger_path.write_text(json.dumps(self.ledger))
        self.assertRaises(ValueError,queue.enqueue,self.root,self.identity,ledger_path,self.root.parent/'outside-queue')
    def test_existing_output_symlink_must_fail(self):p=self.root/'output';p.symlink_to(self.cpath);self.assertRaises(ValueError,queue.write_immutable,p,{'x':1})
    def test_output_parent_symlink_must_fail(self):p=self.root/'parent';p.symlink_to(self.store,target_is_directory=True);self.assertRaises(ValueError,queue.write_immutable,p/'x.json',{'x':1})
    def test_claude_review_exact_packet_pass(self):
        packet=self.root/'RELEASE_PACKET.md';packet.write_text('exact consolidated packet');review=self.root/'review.json';review.write_text(json.dumps({'status':'PASS','reviewer_system':'Claude','release_packet':{'path':str(packet),'sha256':queue.digest(packet)}}))
        self.assertTrue(queue.require_independent_packet_review(self.root,packet,review)['publication_gate_still_required'])
    def test_claude_review_changed_packet_must_fail(self):
        packet=self.root/'RELEASE_PACKET.md';packet.write_text('packet');review=self.root/'review.json';review.write_text(json.dumps({'status':'PASS','reviewer_system':'Claude','release_packet':{'path':str(packet),'sha256':queue.digest(packet)}}));packet.write_text('packet!');self.assertRaises(ValueError,queue.require_independent_packet_review,self.root,packet,review)
    def test_unreviewed_packet_must_fail(self):packet=self.root/'packet';packet.write_text('packet');review=self.root/'review';review.write_text('{}');self.assertRaises(ValueError,queue.require_independent_packet_review,self.root,packet,review)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(dir=Path(tempfile.gettempdir()).resolve());self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.store=self.root/'RESEARCH_PIPELINE_v2/lean_certificates';self.directory=self.store/'Run-187';self.directory.mkdir(parents=True)
        bindings={}
        for key in ('request','independent_cloud_receipt','formal_statement','candidate_proof'):
            p=self.directory/(key+'.txt');p.write_text(key);bindings[key]={'path':str(p),'sha256':queue.digest(p)}
        p=self.directory/'sealed.txt';p.write_text('sealed');bindings['sealed_paper_inputs']={'SEALED_paper.tex':{'path':str(p),'sha256':queue.digest(p)}}
        self.cert={'standard':'VRS-LEAN-ZERO-SORRY-CERTIFICATE-1','status':'LEAN_ZERO_SORRY_CERTIFIED','run_id':'Run-187','verification_standard':'VRS-COMPARATOR-DUAL-KERNEL-1','issued_at_utc':'2026-10-05T11:00:00Z','bindings':bindings}
        self.original=self.directory/'LEAN_ZERO_SORRY_CERTIFICATE.json';self.original.write_text(json.dumps(self.cert))
        self.consumer=UNCHANGED_CURRENT_CERTIFICATE

    def paths(self):return certificate_selection_paths(self.root,self.store,self.consumer)
    def test_old_valid_original_unchanged(self):self.assertEqual(self.paths(),[self.original])
    def test_valid_immutable_successor_selected(self):successor=self.directory/'LEAN_ZERO_SORRY_CERTIFICATE_REBIND.json';self.cert['issued_at_utc']='2026-10-05T17:00:00Z';successor.write_text(json.dumps(self.cert));self.assertEqual(self.paths(),[successor])
    def test_invalid_successor_does_not_launder_original(self):successor=self.directory/'LEAN_ZERO_SORRY_CERTIFICATE_REBIND.json';self.cert['issued_at_utc']='2026-10-05T17:00:00Z';self.cert['bindings']['candidate_proof']['sha256']='0'*64;successor.write_text(json.dumps(self.cert));self.assertEqual(self.paths(),[self.original])
    def test_one_byte_break_reverts_to_invalid_original_audit(self):Path(self.cert['bindings']['request']['path']).write_text('request!');self.assertEqual(self.paths(),[self.original]);self.assertIsNone(self.consumer(self.root,'Run-187'))
    def test_wrong_run_successor_not_selected(self):successor=self.directory/'LEAN_ZERO_SORRY_CERTIFICATE_REBIND.json';self.cert['run_id']='Run-188';successor.write_text(json.dumps(self.cert));self.assertEqual(self.paths(),[self.original])
    def test_current_consumer_outside_configured_store_must_fail(self):other=self.root/'other.json';other.write_text('{}');self.assertRaises(ValueError,certificate_selection_paths,self.root,self.store,lambda root,run:(other,{}))
    def test_custom_cert_root_preserves_originals_only_without_default_inheritance(self):custom=self.root/'overlays';d=custom/'Run-187';d.mkdir(parents=True);p=d/'LEAN_ZERO_SORRY_CERTIFICATE.json';p.write_text('{}');self.assertEqual(certificate_selection_paths(self.root,custom,lambda *_:self.fail('must not query default store')), [p])
    def test_outside_tree_cert_root_must_fail(self):self.assertRaises(ValueError,certificate_selection_paths,self.root,self.root.parent,self.consumer)
    def test_missing_store_must_fail(self):self.assertRaises(FileNotFoundError,certificate_selection_paths,self.root,self.root/'absent',self.consumer)


if __name__=='__main__':unittest.main(verbosity=2)
