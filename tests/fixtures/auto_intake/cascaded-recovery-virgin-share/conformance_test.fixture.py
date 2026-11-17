"""Conformance of cascaded-recovery-virgin-share with viridis-research P3.CascadedRecovery.

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

PACKAGE = ROOT / "research" / "cascaded-recovery-virgin-share"


class CascadedRecoveryConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kernel = staticmethod(_load_runner(PACKAGE, ROOT))
        cls.V = load_runtime(ROOT)

    def test_every_statement_part_holds(self):
        self.assertEqual(conformance_problems(ROOT, PACKAGE), [])

    def test_lean_witnesses(self):
        two = self.kernel({"recovery_fractions": [0.5, 0.5]})
        self.assertEqual((two["virgin_share"], two["uniform_lower_bound"]), (0.25, 0.25))
        self.assertTrue(two["cascade_strictly_better"])
        three = self.kernel({"recovery_fractions": [0.5, 0.25, 0]})
        self.assertEqual((three["virgin_share"], three["uniform_lower_bound"]), (0.375, 0.125))

    def test_strictness_needs_both_conditions(self):
        self.assertFalse(self.kernel({"recovery_fractions": [0, 0.5]})["cascade_strictly_better"])
        self.assertEqual(self.kernel({"recovery_fractions": [0, 0.5]})["cascade_gain"], 0.0)
        self.assertFalse(self.kernel({"recovery_fractions": [0.5, 1]})["cascade_strictly_better"])

    def test_out_of_range_stages_are_refused(self):
        for bad in ([2, 0.5], [-1, 0.5], [], [True], ["x"]):
            with self.assertRaises(self.V.InputError):
                self.kernel({"recovery_fractions": bad})

    def test_manifest_binds_the_sealed_statement(self):
        manifest = json.loads((PACKAGE / "function.json").read_text(encoding="utf-8"))
        prov = manifest["provenance"]
        self.assertEqual(prov["research_statement"], "P3.CascadedRecovery")
        self.assertEqual(prov["statement_sha256"], "a4e3f3c269b81a1d5dacde1535f0112654d5d4c5203e9a01a444bc4edcfbb115")
        self.assertEqual(prov["candidate_sha256"], "eaafbaaa17a780833c6d955cae570ece4c6676fd241accb2bf52bac6773b8f1c")


if __name__ == "__main__":
    unittest.main()
