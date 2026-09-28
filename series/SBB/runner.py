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
    dimension = num(inputs, "dimension")
    rank = num(inputs, "rank")
    kappa = num(inputs, "kappa")
    captured = num(inputs, "captured_fraction")
    baseline = num(inputs, "baseline_cost")
    budget = num(inputs, "dissipation_budget")
    if rank > dimension:
        raise InputError("inputs.rank must be <= inputs.dimension")
    if rank == 0 and captured != 0:
        raise InputError("rank-zero channel requires captured_fraction=0")
    factor = 1 - js_div(kappa, 1 + kappa) * captured
    return {
        "directional_cost_factor": round12(factor),
        "directional_gain": round12(js_div(1, factor)),
        "directional_minimum_deadline": round12(js_div(baseline * factor, budget)),
        "baseline_minimum_deadline": round12(js_div(baseline, budget)),
        "full_subspace_gain": round12(1 + kappa),
        "worst_case_gain": round12(1 + kappa if rank == dimension else 1),
        "coverage_complete": rank == dimension,
        "scope": "whitened quadratic dissipation with a fixed orthogonal-projector channel",
    }
