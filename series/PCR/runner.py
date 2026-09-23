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
    mean = num(inputs, "mean_capacity")
    sd = num(inputs, "capacity_sd")
    alpha = num(inputs, "alpha")
    power = opt(inputs, "power")
    temperature = opt(inputs, "temperature")
    if (power is None) != (temperature is None):
        raise InputError("power and temperature must be supplied together")
    discount = sd * js_sqrt(js_div(1 - alpha, alpha))
    safe = js_max(0, mean - discount)
    rate = None if power is None else js_div(power * safe, KB * temperature * LN2)
    return {
        "precautionary_capacity": round12(safe),
        "absolute_discount": round12(discount),
        "capacity_fraction": round12(js_div(safe, mean)) if mean > 0 else 0,
        "certified_rate_ceiling": None if rate is None else round12(rate),
        "violation_probability_bound": round12(alpha),
        "positive_floor": safe > 0,
        "scope": "one-period two-moment marginal Cantelli certificate",
    }
