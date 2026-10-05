import importlib.util
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("coverage_public_index", ROOT / "scripts/generate_public_index.py")
public_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(public_index)


class PublicIndexQuarantineTests(unittest.TestCase):
    def test_environment_quarantine_and_vacuity_do_not_enter_eligible_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = {
                "tree_root": tmp,
                "file_entities": [
                    {"id": "file:origin", "path": "Origin.lean", "status": "UNSOUND_ENVIRONMENT"},
                    {"id": "file:vacuous", "path": "Vacuous.lean", "status": "CLEAN_UNCERTIFIED",
                     "flags": [{"kind": "vacuous_shape"}]},
                    {"id": "file:axiom", "path": "Gaia.lean", "status": "UNSOUND"},
                ],
                "run_entities": [],
            }
            rendered = public_index.render_index(ledger)
            canon = json.loads(rendered["CANON_INDEX.json"])
            self.assertEqual(canon["entries"], [])
            self.assertEqual(set(canon["quarantined"]), {"file:origin", "file:vacuous", "file:axiom"})
            self.assertIn("UNSOUND_ENVIRONMENT", rendered["README.md"])
            self.assertIn("vacuous source promotion is prohibited", rendered["README.md"])

    def test_public_readme_never_displays_absolute_certification_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = {"tree_root": tmp, "file_entities": [], "run_entities": []}
            rendered = public_index.render_index(ledger)
            self.assertNotIn(tmp, rendered["README.md"])
            self.assertIn("canonical certification mirror", rendered["README.md"])
            for content in rendered.values():
                self.assertNotIn(tmp, content)
                self.assertNotIn("/Users/", content)
                self.assertNotIn("/private/tmp/", content)

    def test_public_json_preserves_diagnostics_and_claim_scope_without_known_absolute_roots(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = {"id": "publication:held", "path": "held", "status": "CERTIFIED",
                     "registration_revalidated": True, "publication_registration_status": "HOLD_NO_CLAIM_MAP",
                     "doi": "10.5281/zenodo.22236409"}
            ledger = {"tree_root": tmp, "file_entities": [], "run_entities": [], "publication_entities": [entry]}
            reason = "ValueError: claim-binding gate held: FileNotFoundError: '" + tmp + "/held/claim_binding.json'"
            generation = "generation diagnostic at " + str(public_index.GENERATION_ROOT) + "/Run-187/source.lean"
            gate = {"status": "HOLD", "reasons": [reason, generation]}
            with patch.object(public_index, "evaluate_publication", return_value=gate):
                rendered = public_index.render_index(ledger)
            registration = json.loads(rendered["ZENODO_DESCRIPTIONS.json"])["publication_registrations"][0]
            self.assertEqual(registration["gate_reasons"], [reason.replace(tmp, "[canonical mirror]"), generation.replace(str(public_index.GENERATION_ROOT), "[generation root]")])
            self.assertEqual(registration["label"], "UNCERTIFIED")
            self.assertEqual(gate["reasons"], [reason, generation])
            self.assertEqual(ledger["tree_root"], tmp)
            nested = {"description": {"errors": [reason, generation], "claim_scope": "supplied HQuad implies the scalar ceiling"}}
            projected = public_index._public_strings(nested, Path(tmp))
            self.assertEqual(projected["description"]["claim_scope"], nested["description"]["claim_scope"])
            for content in rendered.values():
                self.assertNotIn(tmp, content)
                self.assertNotIn("/Users/", content)
                self.assertNotIn("/tmp/", content)
            encoded = json.dumps(projected)
            self.assertNotIn(tmp, encoded)
            self.assertNotIn(str(public_index.GENERATION_ROOT), encoded)
            self.assertIn("claim_binding.json", encoded)
            self.assertIn("FileNotFoundError", encoded)

    def test_uncategorized_status_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = {"tree_root": tmp, "file_entities": [
                {"id": "file:unknown", "path": "Unknown.lean", "status": "MANIFEST_VERIFIED"}
            ], "run_entities": []}
            with self.assertRaisesRegex(ValueError, "unpartitioned ledger status"):
                public_index.render_index(ledger)

    def test_quarantine_retains_evidence_instead_of_editing_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "Origin.lean"
            original = b"axiom physical_assumption : False\n"
            source.write_bytes(original)
            ledger = {"tree_root": tmp, "file_entities": [
                {"id": "file:origin", "path": "Origin.lean", "status": "UNSOUND_ENVIRONMENT"}
            ], "run_entities": []}
            public_index.render_index(ledger)
            self.assertEqual(source.read_bytes(), original)

    def test_publication_join_requires_current_gate_exact_binding_and_same_doi(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = {"id": "publication:corrected", "path": "corrected", "status": "CERTIFIED",
                     "registration_revalidated": True, "publication_registration_status": "PASS",
                     "doi": "10.5281/zenodo.23141980"}
            ledger = {"tree_root": tmp, "file_entities": [], "run_entities": [], "publication_entities": [entry]}
            good = {"status": "PASS", "exact_publication_binding": True, "doi": entry["doi"],
                    "claim_gate": {"claims": [{"lean_theorem": "scalar", "english_claim": "supplied HQuad implies the scalar ceiling"}]}}
            for gate, expected in ((good, 1), ({**good, "doi": "10.5281/zenodo.22236387"}, 0),
                                   ({**good, "exact_publication_binding": False}, 0), ({**good, "status": "HOLD"}, 0)):
                with self.subTest(gate=gate), patch.object(public_index, "evaluate_publication", return_value=gate):
                    rendered = public_index.render_index(ledger)
                    self.assertEqual(len(json.loads(rendered["CANON_INDEX.json"])["entries"]), expected)
            entry["registration_revalidated"] = False
            with patch.object(public_index, "evaluate_publication", return_value=good):
                self.assertEqual(json.loads(public_index.render_index(ledger)["CANON_INDEX.json"])["entries"], [])


if __name__ == "__main__":
    unittest.main()
