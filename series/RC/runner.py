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
    vx = num(inputs, "value_x")
    vy = num(inputs, "value_y")
    cx = num(inputs, "cost_x")
    cy = num(inputs, "cost_y")
    total = num(inputs, "total_flow")
    lower_ratio = js_div(cx, vx)
    upper_ratio = js_div(vy, cy)
    feasible = lower_ratio < upper_ratio
    lower_share = js_div(lower_ratio, 1 + lower_ratio)
    upper_share = js_div(upper_ratio, 1 + upper_ratio)
    share = (lower_share + upper_share) / 2 if feasible else None
    x_flow = None if share is None else total * (1 - share)
    y_flow = None if share is None else total * share
    both = x_flow is not None and y_flow is not None
    return {
        "corridor_nonempty": feasible,
        "flow_ratio_lower": round12(lower_ratio),
        "flow_ratio_upper": round12(upper_ratio),
        "y_flow_share_lower": round12(lower_share),
        "y_flow_share_upper": round12(upper_share),
        "nash_y_flow_share": None if share is None else round12(share),
        "recommended_x_flow": None if x_flow is None else round12(x_flow),
        "recommended_y_flow": None if y_flow is None else round12(y_flow),
        "payoff_x": round12(vx * y_flow - cx * x_flow) if both else None,
        "payoff_y": round12(vy * x_flow - cy * y_flow) if both else None,
        "scope": "two-party one-period linear payoff model with zero disagreement utility",
    }
