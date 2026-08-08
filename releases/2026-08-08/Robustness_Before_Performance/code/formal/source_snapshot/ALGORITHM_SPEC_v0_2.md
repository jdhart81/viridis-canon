# Algorithm Specification

## 1. Decision-case model

A decision case contains:

- a **frame**: system boundary, stakeholders, scales, horizons, authority, and decision owner;
- **invariants**: conditions that must remain satisfied;
- **candidates**: static designs or adaptive policies;
- **scenarios**: disturbances, combinations, durations, aftershocks, and adversarial actions;
- **models and evidence**: data, simulations, expert judgments, causal assumptions, and provenance;
- **governance rules**: vetoes, quorum, appeal, review, and permitted aggregation;
- **budgets**: money, energy, material, time, complexity, labor, and ecological limits.

## 2. Scenario families

The minimum scenario library should include:

1. normal variability and forecast error;
2. single-component failure;
3. correlated and cascading failure;
4. capacity overload and resource scarcity;
5. prolonged disturbance and repeated aftershocks;
6. adversarial exploitation and strategic adaptation;
7. supplier, institution, or infrastructure loss;
8. distribution shift and regime change;
9. model-invalidating conditions;
10. recovery under degraded resources;
11. harms displaced outside the primary system boundary.

Scenario probabilities are optional. Mandatory stress scenarios may be included because they are ethically or strategically material even when probability estimates are unavailable.

## 3. Viability margin

For candidate policy \(p\), invariant \(i\), scenario \(s\), stakeholder or scale \(k\), and time \(t\), define a normalized viability margin:

\[
m_{i,k}(p,s,t) = \frac{o_{i,k}(p,s,t)-\theta_{i,k}}{q_{i,k}}
\]

where \(o\) is the modeled outcome, \(\theta\) is the required threshold, and \(q\) is a declared normalization quantity. The direction is reversed for measures where lower values are safer.

- \(m > 0\): headroom remains;
- \(m = 0\): at the viability boundary;
- \(m < 0\): invariant violation.

Normalization makes margins comparable enough for diagnostics but never makes distinct rights morally interchangeable.

## 4. Evaluation pipeline

### Phase A — Constitute the decision

1. Verify authority, ownership, and decision scope.
2. Register affected stakeholders, including parties outside the immediate boundary.
3. Define invariants, thresholds, horizons, scales, and whether each is non-compensable.
4. Record disagreements and minority definitions.
5. Reject the case as `HOLD` if authority or essential definitions are missing.

### Phase B — Build the system model

1. Map components, actors, resources, dependencies, feedback loops, and control paths.
2. Expand every response path through the typed dependency DAG and identify direct and transitive shared failure domains.
3. Mark irreversible actions and long-lived commitments.
4. Connect every model element to evidence and confidence.

### Phase C — Construct disturbances

1. Draw scenarios from all required families.
2. Combine failures that share causes or can cascade.
3. Add adversarial scenarios when actors can observe and exploit the system.
4. Add boundary challenges that test externalized harm.
5. Include scenarios designed to invalidate core model assumptions.

### Phase D — Evaluate candidates

For every candidate and scenario:

1. simulate or otherwise assess the state trajectory;
2. calculate viability margins;
3. measure degradation shape and failure containment;
4. measure detection, response, switching, and recovery times;
5. evaluate resource headroom and fallback capacity;
6. update the fragility ledger;
7. propagate model and evidence uncertainty;
8. store reproducible traces.

### Phase E — Apply gates

A candidate is inadmissible when it:

- violates a non-compensable invariant in a mandatory scenario;
- relies on unauthorized authority or an unavailable capability;
- exceeds a hard resource or ecological budget;
- exports a prohibited level of fragility or harm;
- depends on evidence below a required confidence floor;
- has no credible detection, fallback, or recovery path where one is required.

Gate failures are returned verbatim. They cannot be repaired by a weighted score.

