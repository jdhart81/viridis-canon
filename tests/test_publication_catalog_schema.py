"""Standard-library contract tests for the public publication-pointer schema."""
from __future__ import annotations

import copy
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from canon_core.catalog import build_catalog
from canon_core.publications import load_publication_joins


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs" / "schemas" / "research-catalog-v1.json"
POINTER_FIELDS = {
    "entity_id", "record_id", "doi", "title", "claim_scope", "disclaimer",
    "public_readback_sha256", "publication_binding_sha256", "certificate_sha256",
}
DISCLAIMER = "logical validity given the model, not empirical validation of its assumptions"


class PublicationCatalogSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = json.loads(SCHEMA.read_text())
        self.items = self.schema["properties"]["publications"]["items"]
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.row = {
            "entity_id": "publication:test-only", "record_id": "23141592",
            "doi": "10.5281/zenodo.23141592", "title": "Test fixture",
            "claim_scope": "A supplied premise implies a stated conditional bound.",
            "disclaimer": DISCLAIMER, "public_readback_sha256": "a" * 64,
            "publication_binding_sha256": "b" * 64, "certificate_sha256": "c" * 64,
        }

    def config(self, row=None):
        path = self.root / "joins.json"
        path.write_text(json.dumps({"standard": "PUBLIC_SCOPED_PUBLICATION_POINTERS_1",
                                   "publications": [row or self.row]}))
        return {"release": "test", "concept_doi": "", "repository": "", "include": [],
                "publication_joins": {"path": "joins.json", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}

    def test_every_builder_top_level_field_is_advertised(self):
        config = self.config()
        path = self.root / "config.json"
        path.write_text(json.dumps(config))
        document = build_catalog(self.root, path)
        self.assertFalse(self.schema["additionalProperties"])
        self.assertLessEqual(set(document), set(self.schema["properties"]))
        self.assertLessEqual(set(self.schema["required"]), set(document))
        self.assertEqual(document["publications"], [self.row])

    def test_publications_is_required_even_for_an_empty_list(self):
        self.assertIn("publications", self.schema["required"])
        self.assertEqual(self.schema["properties"]["publications"]["type"], "array")

    def test_pointer_object_is_closed(self):
        self.assertEqual(self.items["type"], "object")
        self.assertIs(self.items["additionalProperties"], False)
        self.assertEqual(set(self.items["properties"]), POINTER_FIELDS)
        self.assertEqual(set(self.items["required"]), POINTER_FIELDS)

    def test_schema_cannot_advertise_source_admission_fields(self):
        for key in ("status", "canon_eligible", "evidence_class", "tier"):
            self.assertNotIn(key, self.items["properties"])

    def test_nonempty_scope_identity_title_are_required_strings(self):
        for key in ("entity_id", "title", "claim_scope"):
            self.assertEqual(self.items["properties"][key], {"type": "string", "minLength": 1})

    def test_exact_disclaimer_is_schema_bound(self):
        self.assertEqual(self.items["properties"]["disclaimer"], {"const": DISCLAIMER})

    def test_all_three_evidence_hashes_are_strict_lowercase_sha256(self):
        for key in ("public_readback_sha256", "publication_binding_sha256", "certificate_sha256"):
            field = self.items["properties"][key]
            self.assertEqual(field["type"], "string")
            self.assertRegex(self.row[key], field["pattern"])
            for bad in ("", "a" * 63, "A" * 64, "g" * 64, "a" * 65):
                with self.subTest(key=key, value=bad):
                    self.assertIsNone(re.fullmatch(field["pattern"], bad))

    def test_schema_identifier_patterns_exclude_foreign_hosts_and_zero_ids(self):
        fields = self.items["properties"]
        for key, good, bad in (
            ("record_id", "23141592", ("0", "023141592", "foreign")),
            ("doi", "10.5281/zenodo.23141592", ("10.5072/zenodo.23141592", "10.5281/zenodo.0")),
        ):
            self.assertRegex(good, fields[key]["pattern"])
            for value in bad:
                self.assertIsNone(re.fullmatch(fields[key]["pattern"], value))

    def test_runtime_consumer_enforces_same_record_doi_identity(self):
        changed = {**self.row, "doi": "10.5281/zenodo.23141980"}
        with self.assertRaises(ValueError):
            load_publication_joins(self.root, self.config(changed))

    def test_runtime_consumer_rejects_source_admission_injection(self):
        for key, value in (("status", "verified"), ("canon_eligible", True), ("tier", "spine")):
            changed = copy.deepcopy(self.row)
            changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                load_publication_joins(self.root, self.config(changed))


if __name__ == "__main__":
    unittest.main()
