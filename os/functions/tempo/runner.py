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
    haste = num(inputs, "haste_cost")
    neglect = num(inputs, "neglect_cost")
    cadence = num(inputs, "cadence")
    optimum = js_sqrt(js_div(haste, neglect))
    floor = 2 * js_sqrt(haste * neglect)
    cost = js_div(haste, cadence) + neglect * cadence
    return {
        "optimal_cadence": round12(optimum),
        "tempo_floor": round12(floor),
        "cadence_cost": round12(cost),
        "normalized_cost": round12(js_div(cost, floor)),
        "haste_neglect_tax": round12(js_cosh(js_log(js_div(cadence, optimum)))),
        "at_optimum": is_close(cadence, optimum),
    }
