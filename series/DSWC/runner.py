"""Reference runner for the Viridis OS function declared in function.json (stdlib only).

D-Score weight robustness (DSWC, Run-132). Ported from jdhart81/viridisos
modules/dscore_robustness/engine.py. Theorems relied on: tv_range_certificate
(|score(w,z) - score(v,z)| <= TV(w,v) * span(z)) and strict_rank_stability, applied to the
contrast z = parcel_a - parcel_b. Arithmetic of weighted sums only; the D-Score's ecological
validity is not proven.
"""
from viridis_fn import InputError, js_max, js_min, js_sum, round12  # noqa: F401

SUM_TOL = 1e-9


def _simplex(name, values):
    if any(x < 0 for x in values):
        raise InputError(f"{name} must be non-negative")
    if abs(js_sum(values) - 1) > SUM_TOL:
        raise InputError(f"{name} must sum to 1")
    return values


def _score(w, z):
    return js_sum(a * b for a, b in zip(w, z))


def _span(z):
    return js_max(*z) - js_min(*z)


def run(inputs):
    v = _simplex("reference_weights", [float(x) for x in inputs["reference_weights"]])
    w = _simplex("alternative_weights", [float(x) for x in inputs["alternative_weights"]])
    za = [float(x) for x in inputs["parcel_a"]]
    zb = [float(x) for x in inputs["parcel_b"]]
    if not (len(w) == len(za) == len(zb) == len(v)):
        raise InputError("weights and parcel indicators must all have the same length")
    tv = 0.5 * js_sum(abs(a - b) for a, b in zip(w, v))
    contrast = [a - b for a, b in zip(za, zb)]
    gap_ref = _score(v, contrast)
    gap_alt = _score(w, contrast)
    contrast_span = _span(contrast)
    bound = tv * contrast_span
    if contrast_span > 0:
        radius = round12(abs(gap_ref) / contrast_span)
    else:
        radius = None if gap_ref != 0 else 0
    ref_order = (gap_ref > 0) - (gap_ref < 0)
    alt_order = (gap_alt > 0) - (gap_alt < 0)
    leader = {1: "A", -1: "B", 0: "tie"}
    a_ref, a_alt, b_ref, b_alt = _score(v, za), _score(w, za), _score(v, zb), _score(w, zb)
    return {
        "total_variation": round12(tv),
        "score_a_reference": round12(a_ref),
        "score_a_alternative": round12(a_alt),
        "drift_a": round12(abs(a_alt - a_ref)),
        "drift_bound_a": round12(tv * _span(za)),
        "score_b_reference": round12(b_ref),
        "score_b_alternative": round12(b_alt),
        "drift_b": round12(abs(b_alt - b_ref)),
        "drift_bound_b": round12(tv * _span(zb)),
        "gap_reference": round12(gap_ref),
        "gap_alternative": round12(gap_alt),
        "gap_drift_bound": round12(bound),
        "ranking_robust": abs(gap_ref) > bound,
        "robust_tv_radius": radius,
        "leader_reference": leader[ref_order],
        "leader_alternative": leader[alt_order],
        "order_flipped_under_alternative": ref_order != alt_order,
        "scope": "weighted-sum arithmetic for two parcels; ecological validity of the D-Score not proven",
    }
