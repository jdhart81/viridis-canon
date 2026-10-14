import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

DIRECTORY = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, DIRECTORY / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lean = load("lean_repair_lint")
slo = load("pipeline_slo")
PLAYBOOK = {"schema": "VRS-LEAN-REPAIR-PLAYBOOK-1", "rules": [
    {"id": "UNFOLD_LOCAL_ALGEBRA_DEFINITIONS"}, {"id": "RFL_ALGEBRA_REASSOCIATION"}]}
PREFIX = "def disturbanceSq (p : ℝ) : ℝ := p * (1 - p)\ndef purityLoss (p : ℝ) : ℝ := 2 * p * (1 - p)\n"


def candidate(proof):
    return (PREFIX + "theorem dephasing_purity_loss_identity (p : ℝ) :\n    purityLoss p = 2 * disturbanceSq p := by\n  " + proof.replace("\n", "\n  ") + "\n").encode()


class LeanAdvisoryTests(unittest.TestCase):
    def test_run191_four_attempt_regressions(self):
        for proof, flag in [("rfl", "FLAG_RFL_ALGEBRA_REASSOCIATION"),
                            ("ring", "FLAG_UNFOLD_LOCAL_ALGEBRA_DEFINITIONS"),
                            ("ring_nf", "FLAG_UNFOLD_LOCAL_ALGEBRA_DEFINITIONS"),
                            ("unfold purityLoss disturbanceSq\nring", None)]:
            with self.subTest(proof=proof):
                report = lean.lint(candidate(proof), PLAYBOOK)
                row = report["theorems"][0]
                self.assertFalse(report["certifies"])
                self.assertEqual(row["flags"], [flag] if flag else [])
                if not flag:
                    self.assertEqual(row["status"], "ADVISORY_PASS_NOT_CERTIFICATION")

    def test_partial_unfold_still_flags_remaining_definition(self):
        row = lean.lint(candidate("unfold purityLoss\nring"), PLAYBOOK)["theorems"][0]
        self.assertEqual(row["definitions_to_unfold"], ["disturbanceSq"])

    def test_nested_comments_cannot_fake_unfold(self):
        row = lean.lint(candidate("/- unfold purityLoss /- disturbanceSq -/ -/\nring"), PLAYBOOK)["theorems"][0]
        self.assertTrue(row["flags"])

    def test_string_cannot_fake_definition(self):
        source = b'def greeting := "def fictional := 1"\ntheorem x : 1 = 1 := by\n  ring\n'
        row = lean.lint(source, PLAYBOOK)["theorems"][0]
        self.assertEqual(row["referenced_local_definitions"], [])

    def test_explicit_simp_set_and_complex_tactics_are_unassessed(self):
        for proof in ("norm_num [purityLoss, disturbanceSq]", "first | ring | rfl", "simp [purityLoss]"):
            self.assertEqual(lean.lint(candidate(proof), PLAYBOOK)["theorems"][0]["status"], "ADVISORY_UNASSESSED")

    def test_no_first_attempts_is_unavailable_not_zero_acceptance(self):
        result = lean.weekly_first_attempt_rate([], "2026-W42")
        self.assertIsNone(result["rate"])
        self.assertEqual(result["status"], "UNAVAILABLE")

    def test_first_attempt_rate_excludes_later_attempts_and_shows_unknown(self):
        rows = [{"run_id": "Run-191", "attempt": 1, "terminal_status": "REJECTED", "submitted_at_utc": "2026-10-14T17:00:00Z"},
                {"run_id": "Run-191", "attempt": 4, "terminal_status": "ACCEPTED", "submitted_at_utc": "2026-10-14T19:00:00Z"},
                {"run_id": "Run-192", "attempt": 1, "terminal_status": "PENDING"}]
        result = lean.weekly_first_attempt_rate(rows, "2026-W42")
        self.assertEqual(result["terminal_first_attempts"], 1)
        self.assertEqual(result["rate"], 0)
        self.assertEqual(result["status"], "PARTIAL")


