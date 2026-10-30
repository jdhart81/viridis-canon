"""Closed source/stdlib fixtures; no Core import, certificate, child or network.

Only exact selected function ASTs are compiled into private fixture namespaces.
Dependency doubles below are negative/equivalence DATA, not scientific evidence.
"""
from pathlib import Path
import ast
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
import stat
import re
import tempfile
import unittest

REPO=Path(__file__).resolve().parents[2]
G=REPO/'00_lab_infrastructure/gates'
ORIGINAL=G/'corpus_ledger.py'
INDEXED=G/'report_only_ledger/corpus_ledger_indexed_report.py'
CYCLE=G/'report_only_ledger/run_flow_indexed_report_only.py'
OLD_SHA='497aa58f686c48389ef5b4d62e00fa2621cdf45eff45ace4d8e79202076e94cf'

def selected(raw,names,namespace):
    tree=ast.parse(raw)
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
    if {n.name for n in body}!=set(names):raise AssertionError('exact selected source functions')
    exec(compile(ast.Module(body=body,type_ignores=[]),'<closed source-only fixture>','exec'),namespace)
    return namespace

def index_function(raw=None):
    ns={'Path':Path}
    selected(raw or INDEXED.read_bytes(),['lexical_membership_index'],ns)
    return ns['lexical_membership_index']

def boundary_oracle(index):
    rows=[{'absolute_path':'/x/Run-116/a.lean','id':'first'},
          {'absolute_path':'/x/Run-1162/b.lean','id':'sibling'},
          {'absolute_path':'/x/Run-116','id':'equal'},
          {'absolute_path':'/x/Run-116/a.lean','id':'duplicate'},
          {'absolute_path':'/x/Run-116/../outside/c.lean','id':'lexical-parent'}]
    targets=[Path('/x/Run-116'),Path('/x/Run-1162'),Path('/x/Run-11'),Path('/x'),Path('/')]
    got=index(rows)
    for target in targets:
        expected=[r for r in rows if Path(r['absolute_path']).is_relative_to(target)]
        actual=got.get(target,[])
        if len(actual)!=len(expected)or any(a is not b for a,b in zip(actual,expected)):
            raise AssertionError('exact lexical boundary/order/repeated-object oracle')

