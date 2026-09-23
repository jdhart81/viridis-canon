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
    distance = num(inputs, "distance")
    area = num(inputs, "area")
    horizon = num(inputs, "horizon")
    tolerance = num(inputs, "tolerance")
    budget = num(inputs, "budget")
    prefactor = js_div(js_pow(distance, 2), area * horizon)
    shadow_price = js_div(prefactor, js_pow(tolerance, 2))
    rows = [
        {
            "source_index": source_index,
            "prefactor": round12(float(value)),
            "shadow_price": round12(js_div(float(value), js_pow(tolerance, 2))),
        }
        for source_index, value in enumerate(inputs["tower_prefactors"])
    ]
    ordered = sorted(rows, key=lambda row: (row["prefactor"], row["source_index"]))
    return {
        "shadow_prefactor": round12(prefactor),
        "shadow_price": round12(shadow_price),
        "inverse_square_factor": round12(js_div(1, js_pow(tolerance, 2))),
        "tolerance_at_budget": round12(js_sqrt(js_div(prefactor, budget))),
        "within_budget": shadow_price <= budget + 1e-12,
        "capacity_ceiling": round12(js_div(num(inputs, "power") * num(inputs, "dissipation_factor"), num(inputs, "capacity_cost"))),
        "tower_order": ordered,
        "tower_order_preserves_prefactors": all(
            index == len(ordered) - 1 or row["prefactor"] <= ordered[index + 1]["prefactor"]
            for index, row in enumerate(ordered)
        ),
        "scope": "positive-coefficient inverse-square shadow-price and P*D/C capacity model",
    }
