from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from canon_core.canonical import canonical_digest
from canon_core.catalog import build_catalog, validate_catalog, validate_catalog_sources, _publication_index_consumers
from canon_core.cli import _parser, main


class CatalogCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "Demo.lean"
        self.source.write_text("import Mathlib\ntheorem demo (a : Real) : 0 <= a^2 := by positivity\n")
        self.digest = hashlib.sha256(self.source.read_bytes()).hexdigest()
        (self.root / "SPINE_MANIFEST.txt").write_text("Demo.lean\n")
        self.config = {"release": "test", "concept_doi": "", "repository": "",
                       "include": ["*.lean"], "manifest": "SPINE_MANIFEST.txt",
                       "curation": {"Demo.lean": {"title": "Original theorem title", "tier": "spine"}}}
        self.config_path = self.root / "config.json"
        self.config_path.write_text(json.dumps(self.config))
        self.entity = {"id": "file:Demo.lean", "path": "Demo.lean", "status": "CERTIFIED",
                       "certificate_valid": True, "certificate": "missing-certificate.json",
                       "sha256": self.digest}
        self.ledger = {"tree_root": str(self.root), "file_entities": [self.entity], "run_entities": []}
        self.ledger_path = self.root / "corpus_ledger.json"
        self.save_ledger()
        self.claims, _ = _publication_index_consumers()
        self.inspection = {"valid": True, "candidate_sha256": self.digest, "sha256": "a" * 64}
        self.gate = {"status": "PASS", "exact_publication_binding": True,
                     "claim_gate": {"status": "PASS", "claims": [
                         {"status": "PASS", "english_claim": "An explicit model inequality",
                          "lean_theorem": "demo", "nonvacuity_obligation": "witness",
                          "evidence_class": "FORMALLY_VERIFIED"}]}}

    def tearDown(self):
        self.temp.cleanup()

    def save_ledger(self):
        self.ledger_path.write_text(json.dumps(self.ledger))

    def record(self, *, ledger=True, enforce=False, gate=None):
        publication = SimpleNamespace(evaluate_publication=Mock(return_value=gate or self.gate))
        with patch("canon_core.catalog._publication_index_consumers", return_value=(self.claims, publication)), \
             patch.object(self.claims, "inspect_entity_certificate", return_value=self.inspection):
            doc = build_catalog(self.root, self.config_path,
                                ledger_path=self.ledger_path if ledger else None,
                                enforce_coverage=enforce)
        return doc["records"][0], publication

    def test_clean_spine_without_ledger_never_labels_verified(self):
        record, publication = self.record(ledger=False, enforce=True)
        self.assertEqual(record["status"], "working")
        self.assertEqual(record["tier"], "working-corpus")
        self.assertEqual(record["title"], "Original theorem title")
        self.assertIn("UNCERTIFIED", record["caveat"])
        publication.evaluate_publication.assert_not_called()

    def test_current_source_hash_mismatch_holds_before_publication_consumer(self):
        self.entity["sha256"] = "0" * 64
        self.save_ledger()
        record, publication = self.record(enforce=True)
        self.assertIn("INDEX_SOURCE_HASH_MISMATCH", record["metadata"]["verification_coverage"]["reasons"])
        self.assertEqual(record["status"], "working")
        publication.evaluate_publication.assert_not_called()

    def test_certificate_candidate_hash_mismatch_holds(self):
        self.inspection["candidate_sha256"] = "0" * 64
        record, publication = self.record(enforce=True)
        self.assertIn("CERTIFIED_CANDIDATE_HASH_MISMATCH", record["metadata"]["verification_coverage"]["reasons"])
        publication.evaluate_publication.assert_not_called()

    def test_certificate_without_exact_manuscript_binding_stays_held(self):
        gate = {"status": "HOLD", "exact_publication_binding": False, "reasons": ["missing binding"]}
        record, _ = self.record(enforce=True, gate=gate)
        self.assertFalse(record["metadata"]["verification_coverage"]["canon_eligible"])
        self.assertEqual(record["status"], "working")

    def test_trivial_bound_claim_cannot_enter_verified_catalog(self):
        self.gate["claim_gate"]["claims"][0]["evidence_class"] = "CERTIFIED_TRIVIAL"
        record, _ = self.record(enforce=True)
        self.assertEqual(record["status"], "working")
        self.assertIn("MISSING_OR_TRIVIAL_BOUND_CLAIMS", record["metadata"]["verification_coverage"]["reasons"])

    def test_missing_claim_completeness_status_never_passes(self):
        self.gate["claim_gate"].pop("status")
        record, _ = self.record(enforce=True)
        self.assertEqual(record["status"], "working")

    def test_unsafe_environment_and_vacuous_entities_are_quarantined(self):
        for status, flags in [("UNSOUND_ENVIRONMENT", []), ("CERTIFIED", [{"kind": "vacuous_shape"}])]:
            with self.subTest(status=status, flags=flags):
                self.entity.update(status=status, flags=flags)
                self.save_ledger()
                record, publication = self.record(enforce=True)
                self.assertEqual(record["status"], "quarantined")
                self.assertFalse(record["metadata"]["verification_coverage"]["canon_eligible"])
                publication.evaluate_publication.assert_not_called()

    def test_proven_binding_is_report_only_until_separate_flag(self):
        report, _ = self.record()
        enforced, publication = self.record(enforce=True)
        coverage = report["metadata"]["verification_coverage"]
        self.assertEqual(report["status"], "working")
        self.assertTrue(coverage["proposed_canon_eligible"])
        self.assertFalse(coverage["canon_eligible"])
        self.assertEqual(enforced["status"], "verified")
        self.assertEqual(enforced["tier"], "spine")
        self.assertEqual(enforced["title"], report["title"])
        self.assertEqual(enforced["source_sha256"], report["source_sha256"])
        self.assertEqual(publication.evaluate_publication.call_args.kwargs["enforce"], True)

    def test_external_doi_must_match_the_same_bound_artifact(self):
        self.config["doi_by_path"] = {"Demo.lean": "10.5281/zenodo.123"}
        self.config_path.write_text(json.dumps(self.config))
        self.gate["doi"] = "10.5281/zenodo.456"
        record, _ = self.record(enforce=True)
        self.assertEqual(record["status"], "working")
        self.assertIn("PUBLIC_DOI_NOT_BOUND_TO_THIS_ARTIFACT", record["metadata"]["verification_coverage"]["reasons"])

    def test_copied_ledger_verdict_cannot_replace_missing_certificate(self):
        # No mocks for either acceptance consumer: a clean source and copied
        # CERTIFIED ledger row cannot supply its nonexistent certificate.
        record = build_catalog(self.root, self.config_path, ledger_path=self.ledger_path,
                               enforce_coverage=True)["records"][0]
        self.assertEqual(record["status"], "working")
        self.assertIn("COVERAGE_CONSUMER_HOLD", record["metadata"]["verification_coverage"]["reasons"])

    def document_for_record(self, record):
        payload = {"records": [record], "publication_scope": "public"}
        return {**payload, "catalog_digest": canonical_digest(payload)}

    def test_digest_consistent_historical_verified_record_is_rejected(self):
        record, _ = self.record(ledger=False)
        record["status"] = "verified"
        record["integrity"] = "gate-passed"
        record["tier"] = "spine"
        record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
        errors = validate_catalog(self.document_for_record(record))
        self.assertTrue(any("protected eligibility lacks" in error for error in errors))

    def test_digest_consistent_spine_alone_is_rejected(self):
        record, _ = self.record(ledger=False)
        record["tier"] = "spine"
        record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
        self.assertTrue(validate_catalog(self.document_for_record(record)))

    def test_verified_tag_and_unsupported_summary_counts_are_rejected(self):
        record, _ = self.record(ledger=False)
        record["tags"].append("verified")
        record["digest"] = canonical_digest({k: v for k, v in record.items() if k != "digest"})
        document = self.document_for_record(record)
        document["stats"] = {"verified": 26, "spine": 30, "working": 1, "quarantined": 0}
        document["catalog_digest"] = canonical_digest({k: v for k, v in document.items() if k != "catalog_digest"})
        errors = validate_catalog(document)
        self.assertTrue(any("protected eligibility lacks" in error for error in errors))
        self.assertTrue(any("stats.verified" in error for error in errors))
        self.assertTrue(any("stats.spine" in error for error in errors))

    def test_copied_full_pass_cannot_replace_live_validation(self):
        record, _ = self.record(enforce=True)
        errors = validate_catalog(self.document_for_record(record), root=self.root,
                                  config_path=self.config_path, ledger_path=self.ledger_path)
        self.assertTrue(any("current publication coverage HOLD" in error for error in errors))

    def test_validation_reconsumes_current_evidence_and_source_hash(self):
        record, _ = self.record(enforce=True)
        publication = SimpleNamespace(evaluate_publication=Mock(return_value=self.gate))
        with patch("canon_core.catalog._publication_index_consumers", return_value=(self.claims, publication)), \
             patch.object(self.claims, "inspect_entity_certificate", return_value=self.inspection):
            self.assertEqual(validate_catalog(self.document_for_record(record), root=self.root,
                                             config_path=self.config_path, ledger_path=self.ledger_path), [])
            self.source.write_bytes(self.source.read_bytes() + b" ")
            self.assertTrue(any("source hash differs" in error for error in validate_catalog(
                self.document_for_record(record), root=self.root, config_path=self.config_path,
                ledger_path=self.ledger_path)))
        publication.evaluate_publication.assert_called_once()

    def test_mirror_drift_ssot_is_never_admitted(self):
        self.entity["status"] = "MIRROR_DRIFT"
        self.save_ledger()
        record, publication = self.record(enforce=True)
        self.assertEqual(record["status"], "working")
        self.assertIn("LEDGER_ENTITY_NOT_CERTIFIED", record["metadata"]["verification_coverage"]["reasons"])
        publication.evaluate_publication.assert_not_called()

    def test_source_prefix_is_exact_not_a_name_guess(self):
        self.entity["path"] = "mirror/Demo.lean"
        (self.root / "mirror").mkdir()
        (self.root / "mirror/Demo.lean").write_bytes(self.source.read_bytes())
        self.save_ledger()
        self.config["coverage_source_prefix"] = "mirror"
        self.config_path.write_text(json.dumps(self.config))
        record, _ = self.record(enforce=True)
        self.assertEqual(record["status"], "verified")
        self.config["coverage_source_prefix"] = "../other"
        self.config_path.write_text(json.dumps(self.config))
        record, _ = self.record(enforce=True)
        self.assertEqual(record["status"], "working")

    def test_cli_defaults_report_only_and_forwards_explicit_evidence(self):
        args = _parser().parse_args(["build"])
        self.assertFalse(args.enforce_coverage)
        self.assertIsNone(args.ledger)
        with patch("canon_core.cli.write_catalog", return_value={"stats": {"records": 1, "verified": 0},
                                                               "catalog_digest": "a" * 64}) as write:
            self.assertEqual(main(["build", "--root", str(self.root), "--ledger", str(self.ledger_path),
                                   "--source-prefix", "mirror", "--enforce-coverage"]), 0)
        self.assertEqual(write.call_args.kwargs["ledger_path"], self.ledger_path)
        self.assertEqual(write.call_args.kwargs["source_prefix"], "mirror")
        self.assertTrue(write.call_args.kwargs["enforce_coverage"])

    def test_public_source_check_keeps_ssot_diagnostics_but_requires_exact_inventory(self):
        record, _ = self.record()
        self.assertEqual(validate_catalog_sources(self.document_for_record(record), self.root, self.config_path), [])
        record["source_sha256"] = "b" * 64
        self.assertTrue(any("source_sha256" in error for error in validate_catalog_sources(
            self.document_for_record(record), self.root, self.config_path)))
        self.assertTrue(validate_catalog_sources({"records": []}, self.root, self.config_path))

    def test_public_source_check_does_not_replace_live_eligibility_validation(self):
        record, _ = self.record(enforce=True)
        document = self.document_for_record(record)
        self.assertEqual(validate_catalog_sources(document, self.root, self.config_path), [])
        self.assertTrue(validate_catalog(document, root=self.root, config_path=self.config_path))


if __name__ == "__main__":
    unittest.main()
