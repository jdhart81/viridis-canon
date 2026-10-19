"""Real additive default wiring, inert child/Git/public transports only.

This is source behavior under an explicitly mocked inactive host gate. It is not
production qualification, a live publisher, scheduled review or installed hook.
"""
import copy
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock
from w42_fixture import W42Fixture
from common_sync_fixtures import PublicService
import root_scope
import w42_receipt as receipt
import w42_after_source_session as caller
import trusted_canon_adapter as adapter
import approved_release_continuation as continuation
import verified_publication_dispatch as dispatch
import descriptive_os
from deadline import Budget

sync = adapter.sync


class DefaultChainTests(unittest.TestCase):
    def setUp(self):
        self.f = W42Fixture(); self.addCleanup(self.f.close)
        self.budget = Budget()
        fixture = self.f
        class FixedGuardChild:
            pid = 345; returncode = None
            def wait(self, timeout):
                fixture.terminal(); self.returncode = 0; return 0
        self.child = mock.Mock(return_value=FixedGuardChild())
        with mock.patch.object(root_scope, "require_mutation_authority"):
            first = caller.run(fixture.root, fixture.scope_binding, apply=True, budget=self.budget, popen=self.child)
        self.assertEqual(first["status"], "HOLD_CANON_RELEASE_PACKAGE_REQUIRED")
        self.f.proof_path = self.f.root / first["publisher_exit_checkpoint"]["path"]
        self.f.proof_value = self.f.read(self.f.proof_path)
        self.exit_bytes = self.f.proof_path.read_bytes()
        self.payload = self.f.package()
        self.public_record = {"id": 123, "doi": "10.5281/zenodo.123", "submitted": True,
            "metadata": {"title": "Explicit W42 parent title", "license": "existing unchanged rights"},
            "files": [{"key": "paper.pdf", "size": 32, "checksum": "md5:" + "a" * 32}]}
        snapshot = self.f.obj("released-public-record.json", self.public_record)
        coherence = self.f.put("_ZENODO_DEPOSITS/release_coherence.py", b"# inert explicitly bound dependency\n")
        self.rows = []
        intake = self.f.consume(); actual = {row["run_id"]: row for row in intake["children"]}
        for child in self.f.payload_value["publication_mappings"][0]["children"]:
            current = actual[child["run_id"]]
            truth = {key: current[key] for key in ("status", "certifies", "certificate_valid", "certificate", "certificate_sha256", "artifact_label")}
            self.rows.append({"record_id": child["canon_record_id"], "title": "Explicit source " + child["run_id"],
                "path": child["statement_certificate_evidence"]["candidate"]["path"], "doi": intake["doi"],
                "source_sha256": child["source_sha256"], "status": "working", "integrity": "not-canon-admitted",
                "tier": "working-corpus", "tags": ["working", "lean4"], "metadata": {"artifact_type": "lean4", "verification_coverage": {
                    "status": "HOLD", "canon_eligible": False, "proposed_canon_eligible": False, "label": receipt.ARTIFACT_LABEL,
                    "current_artifact": truth, "statement_certificate_evidence": child["statement_certificate_evidence"]}}})
        self.catalog_path = self.f.root / "approved-catalog.json"
        self.config_path = self.f.obj("approved-config.json", {"include": ["series/**/*.lean"], "doi_by_path": {row["path"]: intake["doi"] for row in self.rows}})
        self.f.payload_value.update(standard="VRS-OWNER-CANON-RELEASE-PAYLOAD-1", publication_dois=[intake["doi"]],
            source_files=[{"path": child["source_path"], "sha256": child["source_sha256"]}
                          for child in self.f.payload_value["publication_mappings"][0]["children"]],
            canon_repository=sync.REPOSITORY, base_commit="c" * 40, release_date="2026-10-17",
            protected_guard=self.f.bind(self.f.weekend), guard_dependencies=[self.f.bind(coherence)],
            released_public_records=[{"doi": intake["doi"], "snapshot": self.f.bind(snapshot)}])
        self.f.payload_value["publication_mappings"][0].update(title=self.public_record["metadata"]["title"], abbreviation="W42")
        self.transaction_calls, self.callback_calls = [], []
        self.seal()

    def seal(self):
        self.catalog = {"schema": sync.CATALOG_SCHEMA, "repository": sync.CATALOG_REPOSITORY,
            "publication_scope": "public", "human_publish_gate": True, "records": self.rows}
        self.catalog["catalog_digest"] = sync.digest(self.catalog)
        self.catalog_path.write_bytes(receipt.encoded(self.catalog))
        payload = self.f.payload_value
        payload["expected_catalog_digest"] = self.catalog["catalog_digest"]
        payload["git_files"] = [row for row in payload["git_files"] if row["target_path"] not in {"docs/data/catalog.json", "catalog/config.json"}]
        payload["git_files"] += [{"source": self.f.bind(self.catalog_path), "target_path": "docs/data/catalog.json"},
                                 {"source": self.f.bind(self.config_path), "target_path": "catalog/config.json"}]
        self.payload.write_bytes(receipt.encoded(payload))
        latest = self.f.latest_value
        latest["canon_payload_manifest"] = self.f.bind(self.payload)
        latest["canon_package"]["payload_manifest_sha256"] = self.f.bind(self.payload)["sha256"]
        latest["protected_pr_merge"]["payload_manifest_sha256"] = self.f.bind(self.payload)["sha256"]
        self.f.latest.write_bytes(receipt.encoded(latest))
        self.service = PublicService(self.catalog, "e" * 40)

    def http(self, method, url, **kwargs):
        if url == "https://zenodo.org/api/records/123":
            self.service.calls.append({"method": method, "url": url, "budget": kwargs["budget"]})
            self.assertEqual(method, "GET")
            return 200, copy.deepcopy(self.public_record)
        return self.service(method, url, **kwargs)

    def transaction(self, root, package, *, budget):
        self.assertIs(budget, self.budget)
        self.transaction_calls.append(package)
        return {"commit_sha": "e" * 40, "proposed_source_commit_sha": "d" * 40,
            "pull_request_url": "https://github.com/jdhart81/viridis-canon/pull/123", "public_catalog_url": sync.CATALOG_URL,
            "workflows": [{"name": name, "status": "completed", "conclusion": "success", "headSha": "e" * 40}
                          for name in ("viridis-canon-ci", "research-catalog-and-pages")],
            "sha256": {path: adapter.sha_bytes(raw) for path, raw in package["frozen"].items()}}

    def ssh_child(self, command, **kwargs):
        self.assertEqual(command[0], "ssh")
        self.assertEqual(command[-2], "root@192.241.131.123")
        parts = command[-1].split()
        self.assertEqual(parts[:6], ["docker", "exec", "-i", "viridis-app", "node", "-"])
        expected = {"expected_canon_commit": parts[6], "expected_catalog_digest": parts[7], "expected_record_count": int(parts[8])}
        fixture = self
        class SSHChild:
            args = command; returncode = 0
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def communicate(self, input=None, timeout=None):
                fixture.assertEqual(input, sync.SSH_CALLBACK_SCRIPT)
                fixture.callback_calls.append(copy.deepcopy(expected))
                status, result = fixture.service("POST", sync.SYNC_URL, body=expected, budget=fixture.budget)
                fixture.assertEqual(status, 200)
                return json.dumps(result), ""
            def poll(self): return 0
            def wait(self, timeout=None): return 0
        return SSHChild()

    def apply(self):
        # Only immutable host interlock and external transports are replaced.
        # Rootscope/intake/binding/continuation/adapter/dispatch/index all execute.
        with mock.patch.object(root_scope, "require_mutation_authority"), \
             mock.patch.object(adapter.ProtectedCanonTransaction, "run", side_effect=self.transaction), \
             mock.patch.object(sync, "_http_json", side_effect=self.http), \
             mock.patch.object(subprocess, "Popen", side_effect=self.ssh_child):
            return caller.run(self.f.root, self.f.bind(self.f.latest), apply=True, budget=self.budget, popen=self.child)

    def test_default_wiring_reaches_both_public_metadata_views_and_descriptive_index(self):
        result = self.apply()
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(self.child.call_count, 1)
        self.assertEqual(len(self.transaction_calls), 1)
        self.assertEqual(len(self.callback_calls), 1)
        self.assertEqual(self.f.proof_path.read_bytes(), self.exit_bytes)
        self.assertTrue(result["publisher_exit_checkpoint_reused"])
        self.assertEqual(result["publisher_invocations"], 0)
        shared = result["continuation"]["continuation"]
        self.assertEqual(shared["legacy_consumer_status"], "HOLD_UNCERTIFIED_ARTIFACT")
        index = shared["local_os_reconciliation"]
        observed = descriptive_os.read_index(self.f.root, index["reader_proof"]["index"])
        self.assertEqual({r["run_id"] for r in observed["records"]}, {"Run-198", "Run-199"})
        self.assertFalse(observed["runtime_admission"])
        urls = {call["url"] for call in self.service.calls}
        self.assertTrue({sync.REGISTRY_URL, sync.DECISION_TREE_URL}.issubset(urls))
        self.assertTrue(all(call["budget"] is self.budget for call in self.service.calls))
        self.assertFalse(any(call["url"].startswith("https://zenodo.org") and call["method"] != "GET" for call in self.service.calls))

    def test_metadata_failure_then_retry_reuses_publication_and_canon_checkpoint(self):
        self.service.persistent_map_mutation = lambda value: value["corpus_records"][0].update(caveat="wrong map copy")
        first = self.apply()
        self.assertEqual(first["status"], "CANON_PUBLISHED_APP_METADATA_PENDING")
        canon_checkpoints = list((self.f.root / "reports/approved-canon-continuation").glob("*.json"))
        self.assertEqual(len(canon_checkpoints), 1)
        original = canon_checkpoints[0].read_bytes()
        self.service.persistent_map_mutation = None
        second = self.apply()
        self.assertEqual(second["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(self.child.call_count, 1); self.assertEqual(len(self.transaction_calls), 1)
        self.assertEqual(canon_checkpoints[0].read_bytes(), original)
        self.assertEqual(self.f.proof_path.read_bytes(), self.exit_bytes)
        self.assertTrue(second["continuation"]["canon_checkpoint_reused"])

    def test_mixed_mapping_false_verified_and_missing_child_hold_before_transaction(self):
        original = copy.deepcopy(self.f.payload_value); rows = copy.deepcopy(self.rows)
        for mode in ("mixed", "verified", "missing"):
            with self.subTest(mode=mode):
                self.f.payload_value = copy.deepcopy(original); self.rows = copy.deepcopy(rows)
                children = self.f.payload_value["publication_mappings"][0]["children"]
                if mode == "mixed":
                    children[0]["source_path"] = children[1]["source_path"]
                    children[0]["source_sha256"] = children[1]["source_sha256"]
                elif mode == "verified":
                    self.rows[0].update(status="verified", integrity="gate-passed")
                    self.rows[0]["metadata"]["verification_coverage"].update(status="PASS", canon_eligible=True)
                else: children.pop()
                self.seal()
                with self.assertRaisesRegex(Exception, "HOLD_"): self.apply()
                self.assertEqual(self.transaction_calls, [])
                self.assertEqual(self.callback_calls, [])
                self.assertEqual(self.child.call_count, 1)


if __name__ == "__main__": unittest.main()
