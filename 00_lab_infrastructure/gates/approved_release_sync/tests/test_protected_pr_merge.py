import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import unittest

import test_trusted_canon_adapter as fixtures

adapter = fixtures.adapter
merge = adapter.protected_merge
sync = adapter.sync
URL = "https://github.com/jdhart81/viridis-canon/pull/123"


class Guard:
    def __init__(self):
        self.events = []
        self.row = {"html_url": URL, "state": "open", "merged": False, "merge_commit_sha": "e" * 40,
                    "base": {"ref": "main", "sha": "c" * 40, "repo": {"full_name": sync.REPOSITORY}},
                    "head": {"sha": "d" * 40, "repo": {"full_name": sync.REPOSITORY}}}
        self.all_checks = [{"name": name, "bucket": "pass", "state": "SUCCESS", "workflow": name, "link": "https://example.invalid/" + name}
                           for name in ("catalog", "ci")]
        self.required_checks = copy.deepcopy(self.all_checks)
        self.fail_normal = False
        self.fail_auto = False
        self.after_normal_failure = lambda: None
        self.api_count = 0
        self.on_api = lambda count: None
        self.protection = {"required_status_checks": {"strict": True, "contexts": ["catalog", "ci"], "checks": []},
                           "enforce_admins": {"enabled": True}}
        self.rules = []
        self.policy_rc = 0
        self.review_decision = "APPROVED"

    def gh(self, *args, **kwargs):
        self.events.append(args)
        if args[0] == "api":
            if args[1].endswith("/protection"):
                return SimpleNamespace(returncode=self.policy_rc, stdout=json.dumps(self.protection), stderr="")
            if any(value.endswith("/rules/branches/main") for value in args[1:]):
                return SimpleNamespace(returncode=self.policy_rc, stdout=json.dumps([self.rules]), stderr="")
            self.api_count += 1; self.on_api(self.api_count)
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.row), stderr="")
        if args[:2] == ("pr", "checks"):
            rows = self.required_checks if "--required" in args else self.all_checks
            return SimpleNamespace(returncode=0, stdout=json.dumps(rows), stderr="")
        if args[:2] == ("pr", "merge"):
            failed = self.fail_auto if "--auto" in args else self.fail_normal
            if failed: self.after_normal_failure()
            else: self.row["merged"] = True
            return SimpleNamespace(returncode=int(failed), stdout="", stderr="fixture-secret never surfaced")
        if args[:2] == ("pr", "view"):
            return SimpleNamespace(returncode=0, stdout=json.dumps({"url": URL, "baseRefName": "main", "headRefOid": self.row["head"]["sha"],
                                                                  "reviewDecision": self.review_decision}), stderr="")
        raise AssertionError("unexpected guarded client call")

    def wait_for_pr_merge(self, url, token):
        self.row["merged"] = True
        return self.row["merge_commit_sha"]

    @property
    def merges(self): return [row for row in self.events if row[:2] == ("pr", "merge")]


class ProtectedMergeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.AdapterTests(); self.fixture.setUp()
        self.f = self.fixture.f

    def tearDown(self): self.fixture.tearDown()

    def package(self): return adapter.prepare_package(**self.fixture.kwargs())

    def bounded(self, guard, *, on_sleep=lambda: None):
        clock = [0]
        def sleep(seconds):
            clock[0] += seconds
            on_sleep()
        return merge.merge_approved_pr(guard, "fixture-secret", self.package(), URL, "d" * 40,
            budget=merge.Budget(clock=lambda: clock[0]),
            timeout_seconds=2, poll_seconds=1, monotonic=lambda: clock[0], sleep=sleep)

    def change_approval(self, change):
        approval = json.loads(self.f.approval.read_text()); change(approval)
        self.f.approval.write_text(json.dumps(approval))
        self.f.value["owner_approval"] = self.f.file_binding(self.f.approval); self.f.save_binding()

    def test_missing_or_denied_exact_merge_capability_holds_before_stage_http_and_credentials(self):
        original = self.f.approval.read_bytes()
        changes = [lambda value: value.pop("protected_pr_merge"),
                   lambda value: value["protected_pr_merge"].update(status="NOT_REVIEWED"),
                   lambda value: value["protected_pr_merge"].update(head_sha="wrong"),
                   lambda value: value["protected_pr_merge"].update(required_check_names=[])]
        for key in ("publication_receipt_sha256", "payload_manifest_sha256", "adapter_source_sha256", "merge_policy_source_sha256"):
            changes.append(lambda value, key=key: value["protected_pr_merge"].update({key: "0" * 64}))
        for change in changes:
            self.f.approval.write_bytes(original)
            self.change_approval(change)
            transaction = fixtures.FakeTransaction()
            with self.assertRaisesRegex(sync.SyncHold, "HOLD_EXACT_PROTECTED_PR_MERGE_APPROVAL_REQUIRED"):
                adapter.ApprovedCanonAdapter(apply=True, transaction=transaction,
                    http=lambda *args: self.fail("HTTP before merge capability"))(**self.fixture.kwargs())
            self.assertEqual(transaction.calls, [])
            self.assertFalse((self.f.root / "reports/approved-canon-packages").exists())

    def test_normal_protected_merge_matches_head_without_admin_approval_or_main_push(self):
        guard = Guard()
        self.assertEqual(self.bounded(guard), "e" * 40)
        self.assertEqual(len(guard.merges), 1)
        self.assertIn("--match-head-commit", guard.merges[0]); self.assertIn("d" * 40, guard.merges[0])
        self.assertFalse(any("--admin" in row or row[:2] == ("pr", "review") or "push" in row for row in guard.events))
        self.assertGreaterEqual(guard.api_count, 3)

    def test_missing_scheduled_verdict_waits_and_never_requests_merge(self):
        policy = json.loads(self.f.approval.read_text())["data_pr_review_policy"]
        self.assertTrue(policy["required"])
        verdict = Path(policy["audit_directory"]) / ("VERDICT_PR-123-" + "d" * 7 + ".json")
        verdict.unlink()
        guard = Guard()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_REVIEWS_PENDING_TIMEOUT"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    def test_scheduled_verdict_is_read_from_file_and_bound_to_exact_head_and_base(self):
        policy = json.loads(self.f.approval.read_text())["data_pr_review_policy"]
        path = Path(policy["audit_directory"]) / ("VERDICT_PR-123-" + "d" * 7 + ".json")
        original = json.loads(path.read_text())
        for key, bad in [("head_sha", "a" * 40), ("base_sha", "a" * 40), ("blocking", ["inert finding"])]:
            path.write_text(json.dumps({**original, key: bad}))
            guard = Guard()
            with self.subTest(key=key), self.assertRaisesRegex(sync.SyncHold, "HOLD_SCHEDULED_EXACT_HEAD_REVIEW"):
                self.bounded(guard)
            self.assertEqual(guard.merges, [])

    def test_review_policy_cannot_disable_existing_scheduled_audit(self):
        self.change_approval(lambda value: value["data_pr_review_policy"].update(required=False))
        guard = Guard()
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_SCHEDULED_REVIEW_REQUIRED_BY_EXISTING_AUTHORITY"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    def test_wrong_repo_base_or_head_never_requests_merge(self):
        for field, value in (("base_repo", "other/repo"), ("head_repo", "other/repo"), ("base_ref", "develop"),
                             ("base_sha", "a" * 40), ("head_sha", "a" * 40)):
            with self.subTest(field=field):
                guard = Guard()
                location, key = {"base_repo": (guard.row["base"]["repo"], "full_name"),
                    "head_repo": (guard.row["head"]["repo"], "full_name"), "base_ref": (guard.row["base"], "ref"),
                    "base_sha": (guard.row["base"], "sha"), "head_sha": (guard.row["head"], "sha")}[field]
                location[key] = value
                with self.assertRaises(sync.SyncHold):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_pending_failed_empty_or_ambiguous_checks_never_request_merge(self):
        for kind in ("pending", "fail", "empty", "duplicate", "missing_required", "extra_required"):
            with self.subTest(kind=kind):
                guard = Guard()
                if kind in {"pending", "fail"}: guard.all_checks[0]["bucket"] = kind
                elif kind == "empty": guard.all_checks = []
                elif kind == "duplicate": guard.all_checks.append(copy.deepcopy(guard.all_checks[0]))
                elif kind == "missing_required": guard.required_checks.pop()
                elif kind == "extra_required": guard.required_checks.append({"name": "other", "bucket": "pass"})
                with self.assertRaises(sync.SyncHold):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_head_change_between_check_readback_and_merge_holds(self):
        guard = Guard()
        def change(count):
            if count == 2: guard.row["head"]["sha"] = "a" * 40
        guard.on_api = change
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_IDENTITY"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    def test_pending_or_unregistered_checks_wait_then_merge_once(self):
        for kind in ("pending", "empty", "cli_no_checks"):
            with self.subTest(kind=kind):
                guard = Guard(); original = copy.deepcopy(guard.all_checks)
                if kind == "pending":
                    for row in guard.all_checks: row["bucket"] = "pending"
                elif kind == "empty": guard.all_checks = []; guard.required_checks = []
                else:
                    normal = guard.gh
                    def missing(*args, **kwargs):
                        if args[:2] == ("pr", "checks"):
                            return SimpleNamespace(returncode=1, stdout="", stderr="no checks reported")
                        return normal(*args, **kwargs)
                    guard.gh = missing
                def ready():
                    guard.all_checks = copy.deepcopy(original); guard.required_checks = copy.deepcopy(original)
                    if kind == "cli_no_checks": guard.gh = normal
                self.assertEqual(self.bounded(guard, on_sleep=ready), "e" * 40)
                self.assertEqual(len(guard.merges), 1)

    def test_pending_checks_are_bounded_and_head_or_approval_drift_holds_while_waiting(self):
        for kind in ("timeout", "head", "approval"):
            with self.subTest(kind=kind):
                self.fixture.seal()
                guard = Guard(); guard.all_checks[0]["bucket"] = "pending"
                def during_wait():
                    if kind == "head": guard.row["head"]["sha"] = "a" * 40
                    elif kind == "approval": self.f.approval.write_text('{"changed":"during CI"}')
                with self.assertRaises(sync.SyncHold) as held:
                    self.bounded(guard, on_sleep=during_wait)
                if kind == "timeout": self.assertEqual(str(held.exception), "HOLD_PROTECTED_PR_CHECKS_PENDING_TIMEOUT")
                self.assertEqual(guard.merges, [])

    def test_normal_failure_retry_rechecks_exact_head_and_complete_checks_without_auto(self):
        guard = Guard(); guard.fail_normal = True
        guard.after_normal_failure = lambda: setattr(guard, "fail_normal", False)
        self.assertEqual(self.bounded(guard), "e" * 40)
        self.assertEqual(len(guard.merges), 2)
        self.assertTrue(all("--auto" not in row for row in guard.merges))
        self.assertTrue(all("--match-head-commit" in row for row in guard.merges))
        self.assertGreaterEqual(sum(row[:2] == ("pr", "checks") for row in guard.events), 6)

    def test_head_or_approval_drift_after_failed_request_prevents_auto_retry(self):
        for kind in ("head", "approval"):
            with self.subTest(kind=kind):
                self.fixture.seal()
                guard = Guard(); guard.fail_normal = True
                def drift():
                    if kind == "head": guard.row["head"]["sha"] = "a" * 40
                    else: self.f.approval.write_text('{"changed":"after approved request"}')
                guard.after_normal_failure = drift
                with self.assertRaises(sync.SyncHold):
                    self.bounded(guard)
                self.assertEqual(len(guard.merges), 1)

    def test_failed_merge_requests_preserve_sanitized_hold(self):
        guard = Guard(); guard.fail_normal = True; guard.fail_auto = True
        with self.assertRaisesRegex(sync.SyncHold, "^HOLD_PROTECTED_PR_MERGE_REQUEST$") as held:
            self.bounded(guard)
        self.assertNotIn("fixture-secret", str(held.exception))

    def test_already_merged_retry_revalidates_exact_head_and_checks_without_new_request(self):
        guard = Guard(); guard.row["merged"] = True
        self.assertEqual(self.bounded(guard), "e" * 40)
        self.assertEqual(guard.merges, [])
        self.assertTrue(any(row[:2] == ("pr", "checks") for row in guard.events))
        guard.all_checks[0]["bucket"] = "fail"
        with self.assertRaises(sync.SyncHold):
            self.bounded(guard)

    def test_missing_or_weakened_strict_main_policy_and_merge_queue_hold(self):
        for kind in ("unreadable", "strict", "admins", "contexts", "queue"):
            with self.subTest(kind=kind):
                guard = Guard()
                if kind == "unreadable": guard.policy_rc = 1
                elif kind == "strict": guard.protection["required_status_checks"]["strict"] = False
                elif kind == "admins": guard.protection["enforce_admins"]["enabled"] = False
                elif kind == "contexts": guard.protection["required_status_checks"]["contexts"] = ["different"]
                else: guard.rules = [{"type": "merge_queue"}]
                with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN_POLICY"):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_existing_required_reviews_wait_for_approval_but_denial_holds(self):
        guard = Guard(); guard.protection["required_pull_request_reviews"] = {"required_approving_review_count": 1}
        guard.review_decision = "REVIEW_REQUIRED"
        self.assertEqual(self.bounded(guard, on_sleep=lambda: setattr(guard, "review_decision", "APPROVED")), "e" * 40)
        self.assertEqual(len(guard.merges), 1)
        guard = Guard(); guard.protection["required_pull_request_reviews"] = {"required_approving_review_count": 1}
        guard.review_decision = "CHANGES_REQUESTED"
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_REVIEW_DECISION"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    def test_empty_cli_review_decision_stays_pending_when_positive_reviews_required(self):
        guard = Guard(); guard.protection["required_pull_request_reviews"] = {"required_approving_review_count": 1}
        guard.review_decision = ""
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_REVIEWS_PENDING_TIMEOUT"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    @unittest.skipUnless(shutil.which("git"), "Git required for disposable local fixture")
    def test_offline_head_preview_is_deterministic_and_does_not_write_source_checkout(self):
        repo = self.f.root / "local-canon-checkout"; repo.mkdir()
        environment = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        def run(argv, env=environment):
            return subprocess.run(argv, env=env, text=True, capture_output=True, check=True).stdout.strip()
        run(["git", "init", "--quiet", str(repo)])
        (repo / "README.md").write_text("local approved base fixture\n")
        run(["git", "-C", str(repo), "add", "README.md"])
        command, commit_env = merge.commit_command(repo, "0" * 64, "2026-10-16")
        run(command, env=commit_env)
        initial = run(["git", "-C", str(repo), "rev-parse", "HEAD"])
        self.f.payload_value["base_commit"] = initial; self.fixture.seal()
        package = self.package()
        first = merge.preview_head(package, repo); second = merge.preview_head(package, repo)
        self.assertEqual(first, second)
        self.assertNotEqual(first["head_sha"], initial)
        self.assertEqual(run(["git", "-C", str(repo), "rev-parse", "HEAD"]), initial)
        self.assertEqual(run(["git", "-C", str(repo), "status", "--porcelain"]), "")
        self.assertFalse(first["approval_constructed"])


if __name__ == "__main__": unittest.main()
