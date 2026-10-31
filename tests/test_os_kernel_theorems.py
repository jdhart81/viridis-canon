"""Theorem conformance for the restoration, harmonization and afforestation OS runners (K1-K3).

These replace product parity for the three kernels: each runner must compute what its Lean
theorem proves, checked against independent float formulas over a grid of inputs.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "os" / "lib"))


def _load(fid):
    spec = importlib.util.spec_from_file_location(f"runner_{fid}", ROOT / "os" / "functions" / fid / "runner.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run


restoration, harmonization, afforestation = (_load(f) for f in ("restoration", "harmonization", "afforestation"))
GRID = [0.2, 0.7, 1.0, 1.5, 3.0]


def close(x, y):
    return math.isclose(x, y, rel_tol=1e-8, abs_tol=2e-9)


class Restoration(unittest.TestCase):  # K1
    def test_formulas_over_grid(self):
        for s, d, a in itertools.product(GRID, GRID, GRID):
            out = restoration({"sigma": s, "delta_mu": d, "shape_factor": a})
            r = 2 * a * s / (3 * d)
            self.assertTrue(close(out["critical_radius_r_star"], r))
            self.assertTrue(close(out["critical_nucleus_n_star"], r ** 3))
            self.assertTrue(close(out["barrier_height"], 0.5 * d * r ** 3))
            # r* is the barrier top of G(r) = -d r^3 + a s r^2 on r >= 0
            g = lambda x: -d * x ** 3 + a * s * x ** 2
            self.assertTrue(all(g(r) >= g(r * k / 20) - 1e-12 for k in range(0, 61)))

    def test_canon_witness_and_go_no_go(self):
        out = restoration({"sigma": 1.5, "delta_mu": 1})
        self.assertEqual((out["critical_radius_r_star"], out["critical_nucleus_n_star"], out["barrier_height"]), (1, 1, 0.5))
        self.assertTrue(close(restoration({"sigma": 1, "delta_mu": 1})["critical_nucleus_n_star"], 8 / 27))
        self.assertEqual(restoration({"sigma": 3, "delta_mu": 1, "cluster_size": 8})["go_no_go"], "GO")
        self.assertEqual(restoration({"sigma": 3, "delta_mu": 1, "cluster_size": 7.9})["go_no_go"], "NO_GO")

    def test_no_legacy_grades(self):
        out = restoration({"sigma": 5, "delta_mu": 1})
        self.assertFalse({"recommendation", "broadcast_fails", "nucleation_number"} & set(out))


class Harmonization(unittest.TestCase):  # K2
    CASES = [([1, 1], [1, 1], 0), ([1, 1, 1], [10, 8, 6], 12), ([0.5, 2, 4], [3, -1, 7], 5), ([3], [2], 9)]

    def test_clearing_price_and_optimality(self):
        for a, b, X in self.CASES:
            out = harmonization({"curvatures": a, "ideals": b, "target": X})
            lam = (sum(b) - X) / sum(1 / ai for ai in a)
            x = [bi - lam / ai for ai, bi in zip(a, b)]
            cost = sum(ai / 2 * (xi - bi) ** 2 for ai, xi, bi in zip(a, x, b))
            self.assertTrue(close(out["clearing_price"], lam))
            self.assertTrue(all(close(u, v) for u, v in zip(out["allocation"], x)))
            self.assertTrue(out["market_clears"])
            self.assertTrue(close(out["total_cost"], cost))
            # no other allocation meeting the target is cheaper (strong duality)
            if len(a) > 1:
                for shift in (-1.0, -0.1, 0.1, 1.0):
                    y = list(x); y[0] += shift; y[-1] -= shift
                    self.assertGreaterEqual(sum(ai / 2 * (yi - bi) ** 2 for ai, yi, bi in zip(a, y, b)), cost - 1e-9)

    def test_canon_witness_and_no_legacy_outputs(self):
        out = harmonization({"curvatures": [1, 1], "ideals": [1, 1], "target": 0})
        self.assertEqual((out["clearing_price"], out["allocation"], out["total_cost"]), (1, [0, 0], 1))
        self.assertFalse({"shadow_price", "wu_wei_dividend", "coordination_within_ib"} & set(out))


class Afforestation(unittest.TestCase):  # K3
    def test_formulas_and_levers(self):
        for s, d, a, c in itertools.product(GRID, GRID, [1.0, 2.0], [1.0, 2.5]):
            out = afforestation({"sigma": s, "delta_mu": d, "shape_factor": a, "establishment_constant": c})
            n = (2 * a * s / (3 * d)) ** 3
            e = c * (3 * d / (2 * a * s)) ** 3
            self.assertTrue(close(out["critical_nucleus_n_star"], n))
            self.assertTrue(close(out["barrier_height"], 4 * (a * s) ** 3 / (27 * d ** 2)))
            self.assertTrue(close(out["barrier_height"], 0.5 * d * n))
            self.assertTrue(close(out["seeding_efficiency"], e))
            self.assertTrue(close(out["efficiency_if_edge_hostility_halved"], 8 * e))
            half = afforestation({"sigma": s / 2, "delta_mu": d, "shape_factor": a, "establishment_constant": c})
            # both values are rounded to 9 places, so allow 8x that rounding step
            self.assertTrue(math.isclose(half["seeding_efficiency"], 8 * out["seeding_efficiency"], rel_tol=1e-8, abs_tol=1e-8))

    def test_no_ib_ceiling(self):
        out = afforestation({"sigma": 1, "delta_mu": 1})
        self.assertFalse(any("ib" in k or "ceiling" in k or "density" in k for k in out))


if __name__ == "__main__":
    unittest.main()
