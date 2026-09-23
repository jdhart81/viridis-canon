"""Generic runner for theorem functions (Python stdlib only).

A Lean theorem is "hypotheses ⇒ conclusion".  A theorem function takes values
for the theorem's variables, reports which hypotheses hold, evaluates the
declared derived quantities, and states whether the conclusion follows *from the
theorem* (it does exactly when every hypothesis holds).  It also evaluates the
conclusion as a check on the supplied values; if the hypotheses hold and that
check fails, the manifest's translation of the Lean statement is wrong and the
runner says so (``TRANSLATION_FAULT``) instead of reporting a result.

The runner never estimates a real-world magnitude.  Its output is conditional
mathematics about the supplied values only.
"""

from __future__ import annotations

import math

from viridis_fn import check, evaluate

OUTPUT_KEYS = (
    "theorem",
    "hypotheses",
    "hypotheses_hold",
    "derived",
    "conclusion",
    "conclusion_check",
    "conclusion_follows_from_theorem",
    "status",
)


def _clean(value):
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        value = float(value)
        return value if math.isfinite(value) else None  # full precision: physical units span 1e-23..1e23
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    return None


def run_theorem(manifest: dict, inputs: dict) -> dict:
    env = dict(inputs)
    hypotheses = {h["id"]: check(h["check"], env) for h in manifest.get("hypotheses", [])}
    hold = all(hypotheses.values())
    derived = {}
    for item in manifest.get("derived", []):
        try:
            value = evaluate(item["expression"], env)
        except (TypeError, ValueError, IndexError, KeyError, ZeroDivisionError, OverflowError):
            value = None
        env[item["name"]] = value
        derived[item["name"]] = _clean(value)
    conclusion = manifest["conclusion"]
    conclusion_value = check(conclusion["check"], env)
    if not hold:
        status = "HYPOTHESES_NOT_MET"
    elif conclusion_value:
        status = "CONCLUSION_FOLLOWS"
    else:
        status = "TRANSLATION_FAULT"
    return {
        "theorem": conclusion["lean_theorem"],
        "hypotheses": hypotheses,
        "hypotheses_hold": hold,
        "derived": derived,
        "conclusion": conclusion["statement"],
        "conclusion_check": conclusion_value,
        "conclusion_follows_from_theorem": hold,
        "status": status,
    }
