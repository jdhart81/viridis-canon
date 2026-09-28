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
    theta = js_div(num(inputs, "sigma"), num(inputs, "delta_mu"))
    return {
        "nucleation_number": to_fixed(theta, 9),
        "critical_nucleus_n_star": to_fixed(js_pow(theta, 3), 9),
        "recommendation": "GREEN" if theta <= 0.5 else "AMBER" if theta <= 1 else "RED",
        "broadcast_fails": theta > 1,
    }
