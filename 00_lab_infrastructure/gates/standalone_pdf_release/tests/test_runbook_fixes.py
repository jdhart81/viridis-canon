"""Runbook F1/F2/B6 boundary tests with synthetic inputs and no live network."""
import contextlib
import hashlib
from io import StringIO
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import test_dated_exact_uploads as dated
import test_digest_guard_security as security
import rehearsal

P = dated.publisher
ROOT = Path(__file__).resolve().parents[1]


class RehearsalTests(unittest.TestCase):
    def test_environment_override_holds_before_network(self):
        with mock.patch.dict(os.environ, VIRIDIS_ZENODO_API_BASE='https://sandbox.zenodo.org/api'), mock.patch.object(P, 'api_call') as call:
            with self.assertRaises(rehearsal.RehearsalHold):
                P.publish_bundle(Path('missing'), 'dummy', enforce_new_artifacts=True)
        call.assert_not_called()

    def test_foreign_doi_holds_before_any_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);bundle=dated.DatedExactUploadsTests().make_bundle(root)
            (bundle/'PUBLISHED_DOI.txt').write_text('10.5072/zenodo.1')
            with mock.patch.object(P,'api_call') as call:
                with self.assertRaises(P.PublisherError):P.publish_bundle(bundle,'dummy',enforce_new_artifacts=True)
            call.assert_not_called()
            self.assertFalse((root/'rehearsals').exists())

    def test_publish_action_url_raises_during_rehearsal(self):
        with self.assertRaises(rehearsal.RehearsalHold):rehearsal.publish_action_url(123,rehearse=True)

    def test_rehearsal_zero_publish_bundle_unchanged_and_draft_deleted(self):
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temp):
            root=Path(temp);bundle=dated.DatedExactUploadsTests().make_bundle(root)
            before=rehearsal.tree_hashes(bundle);files={};calls=[];metadata={};deleted=False
            def api(credential,method,url,data=None,content_type=None,**kw):
                nonlocal deleted,metadata
                calls.append((method,url))
                if url.endswith('/actions/publish'):self.fail('publish reached in rehearsal')
                if method=='POST':return {'id':123,'links':{'bucket':'https://zenodo.org/api/files/bucket'}}
                if method=='DELETE':deleted=True;return {}
                if method=='GET' and deleted:
                    kw.get('not_found_status',[]).append(404)
                    return None
                if method=='PUT' and '/api/files/'in url:
                    name=url.rsplit('/',1)[1];files[name]=data;return {'checksum':hashlib.md5(data).hexdigest()}
                if method=='PUT':metadata=json.loads(data)['metadata'];return {}
                if url.endswith('/files'):return [{'filename':name,'checksum':hashlib.md5(raw).hexdigest(),'filesize':len(raw)}for name,raw in files.items()]
                return {'id':123,'metadata':metadata,'files':[]}
            with mock.patch.object(P,'api_call',side_effect=api),mock.patch.object(P,'verification_coverage_report'):
                receipt=P.rehearse_bundle(bundle,'dummy')
            self.assertEqual(receipt['state'],'REHEARSED_DRAFT_DELETED')
            self.assertTrue(deleted);self.assertEqual(before,rehearsal.tree_hashes(bundle))
            self.assertFalse(any(url.endswith('/actions/publish')for method,url in calls))
            self.assertFalse((bundle/'PUBLISHED_DOI.txt').exists())
            self.assertEqual(len(list((root/'rehearsals').rglob('REHEARSAL.json'))),1)

    def test_current_lockstep_refuses_rehearsal_before_any_action(self):
        spec=importlib.util.spec_from_file_location('_runbook_lockstep',ROOT/'weekend_canon_lockstep.py')
        module=importlib.util.module_from_spec(spec);import sys;sys.modules[spec.name]=module;spec.loader.exec_module(module)
        with mock.patch.object(module,'discover_bundles') as discover:
            with self.assertRaisesRegex(module.LockstepError,'rehearsal'):
                module.main(['--date','2026-10-17','--go','--','publisher','--rehearse'])
        discover.assert_not_called()

    def test_active_and_runtime_gate_bytes_equal(self):
        self.assertEqual((ROOT/'manuscript_pdf_gate.py').read_bytes(),(ROOT/'runtime/manuscript_pdf_gate.py').read_bytes())


