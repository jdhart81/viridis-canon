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
    bias = num(inputs, "bias")
    down_cost = num(inputs, "cost_plus_to_minus")
    up_cost = num(inputs, "cost_minus_to_plus")
    current_state = num(inputs, "current_state")
    evidence = num(inputs, "evidence")
    down_threshold = -bias - down_cost / 2
    up_threshold = -bias + up_cost / 2
    stay_cost = -(evidence + bias) * current_state
    switch_state = -current_state
    switch_cost = -(evidence + bias) * switch_state + (down_cost if current_state == 1 else up_cost)
    next_state = switch_state if switch_cost < stay_cost else current_state
    return {
        "down_switch_threshold": round12(down_threshold),
        "up_switch_threshold": round12(up_threshold),
        "history_band_width": round12((down_cost + up_cost) / 2),
        "absolute_loop_integral": round12(down_cost + up_cost),
        "inside_history_band": down_threshold < evidence < up_threshold,
        "next_state": next_state,
        "switch_recommended": next_state != current_state,
        "scope": "two-state myopic retain-on-tie objective with fixed directional switch costs",
    }
