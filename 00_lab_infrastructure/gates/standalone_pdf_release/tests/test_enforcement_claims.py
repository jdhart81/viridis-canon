"""Instruction truth regressions; no publisher import or network traffic."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

DIRECTORY = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("enforcement_claims", DIRECTORY / "enforcement_claims.py")
claims_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(claims_module)


class EnforcementClaimsTests(unittest.TestCase):
    def setUp(self):
        self.claims = json.loads((DIRECTORY / "ENFORCEMENT_CLAIMS.json").read_text())

    def test_repository_readme_status_is_current(self):
        readme = (DIRECTORY / "README.md").read_text(encoding="utf-8")
        self.assertEqual(claims_module.replace_status(readme, self.claims), readme)

    def test_truthful_interim_status(self):
        claims_module.validate_model(self.claims)
        self.assertEqual([r["enforced"] for r in self.claims["routes"].values()], [False, True, True])
        status = claims_module.render_status(self.claims)
        self.assertIn("installed dated publisher", status)
        self.assertIn("does not yet enforce it", status)
        self.assertEqual(status.count(claims_module.BEGIN), 1)
        self.assertEqual(status.count(claims_module.END), 1)

    def test_repository_entrypoint_asts_match_claims(self):
        result = claims_module.verify(self.claims, DIRECTORY.parents[2])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["observations"]), 4)

    def test_dated_claim_cannot_be_flipped_without_installed_calls(self):
        self.claims["routes"]["dated"]["enforced"] = True
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "exceeds source observations"):
            claims_module.render_status(self.claims)

    def test_missing_gate_call_fails_even_with_updated_hash(self):
        raw = b"def publish_bundle():\n    print('manuscript_pdf_gate.require_local')\n"
        entry = {"path": "publisher.py", "sha256": hashlib.sha256(raw).hexdigest(),
                 "gate_calls_present": True,
                 "required_calls": [{"function": "publish_bundle", "call": "manuscript_pdf_gate.require_local"}]}
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "AST observation"):
            claims_module.validate_source(raw, entry)

    def test_calls_in_comments_and_nested_functions_do_not_satisfy_call_site(self):
        raw = b"def publish_bundle():\n    # manuscript_pdf_gate.require_local()\n    def unused():\n        manuscript_pdf_gate.require_local()\n"
        entry = {"path": "publisher.py", "sha256": hashlib.sha256(raw).hexdigest(),
                 "gate_calls_present": True,
                 "required_calls": [{"function": "publish_bundle", "call": "manuscript_pdf_gate.require_local"}]}
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "missing AST call"):
            claims_module.validate_source(raw, entry)

    def test_immediate_prepublication_call_requirement_is_checked(self):
        raw = b"def publish_candidate():\n    manuscript_pdf_gate.require_local()\n"
        entry = {"path": "publisher.py", "sha256": hashlib.sha256(raw).hexdigest(),
                 "gate_calls_present": True,
                 "required_calls": [{"function": "publish_candidate", "call": "manuscript_pdf_gate.require_local", "minimum": 2}]}
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "missing AST call"):
            claims_module.validate_source(raw, entry)

    def test_status_replacement_preserves_surrounding_bytes_and_is_idempotent(self):
        text = "prefix\n" + claims_module.BEGIN + "\nold\n" + claims_module.END + "\nsuffix\n"
        updated = claims_module.replace_status(text, self.claims)
        self.assertTrue(updated.startswith("prefix\n"))
        self.assertTrue(updated.endswith("\nsuffix\n"))
        self.assertEqual(claims_module.replace_status(updated, self.claims), updated)

    def test_ambiguous_status_markers_are_rejected(self):
        for text in ("unmarked", claims_module.BEGIN * 2 + claims_module.END):
            with self.subTest(text=text):
                with self.assertRaises(claims_module.EnforcementDrift):
                    claims_module.replace_status(text, self.claims)

    def test_missing_installed_source_claim_is_rejected(self):
        self.claims["routes"]["successor"]["sources"] = [self.claims["routes"]["successor"]["sources"][0]]
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "installed sources required"):
            claims_module.validate_model(self.claims)

    def test_enforced_source_requires_both_local_and_public_calls(self):
        self.claims["routes"]["digest_guard"]["sources"][0]["required_calls"] = []
        with self.assertRaisesRegex(claims_module.EnforcementDrift, "local and public"):
            claims_module.validate_model(self.claims)

    def test_all_green_status_includes_installed_hashes(self):
        route = self.claims["routes"]["dated"]
        installed = next(row for row in route["sources"] if row["root"] == "core" and row.get("enforcement_source", True))
        source = next(row for row in route["sources"] if row["root"] == "repo" and row.get("enforcement_source", True))
        installed.update(sha256=source["sha256"], gate_calls_present=True,
                         required_calls=copy.deepcopy(source["required_calls"]))
        route["enforced"] = True
        status = claims_module.render_status(self.claims)
        self.assertNotIn("does not yet", status)
        for r in self.claims["routes"].values():
            self.assertIn(next(row for row in r["sources"] if row["root"] == "core")["sha256"], status)

    def test_portable_check_does_not_claim_installed_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for route in self.claims["routes"].values():
                for entry in route["sources"]:
                    if entry["root"] != "repo":
                        continue
                    raw = b"def unrelated():\n    pass\n"
                    entry.update(sha256=hashlib.sha256(raw).hexdigest(), gate_calls_present=False, required_calls=[])
                    path = root / entry["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(raw)
                route["enforced"] = False
            result = claims_module.verify(self.claims, root)
            self.assertEqual(result["scope"], "repo_only_installed_not_verified")


if __name__ == "__main__":
    unittest.main()