class SLOTests(unittest.TestCase):
    def setUp(self):
        self.observer = {"observed_at_utc": "2026-10-14T17:00:00Z", "science": {
            "generation": {"generated_at_utc": "2026-10-14T05:00:00Z", "latest_run": "Run-196",
                           "window": {"generation_due": False}},
            "certification": {"age_hours": 100, "backlog_runs": ["Run-191"]}}}

    def test_generation_freshness_and_certificate_age_stay_separate(self):
        report = slo.collect(self.observer, {}, "2026-10-14T18:00:00Z")
        self.assertEqual(report["generation_freshness"]["status"], "FRESH")
        self.assertEqual(report["certification_age"]["status"], "OVERDUE")
        self.assertEqual(report["certification_age"]["age_hours"], 101)
        self.assertFalse(report["certifies"])
        self.assertEqual(report["external_mutations"], 0)

    def test_absent_snapshots_stay_unavailable(self):
        report = slo.collect({}, {}, "2026-10-14T18:00:00Z")
        for name in ("generation_freshness", "certification_age", "pdf_coverage", "banner_coverage",
                     "leak_scan", "weekly_digest", "fifo_liveness", "new_evidence_footprint"):
            self.assertEqual(report[name]["status"], "UNAVAILABLE")
        self.assertIsNone(report["pdf_coverage"]["ratio"])
        self.assertIsNone(report["new_evidence_footprint"]["bytes"])
        self.assertIsNone(report["leak_scan"]["hits"])

    def test_fifo_alert_strictly_after_24h_and_keeps_failing_goal(self):
        snapshot = {"fifo_head": {"run_id": "Run-191", "held_since_utc": "2026-10-13T18:00:00Z",
                                  "failing_goal": "⊢ purityLoss p = disturbanceSq p * 2"}}
        self.assertEqual(slo.collect(self.observer, snapshot, "2026-10-14T18:00:00Z")["fifo_liveness"]["status"], "BELOW_ALERT_THRESHOLD")
        row = slo.collect(self.observer, snapshot, "2026-10-14T18:00:01Z")["fifo_liveness"]
        self.assertEqual(row["status"], "ALERT")
        self.assertIn("purityLoss", row["failing_goal"])

    def test_fifo_missing_goal_does_not_invent_one(self):
        snapshot = {"fifo_head": {"run_id": "Run-191", "held_since_utc": "2026-10-12T18:00:00Z"}}
        row = slo.collect(self.observer, snapshot, "2026-10-14T18:00:00Z")["fifo_liveness"]
        self.assertEqual(row["status"], "ALERT")
        self.assertIsNone(row["failing_goal"])
        self.assertEqual(row["failing_goal_status"], "UNAVAILABLE")

    def test_coverage_requires_a_dated_receipt_and_consistent_counts(self):
        known = {"status": "KNOWN", "covered": 9, "total": 10, "source_receipt": "review.json",
                 "observed_at_utc": "2026-10-14T17:00:00Z"}
        self.assertEqual(slo.coverage(known)["ratio"], 0.9)
        with self.assertRaises(ValueError): slo.coverage({**known, "covered": 11})
        with self.assertRaises(ValueError): slo.coverage({**known, "source_receipt": None})
        self.assertIsNone(slo.coverage({**known, "covered": 0, "total": 0})["ratio"])

    def test_leak_scan_zero_is_scoped_and_missing_is_unavailable(self):
        snapshot = {"leak_scan": {"status": "KNOWN", "hits": 0, "source_receipt": "scan.json", "scope": ["new files only"]}}
        self.assertEqual(slo.collect(self.observer, snapshot, "2026-10-14T18:00:00Z")["leak_scan"]["status"], "PASS_SCOPED")
        snapshot["leak_scan"]["hits"] = 1
        self.assertEqual(slo.collect(self.observer, snapshot, "2026-10-14T18:00:00Z")["leak_scan"]["status"], "HOLD_TOKEN_HITS")

    def test_footprint_counts_explicit_files_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "included").write_bytes(b"123")
            (root / "excluded").write_bytes(b"123456")
            row = slo.scoped_footprint({"files": ["included"]}, root)
            self.assertEqual(row["bytes"], 3)
            self.assertIsNone(row["day_bytes"])
            self.assertEqual(row["day_status"], "UNAVAILABLE")
            self.assertEqual(slo.scoped_footprint({"files": [], "day_bytes_before_phase": 4}, root)["bytes"], 0)

    def test_footprint_refuses_traversal_duplicates_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); (root / "data").write_bytes(b"x"); (root / "link").symlink_to(root / "data")
            for names in (["../escape"], ["data", "data"], ["link"]):
                with self.subTest(names=names):
                    with self.assertRaises(ValueError): slo.scoped_footprint({"files": names}, root)

    def test_footprint_marks_budget_hold_without_deleting_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (root / "large").open("wb") as stream: stream.truncate(slo.PHASE_LIMIT + 1)
            row = slo.scoped_footprint({"files": ["large"]}, root)
            self.assertEqual(row["status"], "HOLD_BUDGET_EXCEEDED")
            self.assertTrue((root / "large").exists())

    def test_ten_line_summary_and_no_activation(self):
        report = slo.collect(self.observer, {}, "2026-10-14T18:00:00Z")
        self.assertEqual(len(slo.weekly_summary(report).splitlines()), 10)
        self.assertEqual(report["activation"], "PREPARED_NOT_SCHEDULED")

    def test_prior_week_publication_cannot_satisfy_current_week(self):
        snapshot = {"weekly_digest": {"iso_week": "2026-W41", "status": "PUBLISHED",
                                       "source_receipt": "w41-public-readback.json"}}
        report = slo.collect({}, snapshot, "2026-10-14T18:00:00Z")
        self.assertEqual(report["weekly_digest"]["status"], "HOLD_WRONG_ISO_WEEK")
        self.assertEqual(report["weekly_digest"]["iso_week"], "2026-W42")
        self.assertEqual(report["weekly_digest"]["source_iso_week"], "2026-W41")
        self.assertIn("2026-W42", slo.weekly_summary(report))

    def test_digest_week_uses_new_york_at_utc_monday_boundary(self):
        snapshot = {"weekly_digest": {"iso_week": "2026-W41", "status": "PUBLISHED",
                                       "source_receipt": "w41-public-readback.json"}}
        report = slo.collect({}, snapshot, "2026-10-12T00:30:00Z")
        self.assertEqual(report["weekly_digest"]["status"], "PUBLISHED")

    def test_future_coverage_receipt_cannot_report_known_current_coverage(self):
        for field in ("pdf_coverage", "banner_coverage"):
            snapshot = {field: {"status": "KNOWN", "covered": 1, "total": 1,
                              "source_receipt": "future.json", "observed_at_utc": "2026-10-15T00:00:00Z"}}
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "coverage observation"):
                slo.collect({}, snapshot, "2026-10-14T18:00:00Z")

    def test_future_or_naive_timestamps_are_rejected(self):
        with self.assertRaises(ValueError): slo.collect(self.observer, {}, "2026-10-14T18:00:00")
        with self.assertRaises(ValueError): slo.collect(self.observer, {}, "2026-10-14T16:00:00Z")


if __name__ == "__main__":
    unittest.main()
