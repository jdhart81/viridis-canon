"""Reference runner for the Viridis OS Harmonization kernel (stdlib only).

Computes what series/GaianHarmonization.lean proves (`ght_market_clears`,
`ght_strong_duality_decentralized_eq_centralized`): stewards with quadratic costs
(a_i/2)(x_i - b_i)^2 and a shared target sum(x_i) = X are coordinated by the single price

  lambda* = (sum(b) - X) / sum(1/a)
  x_i     = b_i - lambda*/a_i          each steward's best response
  cost    = sum (a_i/2)(x_i - b_i)^2   no feasible allocation costs less

Earlier versions (ported from viridis-conservation-app@398b177) returned max(marginal costs) as the
price, a "wu-wei dividend" overhead*(n-1) and an Intelligence Bound bandwidth check; none is what
the theorem proves. Matches viridisos modules/harmonization/engine.py (v0.2.0).
"""
from viridis_fn import (  # noqa: F401
    InputError, KB, LN2, is_close, js_cosh, js_div, js_log, js_max, js_min, js_pow,
    js_sqrt, js_sum, lexically_less, locale_usd, num, opt, round12, to_fixed,
)


def run(inputs):
    a = [float(v) for v in inputs["curvatures"]]
    b = [float(v) for v in inputs["ideals"]]
    if len(a) != len(b):
        raise InputError("curvatures and ideals must list the same stewards")
    target = num(inputs, "target")
    lam = js_div(js_sum(b) - target, js_sum([js_div(1, ai) for ai in a]))
    x = [bi - js_div(lam, ai) for ai, bi in zip(a, b)]
    total = js_sum(x)
    cost = js_sum([0.5 * ai * (xi - bi) * (xi - bi) for ai, xi, bi in zip(a, x, b)])
    return {
        "clearing_price": to_fixed(lam, 9),
        "allocation": [to_fixed(v, 9) for v in x],
        "total_allocated": to_fixed(total, 9),
        "market_clears": is_close(total, target),
        "total_cost": to_fixed(cost, 9),
    }
