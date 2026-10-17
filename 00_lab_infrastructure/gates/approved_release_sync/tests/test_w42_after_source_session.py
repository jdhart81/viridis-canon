import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
from w42_fixture import W42Fixture, RUNTIME
import root_scope
import w42_receipt as w42
import w42_after_source_session as caller
import descriptive_os
import approved_release_continuation
import trusted_canon_adapter
from deadline import Budget


class W42SourceTests(unittest.TestCase):
    def setUp(self): self.f = W42Fixture(); self.addCleanup(self.f.close)
    def published(self): self.f.terminal(); self.f.proof(); return self.f.consume()
    def assert_hold(self, fn, reason):
        with self.assertRaisesRegex(Exception, reason): fn()

    def test_real_shaped_config_copy_and_separate_statement_truth(self):
        value = self.published()
        original = self.f.scope_value["config"]
        copied = self.f.terminal_value["config"]
        self.assertNotEqual(original["path"], copied["path"])
        self.assertNotEqual(original["sha256"], copied["sha256"])
        self.assertEqual(value["status"], "W42_PUBLISHED_SOURCE_EXIT_VERIFIED")
        self.assertEqual(len(value["children"]), 2)
        note = self.f.read(self.f.manifest)["notes"][0]
        child = self.f.read(self.f.registration)["children"][0]
        self.assertEqual(set(note["publication_binding"]), {"path", "sha256", "bytes"})
        self.assertEqual(set(child["publication_binding"]), {"path", "sha256"})
        self.assertEqual(set(self.f.read(self.f.publication)["manifest"]), {"path", "sha256", "bytes"})
        for row in value["children"]:
            self.assertFalse(row["certifies"]); self.assertFalse(row["certificate_valid"])
            self.assertIsNone(row["certificate"]); self.assertFalse(row["runtime_admission"])
            self.assertTrue(row["statement_certificate_evidence"]["certificate_valid"])
            self.assertFalse(row["statement_certificate_evidence"]["certifies_current_artifact"])
        self.assertEqual(value["legacy_consumer_status"], "HOLD_UNCERTIFIED_ARTIFACT")

    def test_only_producer_evidence_can_have_optional_exact_bytes(self):
        value = {**self.f.bind(self.f.authority), "bytes": self.f.authority.stat().st_size}
        self.assertEqual(w42.evidence_binding(self.f.root, value), self.f.bind(self.f.authority))
        self.assert_hold(lambda: w42.read_bound(self.f.root, value), "HOLD_W42_FILE_BINDING")
        self.assert_hold(lambda: w42.evidence_binding(self.f.root, {**value, "bytes": value["bytes"] + 1}), "HOLD_W42_EVIDENCE_BYTE_SIZE")
        self.assert_hold(lambda: w42.evidence_binding(self.f.root, {**value, "unexpected": True}), "HOLD_W42_EVIDENCE_FILE_BINDING")

    def test_fixed_reviewed_hash_constants(self):
        raw = (RUNTIME / "w42_receipt.py").read_text()
        self.assertIn('GUARD_SHA256 = "7d19e7b3456af246139a43598d233eb947dc626707a9c8bac73e15a28ff2b3df"', raw)
        self.assertIn('FROZEN_WEEKEND_SHA256 = "36b23f17c4ef4a9758f587caeb52f16c72d149fb49776e4e2fc920f5d2e32bec"', raw)

    def test_source_closure_omission_wrong_role_and_drift(self):
        for mode in ("omitted", "wrong_role", "drift"):
            with self.subTest(mode=mode):
                value = copy.deepcopy(self.f.scope_value)
                if mode == "omitted": del value["sources"]["deadline.py"]
                elif mode == "wrong_role":
                    other = self.f.put("wrong/deadline.py", (self.f.runtime / "deadline.py").read_bytes())
                    value["sources"]["deadline.py"] = self.f.bind(other)
                else:
                    path = self.f.runtime / "deadline.py"; before = path.read_bytes(); path.write_bytes(before + b"# drift\n")
                scope = self.f.obj("bad-scope.json", value)
                self.assert_hold(lambda: root_scope.load(self.f.root, self.f.bind(scope)), "HOLD_ROOT_")
                if mode == "drift": path.write_bytes(before)

    def test_mandatory_scheduled_data_pr_review(self):
        for required in (None, False, "true"):
            value = copy.deepcopy(self.f.scope_value); value["data_pr_review_policy"] = {"required": required}
            path = self.f.obj("bad-scope.json", value)
            self.assert_hold(lambda: root_scope.load(self.f.root, self.f.bind(path)), "HOLD_SCHEDULED_EXACT_HEAD")

    def test_source_and_nomination_drift_hold(self):
        self.published()
        path = self.f.root / "_ZENODO_DEPOSITS/legacy_000.py"; path.write_bytes(b"changed\n")
        self.assert_hold(self.f.consume, "HOLD_W42_INPUT_DRIFT")

    def test_old_or_rehearsal_pending_terminal_refused(self):
        self.published(); terminal = copy.deepcopy(self.f.terminal_value)
        for patch in ({"status": "REHEARSAL_PASS"}, {"published": False}, {"source_session_exit_succeeded": False}):
            self.f.terminal_path.write_bytes(w42.encoded({**terminal, **patch})); self.f.refresh_proof()
            self.assert_hold(self.f.consume, "HOLD_W42_FINAL_PUBLICATION_REQUIRED")

    def test_missing_frames_guard_role_command_and_reaped_proof_hold(self):
        self.published(); original = copy.deepcopy(self.f.proof_value)
        mutations = [lambda v: v.update(before={}, after={}), lambda v: v.update(process_reaped=False),
                     lambda v: v.update(child_pid=0), lambda v: v.update(command=["python", "quarantined.py"]),
                     lambda v: v.update(caller=self.f.scope_value["sources"]["deadline.py"])]
        for mutation in mutations:
            value = copy.deepcopy(original); mutation(value); self.f.proof_path.write_bytes(w42.encoded(value))
            self.assert_hold(self.f.consume, "HOLD_GENUINE_OUTER_SOURCE_EXIT_REQUIRED")

    def test_exact_week_and_actual_child_id(self):
        self.published(); original = self.f.read(self.f.registration)
        for patch in ("week", "child"):
            value = copy.deepcopy(original)
            if patch == "week": value["release_week"] = "2026-W41"
            else: value["children"][0]["id"] = "publication:methods-note:2026-W41:Run-198"
            self.f.registration.write_bytes(w42.encoded(value))
            terminal = copy.deepcopy(self.f.terminal_value); terminal["registration_receipt"] = self.f.bind(self.f.registration)
            self.f.terminal_path.write_bytes(w42.encoded(terminal)); self.f.refresh_proof()
            self.assert_hold(self.f.consume, "HOLD_W42_(EXACT_RELEASE_WEEK|UNCERTIFIED_CHILD)")

    def test_admitted_note_upload_source_inventory_required(self):
        self.published()
        value = self.f.read(self.f.manifest); value["notes"][0]["uploads"][0]["filename"] = "../outside.lean"
        # Rebind all causally dependent files to isolate the semantic gate.
        self.f.manifest.write_bytes(w42.encoded(value))
        self.assert_hold(self.f.consume, "HOLD_W42_INPUT_DRIFT")

    def test_inactive_host_gate_cannot_be_bypassed_by_fd_or_json(self):
        value = copy.deepcopy(self.f.scope_value)
        value.update(writer=True, qualified_host=True, inherited_lock_fd=1, host_hook={"status": "PASS"})
        path = self.f.obj("attempted-host-flags.json", value); popen = mock.Mock()
        self.assert_hold(lambda: caller.run(self.f.root, self.f.bind(path), apply=True, popen=popen), "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED")
        popen.assert_not_called(); self.assertFalse((self.f.root / "reports/approved-release-source-exit").exists())

    def test_default_interlock_holds_without_publisher_or_writes(self):
        self.assert_hold(lambda: caller.run(self.f.root, self.f.scope_binding, apply=True, popen=mock.Mock()), "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED")
        self.assertFalse((self.f.root / "reports/approved-release-source-exit").exists())

    def test_terminal_without_owned_exit_never_reenters_publisher(self):
        self.f.terminal(); popen = mock.Mock()
        with mock.patch.object(root_scope, "require_mutation_authority"):
            self.assert_hold(lambda: caller.run(self.f.root, self.f.scope_binding, apply=True, popen=popen), "HOLD_PUBLISHER_EXIT_UNPROVEN_NO_REENTRY")
        popen.assert_not_called()

    def test_child_nonzero_with_valid_terminal_has_no_exit_proof_and_no_retry(self):
        f = self.f
        class Child:
            pid = 234; returncode = None
            def wait(self, timeout): f.terminal(); self.returncode = 1; return 1
        popen = mock.Mock(return_value=Child()); downstream = mock.Mock()
        with mock.patch.object(root_scope, "require_mutation_authority"):
            self.assert_hold(lambda: caller.run(f.root, f.scope_binding, apply=True, popen=popen, continue_fn=downstream), "HOLD_PUBLISHER_NONZERO_NO_REENTRY")
            self.assert_hold(lambda: caller.run(f.root, f.scope_binding, apply=True, popen=popen), "HOLD_PUBLISHER_EXIT_UNPROVEN_NO_REENTRY")
        self.assertEqual(popen.call_count, 1); downstream.assert_not_called()
        folder = f.root / "reports/approved-release-source-exit"
        self.assertEqual([p.name for p in folder.iterdir()], [f.scope_binding["sha256"] + ".started.json"])

    def test_child_timeout_with_terminal_is_uncertain_and_no_retry(self):
        f = self.f
        class Child:
            pid = 234; returncode = None
            def wait(self, timeout): f.terminal(); raise subprocess.TimeoutExpired("fixed", timeout)
        popen = mock.Mock(return_value=Child()); cleanup = mock.Mock()
        with mock.patch.object(root_scope, "require_mutation_authority"), mock.patch.object(caller, "_terminate_owned_live_group", cleanup):
            self.assert_hold(lambda: caller.run(f.root, f.scope_binding, apply=True, popen=popen), "HOLD_PUBLISHER_EXIT_UNCERTAIN_NO_REENTRY")
            self.assert_hold(lambda: caller.run(f.root, f.scope_binding, apply=True, popen=popen), "HOLD_PUBLISHER_EXIT_UNPROVEN_NO_REENTRY")
        self.assertEqual(popen.call_count, 1); cleanup.assert_called_once()

    def test_source_drift_after_exit_never_dispatches(self):
        f = self.f
        class Child:
            pid = 234; returncode = None
            def wait(self, timeout):
                f.terminal(); (f.root / "_ZENODO_DEPOSITS/legacy_000.py").write_bytes(b"drift"); self.returncode = 0; return 0
        downstream = mock.Mock()
        with mock.patch.object(root_scope, "require_mutation_authority"):
            self.assert_hold(lambda: caller.run(f.root, f.scope_binding, apply=True, popen=mock.Mock(return_value=Child()), continue_fn=downstream), "HOLD_W42_INPUT_DRIFT")
        downstream.assert_not_called()

    def test_checkpoint_before_downstream_failure_and_retry_skips_child(self):
        f = self.f
        class Child:
            pid = 234; returncode = None
            def wait(self, timeout): f.terminal(); self.returncode = 0; return 0
        popen = mock.Mock(return_value=Child())
        downstream = mock.Mock(side_effect=[RuntimeError("metadata transport"), {"status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED"}])
        with mock.patch.object(root_scope, "require_mutation_authority"):
            self.assertRaisesRegex(RuntimeError, "metadata transport", caller.run, f.root, f.scope_binding, apply=True, popen=popen, continue_fn=downstream)
            checkpoint = f.root / "reports/approved-release-source-exit" / (f.scope_binding["sha256"] + ".json")
            before = checkpoint.read_bytes()
            result = caller.run(f.root, f.scope_binding, apply=True, popen=popen, continue_fn=downstream)
            self.assertEqual(checkpoint.read_bytes(), before)
        self.assertEqual(popen.call_count, 1); self.assertTrue(result["publisher_exit_checkpoint_reused"])
        self.assertEqual(result["publisher_invocations"], 0)

    def test_missing_canon_package_checkpoints_then_holds_without_second_publish(self):
        f = self.f
        class Child:
            pid = 234; returncode = None
            def wait(self, timeout): f.terminal(); self.returncode = 0; return 0
        popen = mock.Mock(return_value=Child())
        with mock.patch.object(root_scope, "require_mutation_authority"):
            first = caller.run(f.root, f.scope_binding, apply=True, popen=popen)
            second = caller.run(f.root, f.scope_binding, apply=True, popen=popen)
        self.assertEqual(first["status"], "HOLD_CANON_RELEASE_PACKAGE_REQUIRED")
        self.assertEqual(second["status"], first["status"]); self.assertEqual(popen.call_count, 1)

    def test_default_continuation_wires_apply_adapter(self):
        self.published(); self.f.package()
        scope = {**self.f.latest_value, "continuation_route_binding": self.f.bind(self.f.route)}
        import approved_release_continuation as continuation
        import trusted_canon_adapter as adapter
        with mock.patch.object(root_scope, "require_mutation_authority"), mock.patch.object(adapter, "ApprovedCanonAdapter") as construct, mock.patch.object(continuation, "continue_release", return_value={"status": "PENDING"}) as call:
            caller._continue(self.f.root, self.f.bind(self.f.terminal_path), self.f.bind(self.f.latest), scope, budget=Budget())
        construct.assert_called_once_with(apply=True)
        self.assertTrue(call.call_args.kwargs["apply"])
        self.assertIs(call.call_args.kwargs["canon_adapter"], construct.return_value)

    def test_full_root_canon_scope_consumes_actual_exit(self):
        self.published(); self.f.package()
        scope = root_scope.load(self.f.root, self.f.bind(self.f.latest), require_canon=True)
        self.assertEqual(root_scope.validated_intake(self.f.root, scope)["doi"], "10.5281/zenodo.123")
        proof = self.f.proof_value; proof.update(before={}, after={})
        self.f.proof_path.write_bytes(w42.encoded(proof))
        latest = self.f.read(self.f.latest); latest["publisher_exit_checkpoint"] = self.f.bind(self.f.proof_path)
        self.f.latest.write_bytes(w42.encoded(latest))
        self.assert_hold(lambda: root_scope.load(self.f.root, self.f.bind(self.f.latest), require_canon=True), "HOLD_GENUINE_OUTER_SOURCE_EXIT_REQUIRED")

    def test_exact_mapping_omission_foreign_source_and_doi_hold(self):
        self.published(); self.f.package()
        for mode in ("omitted", "foreign", "doi", "format"):
            payload = copy.deepcopy(self.f.payload_value); scope = copy.deepcopy(self.f.latest_value)
            children = payload["publication_mappings"][0]["children"]
            if mode == "omitted": children.pop()
            elif mode == "foreign": children[0]["source_path"] = children[1]["source_path"]; children[0]["source_sha256"] = children[1]["source_sha256"]
            elif mode == "doi": children[0]["backing_doi"] = "10.5281/zenodo.999"
            else: scope["public_projection_format"] = "METHODS_DIGEST_CERTIFIED_JOIN"
            self.assert_hold(lambda: root_scope.validate_w42_mapping(self.f.root, scope, payload), "HOLD_(W42_|CANON_FORMAT_SUCCESSOR_REQUIRED)")

    def catalog(self):
        intake = self.f.consume(); by_run = {r["run_id"]: r for r in intake["children"]}
        rows = {}
        for child in self.f.payload_value["publication_mappings"][0]["children"]:
            actual = by_run[child["run_id"]]
            truth = {key: actual[key] for key in ("status", "certifies", "certificate_valid", "certificate", "certificate_sha256", "artifact_label")}
            rows[child["canon_record_id"]] = {"doi": child["backing_doi"], "source_sha256": child["source_sha256"], "status": "working",
                "integrity": "not-canon-admitted", "tier": "working-corpus", "tags": ["working", "lean4"],
                "metadata": {"artifact_type": "lean4", "verification_coverage": {"status": "HOLD", "canon_eligible": False,
                    "proposed_canon_eligible": False, "label": w42.ARTIFACT_LABEL, "current_artifact": truth,
                    "statement_certificate_evidence": child["statement_certificate_evidence"]}}}
        return rows

    def test_restrictive_existing_source_projection_and_false_cert_regression(self):
        self.published(); self.f.package(); rows = self.catalog()
        root_scope.validate_w42_mapping(self.f.root, self.f.latest_value, self.f.payload_value, rows)
        for mode in ("verified", "current", "statement", "private"):
            changed = copy.deepcopy(rows); row = next(iter(changed.values())); coverage = row["metadata"]["verification_coverage"]
            if mode == "verified": row["status"] = "verified"; row["integrity"] = "gate-passed"; coverage.update(status="PASS", canon_eligible=True)
            elif mode == "current": coverage["current_artifact"]["certifies"] = True
            elif mode == "statement": coverage["statement_certificate_evidence"]["certifies_current_artifact"] = True
            else: row["metadata"]["current_artifact"] = coverage["current_artifact"]
            self.assert_hold(lambda: root_scope.validate_w42_mapping(self.f.root, self.f.latest_value, self.f.payload_value, changed), "HOLD_(W42_|CANON_FORMAT_SUCCESSOR_REQUIRED)")

    def test_descriptive_os_stays_inactive_without_real_host(self):
        self.published(); self.f.package()
        self.assert_hold(lambda: descriptive_os.reconcile(self.f.root, self.f.canon, self.f.terminal_path, self.f.route), "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED")
        self.assertFalse((self.f.root / "ViridisOS").exists())

    def test_descriptive_index_actual_readback_and_legacy_hold(self):
        self.published(); self.f.package()
        with mock.patch.object(root_scope, "require_mutation_authority"):
            result = descriptive_os.reconcile(self.f.root, self.f.canon, self.f.terminal_path, self.f.route)
            second = descriptive_os.reconcile(self.f.root, self.f.canon, self.f.terminal_path, self.f.route)
        self.assertEqual(result, second)
        self.assertEqual(result["status"], "DESCRIPTIVE_OS_INDEX_READBACK_VERIFIED")
        self.assertEqual(result["reader_proof"]["reader"], "descriptive_os.read_index")
        self.assertFalse(result["runtime_admission"]); self.assertFalse(result["automatic_adoption"])
        observed = descriptive_os.read_index(self.f.root, result["reader_proof"]["index"])
        self.assertEqual(len(observed["records"]), 2)
        self.assertEqual(observed["legacy_consumer_status"], "HOLD_UNCERTIFIED_ARTIFACT")
        self.assertTrue(observed["records"][0]["statement_certificate_evidence"]["certificate_valid"])
        self.assertFalse((self.f.root / "RESEARCH_PIPELINE_v2").exists())


if __name__ == "__main__": unittest.main()
