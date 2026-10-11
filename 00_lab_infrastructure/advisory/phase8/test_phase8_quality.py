import copy
import json
import tempfile
import unittest
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import phase8_quality as q


class MetricsTests(unittest.TestCase):
    def row(self, run_id="Run-194", **changes):
        row = {"run_id": run_id, "generated_at_utc": "2026-10-12T05:00:00+00:00",
               "status": "CERTIFIED", "semantic_tier": "UNASSESSED",
               "novelty_status": "UNASSESSED", "selection_recorded": False,
               "portfolio_item_id": None}
        return {**row, **changes}

    def test_no_runs_is_unavailable_not_zero(self):
        result = q.summarize_week([], "2026-W42")
        self.assertIsNone(result["substantive_run_share_assessed"]["share"])
        self.assertIsNone(result["likely_new_run_share_assessed"]["share"])

    def test_unassessed_not_routine_or_known(self):
        report = q.summarize_week([self.row()], "2026-W42")
        self.assertEqual(report["semantic_tier_counts"], {"UNASSESSED": 1})
        self.assertEqual(report["novelty_status_counts"], {"UNASSESSED": 1})
        self.assertIsNone(report["substantive_run_share_assessed"]["share"])
        self.assertEqual(report["substantive_all_attempts_evidenced_lower_bound"]["share"], 0)

    def test_duplicate_digest_and_certificate_do_not_add_attempts(self):
        row = self.row()
        report = q.summarize_week([row, copy.deepcopy(row)], "2026-W42")
        self.assertEqual(report["runs_attempted"], 1)
        self.assertEqual(report["certified"], 1)

    def test_conflicting_run_inputs_remain_unknown(self):
        row = self.row()
        report = q.summarize_week([row, self.row(novelty_status="LIKELY_NEW")], "2026-W42")
        self.assertEqual(report["runs"][0]["status"], "UNKNOWN_CONFLICTING_INPUTS")
        self.assertEqual(report["runs"][0]["novelty_status"], "UNASSESSED")

    def test_actual_manifest_date_in_new_york_not_utc_day(self):
        row = self.row(generated_at_utc="2026-10-12T01:00:00+00:00")
        self.assertEqual(q.summarize_week([row], "2026-W41")["runs_attempted"], 1)
        self.assertEqual(q.summarize_week([row], "2026-W42")["runs_attempted"], 0)

    def test_malformed_and_naive_date_excluded(self):
        report = q.summarize_week([self.row(generated_at_utc="bad"),
                                   self.row("Run-195", generated_at_utc="2026-10-12T01:00:00")], "2026-W42")
        self.assertEqual(report["runs_attempted"], 0)
        self.assertEqual(len(report["undated_runs_excluded"]), 2)

    def test_explicit_activation_excludes_pre_rollout_same_day(self):
        before = self.row(generated_at_utc="2026-10-11T11:12:13+00:00")
        after = self.row("Run-195", generated_at_utc="2026-10-11T18:00:00+00:00")
        activation = q.iso_datetime("2026-10-11T17:00:00+00:00")
        report = q.summarize_week([before, after], "2026-W41", activation)
        self.assertEqual(report["phase8_run_ids_this_week"], ["Run-195"])
        self.assertEqual(q.summarize_week([after], "2026-W41")["phase8_runs_this_week"], 0)

    def test_tiny_assessed_denominator_cannot_meet_target(self):
        rows = [self.row(f"Run-{194+i}") for i in range(10)]
        rows[0].update(semantic_tier="SUBSTANTIVE", novelty_status="LIKELY_NEW")
        report = q.summarize_week(rows, "2026-W42")
        self.assertEqual(report["substantive_run_share_assessed"]["share"], 1)
        self.assertEqual(report["substantive_certified_run_share_evidenced_lower_bound"]["share"], .1)
        self.assertEqual(report["likely_new_all_attempts_evidenced_lower_bound"]["share"], .1)

    def test_substantive_metric_denominator_certified_only(self):
        rows = [self.row(semantic_tier="SUBSTANTIVE"), self.row("Run-195", status="HAS_SORRY")]
        result = q.summarize_week(rows, "2026-W42")
        self.assertEqual(result["substantive_certified_run_share_evidenced_lower_bound"]["denominator"], 1)

    def test_progress_requires_reviewed_current_evidence(self):
        outcomes = [{"portfolio_item_id": "P8-01", "disposition": "DISCHARGED", "evidence_path": "x"},
                    {"portfolio_item_id": "P8-02", "disposition": "STRENGTHENED", "evidence_path": "x",
                     "evidence_current": True, "reviewed": True, "review_reason": "Exact scoped extension."}]
        result = q.summarize_week([self.row(portfolio_outcomes=outcomes)], "2026-W42")
        self.assertEqual(len(result["portfolio_items_strengthened_or_discharged"]), 1)

    def test_invalid_portfolio_id_does_not_count(self):
        report = q.summarize_week([self.row(selection_recorded=True, portfolio_item_id="P8-99")], "2026-W42")
        self.assertEqual(report["portfolio_hit_rate_recorded_selections"]["numerator"], 0)

    def test_four_week_trend_dedups_and_is_not_gate(self):
        activation = datetime(2026, 10, 11, 17, tzinfo=timezone.utc)
        report = q.summarize_week([self.row(semantic_tier="SUBSTANTIVE", novelty_status="LIKELY_NEW")], "2026-W42", activation)
        trend = q.trend_summary([report, copy.deepcopy(report)], activation)
        self.assertEqual(trend["phase8_runs_attempted"], 1)
        self.assertFalse(trend["changes_gate_verdict"])
        self.assertEqual(trend["four_week_review_date"], "2026-11-08T17:00:00+00:00")

    def test_one_real_substantive_main_claim_counts_mixed_run(self):
        self.assertEqual(q.classify_run_depth(["SUBSTANTIVE", "ROUTINE", "UNCLASSIFIED"]), "SUBSTANTIVE")
        self.assertEqual(q.classify_run_depth(["ROUTINE", "UNCLASSIFIED"]), "UNASSESSED")

    def test_rendering_additive_only_and_missing_unassessed(self):
        claims = [{"lean_theorem": "p_eq_p", "evidence_class": "CERTIFIED_TRIVIAL",
                   "foundation_basis": "INDEPENDENT", "scope_status": "FROZEN", "certificate": {"sha256": "x"}}]
        before = copy.deepcopy(claims)
        result = q.add_novelty_to_claims(claims, None, "Run-194")
        self.assertEqual(claims, before)
        self.assertEqual({k: v for k, v in result[0].items() if k != "novelty_status"}, claims[0])
        self.assertIn("UNASSESSED", q.render_claim_table(claims, None, "Run-194"))

    def test_assessment_bound_to_run(self):
        assessment = {"run_id": "Run-195", "status": "LIKELY_NEW"}
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")
        self.assertEqual(q.strict_novelty({"run_id": "Run-194", "status": "NEW"}, "Run-194"), "UNASSESSED")
        self.assertEqual(q.strict_novelty({"run_id": "Run-194", "status": []}, "Run-194"), "UNASSESSED")
        self.assertEqual(q.strict_novelty({"run_id": "Run-194", "status": "LIKELY_NEW"}, "Run-194"), "UNASSESSED")

    def reviewed_assessment(self):
        if q.novelty_stage is None:
            self.skipTest("novelty_stage sibling required for real bound-assessment tests")
        n = q.novelty_stage
        now = datetime(2026, 10, 10, 18, tzinfo=timezone.utc)
        evidence_dir = tempfile.TemporaryDirectory()
        self.addCleanup(evidence_dir.cleanup)
        evidence_path = Path(evidence_dir.name) / "located-excerpt.txt"
        evidence_path.write_text("Theorem 1: A channel bound under an explicit named premise.")
        target = n.target_spec({"exact_statement": "A channel bound under an explicit named premise", "hypotheses": ["supplied physical premise"]})
        sources = [{"url": "https://example.test/known", "title": "Known channel bound", "channel": "arxiv", "score": 1}]
        assessment = {"run_id": "Run-194", "status": "UNASSESSED", "advisory_only": True, "failure_is_non_blocking": True,
                      "target": target, "target_sha256": n.digest(target), "query_sha256": n.digest(["channel bound"]),
                      "queries": ["channel bound"], "assessed_at_utc": now.isoformat(), "source_coverage": [],
                      "all_candidate_sources": sources, "top_closest_sources": sources}
        assessment["search_evidence_sha256"] = n.digest(n.evidence_payload(assessment))
        review = {"target_sha256": assessment["target_sha256"], "query_sha256": assessment["query_sha256"],
                  "search_evidence_sha256": assessment["search_evidence_sha256"], "reviewer": "Named test reviewer",
                  "reviewed_at_utc": now.isoformat(), "proposed_status": "KNOWN", "one_line_reasoning": "Same hypotheses and conclusion.",
                  "source_comparisons": [{"url": sources[0]["url"], "source_statement": target["exact_statement"],
                    "source_hypotheses": target["hypotheses"], "target_hypotheses": target["hypotheses"], "statement_locator": "Theorem 1",
                    "source_evidence_sha256": hashlib.sha256(evidence_path.read_bytes()).hexdigest(),
                    "source_evidence_path": evidence_path.name, "relation": "EQUIVALENT", "reason": "Equivalent statement."}]}
        assessment = n.classify(assessment, review, now=now, evidence_root=evidence_dir.name)
        assessment["classified_at_utc"] = now.isoformat()
        return assessment

    def test_exact_reviewed_novelty_rechecked(self):
        assessment = self.reviewed_assessment()
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "KNOWN")
        assessment["all_candidate_sources"][0]["title"] = "Altered search evidence"
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")

    def test_review_change_or_foreign_target_run_rejected(self):
        assessment = self.reviewed_assessment()
        assessment["comparison_review"]["one_line_reasoning"] = "Changed review"
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")
        assessment = self.reviewed_assessment()
        assessment["target"]["run_id"] = "Run-195"
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")

    def test_stale_at_run_rejected_but_historical_validity_preserved(self):
        assessment = self.reviewed_assessment()
        self.assertEqual(q.strict_novelty(assessment, "Run-194", q.iso_datetime("2026-10-12T05:00:00Z")), "KNOWN")
        self.assertEqual(q.strict_novelty(assessment, "Run-194", q.iso_datetime("2026-10-20T05:00:00Z")), "UNASSESSED")
        assessment["stale_at_run"] = True
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")
        assessment.pop("stale_at_run")
        assessment["valid_at_target_selection"] = False
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")

    def test_saved_evidence_changes_rejected_and_cwd_independent(self):
        assessment = self.reviewed_assessment()
        original = Path.cwd()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                os.chdir(tmp)
                self.assertEqual(q.strict_novelty(assessment, "Run-194"), "KNOWN")
            finally:
                os.chdir(original)
        evidence = Path(assessment["review_evidence_root"]) / "located-excerpt.txt"
        evidence.write_text("Changed exact source excerpt.")
        self.assertEqual(q.strict_novelty(assessment, "Run-194"), "UNASSESSED")

    def test_digest_novelty_deduplicates_runs(self):
        notes = [{"run_id": "Run-194"}, {"run_id": "Run-194"}]
        table = q.render_digest_table(notes, {})
        self.assertEqual(table.count("| Run-194 |"), 1)

    def test_tex_safe_rendering_preserves_raw_input(self):
        claims = [{"lean_theorem": "x_y%z", "evidence_class": "ASSUMED"}]
        before = copy.deepcopy(claims)
        rendered = q.render_claim_table_tex(claims, None, "Run-194")
        self.assertIn(r"x\_y\%z", rendered)
        self.assertIn("UNASSESSED", rendered)
        self.assertEqual(claims, before)

    def test_no_individual_theorem_novelty_assertion(self):
        claims = [{"lean_theorem": "identity", "evidence_class": "CERTIFIED_TRIVIAL"}]
        rendered = q.render_claim_table(claims, {"run_id": "Run-194", "status": "LIKELY_NEW"}, "Run-194")
        self.assertIn("Run-target novelty", rendered)
        self.assertIn("not each auxiliary theorem", rendered)
        self.assertIn("CERTIFIED_TRIVIAL", rendered)

    def test_frozen_authoring_fragment_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "NOVELTY_TABLE.md"
            q.write_authoring_fragment(path, "first")
            q.write_authoring_fragment(path, "first")
            with self.assertRaises(ValueError):
                q.write_authoring_fragment(path, "different")
            self.assertEqual(path.read_text(), "first")

    def test_advisory_cli_bad_data_returns_zero_not_pipeline_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "RESEARCH_PIPELINE_v2").mkdir()
            (root / "RESEARCH_PIPELINE_v2/corpus_ledger.json").write_text(json.dumps({"run_entities": 42}))
            result = q.main(["--tree-root", str(root), "--phase8-root", str(root / "phase8"),
                             "--week", "2026-W42", "--output-dir", str(root / "output")])
            self.assertEqual(result, 0)

    def test_malformed_json_reporting_does_not_touch_protected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipe = root / "RESEARCH_PIPELINE_v2"
            pipe.mkdir()
            ledger = pipe / "corpus_ledger.json"
            ledger.write_text("bad json")
            protected = pipe / "comparator_cloud_lean_verifier.py"
            protected.write_text("protected")
            records, _, gaps = q.collect_tree(root, root / "phase8")
            self.assertEqual(records, [])
            self.assertEqual(len(gaps), 1)
            self.assertEqual(ledger.read_text(), "bad json")
            self.assertEqual(protected.read_text(), "protected")

    def test_tree_adapter_dedup_only_exported_registered_main_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pipe = root / "RESEARCH_PIPELINE_v2"
            pipe.mkdir()
            note = root / "approved-note"
            ledger = {"run_entities": [{"entity_type": "RUN", "id": "Run-194", "status": "CERTIFIED", "certified_theorems": ["actual"]}],
                      "publication_entities": [{"id": "publication:methods-note:W:Run-194", "path": str(note)}]}
            (pipe / "corpus_ledger.json").write_text(json.dumps(ledger))
            digest = pipe / "science_release_queue/digests/a"
            digest.mkdir(parents=True)
            data = {"notes": [{"run_id": "Run-194", "path": str(note), "section": "MAIN_NOTES", "claim_table": [
                {"lean_theorem": "actual", "semantic_tier": "ROUTINE", "headline_eligible": True},
                {"lean_theorem": "not_exported", "semantic_tier": "SUBSTANTIVE", "headline_eligible": True}]}]}
            (digest / "DIGEST_MANIFEST.json").write_text(json.dumps(data))
            duplicate = digest.parent / "b"
            duplicate.mkdir()
            (duplicate / "DIGEST_MANIFEST.json").write_text(json.dumps(data))
            run = root / "science-engine/07_nightly_engine/compound research papers/Run-194-example"
            run.mkdir(parents=True)
            (run / "RUN_MANIFEST.json").write_text(json.dumps(self.row()))
            records, _, _ = q.collect_tree(root, root / "phase8")
            self.assertEqual(records[0]["semantic_tier"], "ROUTINE")
            self.assertEqual(records[0]["headline_claim_tier_counts"], {"ROUTINE": 1})


if __name__ == "__main__":
    unittest.main()
