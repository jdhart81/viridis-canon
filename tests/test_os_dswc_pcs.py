"""Theorem conformance for the D-Score robustness (DSWC) and corridor priority (PCS) runners.

K4 (DSWC, Run-132):
  K4a tv_range_certificate: |score(w,z) - score(v,z)| <= TV(w,v) * span(z) for every parcel.
  K4b strict_rank_stability: ranking_robust implies the order does not flip under w.
  K4c charter_nonvacuous witness: v=(0.6,0.4), w=(0.3,0.7), z=(0,5) gives TV 0.3 and drift 1.5,
      which attains the bound.
  K4d non-simplex weights and length mismatches are rejected.
K5 (PCS, Run-124):
  K5a reliability_derivative_eq_pivotal_probability: pivotal_e = R(p_e := 1) - R(p_e := 0).
  K5b pivotal_probability_independent_of_own_probability: pivotal_e does not depend on p_e.
  K5c closed forms: a series pair has R = p1 p2; a parallel pair has R = 1 - (1-p1)(1-p2).
  K5d graphs with more than 16 links, overlapping cores and bad probabilities are rejected.
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "os" / "lib"))

from viridis_fn import InputError  # noqa: E402


def _load(pkg):
    spec = importlib.util.spec_from_file_location(f"runner_{pkg}", ROOT / "series" / pkg / "runner.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.run


dswc, pcs = _load("DSWC"), _load("PCS")
TOL = 1e-9


def _simplex(rng, n):
    raw = [rng.random() + 1e-3 for _ in range(n)]
    s = sum(raw)
    w = [x / s for x in raw]
    w[-1] = 1 - sum(w[:-1])
    return w


class DScoreRobustness(unittest.TestCase):  # K4
    def test_drift_bound_and_rank_stability_random(self):
        rng = random.Random(132)
        for _ in range(400):
            n = rng.randint(1, 8)
            v, w = _simplex(rng, n), _simplex(rng, n)
            za = [rng.uniform(-10, 10) for _ in range(n)]
            zb = [rng.uniform(-10, 10) for _ in range(n)]
            out = dswc({"reference_weights": v, "alternative_weights": w, "parcel_a": za, "parcel_b": zb})
            self.assertLessEqual(out["drift_a"], out["drift_bound_a"] + TOL)
            self.assertLessEqual(out["drift_b"], out["drift_bound_b"] + TOL)
            self.assertLessEqual(abs(out["gap_alternative"] - out["gap_reference"]), out["gap_drift_bound"] + TOL)
            if out["ranking_robust"]:
                self.assertFalse(out["order_flipped_under_alternative"])

    def test_charter_witness_attains_bound(self):
        out = dswc({"reference_weights": [0.6, 0.4], "alternative_weights": [0.3, 0.7],
                    "parcel_a": [0, 5], "parcel_b": [0, 0]})
        self.assertEqual(out["total_variation"], 0.3)
        self.assertEqual(out["drift_a"], 1.5)
        self.assertEqual(out["drift_bound_a"], 1.5)

    def test_rejects_bad_inputs(self):
        base = {"reference_weights": [0.6, 0.4], "alternative_weights": [0.3, 0.7],
                "parcel_a": [0, 5], "parcel_b": [0, 0]}
        for patch in ({"reference_weights": [0.6, 0.6]}, {"alternative_weights": [1.2, -0.2]},
                      {"parcel_b": [0, 0, 1]}):
            with self.assertRaises(InputError):
                dswc({**base, **patch})


DIAMOND = {"num_nodes": 4, "edges": [[0, 1], [1, 3], [0, 2], [2, 3], [1, 2]], "core_a": [0], "core_b": [3]}


class CorridorPriority(unittest.TestCase):  # K5
    def test_pivotal_is_reliability_difference_and_own_independent(self):
        rng = random.Random(124)
        for _ in range(60):
            p = [round(rng.random(), 3) for _ in DIAMOND["edges"]]
            out = pcs({**DIAMOND, "survival": p})
            for e in range(len(p)):
                hi = pcs({**DIAMOND, "survival": p[:e] + [1] + p[e + 1:]})["reliability"]
                lo = pcs({**DIAMOND, "survival": p[:e] + [0] + p[e + 1:]})["reliability"]
                self.assertTrue(math.isclose(out["pivotal_probability"][e], hi - lo, abs_tol=1e-11))
                other = pcs({**DIAMOND, "survival": p[:e] + [round(rng.random(), 3)] + p[e + 1:]})
                self.assertTrue(math.isclose(other["pivotal_probability"][e], out["pivotal_probability"][e], abs_tol=1e-11))
            self.assertEqual(out["top_link"], out["priority_order"][0])

    def test_series_and_parallel_closed_forms(self):
        series = pcs({"num_nodes": 3, "edges": [[0, 1], [1, 2]], "survival": [0.8, 0.5], "core_a": [0], "core_b": [2]})
        self.assertTrue(math.isclose(series["reliability"], 0.4))
        par = pcs({"num_nodes": 2, "edges": [[0, 1], [0, 1]], "survival": [0.8, 0.5], "core_a": [0], "core_b": [1]})
        self.assertTrue(math.isclose(par["reliability"], 0.9))

    def test_cost_ranking(self):
        out = pcs({**DIAMOND, "survival": [0.5] * 5, "costs": [1, 2, 1, 1, 1]})
        self.assertEqual(out["best_ratio"], max(out["pivotal_per_cost"]))
        self.assertEqual(out["cost_priority_order"][0], out["pivotal_per_cost"].index(out["best_ratio"]))

    def test_rejects_bad_inputs(self):
        many = {"num_nodes": 18, "edges": [[i, i + 1] for i in range(17)], "survival": [0.5] * 17,
                "core_a": [0], "core_b": [17]}
        for bad in (many, {**DIAMOND, "survival": [0.5] * 4}, {**DIAMOND, "survival": [1.5] + [0.5] * 4},
                    {**DIAMOND, "survival": [0.5] * 5, "core_b": [0]}):
            with self.assertRaises(InputError):
                pcs(bad)


if __name__ == "__main__":
    unittest.main()
