from pathlib import Path
import copy
import importlib.util
import json
import tempfile
import sys
import unittest
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))
SOURCE = RUNTIME / "approved_release_continuation.py"
spec = importlib.util.spec_from_file_location("owner_continuation", SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sync = module.sync


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.publication = self.root / "TERMINAL_RESULT.json"
        self.publication.write_text(json.dumps({"standard": "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2",
            "status": "PUBLISHED_STRICT_READBACK_PASS", "published": True, "source_session_exit_succeeded": True,
            "certifies": False, "record_id": "123", "doi": "10.5281/zenodo.123"}))
        # Synthetic technical scope only: no newly invented Justin approval.
        # Real Root scope/owned exit proof integration is tested independently.
        self.approval = self.root / "ROOT_SCOPE_FIXTURE.json"
        self.approval.write_text(json.dumps({"standard": "VRS-APPROVED-RELEASE-SYNC-ROOT-SCOPE-1",
            "status": "ROOT_REVIEWED", "canonical_root": str(self.root),
            "data_pr_review_policy": {"required": True, "audit_directory": str(self.root / "inert-audit-fixtures")}}))
        self.scope_patch = patch.object(module.root_scope, "load", side_effect=self.load_fixture_scope)
        self.scope_patch.start()
        self.host_patch = patch.object(module.root_scope, "require_mutation_authority")
        self.host_patch.start()
        self.mapping_patch = patch.object(module.root_scope, "validate_w42_mapping")
        self.mapping_patch.start()
        self.science = self.root / "exact_reviewed_science.lean"; self.science.write_text("-- immutable fixture source\n")
        self.adapter = self.root / "reviewed_owner_adapter.py"; self.adapter.write_text("# fixture only; never imported from data\n")
        self.payload = self.root / "CANON_RELEASE_PAYLOAD.json"
        self.payload_value = {"standard": "VRS-OWNER-CANON-RELEASE-PAYLOAD-1", "publication_dois": ["10.5281/zenodo.123"],
            "source_files": [self.file_binding(self.science)], "publication_mappings": [{"parent_doi": "10.5281/zenodo.123",
                "parent_canon_publication_id": "methods-2026-W42", "children": [{"run_id": "Run-123", "canon_record_id": "run-123",
                    "backing_doi": "10.5281/zenodo.123", "source_path": self.science.name, "source_sha256": sync.file_hash(self.science)}]}]}
        self.payload.write_text(json.dumps(self.payload_value))
        self.binding = self.root / "APPROVED_CONTINUATION.json"
        self.value = {"standard": module.STANDARD, "status": "OWNER_REVIEWED_PACKAGE_BINDING", "publisher_format": "methods-digest",
            "owner_approval": self.file_binding(self.approval), "publication_receipt": self.file_binding(self.publication),
            "canon_payload_manifest": self.file_binding(self.payload), "owner_canon_adapter": {"adapter_id": "owner-reviewed-digest-v1",
                "reviewed_payload_sha256": sync.file_hash(self.payload), "implementation_source": self.file_binding(self.adapter)}}
        self.save_binding()
        self.canon = self.root / "verified-canon.json"
        self.canon.write_text(json.dumps({"status": "verified", "repository": sync.REPOSITORY, "branch": "main", "spine_changed": False,
            "bundles": [{"doi": "10.5281/zenodo.123"}]}))
        self.calls = []

    def tearDown(self):
        self.mapping_patch.stop()
        self.host_patch.stop()
        self.scope_patch.stop()
        self.temp.cleanup()

    def load_fixture_scope(self, root, binding, *, require_canon=False):
        self.assertEqual(Path(root).resolve(), self.root)
        self.assertTrue(require_canon)
        path = module.bound_file(self.root, binding) if isinstance(binding, dict) else sync.regular(binding, self.root)
        value = sync.object_file(path)
        sync.require(value.get("standard") == "VRS-APPROVED-RELEASE-SYNC-ROOT-SCOPE-1"
            and value.get("status") == "ROOT_REVIEWED" and value.get("canonical_root") == str(self.root),
            "HOLD_EXPLICIT_ROOT_SCOPE_REQUIRED")
        return value

    def file_binding(self, path):
        return {"path": str(path.relative_to(self.root)), "sha256": sync.file_hash(path)}

    def save_binding(self):
        self.binding.write_text(json.dumps(self.value))
        self.binding_sha = sync.file_hash(self.binding)

    def dispatch(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return {"status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED", "publisher_invocations": 0}

    def call(self, **kwargs):
        return module.continue_release(self.publication, root=self.root, route_binding=self.binding,
            expected_binding_sha256=self.binding_sha, dispatcher=self.dispatch, **kwargs)

    def test_absent_approved_package_has_exact_hold(self):
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_RELEASE_PACKAGE_REQUIRED"):
            module.continue_release(self.publication, root=self.root)
        self.assertEqual(self.calls, [])

    def test_dry_run_never_executes_an_adapter_or_dispatcher(self):
        result = self.call(canon_adapter=lambda **kwargs: self.fail("adapter executed"))
        self.assertEqual(result["status"], "OWNER_CONTINUATION_READY_FOR_INTEGRATION")
        self.assertFalse(result["mapping_inferred"])
        self.assertEqual(self.calls, [])

    def test_missing_owner_adapter_holds_without_inventing_canon_closure(self):
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_OWNER_CANON_ADAPTER_IMPLEMENTATION_REQUIRED"):
            self.call(apply=True)
        self.assertEqual(self.calls, [])

    def test_existing_exact_canon_receipt_continues_without_adapter(self):
        self.value["verified_canon_receipt"] = self.file_binding(self.canon); self.save_binding()
        result = self.call(apply=True)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1]["publication_format"], "methods-digest")

    def test_reviewed_owner_adapter_receipt_is_required_before_dispatch(self):
        def owner(**kwargs):
            self.assertEqual(kwargs["expected_binding_sha256"], self.binding_sha)
            return {"status": "VERIFIED_CANON_CLOSURE", "adapter_id": self.value["owner_canon_adapter"]["adapter_id"],
                    "payload_sha256": sync.file_hash(self.payload), "canon_receipt": self.file_binding(self.canon)}
        self.assertEqual(self.call(apply=True, canon_adapter=owner)["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")

    def test_changed_mapping_or_source_is_rejected_before_any_adapter(self):
        self.science.write_text("-- changed source\n")
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CONTINUATION_FILE_DRIFT"):
            self.call(apply=True)
        self.assertEqual(self.calls, [])

    def test_unapproved_parent_child_mapping_cannot_be_inferred(self):
        self.payload_value["publication_mappings"][0]["children"] = []
        self.payload.write_text(json.dumps(self.payload_value))
        self.value["canon_payload_manifest"] = self.file_binding(self.payload)
        self.value["owner_canon_adapter"]["reviewed_payload_sha256"] = sync.file_hash(self.payload); self.save_binding()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_PARENT_CHILD_MAPPING_REQUIRED"):
            self.call(apply=True)

    def test_reconsume_rejects_source_change_during_owner_adapter(self):
        def owner(**kwargs):
            self.science.write_text("-- changed during adapter\n")
            return {"status": "VERIFIED_CANON_CLOSURE", "adapter_id": self.value["owner_canon_adapter"]["adapter_id"],
                    "payload_sha256": sync.file_hash(self.payload), "canon_receipt": self.file_binding(self.canon)}
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CONTINUATION_FILE_DRIFT"):
            self.call(apply=True, canon_adapter=owner)
        self.assertEqual(self.calls, [])

    def test_successor_format_is_real_route_specific_not_a_digest_alias(self):
        self.publication = self.root / "SUCCESSOR_PUBLICATION_RECEIPT.json"
        self.publication.write_text(json.dumps({"standard": "VRS-ZENODO-SUCCESSOR-PUBLICATION-1",
            "state": "ZENODO_SUCCESSOR_WAVE_PUBLISHED", "results": [{"doi": "10.5281/zenodo.123", "record_id": "123"}]}))
        self.value["publisher_format"] = "successor-wave"
        self.value["publication_receipt"] = self.file_binding(self.publication)
        self.value["verified_canon_receipt"] = self.file_binding(self.canon); self.save_binding()
        self.assertEqual(self.call(apply=True)["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(self.calls[0][1]["publication_format"], "successor-wave")

    def test_owner_can_preserve_a_childs_explicit_existing_standalone_doi(self):
        self.payload_value["publication_mappings"][0]["children"][0]["backing_doi"] = "10.5281/zenodo.122"
        self.payload.write_text(json.dumps(self.payload_value))
        self.value["canon_payload_manifest"] = self.file_binding(self.payload)
        self.value["owner_canon_adapter"]["reviewed_payload_sha256"] = sync.file_hash(self.payload); self.save_binding()
        self.assertEqual(self.call()["status"], "OWNER_CONTINUATION_READY_FOR_INTEGRATION")

    def owner_result(self, calls):
        def owner(**kwargs):
            calls.append(kwargs)
            return {"status": "VERIFIED_CANON_CLOSURE", "adapter_id": self.value["owner_canon_adapter"]["adapter_id"],
                    "payload_sha256": sync.file_hash(self.payload), "canon_receipt": self.file_binding(self.canon)}
        return owner

    def test_identical_successful_retry_reuses_checkpoint_without_second_adapter(self):
        calls = []
        owner = self.owner_result(calls)
        first = self.call(apply=True, canon_adapter=owner)
        checkpoint = self.root / first["canon_checkpoint"]
        before, mtime = checkpoint.read_bytes(), checkpoint.stat().st_mtime_ns
        second = self.call(apply=True, canon_adapter=owner)
        self.assertEqual(len(calls), 1)
        self.assertFalse(first["canon_checkpoint_reused"])
        self.assertTrue(second["canon_checkpoint_reused"])
        self.assertEqual(checkpoint.read_bytes(), before)
        self.assertEqual(checkpoint.stat().st_mtime_ns, mtime)

    def test_metadata_exception_keeps_canon_checkpoint_and_retry_calls_adapter_once(self):
        calls = []
        owner = self.owner_result(calls)
        attempts = []
        def flaky(*args, **kwargs):
            attempts.append(1)
            if len(attempts) == 1:
                checkpoint = self.root / "reports/approved-canon-continuation" / (self.binding_sha + ".json")
                self.assertTrue(checkpoint.is_file())
                raise RuntimeError("metadata transport failed")
            return {"status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED"}
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_METADATA_DISPATCH_AFTER_CANON_CHECKPOINT"):
            module.continue_release(self.publication, root=self.root, route_binding=self.binding,
                expected_binding_sha256=self.binding_sha, apply=True, canon_adapter=owner, dispatcher=flaky)
        result = module.continue_release(self.publication, root=self.root, route_binding=self.binding,
            expected_binding_sha256=self.binding_sha, apply=True, canon_adapter=owner, dispatcher=flaky)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(len(calls), 1)
        self.assertTrue(result["canon_checkpoint_reused"])

    def test_metadata_pending_keeps_canon_checkpoint_and_retry_skips_adapter(self):
        calls = []
        owner = self.owner_result(calls)
        pending = lambda *args, **kwargs: {"status": "CANON_PUBLISHED_APP_METADATA_PENDING"}
        first = module.continue_release(self.publication, root=self.root, route_binding=self.binding,
            expected_binding_sha256=self.binding_sha, apply=True, canon_adapter=owner, dispatcher=pending)
        self.assertEqual(first["status"], "CANON_PUBLISHED_APP_METADATA_PENDING")
        second = self.call(apply=True, canon_adapter=owner)
        self.assertEqual(second["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(len(calls), 1)

    def test_changed_checkpoint_canon_receipt_holds_without_replaying_adapter(self):
        calls = []
        owner = self.owner_result(calls)
        self.call(apply=True, canon_adapter=owner)
        self.canon.write_text(self.canon.read_text() + "\n")
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CONTINUATION_FILE_DRIFT"):
            self.call(apply=True, canon_adapter=owner)
        self.assertEqual(len(calls), 1)

    def test_duplicate_child_public_record_ids_are_rejected(self):
        duplicate = copy.deepcopy(self.payload_value["publication_mappings"][0]["children"][0])
        duplicate["run_id"] = "Run-124"
        self.payload_value["publication_mappings"][0]["children"].append(duplicate)
        self.payload.write_text(json.dumps(self.payload_value))
        self.value["canon_payload_manifest"] = self.file_binding(self.payload)
        self.value["owner_canon_adapter"]["reviewed_payload_sha256"] = sync.file_hash(self.payload); self.save_binding()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_CHILD_ID_REQUIRED"):
            self.call()


if __name__ == "__main__":
    unittest.main()
