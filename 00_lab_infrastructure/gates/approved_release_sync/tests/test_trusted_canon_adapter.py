from pathlib import Path
import copy
import json
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

CONTINUATION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONTINUATION / "runtime"))
import trusted_canon_adapter as adapter
import test_approved_release_continuation as fixture_module

sync = adapter.sync


def workflows(commit):
    return [{"name": name, "status": "completed", "conclusion": "success", "headSha": commit}
            for name in ("viridis-canon-ci", "research-catalog-and-pages")]


class FakeTransaction:
    def __init__(self): self.calls = []
    def run(self, root, package, *, budget):
        budget.require_remaining()
        self.calls.append(package)
        return {"commit_sha": "e" * 40, "proposed_source_commit_sha": "d" * 40,
                "public_catalog_url": sync.CATALOG_URL, "workflows": workflows("e" * 40),
                "sha256": {path: adapter.sha_bytes(raw) for path, raw in package["frozen"].items()},
                "pull_request_url": "https://github.com/jdhart81/viridis-canon/pull/123"}


class AlreadyLandedTransaction(FakeTransaction):
    def run(self, root, package, *, budget):
        result = super().run(root, package, budget=budget)
        if len(self.calls) > 1:
            # Same approved public files after an unrelated main change. The
            # recovery path observes no new PR, and CI reruns have new IDs.
            result.update(commit_sha="f" * 40, proposed_source_commit_sha="f" * 40,
                          pull_request_url=None, workflows=workflows("f" * 40))
            for row in result["workflows"]:
                row.update(databaseId=789, url="https://github.com/jdhart81/viridis-canon/actions/runs/789")
        return result


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.f = fixture_module.ContinuationTests(); self.f.setUp()
        f = self.f
        f.adapter.write_bytes(Path(adapter.__file__).read_bytes())
        f.value["owner_canon_adapter"]["implementation_source"] = f.file_binding(f.adapter)
        self.catalog = {"schema": sync.CATALOG_SCHEMA, "repository": sync.CATALOG_REPOSITORY,
            "publication_scope": "public", "human_publish_gate": True, "records": [{"record_id": "run-123",
                "path": "series/R123/Proof.lean", "title": "Explicit owner title", "doi": "10.5281/zenodo.123",
                "status": "working", "integrity": "not-certified", "source_sha256": sync.file_hash(f.science)}]}
        self.catalog["catalog_digest"] = sync.digest(self.catalog)
        self.catalog_source = f.root / "approved_catalog.json"; self.catalog_source.write_text(json.dumps(self.catalog))
        self.config_source = f.root / "approved_config.json"; self.config_source.write_text('{"explicit":"owner supplied config"}')
        self.guard = f.root / "_ZENODO_DEPOSITS/weekend_canon_lockstep.py"; self.guard.parent.mkdir(); self.guard.write_text("# pinned guard fixture\n")
        self.coherence = self.guard.parent / "release_coherence.py"; self.coherence.write_text("# pinned dependency fixture\n")
        self.public_record = {"id": 123, "doi": "10.5281/zenodo.123", "metadata": {"title": "Explicit owner paper", "license": "owner supplied unchanged license"},
                              "files": [{"key": "paper.pdf", "size": 123, "checksum": "md5:" + "a" * 32}]}
        snapshot = f.root / "approved-public-record.json"; snapshot.write_text(json.dumps(self.public_record))
        f.payload_value.update({"canon_repository": sync.REPOSITORY, "base_commit": "c" * 40,
            "expected_catalog_digest": self.catalog["catalog_digest"], "release_date": "2026-10-17",
            "protected_guard": f.file_binding(self.guard), "guard_dependencies": [f.file_binding(self.coherence)],
            "released_public_records": [{"doi": "10.5281/zenodo.123", "snapshot": f.file_binding(snapshot)}],
            "git_files": [{"source": f.file_binding(source), "target_path": target} for source, target in
                ((f.science, "series/R123/Proof.lean"), (self.catalog_source, "docs/data/catalog.json"), (self.config_source, "catalog/config.json"))]})
        f.payload_value["publication_mappings"][0].update({"title": "Explicit owner paper", "abbreviation": "R123"})
        self.seal()

    def tearDown(self): self.f.tearDown()

    def seal(self):
        f = self.f
        f.payload.write_text(json.dumps(f.payload_value))
        f.value["canon_payload_manifest"] = f.file_binding(f.payload)
        f.value["owner_canon_adapter"]["reviewed_payload_sha256"] = sync.file_hash(f.payload)
        audit = f.root / "inert-audit-fixtures"; audit.mkdir(exist_ok=True)
        (audit / ("VERDICT_PR-123-" + "d" * 7 + ".json")).write_text(json.dumps({
            "schema": "VRS-INDEPENDENT-REVIEW-VERDICT-1", "repository": sync.REPOSITORY, "pr": 123,
            "head_sha": "d" * 40, "base_sha": f.payload_value.get("base_commit", "c" * 40),
            "reviewer": "Claude (Anthropic) scheduled auditor run — INERT TEST FIXTURE",
            "blocking": [], "verdict": "PASS", "reviewed_at_utc": "2026-10-17T00:00:00Z"}))
        f.approval.write_text(json.dumps({"standard": "VRS-APPROVED-RELEASE-SYNC-ROOT-SCOPE-1",
            "status": "ROOT_REVIEWED", "canonical_root": str(f.root),
            "data_pr_review_policy": {"required": True, "audit_directory": str(audit)},
            "canon_package": {"publication_receipt_sha256": sync.file_hash(f.publication),
                "payload_manifest_sha256": sync.file_hash(f.payload), "adapter_source_sha256": sync.file_hash(f.adapter)},
            "protected_pr_merge": {"standard": "VRS-ROOT-PROTECTED-PR-MERGE-SCOPE-1", "status": "ROOT_REVIEWED",
                "scope": "PROTECTED_PR_MERGE", "repository": sync.REPOSITORY, "base_branch": "main", "head_sha": "d" * 40,
                "publication_receipt_sha256": sync.file_hash(f.publication), "payload_manifest_sha256": sync.file_hash(f.payload),
                "adapter_source_sha256": sync.file_hash(f.adapter),
                "merge_policy_source_sha256": sync.file_hash(Path(adapter.protected_merge.__file__)),
                "required_check_names": ["catalog", "ci"]}}))
        f.value["owner_approval"] = f.file_binding(f.approval)
        f.save_binding()

    def kwargs(self):
        f = self.f
        return dict(root=f.root, publication_receipt=f.publication, route_binding=f.binding, expected_binding_sha256=f.binding_sha)

    def http(self, method, url, *, budget):
        budget.require_remaining()
        self.assertEqual(method, "GET"); self.assertEqual(url, "https://zenodo.org/api/records/123")
        return 200, copy.deepcopy(self.public_record)

    def test_generator_is_deterministic_and_dry_run_writes_nothing(self):
        first = adapter.prepare_package(**self.kwargs())
        second = adapter.prepare_package(**self.kwargs())
        self.assertEqual(first["plan"], second["plan"])
        self.assertFalse(first["directory"].exists())
        self.assertEqual(first["frozen"]["docs/data/catalog.json"], self.catalog_source.read_bytes())
        self.assertFalse(first["plan"]["license_or_certification_inferred"])

    def test_staging_preserves_exact_source_and_is_idempotent(self):
        result = adapter.prepare_package(**self.kwargs(), stage=True)
        manifest = result["directory"] / "PACKAGE_MANIFEST.json"
        mtime = manifest.stat().st_mtime_ns
        adapter.prepare_package(**self.kwargs(), stage=True)
        self.assertEqual(manifest.stat().st_mtime_ns, mtime)
        for name, raw in result["frozen"].items():
            self.assertEqual((result["directory"] / "payload" / name).read_bytes(), raw)

    def test_missing_explicit_owner_fields_are_named(self):
        self.f.payload_value.pop("base_commit"); self.seal()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_ADAPTER_FIELDS_REQUIRED:base_commit"):
            adapter.prepare_package(**self.kwargs())

    def test_workflow_or_runtime_target_is_refused(self):
        for target in (".github/workflows/publish.yml", "os/admissions.json", "series/R123/runner.py"):
            with self.subTest(target=target):
                self.f.payload_value["git_files"][0]["target_path"] = target; self.seal()
                with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_TARGET_SCOPE"):
                    adapter.prepare_package(**self.kwargs())

    def test_stale_source_or_wrong_catalog_mapping_fails_before_transaction(self):
        self.f.science.write_text("-- changed\n")
        transaction = FakeTransaction()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CONTINUATION_FILE_DRIFT"):
            adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)(**self.kwargs())
        self.assertEqual(transaction.calls, [])

    def test_default_adapter_does_not_call_git_or_load_credentials(self):
        transaction = FakeTransaction()
        result = adapter.ApprovedCanonAdapter(transaction=transaction)(**self.kwargs())
        self.assertEqual(result["status"], "APPROVED_CANON_PACKAGE_PREPARED")
        self.assertEqual(transaction.calls, [])

    def test_binding_generator_requires_exact_approval_and_is_deterministic(self):
        f = self.f
        f.approval.write_text('{"fixture":"hash binding alone is not approval"}')
        args = dict(root=f.root, publication_receipt=f.publication, owner_approval=f.approval,
                    payload_manifest=f.payload, implementation_source=f.adapter, adapter_id="reviewed-canon-v1")
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_EXPLICIT_ROOT_SCOPE_REQUIRED"):
            adapter.build_route_binding(**args)
        self.seal()
        one = adapter.build_route_binding(**args)
        two = adapter.build_route_binding(**args)
        self.assertEqual(one["sha256"], two["sha256"])
        self.assertFalse(one["path"].exists())
        staged = adapter.build_route_binding(**args, stage=True)
        self.assertEqual(sync.file_hash(staged["path"]), staged["sha256"])

    def test_successor_receipt_generates_binding_and_uses_same_trusted_closure(self):
        f = self.f
        f.publication = f.root / "SUCCESSOR_PUBLICATION_RECEIPT.json"
        f.publication.write_text(json.dumps({"standard": "VRS-ZENODO-SUCCESSOR-PUBLICATION-1",
            "state": "ZENODO_SUCCESSOR_WAVE_PUBLISHED", "results": [{"doi": "10.5281/zenodo.123", "record_id": "123"}]}))
        f.value.update(publisher_format="successor-wave", publication_receipt=f.file_binding(f.publication))
        self.seal()
        binding = adapter.build_route_binding(root=f.root, publication_receipt=f.publication, owner_approval=f.approval,
            payload_manifest=f.payload, implementation_source=f.adapter,
            adapter_id=f.value["owner_canon_adapter"]["adapter_id"], stage=True)
        self.assertEqual(binding["binding"]["publisher_format"], "successor-wave")
        transaction = FakeTransaction(); dispatches = []
        def dispatcher(*args, **kwargs):
            dispatches.append(kwargs["publication_format"])
            return {"status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED"}
        result = adapter.continuation.continue_release(f.publication, root=f.root, route_binding=binding["path"],
            expected_binding_sha256=binding["sha256"], apply=True, dispatcher=dispatcher,
            canon_adapter=adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http))
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(dispatches, ["successor-wave"])
        self.assertEqual(len(transaction.calls), 1)

    def test_apply_rejects_manual_bindings_with_missing_denied_or_mismatched_approval(self):
        f = self.f
        original = json.loads(f.approval.read_text())
        cases = [({}, "HOLD_EXPLICIT_ROOT_SCOPE_REQUIRED"),
                 ({**original, "status": "NOT_REVIEWED"}, "HOLD_EXPLICIT_ROOT_SCOPE_REQUIRED"),
                 ({**original, "canon_package": {}}, "HOLD_EXACT_ROOT_CANON_PACKAGE_SCOPE_REQUIRED")]
        cases.extend(({**original, "canon_package": {**original["canon_package"], key: "0" * 64}},
                      "HOLD_EXACT_ROOT_CANON_PACKAGE_SCOPE_REQUIRED") for key in
                     ("publication_receipt_sha256", "payload_manifest_sha256", "adapter_source_sha256"))
        for value, reason in cases:
            with self.subTest(approval=value):
                f.approval.write_text(json.dumps(value)); f.value["owner_approval"] = f.file_binding(f.approval); f.save_binding()
                transaction = FakeTransaction()
                with self.assertRaisesRegex(sync.SyncHold, reason):
                    adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=lambda *args: self.fail("public request before approval"))(**self.kwargs())
                self.assertEqual(transaction.calls, [])
                self.assertFalse((f.root / "reports/approved-canon-packages").exists())

    def test_released_public_metadata_drift_blocks_git_transaction(self):
        transaction = FakeTransaction()
        self.public_record["metadata"]["license"] = "changed after explicit approval"
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_RELEASED_PUBLIC_METADATA_DRIFT"):
            adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)(**self.kwargs())
        self.assertEqual(transaction.calls, [])

    def test_callable_adapter_emits_exact_verified_receipt_only_after_all_checks(self):
        transaction = FakeTransaction()
        result = adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)(**self.kwargs())
        self.assertEqual(result["status"], "VERIFIED_CANON_CLOSURE")
        receipt = sync.object_file(self.f.root / result["canon_receipt"]["path"])
        self.assertEqual(receipt["catalog_digest"], self.catalog["catalog_digest"])
        self.assertEqual(receipt["bundles"][0]["doi"], "10.5281/zenodo.123")
        self.assertEqual(receipt["source_commit_sha"], receipt["commit_sha"])
        self.assertEqual(len(transaction.calls), 1)

    def test_direct_adapter_retry_preserves_historical_canon_receipt(self):
        transaction = AlreadyLandedTransaction()
        trusted = adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)
        first = trusted(**self.kwargs())
        path = self.f.root / first["canon_receipt"]["path"]
        original = path.read_bytes()
        second = trusted(**self.kwargs())
        self.assertEqual(first, second)
        self.assertEqual(path.read_bytes(), original)
        receipt = json.loads(original)
        self.assertEqual(receipt["proposed_source_commit_sha"], "d" * 40)
        self.assertEqual(receipt["commit_sha"], "e" * 40)
        self.assertTrue(receipt["pull_request_url"].endswith("/123"))
        self.assertEqual(len(transaction.calls), 2)  # Second call is fresh readback.

    def test_same_day_receipts_are_scoped_to_exact_route_without_overwriting_legacy(self):
        f = self.f
        legacy = f.root / "_ZENODO_DEPOSITS/LOCKSTEP_RECEIPTS/2026-10-17.json"
        legacy.parent.mkdir(parents=True); legacy.write_text('{"legacy":"immutable separate release"}\n')
        original = legacy.read_bytes()
        trusted = adapter.ApprovedCanonAdapter(apply=True, transaction=FakeTransaction(), http=self.http)
        first = trusted(**self.kwargs())
        first_path = f.root / first["canon_receipt"]["path"]
        approval = json.loads(f.approval.read_text()); approval["approval_reference"] = "second exact route fixture"
        f.approval.write_text(json.dumps(approval)); f.value["owner_approval"] = f.file_binding(f.approval); f.save_binding()
        second = trusted(**self.kwargs())
        self.assertNotEqual(first["canon_receipt"]["path"], second["canon_receipt"]["path"])
        self.assertTrue(first_path.is_file())
        self.assertEqual(legacy.read_bytes(), original)

    def test_interruption_before_outer_checkpoint_reuses_exact_adapter_receipt(self):
        f = self.f; transaction = AlreadyLandedTransaction()
        trusted = adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)
        dispatches = []
        def dispatcher(*args, **kwargs):
            dispatches.append(1)
            return {"status": "PRODUCTION_METADATA_PROPAGATION_VERIFIED"}
        original_checkpoint = adapter.continuation.checkpoint_once
        def interrupted(path, value):
            if "approved-canon-continuation" in path.parts:
                raise OSError("fixture interruption before outer checkpoint")
            return original_checkpoint(path, value)
        args = dict(root=f.root, route_binding=f.binding, expected_binding_sha256=f.binding_sha,
                    apply=True, canon_adapter=trusted, dispatcher=dispatcher)
        with patch.object(adapter.continuation, "checkpoint_once", side_effect=interrupted):
            with self.assertRaisesRegex(OSError, "fixture interruption"):
                adapter.continuation.continue_release(f.publication, **args)
        path = f.root / "_ZENODO_DEPOSITS/LOCKSTEP_RECEIPTS" / ("2026-10-17--" + f.binding_sha + ".json")
        original = path.read_bytes()
        self.assertEqual(dispatches, [])
        result = adapter.continuation.continue_release(f.publication, **args)
        self.assertEqual(result["status"], "PRODUCTION_METADATA_PROPAGATION_VERIFIED")
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(len(transaction.calls), 2)
        adapter.continuation.continue_release(f.publication, **args)
        self.assertEqual(len(transaction.calls), 2)  # Outer checkpoint now skips adapter.

    def test_receipt_recovery_rejects_identity_drift_and_failed_fresh_readback(self):
        transaction = AlreadyLandedTransaction()
        trusted = adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)
        result = trusted(**self.kwargs())
        path = self.f.root / result["canon_receipt"]["path"]
        receipt = json.loads(path.read_text()); receipt["approved_payload_sha256"] = "0" * 64
        path.write_text(json.dumps(receipt)); original = path.read_bytes()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_RECEIPT_COLLISION"):
            trusted(**self.kwargs())
        self.assertEqual(path.read_bytes(), original)
        transaction.run = lambda *args, budget: {"commit_sha": "f" * 40, "public_catalog_url": sync.CATALOG_URL,
                                         "workflows": workflows("f" * 40), "sha256": {}}
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_SOURCE_HASH_RECEIPT"):
            trusted(**self.kwargs())
        self.assertEqual(path.read_bytes(), original)

    def test_failed_workflow_or_false_source_receipt_cannot_become_verified(self):
        transaction = FakeTransaction()
        original = transaction.run
        def failed(root, package, *, budget):
            result = original(root, package, budget=budget); result["workflows"][0]["conclusion"] = "failure"; return result
        transaction.run = failed
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_CANON_REQUIRED_WORKFLOWS"):
            adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)(**self.kwargs())
        self.assertFalse((self.f.root / "_ZENODO_DEPOSITS/LOCKSTEP_RECEIPTS").exists())

    def test_full_continuation_calls_trusted_adapter_once_through_metadata_retry(self):
        f = self.f; transaction = FakeTransaction()
        trusted = adapter.ApprovedCanonAdapter(apply=True, transaction=transaction, http=self.http)
        attempts = []
        def dispatcher(*args, **kwargs):
            attempts.append(1)
            return {"status": "CANON_PUBLISHED_APP_METADATA_PENDING" if len(attempts) == 1 else "PRODUCTION_METADATA_PROPAGATION_VERIFIED"}
        for expected in ("CANON_PUBLISHED_APP_METADATA_PENDING", "PRODUCTION_METADATA_PROPAGATION_VERIFIED"):
            result = adapter.continuation.continue_release(f.publication, root=f.root, route_binding=f.binding,
                expected_binding_sha256=f.binding_sha, apply=True, canon_adapter=trusted, dispatcher=dispatcher)
            self.assertEqual(result["status"], expected)
        self.assertEqual(len(transaction.calls), 1)

    def test_protected_transaction_uses_branch_and_exact_head_protected_merge_without_main_push(self):
        package = adapter.prepare_package(**self.kwargs())
        events = []; state = {"commit": "c" * 40}
        def completed(output="", code=0): return SimpleNamespace(stdout=output, stderr="", returncode=code)
        class Guard:
            TOKEN_REPO_URL = "https://example.invalid/{token}/canon.git"
            def read_github_token(self): events.append("existing credential loader"); return "fixture-token"
            def run(self, argv, **kwargs):
                if "commit" in argv:
                    state["commit"] = "d" * 40
                    return completed()
                repo = Path(argv[-1]); repo.mkdir(); (repo / ".git").mkdir()
                for target in ("docs/data/catalog.json", "catalog/config.json"):
                    path = repo / target; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(package["frozen"][target])
                return completed()
            def git(self, repo, *args, **kwargs):
                events.append(tuple(args))
                if args[:2] == ("rev-parse", "HEAD"): return completed(state["commit"])
                if args[0] == "ls-remote": return completed(code=2)
                if "commit" in args: state["commit"] = "d" * 40
                return completed()
            def preflight_release(self, repo): events.append("existing check-only preflight")
            def gh(self, *args, **kwargs):
                events.append(tuple(args))
                if args[0] == "api":
                    if args[1].endswith("/protection"):
                        return completed(json.dumps({"required_status_checks": {"strict": True, "contexts": ["catalog", "ci"], "checks": []},
                                                     "enforce_admins": {"enabled": True}}))
                    if any(value.endswith("/rules/branches/main") for value in args[1:]): return completed("[[]]")
                    return completed(json.dumps({"html_url": "https://github.com/jdhart81/viridis-canon/pull/123", "state": "open",
                        "merged": state.get("merged", False), "merge_commit_sha": "e" * 40,
                        "base": {"ref": "main", "sha": "c" * 40, "repo": {"full_name": sync.REPOSITORY}},
                        "head": {"sha": "d" * 40, "repo": {"full_name": sync.REPOSITORY}}}))
                if args[:2] == ("pr", "checks"):
                    return completed(json.dumps([{"name": name, "bucket": "pass", "state": "SUCCESS", "workflow": name,
                                                  "link": "https://example.invalid/inert-check/" + name}
                                                 for name in ("catalog", "ci")]))
                if args[:2] == ("pr", "merge"):
                    state["merged"] = True
                return completed(code=1) if args[:2] == ("pr", "view") else completed("https://github.com/jdhart81/viridis-canon/pull/123")
            def wait_for_pr_merge(self, url, token):
                events.append("existing protected merge readback"); state["merged"] = True; return "e" * 40
            def wait_for_main_workflows(self, commit, token): return workflows(commit)
            def verify_public(self, branch, commit, hashes): events.append("fresh public byte readback"); return hashes
            def verify_pages(self, digest, bundles):
                for bundle in bundles:
                    self_outer.assertEqual(len(bundle.payload), len(bundle.payload_targets))
                events.append("Pages and DOI readback"); return sync.CATALOG_URL
        self_outer = self
        # Choreography assertions observe one inert in-memory Guard. The real
        # fork/process-group boundary has dedicated timeout/quiescence tests.
        with patch.object(adapter, "load_existing_guard", return_value=Guard()), \
             patch.object(adapter, "BoundedGuard", side_effect=lambda guard, budget: guard):
            result = adapter.ProtectedCanonTransaction().run(self.f.root, package, budget=adapter.Budget())
        self.assertEqual(result["commit_sha"], "e" * 40)
        pushes = [event for event in events if isinstance(event, tuple) and event and event[0] == "push"]
        self.assertEqual(len(pushes), 1)
        self.assertTrue(pushes[0][-1].startswith("HEAD:refs/heads/canon/approved-"))
        self.assertFalse(any("HEAD:main" in str(event) for event in events))
        merges = [event for event in events if isinstance(event, tuple) and event[:2] == ("pr", "merge")]
        self.assertEqual(len(merges), 1)
        self.assertIn("--match-head-commit", merges[0]); self.assertIn("d" * 40, merges[0])
        self.assertNotIn("--admin", merges[0])
        self.assertFalse(any(isinstance(event, tuple) and event[:2] == ("pr", "review") for event in events))
        self.assertIn("fresh public byte readback", events)
        self.assertIn("Pages and DOI readback", events)

    def test_existing_science_and_doi_history_cannot_be_overwritten(self):
        package = adapter.prepare_package(**self.kwargs())
        repo = self.f.root / "repo-fixture"
        for target, raw in package["frozen"].items():
            path = repo / target; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        adapter.preserve_public_history(repo, package)
        source = repo / "series/R123/Proof.lean"; source.write_text("-- older immutable published bytes\n")
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_EXISTING_SCIENCE_BYTES_IMMUTABLE"):
            adapter.preserve_public_history(repo, package)
        source.write_bytes(package["frozen"]["series/R123/Proof.lean"])
        config = repo / "catalog/config.json"
        config.write_text(json.dumps({"explicit": "owner supplied config", "doi_by_path": {"series/Old.lean": "10.5281/zenodo.122"}}))
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_EXISTING_DOI_MAPPING_CHANGE"):
            adapter.preserve_public_history(repo, package)

    def curation_history_fixture(self):
        package = adapter.prepare_package(**self.kwargs())
        repo = self.f.root / "curation-history-fixture"
        old_path = "series/R122/Proof.lean"; new_path = "series/R123/Proof.lean"
        retained = {"record_id": "run-122", "title": "Retained conditional source", "path": old_path,
            "doi": "10.5281/zenodo.122", "source_sha256": "a" * 64,
            "status": "working", "integrity": "not-canon-admitted"}
        old_catalog = copy.deepcopy(self.catalog); old_catalog["records"] = [retained]
        old_catalog.pop("catalog_digest"); old_catalog["catalog_digest"] = sync.digest(old_catalog)
        new_catalog = copy.deepcopy(self.catalog); new_catalog["records"].insert(0, retained)
        new_catalog.pop("catalog_digest"); new_catalog["catalog_digest"] = sync.digest(new_catalog)
        old_config = {"explicit": "unchanged policy", "doi_by_path": {old_path: "10.5281/zenodo.122"},
                      "curation": {old_path: {"status": "working", "label": "retained scope"}}}
        new_config = copy.deepcopy(old_config)
        new_config["doi_by_path"][new_path] = "10.5281/zenodo.123"
        new_config["curation"][new_path] = {"status": "working", "label": "UNCERTIFIED conditional artifact"}
        for target, value in [("docs/data/catalog.json", old_catalog), ("catalog/config.json", old_config)]:
            path = repo / target; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value))
        package["frozen"]["docs/data/catalog.json"] = json.dumps(new_catalog).encode()
        package["frozen"]["catalog/config.json"] = json.dumps(new_config).encode()
        return repo, package, new_catalog, new_config

    def test_explicit_new_source_curation_append_preserves_history_and_policy(self):
        repo, package, catalog, config = self.curation_history_fixture()
        adapter.preserve_public_history(repo, package)
        self.assertEqual(config["curation"]["series/R122/Proof.lean"]["label"], "retained scope")
        self.assertEqual(catalog["records"][-1]["status"], "working")

    def test_existing_curation_cannot_be_rewritten(self):
        repo, package, _, config = self.curation_history_fixture()
        config["curation"]["series/R122/Proof.lean"]["label"] = "rewritten old claim"
        package["frozen"]["catalog/config.json"] = json.dumps(config).encode()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_EXISTING_CANON_CURATION_CHANGE"):
            adapter.preserve_public_history(repo, package)

    def test_new_curation_must_name_new_frozen_source_path(self):
        repo, package, _, config = self.curation_history_fixture()
        config["curation"]["series/Foreign/Proof.lean"] = {"status": "working"}
        package["frozen"]["catalog/config.json"] = json.dumps(config).encode()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_NEW_CANON_CURATION_SCOPE"):
            adapter.preserve_public_history(repo, package)

    def test_new_source_cannot_gain_verified_or_spine_admission(self):
        repo, package, catalog, _ = self.curation_history_fixture()
        original = copy.deepcopy(catalog["records"][-1])
        for change in [{"status": "verified"}, {"integrity": "gate-passed"}, {"tier": "spine"},
                       {"tags": ["verified"]}, {"metadata": {"verification_coverage": {"canon_eligible": True}}}]:
            catalog["records"][-1] = {**original, **change}
            catalog.pop("catalog_digest"); catalog["catalog_digest"] = sync.digest(catalog)
            package["frozen"]["docs/data/catalog.json"] = json.dumps(catalog).encode()
            with self.subTest(change=change), self.assertRaisesRegex(sync.SyncHold, "HOLD_NEW_SOURCE_CANNOT_GAIN_SCIENTIFIC_ADMISSION"):
                adapter.preserve_public_history(repo, package)


if __name__ == "__main__": unittest.main()
