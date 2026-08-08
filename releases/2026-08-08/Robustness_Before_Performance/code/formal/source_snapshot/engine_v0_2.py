"""Deterministic reference implementation of the robustness decision kernel."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime
from statistics import fmean
from typing import Any, Iterable

from .canonical import canonical_hash
from .validation import validate_inputs


ENGINE_VERSION = "0.2.0"


def _rounded(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def _mean(values: Iterable[float]) -> float | None:
    materialized = list(values)
    return _rounded(fmean(materialized)) if materialized else None


def _viability(invariant: dict[str, Any], observed: float) -> tuple[bool, float]:
    threshold = float(invariant["threshold"])
    normalizer = float(invariant.get("normalization") or max(abs(threshold), 1.0))
    operator = invariant["operator"]

    if operator == ">=":
        return observed >= threshold, _rounded((observed - threshold) / normalizer)
    if operator == ">":
        return observed > threshold, _rounded((observed - threshold) / normalizer)
    if operator == "<=":
        return observed <= threshold, _rounded((threshold - observed) / normalizer)
    if operator == "<":
        return observed < threshold, _rounded((threshold - observed) / normalizer)
    if operator == "==":
        viable = math.isclose(observed, threshold, rel_tol=1e-9, abs_tol=1e-12)
        return viable, _rounded(-abs(observed - threshold) / normalizer)
    raise ValueError(f"Unsupported invariant operator: {operator}")


def _set_independence(dependency_sets: list[set[str]]) -> tuple[float | None, float | None]:
    if not dependency_sets:
        return None, None
    if len(dependency_sets) == 1:
        return 0.0, 1.0
    pairwise_independence: list[float] = []
    for left_index, left in enumerate(dependency_sets):
        for right in dependency_sets[left_index + 1 :]:
            union = left | right
            similarity = len(left & right) / len(union) if union else 1.0
            pairwise_independence.append(1.0 - similarity)

    all_dependencies = set().union(*dependency_sets)
    shared_by_all = set.intersection(*dependency_sets)
    common_mode = len(shared_by_all) / len(all_dependencies) if all_dependencies else 1.0
    return _mean(pairwise_independence), _rounded(common_mode)


def _dependency_closure(
    dependency_id: str,
    dependencies: dict[str, dict[str, Any]],
    memo: dict[str, set[str]],
) -> set[str]:
    if dependency_id in memo:
        return memo[dependency_id]
    closure = {dependency_id}
    for parent_id in dependencies[dependency_id]["parent_ids"]:
        closure.update(_dependency_closure(parent_id, dependencies, memo))
    memo[dependency_id] = closure
    return closure


def _fallback_profile(
    paths: list[dict[str, Any]],
    dependencies: dict[str, dict[str, Any]],
) -> tuple[dict[str, float | int | None], dict[str, Any]]:
    direct_sets = [set(path["dependency_ids"]) for path in paths]
    memo: dict[str, set[str]] = {}
    expanded_sets = [
        set().union(*(_dependency_closure(dependency_id, dependencies, memo) for dependency_id in path["dependency_ids"]))
        for path in paths
    ]
    direct_independence, direct_common_mode = _set_independence(direct_sets)
    expanded_independence, expanded_common_mode = _set_independence(expanded_sets)
    shared_failure_domains = sorted(set.intersection(*expanded_sets)) if expanded_sets else []
    direct_common_dependencies = sorted(set.intersection(*direct_sets)) if direct_sets else []
    path_closures = [
        {
            "path_id": path["path_id"],
            "direct_dependencies": sorted(direct),
            "expanded_failure_domains": sorted(expanded),
        }
        for path, direct, expanded in zip(paths, direct_sets, expanded_sets)
    ]
    return {
        "fallback_path_count": len(paths),
        "fallback_independence": expanded_independence,
        "common_mode_exposure": expanded_common_mode,
        "direct_fallback_independence": direct_independence,
        "direct_common_mode_exposure": direct_common_mode,
    }, {
        "direct_common_dependencies": direct_common_dependencies,
        "shared_failure_domains": shared_failure_domains,
        "path_dependency_closures": path_closures,
    }


def _candidate_evaluation(
    case: dict[str, Any],
    outcomes: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    candidate_id = candidate["id"]
    invariant_records = {record["id"]: record for record in case["invariants"]}
    mandatory_scenarios = {record["id"] for record in case["scenarios"] if record["mandatory"]}
    minimum_confidence = case["governance"].get("minimum_assessment_confidence", 0.0)

    assessments = sorted(
        (record for record in outcomes["assessments"] if record["candidate_id"] == candidate_id),
        key=lambda record: (
            record["scenario_id"],
            record["invariant_id"],
            record["stakeholder_id"],
            str(record["time_point"]),
        ),
    )
    margins: list[float] = []
    mandatory_margins: list[float] = []
    confidences: list[float] = []
    breaches: list[dict[str, Any]] = []
    gate_failures: list[dict[str, Any]] = []
    scenario_viability: dict[str, list[bool]] = defaultdict(list)

    for assessment in assessments:
        invariant = invariant_records[assessment["invariant_id"]]
        viable, margin = _viability(invariant, assessment["observed_value"])
        margins.append(margin)
        confidences.append(assessment["confidence"])
        scenario_viability[assessment["scenario_id"]].append(viable)
        if assessment["scenario_id"] in mandatory_scenarios:
            mandatory_margins.append(margin)

        if not viable:
            breach = {
                "scenario_id": assessment["scenario_id"],
                "invariant_id": assessment["invariant_id"],
                "stakeholder_id": assessment["stakeholder_id"],
                "time_point": assessment["time_point"],
                "observed_value": assessment["observed_value"],
                "operator": invariant["operator"],
                "threshold": invariant["threshold"],
                "margin": margin,
                "non_compensable": invariant["non_compensable"],
            }
            breaches.append(breach)
            if invariant["non_compensable"] and assessment["scenario_id"] in mandatory_scenarios:
                gate_failures.append({
                    "code": "NON_COMPENSABLE_BREACH",
                    "message": (
                        f"{assessment['invariant_id']} failed for {assessment['stakeholder_id']} "
                        f"in mandatory scenario {assessment['scenario_id']} at {assessment['time_point']}"
                    ),
                    "details": breach,
                })

        if assessment["scenario_id"] in mandatory_scenarios and assessment["confidence"] < minimum_confidence:
            gate_failures.append({
                "code": "ASSESSMENT_CONFIDENCE_BELOW_FLOOR",
                "message": (
                    f"Assessment confidence {assessment['confidence']} is below required floor "
                    f"{minimum_confidence} for {assessment['scenario_id']} / {assessment['invariant_id']}"
                ),
                "details": {
                    "scenario_id": assessment["scenario_id"],
                    "invariant_id": assessment["invariant_id"],
                    "stakeholder_id": assessment["stakeholder_id"],
                    "confidence": assessment["confidence"],
                },
            })

    externalities = sorted(
        (record for record in outcomes["externalities"] if record["candidate_id"] == candidate_id),
        key=lambda record: (record["scenario_id"], record["stakeholder_id"], record["description"]),
    )
    for externality in externalities:
        if externality["prohibited"]:
            gate_failures.append({
                "code": "PROHIBITED_EXTERNALITY",
                "message": (
                    f"Prohibited externality affects {externality['stakeholder_id']} "
                    f"in scenario {externality['scenario_id']}: {externality['description']}"
                ),
                "details": externality,
            })

    paths = sorted(
        (record for record in outcomes["fallback_paths"] if record["candidate_id"] == candidate_id),
        key=lambda record: record["path_id"],
    )
    dependency_records = {record["id"]: record for record in outcomes["dependencies"]}
    fallback_profile, dependency_ledger = _fallback_profile(paths, dependency_records)
    recovery = [record for record in outcomes["recovery"] if record["candidate_id"] == candidate_id]
    custom_metrics = {
        record["name"]: record["value"]
        for record in outcomes["candidate_metrics"]
        if record["candidate_id"] == candidate_id
    }

    mandatory_passes = [
        all(scenario_viability[scenario_id])
        for scenario_id in sorted(mandatory_scenarios)
    ]
    profile: dict[str, float | int | None] = {
        "worst_viability_margin": min(mandatory_margins) if mandatory_margins else None,
        "worst_exploratory_margin": min(margins) if margins else None,
        "mandatory_scenario_pass_rate": (
            sum(1 for passed in mandatory_passes if passed) / len(mandatory_passes)
            if mandatory_passes
            else None
        ),
        "mean_detection_time_hours": _mean(record["detection_time_hours"] for record in recovery),
        "mean_containment_time_hours": _mean(record["containment_time_hours"] for record in recovery),
        "mean_recovery_time_hours": _mean(record["recovery_time_hours"] for record in recovery),
        "mean_switching_cost": _mean(record["switching_cost"] for record in recovery),
        "irreversibility": _mean(record["irreversibility"] for record in recovery),
        # Externalities may measure unlike harms. Report the largest declared
        # normalized magnitude; preserve every raw entry in the fragility ledger.
        "maximum_externality_magnitude": max((record["magnitude"] for record in externalities), default=0.0),
        "minimum_assessment_confidence": min(confidences) if confidences else None,
        "mean_assessment_confidence": _mean(confidences),
    }
    profile.update(fallback_profile)
    profile.update(custom_metrics)

    return {
        "candidate_id": candidate_id,
        "candidate_name": candidate["name"],
        "admissible": not gate_failures,
        "gate_failures": sorted(gate_failures, key=lambda item: (item["code"], item["message"])),
        "breaches": breaches,
        "profile": profile,
        "fragility_ledger": {
            **dependency_ledger,
            "externalities": externalities,
            "irreversible_commitments": candidate.get("irreversible_commitments", []),
        },
    }


def _dominates(
    left: dict[str, Any],
    right: dict[str, Any],
    dimensions: list[dict[str, str]],
) -> bool:
    no_worse = True
    strictly_better = False
    for dimension in dimensions:
        name = dimension["name"]
        left_value = left["profile"][name]
        right_value = right["profile"][name]
        if dimension["direction"] == "maximize":
            no_worse = no_worse and left_value >= right_value
            strictly_better = strictly_better or left_value > right_value
        else:
            no_worse = no_worse and left_value <= right_value
            strictly_better = strictly_better or left_value < right_value
    return no_worse and strictly_better


def _pareto_frontier(
    evaluations: list[dict[str, Any]],
    dimensions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    return sorted(
        [
            candidate
            for candidate in evaluations
            if not any(
                other["candidate_id"] != candidate["candidate_id"]
                and _dominates(other, candidate, dimensions)
                for other in evaluations
            )
        ],
        key=lambda item: item["candidate_id"],
    )


def _select_candidate(
    frontier: list[dict[str, Any]],
    governance: dict[str, Any],
) -> tuple[str | None, list[str]]:
    rule = governance["selection_rule"]
    if rule == "pareto_only":
        return None, ["Authorized governance selection is required from the Pareto frontier"]
    if rule == "unique_pareto":
        if len(frontier) == 1:
            return frontier[0]["candidate_id"], []
        return None, ["Multiple non-dominated candidates remain"]
    if rule == "lexicographic":
        dimensions = governance["comparison_dimensions"]

        def vector(candidate: dict[str, Any]) -> tuple[float, ...]:
            return tuple(
                -float(candidate["profile"][dimension["name"]])
                if dimension["direction"] == "maximize"
                else float(candidate["profile"][dimension["name"]])
                for dimension in dimensions
            )

        vectors = {candidate["candidate_id"]: vector(candidate) for candidate in frontier}
        best_vector = min(vectors.values())
        winners = sorted(candidate_id for candidate_id, candidate_vector in vectors.items() if candidate_vector == best_vector)
        if len(winners) == 1:
            return winners[0], []
        return None, [f"Lexicographic comparison is tied: {', '.join(winners)}"]
    raise ValueError(f"Unsupported selection rule: {rule}")


def _scope_covers(scopes: list[str], requested: str) -> bool:
    for scope in scopes:
        if scope == "*" or scope == requested:
            return True
        if scope.endswith(".*") and requested.startswith(scope[:-1]):
            return True
    return False


def _action_boundary(case: dict[str, Any], selected: str | None) -> dict[str, Any]:
    policy = case.get("governance", {}).get("action_policy", {})
    lease = policy.get("authority_lease")
    reasons: list[str] = []
    authorized = True

    if selected is None:
        authorized = False
        reasons.append("No candidate has been selected")
    if policy.get("mode") != "bounded_execution":
        authorized = False
        reasons.append("Decision case is advisory-only")
    if "decision.execute" not in policy.get("authorized_actions", []):
        authorized = False
        reasons.append("Action policy does not authorize decision.execute")
    if not lease:
        authorized = False
        reasons.append("No authority lease is attached")
    else:
        if lease.get("state") != "ACTIVE":
            authorized = False
            reasons.append(f"Authority lease is {lease.get('state')}")
        if not _scope_covers(lease.get("scopes", []), "decision.execute"):
            authorized = False
            reasons.append("Authority lease does not cover decision.execute")
        evaluation_time = datetime.fromisoformat(case["evaluation_time"].replace("Z", "+00:00"))
        expires_at = datetime.fromisoformat(lease["expires_at"].replace("Z", "+00:00"))
        if evaluation_time >= expires_at:
            authorized = False
            reasons.append("Authority lease is expired at the declared evaluation time")

    return {
        "execution_status": "AUTHORIZED_NOT_EXECUTED" if authorized else "NOT_AUTHORIZED",
        "executed": False,
        "selected_candidate": selected,
        "authorized_actions": policy.get("authorized_actions", []) if authorized else [],
        "authority_lease_id": lease.get("lease_id") if lease else None,
        "reasons": sorted(set(reasons)),
    }


def evaluate_case(case: dict[str, Any], outcomes: dict[str, Any]) -> dict[str, Any]:
    """Evaluate one case and return a deterministic, hash-bound decision record."""

    input_hashes = {
        "case_sha256": canonical_hash(case),
        "outcomes_sha256": canonical_hash(outcomes),
    }
    issues = validate_inputs(case, outcomes)
    if issues:
        record: dict[str, Any] = {
            "engine_version": ENGINE_VERSION,
            "status": "HOLD",
            "case_id": case.get("case_id"),
            "case_version": case.get("version"),
            "evaluation_time": case.get("evaluation_time"),
            "input_hashes": input_hashes,
            "issues": issues,
            "evaluations": [],
            "admissible_candidates": [],
            "pareto_frontier": [],
            "selected_candidate": None,
            "action_boundary": {
                "execution_status": "NOT_AUTHORIZED",
                "executed": False,
                "selected_candidate": None,
                "authorized_actions": [],
                "authority_lease_id": None,
                "reasons": ["Decision case is structurally invalid"],
            },
        }
        record["record_sha256"] = canonical_hash(record)
        return record

    evaluations = [
        _candidate_evaluation(case, outcomes, candidate)
        for candidate in sorted(case["candidates"], key=lambda item: item["id"])
    ]
    admissible = [evaluation for evaluation in evaluations if evaluation["admissible"]]
    dimensions = case["governance"]["comparison_dimensions"]

    missing_dimensions: list[dict[str, str]] = []
    for evaluation in admissible:
        for dimension in dimensions:
            value = evaluation["profile"].get(dimension["name"])
            if value is None:
                missing_dimensions.append({
                    "code": "MISSING_COMPARISON_DIMENSION",
                    "message": f"{evaluation['candidate_id']} has no value for comparison dimension {dimension['name']}",
                    "path": f"/evaluations/{evaluation['candidate_id']}/profile/{dimension['name']}",
                })

    if not admissible:
        status = "NO_ADMISSIBLE_OPTION"
        frontier: list[dict[str, Any]] = []
        selected = None
        selection_notes = ["Every candidate failed at least one hard gate"]
    elif missing_dimensions:
        status = "HOLD"
        frontier = []
        selected = None
        selection_notes = ["A declared comparison dimension is missing"]
    else:
        frontier = _pareto_frontier(admissible, dimensions)
        selected, selection_notes = _select_candidate(frontier, case["governance"])
        status = "DECISION" if selected is not None else "DECISION_READY"

    record = {
        "engine_version": ENGINE_VERSION,
        "status": status,
        "case_id": case["case_id"],
        "case_version": case["version"],
        "evaluation_time": case["evaluation_time"],
        "model_id": outcomes["model_id"],
        "input_hashes": input_hashes,
        "issues": missing_dimensions,
        "decision_rule": case["governance"]["decision_rule"],
        "selection_rule": case["governance"]["selection_rule"],
        "evaluations": evaluations,
        "admissible_candidates": sorted(evaluation["candidate_id"] for evaluation in admissible),
        "pareto_frontier": [evaluation["candidate_id"] for evaluation in frontier],
        "selected_candidate": selected,
        "action_boundary": _action_boundary(case, selected),
        "selection_notes": selection_notes,
        "dissent": case.get("dissent", []),
    }
    record["record_sha256"] = canonical_hash(record)
    return record
