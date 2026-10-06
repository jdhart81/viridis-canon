"""Fresh isolated Python cannot borrow missing consumers from the Git checkout."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class PreparedRuntimeImportsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'canonical runtime'
        source = Path(__file__).parent/'production_snapshots/phase5-20261005-oai-cutover/after'
        shutil.copytree(source, self.root)
        # Existing pinned runtime support is not an installation target. Seed
        # this isolated fixture only from the exact reviewed protected bytes.
        import hashlib
        repo=Path(__file__).resolve().parents[2]
        baseline=json.loads((repo/'comparator-deploy/PROTECTED_IMPLEMENTATION_BASELINE.json').read_text())
        for name in ('engine3_align_challenge.py','job_observation_policy.py'):
            support=repo/'comparator-deploy'/name
            self.assertEqual(hashlib.sha256(support.read_bytes()).hexdigest(),baseline['unchanged_support_sha256'][name])
            shutil.copyfile(support,self.root/'RESEARCH_PIPELINE_v2'/name)

    def run_isolated(self, code):
        completed = subprocess.run([sys.executable, '-I', '-c', code, str(self.root)],
                                   capture_output=True, text=True, timeout=15)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_complete_consumer_closure_imports_only_prepared_target(self):
        result = self.run_isolated('''
import importlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
gates = root/'RESEARCH_PIPELINE_v2/verification_coverage_gates'
sys.path.insert(0, str(gates))
names = ['certificate_inspection','claim_binding','corpus_ledger','doi_audit','doi_triage',
         'mirror_parity','production_hooks','publication_gate','run_flow','static_pregate',
         'theorem_coverage','publication_binding','manuscript_structure','release_packet',
         'nightly_coverage','nightly_publication_intake','premise_declaration']
for name in names:
    module = importlib.import_module(name)
    assert pathlib.Path(module.__file__).resolve().is_relative_to(gates), name
from production_hooks import publication_report
observed = publication_report(root, root/'missing artifact', 'isolated', enforce_new_artifacts=True)
assert observed['status'] == 'HOLD' and observed['blocking'] is True
from nightly_publication_intake import prepare
intake = prepare(root, 'Run-186', root/'RESEARCH_PIPELINE_v2/finalized_runs/Run-186')
assert intake['status'] == 'HOLD'
assert observed['zenodo_writes'] is False and intake['zenodo_writes'] is False
print(json.dumps({'imported': names, 'gate': observed['status'], 'intake': intake['status'], 'network': False}))
''')
        self.assertEqual(len(result['imported']), 17)
        self.assertEqual(result['gate'], 'HOLD'); self.assertFalse(result['network'])

    def test_new_issuer_and_real_premise_intake_reuse_pinned_runtime_support(self):
        result = self.run_isolated(r'''
import importlib.util, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
pipeline=root/'RESEARCH_PIPELINE_v2';gates=pipeline/'verification_coverage_gates'
sys.path.insert(0,str(pipeline));sys.path.insert(0,str(gates))
spec=importlib.util.spec_from_file_location('isolated_issuer',pipeline/'issue_lean_zero_sorry_certificate.py')
issuer=importlib.util.module_from_spec(spec);spec.loader.exec_module(issuer)
assert pathlib.Path(issuer.__file__).resolve().is_relative_to(root)
from premise_declaration import evaluate
source='theorem target (n : Nat) : n ≤ n + 1 := by\n  exact Nat.le_succ n\n'
formal=issuer.align_challenge(source,source,['target'])[0]
checked=evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT'},formal_statement=formal,candidate=source,paper_text=r'\begin{abstract}INDEPENDENT: mathematical model ordering.\end{abstract}',theorem_names=['target'],required=True)
assert checked['status']=='PASS',checked
assert checked['certifies'] is False and checked['local_lean_execution'] is False
print(json.dumps({'premise':checked['status'],'issuer_imported':True,'proof_submitted':False,'certificate_issued':False}))
''')
        self.assertEqual(result['premise'],'PASS');self.assertTrue(result['issuer_imported'])
        self.assertFalse(result['certificate_issued']);self.assertFalse(result['proof_submitted'])

    def test_missing_or_changed_pinned_signature_parser_is_hold(self):
        path=self.root/'RESEARCH_PIPELINE_v2/engine3_align_challenge.py'
        path.write_bytes(path.read_bytes()+b' ')
        result=self.run_isolated(r'''
import json,pathlib,sys
root=pathlib.Path(sys.argv[1]);sys.path.insert(0,str(root/'RESEARCH_PIPELINE_v2/verification_coverage_gates'))
from premise_declaration import evaluate
checked=evaluate({'foundation_basis':'INDEPENDENT'},{'foundation_basis':'INDEPENDENT'},formal_statement='',candidate='',paper_text='',theorem_names=['target'],required=True)
assert checked['status']=='HOLD' and 'pinned signature parser' in str(checked['reasons']),checked
print(json.dumps({'status':checked['status'],'network':False}))
''')
        self.assertEqual(result['status'],'HOLD');self.assertFalse(result['network'])

    def test_missing_dependency_fails_closed_in_actual_prepared_publisher(self):
        (self.root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/publication_binding.py').unlink()
        result = self.run_isolated('''
import importlib.util, json, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
publisher_path = root/'_ZENODO_DEPOSITS/publish_dated_bundles.py'
spec = importlib.util.spec_from_file_location('isolated_publisher', publisher_path)
publisher = importlib.util.module_from_spec(spec); spec.loader.exec_module(publisher)
rejected = False
try:
    publisher.verification_coverage_report(root/'artifact', 'isolated', enforce_new_artifacts=True)
except publisher.PublisherError as exc:
    rejected = 'HOLD' in str(exc) and 'publication_binding' in str(exc)
assert rejected
print(json.dumps({'missing_dependency_hold': rejected, 'network': False}))
''')
        self.assertTrue(result['missing_dependency_hold']); self.assertFalse(result['network'])


if __name__ == '__main__': unittest.main()
