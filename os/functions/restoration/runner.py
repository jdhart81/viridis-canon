"""Reference runner for the Viridis OS Restoration kernel (stdlib only).

Computes what series/ForestNucleation.lean proves (`critical_nucleus`, `barrier_half_identity`):
for a planted cluster of n = r^3 trees with free energy G(r) = -dmu*r^3 + a*sigma*r^2,

  r*  = 2*a*sigma / (3*dmu)    unique barrier top on r >= 0
  n*  = r*^3                   critical cluster size
  dG* = 1/2 * dmu * n*         barrier height

and the go/no-go the theorem supports: a planned cluster at or above n* is past the barrier top.
The ratio sigma/dmu is reported for convenience only. Earlier versions (ported from
viridis-conservation-app@398b177) used n* = (sigma/dmu)^3, which drops the (2a/3)^3 factor, and
graded sigma/dmu into GREEN/AMBER/RED at 0.5 and 1; those cut-offs are not in the theorem.
Matches viridisos modules/restoration/engine.py (v0.2.0). JavaScript-number semantics via viridis_fn.
"""
from viridis_fn import (  # noqa: F401
    InputError, KB, LN2, is_close, js_cosh, js_div, js_log, js_max, js_min, js_pow,
    js_sqrt, js_sum, lexically_less, locale_usd, num, opt, round12, to_fixed,
)


def run(inputs):
    sigma = num(inputs, "sigma")
    delta_mu = num(inputs, "delta_mu")
    a = opt(inputs, "shape_factor", 1.0)
    r_star = js_div(2 * a * sigma, 3 * delta_mu)
    n_star = js_pow(r_star, 3)
    out = {
        "critical_radius_r_star": to_fixed(r_star, 9),
        "critical_nucleus_n_star": to_fixed(n_star, 9),
        "barrier_height": to_fixed(0.5 * delta_mu * n_star, 9),
        "edge_to_suitability_ratio": to_fixed(js_div(sigma, delta_mu), 9),
    }
    cluster = opt(inputs, "cluster_size")
    if cluster is not None:
        out["cluster_size"] = to_fixed(cluster, 9)
        out["cluster_reaches_n_star"] = cluster >= n_star
        out["go_no_go"] = "GO" if cluster >= n_star else "NO_GO"
    return out
