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
    richness = num(inputs, "predictive_richness")
    bandwidth = num(inputs, "observation_bandwidth")
    power = num(inputs, "maintenance_power")
    factor = num(inputs, "boltzmann_constant") * num(inputs, "temperature") * LN2
    data_ceiling = richness * bandwidth
    maintenance_ceiling = js_div(power, factor)
    apply_landauer = inputs["landauer_maintenance_assumption"] is True
    effective = js_min(data_ceiling, maintenance_ceiling) if apply_landauer else data_ceiling
    if apply_landauer:
        regime = "DATA_LIMITED" if data_ceiling <= maintenance_ceiling else "MAINTENANCE_LIMITED"
    else:
        regime = "DATA_BOUND_ONLY_NO_LANDAUER_ASSERTION"
    observed = num(inputs, "observed_information_rate")
    return {
        "data_information_ceiling": round12(data_ceiling),
        "maintenance_information_ceiling": round12(maintenance_ceiling) if apply_landauer else None,
        "effective_information_ceiling": round12(effective),
        "critical_maintenance_power": round12(data_ceiling * factor),
        "binding_regime": regime,
        "observed_information_rate": round12(observed),
        "within_effective_ceiling": observed <= effective + 1e-12,
        "landauer_maintenance_assumption_applied": apply_landauer,
        "scope": "predictive-richness data bound; thermodynamic minimum applies only to declared maintenance or erasure work",
    }
