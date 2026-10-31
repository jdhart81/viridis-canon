"""Reference runner for the Viridis OS Afforestation kernel (stdlib only).

Computes what series/AfforestationStewardship.lean proves, in the nucleation model shared with
Forest Nucleation (site suitability dmu > 0, edge hostility sigma > 0, shape factor a > 0,
establishment constant C > 0):

  n*  = (2*a*sigma / (3*dmu))^3          critical nucleus (`nStar`)
  dG* = 4*(a*sigma)^3 / (27*dmu^2)       barrier = 1/2*dmu*n* (`homogeneous_limit_recovers_fnt`)
  e   = C * (3*dmu / (2*a*sigma))^3      seeding efficiency = C/n* (`eff`)
  e(sigma/2) = 8*e                       (`site_prep_halving_sigma_eightfolds_efficiency`)
  e(t*dmu) = t^3*e                       (`establishment_efficiency_cubic_in_drive_over_tension`)

Earlier versions (ported from viridis-conservation-app@398b177) returned density (prep*dmu/sigma)^3,
which drops the (2a/3)^3 factor, and an "IB seeding-rate ceiling". The theorem file's
`sower_IB_ceiling` only rearranges an assumed premise; the Intelligence Bound is a conjecture,
so it is not a product check. Matches viridisos modules/afforestation/engine.py (v0.2.0).
"""
from viridis_fn import (  # noqa: F401
    InputError, KB, LN2, is_close, js_cosh, js_div, js_log, js_max, js_min, js_pow,
    js_sqrt, js_sum, lexically_less, locale_usd, num, opt, round12, to_fixed,
)


def run(inputs):
    sigma = num(inputs, "sigma")
    delta_mu = num(inputs, "delta_mu")
    a = opt(inputs, "shape_factor", 1.0)
    c = opt(inputs, "establishment_constant", 1.0)
    n_star = js_pow(js_div(2 * a * sigma, 3 * delta_mu), 3)
    barrier = js_div(4 * js_pow(a * sigma, 3), 27 * js_pow(delta_mu, 2))
    e = c * js_pow(js_div(3 * delta_mu, 2 * a * sigma), 3)
    return {
        "critical_nucleus_n_star": to_fixed(n_star, 9),
        "barrier_height": to_fixed(barrier, 9),
        "seeding_efficiency": to_fixed(e, 9),
        "efficiency_if_edge_hostility_halved": to_fixed(8 * e, 9),
    }
