"""Explicit exact-head protected PR merge capability; default without approval HOLDs.

No API call occurs at import. All remote calls use the existing guarded client.
No direct-main push, administrator bypass, review approval or new grant exists.
"""
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

import approved_release_continuation as continuation
import root_scope
from deadline import Budget

sync = continuation.sync


def require_approval(package, head_sha=None):
    sync.require(sync.file_hash(package["checked"]["approval"]) == package["checked"]["binding"]["owner_approval"]["sha256"],
                 "HOLD_CONTINUATION_FILE_DRIFT")
    scope = root_scope.load(package["checked"]["root"], package["checked"]["approval"], require_canon=True)
    approval = scope.get("protected_pr_merge")
    required = {"standard": "VRS-ROOT-PROTECTED-PR-MERGE-SCOPE-1", "status": "ROOT_REVIEWED",
        "scope": "PROTECTED_PR_MERGE", "repository": sync.REPOSITORY, "base_branch": "main",
        "publication_receipt_sha256": package["checked"]["binding"]["publication_receipt"]["sha256"],
        "payload_manifest_sha256": package["plan"]["payload_sha256"],
        "adapter_source_sha256": package["checked"]["binding"]["owner_canon_adapter"]["implementation_source"]["sha256"],
        "merge_policy_source_sha256": sync.file_hash(Path(__file__))}
    sync.require(isinstance(approval, dict) and all(approval.get(key) == value for key, value in required.items()),
                 "HOLD_EXACT_PROTECTED_PR_MERGE_APPROVAL_REQUIRED")
    names = approval.get("required_check_names")
    sync.require(sync.SHA40.fullmatch(str(approval.get("head_sha")))
                 and isinstance(names, list) and names and all(isinstance(name, str) and name for name in names)
                 and names == sorted(set(names)), "HOLD_EXACT_PROTECTED_PR_MERGE_APPROVAL_REQUIRED")
    sync.require(head_sha is None or approval["head_sha"] == head_sha, "HOLD_APPROVED_PR_HEAD_MISMATCH")
    optional = approval.get("permitted_skipped_checks", [])
    supported = {("deploy-pages", "research-catalog-and-pages"), ("release-bundle", "viridis-os-bundle"), ("dco", "DCO")}
    sync.require(isinstance(optional, list) and all(isinstance(row, dict) and set(row) == {"name", "workflow"}
                 and (row["name"], row["workflow"]) in supported and row["name"] not in names for row in optional)
                 and len({(row["name"], row["workflow"]) for row in optional}) == len(optional),
                 "HOLD_PROTECTED_PR_CONDITIONAL_SKIP_SCOPE")
    return approval


def require_scheduled_review(package, head_sha, pr_url):
    """Consume the existing scheduled auditor's actual exact-head verdict.

    A missing verdict is pending. This module never writes an audit, makes a
    review request, approves a PR or claims fresh human authorization.
    """
    scope = root_scope.load(package["checked"]["root"], package["checked"]["approval"], require_canon=True)
    policy = scope["data_pr_review_policy"]
    sync.require(policy.get("required") is True, "HOLD_SCHEDULED_REVIEW_REQUIRED_BY_EXISTING_AUTHORITY")
    raw_directory = policy.get("audit_directory")
    sync.require(isinstance(raw_directory, str) and Path(raw_directory).is_absolute()
                 and ".." not in Path(raw_directory).parts, "HOLD_SCHEDULED_REVIEW_DIRECTORY")
    directory = Path(raw_directory)
    sync.require(not any(p.is_symlink() for p in (directory, *directory.parents)), "HOLD_SCHEDULED_REVIEW_DIRECTORY")
    if not directory.exists(): return False
    sync.require(directory.is_dir(), "HOLD_SCHEDULED_REVIEW_DIRECTORY")
    number = re.fullmatch(r"https://github\.com/jdhart81/viridis-canon/pull/([1-9][0-9]*)", str(pr_url))
    sync.require(number is not None, "HOLD_SCHEDULED_REVIEW_PR_IDENTITY")
    path = directory / ("VERDICT_PR-" + number.group(1) + "-" + head_sha[:7] + ".json")
    if not path.exists(): return False
    verdict = sync.object_file(sync.regular(path, directory))
    sync.require(verdict.get("schema") == "VRS-INDEPENDENT-REVIEW-VERDICT-1"
                 and verdict.get("repository") == sync.REPOSITORY and verdict.get("pr") == int(number.group(1))
                 and verdict.get("head_sha") == head_sha and verdict.get("base_sha") == package["plan"]["base_commit"]
                 and isinstance(verdict.get("reviewer"), str) and verdict["reviewer"].startswith("Claude (Anthropic)")
                 and "scheduled auditor run" in verdict["reviewer"] and verdict.get("blocking") == []
                 and verdict.get("verdict") in {"PASS", "PASS_WITH_NITS"}, "HOLD_SCHEDULED_EXACT_HEAD_REVIEW")
    try: reviewed = dt.datetime.fromisoformat(verdict["reviewed_at_utc"].replace("Z", "+00:00"))
    except (KeyError, ValueError, TypeError): raise sync.SyncHold("HOLD_SCHEDULED_REVIEW_TIMESTAMP") from None
    sync.require(reviewed.tzinfo is not None, "HOLD_SCHEDULED_REVIEW_TIMESTAMP")
    return True


