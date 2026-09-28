"""Reference runner for the Viridis OS function declared in function.json (stdlib only).

Ported without numerical change from viridis-conservation-app@398b177
src/lib/conservationDecisionRuntime.ts (WS-20 parity port). Arithmetic uses
viridis_fn's JavaScript-number semantics so receipts are bit-for-bit identical
to the product runtime.
"""
from viridis_fn import (  # noqa: F401
    InputError, KB, LN2, is_close, js_cosh, js_div, js_log, js_max, js_min, js_pow,
    js_sqrt, js_sum, lexically_less, locale_usd, num, opt, round12, to_fixed,
)

def run(inputs):
    budget = num(inputs, "budget_usd")
    evidence_ready = inputs["declared_evidence_ready"]
    price_authorized = inputs["declared_price_authorized"]
    assets = inputs["assets"]
    seen = set()
    for index, asset in enumerate(assets):
        if not asset["asset_id"].strip(" \t\n\r\x0b\x0c\u00a0\ufeff\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"):
            raise InputError(f"inputs.assets[{index}].asset_id must be a non-empty string")
        if asset["asset_id"] in seen:
            raise InputError(f"inputs.assets[{index}].asset_id must be unique")
        seen.add(asset["asset_id"])
    rows = []
    for asset in assets:
        row = dict(asset)
        row["benefit"] = float(asset["gross_avoided_value_usd"]) - float(asset["embodied_transition_cost_usd"])
        rows.append(row)
    cap = [float(a["capital_cost_usd"]) for a in rows]
    fric = [float(a["transition_friction_usd"]) for a in rows]
    ben = [a["benefit"] for a in rows]

    def allocations(shadow_price):
        return [js_min(1, js_max(0, js_div(ben[i] - shadow_price * cap[i], fric[i]))) for i in range(len(rows))]

    unconstrained = allocations(0.0)
    unconstrained_spend = js_sum(cap[i] * unconstrained[i] for i in range(len(rows)))
    shadow_price = 0.0
    fractions = unconstrained
    allocation_status = "BUDGET_SLACK"
    if unconstrained_spend > budget + 1e-9:
        lower = 0.0
        upper = js_max(*[js_max(js_div(ben[i], cap[i]), 0) for i in range(len(rows))])
        for _ in range(160):
            midpoint = (lower + upper) / 2
            alloc = allocations(midpoint)
            spend = js_sum(cap[i] * alloc[i] for i in range(len(rows)))
            if spend > budget:
                lower = midpoint
            else:
                upper = midpoint
        shadow_price = upper
        fractions = allocations(shadow_price)
        allocation_status = "BUDGET_BINDING"
    budget_used = js_sum(cap[i] * fractions[i] for i in range(len(rows)))
    objective = 0.0
    for i in range(len(rows)):
        # JS: sum + b*f - 0.5*c*f**2 evaluates as (sum + b*f) - 0.5*c*f**2
        objective = (objective + ben[i] * fractions[i]) - 0.5 * fric[i] * js_pow(fractions[i], 2)
    coordinate_kkt = True
    allocation_rows = []
    for i, asset in enumerate(rows):
        fraction = fractions[i]
        gradient = ben[i] - fric[i] * fraction - shadow_price * cap[i]
        if fraction > 1e-9 and fraction < 1 - 1e-9:
            coordinate_ok = abs(gradient) <= 1e-9
        elif fraction <= 1e-9:
            coordinate_ok = gradient <= 1e-9
        else:
            coordinate_ok = gradient >= -1e-9
        coordinate_kkt = coordinate_kkt and coordinate_ok
        allocation_rows.append({
            "asset_id": asset["asset_id"],
            "net_declared_benefit_usd": round12(ben[i]),
            "allocation_fraction": round12(fraction),
            "allocated_capital_usd": round12(cap[i] * fraction),
            "objective_contribution_usd": round12(ben[i] * fraction - 0.5 * fric[i] * js_pow(fraction, 2)),
            "stationarity_residual_usd": round12(gradient),
        })
    declared_ready = bool(evidence_ready) and bool(price_authorized)
    any_allocation = any(f > 1e-9 for f in fractions)
    action_state = "HOLD" if not declared_ready else "REDESIGN" if not any_allocation else "INVESTIGATE"
    if not declared_ready:
        action_summary = "Hold any real allocation until evidence readiness and price authority are independently confirmed."
    elif not any_allocation:
        action_summary = "Redesign the declared alternatives; none has positive allocation under this scenario."
    else:
        action_summary = "Advance this scenario to accountable evidence review before any capital commitment."
    budget_feasible = budget_used <= budget + 1e-9
    complementary = shadow_price <= 1e-9 or abs(budget_used - budget) <= 1e-9
    return {
        "allocation_status": allocation_status,
        "budget_shadow_price": round12(shadow_price),
        "budget_used_usd": round12(budget_used),
        "budget_remaining_usd": round12(js_max(0, budget - budget_used)),
        "scenario_objective_value_usd": round12(objective),
        "assets": allocation_rows,
        "implementation_checks": {
            "box_feasible": all(f >= -1e-9 and f <= 1 + 1e-9 for f in fractions),
            "budget_feasible": budget_feasible,
            "coordinate_kkt_conditions": coordinate_kkt,
            "complementary_budget_regime": complementary,
            "passed": budget_feasible and coordinate_kkt and complementary,
        },
        "formal_claims": [
            "clipped allocation remains between zero and one",
            "interior coordinates satisfy the declared stationarity identity",
            "increasing embodied transition burden lowers declared benefit",
        ],
        "formal_scope": "The Comparator certificate covers the listed algebraic Run-139 claims, not the input values or a real-world allocation decision.",
        "empirical_status": "USER_SUPPLIED_UNVALIDATED",
        "decision_lens": {
            "ecologicalState": "DECLARED_BURDEN_SCENARIO",
            "ecologicalSummary": "The result compares user-supplied avoided and embodied burden values; it does not measure ecological effects.",
            "evidenceState": "DECLARED_READY_UNVERIFIED" if declared_ready else "AUTHORITY_OR_EVIDENCE_MISSING",
            "businessState": "CAPITAL_SCENARIO_QUANTIFIED",
            "businessSummary": f"The model allocates ${locale_usd(round12(budget_used))} of the declared ${locale_usd(round12(budget))} budget across {len(rows)} divisible alternatives.",
            "optionsState": "MODEL_RANKED_ALTERNATIVES",
            "optionsSummary": "Compare the fractional allocations, shadow price, and zero-allocation alternatives within the declared one-budget model.",
            "actionState": action_state,
            "actionSummary": action_summary,
        },
        "claim_boundary": "Scenario-only allocation for fixed, user-supplied coefficients. No appraisal, investment advice, empirical validation, price authorization, credit quantity, causal impact, or certification is produced.",
    }
