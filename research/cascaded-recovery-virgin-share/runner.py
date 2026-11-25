"""Reference runner for the Viridis OS function declared in function.json (stdlib only).

Cascaded recovery: virgin share after n recovery stages (viridis-research P3.CascadedRecovery,
PROVEN in runs/2026-11-16_P3). Stage i recovers the fraction r_i of what reaches it, so the
share of the original stream still met by virgin material is prod(1 - r_i). Exact rational
arithmetic; outputs are rounded to 12 places only at the end. Every output is a term of the
sealed statement: the share, the uniform lower bound (1 - max r)^n, the best single stage's
share min_j (1 - r_j), and whether the strictness clause (part 4) applies to that best stage.
"""
import math
from fractions import Fraction

from viridis_fn import InputError, round12  # noqa: F401

MAX_STAGES = 64


def _fraction(value, i):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"recovery_fractions[{i}] must be a number")
    if isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"recovery_fractions[{i}] must be finite")
    f = Fraction(value)
    if f < 0:
        raise InputError(f"recovery_fractions[{i}] must be >= 0 (a stage cannot add demand)")
    if f > 1:
        raise InputError(f"recovery_fractions[{i}] must be <= 1 (a stage cannot recover more than reaches it)")
    return f


def run(inputs):
    raw = inputs.get("recovery_fractions")
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_STAGES:
        raise InputError(f"recovery_fractions needs 1 to {MAX_STAGES} stages")
    r = [_fraction(v, i) for i, v in enumerate(raw)]
    n = len(r)
    share = Fraction(1)
    for x in r:
        share *= 1 - x
    top = max(r)
    lower = (1 - top) ** n
    best = min(range(n), key=lambda j: (1 - r[j], j))
    best_share = 1 - r[best]
    strict = r[best] < 1 and any(r[k] > 0 for k in range(n) if k != best)
    return {
        "virgin_share": round12(float(share)),
        "recovered_share": round12(float(1 - share)),
        "stage_count": n,
        "uniform_lower_bound": round12(float(lower)),
        "best_single_stage": best,
        "best_single_stage_share": round12(float(best_share)),
        "cascade_strictly_better": strict,
        "cascade_gain": round12(float(best_share - share)),
    }
