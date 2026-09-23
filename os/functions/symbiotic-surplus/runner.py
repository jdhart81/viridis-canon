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
    epsilon = num(inputs, "epsilon_landauer")
    subsidy_sum = num(inputs, "subsidy_e_to_a") + num(inputs, "subsidy_a_to_e")
    reciprocal = is_close(subsidy_sum, 0)
    joint_ceiling = js_div(
        num(inputs, "partner_a_power") * num(inputs, "partner_a_dissipation")
        + num(inputs, "partner_e_power") * num(inputs, "partner_e_dissipation"),
        epsilon,
    )
    observed_joint = num(inputs, "observed_rate_a") + num(inputs, "observed_rate_e")
    norm_product = num(inputs, "norm_a_squared") * num(inputs, "norm_e_squared")
    inner_square = js_pow(num(inputs, "inner_product"), 2)
    if inner_square > norm_product + 1e-12:
        raise InputError("declared geometry violates the Cauchy-Schwarz premise")
    surplus = subsidy_sum - num(inputs, "housekeeping_dissipation")
    return {
        "reciprocity_residual": round12(subsidy_sum),
        "reciprocal_fixed_point": reciprocal,
        "joint_rate_ceiling": round12(joint_ceiling) if reciprocal else None,
        "observed_joint_rate": round12(observed_joint),
        "within_joint_ceiling": (observed_joint <= joint_ceiling + 1e-12) if reciprocal else None,
        "symbiotic_surplus": round12(surplus),
        "coupling_regime": "MUTUALISTIC_WITHIN_MODEL" if surplus >= 0 else "PARASITIC_WITHIN_MODEL",
        "extraction_efficiency": round12(js_div(inner_square, norm_product)),
        "positive_net_subsidy": subsidy_sum > 0,
        "scope": "two-partner supplied-flow model; the joint ceiling requires exact reciprocal subsidy cancellation",
    }
