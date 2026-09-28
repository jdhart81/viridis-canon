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
    dissipation = [float(v) for v in inputs["dissipation_factors"]]
    alignment = [float(v) for v in inputs["alignment_factors"]]
    if len(dissipation) != len(alignment):
        raise InputError("dissipation_factors and alignment_factors must have the same non-zero length")
    product = 1.0
    for value in dissipation:
        product = product * value
    geometric_mean = js_pow(product, js_div(1, float(len(dissipation))))
    alignment_product = 1.0
    for value in alignment:
        alignment_product = alignment_product * value
    kappa = num(inputs, "boltzmann_constant") * num(inputs, "temperature") * LN2
    base = js_div(num(inputs, "power") * geometric_mean, kappa)
    ceiling = base * alignment_product
    bottleneck = 0
    for index, value in enumerate(alignment):
        if value < alignment[bottleneck]:
            bottleneck = index
    return {
        "ring_count": len(dissipation),
        "thermodynamic_factor": round12(kappa),
        "geometric_mean_dissipation": round12(geometric_mean),
        "alignment_product": round12(alignment_product),
        "unaligned_base_rate": round12(base),
        "aligned_rate_ceiling": round12(ceiling),
        "retained_fraction": round12(alignment_product),
        "bottleneck_ring_index": bottleneck,
        "perfect_alignment": all(value == 1 for value in alignment),
        "ceiling_not_above_base": ceiling <= base + 1e-12,
        "scope": "finite multi-ring geometric-mean dissipation and multiplicative supplied alignment factors",
    }
