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
    observations = inputs["observations"]
    p0 = num(inputs, "p0")
    p1 = num(inputs, "p1")
    alpha = num(inputs, "alpha")
    if p0 == p1:
        raise InputError("p0 and p1 must differ")
    a_value = 0.0
    maximum = 1.0
    alarm_index = None
    threshold = js_div(1, alpha)
    up = js_div(p1, p0)
    down = js_div(1 - p1, 1 - p0)
    for offset, raw in enumerate(observations):
        index = offset + 1
        likelihood = up if raw else down
        a_value = likelihood * (a_value + js_div(1, float(index * (index + 1))))
        current = a_value + js_div(1, float(index + 1))
        maximum = js_max(maximum, current)
        if alarm_index is None and current >= threshold:
            alarm_index = index
    current = a_value + js_div(1, float(len(observations) + 1))
    return {
        "current_mixture_evidence": round12(current),
        "maximum_mixture_evidence": round12(maximum),
        "alarm_threshold": round12(threshold),
        "alarmed": alarm_index is not None,
        "alarm_index": alarm_index,
        "observations_processed": len(observations),
        "false_alarm_probability_bound": round12(alpha),
        "scope": "single frozen Bernoulli likelihood-ratio process under the declared iid null",
    }