### Phase F — Construct the robustness profile

For each admissible candidate, report at least:

- worst viability margin;
- share of scenarios and time within viability bounds;
- tail loss or conditional tail expectation where probabilities are defensible;
- degradation slope and cliff behavior;
- time to detection, containment, recovery, and adaptation;
- resource and capacity headroom;
- common-mode failure exposure;
- diversity of viable fallback pathways;
- reversibility and switching cost;
- modularity and blast radius;
- observability and diagnostic quality;
- externalized fragility by stakeholder, place, scale, and time;
- evidence confidence and sensitivity to contested assumptions;
- nominal performance and full lifecycle cost.

### Phase G — Compare without concealing trade-offs

1. Remove candidates dominated across the declared dimensions.
2. Present the Pareto frontier between viability, robustness, cost, performance, and distributional outcomes.
3. Calculate scenario regret and sensitivity to weights only as supporting evidence.
4. Prefer policies that remain admissible across a wide region of plausible assumptions.
5. Escalate irreducible value conflicts to the authorized governance process.
6. Return `HOLD` when evidence cannot distinguish candidates or no candidate passes.

### Phase H — Govern deployment and learning

1. Separate selection from execution; verify an explicit, scoped, active, unexpired authority lease before marking any action authorized.
2. Record authorization as `AUTHORIZED_NOT_EXECUTED`; the reference kernel never performs the action itself.
3. Start with the smallest reversible deployment proportional to the stakes.
4. Monitor leading indicators, invariant margins, and model drift.
5. Define trigger thresholds and pre-authorized fallback actions.
6. Run scheduled and surprise stress exercises.
7. Record near misses, unexpected adaptations, and harms outside the boundary.
8. Reconstitute the decision when the frame, authority, or disturbance environment changes materially.

## 5. Reference pseudocode

```text
function decide(case):
    constitution = validate_authority_frame_and_invariants(case)
    if not constitution.valid:
        return HOLD(constitution.missing_or_contested_fields)

    model = build_evidence_bound_system_model(case)
    scenarios = construct_and_challenge_scenarios(case, model)
    results = []

    for policy in case.candidates:
        traces = []
        for scenario in scenarios:
            trajectory = evaluate(policy, scenario, model)
            traces.append(assess_viability_recovery_and_spillovers(trajectory))

        gates = apply_noncompensable_gates(policy, traces, case.governance)
        profile = build_robustness_profile(policy, traces, gates)
        results.append({policy, traces, gates, profile})

    admissible = results where gates.pass
    if admissible is empty:
        return HOLD(all_gate_failures(results))

    frontier = pareto_frontier(admissible)
    sensitivity = challenge_models_weights_and_scenarios(frontier)
    recommendation = apply_authorized_decision_rule(frontier, sensitivity)

    return DECISION_RECORD(
        recommendation,
        frontier,
        rejected=results - admissible,
        monitoring=build_monitoring_and_fallback_policy(recommendation),
        dissent=case.dissent,
        provenance=case.evidence
    )
```

## 6. Anti-Goodhart protections

- No metric may be used without its failure modes and gaming incentives.
- Randomized audits and withheld stress scenarios test overfitting.
- Evaluation includes raw outcomes and distributions, not only scores.
- Metric definitions and weights are versioned and public to authorized reviewers.
- Domain experts, affected stakeholders, and adversarial reviewers can challenge the model independently.
- A candidate optimized specifically for the test suite is evaluated against novel and model-breaking scenarios.

## 7. Validation standard

The algorithm itself is not robust merely because its specification uses the word. It must be tested through:

- historical back-testing without retroactively changing the decision frame;
- prospective decisions with pre-registered expectations;
- comparison against competent baseline decision processes;
- red-team construction of omitted scenarios and shared dependencies;
- inter-rater analysis for judgment-heavy inputs;
- calibration of uncertainty statements;
- monitoring for distributional harm and fragility export after deployment.
