"""Conformance of loop-mass-balance with viridis-research P3.LoopMassBalance.

Entered by auto-intake (docs/auto_intake/README.md). The exact values are the Lean sanity
examples in the sealed statement; the generic checks replay every statement part.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canon_core.auto_intake import _load_runner, conformance_problems  # noqa: E402
from canon_core.function_schema import load_runtime  # noqa: E402

PACKAGE = ROOT / "research" / "loop-mass-balance"
WITNESS = {"demand": 10, "recovery_fraction": 0.5, "retention": 0.5, "initial_stock": 0}


class LoopMassBalanceConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kernel = staticmethod(_load_runner(PACKAGE, ROOT))
        cls.V = load_runtime(ROOT)

    def test_every_statement_part_holds(self):
        self.assertEqual(conformance_problems(ROOT, PACKAGE), [])

    def test_lean_witnesses(self):
        two = self.kernel({**WITNESS, "periods": 2})
        self.assertEqual(two["virgin_per_period"], 5.0)
        self.assertEqual(two["steady_stock"], 10.0)
        self.assertEqual(two["stock_path"], [0.0, 5.0, 7.5])
        self.assertEqual(two["gap_at_horizon"], -2.5)
        self.assertEqual(self.kernel({**WITNESS, "periods": 3})["cumulative_virgin"], 15.0)
        higher = self.kernel({**WITNESS, "recovery_fraction": 0.75, "periods": 3})
        self.assertEqual(higher["cumulative_virgin"], 7.5)

    def test_strictness_needs_demand_and_horizon(self):
        zero = {"demand": 0, "retention": 0.5, "initial_stock": 0, "periods": 3}
        low = self.kernel({**zero, "recovery_fraction": 0})
        high = self.kernel({**zero, "recovery_fraction": 1})
        self.assertEqual((low["cumulative_virgin"], high["cumulative_virgin"]), (0.0, 0.0))
        self.assertFalse(low["virgin_total_strictly_decreasing_in_recovery"])
        self.assertFalse(self.kernel({**WITNESS, "periods": 0})["virgin_total_strictly_decreasing_in_recovery"])

    def test_out_of_range_inputs_are_refused(self):
        bad = (
            {"demand": 1, "recovery_fraction": 1, "retention": 1, "initial_stock": 0, "periods": 3},
            {**WITNESS, "recovery_fraction": 2, "periods": 3},
            {**WITNESS, "recovery_fraction": -0.1, "periods": 3},
            {**WITNESS, "demand": -1, "periods": 3},
            {**WITNESS, "retention": -0.1, "periods": 3},
            {**WITNESS, "periods": 1.5},
            {**WITNESS, "periods": -1},
            {**WITNESS, "periods": 1001},
            {**WITNESS, "demand": True, "periods": 3},
            {**WITNESS, "demand": float("nan"), "periods": 3},
            dict(WITNESS),
        )
        for inputs in bad:
            with self.assertRaises(self.V.InputError):
                self.kernel(inputs)

    def test_manifest_binds_the_sealed_statement(self):
        manifest = json.loads((PACKAGE / "function.json").read_text(encoding="utf-8"))
        prov = manifest["provenance"]
        self.assertEqual(prov["research_statement"], "P3.LoopMassBalance")
        self.assertEqual(prov["statement_sha256"], "f00634594133f7edfb49f21bf30203d259cc8dfa7e62a40326bff1da1ea31ac7")
        self.assertEqual(prov["candidate_sha256"], "0e110da9753e71462f1f2613eef5f7aa9e7fd1c6d8b368034fcc5210283a69b3")


if __name__ == "__main__":
    unittest.main()
