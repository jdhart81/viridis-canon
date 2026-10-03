"""F2e section 5 regressions: synthetic transports only, no Lean execution."""
import concurrent.futures
import datetime
import errno
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import types
from unittest.mock import patch

from test_comparator_timeout import TimeoutTests, client, DEPLOY

FIXTURES = Path(__file__).parent / 'fixtures'
old = types.ModuleType('pre_diagnostics_test_only')
exec(compile((FIXTURES/'comparator_client_f2d.py').read_text(), 'pre_diagnostics_test_only', 'exec'),old.__dict__)
issuer = types.ModuleType('unchanged_issuer_test_only')
exec(compile((FIXTURES/'comparator_issuer_unchanged.py').read_text(),'unchanged_issuer_test_only','exec'),issuer.__dict__)


class DiagnosticsTests(TimeoutTests):
    def run_transport(self, stdout=b'', stderr=b'', rc=0, error=None, root=None):
        token=client._DIAGNOSTICS_DIR.set(root or self.root)
        try:
            with patch.object(client.subprocess,'run',side_effect=error,
                              return_value=types.SimpleNamespace(stdout=stdout,stderr=stderr,returncode=rc)):
                return client.ssh_transport({},'fixture.invalid',self.key,1200)
        finally:
            client._DIAGNOSTICS_DIR.reset(token)

    def manifests(self):
        return [json.loads(p.read_text()) for p in self.root.glob('transport-diagnostics/*/manifest.json')]

    def test_acceptance_function_source_bytes_unchanged(self):
        new=(DEPLOY/'comparator_cloud_lean_verifier.py').read_text()
        previous=(FIXTURES/'comparator_client_f2d.py').read_text()
        extract=lambda s:s[s.index('def verify('):s.index('\ndef main(')]
        self.assertEqual(extract(new).encode(),extract(previous).encode())
        self.assertEqual(hashlib.sha256(extract(new).encode()).digest(),hashlib.sha256(extract(previous).encode()).digest())
        self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),'04b51c869205a66c452241bffce76945c2b735cf90cae15c645fdbadb2f7a606')
        self.assertEqual(hashlib.sha256((FIXTURES/'comparator_issuer_unchanged.py').read_bytes()).hexdigest(),'789cb903c972a9c10731360769ccff56055b3257de9491a75b92c0d549b5c438')

    def test_full_success_receipt_and_unchanged_issuer_bytes_identical(self):
        request=json.loads(self.request.read_text())
        for name in ['SEALED_paper.pdf','SEALED_paper.tex','SEALED_CLAIM_INVENTORY.json','SEALED_RUN_MANIFEST.json']:
            f=self.root/name;f.write_bytes(b'test-only sealed input')
            request['input_sha256'][name]=hashlib.sha256(f.read_bytes()).hexdigest()
        self.request.write_text(json.dumps(request))
        class FixedClock(datetime.datetime):
            @classmethod
            def now(cls,tz=None): return cls(2026,10,3,tzinfo=datetime.timezone.utc)
        cert=self.root/'certificate.json';receipt_bytes=[];cert_bytes=[]
        with patch.object(datetime,'datetime',FixedClock):
            for module in [old,client]:
                module.verify(**self.kw,transport=self.fake_transport)
                receipt_bytes.append(self.output.read_bytes())
                issuer.issue(request_path=self.request,cloud_receipt_path=self.output,output_path=cert)
                cert_bytes.append(cert.read_bytes());cert.unlink();self.output.unlink()
        self.assertEqual(receipt_bytes[0],receipt_bytes[1]);self.assertEqual(cert_bytes[0],cert_bytes[1])
        self.assertFalse((self.root/'transport-diagnostics').exists())

    def test_rejection_decisions_identical(self):
        for case in ['verification-failed','missing-marker','missing-export','wrong-project','invalid-observation','source-hash','forbidden']:
            with self.subTest(case=case):
                request_bytes=self.request.read_bytes();candidate_bytes=self.candidate.read_bytes()
                def transport(payload,host,key,timeout):
                    rc,res=self.fake_transport(payload,host,key,timeout)
                    if case=='verification-failed':res['type']='verification-failed';rc=2
                    if case=='missing-marker':res['output']='Your solution is okay!'
                    if case=='missing-export':res['theoremNames']=[]
                    if case=='wrong-project':res['project']='wrong'
                    if case=='invalid-observation':res['executionEvidence']={}
                    return rc,res
                if case=='source-hash':self.candidate.write_bytes(candidate_bytes+b'\n')
                if case=='forbidden':
                    self.candidate.write_bytes(candidate_bytes+b'\nexample : True := by sorry\n')
                    req=json.loads(self.request.read_text());req['input_sha256'][self.candidate.name]=hashlib.sha256(self.candidate.read_bytes()).hexdigest();self.request.write_text(json.dumps(req))
                outcomes=[]
                for module in [old,client]:
                    try:
                        r=module.verify(**self.kw,transport=transport);r.pop('verified_at_utc');outcomes.append(r)
                    except module.VerificationError as e:outcomes.append(str(e))
                    if self.output.exists():self.output.unlink()
                self.assertEqual(outcomes[0],outcomes[1])
                self.request.write_bytes(request_bytes);self.candidate.write_bytes(candidate_bytes)

    def test_invalid_raw_fixtures_are_captured_and_rejected(self):
        for raw in [b'',b'progress\n{}',b'warning\n{}',b'{"partial":',b'\xff',b'[]']:
            with self.subTest(raw=raw):
                with self.assertRaises((client.VerificationError,UnicodeDecodeError)):
                    self.run_transport(raw,b'fixture diagnostic stderr')
                paths=list(self.root.glob('transport-diagnostics/*/stdout.bin'))
                self.assertTrue(any(p.read_bytes()==raw for p in paths))
        self.assertFalse(self.output.exists())

    def test_nonzero_and_signal_exit_retained(self):
        for rc in [2,255,-9]:
            result=self.run_transport(b'{}',b'fixture error',rc=rc)
            self.assertEqual(result,(rc,{}))
        ms=self.manifests();self.assertEqual({m['returncode'] for m in ms},{2,255,-9})
        self.assertEqual(next(m for m in ms if m['returncode']==-9)['signal'],9)

    def test_partial_timeout_exact_bytes_and_allowance(self):
        error=subprocess.TimeoutExpired('test-only',1260,output=b'partial\r\n',stderr=b'pending')
        with self.assertRaisesRegex(client.VerificationError,'TimeoutExpired'):
            self.run_transport(error=error)
        m=self.manifests()[0];self.assertFalse(m['capture_complete']);self.assertIsNone(m['returncode'])
        self.assertEqual(m['ssh_wall_clock_seconds'],1260);self.assertEqual(m['streams']['stdout']['captured_sha256'],hashlib.sha256(b'partial\r\n').hexdigest())
        self.assertFalse(self.output.exists())

    def test_sizes_caps_hashes_and_modes(self):
        for size in [0,client.DIAGNOSTIC_CAP,client.DIAGNOSTIC_CAP+1]:
            raw=b'x'*size
            with self.assertRaises(client.VerificationError):self.run_transport(raw,raw)
        for p in self.root.glob('transport-diagnostics/*/manifest.json'):
            m=json.loads(p.read_text())
            self.assertEqual(stat.S_IMODE(p.parent.stat().st_mode),0o700)
            for label,v in m['streams'].items():
                f=p.parent/v['filename'];raw=f.read_bytes();self.assertEqual(len(raw),min(v['captured_length'],client.DIAGNOSTIC_CAP))
                self.assertEqual(v['captured_sha256'],hashlib.sha256(b'x'*v['captured_length']).hexdigest());self.assertEqual(v['retained_sha256'],hashlib.sha256(raw).hexdigest())
                self.assertEqual(v['truncated'],v['captured_length']>client.DIAGNOSTIC_CAP)
                self.assertEqual(stat.S_IMODE(f.stat().st_mode),0o600)
            self.assertEqual(stat.S_IMODE(p.stat().st_mode),0o600)
        self.assertEqual(stat.S_IMODE((self.root/'transport-diagnostics').stat().st_mode),0o700)

    def test_spawn_failure_streams_are_unavailable(self):
        with self.assertRaisesRegex(client.VerificationError,'FileNotFoundError'):self.run_transport(error=FileNotFoundError('fixture missing binary'))
        m=self.manifests()[0];self.assertIsNone(m['returncode']);self.assertFalse(m['capture_complete'])
        self.assertEqual(m['streams'],{'stdout':{'available':False},'stderr':{'available':False}})

    def test_symlinks_traversal_and_insecure_modes_rejected(self):
        token=client._DIAGNOSTICS_DIR.set(self.root/'..'/'escape')
        try:
            with self.assertRaisesRegex(OSError,'traversal'):
                client._persist_transport_diagnostics(b'',b'',started='test',elapsed=0,timeout=300)
        finally:client._DIAGNOSTICS_DIR.reset(token)
        link=self.root/'transport-diagnostics';link.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(client.VerificationError):self.run_transport(b'bad')
        self.assertEqual(list(self.root.glob('*/manifest.json')),[]);link.unlink();link.mkdir(mode=0o755)
        with self.assertRaises(client.VerificationError):self.run_transport(b'bad')
        self.assertEqual(list(link.iterdir()),[])

    def test_logging_failure_does_not_mask_failure_or_nonzero(self):
        for e in [PermissionError('fixture'),OSError(errno.ENOSPC,'fixture disk full')]:
            with patch.object(client,'_persist_transport_diagnostics',side_effect=e):
                with self.assertRaisesRegex(client.VerificationError,'non-JSON'):self.run_transport(b'bad')
                self.assertEqual(self.run_transport(b'{}',rc=2),(2,{}))
        self.assertFalse(self.output.exists())

    def test_closed_diagnostic_stderr_cannot_mask_failure(self):
        with patch.object(client,'_persist_transport_diagnostics',side_effect=PermissionError('fixture')), patch.object(client.sys,'stderr',types.SimpleNamespace(write=lambda *args: (_ for _ in ()).throw(OSError('closed')))):
            with self.assertRaisesRegex(client.VerificationError,'non-JSON'):
                self.run_transport(b'bad')

    def test_collision_and_concurrent_immutable_isolation(self):
        with self.assertRaises(client.VerificationError):self.run_transport(b'first')
        before={str(p):p.read_bytes() for p in self.root.glob('transport-diagnostics/*/*')}
        fixed=types.SimpleNamespace(hex='collision')
        with patch.object(client.uuid,'uuid4',return_value=fixed):
            with self.assertRaises(client.VerificationError):self.run_transport(b'second')
            with self.assertRaises(client.VerificationError):self.run_transport(b'third')
        for p,data in before.items():self.assertEqual(Path(p).read_bytes(),data)
        self.assertEqual((self.root/'transport-diagnostics/collision/stdout.bin').read_bytes(),b'second')
        def write(index):
            token=client._DIAGNOSTICS_DIR.set(self.root)
            try:client._persist_transport_diagnostics(str(index).encode(),b'',started='fixture',elapsed=0,timeout=300)
            finally:client._DIAGNOSTICS_DIR.reset(token)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(write,range(8)))
        self.assertEqual(len(self.manifests()),10)

    def test_no_stdin_key_or_environment_retention_and_public_exclusion(self):
        self.key.write_text('SENTINEL_PRIVATE_KEY')
        with patch.dict(os.environ,{'PRIVATE_TOKEN':'SENTINEL_ENV_SECRET'}):
            token=client._DIAGNOSTICS_DIR.set(self.root)
            try:
                with patch.object(client.subprocess,'run',return_value=types.SimpleNamespace(stdout=b'bad',stderr=b'fixture',returncode=2)):
                    with self.assertRaises(client.VerificationError):client.ssh_transport({'secret':'SENTINEL_STDIN'},'fixture.invalid',self.key,300)
            finally:client._DIAGNOSTICS_DIR.reset(token)
        raw=b''.join(p.read_bytes() for p in self.root.glob('transport-diagnostics/*/*'))
        for secret in [b'SENTINEL_PRIVATE_KEY',b'SENTINEL_ENV_SECRET',b'SENTINEL_STDIN']:self.assertNotIn(secret,raw)
        repo=DEPLOY.parent
        r=subprocess.run(['git','check-ignore','--no-index','transport-diagnostics/fixture/stdout.bin'],cwd=repo,capture_output=True)
        self.assertEqual(r.returncode,0)
        self.assertFalse(json.loads(self.manifests()[0] and next(self.root.glob('transport-diagnostics/*/manifest.json')).read_text())['receipt_evidence'])

    def test_decoding_matches_prechange_text_mode(self):
        for raw in [b'{"value":"line\\r\\n"}\r\n',b'{}\r',b'{}\r\n']:
            self.assertEqual(client._text_mode_decode(raw,'utf-8'),raw.decode('utf-8').replace('\r\n','\n').replace('\r','\n'))
