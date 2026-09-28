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
    demands = [float(v) for v in inputs["demands"]]
    supplies = [float(v) for v in inputs["supplies"]]
    edges = inputs["edges"]
    for supply, site in edges:
        if supply < 0 or supply >= len(supplies) or site < 0 or site >= len(demands):
            raise InputError("edge index is out of range")
    n_sites = len(demands)
    # Per-site eligible-supply bitmask; neighbours of a subset = OR of its sites.
    site_mask = [0] * n_sites
    for supply, site in edges:
        site_mask[int(site)] |= 1 << int(supply)
    supply_order = list(range(len(supplies)))

    def neighbours_of(mask_bits):
        return [s for s in supply_order if (mask_bits >> s) & 1]

    all_sites = list(range(n_sites))
    union_all = 0
    for site in all_sites:
        union_all |= site_mask[site]
    best = 1.0
    witness = all_sites
    witness_neighbours = neighbours_of(union_all)
    for mask in range(1, 2 ** n_sites):
        subset = [i for i in all_sites if mask & (1 << i)]
        union = 0
        for site in subset:
            union |= site_mask[site]
        neighbours = neighbours_of(union)
        ratio = js_div(js_sum(supplies[i] for i in neighbours), js_sum(demands[i] for i in subset))
        lexical = lexically_less(subset, witness)
        if ratio < best - 1e-14 or (abs(ratio - best) <= 1e-14 and lexical):
            best = ratio
            witness = subset
            witness_neighbours = neighbours
    certificate = js_max(0, js_min(1, best))
    return {
        "common_fulfillment_fraction": round12(certificate),
        "full_fulfillment_feasible": certificate >= 1 - 1e-12,
        "bottleneck_site_indices": witness,
        "eligible_supply_indices": witness_neighbours,
        "bottleneck_ratio": round12(best),
        "scope": "continuous one-period frozen binary-eligibility supply network",
    }
