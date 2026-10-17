"""Inert adapter/HTTP tests; no Core imports, providers, secrets or old queue."""
import copy
import json
from pathlib import Path
import time
import unittest
from unittest.mock import Mock, patch

from common_sync_fixtures import Budget, Fixture, sync
import verified_publication_dispatch as dispatch


class CommonDispatchTests(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.publication = self.f.root / "TERMINAL_RESULT.json"
        self.publication.write_text(json.dumps({"standard": "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2",
            "status": "PUBLISHED_STRICT_READBACK_PASS", "published": True,
            "source_session_exit_succeeded": True, "certifies": False, "doi": "10.5281/zenodo.123"}))
        self.route = self.f.root / "route.json"; self.route.write_text("{}\n")
        self.adapter_budgets = []

    def tearDown(self): self.f.close()

    def reconcile(self, root, canon, publication, route, *, budget):
        self.adapter_budgets.append(budget)
        self.assertEqual((root, canon, publication, route), (self.f.root, self.f.canon, self.publication, self.route))
        path = root / "ViridisOS/data/approved_release_sync/inert-index.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"certifies": False, "runtime_admission": False, "automatic_adoption": False, "certificate": None,
                                   "legacy_consumer_status": dispatch.LEGACY_HOLD}))
        binding = {"path": str(path.relative_to(root)), "sha256": sync.file_hash(path)}
        return {"status": "DESCRIPTIVE_OS_INDEX_READBACK_VERIFIED", "readback_verified": True,
            "certifies": False, "runtime_admission": False, "automatic_adoption": False, "certificate": None,
            "legacy_consumer_status": dispatch.LEGACY_HOLD,
            "reader_proof": {"reader": "descriptive_os.read_index",
                "source_sha256": sync.file_hash(Path(dispatch.__file__).with_name("descriptive_os.py")),
                "artifact_sha256": binding["sha256"], "index": binding}}

    def call(self, *, apply=True, adapter=None, permit_inert_test=False):
        kwargs = dict(root=self.f.root, publication_format="methods-digest", apply=apply,
            http=self.f.http, environ=self.f.environment, local_os=adapter or self.reconcile,
            route_binding=self.route, budget=self.f.budget)
        # This scope seam only avoids constructing unrelated owner fixtures.
        # The real fixed mutation interlock is patched solely in downstream tests.
        with patch.object(dispatch, "_scope", return_value=(self.route, {"inert_test_only": True})):
            if permit_inert_test:
                with patch.object(sync, "require_mutation_authority"):
                    return dispatch.dispatch(self.publication, self.f.canon, [], **kwargs)
            return dispatch.dispatch(self.publication, self.f.canon, [], **kwargs)

    def receipts(self):
        return list((self.f.root / "reports/approved-release-sync/verified-publication-dispatch").glob("*.json"))

    def test_unpatched_host_gate_prevents_adapter_post_and_all_local_writes(self):
        adapter = Mock()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED"):
            self.call(adapter=adapter)
        adapter.assert_not_called()
        self.assertTrue(all(call["method"] == "GET" for call in self.f.http.calls))
        self.assertFalse((self.f.root / "ViridisOS").exists())
        self.assertFalse((self.f.root / "reports").exists())

    def test_read_only_plan_never_imports_adapter_or_mutates(self):
        adapter = Mock()
        result = self.call(apply=False, adapter=adapter)
        self.assertEqual(result["status"], "DRY_RUN")
        self.assertEqual(result["legacy_consumer_status"], dispatch.LEGACY_HOLD)
        adapter.assert_not_called()
        self.assertFalse((self.f.root / "reports").exists())
        self.assertTrue(all(call["method"] == "GET" for call in self.f.http.calls))

    def test_limited_metadata_success_preserves_legacy_hold_and_same_budget(self):
        result = self.call(permit_inert_test=True)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(result["scope"], "NEW_DESCRIPTIVE_OS_INDEX_AND_BOTH_APP_METADATA_READBACKS_ONLY")
        self.assertEqual(result["legacy_consumer_status"], dispatch.LEGACY_HOLD)
        for key in ["runtime_adoption", "runtime_admission", "certifies"]: self.assertIs(result[key], False)
        self.assertEqual(result["publisher_invocations"], 0); self.assertEqual(result["zenodo_mutations"], 0)
        self.assertEqual(self.adapter_budgets, [self.f.budget])
        self.assertTrue(all(call["budget"] is self.f.budget for call in self.f.http.calls))
        urls = [call["url"] for call in self.f.http.calls]
        self.assertIn(sync.REGISTRY_URL, urls); self.assertIn(sync.DECISION_TREE_URL, urls)

    def test_invalid_descriptive_authority_or_reader_never_posts(self):
        for key, value in [("certifies", True), ("certificate", {}), ("runtime_admission", True),
                           ("automatic_adoption", True), ("automatic_adoption", None),
                           ("legacy_consumer_status", "PASS"), ("readback_verified", False)]:
            def adapter(*args, _key=key, _value=value, **kwargs):
                result = self.reconcile(*args, **kwargs)
                if _key == "automatic_adoption" and _value is None: result.pop(_key)
                else: result[_key] = _value
                return result
            with self.subTest(key=key):
                result = self.call(adapter=adapter, permit_inert_test=True)
                self.assertEqual(result["status"], "CANON_PUBLISHED_VIRIDISOS_PENDING")
                self.assertEqual(result["reason"], "HOLD_DESCRIPTIVE_OS_READBACK_REQUIRED")
        self.assertFalse(any(call["method"] == "POST" for call in self.f.http.calls))

    def test_index_bytes_source_identity_and_named_namespace_must_match(self):
        for mutation in ["source", "bytes", "namespace"]:
            value = self.reconcile(self.f.root, self.f.canon, self.publication, self.route, budget=self.f.budget)
            if mutation == "source": value["reader_proof"]["source_sha256"] = "0" * 64
            elif mutation == "bytes":
                (self.f.root / value["reader_proof"]["index"]["path"]).write_text("changed")
            else:
                path = self.f.root / "orphan.json"; path.write_text("{}")
                value["reader_proof"]["index"] = {"path": "orphan.json", "sha256": sync.file_hash(path)}
                value["reader_proof"]["artifact_sha256"] = sync.file_hash(path)
            with self.subTest(mutation=mutation), self.assertRaises(sync.SyncHold):
                dispatch.validate_descriptive_result(value, root=self.f.root)

    def test_changed_publication_after_adapter_blocks_metadata(self):
        def adapter(*args, **kwargs):
            result = self.reconcile(*args, **kwargs)
            self.publication.write_text(self.publication.read_text() + "\n")
            return result
        result = self.call(adapter=adapter, permit_inert_test=True)
        self.assertEqual(result["reason"], "HOLD_PUBLICATION_EVIDENCE_CHANGED")
        self.assertFalse(any(call["method"] == "POST" for call in self.f.http.calls))

    def test_success_survives_later_bad_descriptive_readback(self):
        self.call(permit_inert_test=True)
        path = self.receipts()[0]; before = path.read_bytes()
        def adapter(*args, **kwargs):
            result = self.reconcile(*args, **kwargs); result["runtime_admission"] = True; return result
        held = self.call(adapter=adapter, permit_inert_test=True)
        self.assertEqual(held["existing_verified_receipt_sha256"], sync.file_hash(path))
        self.assertEqual(path.read_bytes(), before)

    def test_blocking_adapter_shares_absolute_budget_and_receipts_cleanup_hold(self):
        self.f.budget = Budget(0.04, 0.1)
        def blocked(*_args, **_kwargs): time.sleep(10)
        start = time.monotonic()
        result = self.call(adapter=blocked, permit_inert_test=True)
        self.assertEqual(result["reason"], "HOLD_SHARED_DEADLINE")
        self.assertLess(time.monotonic() - start, 0.5)
        self.assertEqual(len(self.receipts()), 1)
        self.assertFalse(any(call["method"] == "POST" for call in self.f.http.calls))

    def test_only_fixed_hash_bound_adapter_is_loadable_without_execution(self):
        source = Path(dispatch.__file__).resolve().with_name("descriptive_os.py")
        root = source.parent.parent
        binding = {"path": str(source.relative_to(root)), "sha256": sync.file_hash(source)}
        function = dispatch._fixed_descriptive_adapter(root, {"sources": {"descriptive_os.py": binding}})
        self.assertEqual(function.__name__, "reconcile")
        for bad in [{**binding, "sha256": "0" * 64}, {"path": "runtime/postpublication_sync.py", "sha256": binding["sha256"]}]:
            with self.subTest(binding=bad), self.assertRaisesRegex(sync.SyncHold, "HOLD_REVIEWED_DESCRIPTIVE_ADAPTER_REQUIRED"):
                dispatch._fixed_descriptive_adapter(root, {"sources": {"descriptive_os.py": bad}})


if __name__ == "__main__": unittest.main()