def commit_command(repo, payload_sha256, release_date):
    sync.require(sync.SHA64.fullmatch(str(payload_sha256)), "HOLD_CANON_COMMIT_PAYLOAD")
    try:
        sync.require(dt.date.fromisoformat(release_date).isoformat() == release_date, "HOLD_CANON_COMMIT_DATE")
    except (ValueError, TypeError):
        raise sync.SyncHold("HOLD_CANON_COMMIT_DATE") from None
    env = dict(os.environ, GIT_AUTHOR_DATE=release_date + "T00:00:00+00:00",
               GIT_COMMITTER_DATE=release_date + "T00:00:00+00:00", GIT_AUTHOR_NAME="Justin D. Hart",
               GIT_COMMITTER_NAME="Justin D. Hart", GIT_AUTHOR_EMAIL="justin@viridisconservation.com",
               GIT_COMMITTER_EMAIL="justin@viridisconservation.com", GIT_TERMINAL_PROMPT="0",
               GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    return (["git", "-C", str(repo), "-c", "core.hooksPath=" + os.devnull,
             "-c", "commit.gpgSign=false", "commit", "--quiet", "--no-gpg-sign", "-m",
             "canon: approved publication " + payload_sha256], env)


def _ruleset_policy(guard, token, approved, effective):
    """Prove active, nonbypassable full rulesets match effective main rules."""
    fields = {"ruleset_id", "ruleset_source_type", "ruleset_source"}
    sync.require(effective and all(fields.issubset(row) and type(row["ruleset_id"]) is int and row["ruleset_id"] > 0
                 and row["ruleset_source_type"] == "Repository" and row["ruleset_source"] == sync.REPOSITORY
                 and set(row).issubset(fields | {"type", "parameters"}) for row in effective),
                 "HOLD_PROTECTED_MAIN_RULESET:effective_source")
    identifiers = approved.get("ruleset_ids")
    sync.require(isinstance(identifiers, list) and identifiers and all(type(value) is int and value > 0 for value in identifiers)
                 and identifiers == sorted(set(identifiers)) and set(identifiers) == {row["ruleset_id"] for row in effective},
                 "HOLD_PROTECTED_MAIN_RULESET:approved_ids")
    contexts, types, strict, reviewed, conditional_review = set(), set(), False, False, False
    default_main = None
    for identifier in identifiers:
        response = guard.gh("api", "repos/" + sync.REPOSITORY + "/rulesets/" + str(identifier), token=token, check=False)
        sync.require(response.returncode == 0, "HOLD_PROTECTED_MAIN_RULESET:full_readback")
        try:
            full = json.loads(response.stdout)
            identity = (type(full.get("id")) is int and full["id"] == identifier and full.get("target") == "branch"
                        and full.get("source_type") == "Repository" and full.get("source") == sync.REPOSITORY
                        and full.get("enforcement") == "active" and full.get("bypass_actors") == []
                        and full.get("current_user_can_bypass") == "never"
                        and full["_links"]["self"]["href"] == "https://api.github.com/repos/" + sync.REPOSITORY + "/rulesets/" + str(identifier))
            condition = full["conditions"]["ref_name"]
            applicable = (set(full["conditions"]) == {"ref_name"} and isinstance(condition, dict)
                          and set(condition) == {"include", "exclude"} and condition["exclude"] == []
                          and isinstance(condition["include"], list) and condition["include"]
                          and all(value in {"~DEFAULT_BRANCH", "refs/heads/main"} for value in condition["include"]))
            rules = full["rules"]
        except (ValueError, TypeError, KeyError, AttributeError):
            raise sync.SyncHold("HOLD_PROTECTED_MAIN_RULESET:full_identity") from None
        sync.require(identity and applicable, "HOLD_PROTECTED_MAIN_RULESET:active_no_bypass_main_identity")
        if "~DEFAULT_BRANCH" in condition["include"]:
            if default_main is None:
                repository = guard.gh("api", "repos/" + sync.REPOSITORY, token=token, check=False)
                sync.require(repository.returncode == 0, "HOLD_PROTECTED_MAIN_RULESET:default_branch_readback")
                try:
                    metadata = json.loads(repository.stdout)
                    default_main = metadata.get("full_name") == sync.REPOSITORY and metadata.get("default_branch") == "main"
                except (ValueError, TypeError, AttributeError):
                    raise sync.SyncHold("HOLD_PROTECTED_MAIN_RULESET:default_branch_readback") from None
            sync.require(default_main, "HOLD_PROTECTED_MAIN_RULESET:default_branch_main_required")
        sync.require(isinstance(rules, list) and rules and all(isinstance(row, dict) and isinstance(row.get("type"), str)
                     and set(row).issubset({"type", "parameters"}) for row in rules), "HOLD_PROTECTED_MAIN_RULESET:rule_shape")
        actual = [{key: value for key, value in row.items() if key not in fields}
                  for row in effective if row["ruleset_id"] == identifier]
        canonical = lambda values: sorted(json.dumps(value, sort_keys=True, separators=(",", ":")) for value in values)
        sync.require(canonical(rules) == canonical(actual), "HOLD_PROTECTED_MAIN_RULESET:effective_full_mismatch")
        for row in rules:
            types.add(row["type"])
            if row["type"] == "required_status_checks":
                parameters = row.get("parameters")
                sync.require(isinstance(parameters, dict) and type(parameters.get("strict_required_status_checks_policy")) is bool
                             and parameters.get("do_not_enforce_on_create") is False,
                             "HOLD_PROTECTED_MAIN_RULESET:status_check_parameters")
                checks = parameters.get("required_status_checks")
                sync.require(isinstance(checks, list) and checks and all(isinstance(check, dict)
                             and isinstance(check.get("context"), str) and check["context"]
                             and ("integration_id" not in check or type(check["integration_id"]) is int and check["integration_id"] > 0)
                             for check in checks), "HOLD_PROTECTED_MAIN_RULESET:required_contexts")
                names = [check["context"] for check in checks]
                sync.require(len(set(names)) == len(names), "HOLD_PROTECTED_MAIN_RULESET:duplicate_contexts")
                contexts.update(names)
                strict = strict or parameters["strict_required_status_checks_policy"]
            if row["type"] == "pull_request":
                parameters = row.get("parameters")
                sync.require(isinstance(parameters, dict) and type(parameters.get("required_approving_review_count")) is int
                             and parameters["required_approving_review_count"] >= 0
                             and isinstance(parameters.get("allowed_merge_methods"), list) and "merge" in parameters["allowed_merge_methods"],
                             "HOLD_PROTECTED_MAIN_RULESET:pull_request_parameters")
                reviewed = reviewed or parameters["required_approving_review_count"] > 0 or any(parameters.get(key) is True for key in
                    ("require_code_owner_review", "require_last_push_approval")) or bool(parameters.get("required_reviewers"))
                conditional_review = conditional_review or parameters.get("require_extra_approval_for_unattributed_changes") is True
    sync.require({"pull_request", "deletion", "non_fast_forward", "required_status_checks"}.issubset(types),
                 "HOLD_PROTECTED_MAIN_RULESET:required_publication_rules")
    sync.require(strict, "HOLD_PROTECTED_MAIN_RULESET:strict_up_to_date")
    sync.require(contexts == set(approved["required_check_names"]), "HOLD_PROTECTED_MAIN_RULESET:required_contexts")
    return {"reviews_required": reviewed, "conditional_review": conditional_review,
            "policy_source": "active_repository_rulesets", "ruleset_ids": identifiers,
            "strict_up_to_date": True, "actor_can_bypass": False, "required_check_names": sorted(contexts)}


def require_repository_policy(guard, token, package):
    """Read strict classic or equivalent ruleset policy; never change rules."""
    approved = require_approval(package)
    result = guard.gh("api", "repos/" + sync.REPOSITORY + "/branches/main/protection", token=token, check=False)
    rules = guard.gh("api", "--paginate", "--slurp", "repos/" + sync.REPOSITORY + "/rules/branches/main", token=token, check=False)
    sync.require(rules.returncode == 0, "HOLD_PROTECTED_MAIN_POLICY:merge_queue_rules_unavailable")
    try:
        pages = json.loads(rules.stdout)
    except (ValueError, TypeError):
        raise sync.SyncHold("HOLD_PROTECTED_MAIN_POLICY:merge_queue_rules_unavailable") from None
    sync.require(isinstance(pages, list) and pages and all(isinstance(page, list) for page in pages),
                 "HOLD_PROTECTED_MAIN_POLICY:effective_rules_pagination")
    rows = [row for page in pages for row in page]
    sync.require(all(isinstance(row, dict) and isinstance(row.get("type"), str) for row in rows),
                 "HOLD_PROTECTED_MAIN_POLICY:merge_queue_rules_unavailable")
    sync.require(len({json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows}) == len(rows),
                 "HOLD_PROTECTED_MAIN_POLICY:effective_rules_duplicate")
    sync.require(not any(row["type"] == "merge_queue" for row in rows), "HOLD_PROTECTED_MAIN_POLICY:merge_queue_not_supported")
    if result.returncode != 0:
        try:
            absent = str(json.loads(result.stdout).get("status")) == "404"
        except (ValueError, TypeError, AttributeError):
            absent = False
        absent = absent or bool(re.search(r"\bHTTP\s+404\b", result.stderr or ""))
        sync.require(absent, "HOLD_PROTECTED_MAIN_POLICY_UNAVAILABLE")
        return _ruleset_policy(guard, token, approved, rows)
    try:
        policy = json.loads(result.stdout)
        checks = policy["required_status_checks"]
        strict = checks["strict"] is True
        enforced = policy["enforce_admins"]["enabled"] is True
        contexts = checks.get("contexts", [])
        app_checks = checks.get("checks", [])
        valid = (isinstance(contexts, list) and all(isinstance(name, str) and name for name in contexts)
                 and isinstance(app_checks, list) and all(isinstance(row, dict) and isinstance(row.get("context"), str)
                                                         and row["context"] for row in app_checks))
    except (ValueError, TypeError, KeyError, AttributeError):
        raise sync.SyncHold("HOLD_PROTECTED_MAIN_POLICY_UNAVAILABLE") from None
    sync.require(strict, "HOLD_PROTECTED_MAIN_POLICY:required_status_checks.strict")
    sync.require(enforced, "HOLD_PROTECTED_MAIN_POLICY:enforce_admins.enabled")
    sync.require(valid and set(contexts) | {row["context"] for row in app_checks} == set(approved["required_check_names"]),
                 "HOLD_PROTECTED_MAIN_POLICY:required_contexts")
    review = policy.get("required_pull_request_reviews")
    sync.require(review is None or (isinstance(review, dict)
                 and type(review.get("required_approving_review_count", 0)) is int
                 and review.get("required_approving_review_count", 0) >= 0),
                 "HOLD_PROTECTED_MAIN_POLICY:required_pull_request_reviews")
    return {"reviews_required": isinstance(review, dict) and
            (review.get("required_approving_review_count", 0) > 0 or review.get("require_code_owner_reviews") is True)}


def preview_head(package, checkout, *, runner=subprocess.run, budget=None):
    budget = budget or Budget()
    budget.require_remaining()
    """Prepare an exact head from an existing local Canon checkout, offline.

    This creates only a disposable local clone. It consumes no credentials and
    does not write the source checkout, publish, push or construct approval.
    The owner can bind the returned SHA before enabling the merge capability.
    """
    checkout = Path(checkout).resolve(strict=True)
    sync.require(checkout.is_dir() and not any(path.is_symlink() for path in (checkout, *checkout.parents)),
                 "HOLD_LOCAL_CANON_CHECKOUT")
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
    def run(argv, *, command_env=None):
        result = runner(argv, env=command_env or env, text=True, capture_output=True, check=False, timeout=budget.remaining_cap(60))
        sync.require(result.returncode == 0, "HOLD_LOCAL_CANON_HEAD_PREPARATION")
        return result.stdout.strip()
    with tempfile.TemporaryDirectory(prefix="approved-canon-head-") as scratch:
        repo = Path(scratch).resolve(strict=True) / "canon"
        run(["git", "-c", "core.hooksPath=" + os.devnull, "clone", "--quiet", "--no-hardlinks", "--no-checkout", "--", str(checkout), str(repo)])
        run(["git", "-C", str(repo), "checkout", "--quiet", "--detach", package["plan"]["base_commit"]])
        for relative, raw in package["frozen"].items():
            target = repo / relative
            sync.require(not Path(relative).is_absolute() and ".." not in Path(relative).parts
                         and not any(path.is_symlink() for path in (target, *target.parents)), "HOLD_CANON_HEAD_SOURCE_SCOPE")
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        run(["git", "-C", str(repo), "add", "--", *sorted(package["frozen"])])
        changed = run(["git", "-C", str(repo), "diff", "--cached", "--name-only"])
        if changed:
            argv, commit_env = commit_command(repo, package["plan"]["payload_sha256"], package["plan"]["release_date"])
            run(argv, command_env=commit_env)
        head = run(["git", "-C", str(repo), "rev-parse", "HEAD"])
        sync.require(sync.SHA40.fullmatch(head), "HOLD_CANON_HEAD_PREPARATION")
        return {"head_sha": head, "base_commit": package["plan"]["base_commit"],
                "payload_manifest_sha256": package["plan"]["payload_sha256"], "public_actions": 0,
                "source_checkout_writes": 0, "approval_constructed": False}


def merge_approved_pr(guard, token, package, pr_url, head_sha, *, budget=None, timeout_seconds=540, poll_seconds=15,
                      monotonic=time.monotonic, sleep=time.sleep):
    """Request normal policy-enforced merge, matching the approved exact head."""
    budget = budget or Budget()
    budget.require_remaining()
    root_scope.require_mutation_authority(package["checked"]["root_scope"])
    approved = require_approval(package, head_sha)
    sync.require(0 < timeout_seconds <= 540 and 0 < poll_seconds <= 60, "HOLD_PROTECTED_PR_WAIT_BOUNDS")
    deadline = monotonic() + budget.remaining_cap(timeout_seconds)
    match = re.fullmatch(r"https://github\.com/jdhart81/viridis-canon/pull/([1-9][0-9]*)", str(pr_url))
    sync.require(match is not None, "HOLD_PROTECTED_PR_IDENTITY")
    policy = {"reviews_required": False, "conditional_review": False}
    def inspect():
        budget.require_remaining()
        result = guard.gh("api", "repos/" + sync.REPOSITORY + "/pulls/" + match.group(1), token=token, check=False)
        sync.require(result.returncode == 0, "HOLD_PROTECTED_PR_READBACK")
        try:
            row = json.loads(result.stdout)
            identity = row["html_url"] == pr_url and row["base"]["repo"]["full_name"] == sync.REPOSITORY
            identity = identity and row["head"]["repo"]["full_name"] == sync.REPOSITORY and row["base"]["ref"] == "main"
            identity = identity and row["head"]["sha"] == head_sha
        except (ValueError, TypeError, KeyError):
            raise sync.SyncHold("HOLD_PROTECTED_PR_IDENTITY") from None
        sync.require(identity, "HOLD_PROTECTED_PR_IDENTITY")
        if row.get("merged") is True:
            sync.require(sync.SHA40.fullmatch(str(row.get("merge_commit_sha"))), "HOLD_PROTECTED_PR_MERGE_READBACK")
            return row["merge_commit_sha"]
        policy.update(require_repository_policy(guard, token, package))
        sync.require(row.get("state") == "open" and row["base"].get("sha") == package["plan"]["base_commit"],
                     "HOLD_PROTECTED_PR_STATE_OR_BASE")
        return None
    def checks():
        budget.require_remaining()
        inventories, pending = [], False
        optional = {(row["name"], row["workflow"]) for row in approved.get("permitted_skipped_checks", [])}
        for required_only in (False, True):
            args = ["pr", "checks", pr_url, "--repo", sync.REPOSITORY, "--json", "name,state,bucket,workflow,link"]
            if required_only: args.append("--required")
            result = guard.gh(*args, token=token, check=False)
            no_checks = (result.returncode == 1 and "no checks reported" in (result.stderr or "").lower()
                         and (result.stdout or "").strip() in {"", "[]"})
            sync.require(result.returncode in {0, 8} or no_checks, "HOLD_PROTECTED_PR_CHECKS")
            try: rows = [] if no_checks else json.loads(result.stdout)
            except (ValueError, TypeError): raise sync.SyncHold("HOLD_PROTECTED_PR_CHECKS") from None
            sync.require(isinstance(rows, list) and all(isinstance(row, dict) and isinstance(row.get("name"), str)
                         and row["name"] and isinstance(row.get("workflow"), str) and isinstance(row.get("link"), str)
                         for row in rows), "HOLD_PROTECTED_PR_CHECKS")
            identities = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows]
            sync.require(len(set(identities)) == len(identities), "HOLD_PROTECTED_PR_CHECKS_AMBIGUOUS")
            for row in rows:
                state = row.get("state"); bucket = row.get("bucket")
                if bucket == "skipping":
                    # These three existing PR-conditional jobs are distinct
                    # from required success, and need explicit Root scoping.
                    sync.require(not required_only and state == "SKIPPED" and (row["name"], row["workflow"]) in optional,
                                 "HOLD_PROTECTED_PR_UNAPPROVED_SKIP")
                else:
                    sync.require(bucket in {"pass", "pending"} and (bucket != "pass" or state == "SUCCESS"),
                                 "HOLD_PROTECTED_PR_CHECKS")
                pending = pending or bucket == "pending"
            pending = pending or not rows or result.returncode == 8
            inventories.append(rows)
        all_rows, required_rows = inventories
        required_names = {row["name"] for row in required_rows}
        sync.require(required_names.issubset(approved["required_check_names"]), "HOLD_PROTECTED_PR_REQUIRED_CHECK_SET")
        if required_names != set(approved["required_check_names"]): pending = True
        # Different workflows may legitimately publish the same context. All
        # instances must pass; every required observation must also be present.
        if any(row not in all_rows for row in required_rows): pending = True
        return not pending
    def reviews():
        budget.require_remaining()
        if not require_scheduled_review(package, head_sha, pr_url): return False
        if not policy["reviews_required"] and not policy["conditional_review"]: return True
        result = guard.gh("pr", "view", pr_url, "--repo", sync.REPOSITORY,
                          "--json", "url,baseRefName,headRefOid,reviewDecision", token=token, check=False)
        sync.require(result.returncode == 0, "HOLD_PROTECTED_PR_REVIEW_READBACK")
        try:
            row = json.loads(result.stdout)
            sync.require(row.get("url") == pr_url and row.get("baseRefName") == "main" and row.get("headRefOid") == head_sha,
                         "HOLD_PROTECTED_PR_REVIEW_IDENTITY")
            decision = row.get("reviewDecision")
        except (ValueError, TypeError, AttributeError):
            raise sync.SyncHold("HOLD_PROTECTED_PR_REVIEW_READBACK") from None
        sync.require(decision in {None, "", "APPROVED", "REVIEW_REQUIRED"}, "HOLD_PROTECTED_PR_REVIEW_DECISION")
        return decision == "APPROVED" or decision in {None, ""} and not policy["reviews_required"]
    def pause(reason):
        remaining = deadline - monotonic()
        sync.require(remaining > 0, reason)
        sleep(min(poll_seconds, remaining, budget.remaining_cap(poll_seconds)))
        budget.require_remaining()
    def wait_checks():
        while True:
            require_approval(package, head_sha)
            inspect()
            ready = checks()
            merged = inspect()
            reviewed = reviews()
            if ready and reviewed: return merged
            pause("HOLD_PROTECTED_PR_CHECKS_PENDING_TIMEOUT" if not ready else "HOLD_PROTECTED_PR_REVIEWS_PENDING_TIMEOUT")
    def wait_merge():
        while True:
            merged = wait_checks()
            if merged: return merged
            pause("HOLD_PROTECTED_PR_MERGE_PENDING_TIMEOUT")
    merged = inspect()
    if merged:
        sync.require(wait_checks() == merged, "HOLD_PROTECTED_PR_MERGE_READBACK")
        return merged
    # Immediate normal merge only. Never leave auto-merge armed for a future,
    # mutable head. A retry refreshes approval, strict policy, head and checks.
    for attempt in range(2):
        merged = wait_checks()
        if merged: return merged
        require_approval(package, head_sha)
        args = ["pr", "merge", pr_url, "--repo", sync.REPOSITORY, "--merge", "--match-head-commit", head_sha, "--delete-branch"]
        result = guard.gh(*args, token=token, check=False)
        if result.returncode == 0:
            return wait_merge()
        merged = inspect()
        if merged:
            sync.require(wait_checks() == merged, "HOLD_PROTECTED_PR_MERGE_READBACK")
            return merged
        if attempt == 0:
            pause("HOLD_PROTECTED_PR_MERGE_PENDING_TIMEOUT")
    raise sync.SyncHold("HOLD_PROTECTED_PR_MERGE_REQUEST")
