"""Reference runner for the Viridis OS function declared in function.json (stdlib only).

Corridor link priority (PCS, Run-124). Ported from jdhart81/viridisos
modules/corridor_priority/engine.py. Exact two-terminal reliability and each link's pivotal
probability by enumeration of all 2^m link states in rational arithmetic; by
reliability_derivative_eq_pivotal_probability the pivotal probability is the reliability
gradient. Exact for INDEPENDENT link survival only.
"""
from fractions import Fraction

from viridis_fn import InputError, round12  # noqa: F401

MAX_EDGES = 16
MAX_NODES = 64


def _node(v, n):
    if isinstance(v, bool) or int(v) != v or not 0 <= int(v) < n:
        raise InputError(f"node index must be in 0..{n - 1}")
    return int(v)


def run(inputs):
    n = inputs["num_nodes"]
    if isinstance(n, bool) or int(n) != n or not 2 <= int(n) <= MAX_NODES:
        raise InputError(f"num_nodes must be an integer in 2..{MAX_NODES}")
    n = int(n)
    raw = inputs["edges"]
    probs = inputs["survival"]
    if not raw:
        raise InputError("edges needs at least one link")
    if len(raw) > MAX_EDGES:
        raise InputError(f"at most {MAX_EDGES} links (exact enumeration of 2^m states)")
    if len(probs) != len(raw):
        raise InputError("survival needs one probability per link")
    links = []
    for u, v in raw:
        u, v = _node(u, n), _node(v, n)
        if u == v:
            raise InputError("self-loops are not corridor links")
        links.append((u, v))
    p = []
    for x in probs:
        if not 0 <= float(x) <= 1:
            raise InputError("survival probabilities must be in [0, 1]")
        p.append(Fraction(repr(float(x))))
    a = sorted({_node(x, n) for x in inputs["core_a"]})
    b = sorted({_node(x, n) for x in inputs["core_b"]})
    if not a or not b:
        raise InputError("both terminal cores need at least one node")
    if set(a) & set(b):
        raise InputError("terminal cores must be disjoint")
    m = len(links)
    start = sum(1 << x for x in a)
    target = sum(1 << x for x in b)
    phi = [False] * (1 << m)
    for mask in range(1 << m):
        reach, changed = start, True
        while changed:
            changed = False
            for k, (u, v) in enumerate(links):
                if (mask >> k) & 1 and ((reach >> u) & 1) != ((reach >> v) & 1):
                    reach |= (1 << u) | (1 << v)
                    changed = True
        phi[mask] = bool(reach & target)
    w = [Fraction(1)]
    for k in range(m):
        w = [x * (1 - p[k]) for x in w] + [x * p[k] for x in w]
    rel = sum((w[s] for s in range(len(w)) if phi[s]), Fraction(0))
    piv = []
    for k in range(m):
        bit = 1 << k
        piv.append(sum((w[s] + w[s | bit] for s in range(len(w))
                        if not s & bit and phi[s | bit] and not phi[s]), Fraction(0)))
    order = sorted(range(m), key=lambda k: (-piv[k], k))
    out = {
        "reliability": round12(float(rel)),
        "pivotal_probability": [round12(float(x)) for x in piv],
        "priority_order": order,
        "top_link": order[0],
        "scope": "independent link survival; exact two-terminal reliability by enumeration",
    }
    costs = inputs.get("costs")
    if costs is not None:
        if len(costs) != m or any(float(c) <= 0 for c in costs):
            raise InputError("costs needs one positive cost per link")
        ratio = [piv[k] / Fraction(repr(float(costs[k]))) for k in range(m)]
        cost_order = sorted(range(m), key=lambda k: (-ratio[k], k))
        out["pivotal_per_cost"] = [round12(float(x)) for x in ratio]
        out["cost_priority_order"] = cost_order
        out["best_ratio"] = round12(float(ratio[cost_order[0]]))
    return out
