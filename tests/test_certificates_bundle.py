"""The published certificate bundle stays byte-exact and its index stays current.

Runs in the research-portal workflow (python3 -m unittest discover -s tests).
Standard library only; no Lean required.
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CERTS = ROOT / "certificates"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class CertificateBundleTests(unittest.TestCase):
    def test_every_binding_matches(self):
        verify = _load(CERTS / "verify_bundle.py", "verify_bundle")
        runs = sorted(p for p in CERTS.glob("Run-*") if p.is_dir())
        self.assertGreater(len(runs), 0)
        for run in runs:
            checked, problems, _ = verify.check_run(run)
            self.assertGreater(checked, 0, run.name)
            self.assertEqual(problems, [], f"{run.name}: {problems}")

    def test_index_and_configs_are_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "build_certificates_index.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_index_labels_are_honest(self):
        ix = json.loads((CERTS / "index.json").read_text())
        for r in ix["runs"]:
            self.assertEqual(r["certificate_status"], "LEAN_ZERO_SORRY_CERTIFIED", r["run"])
            self.assertIn(r["depth"]["label"], {"substantial", "elementary"})
            self.assertEqual(set(r["permitted_axioms"]), {"propext", "Quot.sound", "Classical.choice"}, r["run"])
            if r["challenge_identical_to_solution"]:
                self.assertEqual(r["files"]["challenge"]["sha256"], r["files"]["solution"]["sha256"])

    def test_no_credentials_or_private_hosts(self):
        pattern = re.compile(
            r"BEGIN (RSA|OPENSSH|EC|PRIVATE)|ghp_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|"
            r"Bearer [A-Za-z0-9._-]{20,}|138\.197\.18\.27"
        )
        for f in CERTS.rglob("*"):
            if f.is_file() and f.suffix in {".json", ".lean", ".md", ".sh", ".py"}:
                self.assertIsNone(pattern.search(f.read_text(errors="replace")), str(f))


if __name__ == "__main__":
    unittest.main()
