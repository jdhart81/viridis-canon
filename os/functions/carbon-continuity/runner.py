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
    a = num(inputs, "a")
    d = num(inputs, "d")
    r = num(inputs, "r")
    p = num(inputs, "p")
    loop_gain = r * p
    leakage_product = (1 - a) * (1 - d)
    threshold_met = loop_gain > leakage_product or is_close(loop_gain, leakage_product)
    living = r
    durable = 1 - a
    next_living = a * living + r * durable
    next_durable = p * living + d * durable
    return {
        "a": a, "d": d, "r": r, "p": p,
        "loop_gain": round12(loop_gain),
        "leakage_product": round12(leakage_product),
        "continuity_number": round12(js_div(loop_gain, leakage_product)),
        "threshold_met": threshold_met,
        "regime": "CONTINUITY_CAPABLE_WITHIN_MODEL" if threshold_met else "DEPLETING_WITHIN_MODEL",
        "witness_living": round12(living),
        "witness_durable": round12(durable),
        "witness_next_living": round12(next_living),
        "witness_next_durable": round12(next_durable),
        "witness_nondecreasing": threshold_met and next_living + 1e-12 >= living and next_durable + 1e-12 >= durable,
        "market_use": "decision_support_only",
        "formal_claim_type": "supplied_coefficient_threshold_evaluation",
        "market_claim_status": "MODEL_OUTPUT_ONLY",
        "empirically_calibrated": False,
        "underwriting_advice": False,
        "credit_quantity_tco2e": None,
        "claim_boundary": "Model-scoped decision support only. Supplied coefficients require separate empirical justification; this output is not a carbon credit, project rating, insurance price, underwriting decision, or causal field claim.",
    }
