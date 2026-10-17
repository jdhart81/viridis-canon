"""Auditor S5/S10/S11 semantics, using dummy HTTP without live endpoints."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.error
import urllib.parse

import test_publish_successor_credentials as fixtures
import rehearsal

PUBLISHER = fixtures.PUBLISHER
TOKEN = fixtures.TOKEN


class NativeHTTP(fixtures.SuccessorHTTP):
    def __init__(self, *, drop_custom=False, keep_copyright=True, delete_failures=0, gone_status=404):
        super().__init__()
        self.custom_fields = {"code:codeRepository":"https://github.com/jdhart81/viridis-canon"}
        self.access = {"record":"public","files":"public"}
        self.predecessor_custom = copy.deepcopy(self.custom_fields)
        self.drop_custom, self.keep_copyright = drop_custom, keep_copyright
        self.deleted = False
        self.delete_failures, self.gone_status, self.delete_requests = delete_failures, gone_status, 0

    def open(self, request, timeout):
        path = urllib.parse.urlsplit(request.full_url).path
        method = request.get_method()
        if method == "DELETE" and path in {"/api/records/200/draft","/api/deposit/depositions/200"}:
            self.requests.append(request); self.delete_requests += 1
            if self.deleted:
                raise urllib.error.HTTPError(request.full_url,self.gone_status,"deleted",{},None)
            if self.delete_failures:
                self.delete_failures -= 1
                raise urllib.error.HTTPError(request.full_url,500,"temporary failure",{},None)
            self.deleted = True
            return fixtures.Response({})
        if self.deleted and method == "GET" and path in {"/api/records/200/draft","/api/deposit/depositions/200"}:
            self.requests.append(request)
            raise urllib.error.HTTPError(request.full_url,self.gone_status,"deleted",{},None)
        response = super().open(request, timeout)
        if method == "PUT" and path == "/api/deposit/depositions/200":
            if self.keep_copyright:
                self.metadata["copyright"] = fixtures.COPYRIGHT
            if self.drop_custom:
                self.custom_fields = {}
        if method == "PUT" and path == "/api/records/200/draft":
            payload = json.loads(request.data)
            self.custom_fields = copy.deepcopy(payload.get("custom_fields", {}))
            self.access = copy.deepcopy(payload.get("access", {}))
        if method == "GET" and path == "/api/deposit/depositions/200":
            value = json.loads(response.data)
            value["metadata"] = copy.deepcopy(self.metadata)
            return fixtures.Response(value)
        if request.get_header("Accept") == "application/vnd.inveniordm.v1+json":
            value = json.loads(response.data)
            value.update(custom_fields=copy.deepcopy(self.predecessor_custom if path == "/api/records/100" else self.custom_fields),
                         access=copy.deepcopy(self.access), parent={"id":"99"},
                         files={"entries":{row["filename"]:{"key":row["filename"],"checksum":row["checksum"],"size":row["filesize"]}for row in self.files}})
            return fixtures.Response(value)
        return response


class SuccessorHardeningTests(unittest.TestCase):
    def setUp(self):
        self.publisher = PUBLISHER

    def candidate(self, root):
        bundle = root / "XX"; bundle.mkdir()
        (bundle / "paper.pdf").write_bytes(b"%PDF-1.4 approved successor")
        metadata = {"title":"Retained scientific title","creators":[{"name":"Example"}],"version":"v2"}
        return {"bundle":bundle,"abbreviation":"XX","predecessor_doi":"10.5281/zenodo.100","new_version":"v2",
                "upload_names":("paper.pdf",),"metadata":{"metadata":metadata},
                "approved_preflight_json":json.dumps(fixtures.local_preflight(bundle,[bundle / "paper.pdf"]))}

    def test_legacy_put_custom_fields_loss_holds_before_publish(self):
        p = self.publisher
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = self.candidate(root); server = NativeHTTP(drop_custom=True)
            with mock.patch.object(p,"ROOT",root), mock.patch.object(p.urllib.request,"build_opener",return_value=server):
                with self.assertRaisesRegex(p.SuccessorPublisherError,"native successor protected content differs"):
                    p.publish_candidate(candidate,TOKEN)
            self.assertFalse(server.published); self.assertTrue(server.deleted)
            self.assertFalse((candidate["bundle"] / "PUBLISHED_DOI.txt").exists())
            receipt = json.loads((candidate["bundle"] / "NATIVE_SUCCESSOR_READBACK.json").read_text())
            self.assertEqual(receipt["before_legacy_put"]["custom_fields"],server.predecessor_custom)
            self.assertEqual(receipt["after"]["custom_fields"],{})

    def test_legacy_put_preserves_complete_native_fields_and_can_publish(self):
        p = self.publisher
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); candidate = self.candidate(root); server = NativeHTTP()
            with mock.patch.object(p,"ROOT",root), mock.patch.object(p.urllib.request,"build_opener",return_value=server):
                result = p.publish_candidate(candidate,TOKEN)
            self.assertEqual(result["doi"],"10.5281/zenodo.200")
            self.assertEqual(server.custom_fields,server.predecessor_custom)

    def test_recovered_doi_readback_error_is_preserved_without_delete(self):
        p = self.publisher
        for recovery in ("public_record","submitted_deposition","receipt"):
            with self.subTest(recovery=recovery), tempfile.TemporaryDirectory() as temp:
                root = Path(temp); candidate = self.candidate(root); calls = []
                if recovery == "receipt":
                    (candidate["bundle"] / "PUBLISHED_DOI.txt").write_text("10.5281/zenodo.777")
                def api(token,method,url,*args,**kwargs):
                    calls.append((method,url))
                    if url.endswith("/records/100"):
                        return {"id":100,"metadata":{"copyright":fixtures.COPYRIGHT}}
                    if url.endswith("/records/777"):
                        return {"id":777,"metadata":{"doi":"10.5281/zenodo.777"}} if recovery == "public_record" else None
                    if url.endswith("/deposit/depositions/777"):
                        return {"id":777,"submitted":True,"metadata":{"doi":"10.5281/zenodo.777"}}
                    self.fail("unexpected request after a recovered DOI")
                original = p.SuccessorPublisherError("published DOI retained; exact public readback mismatch")
                with mock.patch.object(p,"api_call",side_effect=api), mock.patch.object(p,"ensure_draft",return_value="777"), \
                     mock.patch.object(p,"verify_manuscript_readback",side_effect=original):
                    with self.assertRaises(p.SuccessorPublisherError) as caught:
                        p.publish_candidate(candidate,TOKEN)
                self.assertIs(caught.exception,original)
                self.assertFalse(any(method == "DELETE" for method,url in calls))
                self.assertEqual((candidate["bundle"] / "PUBLISHED_DOI.txt").read_text().strip(),"10.5281/zenodo.777")

    def test_successor_override_refused_before_any_api_or_receipt(self):
        p = self.publisher
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ,VIRIDIS_ZENODO_API_BASE="https://sandbox.zenodo.org/api"):
            candidate = self.candidate(Path(temp))
            with mock.patch.object(p,"api_call") as api:
                with self.assertRaises((p.SuccessorPublisherError,getattr(p,"rehearsal",rehearsal).RehearsalHold)):
                    p.publish_candidate(candidate,TOKEN)
                api.assert_not_called()
            self.assertFalse((candidate["bundle"] / "APPROVED_UPLOAD_PREFLIGHT.json").exists())

    def test_successor_api_override_refused_before_opener(self):
        p = self.publisher
        with mock.patch.dict(os.environ,VIRIDIS_ZENODO_API_BASE="https://sandbox.zenodo.org/api"), mock.patch.object(p.urllib.request,"build_opener") as opener:
            with self.assertRaises((p.SuccessorPublisherError,getattr(p,"rehearsal",rehearsal).RehearsalHold)):
                p.api_call(TOKEN,"GET","https://zenodo.org/api/records/100")
            opener.assert_not_called()

    def test_foreign_doi_holds_before_any_receipt(self):
        p = self.publisher
        self.assertIsNone(p.extract_doi({"metadata":{"doi":"10.5072/zenodo.777"}}))
        with tempfile.TemporaryDirectory() as temp:
            candidate = self.candidate(Path(temp)); (candidate["bundle"] / "PUBLISHED_DOI.txt").write_text("10.5072/zenodo.777")
            with mock.patch.object(p,"api_call") as api:
                with self.assertRaises(p.SuccessorPublisherError):p.publish_candidate(candidate,TOKEN)
                api.assert_not_called()
            self.assertFalse((candidate["bundle"] / "APPROVED_UPLOAD_PREFLIGHT.json").exists())

    def test_successor_rehearsal_detects_native_loss_and_deletes(self):
        p = self.publisher
        if not hasattr(p,"rehearse_candidate"):
            self.skipTest("guarded successor has no rehearsal entry; digest uses its controller")
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temp):
            root = Path(temp); candidate = self.candidate(root); before = p.rehearsal.tree_hashes(candidate["bundle"])
            server = NativeHTTP(drop_custom=True)
            with mock.patch.object(p,"ROOT",root), mock.patch.object(p.urllib.request,"build_opener",return_value=server):
                with self.assertRaisesRegex(p.SuccessorPublisherError,"native successor protected content differs"):
                    p.rehearse_candidate(candidate,TOKEN)
            self.assertTrue(server.deleted); self.assertFalse(server.published)
            self.assertEqual(before,p.rehearsal.tree_hashes(candidate["bundle"]))
            receipt = json.loads(next((root / "rehearsals").rglob("REHEARSAL.json")).read_text())
            self.assertEqual(receipt["state"],"HOLD_REHEARSAL_DRAFT_DELETED")

    def test_successor_rehearsal_retry_delete_and_accept_410(self):
        p = self.publisher
        if not hasattr(p,"rehearse_candidate"):
            self.skipTest("guarded successor has no rehearsal entry; digest uses its controller")
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temp):
            root = Path(temp); candidate = self.candidate(root); before = p.rehearsal.tree_hashes(candidate["bundle"])
            server = NativeHTTP(delete_failures=1,gone_status=410)
            with mock.patch.object(p,"ROOT",root), mock.patch.object(p.urllib.request,"build_opener",return_value=server):
                receipt = p.rehearse_candidate(candidate,TOKEN)
            self.assertEqual(receipt["state"],"REHEARSED_DRAFT_DELETED")
            self.assertEqual(receipt["deletion"]["http_status"],410)
            self.assertEqual(receipt["deletion"]["attempts"],2)
            self.assertEqual(before,p.rehearsal.tree_hashes(candidate["bundle"]))
            self.assertFalse(server.published)

    def test_successor_rehearsal_cleanup_failure_keeps_draft_id(self):
        p = self.publisher
        if not hasattr(p,"rehearse_candidate"):
            self.skipTest("guarded successor has no rehearsal entry; digest uses its controller")
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temp):
            root = Path(temp); candidate = self.candidate(root); server = NativeHTTP(delete_failures=2)
            with mock.patch.object(p,"ROOT",root), mock.patch.object(p.urllib.request,"build_opener",return_value=server):
                with self.assertRaisesRegex(p.SuccessorPublisherError,"HOLD_DRAFT_CLEANUP_REQUIRED"):
                    p.rehearse_candidate(candidate,TOKEN)
            receipt = json.loads(next((root / "rehearsals").rglob("REHEARSAL.json")).read_text())
            self.assertEqual(receipt["state"],"HOLD_DRAFT_CLEANUP_REQUIRED")
            self.assertEqual(receipt["draft_id"],"200")
            self.assertFalse(receipt["deletion"]["deleted"])
            self.assertFalse(server.published)

    def test_copyright_hold_then_rehearsal_finally_accepts_already_gone_draft(self):
        p=self.publisher
        if not hasattr(p,'rehearse_candidate'):
            self.skipTest('guarded source has no separate rehearsal entrypoint')
        class NativePutDrift(NativeHTTP):
            def open(self,request,timeout):
                result=super().open(request,timeout)
                if request.get_method()=='PUT' and urllib.parse.urlsplit(request.full_url).path=='/api/records/200/draft':
                    self.metadata['title']='unexpected native PUT drift'
                return result
        with tempfile.TemporaryDirectory() as temporary,mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temporary):
            root=Path(temporary);candidate=self.candidate(root);server=NativePutDrift(keep_copyright=False,gone_status=410)
            output=root/'rehearsals/exact'
            with mock.patch.object(p,'ROOT',root),mock.patch.object(p.urllib.request,'build_opener',return_value=server):
                with self.assertRaisesRegex(p.SuccessorPublisherError,'copyright-only RDM draft readback differs'):
                    p.rehearse_candidate(candidate,TOKEN,output=output)
            receipt=json.loads((output/'REHEARSAL.json').read_text())
            self.assertEqual(receipt['draft_id'],'200');self.assertEqual(receipt['state'],'HOLD_REHEARSAL_DRAFT_DELETED')
            self.assertEqual(receipt['deletion']['http_status'],410);self.assertGreaterEqual(server.delete_requests,2)
            self.assertFalse(server.published)

    def test_native_projection_ignores_ambient_module_and_rejects_installed_tamper(self):
        import sys
        from types import SimpleNamespace
        p=self.publisher
        value={'id':'200','metadata':{'title':'Retained'},'custom_fields':{'retain':True},'files':{'entries':{}}}
        with mock.patch.dict(sys.modules,{'own_record_comparison':SimpleNamespace(prior_protected_projection=lambda *a,**kw:{})}):
            projected=p.native_projection(value)
        self.assertEqual(projected['custom_fields'],{'retain':True})
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary).resolve(); path=root/'RESEARCH_PIPELINE_v2/verification_coverage_gates/own_record_comparison.py'
            path.parent.mkdir(parents=True);path.write_text('raise RuntimeError("ambient executed")')
            with mock.patch.object(p,'ROOT',root):
                with self.assertRaisesRegex(p.SuccessorPublisherError,'reviewed native protected projection source differs'):
                    p.native_projection(value)
