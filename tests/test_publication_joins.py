import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from canon_core.publications import load_publication_joins
from canon_core.catalog import build_catalog, validate_catalog_sources


class PublicationJoinTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / "joins.json"
        self.row = {"entity_id": "publication:foundation", "record_id": "23141592", "doi": "10.5281/zenodo.23141592", "title": "Exact title", "claim_scope": "Named supplied premises imply the minimum rate bound.", "disclaimer": "logical validity given the model, not empirical validation of its assumptions", "public_readback_sha256": "a" * 64, "publication_binding_sha256": "b" * 64, "certificate_sha256": "c" * 64}

    def config(self, rows=None):
        self.path.write_text(json.dumps({"standard": "PUBLIC_SCOPED_PUBLICATION_POINTERS_1", "publications": rows if rows is not None else [self.row]}))
        return {"publication_joins": {"path": "joins.json", "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest()}}

    def test_explicit_pointer_is_separate_from_source_admission(self):
        rows = load_publication_joins(self.root, self.config())
        self.assertEqual(rows, [self.row])
        self.assertNotIn("status", rows[0])
        self.assertNotIn("canon_eligible", rows[0])

    def test_one_byte_snapshot_change_rejects(self):
        config = self.config()
        self.path.write_bytes(self.path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_publication_joins(self.root, config)

    def test_foreign_doi_missing_evidence_and_eligibility_injection_reject(self):
        for changes in ({"doi": "10.5281/zenodo.22236387"}, {"certificate_sha256": ""}, {"canon_eligible": True}, {"status": "verified"}, {"disclaimer": "empirically verified"}):
            with self.subTest(changes=changes):
                row = {**self.row, **changes}
                with self.assertRaises(ValueError):
                    load_publication_joins(self.root, self.config([row]))

    def test_duplicate_pointer_rejects(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_publication_joins(self.root, self.config([self.row, copy.deepcopy(self.row)]))

    def test_missing_optional_pointer_file_defaults_to_no_publications(self):
        self.assertEqual(load_publication_joins(self.root, {}), [])

    def test_symlink_or_outside_file_rejects(self):
        config = self.config()
        link = self.root / "link.json"
        link.symlink_to(self.path)
        for path in ("link.json", "../joins.json", str(self.path)):
            with self.subTest(path=path), self.assertRaises(ValueError):
                load_publication_joins(self.root, {"publication_joins": {**config["publication_joins"], "path": path}})

    def test_catalog_rejects_changed_or_missing_explicit_publication_projection(self):
        config = {**self.config(), "release": "test", "concept_doi": "", "repository": "", "include": []}
        path = self.root / "config.json"
        path.write_text(json.dumps(config))
        document = build_catalog(self.root, path)
        self.assertEqual(validate_catalog_sources(document, self.root, path), [])
        changed = copy.deepcopy(document)
        changed["publications"][0]["doi"] = "10.5281/zenodo.22236387"
        self.assertTrue(validate_catalog_sources(changed, self.root, path))
        del document["publications"]
        self.assertTrue(validate_catalog_sources(document, self.root, path))


if __name__ == "__main__":
    unittest.main()