class GuardRepreflightTests(security.DigestGuardSecurityTests):
    def test_package_mutation_after_controller_load_blocks_execute(self):
        source="from pathlib import Path\nPath("+repr(str(self.package/'Run-167-Paper.pdf'))+").write_bytes(b'%PDF-mutated')\ndef execute(*args):\n    return {'published': True, 'record_id': '123', 'doi': '10.5281/zenodo.123'}\n"
        self.configure(source)
        with mock.patch.object(security.publisher,'token',return_value=security.DUMMY_TOKEN), mock.patch.object(security.gate,'public_record',return_value={'id':123,'doi':'10.5281/zenodo.123'}), mock.patch.object(security.gate,'require_public',return_value={}):
            with self.assertRaises(security.gate.ManuscriptPDFHold):security.guard.dispatch(self.config,self.digest,self.output)
        self.assertEqual(list(self.output.iterdir()),[])

    def test_unadapted_w42_controller_holds_before_loading_credential(self):
        with mock.patch.dict(os.environ, VIRIDIS_ENGINE_ROOT=str(self.root)), mock.patch.object(security.publisher, 'token') as token:
            with self.assertRaises(security.gate.ManuscriptPDFHold):
                security.guard.dispatch(self.config, self.digest, self.root/'rehearsals/test', rehearse=True)
        token.assert_not_called()

    def test_credential_free_gate_hold_echoes_reason(self):
        (self.package/'Run-167-Paper.pdf').unlink();out=StringIO();err=StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),mock.patch.object(security.publisher,'token') as token:
            code=security.guard.main(['--config',str(self.config),'--expected-config-sha256',self.digest])
        self.assertEqual(code,1);token.assert_not_called();self.assertIn('regular manuscript/reproduction file required',err.getvalue())

    def test_credential_free_dispatch_hash_hold_echoes_reason(self):
        self.controller.write_text(self.controller.read_text() + '\n# drift')
        out=StringIO();err=StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),mock.patch.object(security.publisher,'token') as token:
            code=security.guard.main(['--config',str(self.config),'--expected-config-sha256',self.digest,'--go','--output',str(self.output)])
        self.assertEqual(code,1);token.assert_not_called()
        self.assertIn('reviewed controller source hash differs',err.getvalue())

    def test_credential_free_dispatch_output_hold_echoes_reason(self):
        out=StringIO();err=StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),mock.patch.object(security.publisher,'token') as token:
            code=security.guard.main(['--config',str(self.config),'--expected-config-sha256',self.digest,'--go','--output',str(self.root/'outside-reports')])
        self.assertEqual(code,1);token.assert_not_called()
        self.assertIn('controller output must remain in canonical private reports',err.getvalue())

    def test_guard_override_refused_before_any_credential_or_network(self):
        out=StringIO();err=StringIO()
        with mock.patch.dict(os.environ,VIRIDIS_ZENODO_API_BASE='https://sandbox.zenodo.org/api'), \
             contextlib.redirect_stdout(out),contextlib.redirect_stderr(err),mock.patch.object(security.publisher,'token') as token, \
             mock.patch.object(security.gate,'public_record') as network:
            code=security.guard.main(['--config',str(self.config),'--expected-config-sha256',self.digest,'--go','--output',str(self.output)])
        self.assertEqual(code,1);token.assert_not_called();network.assert_not_called()
        self.assertIn('VIRIDIS_ZENODO_API_BASE is forbidden',err.getvalue())
