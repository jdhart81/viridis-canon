"""Access pointers preserve claim labels and never attach papers to Lean sources."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from canon_core.canonical import canonical_digest
from canon_core.manuscript_access import (ACCESS_FIELDS, HOLD, LINKED, load_mapping,
                                         project_access, validate_access_fields)
from canon_core.catalog import build_catalog, validate_catalog

ROOT = Path(__file__).resolve().parents[1]


class ManuscriptAccessTests(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT / "docs/data/catalog.json").read_text())
        self.config = json.loads((ROOT / "catalog/config.json").read_text())
        self.mapping, self.mapping_sha = load_mapping(ROOT, self.config)

    def project(self, mapping=None):
        return project_access(self.catalog["publications"], self.catalog["methods_digests"],
                              self.mapping if mapping is None else mapping, self.mapping_sha)

    def test_all_explicit_papers_and_each_digest_note_have_exact_direct_links(self):
        publications, digests, report = self.project()
        self.assertEqual(report["linked_paper_entries"], len(publications) + sum(len(d["notes"]) for d in digests))
        for row in publications:
            validate_access_fields(row, row["record_id"])
        for group in digests:
            self.assertNotIn("pdf_url", group)
            self.assertFalse(group["certifies"])
            for note in group["notes"]:
                validate_access_fields(note, group["record_id"], note["run_id"])
                self.assertEqual(note["pdf_access"]["status"], LINKED)

    def test_access_projection_preserves_all_scientific_scope_and_certification_fields(self):
        publications, digests, _ = self.project()
        def strip(row): return {key: value for key, value in row.items() if key not in ACCESS_FIELDS}
        self.assertEqual([strip(row) for row in publications], [strip(row) for row in self.catalog["publications"]])
        for before, after in zip(self.catalog["methods_digests"], digests):
            self.assertEqual({k: v for k, v in before.items() if k != "notes"}, {k: v for k, v in after.items() if k != "notes"})
            self.assertEqual([strip(row) for row in before["notes"]], [strip(row) for row in after["notes"]])

    def test_no_access_is_invented_for_lean_only_records_or_ecochain_gap(self):
        self.assertTrue(all("pdf_url" not in row for row in self.catalog["records"]))
        _, _, report = self.project()
        gap = next(row for row in report["unresolved"] if row.get("record_id") == "20467431")
        self.assertNotIn("pdf_url", gap)
        self.assertIn("UNCOVERED", gap["status"])
        self.assertEqual(report["status"], "HOLD_UNRESOLVED_MANUSCRIPTS")

    def test_missing_mapping_has_explicit_hold_without_selecting_another_pdf(self):
        changed = copy.deepcopy(self.mapping)
        removed = changed["bindings"].pop(0)
        publications, digests, _ = self.project(changed)
        rows = publications + [note for group in digests for note in group["notes"]]
        row = next(item for item in rows if item["entity_id"] == removed["entity_id"])
        self.assertIsNone(row["pdf_url"])
        self.assertEqual(row["pdf_access"]["status"], HOLD)

    def test_ambiguous_and_unknown_source_only_entity_mappings_refuse(self):
        for kind in ("duplicate", "source_only"):
            changed = copy.deepcopy(self.mapping)
            if kind == "duplicate": changed["bindings"].append(copy.deepcopy(changed["bindings"][0]))
            else: changed["bindings"][0]["entity_id"] = "source:unrelated-lean-file"
            with self.subTest(kind=kind), self.assertRaises(ValueError): self.project(changed)

    def test_wrong_record_or_wrong_run_archive_member_refuses(self):
        for key, value in (("record_id", "999"), ("archive_member", "notes/Run-999/paper.pdf")):
            changed = copy.deepcopy(self.mapping)
            row = next(item for item in changed["bindings"] if item["run_id"])
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): self.project(changed)

    def test_access_cannot_inject_verification_or_foreign_host(self):
        publications, _, _ = self.project()
        row = publications[0]
        for change in ({"pdf_url": "https://example.invalid/paper.pdf"},
                       {"pdf_access": {**row["pdf_access"], "certifies": True}},
                       {"pdf_access": {**row["pdf_access"], "status": "CERTIFIED"}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_access_fields({**row, **change}, row["record_id"])

    def test_mapping_hash_tamper_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); path = root / "mapping.json"
            path.write_text(json.dumps(self.mapping))
            config = {"manuscript_access": {"path": "mapping.json", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SHA-256"): load_mapping(root, config)

    def test_builder_uses_hash_bound_mapping_and_preserves_deterministic_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for key in ("publication_joins", "methods_digest_joins", "manuscript_access"):
                value = self.config[key]
                source = ROOT / value["path"]
                # The existing joins live at repository-relative configured paths.
                target = root / value["path"]; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
            config = {key: self.config[key] for key in ("release", "concept_doi", "repository", "publication_joins", "methods_digest_joins", "manuscript_access")}
            config["include"] = []
            path = root / "config.json"; path.write_text(json.dumps(config))
            first = build_catalog(root, path); second = build_catalog(root, path)
            self.assertEqual(first, second)
            self.assertEqual(first["catalog_digest"], canonical_digest({k: v for k, v in first.items() if k != "catalog_digest"}))
            self.assertEqual(validate_catalog(first), [])
            self.assertTrue(all(row["pdf_url"] for row in first["publications"]))

    def test_checked_catalog_digest_covers_access_fields(self):
        payload = {k: v for k, v in self.catalog.items() if k != "catalog_digest"}
        self.assertEqual(canonical_digest(payload), self.catalog["catalog_digest"])
        payload["publications"][0]["pdf_url"] += "?tamper=1"
        self.assertNotEqual(canonical_digest(payload), self.catalog["catalog_digest"])


if __name__ == "__main__":
    unittest.main()
