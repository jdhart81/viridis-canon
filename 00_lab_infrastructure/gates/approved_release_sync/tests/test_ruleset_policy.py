"""Exact source-shaped fixtures from existing Canon rules; no remote calls."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import test_protected_pr_merge as fixtures

adapter, merge, sync = fixtures.adapter, fixtures.merge, fixtures.sync
FIXTURES = Path(__file__).parent / "fixtures/canon-policy"
IDENTIFIERS = [19785596, 24087331]
CONTEXTS = sorted(["verify", "verify-catalog", "lean-build-current", "lean-build-p0", "deposit-verify", "gitleaks"])
OPTIONAL_PAIRS = [("deploy-pages", "research-catalog-and-pages"), ("release-bundle", "viridis-os-bundle"), ("dco", "DCO")]


class RulesetGuard(fixtures.Guard):
    def __init__(self):
        super().__init__()
        self.rules = json.loads((FIXTURES / "canon-main-rules.json").read_text())
        self.full = {value: json.loads((FIXTURES / ("canon-ruleset-" + str(value) + ".json")).read_text()) for value in IDENTIFIERS}
        self.metadata = {"full_name": sync.REPOSITORY, "default_branch": "main"}
        self.all_checks = [{"name": name, "state": "SUCCESS", "bucket": "pass", "workflow": name,
                            "link": "https://example.invalid/inert-check/" + name} for name in CONTEXTS]
        self.required_checks = copy.deepcopy(self.all_checks)
        self.pages = None
        self.classic_status = 404
        self.full_rc = 0

    def gh(self, *args, **kwargs):
        endpoint = next((value for value in args[1:] if value.startswith("repos/")), "") if args[0] == "api" else ""
        if endpoint.endswith("/protection"):
            self.events.append(args)
            return SimpleNamespace(returncode=1, stdout=json.dumps({"status": str(self.classic_status)}), stderr="")
        if endpoint.endswith("/rules/branches/main"):
            self.events.append(args)
            assert "--paginate" in args and "--slurp" in args
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.pages if self.pages is not None else [self.rules[:2], self.rules[2:]]), stderr="")
        if "/rulesets/" in endpoint:
            self.events.append(args)
            value = self.full.get(int(endpoint.rsplit("/", 1)[-1]))
            return SimpleNamespace(returncode=self.full_rc, stdout=json.dumps(value), stderr="")
        if endpoint == "repos/" + sync.REPOSITORY:
            self.events.append(args)
            return SimpleNamespace(returncode=0, stdout=json.dumps(self.metadata), stderr="")
        return super().gh(*args, **kwargs)


class RulesetPolicyTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.fixtures.AdapterTests(); self.fixture.setUp()
        self.f = self.fixture.f
        self.approval = json.loads(self.f.approval.read_text())
        self.approval["protected_pr_merge"].update(required_check_names=CONTEXTS, ruleset_ids=IDENTIFIERS)
        self.seal()

    def tearDown(self): self.fixture.tearDown()

    def seal(self):
        self.f.approval.write_text(json.dumps(self.approval))
        self.f.value["owner_approval"] = self.f.file_binding(self.f.approval); self.f.save_binding()

    def package(self): return adapter.prepare_package(**self.fixture.kwargs())

    def bounded(self, guard, on_sleep=lambda: None):
        clock = [0]
        def sleep(seconds): clock[0] += seconds; on_sleep()
        return merge.merge_approved_pr(guard, "fixture-secret", self.package(), fixtures.URL, "d" * 40,
            budget=merge.Budget(clock=lambda: clock[0]),
            timeout_seconds=2, poll_seconds=1, monotonic=lambda: clock[0], sleep=sleep)

    def distinct_check_inventory(self):
        guard = RulesetGuard()
        first = next(row for row in guard.all_checks if row["name"] == "gitleaks")
        # Observed public PR shape: same name AND workflow, distinct run/job
        # links. These are fixture identities; this test makes no HTTP requests.
        first.update(workflow="Secret scan", link="https://github.com/jdhart81/viridis-canon/actions/runs/39060018664/job/117475868515")
        guard.all_checks.append({**first,
            "link": "https://github.com/jdhart81/viridis-canon/actions/runs/39059980127/job/117475755174"})
        guard.required_checks = copy.deepcopy(guard.all_checks)
        self.approval["protected_pr_merge"]["permitted_skipped_checks"] = [
            {"name": name, "workflow": workflow} for name, workflow in OPTIONAL_PAIRS]
        guard.all_checks.extend({"name": name, "workflow": workflow, "link": "https://example.invalid/inert-check/" + name,
                                 "bucket": "skipping", "state": "SKIPPED"} for name, workflow in OPTIONAL_PAIRS)
        self.seal()
        return guard

    def test_six_required_names_distinct_gitleaks_and_exact_three_optional_skips_pass(self):
        guard = self.distinct_check_inventory()
        self.assertEqual({row["name"] for row in guard.required_checks}, set(CONTEXTS))
        self.assertEqual(sum(row["name"] == "gitleaks" for row in guard.required_checks), 2)
        self.assertEqual(self.bounded(guard), "e" * 40)
        self.assertEqual(len(guard.merges), 1)

    def test_either_distinct_gitleaks_failure_or_pending_blocks_merge(self):
        for observation in [0, 1]:
            for state, bucket in [("FAILURE", "fail"), ("PENDING", "pending")]:
                guard = self.distinct_check_inventory()
                for rows in [guard.all_checks, guard.required_checks]:
                    [row for row in rows if row["name"] == "gitleaks"][observation].update(state=state, bucket=bucket)
                with self.subTest(observation=observation, bucket=bucket), self.assertRaises(sync.SyncHold):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_unapproved_or_required_skip_and_required_nonsuccess_are_rejected(self):
        for kind in ["unscoped", "wrong_workflow", "required_optional_skip", "required_skip", "neutral", "cancelled"]:
            guard = self.distinct_check_inventory()
            if kind == "unscoped":
                self.approval["protected_pr_merge"].pop("permitted_skipped_checks"); self.seal()
            elif kind == "wrong_workflow": guard.all_checks[-1]["workflow"] = "unapproved-workflow"
            elif kind == "required_optional_skip": guard.required_checks.append(copy.deepcopy(guard.all_checks[-1]))
            else:
                for rows in [guard.all_checks, guard.required_checks]:
                    next(row for row in rows if row["name"] == "verify").update(
                        state={"required_skip": "SKIPPED", "neutral": "NEUTRAL", "cancelled": "CANCELLED"}[kind],
                        bucket={"required_skip": "skipping", "neutral": "pass", "cancelled": "cancel"}[kind])
            with self.subTest(kind=kind), self.assertRaises(sync.SyncHold): self.bounded(guard)
            self.assertEqual(guard.merges, [])

    def test_identical_full_duplicate_check_observation_is_ambiguous(self):
        guard = self.distinct_check_inventory()
        guard.all_checks.append(copy.deepcopy(guard.all_checks[0]))
        with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_CHECKS_AMBIGUOUS"):
            self.bounded(guard)
        self.assertEqual(guard.merges, [])

    def test_optional_skip_scope_cannot_include_required_or_other_pairs(self):
        for row in [{"name": "verify", "workflow": "viridis-canon-ci"},
                    {"name": "deploy-pages", "workflow": "other"},
                    {"name": "unrecognized", "workflow": "other"}]:
            self.approval["protected_pr_merge"]["permitted_skipped_checks"] = [row]; self.seal()
            guard = RulesetGuard()
            with self.subTest(row=row), self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_PR_CONDITIONAL_SKIP_SCOPE"):
                self.bounded(guard)
            self.assertEqual(guard.merges, [])

    def test_actual_rulesets_prove_strict_no_bypass_and_allow_nonstrict_supplement(self):
        guard = RulesetGuard()
        self.assertFalse(guard.full[24087331]["rules"][0]["parameters"]["strict_required_status_checks_policy"])
        proof = merge.require_repository_policy(guard, "fixture-secret", self.package())
        self.assertEqual(proof["ruleset_ids"], IDENTIFIERS)
        self.assertEqual(proof["required_check_names"], CONTEXTS)
        self.assertTrue(proof["strict_up_to_date"])
        self.assertFalse(proof["actor_can_bypass"])
        self.assertFalse(proof["reviews_required"])
        self.assertTrue(proof["conditional_review"])

    def test_real_shaped_policy_closes_normal_exact_head_merge_without_new_review_gate(self):
        # CLI exports its absent GraphQL review decision as the Go string zero
        # value, not JSON null. Existing Canon rules require zero approvals.
        guard = RulesetGuard(); guard.review_decision = ""
        self.assertEqual(self.bounded(guard), "e" * 40)
        self.assertEqual(len(guard.merges), 1)
        self.assertTrue(all("--auto" not in event and "--admin" not in event for event in guard.events))
        self.assertTrue(all("--match-head-commit" in event for event in guard.merges))

    def test_inactive_bypass_source_identity_scope_or_default_branch_drift_holds(self):
        cases = [lambda guard: guard.full[19785596].update(enforcement="disabled"),
                 lambda guard: guard.full[19785596].update(bypass_actors=[{"actor_type": "RepositoryRole", "actor_id": 5}]),
                 lambda guard: guard.full[19785596].update(current_user_can_bypass="always"),
                 lambda guard: guard.full[19785596].update(source="other/repo"),
                 lambda guard: guard.full[19785596].update(id=999),
                 lambda guard: guard.full[19785596]["conditions"]["ref_name"].update(exclude=["refs/heads/main"]),
                 lambda guard: guard.full[19785596]["conditions"]["ref_name"].update(include=["refs/heads/*"]),
                 lambda guard: guard.metadata.update(default_branch="develop"),
                 lambda guard: guard.full[19785596]["_links"]["self"].update(href="https://example.invalid/forged")]
        for change in cases:
            with self.subTest(change=change):
                guard = RulesetGuard(); change(guard)
                with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN_RULESET"):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_effective_full_rule_parameters_sources_ids_and_pagination_must_match_completely(self):
        cases = [lambda guard: guard.rules[0]["parameters"].update(strict_required_status_checks_policy=True),
                 lambda guard: guard.rules[0].update(ruleset_source="other/repo"),
                 lambda guard: guard.rules[0].update(ruleset_id=999),
                 lambda guard: guard.rules.pop(),
                 lambda guard: guard.rules.append(copy.deepcopy(guard.rules[0])),
                 lambda guard: setattr(guard, "pages", guard.rules),
                 lambda guard: setattr(guard, "pages", []),
                 lambda guard: guard.rules.append({"type": "deletion", "ruleset_source_type": "Repository",
                                                    "ruleset_source": sync.REPOSITORY, "ruleset_id": 999})]
        for change in cases:
            with self.subTest(change=change):
                guard = RulesetGuard(); change(guard)
                with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN"):
                    self.bounded(guard)
                self.assertEqual(guard.merges, [])

    def test_ruleset_ids_are_explicit_approval_fields_not_inferred_from_response(self):
        for value in (None, [19785596], [19785596, 999], [24087331, 19785596]):
            self.approval["protected_pr_merge"]["ruleset_ids"] = value; self.seal()
            with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN_RULESET:approved_ids"):
                merge.require_repository_policy(RulesetGuard(), "fixture-secret", self.package())

    def test_matching_but_weakened_full_and_effective_policy_or_context_union_holds(self):
        for kind in ("strict", "contexts", "pull_request", "queue"):
            guard = RulesetGuard()
            if kind == "strict":
                guard.full[19785596]["rules"][-1]["parameters"]["strict_required_status_checks_policy"] = False
                guard.rules[-1]["parameters"]["strict_required_status_checks_policy"] = False
            elif kind == "contexts":
                guard.full[24087331]["rules"][0]["parameters"]["required_status_checks"][0]["context"] = "other"
                guard.rules[0]["parameters"]["required_status_checks"][0]["context"] = "other"
            elif kind == "pull_request":
                guard.full[19785596]["rules"] = [row for row in guard.full[19785596]["rules"] if row["type"] != "pull_request"]
                guard.rules = [row for row in guard.rules if row["type"] != "pull_request"]
            else: guard.rules.append({"type": "merge_queue"})
            with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN"):
                self.bounded(guard)
            self.assertEqual(guard.merges, [])

    def test_only_explicit_classic_404_falls_back_and_full_read_failure_holds(self):
        for kind in ("auth", "network", "full_missing", "full_malformed"):
            guard = RulesetGuard()
            if kind == "auth": guard.classic_status = 403
            elif kind == "network": guard.classic_status = "unavailable"
            elif kind == "full_missing": guard.full_rc = 1
            else: guard.full[19785596] = None
            with self.assertRaisesRegex(sync.SyncHold, "HOLD_PROTECTED_MAIN"):
                self.bounded(guard)
            self.assertEqual(guard.merges, [])

    def test_conditional_unattributed_review_pending_is_waited_without_adding_approval(self):
        guard = RulesetGuard(); guard.review_decision = "REVIEW_REQUIRED"
        self.assertEqual(self.bounded(guard, lambda: setattr(guard, "review_decision", "APPROVED")), "e" * 40)
        self.assertEqual(len(guard.merges), 1)
        self.assertFalse(any(event[:2] == ("pr", "review") for event in guard.events))


if __name__ == "__main__": unittest.main()
