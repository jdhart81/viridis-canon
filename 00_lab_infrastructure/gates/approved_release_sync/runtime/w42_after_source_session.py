#!/usr/bin/env python3
"""Inactive additive caller after the fixed W42 outer guard truly exits.

No source or JSON value can activate this proposal. The shared host interlock
holds all applies until a separately reviewed genuine Core host integration
exists. Tests explicitly replace that interlock to exercise causal recovery.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile

import root_scope
import w42_receipt as receipt
from deadline import Budget

STANDARD = "VRS-W42-AFTER-SOURCE-SESSION-1"


def immutable_json(path, value):
    path = Path(path)
    receipt.need(not any(p.is_symlink() for p in (path, *path.parents)), "HOLD_SOURCE_EXIT_CHECKPOINT_PATH")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = receipt.encoded(value)
    fd, scratch = tempfile.mkstemp(prefix=".w42-exit-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        try: os.link(scratch, path)
        except FileExistsError:
            receipt.need(path.is_file() and path.read_bytes() == raw, "HOLD_SOURCE_EXIT_CHECKPOINT_CONFLICT")
        directory = os.open(path.parent, os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if os.path.exists(scratch): os.unlink(scratch)


def utc_now(): return dt.datetime.now(dt.timezone.utc).isoformat()


def _terminate_owned_live_group(child, budget):
    """Only signal an unreaped process group owned by this invocation."""
    if child.returncode is None:
        try: os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        child.wait(timeout=budget.cleanup_remaining_cap(20))


def _continue(root, terminal_binding, scope_binding, scope, *, budget):
    if not scope.get("canon_package"):
        return {"status": "HOLD_CANON_RELEASE_PACKAGE_REQUIRED", "publisher_invocations": 0,
                "reason": "Root must bind the completed receipt, exact public package and exact-head scheduled review."}
    # Source-owned fixed imports only; never choose an adapter from supplied data.
    import approved_release_continuation as continuation
    import trusted_canon_adapter as adapter
    payload, _ = receipt.read_bound(root, scope.get("canon_payload_manifest"))
    receipt.need(scope["canon_payload_manifest"]["sha256"] == scope["canon_package"]["payload_manifest_sha256"],
                 "HOLD_ROOT_CANON_PAYLOAD_BINDING")
    approval, _ = receipt.read_bound(root, scope_binding)
    implementation, _ = receipt.read_bound(root, scope["sources"]["trusted_canon_adapter.py"])
    # The route binds this immutable scope; the scope cannot also bind the
    # route hash without a self-reference. Build the deterministic acyclic
    # route from its already reviewed exact publication/payload/source pins.
    route = budget.call(adapter.build_route_binding, root=root,
        publication_receipt=receipt.path_at(root, terminal_binding["path"]), owner_approval=approval,
        payload_manifest=payload, implementation_source=implementation,
        adapter_id="w42-uncertified-source-records-v1", stage=True)
    return continuation.continue_release(receipt.path_at(root, terminal_binding["path"]), root=root,
        route_binding=route["path"], expected_binding_sha256=route["sha256"], apply=True,
        canon_adapter=adapter.ApprovedCanonAdapter(apply=True), budget=budget)


def run(root, scope_binding, *, apply=False, budget=None, continue_fn=None, popen=None):
    budget = budget or Budget(); budget.require_remaining()
    root = Path(root).resolve(strict=True)
    scope = root_scope.load(root, scope_binding)
    command = receipt.fixed_command(root, scope)
    summary = {"standard": STANDARD, "publisher_invocations": 0, "zenodo_republished_on_retry": False,
               "certifies": False, "runtime_admission": False, "host_integration": "NOT_INSTALLED"}
    if not apply:
        receipt.source_snapshot(root, scope_binding)
        return {**summary, "status": "INACTIVE_SOURCE_PREPARATION", "external_mutations": 0, "core_writes": 0,
                "reason": "HOLD_QUALIFIED_CORE_HOST_HOOK_NOT_INSTALLED"}
    # Deliberately unconditional in this proposal. No FD, lease or scope flag
    # is treated as the missing genuine whole-session Core host qualification.
    root_scope.require_mutation_authority(scope)
    explicit = scope.get("publisher_exit_checkpoint")
    checkpoint = root / "reports/approved-release-source-exit" / (scope_binding["sha256"] + ".json")
    if explicit is not None:
        checkpoint, _ = receipt.read_bound(root, explicit)
    start_path = checkpoint.with_suffix(".started.json")
    terminal_path = Path(scope["publisher_output"]) / "TERMINAL_RESULT.json"
    if checkpoint.exists():
        proof_binding = receipt.binding(root, checkpoint)
        proof = receipt.object_at(root, proof_binding)
        initial_scope = proof.get("root_scope")
        intake = receipt.consume(root, proof.get("terminal"), proof_binding, initial_scope, budget=budget)
        if explicit is not None:
            root_scope.load(root, scope_binding, require_canon=bool(scope.get("canon_package")))
        else:
            receipt.need(initial_scope == scope_binding, "HOLD_SOURCE_EXIT_SCOPE_MISMATCH")
        reused = True
    else:
        # An old terminal or a started/uncertain invocation never authorizes
        # rerunning the publisher. Only our owned genuine exit is resumable.
        receipt.need(not terminal_path.exists() and not start_path.exists(), "HOLD_PUBLISHER_EXIT_UNPROVEN_NO_REENTRY")
        before = receipt.source_snapshot(root, scope_binding)
        started = utc_now()
        immutable_json(start_path, {"standard": STANDARD, "status": "PUBLISHER_INVOCATION_STARTED_NO_REENTRY",
            "root_scope": scope_binding, "command_sha256": receipt.digest(receipt.encoded(command)),
            "before": before, "started_at_utc": started})
        factory = popen or subprocess.Popen
        child = None
        try:
            # Reserve thirty active seconds for genuine exit/source checkpoint.
            allowance = budget.require_remaining() - 30
            receipt.need(allowance > 0, "HOLD_PUBLICATION_CHECKPOINT_BUDGET")
            child = factory(command, cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)
            receipt.need(type(child.pid) is int and child.pid > 0, "HOLD_PUBLISHER_CHILD_IDENTITY")
            returncode = child.wait(timeout=min(480, allowance))
        except BaseException:
            if child is not None:
                try: _terminate_owned_live_group(child, budget)
                except BaseException: pass
            raise receipt.PublicationHold("HOLD_PUBLISHER_EXIT_UNCERTAIN_NO_REENTRY") from None
        receipt.need(returncode == 0 and child.returncode == 0, "HOLD_PUBLISHER_NONZERO_NO_REENTRY")
        after = receipt.source_snapshot(root, scope_binding)
        receipt.need(after == before, "HOLD_PUBLISHER_SOURCE_DRIFT_NO_REENTRY")
        terminal_binding = receipt.binding(root, terminal_path)
        proof = {"standard": receipt.EXIT_STANDARD, "status": "GUARD_REAPED_EXIT0_SOURCE_UNCHANGED",
            "root_scope": scope_binding, "terminal": terminal_binding, "before": before, "after": after,
            "returncode": returncode, "process_reaped": True, "child_pid": child.pid,
            "command": command, "command_sha256": receipt.digest(receipt.encoded(command)),
            "caller": scope["sources"]["w42_after_source_session.py"], "started_at_utc": started,
            "finished_at_utc": utc_now()}
        # Irreversible publication is already complete: persist causal evidence
        # before metadata/Canon work or a downstream deadline can interrupt it.
        immutable_json(checkpoint, proof)
        proof_binding = receipt.binding(root, checkpoint)
        intake = receipt.consume(root, terminal_binding, proof_binding, scope_binding, budget=budget)
        reused = False
    result = (continue_fn or _continue)(root, intake["publication"], scope_binding, scope, budget=budget)
    return {**summary, "status": result["status"], "publisher_invocations": 0 if reused else 1,
            "publisher_exit_checkpoint": proof_binding, "publisher_exit_checkpoint_reused": reused,
            "legacy_consumer_status": intake["legacy_consumer_status"], "continuation": result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--root-scope", type=Path, required=True)
    parser.add_argument("--expected-root-scope-sha256", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    scope = {"path": str(args.root_scope), "sha256": args.expected_root_scope_sha256}
    try: value = run(args.root, scope, apply=args.apply)
    except Exception as error:
        reason = str(error) if str(error).startswith("HOLD_") else "HOLD_W42_CALLER_INPUT"
        value = {"standard": STANDARD, "status": "HOLD_W42_CONTINUATION", "reason": reason,
                 "publisher_invocations": 0, "certifies": False, "runtime_admission": False}
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value["status"] in {"INACTIVE_SOURCE_PREPARATION", "PRODUCTION_METADATA_PROPAGATION_VERIFIED"} else 2


if __name__ == "__main__": raise SystemExit(main())
