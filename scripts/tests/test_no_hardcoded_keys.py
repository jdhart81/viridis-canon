"""Fail on credential-shaped Aristotle literals in tracked working-tree files."""

import os
from pathlib import Path
import re
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from aristotle_env import get_api_key


class CredentialTests(unittest.TestCase):
    def test_no_hardcoded_keys(self):
        pattern = re.compile(rb"arstl" + rb"[A-Za-z0-9_-]{20,}")
        tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        findings = []
        for name in tracked.split(b"\0"):
            if not name:
                continue
            path = ROOT / os.fsdecode(name)
            if not path.is_file():
                continue
            for number, line in enumerate(path.read_bytes().splitlines(), 1):
                if pattern.search(line):
                    findings.append(f"{os.fsdecode(name)}:{number}")
        self.assertFalse(findings, "Credential-shaped literals at: " + ", ".join(findings))

    def test_missing_key_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(SystemExit, "ARISTOTLE_API_KEY"):
                get_api_key()

    def test_empty_key_fails(self):
        for value in ("", "   "):
            with patch.dict(os.environ, {"ARISTOTLE_API_KEY": value}, clear=True):
                with self.assertRaisesRegex(SystemExit, "ARISTOTLE_API_KEY"):
                    get_api_key()

    def test_environment_key_is_used(self):
        with patch.dict(os.environ, {"ARISTOTLE_API_KEY": "unit-test-value"}, clear=True):
            self.assertEqual(get_api_key(), "unit-test-value")


if __name__ == "__main__":
    unittest.main()
