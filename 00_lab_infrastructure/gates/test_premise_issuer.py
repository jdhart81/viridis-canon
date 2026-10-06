"""Approved issuer intake tests consume synthetic receipts, never submit proofs."""
import datetime
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

import test_comparator_timeout as timeout_fixtures
client,DEPLOY=timeout_fixtures.client,timeout_fixtures.DEPLOY
from test_premise_declaration import INDEPENDENT, CONDITIONAL, paper

spec=importlib.util.spec_from_file_location('approved_intake_issuer_under_test',DEPLOY/'issue_lean_zero_sorry_certificate.py')
issuer=importlib.util.module_from_spec(spec);spec.loader.exec_module(issuer)
previous=types.ModuleType('historical_issuer_test_only')
exec(compile((Path(__file__).parent/'fixtures/comparator_issuer_unchanged.py').read_text(),'historical_issuer_test_only','exec'),previous.__dict__)


class PremiseIssuerTests(unittest.TestCase):
    def setUp(self):
        timeout_fixtures.TimeoutTests.setUp(self)
        self.fake_transport=lambda *a:timeout_fixtures.TimeoutTests.fake_transport(self,*a)
        self.cert=self.root/'certificate.json'

    def envelope(self,source=INDEPENDENT,basis='INDEPENDENT',text=None):
        self.candidate.write_text(source+'\ntheorem witness : ∃ n : Nat, n > 0 := by\n  exact ⟨1, Nat.zero_lt_succ 0⟩\n')
        target='product_form_fixture' if 'theorem product_form_fixture' in source else 'independent_target'
        self.formal.write_text(client.align_challenge(self.candidate.read_text(),self.candidate.read_text(),[target,'witness'])[0])
        request=json.loads(self.request.read_text());request['expected_theorem_names']=[target,'witness']
        values={'SEALED_paper.pdf':b'%PDF-synthetic recorded fixture',
                'SEALED_paper.tex':paper(text or 'INDEPENDENT: model ordering.').encode(),
                'SEALED_CLAIM_INVENTORY.json':json.dumps({'claims':[],**({'foundation_basis':basis} if basis else {})}).encode(),
                'SEALED_RUN_MANIFEST.json':json.dumps({'source_run':'Run-900',**({'foundation_basis':basis} if basis else {})}).encode()}
        for name,data in values.items(): (self.root/name).write_bytes(data)
        request['input_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [self.candidate,self.formal]+[self.root/n for n in values]}
        request['statement_contract_sha256']=hashlib.sha256(self.formal.read_bytes()).hexdigest();self.request.write_text(json.dumps(request))
        client.verify(**self.kw,transport=self.fake_transport)

    def issue(self,required=False):
        return issuer.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=self.cert,require_premise_declaration=required)

    def test_enabled_new_run_includes_sealed_basis_and_premise_gate(self):
        self.envelope();result=self.issue(required=True)
        self.assertEqual(result['foundation_basis'],'INDEPENDENT')
        self.assertEqual(result['premise_declaration']['status'],'PASS')
        self.assertTrue(result['gates']['premise_declaration'])
        self.assertEqual(json.loads(self.cert.read_text()),result)

    def test_default_historical_certificate_output_bytes_identical(self):
        self.envelope(basis=None)
        class FixedClock(datetime.datetime):
            @classmethod
            def now(cls,tz=None):return cls(2026,10,4,tzinfo=datetime.timezone.utc)
        with patch.object(datetime,'datetime',FixedClock):
            old=previous.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=self.cert)
            before=self.cert.read_bytes();self.cert.unlink()
            current=self.issue();after=self.cert.read_bytes()
        self.assertEqual(old,current);self.assertEqual(before,after)
        self.assertNotIn('foundation_basis',current);self.assertNotIn('premise_declaration',current['gates'])

    def test_cutover_missing_fields_is_hold_without_certificate(self):
        self.envelope(basis=None)
        with self.assertRaisesRegex(issuer.CertificateError,'PREMISE_DECLARATION_MISSING_OR_UNKNOWN'):self.issue(required=True)
        self.assertFalse(self.cert.exists())

    def test_removed_pl_hold_even_when_synthetic_receipt_is_green(self):
        self.envelope(source=CONDITIONAL.replace('(PL : R_obs * K ≤ P) ',''),basis='CONDITIONAL_PL_PD',text='The product form is conditional on premises PL and PD.')
        with self.assertRaisesRegex(issuer.CertificateError,'PREMISE_DROPPED'):self.issue(required=True)
        self.assertFalse(self.cert.exists())

    def test_product_under_theorem_is_hold_without_certificate(self):
        self.envelope(source=CONDITIONAL,basis='THEOREM',text='THEOREM: the product form holds.')
        with self.assertRaisesRegex(issuer.CertificateError,'PREMISE_UNDERDECLARED'):self.issue(required=True)
        self.assertFalse(self.cert.exists())

    def test_sealed_byte_mismatch_retains_existing_rejection(self):
        self.envelope();p=self.root/'SEALED_RUN_MANIFEST.json';p.write_bytes(p.read_bytes()+b' ')
        with self.assertRaisesRegex(issuer.CertificateError,'sealed paper input byte binding failed'):self.issue(required=True)
        self.assertFalse(self.cert.exists())

    def test_kernel_rejection_and_axiom_allowlist_unchanged(self):
        self.envelope();cloud=json.loads(self.output.read_text());cloud['checks']['nanoda_kernel_accepted']=False
        self.output.write_text(json.dumps(cloud))
        with self.assertRaisesRegex(issuer.CertificateError,'nanoda_kernel_accepted'):self.issue(required=True)
        self.assertEqual(issuer.PERMITTED_AXIOMS,previous.PERMITTED_AXIOMS)
        self.assertEqual(issuer.COMPARATOR_CHECKS,previous.COMPARATOR_CHECKS)

    def test_exact_preexisting_acceptance_source_and_helpers_unchanged(self):
        old=(Path(__file__).parent/'fixtures/comparator_issuer_unchanged.py').read_text();new=(DEPLOY/'issue_lean_zero_sorry_certificate.py').read_text()
        start='    request_path = request_path.resolve()';end='    bindings: dict[str, Any] = {'
        original=old[old.index(start):old.index(end)]
        now=new[new.index(start):new.index('    premise_declaration = None')]
        self.assertEqual(original.encode(),now.encode())
        helper_start='def validate_comparator_witness_evidence(';helper_end='\ndef issue('
        self.assertEqual(old[old.index(helper_start):old.index(helper_end)].encode(),new[new.index(helper_start):new.index(helper_end)].encode())
        self.assertEqual(inspect.signature(issuer.issue).parameters['require_premise_declaration'].default,False)

    def test_cli_explicit_cutover_flag_and_default(self):
        import contextlib,io
        args=['issuer','--request',str(self.request),'--cloud-receipt',str(self.output),'--output',str(self.cert)]
        for flag,expected in [([],False),(['--require-premise-declaration'],True)]:
            with patch.object(sys,'argv',args+flag),patch.object(issuer,'issue',return_value={'status':'fixture'}) as called,contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(issuer.main(),0)
            self.assertEqual(called.call_args.kwargs['require_premise_declaration'],expected)


if __name__=='__main__':unittest.main()
