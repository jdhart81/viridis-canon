"""Foundation limit/termination regressions: fake processes and transport only."""
import hashlib
import json
from pathlib import Path
import subprocess
from unittest.mock import patch
from test_comparator_timeout import TimeoutTests, client, DEPLOY
from test_comparator_diagnostics import issuer

PROFILE = DEPLOY / 'service-profile'

class FoundationTerminationTests(TimeoutTests):
    def test_fake_process_regressions(self):
        subprocess.run(['node','--test',str(PROFILE/'tests/resource-termination.test.mjs')],check=True,capture_output=True,text=True)

    def test_killed_result_cannot_verify_or_issue_even_with_kernel_markers(self):
        request=json.loads(self.request.read_text())
        for name in ['SEALED_paper.pdf','SEALED_paper.tex','SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json']:
            p=self.root/name;p.write_bytes(b'fixture only');request['input_sha256'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.request.write_text(json.dumps(request))
        script = """
import {withTerminationDiagnostics, DEFAULT_PROFILE} from 'MODULE';
const ctx={requestId:'fixture-only',profile:DEFAULT_PROFILE,records:[{phase:'compare-kernels',exitCode:null,signal:process.argv[1],guard_fired:false,reason:'signaled'}]};
console.log(JSON.stringify(withTerminationDiagnostics({type:'verification-ok',project:'viridis-lean-4.28',output:'MARKERS',theoremNames:['target','witness']},ctx)));
""".replace('MODULE',(PROFILE/'src/resource-profile.mjs').as_uri()).replace('MARKERS','\\n'.join(client.DUAL_KERNEL_MARKERS))
        for signal in ['SIGXCPU','SIGKILL']:
            terminal=json.loads(subprocess.check_output(['node','--input-type=module','-e',script,signal],text=True))
            self.assertEqual(terminal['type'],'verification-failed')
            # Return zero at the outer transport to prove the result gate itself rejects.
            receipt=client.verify(**self.kw,transport=lambda *args:(0,terminal))
            self.assertEqual(receipt['status'],'HOLD')
            cert=self.root/'certificate.json'
            with self.assertRaises(issuer.CertificateError):
                issuer.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=cert)
            self.assertFalse(cert.exists());self.output.unlink()

    def test_scientific_acceptance_and_issuer_hashes_unchanged(self):
        before=(Path(__file__).parent/'fixtures/comparator_client_f2d.py').read_bytes()
        after=(DEPLOY/'comparator_cloud_lean_verifier.py').read_bytes()
        extract=lambda s:s[s.index(b'def verify('):s.index(b'\ndef main(')]
        self.assertEqual(extract(before),extract(after))
        self.assertEqual(hashlib.sha256(extract(before)).digest(),hashlib.sha256(extract(after)).digest())
        self.assertEqual(hashlib.sha256(after).hexdigest(),'b745e90ad147a0d5bd6787e20049e9bbb49a694837172851c77958b271718202')
        self.assertEqual(hashlib.sha256((Path(__file__).parent/'fixtures/comparator_issuer_unchanged.py').read_bytes()).hexdigest(),'789cb903c972a9c10731360769ccff56055b3257de9491a75b92c0d549b5c438')

    def test_patch_scope_contains_no_script_toolchain_memory_or_acceptance_edit(self):
        patch=(PROFILE/'service.patch').read_text()
        changed=[line[6:] for line in patch.splitlines() if line.startswith('+++ b/')]
        self.assertEqual(changed,['server/src/exec.ts','server/src/worker.ts','server/src/shared.ts','server/src/resource-profile.mjs','server/src/app.ts'])
        self.assertNotIn('ulimit',patch)
        self.assertNotIn('MemoryMax',patch)
        for name in ['comparator.sh', 'compile.sh', 'collectThms.sh']:
            self.assertEqual((DEPLOY/'remote_service'/name).read_bytes(), (DEPLOY/'deployed_snapshots/F2h-20261003'/name).read_bytes())
        for name in ['resource-profile.mjs','resource-profile.d.mts','guarded-process.mjs','guarded-process.d.mts']:
            self.assertEqual((PROFILE/'src'/name).read_bytes(),(DEPLOY/'remote_service'/name).read_bytes())

    def test_forbidden_axioms_and_sealed_hash_drift_still_block_issuer(self):
        request=json.loads(self.request.read_text())
        for name in ['SEALED_paper.pdf','SEALED_paper.tex','SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json']:
            p=self.root/name;p.write_bytes(b'fixture only');request['input_sha256'][name]=hashlib.sha256(p.read_bytes()).hexdigest()
        self.request.write_text(json.dumps(request))
        receipt=client.verify(**self.kw,transport=self.fake_transport)
        receipt['contract']['permitted_axioms'].append('ForbiddenAxiom')
        self.output.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(issuer.CertificateError,'axiom'):
            issuer.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=self.root/'certificate.json')
        self.output.unlink();client.verify(**self.kw,transport=self.fake_transport)
        (self.root/'SEALED_paper.pdf').write_bytes(b'changed sealed input')
        with self.assertRaises(issuer.CertificateError):
            issuer.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=self.root/'certificate.json')
        self.assertFalse((self.root/'certificate.json').exists())

    def test_optional_diagnostics_do_not_change_scientific_success_checks(self):
        results=[]
        for extended in [False,True]:
            def transport(payload,*args):
                rc,r=self.fake_transport(payload,*args)
                if extended:r['terminationDiagnostics']={'standard':'VRS-COMPARATOR-TERMINATION-1',
                    'requestId':'fixture-only','profile':'nightly-default','records':[{'phase':'compare-kernels','exitCode':0,'signal':None,'guard_fired':False}]}
                return rc,r
            results.append(client.verify(**self.kw,transport=transport));self.output.unlink()
        for key in ['status','checks','contract','candidate','formal_statement','runtime_observation_assessment']:
            self.assertEqual(results[0].get(key),results[1].get(key))
        self.assertIn('terminationDiagnostics',results[1]['provider_response'])

    def test_wrapper_preserves_extension_but_still_rejects_other_request_or_cache(self):
        from test_comparator_wrapper import WrapperTests, JOB
        for mutation in [None,'other','cache']:
            w=WrapperTests();w.setUp();event=w.success()
            event['terminationDiagnostics']={'requestId':JOB,'profile':'foundation-run900-approved-v1',
                'records':[{'exitCode':0,'signal':None,'guard_fired':False}]}
            if mutation=='other':event['requestId']='00000000-0000-4000-8000-000000000002'
            if mutation=='cache':event['executionEvidence']['delivery']['mode']='CACHE_REUSE'
            w.polls=[event];rc,result=w.run_wrapper()
            self.assertEqual(rc,0 if mutation is None else 2)
            if mutation is None:self.assertEqual(result['terminationDiagnostics'],event['terminationDiagnostics'])
            w.assert_same_id_once()
