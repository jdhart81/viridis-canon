"""Inert synthetic public services; never import Core or contact a provider."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))
import postpublication_sync as sync
from deadline import Budget


class PublicService:
    def __init__(self, catalog, commit):
        self.catalog, self.commit = copy.deepcopy(catalog), commit
        self.calls, self.pinned = [], {}
        self.registry, self.map = {}, {}
        self.persistent_map_mutation = None
        self.uncertain_callback = False

    def project(self):
        rows = []
        for source in self.catalog["records"]:
            coverage = source.get("metadata", {}).get("verification_coverage")
            verified = sync.expected_label(source) == "VERIFIED"
            quarantine = source["status"] == "quarantined"
            rows.append({"record_id": source["record_id"], "title": source["title"], "path": source["path"],
                "doi": source["doi"], "canon_status": source["status"], "canon_integrity": source["integrity"],
                "source_sha256": source["source_sha256"], "certification_label": sync.expected_label(source),
                "verification_coverage": copy.deepcopy(coverage),
                "certification_detail": coverage.get("label", "No current hash-bound certification coverage is recorded.") if coverage else "No current hash-bound certification coverage is recorded.",
                "certification_scope": "Current public Canon classification; not an empirical or production certificate",
                "certification_authority": False, "caveat": source.get("caveat", ""),
                "kernel_state": "QUARANTINED" if quarantine else "KERNEL_CANDIDATE" if verified else "NOT_ELIGIBLE",
                "research_state": "QUARANTINED" if quarantine else "ZERO_SORRY_RESEARCH" if verified else "CANON_WORKING",
                "os_tier": "reference", "function_ids": [], "module_id": "", "decision_tree_paths": [],
                "disposition": "QUARANTINED" if quarantine else "REFERENCE_ONLY", "runtime_binding": None})
        registry = {"standard": "VOS-CANON-KERNEL-REGISTRY-3", "catalog_digest": self.catalog["catalog_digest"],
            "canon_commit": self.commit, "record_count": len(rows), "records": rows,
            "runtime_source": {"commit": "b" * 40, "metadata_is_runtime_activation": False},
            "policy": {k: False for k in ["automatic_certification_authority", "automatic_decision_tree_activation", "automatic_module_activation"]},
            "stats": {"records": len(rows), "kernel_candidates": sum(sync.expected_label(r) == "VERIFIED" for r in self.catalog["records"])}}
        decision_tree = {"schema_version": 3, **{k: copy.deepcopy(registry[k]) for k in ["catalog_digest", "canon_commit", "record_count", "runtime_source"]},
            "authority": {"automatic_kernel_activation": False},
            "stats": {"canon_records": len(rows), "kernel_candidate_records": registry["stats"]["kernel_candidates"]},
            "corpus_records": [{**copy.deepcopy(row), "module_ids": [], "decision_family_ids": row["decision_tree_paths"],
                                 "runtime_disposition": row["disposition"]} for row in rows]}
        return registry, decision_tree

    def make_current(self):
        self.registry, self.map = self.project()
        if self.persistent_map_mutation: self.persistent_map_mutation(self.map)

    def __call__(self, method, url, *, body=None, secret=None, budget, approved_scope=None):
        self.calls.append({"method": method, "url": url, "budget": budget, "remaining": budget.require_remaining(),
                           "body": copy.deepcopy(body)})
        if method == "POST":
            if body["expected_canon_commit"] != self.commit:
                return 409, {"status": "hold"}
            self.make_current()
            if self.uncertain_callback: raise RuntimeError("inert secret must not escape: " + str(secret))
            return 200, {"status": "synchronized", "catalog_digest": self.catalog["catalog_digest"],
                         "canon_commit": self.commit, "record_count": len(self.catalog["records"])}
        if url == sync.CATALOG_URL: return 200, copy.deepcopy(self.catalog)
        if url == sync.MAIN_URL: return 200, {"object": {"sha": self.commit}}
        if url == sync.REGISTRY_URL: return 200, copy.deepcopy(self.registry)
        if url == sync.DECISION_TREE_URL: return 200, copy.deepcopy(self.map)
        if url.startswith("https://raw.githubusercontent.com/"):
            return 200, copy.deepcopy(self.pinned.get(url.split("/")[5], self.catalog))
        if url == "https://zenodo.org/api/records/123": return 200, {"id": 123, "doi": "10.5281/zenodo.123", "submitted": True}
        raise AssertionError("Unapproved inert request destination")


class Fixture:
    def __init__(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.commit = "c" * 40
        rows = []
        for index, (status, integrity, coverage) in enumerate([
            ("verified", "gate-passed", {"status": "HOLD", "canon_eligible": False, "label": "UNCERTIFIED — exact fixture gap"}),
            ("working", "not-canon-admitted", None),
            ("quarantined", "gate-passed", {"status": "PASS", "canon_eligible": True, "label": "Retained predecessor only"}),
            ("verified", "gate-passed", {"status": "PASS", "canon_eligible": True, "label": "Exact hypothetical current coverage"}),
        ]):
            rows.append({"record_id": "run" + str(index), "title": "Conditional fixture " + str(index),
                "path": "public/fixture" + str(index) + ".lean", "doi": "10.5281/zenodo.123", "source_sha256": str(index + 1) * 64,
                "status": status, "integrity": integrity, "metadata": {} if coverage is None else {"verification_coverage": coverage}})
        self.catalog = {"schema": sync.CATALOG_SCHEMA, "repository": sync.CATALOG_REPOSITORY,
            "publication_scope": "public", "human_publish_gate": True, "records": rows}
        self.catalog["catalog_digest"] = sync.digest(self.catalog)
        self.canon = self.root / "verified-canon.json"
        self.canon.write_text(json.dumps({"status": "verified", "repository": sync.REPOSITORY, "branch": "main", "spine_changed": False,
            "commit_sha": self.commit, "catalog_digest": self.catalog["catalog_digest"], "public_catalog_url": sync.CATALOG_URL,
            "bundles": [{"doi": "10.5281/zenodo.123"}]}))
        self.doi = self.root / "PUBLISHED_DOI.txt"; self.doi.write_text("10.5281/zenodo.123\n")
        self.http = PublicService(self.catalog, self.commit)
        self.budget = Budget()
        self.environment = {"CRON_SECRET": "inert-test-secret"}

    def close(self): self.temp.cleanup()

    def synchronize(self, *, apply=True, permit_inert_test=False):
        kwargs = {"root": self.root, "apply": apply, "http": self.http, "budget": self.budget,
                  "environ": self.environment, "approved_scope": {"fixture_only": True}}
        if permit_inert_test:
            with patch.object(sync, "require_mutation_authority"):
                return sync.synchronize(self.canon, [self.doi], **kwargs)
        return sync.synchronize(self.canon, [self.doi], **kwargs)

    def receipts(self): return list((self.root / "reports/approved-release-sync/postpublication-sync").glob("*.json"))
