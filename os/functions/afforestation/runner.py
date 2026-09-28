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
    prep = opt(inputs, "prep", 1.0)
    rate = opt(inputs, "rate", 0.0)
    rate_max = opt(inputs, "rate_max", 1.0)
    return {
        "optimal_density": to_fixed(js_pow(js_div(prep * num(inputs, "delta_mu"), num(inputs, "sigma")), 3), 9),
        "site_prep_multiplier": to_fixed(js_pow(prep, 3), 6),
        "seeding_within_ib_ceiling": rate >= 0 and rate <= rate_max,
    }
