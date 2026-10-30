"""Synthetic HTTP/SSH and temporary receipts only; the live host gate stays closed."""
import copy
import json
import subprocess
import time
import unittest
from unittest.mock import patch

from common_sync_fixtures import Budget, Fixture, sync


class CommonSyncTests(unittest.TestCase):
    def setUp(self): self.f = Fixture()
    def tearDown(self): self.f.close()

    def test_unqualified_host_has_zero_http_or_receipt_mutations(self):
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED"):
            self.f.synchronize()
        self.assertEqual(self.f.http.calls, [])
        self.assertEqual(self.f.receipts(), [])

    def test_read_only_current_plan_checks_both_endpoints_without_writes(self):
        self.f.http.make_current()
        result = self.f.synchronize(apply=False)
        self.assertEqual(result["status"], "ALREADY_SYNCHRONIZED")
        urls = [c["url"] for c in self.f.http.calls]
        self.assertIn(sync.REGISTRY_URL, urls); self.assertIn(sync.DECISION_TREE_URL, urls)
        self.assertTrue(all(c["method"] == "GET" for c in self.f.http.calls))
        self.assertEqual(self.f.receipts(), [])

    def test_inert_apply_and_replay_verify_full_rows_and_preserve_success(self):
        result = self.f.synchronize(permit_inert_test=True)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertTrue(result["decision_tree_records_digest"])
        self.assertFalse(result["runtime_execution_verified"])
        self.assertEqual([row["certification_label"] for row in self.f.http.registry["records"]],
                         ["UNCERTIFIED", "UNCERTIFIED", "UNCERTIFIED", "VERIFIED"])
        path = self.f.receipts()[0]; before = path.read_bytes(); mtime = path.stat().st_mtime_ns
        self.assertEqual(self.f.synchronize(permit_inert_test=True), result)
        self.assertEqual(path.read_bytes(), before); self.assertEqual(path.stat().st_mtime_ns, mtime)
        self.assertEqual(sum(c["method"] == "POST" for c in self.f.http.calls), 1)

    def test_decision_tree_same_count_with_stale_full_row_holds(self):
        self.f.http.make_current()
        self.f.http.map["corpus_records"][0]["runtime_binding"] = {"stale": True}
        with self.assertRaisesRegex(sync.SyncHold, "FULL_ROW_MISMATCH"):
            sync.validate_decision_tree(self.f.http.map, self.f.http.registry)

    def test_decision_tree_duplicate_id_and_unexpected_field_hold(self):
        self.f.http.make_current()
        for change in ["duplicate", "field"]:
            value = copy.deepcopy(self.f.http.map)
            if change == "duplicate": value["corpus_records"][1] = copy.deepcopy(value["corpus_records"][0])
            else: value["corpus_records"][0]["unsupported_current_certification"] = True
            with self.subTest(change=change), self.assertRaises(sync.SyncHold):
                sync.validate_decision_tree(value, self.f.http.registry)

    def test_registry_coverage_detail_and_every_source_field_checked(self):
        registry, _ = self.f.http.project()
        expected = {"expected_catalog_digest": self.f.catalog["catalog_digest"], "expected_canon_commit": self.f.commit,
                    "expected_record_count": len(self.f.catalog["records"])}
        rows = sync.catalog_rows(self.f.catalog)
        for key, bad in [("title", "stale"), ("path", "old.lean"), ("caveat", "lost"),
                         ("certification_label", "VERIFIED"), ("certification_detail", "certified"),
                         ("verification_coverage", None), ("certification_authority", True)]:
            current = copy.deepcopy(registry); current["records"][0][key] = bad
            with self.subTest(key=key), self.assertRaises(sync.SyncHold): sync.validate_registry(current, expected, rows)

    def test_full_coverage_is_required_for_candidate_and_quarantine_wins(self):
        registry, _ = self.f.http.project()
        self.assertEqual(registry["records"][0]["kernel_state"], "NOT_ELIGIBLE")
        self.assertEqual(registry["records"][2]["kernel_state"], "QUARANTINED")
        self.assertEqual(registry["stats"]["kernel_candidates"], 1)

    def test_separate_predecessor_statement_truth_survives_both_metadata_readbacks(self):
        coverage = self.f.catalog["records"][0]["metadata"]["verification_coverage"]
        coverage["current_artifact"] = {"status": "UNCERTIFIED", "certifies": False, "certificate_valid": False,
                                        "certificate": None, "certificate_sha256": None}
        coverage["statement_certificate_evidence"] = {"scope": "SEALED_PREDECESSOR_STATEMENT_ONLY",
            "certificate_valid": True, "certifies_current_artifact": False, "source_evidence_sha256": "a" * 64}
        self.f.catalog.pop("catalog_digest"); self.f.catalog["catalog_digest"] = sync.digest(self.f.catalog)
        self.f.http.catalog = copy.deepcopy(self.f.catalog)
        canon = sync.object_file(self.f.canon); canon["catalog_digest"] = self.f.catalog["catalog_digest"]
        self.f.canon.write_text(json.dumps(canon))
        result = self.f.synchronize(permit_inert_test=True)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        for rows in [self.f.http.registry["records"], self.f.http.map["corpus_records"]]:
            self.assertEqual(rows[0]["verification_coverage"], coverage)
            self.assertEqual(rows[0]["certification_label"], "UNCERTIFIED")
            self.assertFalse(rows[0]["certification_authority"])

    def test_invalid_catalog_digest_holds_before_callback(self):
        self.f.http.catalog["records"][0]["title"] = "digest drift"
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CATALOG_DIGEST"):
            self.f.synchronize(permit_inert_test=True)
        self.assertFalse(any(c["method"] == "POST" for c in self.f.http.calls))

    def test_code_only_main_advance_requires_both_raw_catalog_pins(self):
        self.f.http.commit = "e" * 40; self.f.http.make_current()
        result = self.f.synchronize(permit_inert_test=True)
        self.assertEqual(result["metadata_source_commit"], "e" * 40)
        urls = [c["url"] for c in self.f.http.calls]
        for commit in [self.f.commit, "e" * 40]:
            self.assertTrue(any("/" + commit + "/docs/data/catalog.json" in url for url in urls))

    def test_stale_app_replay_uses_current_same_catalog_commit_in_callback(self):
        self.f.http.commit = "e" * 40
        result = self.f.synchronize(permit_inert_test=True)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(result["expected"]["expected_canon_commit"], self.f.commit)
        self.assertEqual(result["metadata_source_commit"], "e" * 40)
        posts = [call for call in self.f.http.calls if call["method"] == "POST"]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["body"]["expected_canon_commit"], "e" * 40)
        self.assertEqual(posts[0]["body"]["expected_catalog_digest"], self.f.catalog["catalog_digest"])

    def test_digest_receipt_cannot_claim_or_omit_current_certification(self):
        value = {"standard": "VRS-STANDALONE-PDF-DIGEST-EXECUTION-2", "status": "PUBLISHED_STRICT_READBACK_PASS",
                 "published": True, "source_session_exit_succeeded": True, "doi": "10.5281/zenodo.123"}
        for claim in [None, True, 0]:
            current = {**value, "certifies": claim} if claim is not None else value
            with self.subTest(claim=claim), self.assertRaisesRegex(sync.SyncHold, "HOLD_DIGEST_PUBLICATION_PENDING"):
                sync.publication_dois(current)
        self.assertEqual(sync.publication_dois({**value, "certifies": False}), ("methods-digest", {"10.5281/zenodo.123"}))

    def test_changed_current_catalog_never_downgrades_to_old_receipt(self):
        self.f.http.commit = "e" * 40
        changed = copy.deepcopy(self.f.catalog); changed.pop("catalog_digest")
        changed["records"][0]["title"] = "new release"; changed["catalog_digest"] = sync.digest(changed)
        self.f.http.pinned["e" * 40] = changed
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CURRENT_CANON_CATALOG_DRIFT"):
            self.f.synchronize(permit_inert_test=True)
        self.assertFalse(any(c["method"] == "POST" for c in self.f.http.calls))

    def test_success_receipt_survives_later_persistent_decision_map_regression(self):
        self.f.synchronize(permit_inert_test=True)
        path = self.f.receipts()[0]; before = path.read_bytes()
        self.f.http.persistent_map_mutation = lambda value: value["corpus_records"][0].update(title="stale")
        self.f.http.make_current()
        result = self.f.synchronize(permit_inert_test=True)
        self.assertEqual(result["status"], "CANON_PUBLISHED_APP_METADATA_PENDING")
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(result["existing_verified_receipt_sha256"], sync.file_hash(path))

    def test_uncertain_applied_callback_recovers_by_both_readbacks_without_second_post(self):
        self.f.http.uncertain_callback = True
        self.assertEqual(self.f.synchronize(permit_inert_test=True)["status"], "CANON_PUBLISHED_APP_METADATA_PENDING")
        self.f.http.uncertain_callback = False
        self.assertEqual(self.f.synchronize(permit_inert_test=True)["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(sum(c["method"] == "POST" for c in self.f.http.calls), 1)
        self.assertNotIn(self.f.environment["CRON_SECRET"], "".join(p.read_text() for p in self.f.receipts()))

    def test_same_budget_is_threaded_through_every_http_stage(self):
        now = [0.0]; self.f.budget = Budget(clock=lambda: now[0])
        delegate = self.f.http
        def http(*args, **kwargs):
            value = delegate(*args, **kwargs); now[0] += 0.1; return value
        with patch.object(sync, "require_mutation_authority"):
            sync.synchronize(self.f.canon, [self.f.doi], root=self.f.root, apply=True, http=http,
                             environ=self.f.environment, budget=self.f.budget)
        self.assertTrue(all(c["budget"] is self.f.budget for c in delegate.calls))
        self.assertGreater(delegate.calls[0]["remaining"], delegate.calls[-1]["remaining"])

    def test_blocked_http_is_bounded_by_shared_deadline(self):
        def blocked(*_args, **_kwargs): time.sleep(10)
        began = time.monotonic()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_SHARED_DEADLINE"):
            sync.get(blocked, sync.REGISTRY_URL, budget=Budget(0.03, 0.03))
        self.assertLess(time.monotonic() - began, 0.5)

    def test_direct_post_also_hits_unqualified_host_gate_before_opener(self):
        with patch.object(sync.urllib.request, "build_opener") as opener:
            with self.assertRaisesRegex(sync.SyncHold, "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED"):
                sync.http_json("POST", sync.SYNC_URL, body={}, secret="inert", budget=self.f.budget)
            opener.assert_not_called()

    def test_ssh_outer_and_remote_timeouts_share_remaining_budget(self):
        now = [0.0]; budget = Budget(clock=lambda: now[0]); now[0] = 535
        expected = {"expected_canon_commit": self.f.commit, "expected_catalog_digest": self.f.catalog["catalog_digest"], "expected_record_count": 4}
        output = {"status": "synchronized", "catalog_digest": expected["expected_catalog_digest"], "canon_commit": self.f.commit, "record_count": 4}
        calls = []
        def runner(command, **kwargs):
            calls.append((command, kwargs)); return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        with patch.object(sync, "require_mutation_authority"):
            status, value = sync.metadata_callback(expected, transport="existing-app-ssh", secret=None,
                http=self.f.http, runner=runner, budget=budget)
        self.assertEqual((status, value), (200, output))
        command, kwargs = calls[0]
        self.assertLessEqual(kwargs["timeout"], 5)
        self.assertTrue(command[-1].endswith(" 5000"))
        self.assertIn("AbortSignal.timeout(Number(timeoutText))", kwargs["input"])
        self.assertIn("redirect:'error'", kwargs["input"])
        self.assertNotIn("env", kwargs)


if __name__ == "__main__": unittest.main()
