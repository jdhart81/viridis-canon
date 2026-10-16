"""Existing nightly checkpoint adapter; inactive until reviewed installation.

The scheduler writes a hash-bound queue after its normal authority, parity,
scope and premise preflights. This adapter changes only reservation/dispatch
ownership. It uses the unchanged private verifier and issuer; it never calls
Lean locally or publishes. No standalone timer or scheduler is provided.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scheduler_liveness import (LivenessHold, RequestIdentity, SchedulerLane,
                               file_digest, immutable_json, digest_json, timed_record, durable_mkdir, fsync_directory)


def bound(value: dict, *, inside: Path | None = None) -> Path:
    if not isinstance(value, dict) or not isinstance(value.get("path"), str):
        raise LivenessHold("HOLD_QUEUE_FILE_BINDING")
    path = Path(value["path"])
    if not path.is_absolute() or file_digest(path) != value.get("sha256"):
        raise LivenessHold("HOLD_QUEUE_FILE_BINDING")
    if inside is not None and not path.resolve().is_relative_to(inside.resolve()):
        raise LivenessHold("HOLD_QUEUE_PATH_SCOPE")
    return path


def identity_for(entry: dict, pipeline: Path) -> tuple[RequestIdentity, dict]:
    paths = {name: bound(entry.get(name), inside=pipeline) for name in ("request", "formal_statement", "candidate")}
    request = json.loads(paths["request"].read_text())
    run = entry.get("run_id")
    if (request.get("source_run") != run or request.get("request_kind", "LEAN_PROOF") != "LEAN_PROOF"
            or request.get("toolchain") != "leanprover/lean4:v4.28.0"
            or request.get("local_lean_execution") is not False):
        raise LivenessHold("HOLD_QUEUE_REQUEST_IDENTITY")
    inputs = request.get("input_sha256", {})
    if any(inputs.get(path.name) != file_digest(path) for name, path in paths.items() if name != "request"):
        raise LivenessHold("HOLD_QUEUE_REQUEST_INPUT")
    identity = RequestIdentity(run, file_digest(paths["request"]), file_digest(paths["candidate"]),
        file_digest(paths["formal_statement"]), hashlib.sha256(request["toolchain"].encode()).hexdigest(),
        hashlib.sha256(str(request.get("mathlib_rev", "")).encode()).hexdigest())
    return identity, paths


def terminal_hold(entry: dict, identity: RequestIdentity, pipeline: Path) -> bool:
    value = entry.get("terminal_hold")
    if value is None:
        return False
    path = bound(value, inside=pipeline)
    # The reviewed PR109 helper is the sole terminal-object classifier.
    # A queue flag cannot establish a different exclusion policy.
    try:
        from verification_coverage_gates.terminal_certification.terminal_hold import terminal_hold as classify
    except ImportError as exc:
        raise LivenessHold("HOLD_QUEUE_TERMINAL_HOLD_BINDING") from exc
    finalized = pipeline / "finalized_runs" / identity.run_id
    package = finalized if finalized.is_dir() else pipeline / "nightly_packages" / identity.run_id
    evidence = classify(package, pipeline / "lean_certificates")
    hold = json.loads(path.read_text())
    bindings = hold.get("bindings", {})
    if (evidence is None or evidence.get("request_sha256") != identity.request_sha256
            or evidence.get("receipt_sha256") != file_digest(path)
            or bindings.get("formal_statement_sha256") != identity.statement_sha256
            or bindings.get("candidate_sha256") != identity.candidate_sha256):
        raise LivenessHold("HOLD_QUEUE_TERMINAL_HOLD_BINDING")
    return True


def _premise_check(pipeline: Path, paths: dict) -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location("_lane_premise_preflight", pipeline / "verification_coverage_gates/premise_declaration.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_envelope(paths["request"], paths["formal_statement"], paths["candidate"], required=True)


def validate_policy(pipeline: Path, *, reconcile_only: bool = False) -> dict:
    policy = json.loads((pipeline / "PARALLEL_CERTIFICATION_POLICY.json").read_text())
    if (policy.get("standard") != "VRS-PARALLEL-CERTIFY-ORDERED-PUBLISH-1"
            or policy.get("active") is not True or policy.get("max_in_flight") != 2
            or policy.get("scheduler_id") != "viridis-nightly-science-generator"):
        if not (reconcile_only and policy.get("active") is False
                and policy.get("standard") == "VRS-PARALLEL-CERTIFY-ORDERED-PUBLISH-1"
                and policy.get("max_in_flight") == 2
                and policy.get("scheduler_id") == "viridis-nightly-science-generator"):
            raise LivenessHold("HOLD_PARALLEL_POLICY_NOT_INSTALLED")
    required = {"nightly_checkpoint.py", "checkpoint_certification_lane.py", "scheduler_liveness.py",
                "job_observation_policy.py", "comparator_cloud_lean_verifier.py",
                "verification_coverage_gates/terminal_certification/terminal_hold.py", "issue_lean_zero_sorry_certificate.py",
                "verification_coverage_gates/premise_declaration.py", "checkpoint_advisory.py",
                "pipeline_advisory/checkpoint_slo_hook.py", "pipeline_advisory/pipeline_slo.py",
                "pipeline_advisory/lean_repair_lint.py"}
    bindings = policy.get("installed_source_sha256", {})
    if set(bindings) != required or any(file_digest(pipeline / name) != bindings[name] for name in required):
        raise LivenessHold("HOLD_PARALLEL_SOURCE_CLOSURE")
    receipt = bound(policy.get("reviewed_installation"), inside=pipeline)
    installation = json.loads(receipt.read_text())
    if (installation.get("merged_by") != "Justin" or installation.get("ci") != "PASS"
            or installation.get("independent_review") != "PASS"
            or installation.get("installed_source_sha256") != bindings):
        raise LivenessHold("HOLD_PARALLEL_INSTALLATION_EVIDENCE")
    return policy


def _certificate_result(identity: RequestIdentity, entry: dict, certificate: dict) -> dict:
    bindings, gates = certificate.get("bindings", {}), certificate.get("gates", {})
    expected = {"request": identity.request_sha256, "formal_statement": identity.statement_sha256,
                "candidate_proof": identity.candidate_sha256}
    if (certificate.get("run_id") != identity.run_id or certificate.get("status") != "LEAN_ZERO_SORRY_CERTIFIED"
            or any(bindings.get(key, {}).get("sha256") != value for key, value in expected.items())
            or any(gates.get(name) is not True for name in (
                "comparator_nanoda_kernel", "comparator_lean_kernel", "zero_sorries_or_admits",
                "nonvacuity_witnesses", "premise_declaration", "allowed_axioms_only",
                "independent_cloud_kernel_verification", "frozen_statement_and_candidate_hash_bound",
                "sealed_statement_signature_alignment")) or gates.get("local_lean_execution") is not False):
        raise LivenessHold("HOLD_ISSUER_RESULT_BINDING")
    cloud_path = Path(entry["receipt_output"])
    if bindings.get("independent_cloud_receipt", {}).get("sha256") != file_digest(cloud_path):
        raise LivenessHold("HOLD_ISSUER_RECEIPT_BINDING")
    return {"identity": identity.__dict__, "nanoda_accepted": True, "default_kernel_accepted": True,
            "zero_holes": True, "premise_gate": True, "nonvacuity_gate": True,
            "certificate_sha256": file_digest(Path(entry["certificate_output"])),
            "proof_sha256": identity.candidate_sha256, "provider_receipt_sha256": file_digest(cloud_path),
            "certificate_path": str(Path(entry["certificate_output"])), "provider_receipt": str(cloud_path)}


def _verify_one(identity: RequestIdentity, entry: dict, paths: dict) -> tuple[dict, dict]:
    # Import the unchanged installed authority only at the actual scheduler call.
    from comparator_cloud_lean_verifier import verify
    from issue_lean_zero_sorry_certificate import issue
    cloud = verify(request_path=paths["request"], formal_statement_path=paths["formal_statement"],
                   candidate_path=paths["candidate"], output_path=Path(entry["receipt_output"]))
    if cloud.get("status") != "VERIFIED":
        return cloud, {}
    certificate = issue(request_path=paths["request"], cloud_receipt_path=Path(entry["receipt_output"]),
                        output_path=Path(entry["certificate_output"]), require_premise_declaration=True)
    return cloud, certificate


def _held_entry(lane: SchedulerLane, identity: RequestIdentity, entry: dict) -> dict:
    return {**entry, "certificate_output": str(lane.root / "verified-results" / identity.key / "certificate.json")}


def _result_payload(row: dict) -> dict:
    return {key: value for key, value in row.items() if key not in {"standard", "recorded_at_utc"}}


def _accept(lane: SchedulerLane, identity: RequestIdentity, entry: dict) -> dict:
    certificate = json.loads(Path(entry["certificate_output"]).read_text())
    value = _certificate_result(identity, entry, certificate)
    # Re-read issuer bytes inside the lane callback, rather than approving the
    # same caller-created dictionary by equality with itself.
    return lane.accept(identity, value, lambda exact, observed:
        exact == identity and _certificate_result(exact, entry,
            json.loads(Path(entry["certificate_output"]).read_text())) == observed)


def _reconcile(lane: SchedulerLane, pipeline: Path) -> dict[str, str]:
    """Reconcile original request outputs; this function never sends a request."""
    errors = {}
    terminal = {RequestIdentity(**row["identity"]).key for row in lane._rows("terminal")}
    accepted = {RequestIdentity(**row["identity"]).key: row for row in lane._rows("results")}
    for reservation in lane._rows("requests"):
        identity = RequestIdentity(**reservation["identity"])
        context_path = lane.root / "contexts" / (identity.key + ".json")
        if context_path.is_symlink() or not context_path.is_file():
            errors[identity.key] = "HOLD_REQUEST_CONTEXT_UNAVAILABLE"
            continue
        context = json.loads(context_path.read_text())
        if context.get("identity") != identity.__dict__:
            raise LivenessHold("HOLD_REQUEST_CONTEXT_BINDING")
        canonical = context["entry"]
        observed_identity, paths = identity_for(canonical, pipeline)
        if observed_identity != identity:
            raise LivenessHold("HOLD_REQUEST_CONTEXT_BINDING")
        entry = _held_entry(lane, identity, canonical)
        if identity.key in accepted:
            current = _certificate_result(identity, entry,
                json.loads(Path(entry["certificate_output"]).read_text()))
            if current != _result_payload(accepted[identity.key]):
                raise LivenessHold("HOLD_RESULT_ARTIFACT_DRIFT")
            continue
        if identity.key in terminal:
            continue
        receipt = Path(entry["receipt_output"])
        if not receipt.exists():
            errors[identity.key] = "HOLD_REQUEST_RECONCILIATION_REQUIRED"
            continue
        try:
            cloud = json.loads(receipt.read_text())
            if cloud.get("status") == "VERIFIED":
                if not Path(entry["certificate_output"]).exists():
                    from issue_lean_zero_sorry_certificate import issue
                    issue(request_path=paths["request"], cloud_receipt_path=receipt,
                          output_path=Path(entry["certificate_output"]), require_premise_declaration=True)
                _accept(lane, identity, entry)
            else:
                goal = cloud.get("provider_response", {}).get("output")
                if not isinstance(goal, str) or not goal.strip():
                    raise LivenessHold("HOLD_REJECTION_EVIDENCE_REQUIRED")
                lane.record_rejection(identity, receipt, file_digest(receipt), goal[:32768])
        except (OSError, ValueError, TypeError, AttributeError, KeyError, LivenessHold):
            errors[identity.key] = "HOLD_PROVIDER_RESULT_RECONCILIATION_REQUIRED"
    return errors


def _promote_prefix(lane: SchedulerLane, prepared: list, result: dict) -> None:
    """Canonical certificates become visible only in the actual ordered prefix.

    This is certificate visibility, not publication admission: every existing
    paper, review, package and publication-authority guard still runs later.
    """
    accepted = {RequestIdentity(**row["identity"]).key for row in lane._rows("results")}
    prefix = lane.publication_prefix([identity for identity, _, _, _ in prepared], accepted)
    result["canonical_certificates"] = []
    for identity, entry, _, _ in prepared:
        if identity.run_id not in prefix:
            continue
        source = Path(_held_entry(lane, identity, entry)["certificate_output"])
        target = Path(entry["certificate_output"])
        if target.exists():
            if file_digest(target) != file_digest(source):
                raise LivenessHold("HOLD_CANONICAL_CERTIFICATE_COLLISION")
        else:
            import os
            durable_mkdir(target.parent)
            # Same-filesystem exclusive link preserves the exact issuer bytes.
            os.link(source, target)
            fsync_directory(target.parent)
        result["canonical_certificates"].append(identity.run_id)


def drain_checkpoint(start_path: Path, queue_path: Path, *, pipeline: Path | None = None,
                     reconcile_only: bool = False) -> dict:
    pipeline = pipeline or Path(__file__).resolve().parent
    from nightly_checkpoint import read_start
    policy = validate_policy(pipeline, reconcile_only=reconcile_only)
    if not reconcile_only:
        from comparator_data_egress_authorization import validate_authorization
        if validate_authorization(pipeline / "COMPARATOR_DATA_EGRESS_AUTHORIZATION.json",
                                  pipeline / "LEAN_VERIFIER_BACKENDS.json").get("status") != "AUTHORIZED":
            raise LivenessHold("HOLD_COMPARATOR_AUTHORIZATION")
    start_path = start_path.resolve()
    if (not start_path.is_relative_to((pipeline / "nightly_checkpoints").resolve())
            or start_path.name != "START.json"
            or (not reconcile_only and (start_path.parent / "FINISH.json").exists())):
        raise LivenessHold("HOLD_CHECKPOINT_IDENTITY")
    start = read_start(start_path)
    queue = json.loads(queue_path.read_text())
    entries = queue.get("entries", [])
    if (queue.get("standard") != "VRS-SCHEDULER-CERTIFICATION-QUEUE-1"
            or queue.get("start_sha256") != file_digest(start_path)
            or not isinstance(entries, list)
            or [row.get("run_id") for row in entries] != start["science"]["certification"]["backlog_runs"]):
        raise LivenessHold("HOLD_QUEUE_BASELINE")
    prepared, outputs, preflight_holds = [], set(), {}
    for entry in entries:
        identity, paths = identity_for(entry, pipeline)
        for key in ("receipt_output", "certificate_output"):
            path = Path(entry[key])
            if (not path.is_absolute() or not path.resolve().is_relative_to(paths["request"].parent.resolve())
                    or path.is_symlink() or str(path) in outputs):
                raise LivenessHold("HOLD_QUEUE_OUTPUT_SCOPE")
            outputs.add(str(path))
        held = terminal_hold(entry, identity, pipeline)
        if not held:
            premise = _premise_check(pipeline, paths)
            if premise.get("status") != "PASS" or premise.get("historical_exemption") is not False:
                preflight_holds[identity.key] = "HOLD_QUEUE_PREMISE_PREFLIGHT"
        # Persist canonical absolute paths so macOS /var aliases do not make
        # hash-bound restart/advisory evidence appear outside the same root.
        entry = {**entry, **{name: {**entry[name], "path": str(path.resolve())} for name, path in paths.items()},
                 **{name: str(Path(entry[name]).resolve()) for name in ("receipt_output", "certificate_output")}}
        prepared.append((identity, entry, paths, held))
    result = {"standard": "VRS-SCHEDULER-CERTIFICATION-CHECKPOINT-1", "start_sha256": file_digest(start_path),
              "queue_sha256": file_digest(queue_path), "accepted": [], "holds": [],
              "reconcile_only": reconcile_only, "publication_performed": False}
    lane = SchedulerLane(pipeline / "parallel_certification")
    with lane.checkpoint():
        # Validate all prior accepted bytes before granting any new transport.
        errors = _reconcile(lane, pipeline)
        errors.update(preflight_holds)
        reserved_keys = {RequestIdentity(**row["identity"]).key for row in lane._rows("requests")}
        reservations = []
        for index, (identity, entry, paths, held) in enumerate(prepared):
            if identity.key in preflight_holds:
                timed_record(lane.root / "preflight-holds" / (identity.key + ".json"), {
                    "standard": "VRS-QUEUE-PREMISE-PREFLIGHT-HOLD-1", "identity": identity.__dict__,
                    "code": preflight_holds[identity.key], "certifies": False})
                continue
            if held:
                hold_path = bound(entry["terminal_hold"], inside=pipeline)
                timed_record(lane.root / "holds" / (identity.key + ".json"), {
                    "standard": "VRS-VALIDATED-TERMINAL-SEALED-HOLD-1", "identity": identity.__dict__,
                    "source_hold": {"path": str(hold_path), "sha256": file_digest(hold_path)}})
                continue
            if not held and identity.key not in reserved_keys and any(Path(entry[key]).exists() for key in ("receipt_output", "certificate_output")):
                raise LivenessHold("HOLD_FRESH_OUTPUT_ALREADY_EXISTS")
            if reconcile_only:
                continue
            context_path = lane.root / "contexts" / (identity.key + ".json")
            if identity.key in reserved_keys:
                # Original outputs remain authoritative after a later queue names
                # fresh paths for an already reserved immutable request.
                context = json.loads(context_path.read_text())
                if context.get("identity") != identity.__dict__:
                    raise LivenessHold("HOLD_REQUEST_CONTEXT_BINDING")
                entry = context["entry"]
                prepared[index] = (identity, entry, paths, held)
            else:
                context = {"identity": identity.__dict__, "entry": {key: entry[key] for key in
                    ("run_id", "request", "formal_statement", "candidate", "receipt_output", "certificate_output")}}
                immutable_json(context_path, context)
            try:
                reservation = lane.reserve(identity)
                if reservation["dispatch"]:
                    reservations.append(reservation)
            except LivenessHold as exc:
                errors[identity.key] = str(exc)
        selected = {row["request"]["identity"]["request_sha256"] for row in reservations}
        work = [(identity, entry, paths) for identity, entry, paths, _ in prepared if identity.request_sha256 in selected]
        # The private verifier/issuer API does not promise thread safety. Calls
        # are serialized; the lane still bounds unresolved provider requests at2.
        for identity, entry, paths in work:
            held_entry = _held_entry(lane, identity, entry)
            durable_mkdir(Path(held_entry["certificate_output"]).parent)
            try:
                cloud, certificate = _verify_one(identity, held_entry, paths)
                if cloud.get("status") == "VERIFIED":
                    _accept(lane, identity, held_entry)
                else:
                    errors[identity.key] = "HOLD_PROVIDER_RESULT_RECONCILIATION_REQUIRED"
            except Exception:
                # Never include provider/SSH/exception/credential prose. Counter
                # assertions in tests live outside this intentionally broad seam.
                errors[identity.key] = "HOLD_PROVIDER_RESULT_RECONCILIATION_REQUIRED"
        errors.update(_reconcile(lane, pipeline))
        accepted_rows = {RequestIdentity(**row["identity"]).key: row for row in lane._rows("results")}
        rejected = {RequestIdentity(**row["identity"]).key for row in lane._rows("terminal")}
        for identity, entry, _, held in prepared:
            if identity.key in accepted_rows:
                result["accepted"].append(identity.run_id)
            else:
                result["holds"].append({"run_id": identity.run_id, "request_key": identity.key,
                    "code": "HOLD_TERMINAL_SEALED_OBJECT" if held else
                            "HOLD_TERMINAL_REJECTED_REQUEST" if identity.key in rejected else
                            errors.get(identity.key, "HOLD_POLICY_INACTIVE_NO_DISPATCH" if reconcile_only else
                                       "HOLD_REQUEST_RECONCILIATION_REQUIRED")})
        if not reconcile_only:
            _promote_prefix(lane, prepared, result)
        else:
            result["canonical_certificates"] = []
    result["status"] = "HOLD" if result["holds"] else "COMPLETED"
    immutable_json(start_path.parent / ("PARALLEL_CERTIFICATION_" + digest_json(result) + ".json"), result)
    return result


def reconcile_checkpoint(start_path: Path, queue_path: Path, *, pipeline: Path | None = None) -> dict:
    """Rollback reconciliation works with active:false and never sends/publishes."""
    return drain_checkpoint(start_path, queue_path, pipeline=pipeline, reconcile_only=True)
