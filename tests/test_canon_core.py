from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from canon_core.canonical import canonical_bytes, canonical_digest
from canon_core.catalog import build_catalog, validate_catalog, write_catalog
from canon_core.model import ResearchRecord


ROOT = Path(__file__).resolve().parents[1]


class CanonicalTests(unittest.TestCase):
    def test_canonical_bytes_ignore_dict_order(self) -> None:
        left = {"b": 2, "a": [1, {"d": 4, "c": 3}]}
        right = {"a": [1, {"c": 3, "d": 4}], "b": 2}
        self.assertEqual(canonical_bytes(left), canonical_bytes(right))

    def test_digest_changes_when_payload_changes(self) -> None:
        self.assertNotEqual(canonical_digest({"a": 1}), canonical_digest({"a": 2}))

    def test_record_digest_roundtrip_shape(self) -> None:
        record = ResearchRecord(
            record_id="demo",
            title="Demo",
            summary="A test record.",
            path="Demo.lean",
            status="working",
            tier="working-corpus",
            visibility="public",
            source_sha256="0" * 64,
        )
        rendered = record.to_dict()
        self.assertEqual(rendered["digest"], canonical_digest(record.payload()))


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = build_catalog(ROOT)

    def test_catalog_has_records(self) -> None:
        self.assertGreater(self.catalog["stats"]["records"], 40)

    def test_catalog_digest_validates(self) -> None:
        self.assertEqual(validate_catalog(self.catalog), [])

    def test_record_ids_and_paths_are_unique(self) -> None:
        records = self.catalog["records"]
        self.assertEqual(len(records), len({record["record_id"] for record in records}))
        self.assertEqual(len(records), len({record["path"] for record in records}))

    def test_intelligence_bound_is_spine(self) -> None:
        record = next(
            record
            for record in self.catalog["records"]
            if record["record_id"] == "intelligence-bound"
        )
        self.assertEqual(record["status"], "verified")
        self.assertEqual(record["tier"], "spine")

    def test_ai_safety_is_quarantined(self) -> None:
        record = next(
            record
            for record in self.catalog["records"]
            if record["record_id"] == "ai-safety-quarantined"
        )
        self.assertEqual(record["status"], "quarantined")
        self.assertEqual(record["integrity"], "quarantined")

    def test_public_output_does_not_leak_private_records(self) -> None:
        self.assertTrue(
            all(record["visibility"] == "public" for record in self.catalog["records"])
        )

    def test_formal_and_empirical_status_are_separate(self) -> None:
        verified = [
            record for record in self.catalog["records"] if record["status"] == "verified"
        ]
        self.assertTrue(verified)
        self.assertTrue(
            all(record["external_validation"] == "not-recorded" for record in verified)
        )
        self.assertTrue(all("empirical" in record["caveat"].lower() for record in verified))

    def test_every_record_carries_source_and_record_digests(self) -> None:
        for record in self.catalog["records"]:
            self.assertEqual(len(record["source_sha256"]), 64)
            self.assertEqual(len(record["digest"]), 64)

    def test_every_public_record_has_an_abstract_and_readable_artifact(self) -> None:
        for record in self.catalog["records"]:
            self.assertGreaterEqual(len(record["abstract"].strip()), 20, record["path"])
            self.assertTrue(record["source_url"].startswith("https://"), record["path"])
            self.assertTrue(record["paper_url"].startswith("https://"), record["path"])

    def test_published_records_link_to_their_declared_doi(self) -> None:
        published = [
            record
            for record in self.catalog["records"]
            if record["doi"]
        ]
        self.assertGreaterEqual(len(published), 35)
        for record in published:
            self.assertEqual(
                record["paper_url"],
                f"https://doi.org/{record['doi']}",
                record["path"],
            )

    def test_write_catalog_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            one = Path(temp) / "one.json"
            two = Path(temp) / "two.json"
            write_catalog(ROOT, one)
            write_catalog(ROOT, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(json.loads(one.read_text()), self.catalog)

    def test_tampered_catalog_is_rejected(self) -> None:
        tampered = json.loads(json.dumps(self.catalog))
        tampered["records"][0]["title"] = "Tampered"
        errors = validate_catalog(tampered)
        self.assertTrue(any("catalog_digest" in error for error in errors))
        self.assertTrue(any("digest mismatch" in error for error in errors))

    def test_private_workspace_records_require_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "public.md").write_text("# Public\n", encoding="utf-8")
            (root / "private.md").write_text("# Private\n", encoding="utf-8")
            config = {
                "release": "test",
                "concept_doi": "",
                "repository": "",
                "include": ["*.md"],
                "manifest": "",
                "curation": {
                    "private.md": {
                        "title": "Private",
                        "visibility": "private"
                    }
                }
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            public = build_catalog(root, config_path=config_path)
            workspace = build_catalog(
                root,
                config_path=config_path,
                include_private=True,
            )
            self.assertEqual(public["publication_scope"], "public")
            self.assertEqual(public["stats"]["records"], 1)
            self.assertEqual(workspace["publication_scope"], "workspace")
            self.assertEqual(workspace["stats"]["records"], 2)
            self.assertEqual(validate_catalog(public), [])
            self.assertEqual(validate_catalog(workspace), [])

    def test_default_private_visibility_protects_workspace_catalogs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "research.md").write_text("# Internal result\n", encoding="utf-8")
            config = {
                "release": "test",
                "concept_doi": "",
                "repository": "",
                "include": ["*.md"],
                "manifest": "",
                "default_visibility": "private",
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            public = build_catalog(root, config_path=config_path)
            workspace = build_catalog(
                root,
                config_path=config_path,
                include_private=True,
            )
            self.assertEqual(public["stats"]["records"], 0)
            self.assertEqual(workspace["records"][0]["visibility"], "private")
            self.assertEqual(workspace["records"][0]["source_url"], "")
            self.assertEqual(workspace["records"][0]["paper_url"], "")


if __name__ == "__main__":
    unittest.main()
