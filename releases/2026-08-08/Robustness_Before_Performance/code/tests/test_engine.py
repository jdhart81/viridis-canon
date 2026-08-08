from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from robustness_engine.engine import evaluate_case
from robustness_engine.lineage import lineage_artifact_id
from robustness_engine.trajectory import analyze_trajectory
from robustness_engine.uncertainty import assess_interval_viability
from robustness_engine.validation import validate_inputs, validate_schema


ROOT = Path(__file__).resolve().parents[1]


def load_fixture(domain: str) -> tuple[dict, dict]:
    fixture_dir = ROOT / "examples" / domain
    case = json.loads((fixture_dir / "case.json").read_text(encoding="utf-8"))
    outcomes = json.loads((fixture_dir / "outcomes.json").read_text(encoding="utf-8"))
    return case, outcomes


def evaluations_by_id(record: dict) -> dict[str, dict]:
    return {evaluation["candidate_id"]: evaluation for evaluation in record["evaluations"]}


class RobustnessEngineTests(unittest.TestCase):
    def test_v02_formal_source_snapshot_matches_frozen_hashes(self) -> None:
        formal_dir = ROOT / "formal"
        snapshot_dir = formal_dir / "source_snapshot"
        manifest = json.loads((snapshot_dir / "MANIFEST.json").read_text(encoding="utf-8"))

        for filename, expected in manifest["files"].items():
            actual = hashlib.sha256((snapshot_dir / filename).read_bytes()).hexdigest()
            self.assertEqual(actual, expected, filename)
        request_hash = hashlib.sha256((formal_dir / "ARISTOTLE_FORGE_REQUEST.json").read_bytes()).hexdigest()
        self.assertEqual(request_hash, manifest["request_sha256"])

    def test_example_inputs_are_structurally_and_semantically_valid(self) -> None:
        for domain in ("municipal_heat", "cyber_identity"):
            case, outcomes = load_fixture(domain)
            self.assertEqual(validate_inputs(case, outcomes), [], domain)

    def test_decision_records_conform_to_output_contract(self) -> None:
        for domain in ("municipal_heat", "cyber_identity"):
            case, outcomes = load_fixture(domain)
            record = evaluate_case(case, outcomes)
            self.assertEqual(validate_schema(record, "decision-record.schema.json"), [], domain)

    def test_municipal_case_requires_governance_selection(self) -> None:
        case, outcomes = load_fixture("municipal_heat")
        record = evaluate_case(case, outcomes)
        evaluations = evaluations_by_id(record)

        self.assertEqual(record["status"], "DECISION_READY")
        self.assertEqual(record["pareto_frontier"], ["distributed_passive_network"])
        self.assertIsNone(record["selected_candidate"])
        self.assertTrue(evaluations["distributed_passive_network"]["admissible"])

        central_codes = {failure["code"] for failure in evaluations["central_cooling_centers"]["gate_failures"]}
        alert_codes = {failure["code"] for failure in evaluations["alert_only"]["gate_failures"]}
        self.assertIn("PROHIBITED_EXTERNALITY", central_codes)
        self.assertIn("NON_COMPENSABLE_BREACH", alert_codes)

    def test_cyber_case_selects_split_control_recovery(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        record = evaluate_case(case, outcomes)
        evaluations = evaluations_by_id(record)

        self.assertEqual(record["status"], "DECISION")
        self.assertEqual(record["selected_candidate"], "split_control_recovery")
        self.assertFalse(evaluations["single_optimized_path"]["admissible"])
        self.assertTrue(evaluations["shared_control_hot_standby"]["admissible"])
        self.assertTrue(evaluations["split_control_recovery"]["admissible"])
        self.assertEqual(record["action_boundary"]["execution_status"], "NOT_AUTHORIZED")
        self.assertFalse(record["action_boundary"]["executed"])

    def test_claim_states_remain_independent(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        record = evaluate_case(case, outcomes)
        summary = record["epistemic_summary"]["asserted_count_by_state"]

        self.assertEqual(record["engine_version"], "0.6.0")
        self.assertEqual(summary["NUMERICALLY_SUPPORTED"], 2)
        for state in (
            "ASSUMED",
            "HYPOTHESIZED",
            "REPRODUCED",
            "FORMALLY_PROVED",
            "EMPIRICALLY_SUPPORTED",
            "AUTHORIZED",
            "DEPLOYED",
            "OBSERVED",
        ):
            self.assertEqual(summary[state], 0)
        self.assertEqual(record["epistemic_summary"]["implication_policy"], "NONE")
        self.assertEqual(record["epistemic_summary"]["inference_edges"], [])
        self.assertIn("AUTHORIZED", record["claim_ledger"][0]["unasserted_states"])

    def test_fixture_intervals_produce_separated_robust_margins(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        record = evaluate_case(case, outcomes)
        evaluations = evaluations_by_id(record)

        self.assertEqual(record["comparison_mode"], "ROBUST_INTERVAL_DOMINANCE")
        self.assertEqual(
            record["dominance_rule"],
            "WORST_CASE_NO_WORSE_THAN_OTHER_BEST_CASE",
        )
        self.assertEqual(
            evaluations["shared_control_hot_standby"]["profile_intervals"]["worst_viability_margin"],
            {"lower": 0.003, "upper": 0.007, "provenance": "DERIVED_INTERVAL"},
        )
        self.assertEqual(
            evaluations["split_control_recovery"]["profile_intervals"]["worst_viability_margin"],
            {"lower": 0.018, "upper": 0.022, "provenance": "DERIVED_INTERVAL"},
        )
        self.assertEqual(record["selected_candidate"], "split_control_recovery")

    def test_interval_crossing_noncompensable_boundary_holds(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        for assessment in outcomes["assessments"]:
            if (
                assessment["candidate_id"] == "split_control_recovery"
                and assessment["scenario_id"] == "identity_dependency_exploit"
                and assessment["invariant_id"] == "authentication_availability"
            ):
                assessment["observed_interval"] = {
                    "lower": 0.94,
                    "upper": 0.98,
                    "basis": "Synthetic uncertainty crossing the safety threshold",
                }
        record = evaluate_case(case, outcomes)
        split = evaluations_by_id(record)["split_control_recovery"]

        self.assertEqual(record["status"], "HOLD")
        self.assertFalse(split["admissible"])
        self.assertEqual(split["gate_failures"], [])
        self.assertEqual(
            {hold["code"] for hold in split["uncertainty_holds"]},
            {"NON_COMPENSABLE_INTERVAL_UNCERTAIN"},
        )
        self.assertIn(
            "NON_COMPENSABLE_INTERVAL_UNCERTAIN",
            {issue["code"] for issue in record["issues"]},
        )
        self.assertEqual(record["action_boundary"]["execution_status"], "NOT_AUTHORIZED")
        self.assertEqual(validate_schema(record, "decision-record.schema.json"), [])

    def test_interval_bounds_must_contain_point(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        metric = next(
            record
            for record in outcomes["candidate_metrics"]
            if record["candidate_id"] == "shared_control_hot_standby"
            and record["name"] == "latency_ms"
        )
        metric["value_interval"] = {
            "lower": 36,
            "upper": 40,
            "basis": "Invalid test interval",
        }
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("POINT_OUTSIDE_INTERVAL", {issue["code"] for issue in record["issues"]})

    def test_interval_viability_covers_every_invariant_operator(self) -> None:
        cases = [
            (">=", 1.0, 1.2, 1.1, 1.3, "ROBUST_PASS"),
            (">", 1.0, 1.2, 1.0, 1.3, "UNCERTAIN"),
            ("<=", 1.0, 0.8, 0.7, 0.9, "ROBUST_PASS"),
            ("<", 1.0, 1.1, 1.0, 1.2, "ROBUST_FAIL"),
            ("==", 1.0, 1.0, 1.0, 1.0, "ROBUST_PASS"),
            ("==", 1.0, 1.0, 0.9, 1.1, "UNCERTAIN"),
            ("==", 1.0, 1.2, 1.1, 1.3, "ROBUST_FAIL"),
        ]
        for operator, threshold, point, lower, upper, expected in cases:
            with self.subTest(operator=operator, lower=lower, upper=upper):
                result = assess_interval_viability(
                    {
                        "operator": operator,
                        "threshold": threshold,
                        "normalization": 1.0,
                    },
                    point,
                    {"lower": lower, "upper": upper, "basis": "Operator test"},
                )
                self.assertEqual(result["viability_state"], expected)

    def test_equality_invariant_uses_exact_declared_boundary(self) -> None:
        exact = assess_interval_viability(
            {"operator": "==", "threshold": 1.0, "normalization": 1.0},
            1.0,
            None,
        )
        near_but_distinct = assess_interval_viability(
            {"operator": "==", "threshold": 1.0, "normalization": 1.0},
            1.0 + 1e-13,
            None,
        )

        self.assertEqual(exact["viability_state"], "ROBUST_PASS")
        self.assertEqual(near_but_distinct["viability_state"], "ROBUST_FAIL")

    def test_robust_dominance_refuses_overlapping_or_touching_metric_intervals(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["governance"]["comparison_dimensions"] = [
            {
                "name": "latency_ms",
                "direction": "minimize",
                "rationale": "Test interval-aware comparison in isolation",
            }
        ]
        metrics = {
            record["candidate_id"]: record
            for record in outcomes["candidate_metrics"]
            if record["name"] == "latency_ms"
        }
        metrics["shared_control_hot_standby"]["value_interval"] = {
            "lower": 30,
            "upper": 40,
            "basis": "Touching synthetic range",
        }
        metrics["split_control_recovery"]["value_interval"] = {
            "lower": 40,
            "upper": 48,
            "basis": "Touching synthetic range",
        }
        unresolved = evaluate_case(case, outcomes)

        self.assertEqual(unresolved["status"], "DECISION_READY")
        self.assertEqual(
            unresolved["pareto_frontier"],
            ["shared_control_hot_standby", "split_control_recovery"],
        )
        self.assertIsNone(unresolved["selected_candidate"])
        self.assertIn("interval-overlapping", unresolved["selection_notes"][0])

        metrics["shared_control_hot_standby"]["value_interval"] = {
            "lower": 30,
            "upper": 35,
            "basis": "Separated synthetic range",
        }
        separated = evaluate_case(case, outcomes)
        self.assertEqual(separated["status"], "DECISION")
        self.assertEqual(separated["pareto_frontier"], ["shared_control_hot_standby"])
        self.assertEqual(separated["selected_candidate"], "shared_control_hot_standby")

    def test_fixture_trajectories_report_coverage_and_recovery(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        record = evaluate_case(case, outcomes)
        evaluations = evaluations_by_id(record)
        shared = evaluations["shared_control_hot_standby"]
        split = evaluations["split_control_recovery"]
        single = evaluations["single_optimized_path"]

        self.assertEqual(shared["profile"]["trajectory_coverage_rate"], 0.25)
        self.assertEqual(split["profile"]["trajectory_coverage_rate"], 0.25)
        self.assertEqual(split["profile"]["trajectory_count"], 2)
        self.assertEqual(split["profile"]["unrecovered_trajectory_count"], 0)
        self.assertEqual(split["profile"]["maximum_possible_violation_span_hours"], 0)
        self.assertEqual(len(split["trajectory_analysis"]), 2)
        self.assertIn(
            "NON_COMPENSABLE_TRAJECTORY_BREACH",
            {failure["code"] for failure in single["gate_failures"]},
        )

    def test_trajectory_coverage_below_declared_floor_holds(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["governance"]["trajectory_policy"]["minimum_mandatory_coverage"] = 0.5
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn(
            "TRAJECTORY_COVERAGE_BELOW_FLOOR",
            {issue["code"] for issue in record["issues"]},
        )
        self.assertEqual(record["action_boundary"]["execution_status"], "NOT_AUTHORIZED")

    def test_trajectory_samples_must_be_strictly_ordered(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        outcomes["trajectories"][0]["samples"][1]["elapsed_hours"] = 0
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn(
            "NON_MONOTONIC_TRAJECTORY_TIME",
            {issue["code"] for issue in record["issues"]},
        )

    def test_trajectory_interval_crossing_boundary_holds(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        trajectory = next(
            item
            for item in outcomes["trajectories"]
            if item["candidate_id"] == "split_control_recovery"
            and item["invariant_id"] == "authentication_availability"
        )
        trajectory["samples"][1]["observed_interval"] = {
            "lower": 0.94,
            "upper": 0.98,
            "basis": "Synthetic boundary-crossing trajectory interval",
        }
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        split = evaluations_by_id(record)["split_control_recovery"]
        self.assertIn(
            "NON_COMPENSABLE_TRAJECTORY_UNCERTAIN",
            {hold["code"] for hold in split["uncertainty_holds"]},
        )

    def test_aftershock_and_shortfall_measures_are_explicit(self) -> None:
        analysis = analyze_trajectory(
            {"operator": ">=", "threshold": 0, "normalization": 1},
            {
                "candidate_id": "candidate",
                "scenario_id": "scenario",
                "invariant_id": "invariant",
                "stakeholder_id": "stakeholder",
                "scale": "system",
                "basis": "Synthetic alternating path",
                "samples": [
                    {"elapsed_hours": 0, "observed_value": 1, "evidence_refs": ["e"]},
                    {"elapsed_hours": 1, "observed_value": -1, "evidence_refs": ["e"]},
                    {"elapsed_hours": 2, "observed_value": 1, "evidence_refs": ["e"]},
                    {"elapsed_hours": 3, "observed_value": -1, "evidence_refs": ["e"]},
                ],
            },
        )

        self.assertEqual(analysis["aftershock_count"], 2)
        self.assertEqual(analysis["possible_violation_span_hours"], 3)
        self.assertEqual(analysis["robust_violation_span_hours"], 0)
        self.assertEqual(analysis["declared_linear_shortfall_area"], 1.5)
        self.assertIsNone(analysis["guaranteed_recovery_elapsed_hours"])

    def test_content_address_mismatch_holds_before_evaluation(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        outcomes["lineage"]["artifacts"][0]["manifest"]["version"] = "tampered"
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIsNone(record["lineage_summary"])
        self.assertIn(
            "LINEAGE_CONTENT_ADDRESS_MISMATCH",
            {issue["code"] for issue in record["issues"]},
        )

    def test_model_recall_cascades_to_adapter_and_holds(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        model_id = outcomes["lineage"]["model_artifact_id"]
        adapter_id = outcomes["lineage"]["adapter_artifact_ids"][0]
        outcomes["lineage"]["artifacts"][0]["recall"] = {
            "reason": "Synthetic model defect discovered during test",
            "authority": "Fixture review authority",
            "effective_at": "2026-08-05T00:00:00Z",
        }
        record = evaluate_case(case, outcomes)
        states = {
            artifact["artifact_id"]: artifact["effective_state"]
            for artifact in record["lineage_summary"]["artifacts"]
        }

        self.assertEqual(record["status"], "HOLD")
        self.assertFalse(record["lineage_summary"]["decision_usable"])
        self.assertEqual(states[model_id], "RECALLED")
        self.assertEqual(states[adapter_id], "QUARANTINED")
        self.assertEqual(record["lineage_summary"]["quarantined_artifact_ids"], [adapter_id])
        self.assertEqual(
            {issue["code"] for issue in record["issues"]},
            {"REQUIRED_ARTIFACT_RECALLED", "REQUIRED_ARTIFACT_QUARANTINED"},
        )
        self.assertEqual(validate_schema(record, "decision-record.schema.json"), [])

    def test_future_recall_is_visible_but_not_yet_effective(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        model_id = outcomes["lineage"]["model_artifact_id"]
        outcomes["lineage"]["artifacts"][0]["recall"] = {
            "reason": "Synthetic scheduled retirement",
            "authority": "Fixture review authority",
            "effective_at": "2026-08-07T00:00:00Z",
        }
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "DECISION")
        self.assertTrue(record["lineage_summary"]["decision_usable"])
        self.assertEqual(record["lineage_summary"]["pending_recall_artifact_ids"], [model_id])
        self.assertEqual(record["lineage_summary"]["recalled_artifact_ids"], [])
        self.assertEqual(record["lineage_summary"]["quarantined_artifact_ids"], [])

    def test_unrelated_recall_does_not_taint_required_lineage(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        manifest = {
            "dataset_id": "unused-synthetic-dataset",
            "version": "1.0.0",
        }
        artifact_id = lineage_artifact_id("DATASET", manifest, [])
        outcomes["lineage"]["artifacts"].append({
            "artifact_id": artifact_id,
            "kind": "DATASET",
            "manifest": manifest,
            "parent_ids": [],
            "recall": {
                "reason": "Unused synthetic dataset withdrawn",
                "authority": "Fixture review authority",
                "effective_at": "2026-08-05T00:00:00Z",
            },
        })
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "DECISION")
        self.assertTrue(record["lineage_summary"]["decision_usable"])
        self.assertEqual(record["lineage_summary"]["recalled_artifact_ids"], [artifact_id])
        self.assertEqual(record["lineage_summary"]["blocked_required_artifact_ids"], [])

    def test_claim_state_requires_matching_evidence_class(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["claims"][0]["assertions"][0]["state"] = "FORMALLY_PROVED"
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("CLAIM_STATE_SUPPORT_MISMATCH", {issue["code"] for issue in record["issues"]})

    def test_formal_proof_does_not_imply_authorization_or_deployment(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["evidence"].append({
            "id": "synthetic_formal_receipt",
            "claim": "A fixture theorem passed a synthetic formal audit",
            "source": "Unit-test receipt",
            "evidence_class": "FORMAL_PROOF_RECEIPT",
            "confidence": 1.0,
            "limitations": "Test-only evidence",
            "contested": False,
        })
        case["claims"].append({
            "id": "synthetic_formal_claim",
            "statement": "A fixture-level kernel property has a formal proof receipt.",
            "scope": "Unit-test theorem only",
            "assertions": [{
                "state": "FORMALLY_PROVED",
                "evidence_refs": ["synthetic_formal_receipt"],
                "basis": "The test supplies the exact evidence class required for this state.",
            }],
            "limitations": "No authorization, deployment, or observed outcome is asserted.",
        })
        record = evaluate_case(case, outcomes)
        summary = record["epistemic_summary"]["asserted_count_by_state"]

        self.assertEqual(record["status"], "DECISION")
        self.assertEqual(summary["FORMALLY_PROVED"], 1)
        self.assertEqual(summary["AUTHORIZED"], 0)
        self.assertEqual(summary["DEPLOYED"], 0)
        self.assertEqual(summary["OBSERVED"], 0)

    def test_active_bounded_authority_is_recorded_but_never_executed(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["governance"]["action_policy"] = {
            "mode": "bounded_execution",
            "authorized_actions": ["decision.execute"],
            "authority_lease": {
                "lease_id": "lease-cyber-001",
                "principal": "Chief information security officer",
                "state": "ACTIVE",
                "scopes": ["decision.execute"],
                "expires_at": "2026-08-07T00:00:00Z",
                "revocable": True,
            },
        }
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "DECISION")
        self.assertEqual(record["action_boundary"]["execution_status"], "AUTHORIZED_NOT_EXECUTED")
        self.assertEqual(record["action_boundary"]["authorized_actions"], ["decision.execute"])
        self.assertFalse(record["action_boundary"]["executed"])
        self.assertEqual(validate_schema(record, "decision-record.schema.json"), [])

    def test_expired_or_revoked_authority_fails_closed(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["governance"]["action_policy"] = {
            "mode": "bounded_execution",
            "authorized_actions": ["decision.execute"],
            "authority_lease": {
                "lease_id": "lease-cyber-expired",
                "principal": "Chief information security officer",
                "state": "ACTIVE",
                "scopes": ["decision.*"],
                "expires_at": "2026-08-05T00:00:00Z",
                "revocable": True,
            },
        }
        expired = evaluate_case(case, outcomes)
        self.assertEqual(expired["action_boundary"]["execution_status"], "NOT_AUTHORIZED")
        self.assertIn("Authority lease is expired at the declared evaluation time", expired["action_boundary"]["reasons"])

        case["governance"]["action_policy"]["authority_lease"]["expires_at"] = "2026-08-07T00:00:00Z"
        case["governance"]["action_policy"]["authority_lease"]["state"] = "REVOKED"
        revoked = evaluate_case(case, outcomes)
        self.assertEqual(revoked["action_boundary"]["execution_status"], "NOT_AUTHORIZED")
        self.assertIn("Authority lease is REVOKED", revoked["action_boundary"]["reasons"])

    def test_invalid_evaluation_time_holds_without_evaluating_authority(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        case["evaluation_time"] = "not-a-timestamp"
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("INVALID_DATETIME", {issue["code"] for issue in record["issues"]})
        self.assertEqual(record["action_boundary"]["execution_status"], "NOT_AUTHORIZED")

    def test_shared_dependencies_reduce_fallback_credit(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        evaluations = evaluations_by_id(evaluate_case(case, outcomes))
        shared = evaluations["shared_control_hot_standby"]["profile"]
        split = evaluations["split_control_recovery"]["profile"]

        self.assertLess(shared["fallback_independence"], split["fallback_independence"])
        self.assertGreater(shared["common_mode_exposure"], split["common_mode_exposure"])
        self.assertEqual(shared["direct_fallback_independence"], 1.0)
        self.assertEqual(shared["direct_common_mode_exposure"], 0.0)
        self.assertEqual(
            evaluations["shared_control_hot_standby"]["fragility_ledger"]["direct_common_dependencies"],
            [],
        )
        self.assertEqual(
            evaluations["shared_control_hot_standby"]["fragility_ledger"]["shared_failure_domains"],
            ["provider_global_control_plane"],
        )

    def test_dependency_cycle_holds_case(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        dependencies = {record["id"]: record for record in outcomes["dependencies"]}
        dependencies["provider_global_control_plane"]["parent_ids"] = ["region_a_runtime"]
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("DEPENDENCY_CYCLE", {issue["code"] for issue in record["issues"]})

    def test_unknown_fallback_dependency_holds_case(self) -> None:
        case, outcomes = load_fixture("municipal_heat")
        outcomes["fallback_paths"][0]["dependency_ids"].append("unregistered_control_plane")
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("UNKNOWN_DEPENDENCY", {issue["code"] for issue in record["issues"]})

    def test_high_nominal_performance_cannot_compensate_for_hard_failure(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        record = evaluate_case(case, outcomes)
        evaluations = evaluations_by_id(record)

        self.assertEqual(evaluations["single_optimized_path"]["profile"]["latency_ms"], 25)
        self.assertFalse(evaluations["single_optimized_path"]["admissible"])
        self.assertNotIn("single_optimized_path", record["pareto_frontier"])

    def test_missing_mandatory_evidence_holds_case(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        outcomes["assessments"].pop()
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("MISSING_MANDATORY_ASSESSMENT", {issue["code"] for issue in record["issues"]})

    def test_missing_authority_holds_case(self) -> None:
        case, outcomes = load_fixture("municipal_heat")
        case["governance"]["authorities"] = []
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "HOLD")
        self.assertIn("SCHEMA_ERROR", {issue["code"] for issue in record["issues"]})

    def test_no_admissible_option_is_distinct_from_hold(self) -> None:
        case, outcomes = load_fixture("municipal_heat")
        for assessment in outcomes["assessments"]:
            if (
                assessment["candidate_id"] == "distributed_passive_network"
                and assessment["scenario_id"] == "grid_outage_heatwave"
                and assessment["invariant_id"] == "high_risk_health_index"
            ):
                assessment["observed_value"] = 1.2
                assessment["observed_interval"] = {
                    "lower": 1.1,
                    "upper": 1.3,
                    "basis": "Synthetic definitely failing range",
                }
        record = evaluate_case(case, outcomes)

        self.assertEqual(record["status"], "NO_ADMISSIBLE_OPTION")
        self.assertEqual(record["admissible_candidates"], [])

    def test_identical_inputs_produce_identical_record(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        first = evaluate_case(case, outcomes)
        second = evaluate_case(copy.deepcopy(case), copy.deepcopy(outcomes))

        self.assertEqual(first, second)
        self.assertEqual(first["record_sha256"], second["record_sha256"])

    def test_input_order_does_not_change_decision(self) -> None:
        case, outcomes = load_fixture("cyber_identity")
        original = evaluate_case(case, outcomes)

        reordered_case = copy.deepcopy(case)
        reordered_outcomes = copy.deepcopy(outcomes)
        reordered_case["candidates"].reverse()
        reordered_case["scenarios"].reverse()
        reordered_case["claims"].reverse()
        reordered_outcomes["assessments"].reverse()
        reordered_outcomes["fallback_paths"].reverse()
        reordered_outcomes["recovery"].reverse()
        reordered_outcomes["trajectories"].reverse()
        reordered_outcomes["externalities"].reverse()
        reordered_outcomes["candidate_metrics"].reverse()
        reordered_outcomes["lineage"]["artifacts"].reverse()
        reordered = evaluate_case(reordered_case, reordered_outcomes)

        self.assertEqual(original["status"], reordered["status"])
        self.assertEqual(original["selected_candidate"], reordered["selected_candidate"])
        self.assertEqual(original["pareto_frontier"], reordered["pareto_frontier"])
        self.assertEqual(original["evaluations"], reordered["evaluations"])
        self.assertEqual(original["claim_ledger"], reordered["claim_ledger"])
        self.assertEqual(original["lineage_summary"], reordered["lineage_summary"])


if __name__ == "__main__":
    unittest.main()