class IndexedReportOnlyTests(unittest.TestCase):
    def test_original_source_and_only_membership_build_delta(self):
        old=ORIGINAL.read_bytes();self.assertEqual(hashlib.sha256(old).hexdigest(),OLD_SHA)
        oldf=next(n for n in ast.parse(old).body if isinstance(n,ast.FunctionDef)and n.name=='build')
        newf=next(n for n in ast.parse(INDEXED.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=='_indexed_build')
        newf.name='build'
        inserts=[n for n in newf.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='membership']
        self.assertEqual(len(inserts),1);newf.body.remove(inserts[0])
        newmembers=[n for n in ast.walk(newf)if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='members']
        oldmembers=[n for n in ast.walk(oldf)if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='members']
        self.assertEqual(len(newmembers),1);newmembers[0].value=oldmembers[0].value
        self.assertEqual(ast.dump(newf,include_attributes=False),ast.dump(oldf,include_attributes=False))
    def test_lexical_boundary_equal_parent_order_and_duplicates(self):
        boundary_oracle(index_function())
    def test_empty_and_repeated_same_object(self):
        fn=index_function();self.assertEqual(fn([]),{})
        row={'absolute_path':'/a/r/f'};got=fn([row,row]);self.assertEqual(len(got[Path('/a/r')]),2)
        self.assertIs(got[Path('/a/r')][0],row);self.assertIs(got[Path('/a/r')][1],row)
    def test_relative_path_anchor_and_dot_semantics(self):
        rows=[{'absolute_path':'a/./b/f'},{'absolute_path':'a/../outside/f'},{'absolute_path':'/a/b/f'}]
        fn=index_function();got=fn(rows)
        for target in map(Path,['a','a/b','a/..','/a','.', '/']):
            expected=[r for r in rows if Path(r['absolute_path']).is_relative_to(target)]
            actual=got.get(target,[])
            self.assertEqual(len(actual),len(expected));self.assertTrue(all(a is b for a,b in zip(actual,expected)))
    def test_original_build_object_classification_and_call_order_equivalence(self):
        with tempfile.TemporaryDirectory(prefix='closed-indexed-report-')as td:
            root=Path(td).resolve(strict=True);certroot=root/'cert';certroot.mkdir()
            papers=root/'science-engine/07_nightly_engine/compound research papers';papers.mkdir(parents=True)
            dirs=[papers/'Run-116_paper',papers/'Run-117_paper',papers/'Run-118_empty',papers/'Run-META-001_canon-synthesis']
            for d in dirs:d.mkdir()
            paths=[dirs[0]/'a.lean',dirs[1]/'candidate.lean',root/'unrelated'/'Run-1162_other'/'b.lean']
            for path in paths:path.parent.mkdir(parents=True,exist_ok=True);path.write_text('TEST ONLY')
            cert={'valid':True,'candidate_sha256':'candidate','run_id':'Run-117','path':str(certroot/'fixture.json'),'candidate_path':str(paths[1]),'sealed_paper_inputs':{},'certified_theorems':['fixture'],'nonvacuity':['fixture']}
            def run(indexed):
                calls=[]
                def scan(path):
                    calls.append(('scan',str(path)))
                    return {'sha256':'candidate'if path==paths[1]else'other','errors':[],'flags':[],'has_sorry':path==paths[0],'static_pass':True,'declared_axioms':[]}
                def inspect(path,tree):calls.append(('inspect',str(path)));return deepcopy(cert)
                def choose(tree,cr,callback):
                    calls.append(('select',str(cr)));self.assertEqual(callback(tree,'Run-117'),'fixture-current');return [certroot/'fixture.json']
                def discover(tree):calls.append(('discover',str(tree)));return list(paths),['fixture-discovery-error'],['fixture-excluded']
                def parity(tree,rel,gen):calls.append(('parity',str(rel)));return {'status':'MATCH','errors':[],'differences':[]}
                def flow(tree,row):calls.append(('flow',row['id']));return {'state':row['status'],'causes':[],'receipts':[]}
                def preserve(ledger,previous):calls.append(('preserve',previous['fixture']));ledger['fixture_preserved']=deepcopy(previous);return ledger
                ns={'Path':Path,'json':json,'re':re,'Counter':Counter,'GENERATION_ROOT':root/'gen','PRIORITY':('MIRROR_DRIFT','UNSOUND','HAS_SORRY','DEBT','NO_FORMALIZATION','CLEAN_UNCERTIFIED','CERTIFIED')}
                selected(ORIGINAL.read_bytes(),['partition_status','counts','run_id','file_status'],ns)
                ns.update(scan=scan,inspect_certificate=inspect,certificate_selection_paths=choose,pipeline_modules=lambda root:(type('Fixture',(),{'current_certificate':staticmethod(lambda tree,rid:'fixture-current')}),None),discover=discover,run_parity=parity,flow=flow,preserve_publication_registrations=preserve)
                if indexed:
                    ns['lexical_membership_index']=index_function();selected(INDEXED.read_bytes(),['_indexed_build'],ns);fn=ns['_indexed_build']
                else:selected(ORIGINAL.read_bytes(),['build'],ns);fn=ns['build']
                return fn(root,certroot,generation_root=root/'gen',previous_ledger={'fixture':'prior'}),calls
            expected,oldcalls=run(False);actual,newcalls=run(True)
            self.assertEqual(actual,expected);self.assertEqual(newcalls,oldcalls)
            self.assertEqual(sum(c==('scan',str(paths[1]))for c in newcalls),2,'valid candidate must be freshly rescanned, never cached')
            self.assertEqual(actual['errors'],['fixture-discovery-error'])
            self.assertEqual(actual['run_entities'][0]['underlying_status'],'HAS_SORRY')
            self.assertEqual(actual['run_entities'][1]['status'],'CERTIFIED')
    def test_report_only_rejects_forbidden_modes_before_profile_or_import(self):
        ns={'Path':Path};selected(CYCLE.read_bytes(),['cycle_report'],ns)
        def unsafe(*args):raise AssertionError('forbidden branch reached profile')
        ns['producer_evidence']=unsafe
        for kw in ({'enforce_new_artifacts':True},{'enforce_new_artifacts':0},{'intake_reviewed_nightly':True},{'public_readback':'fixture'}):
            with self.assertRaisesRegex(ValueError,'REPORT_ONLY'):ns['cycle_report']('/fixture','/fixture/checkpoint',**kw)
    def test_membership_mutants_are_rejected_by_same_causal_oracle(self):
        original=INDEXED.read_text();mutations={
            'M01_prefix_boundary':("for ancestor in (path,*path.parents):", "for ancestor in (path,*path.parents,Path(str(path).replace('Run-1162','Run-116')).parent):"),
            'M02_drop_repeats':("indexed.setdefault(ancestor,[]).append(entity)","indexed[ancestor]=[entity]"),
            'M03_reverse_order':("indexed.setdefault(ancestor,[]).append(entity)","indexed.setdefault(ancestor,[]).insert(0,entity)"),
            'M04_omit_equal_path':("for ancestor in (path,*path.parents):", "for ancestor in path.parents:"),
            'M05_copy_identity':("indexed.setdefault(ancestor,[]).append(entity)","indexed.setdefault(ancestor,[]).append(dict(entity))"),
        }
        boundary_oracle(index_function())
        for name,(before,after)in mutations.items():
            with self.subTest(mutant=name):
                self.assertEqual(original.count(before),1)
                mutant=index_function(original.replace(before,after).encode())
                with self.assertRaises(AssertionError):boundary_oracle(mutant)
                print('REPORT_ONLY_INDEX_MUTANT_ASSERTION_KILLED='+name,flush=True)
    def test_missing_producer_profile_fails_before_source_reads(self):
        ns={'Path':Path};selected(CYCLE.read_bytes(),['producer_evidence'],ns)
        with tempfile.TemporaryDirectory(prefix='negative-only-profile-')as td:
            root=Path(td).resolve(strict=True)
            with self.assertRaisesRegex(ValueError,'profile required'):ns['producer_evidence'](root,None,None)
    def test_duplicate_profile_keys_rejected_by_actual_bounded_fd_reader(self):
        ns={'Path':Path,'os':os,'stat':stat,'hashlib':hashlib,'json':json,'re':re}
        selected(INDEXED.read_bytes(),['checked_source'],ns)
        selected(CYCLE.read_bytes(),['producer_evidence'],ns)
        with tempfile.TemporaryDirectory(prefix='negative-only-profile-')as td:
            root=Path(td).resolve(strict=True);p=root/'negative.json';raw=b'{"standard":"x","standard":"y"}'
            p.write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'duplicate producer profile key'):
                ns['producer_evidence'](root,p,hashlib.sha256(raw).hexdigest())
    def test_no_scientific_output_or_original_producer_relabel(self):
        tree=ast.parse(CYCLE.read_bytes());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='producer_evidence')
        text=ast.unparse(fn)
        self.assertIn('executed_source_rows',text);self.assertIn('scientific_admission',text)
        self.assertNotIn('source_generator_sha256',text)
        source=INDEXED.read_text();self.assertNotIn('setattr(_ORIGINAL',source)
        self.assertNotIn('_ORIGINAL.build =',source)

if __name__=='__main__':unittest.main()
