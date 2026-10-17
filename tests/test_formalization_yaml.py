"""formalization.yaml stays in sync with the function manifests and certificates.

Runs in the research-portal workflow; standard library only.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class FormalizationYamlTests(unittest.TestCase):
    def test_is_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_formalization_yaml.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_result_has_lean_module_and_paper(self):
        text = (ROOT / "formalization.yaml").read_text()
        blocks = text.split("\n  - id: ")[1:]
        self.assertGreater(len(blocks), 0)
        for block in blocks:
            self.assertIn("    lean:\n      module: ", block)
            self.assertIn("    paper: ", block)
            self.assertIn("    empirical_validation: ", block)


if __name__ == "__main__":
    unittest.main()
