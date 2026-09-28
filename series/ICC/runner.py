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
    ceiling = num(inputs, "conditional_task_entropy") + num(inputs, "proxy_leakage_budget")
    declared = opt(inputs, "task_information_ceiling")
    effective = ceiling if declared is None else js_min(ceiling, declared)
    observed = opt(inputs, "observed_task_information")
    return {
        "invariance_information_ceiling": round12(ceiling),
        "effective_information_ceiling": round12(effective),
        "observed_task_information": None if observed is None else round12(observed),
        "within_declared_ceiling": None if observed is None else observed <= effective + 1e-12,
        "ceiling_slack": None if observed is None else round12(effective - observed),
        "scope": "finite-variable mutual information with a separately justified leakage budget",
    }
