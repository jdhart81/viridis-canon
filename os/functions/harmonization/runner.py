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
    costs = [float(v) for v in inputs["marginal_costs"]]
    overhead = opt(inputs, "command_overhead", 1.0)
    bandwidth = opt(inputs, "bandwidth", 0.0)
    ib_bound = opt(inputs, "ib_bound", 1.0)
    return {
        "shadow_price": to_fixed(js_max(*costs), 9),
        "wu_wei_dividend": to_fixed(overhead * len(costs) - overhead, 9),
        "decentralization_cheaper": overhead * len(costs) > overhead,
        "coordination_within_ib": bandwidth >= 0 and bandwidth <= ib_bound,
    }
