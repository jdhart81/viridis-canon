"""Client waiting regressions; fake transport only, no Lean or credentials."""
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).resolve().parents[2] / 'comparator-deploy'
# Imports resolve only the byte-identical reviewed client dependencies.
sys.path.insert(0, str(DEPLOY))
spec = importlib.util.spec_from_file_location('timeout_client_under_test', DEPLOY / 'comparator_cloud_lean_verifier.py')
client = importlib.util.module_from_spec(spec)
spec.loader.exec_module(client)


class TimeoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.key = self.root / 'fake-test-key'
        self.key.write_text('not a credential')
        self.candidate = self.root / 'candidate.lean'
        self.candidate.write_text('theorem target (n : Nat) : n + 0 = n := by\n  simp\n\ntheorem witness : ∃ n : Nat, n > 0 := by\n  exact ⟨1, Nat.zero_lt_succ 0⟩\n')
        self.formal = self.root / 'statement.lean'
        source = self.candidate.read_text()
        challenge, _ = client.align_challenge(source, source, ['target', 'witness'])
        self.formal.write_text(challenge)
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.request = self.root / 'request.json'
        self.request.write_text(json.dumps({'request_kind':'LEAN_PROOF', 'toolchain':'leanprover/lean4:v4.28.0', 'mathlib_rev':'8f9d9cff6bd728b17a24e163c9402775d9e6a365', 'input_sha256':{self.candidate.name:sha(self.candidate), self.formal.name:sha(self.formal)}, 'statement_contract_sha256':sha(self.formal), 'expected_theorem_names':['target','witness'], 'nonvacuity_obligations':['witness'], 'source_run':'Run-900'}))
        self.output = self.root / 'receipt.json'
        self.kw = dict(request_path=self.request, formal_statement_path=self.formal, candidate_path=self.candidate, output_path=self.output, key=self.key)
        self.calls = []

    def fake_transport(self, payload, host, key, timeout):
        self.calls.append((payload, timeout))
        return 0, {'type':'verification-ok','project':'viridis-lean-4.28','theoremNames':payload['theoremNames'],'output':'\n'.join(client.DUAL_KERNEL_MARKERS),'requestId':'test-only'}

    def test_1800_accepted_and_forwarded(self):
        receipt = client.verify(**self.kw, timeout=1800, transport=self.fake_transport)
        self.assertEqual(self.calls[-1][1], 1800)
        self.assertEqual(receipt['status'], 'VERIFIED')

    def test_1801_rejected_before_transport(self):
        with self.assertRaisesRegex(client.VerificationError, 'timeout must be between 1 and 1800 seconds'):
            client.verify(**self.kw, timeout=1801, transport=self.fake_transport)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.output.exists())

    def test_default_unchanged_in_function_and_cli(self):
        self.assertEqual(inspect.signature(client.verify).parameters['timeout'].default, 300)
        client.verify(**self.kw, transport=self.fake_transport)
        self.assertEqual(self.calls[-1][1], 300)
        args = ['client','--request',str(self.request),'--formal-statement',str(self.formal),'--candidate',str(self.candidate),'--output',str(self.output)]
        with patch.object(sys,'argv',args), patch.object(client,'verify',return_value={'status':'VERIFIED'}) as verify, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(client.main(), 0)
        self.assertEqual(verify.call_args.kwargs['timeout'],300)

    def test_ssh_wall_clock_is_timeout_plus_60(self):
        with patch.object(client.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=b'{}',stderr=b'')) as run:
            client.ssh_transport({}, 'test.invalid', self.key, 1800)
        self.assertEqual(run.call_args.kwargs['timeout'],1860)

    def test_receipts_identical_to_prechange_client_and_extended_wait(self):
        # Reconstruct the exact previously protected source solely in this test.
        new = (DEPLOY/'comparator_cloud_lean_verifier.py').read_text()
        old = (Path(__file__).parent/'fixtures/comparator_client_f2d.py').read_text()
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),'04b51c869205a66c452241bffce76945c2b735cf90cae15c645fdbadb2f7a606')
        previous = types.ModuleType('prechange_test_only')
        exec(compile(old,'prechange_test_only','exec'),previous.__dict__)
        before = previous.verify(**self.kw,transport=self.fake_transport)
        self.output.unlink()
        after = client.verify(**self.kw,timeout=1800,transport=self.fake_transport)
        # Actual recording time is the only variable; no schema additions permitted.
        before.pop('verified_at_utc');after.pop('verified_at_utc')
        self.assertEqual(before,after)
        self.assertEqual(self.calls[0][0],self.calls[1][0])
        self.assertEqual([x[1] for x in self.calls],[300,1800])

    def test_protected_baseline_and_unchanged_imports(self):
        baseline=json.loads((DEPLOY/'PROTECTED_IMPLEMENTATION_BASELINE.json').read_text())
        for name in ['comparator_cloud_lean_verifier.py','engine3_align_challenge.py']:
            self.assertEqual(hashlib.sha256((DEPLOY/name).read_bytes()).hexdigest(), baseline['protected_implementation_sha256'][name])
        for name,sha in baseline['unchanged_support_sha256'].items():
            self.assertEqual(hashlib.sha256((DEPLOY/name).read_bytes()).hexdigest(),sha)


if __name__ == '__main__':
    unittest.main()
