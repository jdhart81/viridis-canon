"""Reference runner for the Viridis OS function declared in function.json (stdlib only).

Loop mass balance for one material (viridis-research P3.LoopMassBalance, PROVEN in
runs/2026-11-15_P3). Demand D per period, of which the fraction r is met from recovered
material, so the virgin input per period is V = D(1 - r). The secondary stock follows
S(t+1) = rho S(t) + r D from S(0) and settles towards S* = r D / (1 - rho). Exact rational
arithmetic; outputs are rounded to 12 places only at the end. Every output is a term of the
sealed statement: V, S*, the stock path S(0..T), the gap S(T) - S*, the cumulative virgin
input over T periods, and whether the strictness clause (D > 0 and T > 0) applies.
"""
import math
from fractions import Fraction

from viridis_fn import InputError, round12  # noqa: F401

MAX_PERIODS = 1000


def _number(inputs, name):
    if name not in inputs:
        raise InputError(f"{name} is required")
    value = inputs[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{name} must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"{name} must be finite")
    return Fraction(value)


def run(inputs):
    D = _number(inputs, "demand")
    r = _number(inputs, "recovery_fraction")
    rho = _number(inputs, "retention")
    s0 = _number(inputs, "initial_stock")
    T = _number(inputs, "periods")
    if D < 0:
        raise InputError("demand must be >= 0")
    if r < 0 or r > 1:
        raise InputError("recovery_fraction must lie in [0, 1]")
    if rho < 0:
        raise InputError("retention must be >= 0")
    if rho >= 1:
        raise InputError("retention must be < 1 (with full retention the stock has no steady level)")
    if T.denominator != 1 or T < 0:
        raise InputError("periods must be a whole number >= 0")
    if T > MAX_PERIODS:
        raise InputError(f"periods must be at most {MAX_PERIODS}")
    T = int(T)
    virgin = D * (1 - r)
    steady = r * D / (1 - rho)
    path = [s0]
    for _ in range(T):
        path.append(rho * path[-1] + r * D)
    return {
        "virgin_per_period": round12(float(virgin)),
        "steady_stock": round12(float(steady)),
        "stock_path": [round12(float(s)) for s in path],
        "stock_at_horizon": round12(float(path[-1])),
        "gap_at_horizon": round12(float(path[-1] - steady)),
        "cumulative_virgin": round12(float(T * virgin)),
        "virgin_total_strictly_decreasing_in_recovery": D > 0 and T > 0,
    }
