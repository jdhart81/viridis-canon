#!/usr/bin/env python3
"""Adversarial gate for Run 119, written before the paper.

Preregistered hypotheses
------------------------
H1. For beta > 0, resetting a maximum-age component uniquely minimizes the
    next-step log-sum-exp potential when the maximum is unique.
H2. The locked META transition moves the live staleness sum from 139 to 155 and
    makes area 13 the unique severe-starvation choice for Run 120.
H3. The v1 policy is not a total executable selector because it does not define
    ``scoring_staleness`` or deterministic tie-breaking.
H4. The proposal leaves the actual Run 119/120 choices unchanged while making
    an adversarial tied state deterministic.

Falsifiers
----------
Any exact or randomized counterexample to H1; any beta in the registered sweep
that changes Run 120 away from area 13; a present policy definition for either
missing field; or proposal drift on the actual two-run replay.

The checks are finite computational evidence, not formal proof.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from pathlib import Path


SEED = 11920260804
TOL = 2e-12
POLICY_PATH = Path(__file__).with_name("NIGHTLY_SELECTION_POLICY_v1.json")
STATE_PATH = Path(__file__).with_name("INPUT_STATE_SNAPSHOT.json")
PROPOSAL_PATH = Path(__file__).with_name("POLICY_PROPOSAL_v1.1.json")
EXPECTED_POLICY_HASH = "fdee0f1dff1a92ebe42ef7413a98b39b771b8759ad385ba3fb037898935cd09e"
EXPECTED_STATE_HASH = "f329b1a6d39e52c154a5b97aa9166512ed0c64d106396f9f7763ae82c3a9286e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logsumexp(values: list[float]) -> float:
    m = max(values)
    return m + math.log(sum(math.exp(x - m) for x in values))


def free_energy(ages: list[int], beta: float) -> float:
    if beta <= 0:
        raise ValueError("beta must be positive")
    return logsumexp([beta * age for age in ages]) / beta


def serve(ages: list[int], selected: int) -> list[int]:
    out = [age + 1 for age in ages]
    out[selected] = 0
    return out


def meta_step(ages: list[int]) -> list[int]:
    return [age + 1 for age in ages]


def score(area: dict) -> float:
    return (
        float(area["weight"]) * int(area["staleness"])
        + float(area.get("standing_flags", 0.0))
        + float(area.get("coverage_relief", 0.0))
    )


def severe_candidates(areas: list[dict], threshold: int) -> list[dict]:
    return [a for a in areas if int(a["staleness"]) >= threshold]


def proposed_severe_choice(areas: list[dict], threshold: int) -> dict | None:
    candidates = severe_candidates(areas, threshold)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda a: (-int(a["staleness"]), -score(a), str(a["id"])),
    )


class Gate:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, condition: bool, detail: str) -> None:
        if condition:
            self.passed += 1
            print(f"PASS {self.passed + self.failed:02d} | {name} | {detail}")
        else:
            self.failed += 1
            print(f"FAIL {self.passed + self.failed:02d} | {name} | {detail}")


def main() -> int:
    print("RUN 119 ADVERSARIAL GATE")
    print(f"seed={SEED}")
    print(f"tolerance={TOL:.1e}")
    print("hypotheses=H1 one-step free-energy certificate; H2 locked transition; H3 executable-policy audit; H4 no-drift proposal replay")
    print("falsifier=any counterexample, next-choice drift, or explicit policy definition contradicting H3")

    gate = Gate()
    rng = random.Random(SEED)
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    proposal = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))

    gate.check(
        "locked input hashes",
        sha256(POLICY_PATH) == EXPECTED_POLICY_HASH and sha256(STATE_PATH) == EXPECTED_STATE_HASH,
        f"policy={sha256(POLICY_PATH)} state={sha256(STATE_PATH)}",
    )
    gate.check(
        "proposal is non-adopting",
        proposal["status"] == "PROPOSAL_ONLY_NOT_ADOPTED"
        and proposal["base_policy_sha256"] == EXPECTED_POLICY_HASH,
        f"status={proposal['status']}",
    )
    gate.check(
        "machine checksum",
        sum(int(a["staleness"]) for a in state["areas"]) == state["sum_staleness"] == 139,
        f"sum={sum(int(a['staleness']) for a in state['areas'])}",
    )
    directives = [d for d in state["locked_directives"] if d.get("run") == 119]
    gate.check(
        "locked Run 119 directive",
        directives == [{"run": 119, "kind": "meta", "area_id": None, "lens": "Thermodynamic", "reason": "scheduled_meta_policy_review_no_self_adoption"}],
        f"directives={directives}",
    )

    # Exact pairwise selection identity on a hand-auditable state.
    ages = [2, 7, 4]
    beta = 0.7
    zj = [sum(math.exp(beta * x) for x in serve(ages, j)) for j in range(3)]
    exact_gap = math.exp(beta) * (math.exp(beta * ages[1]) - math.exp(beta * ages[0]))
    observed_gap = zj[0] - zj[1]
    gate.check(
        "exact reset-gap identity",
        math.isclose(observed_gap, exact_gap, rel_tol=TOL, abs_tol=TOL),
        f"observed={observed_gap:.12e} exact={exact_gap:.12e}",
    )
    gate.check(
        "hand-case maximum age minimizes potential",
        zj[1] == min(zj),
        f"post_reset_Z={[f'{z:.6f}' for z in zj]}",
    )

    exhaustive_cases = 0
    exhaustive_failures = 0
    for n in range(2, 7):
        for state_ages in itertools.product(range(5), repeat=n):
            maxima = {i for i, age in enumerate(state_ages) if age == max(state_ages)}
            for b in (0.05, 0.3, 1.0, 2.0):
                energies = [free_energy(serve(list(state_ages), j), b) for j in range(n)]
                minimizers = {j for j, val in enumerate(energies) if abs(val - min(energies)) <= TOL}
                exhaustive_cases += 1
                if minimizers != maxima:
                    exhaustive_failures += 1
    gate.check(
        "exhaustive small-state certificate",
        exhaustive_failures == 0,
        f"cases={exhaustive_cases} failures={exhaustive_failures}",
    )

    random_cases = 10_000
    random_failures = 0
    worst_margin = math.inf
    for _ in range(random_cases):
        n = rng.randint(2, 32)
        state_ages = [rng.randint(0, 80) for _ in range(n)]
        # Force a unique maximum so strictness can be tested.
        winner = rng.randrange(n)
        state_ages[winner] = max(state_ages) + 1
        b = 10 ** rng.uniform(-3, 0.4)
        vals = [free_energy(serve(state_ages, j), b) for j in range(n)]
        ordered = sorted(vals)
        margin = ordered[1] - ordered[0]
        worst_margin = min(worst_margin, margin)
        if vals.index(min(vals)) != winner or margin <= 0:
            random_failures += 1
    gate.check(
        "random unique-maximum strictness",
        random_failures == 0,
        f"cases={random_cases} failures={random_failures} min_margin={worst_margin:.3e}",
    )

    tie_ages = [11, 4, 11, 0]
    tie_vals = [free_energy(serve(tie_ages, j), 0.9) for j in range(4)]
    tie_min = min(tie_vals)
    tie_set = {j for j, val in enumerate(tie_vals) if abs(val - tie_min) <= TOL}
    gate.check(
        "tie negative control",
        tie_set == {0, 2},
        f"minimizers={sorted(tie_set)} maxima={[0, 2]}",
    )

    beta_zero_energies = [sum(math.exp(0.0 * x) for x in serve(ages, j)) for j in range(3)]
    gate.check(
        "beta-zero degeneracy negative control",
        beta_zero_energies == [3.0, 3.0, 3.0],
        f"Z_0={beta_zero_energies}",
    )

    bounds_ok = True
    bound_slack = []
    for b in (0.1, 1.0, 10.0, 100.0):
        sample = [3, 22, 5, 14, 9]
        f = free_energy(sample, b)
        lo = max(sample)
        hi = lo + math.log(len(sample)) / b
        bounds_ok &= lo - TOL <= f <= hi + TOL
        bound_slack.append(f - lo)
    gate.check(
        "stable thermal-limit bounds",
        bounds_ok and all(x >= -TOL for x in bound_slack),
        f"F_beta-max={[f'{x:.3e}' for x in bound_slack]}",
    )

    nonmax_worse = True
    for b in (1e-6, 1e-3, 0.1, 1.0, 10.0, 100.0):
        sample = [7, 22, 13, 0]
        best = free_energy(serve(sample, 1), b)
        nonmax_worse &= all(best < free_energy(serve(sample, j), b) for j in (0, 2, 3))
    gate.check(
        "nonmaximum reset is strictly worse",
        nonmax_worse,
        "beta sweep=1e-6..100 unique maximum age=22",
    )

    live_ages = [int(a["staleness"]) for a in state["areas"]]
    post_meta_ages = meta_step(live_ages)
    gate.check(
        "META transition checksum",
        sum(post_meta_ages) == 155 and all(b == a + 1 for a, b in zip(live_ages, post_meta_ages)),
        f"pre_sum={sum(live_ages)} post_sum={sum(post_meta_ages)} resets=0",
    )
    max_age = max(post_meta_ages)
    max_ids = [state["areas"][i]["id"] for i, age in enumerate(post_meta_ages) if age == max_age]
    gate.check(
        "Run 120 unique severe-starvation area",
        max_age == 22 and max_ids == ["13"],
        f"max_age={max_age} ids={max_ids}",
    )

    live_beta_choice_ok = True
    for b in (1e-6, 1e-3, 0.1, 1.0, 10.0, 100.0):
        vals = [free_energy(serve(post_meta_ages, j), b) for j in range(16)]
        live_beta_choice_ok &= vals.index(min(vals)) == 12
    gate.check(
        "Run 120 choice invariant across temperature",
        live_beta_choice_ok,
        "all beta choose zero-based index 12 / area 13",
    )

    post_meta_areas = []
    for area, age in zip(state["areas"], post_meta_ages):
        item = dict(area)
        item["staleness"] = age
        post_meta_areas.append(item)
    threshold = int(policy["thresholds"]["severe_starvation"])
    proposed_choice = proposed_severe_choice(post_meta_areas, threshold)
    gate.check(
        "proposal actual-state replay",
        proposed_choice is not None and proposed_choice["id"] == "13",
        f"threshold={threshold} selected={None if proposed_choice is None else proposed_choice['id']}",
    )

    formula = str(policy.get("score", {}).get("formula", ""))
    policy_text = json.dumps(policy, sort_keys=True).lower()
    scoring_defined = "scoring_staleness" in policy.get("score", {}) and policy["score"].get("scoring_staleness")
    tie_defined = "tie_break" in policy_text or "tiebreak" in policy_text
    gate.check(
        "undefined scoring_staleness detected",
        "scoring_staleness" in formula and not scoring_defined,
        f"formula={formula!r} explicit_definition={bool(scoring_defined)}",
    )
    gate.check(
        "missing deterministic tie-break detected",
        not tie_defined,
        f"tie_definition_present={tie_defined}",
    )

    adversarial_areas = [dict(a) for a in post_meta_areas]
    adversarial_areas[11]["staleness"] = 22  # area 12 tied with area 13
    current_candidate_ids = [a["id"] for a in severe_candidates(adversarial_areas, threshold)]
    total_choice = proposed_severe_choice(adversarial_areas, threshold)
    gate.check(
        "adversarial tie exposes partial selector",
        current_candidate_ids == ["12", "13"] and total_choice is not None,
        f"current_candidates={current_candidate_ids} proposal={total_choice['id'] if total_choice else None}",
    )
    gate.check(
        "proposal deterministically resolves tie",
        total_choice is not None and total_choice["id"] in current_candidate_ids,
        f"selected={None if total_choice is None else total_choice['id']} rule=age,score,area_id",
    )

    lens_order = policy["lens_policy"]["order"]
    next_lens = lens_order[(lens_order.index("Thermodynamic") + 1) % len(lens_order)]
    distance = 120 - int(next(a["last_run"] for a in state["areas"] if a["id"] == "13"))
    gate.check(
        "Run 120 lens and combination guard",
        next_lens == "Stewardship" and distance >= int(policy["thresholds"]["combination_guard_runs"]),
        f"lens={next_lens} area13_distance={distance}",
    )

    # Model limits: unequal service costs invalidate the unqualified max-age rule.
    unequal_cost_ages = [10, 9]
    costs = [100.0, 1.0]
    b = 1.0
    utility = [
        free_energy(unequal_cost_ages, b) - free_energy(serve(unequal_cost_ages, j), b) - costs[j]
        for j in range(2)
    ]
    gate.check(
        "unequal-cost scope negative control",
        utility[1] > utility[0],
        f"net_benefit={[f'{u:.3f}' for u in utility]} max-age_not_optimal_when_costed",
    )

    print()
    print(f"SUMMARY: {gate.passed} PASS / {gate.failed} FAIL")
    if gate.failed:
        print("STATUS: NUMERICAL_GATE_FAIL")
        print("INTERPRETATION: at least one preregistered invariant failed; do not advance state.")
        return 1
    print("STATUS: NUMERICAL_GATE_PASS")
    print("INTERPRETATION: finite exact/exhaustive/randomized checks support a one-step equal-cost certificate and expose two policy-schema gaps; no formal proof, long-run optimality, productivity gain, novelty, or adoption is established.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
