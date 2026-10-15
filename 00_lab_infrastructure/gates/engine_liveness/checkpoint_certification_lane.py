"""Existing nightly checkpoint adapter; inactive until reviewed installation.

The scheduler writes a hash-bound queue after its normal authority, parity,
scope and premise preflights. This adapter changes only reservation/dispatch
ownership. It uses the unchanged private verifier and issuer; it never calls
Lean locally or publishes. No standalone timer or scheduler is provided.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path

from scheduler_liveness import (LivenessHold, RequestIdentity, SchedulerLane,
                               file_digest, immutable_json, digest_json)


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
    hold = json.loads(path.read_text())
    bindings = hold.get("bindings", {})
    if (hold.get("schema_version") != "VRS-CERTIFICATION-PREMISE-HOLD-1"
            or hold.get("run_id") != identity.run_id or hold.get("status") != "HOLD_PREMISE_DECLARATION"
            or hold.get("terminal_for_sealed_object") is not True
            or hold.get("certificate_issued") is not False
            or bindings.get("request_sha256") != identity.request_sha256
            or bindings.get("formal_statement_sha256") != identity.statement_sha256
            or bindings.get("candidate_sha256") != identity.candidate_sha256
            or hold.get("checker_result", {}).get("status") != "HOLD"):
        raise LivenessHold("HOLD_QUEUE_TERMINAL_HOLD_BINDING")
    return True


def validate_policy(pipeline: Path) -> dict:
    policy = json.loads((pipeline / "PARALLEL_CERTIFICATION_POLICY.json").read_text())
    if (policy.get("standard") != "VRS-PARALLEL-CERTIFY-ORDERED-PUBLISH-1"
            or policy.get("active") is not True or policy.get("max_in_flight") != 2
            or policy.get("scheduler_id") != "viridis-nightly-science-generator"):
        raise LivenessHold("HOLD_PARALLEL_POLICY_NOT_INSTALLED")
    required = {"nightly_checkpoint.py", "checkpoint_certification_lane.py", "scheduler_liveness.py",
                "job_observation_policy.py", "comparator_cloud_lean_verifier.py", "issue_lean_zero_sorry_certificate.py",
                "verification_coverage_gates/premise_declaration.py"}
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
            "proof_sha256": identity.candidate_sha256, "provider_receipt_sha256": file_digest(cloud_path)}


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


def drain_checkpoint(start_path: Path, queue_path: Path, *, pipeline: Path | None = None) -> dict:
    pipeline = pipeline or Path(__file__).resolve().parent
    from comparator_data_egress_authorization import validate_authorization
    from nightly_checkpoint import read_start
    validate_policy(pipeline)
    if validate_authorization(pipeline / "COMPARATOR_DATA_EGRESS_AUTHORIZATION.json",
                              pipeline / "LEAN_VERIFIER_BACKENDS.json").get("status") != "AUTHORIZED":
        raise LivenessHold("HOLD_COMPARATOR_AUTHORIZATION")
    start_path = start_path.resolve()
    if (not start_path.is_relative_to((pipeline / "nightly_checkpoints").resolve())
            or start_path.name != "START.json" or (start_path.parent / "FINISH.json").exists()):
        raise LivenessHold("HOLD_CHECKPOINT_IDENTITY")
    start = read_start(start_path)
    queue = json.loads(queue_path.read_text())
    entries = queue.get("entries", [])
    if (queue.get("standard") != "VRS-SCHEDULER-CERTIFICATION-QUEUE-1"
            or queue.get("start_sha256") != file_digest(start_path)
            or not isinstance(entries, list)
            or [row.get("run_id") for row in entries] != start["science"]["certification"]["backlog_runs"]):
        raise LivenessHold("HOLD_QUEUE_BASELINE")
    prepared = []
    outputs = set()
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
            import importlib.util
            spec = importlib.util.spec_from_file_location("_lane_premise_preflight", pipeline / "verification_coverage_gates/premise_declaration.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            premise = module.validate_envelope(paths["request"], paths["formal_statement"], paths["candidate"], required=True)
            if premise.get("status") != "PASS" or premise.get("historical_exemption") is not False:
                raise LivenessHold("HOLD_QUEUE_PREMISE_PREFLIGHT")
        prepared.append((identity, entry, paths, held))
    result = {"standard": "VRS-SCHEDULER-CERTIFICATION-CHECKPOINT-1", "start_sha256": file_digest(start_path),
              "queue_sha256": file_digest(queue_path), "accepted": [], "holds": [], "publication_performed": False}
    lane = SchedulerLane(pipeline / "parallel_certification")
    with lane.checkpoint():
        reserved_keys = {RequestIdentity(**row["identity"]).key for row in lane._rows("requests")}
        for identity, entry, _, held in prepared:
            if not held and identity.key not in reserved_keys and any(Path(entry[key]).exists() for key in ("receipt_output", "certificate_output")):
                raise LivenessHold("HOLD_FRESH_OUTPUT_ALREADY_EXISTS")
        reservations = lane.eligible_dispatches([(identity, held) for identity, _, _, held in prepared])
        selected = {row["request"]["identity"]["request_sha256"] for row in reservations}
        work = [(identity, entry, paths) for identity, entry, paths, _ in prepared if identity.request_sha256 in selected]
        # Reservation exists before either thread can enter the protected transport.
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [(identity, entry, executor.submit(_verify_one, identity, entry, paths)) for identity, entry, paths in work]
            for identity, entry, future in futures:
                try:
                    cloud, certificate = future.result()
                    if cloud.get("status") != "VERIFIED":
                        # Failed or ambiguous transport never releases capacity here.
                        # Authenticated terminal rejection requires explicit reconciliation
                        # through lane.record_rejection with the genuine failing goal.
                        raise LivenessHold("HOLD_COMPARATOR_REJECTED_OR_AMBIGUOUS")
                    value = _certificate_result(identity, entry, certificate)
                    lane.accept(identity, value, lambda exact, observed: exact == identity and observed == value)
                except Exception:
                    # Do not leak provider, SSH, exception or credential prose.
                    pass
        # Resume reads original immutable reservations/results. Never redispatch.
        accepted_rows = {RequestIdentity(**row["identity"]).key: row for row in lane._rows("results")}
        for identity, entry, paths, held in prepared:
            if identity.key in accepted_rows:
                # Revalidate the real output bindings before exposing current credit.
                current_result = _certificate_result(identity, entry, json.loads(Path(entry["certificate_output"]).read_text()))
                if {**current_result, "standard": "VRS-IMMUTABLE-VERIFIED-RESULT-1"} != accepted_rows[identity.key]:
                    raise LivenessHold("HOLD_RESULT_ARTIFACT_DRIFT")
                result["accepted"].append(identity.run_id)
            elif held or any(row["identity"] == identity.__dict__ for row in lane._rows("requests")):
                result["holds"].append({"run_id": identity.run_id,
                    "code": "HOLD_TERMINAL_SEALED_OBJECT" if held else "HOLD_REQUEST_RECONCILIATION_REQUIRED"})
    # The existing FINISH still computes credit from START's original named debt.
    result["status"] = "HOLD" if result["holds"] else "COMPLETED"
    immutable_json(start_path.parent / ("PARALLEL_CERTIFICATION_" + digest_json(result) + ".json"), result)
    return result
