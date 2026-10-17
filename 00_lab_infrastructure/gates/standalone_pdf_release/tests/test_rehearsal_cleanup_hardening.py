"""Cleanup uncertainty always leaves an engine receipt with the draft identity."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import test_dated_exact_uploads as fixtures

P = fixtures.publisher


class RehearsalCleanupTests(unittest.TestCase):
    def exercise(self, *, midway=False, delete_failures=0, gone=404, real_hook=False):
        with tempfile.TemporaryDirectory() as temporary, mock.patch.dict(os.environ,VIRIDIS_ENGINE_ROOT=temporary):
            root = Path(temporary); bundle = fixtures.DatedExactUploadsTests().make_bundle(root)
            before = P.rehearsal.tree_hashes(bundle)
            state = {"files":{},"metadata":{},"deleted":False,"delete_calls":0,"publish_calls":0}
            def api(credential,method,url,data=None,content_type=None,**kwargs):
                if url.endswith("/actions/publish"):
                    state["publish_calls"] += 1; self.fail("publication reached rehearsal")
                if method == "POST":return {"id":123,"links":{"bucket":"https://zenodo.org/api/files/bucket"}}
                if method == "DELETE":
                    state["delete_calls"] += 1
                    if state["delete_calls"] <= delete_failures:raise P.PublisherError("synthetic delete failure")
                    state["deleted"] = True;return {}
                if method == "GET" and state["deleted"]:
                    kwargs.get("not_found_status",[]).append(gone);return None
                if method == "PUT" and "/api/files/" in url:
                    state["files"][url.rsplit("/",1)[1]] = data
                    return {"checksum":"0"*32 if midway else hashlib.md5(data).hexdigest()}
                if method == "PUT":state["metadata"] = json.loads(data)["metadata"];return {}
                if url.endswith("/files"):
                    return [{"filename":name,"checksum":hashlib.md5(raw).hexdigest(),"filesize":len(raw)}for name,raw in state["files"].items()]
                return {"id":123,"metadata":state["metadata"],"files":[]}
            if real_hook:
                sys.path.insert(0,str(Path(__file__).parents[2]))
                hooks = importlib.import_module("production_hooks")
                report = {"enforcement":True,"mode":"ENFORCING","status":"PASS","exact_publication_binding":True}
                scope = mock.patch.object(hooks,"publication_report",return_value=report)
            else:
                scope = mock.patch.object(P,"verification_coverage_report")
            failure = None
            with scope, mock.patch.object(P,"ROOT",root), mock.patch.object(P,"api_call",side_effect=api):
                try:result = P.rehearse_bundle(bundle,"synthetic-header-only")
                except P.PublisherError as exc:failure = exc
            receipts = list((root / "rehearsals").rglob("REHEARSAL.json"))
            self.assertEqual(len(receipts),1)
            receipt = json.loads(receipts[0].read_text())
            self.assertEqual(before,P.rehearsal.tree_hashes(bundle));self.assertEqual(state["publish_calls"],0)
            if real_hook:
                observations = list((root / "rehearsals").rglob("verification-coverage/*.json"))
                self.assertEqual(len(observations),1)
                self.assertTrue(json.loads(observations[0].read_text())["rehearsal"])
                self.assertFalse((root / "reports").exists())
            return receipt,state,failure

    def test_midway_hold_still_deletes_and_records_draft(self):
        receipt,state,error = self.exercise(midway=True)
        self.assertIsNotNone(error);self.assertTrue(state["deleted"])
        self.assertEqual(receipt["draft_id"],123)
        self.assertEqual(receipt["state"],"HOLD_REHEARSAL_DRAFT_DELETED")

    def test_delete_is_retried_and_410_confirmed(self):
        receipt,state,error = self.exercise(delete_failures=1,gone=410)
        self.assertIsNone(error);self.assertEqual(state["delete_calls"],2)
        self.assertEqual(receipt["deletion"]["http_status"],410)

    def test_failed_cleanup_keeps_receipt_and_identity(self):
        receipt,state,error = self.exercise(delete_failures=2)
        self.assertIsNotNone(error);self.assertFalse(state["deleted"])
        self.assertEqual(receipt["state"],"HOLD_DRAFT_CLEANUP_REQUIRED")
        self.assertEqual(receipt["draft_id"],123)

    def test_real_coverage_hook_persists_only_in_engine_scope(self):
        receipt,state,error = self.exercise(real_hook=True)
        self.assertIsNone(error);self.assertEqual(receipt["state"],"REHEARSED_DRAFT_DELETED")
