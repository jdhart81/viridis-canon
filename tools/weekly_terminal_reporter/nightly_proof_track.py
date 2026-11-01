#!/usr/bin/env python3
"""Report the mandatory formal proof-track state for nightly science runs.

This tool deliberately separates formalization from paper/release eligibility.
A paper-quality HOLD must remain visible, but it cannot make a generated
conjecture disappear from the proof-track report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import types
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from viridis_paths import CONTROL_ROOT

LIVE_ROOT = Path("/Users/justinhart/Desktop/science ")
RUNS_REL = Path("07_nightly_engine/compound research papers")
STATE_REL = Path("07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json")
PROOF_GATE_PASS_STATUSES = {
    "AUDITED_VERIFIED",
}
PROVIDER_WARNING_STATUS = "PROOF_GATE_ACCEPTED_ZERO_SORRY_PROVIDER_WARNING"
CERTIFIED_STATUS = "LEAN_ZERO_SORRY_CERTIFIED"
TERMINAL_HELPER_SHA256 = "c131bc30020abea90b646023e6c9c1b8974ee15e1c9024b11fd6a1a48379a5f3"
TERMINAL_RECEIPTS = {
    "Run-194": (
        "PREMISE_DECLARATION_HOLD_ENGINE_20261015.json",
        "0c03ddd7ff286fb114d19354616b04006529c3bf650bf21936ed6e695737c065",
    ),
}
TERMINAL_UNRESOLVED = "HOLD_TERMINAL_PREMISE_EVIDENCE_UNRESOLVED"
TERMINAL_CONFLICT = "HOLD_TERMINAL_PREMISE_CERTIFICATE_CONFLICT"


class _TerminalEvidenceError(ValueError):
    """An expected trusted object's terminal evidence cannot be resolved."""


def _terminal_bytes(path: Path) -> bytes:
    """Bound a regular-file read; byte rereads below delimit a read window."""
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise _TerminalEvidenceError("symlink in terminal observation ancestry")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(path, flags)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > 4_000_000:
            raise _TerminalEvidenceError("nonregular or oversized terminal observation")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read(4_000_001)
        after = os.fstat(descriptor)
        current = path.lstat()
        if (len(data) > 4_000_000 or
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) !=
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or
                (after.st_dev, after.st_ino) != (current.st_dev, current.st_ino) or
                not stat.S_ISREG(current.st_mode)):
            raise _TerminalEvidenceError("terminal observation changed during read")
        return data
    finally:
        os.close(descriptor)


def _terminal_object(data: bytes) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise _TerminalEvidenceError("duplicate terminal observation key")
            result[key] = value
        return result
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise _TerminalEvidenceError("terminal observation must be a JSON object")
    return value


def _terminal_sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _remember(snapshots: dict[Path, bytes], path: Path) -> bytes:
    data = _terminal_bytes(path)
    if path in snapshots and snapshots[path] != data:
        raise _TerminalEvidenceError("terminal observation drifted between reads")
    snapshots[path] = data
    return data


def _load_terminal_helper(control_root: Path):
    """Load only the unchanged, pinned helper, without an ambient import cache."""
    path = control_root / "RESEARCH_PIPELINE_v2/verification_coverage_gates/terminal_certification/terminal_hold.py"
    data = _terminal_bytes(path)
    if _terminal_sha(data) != TERMINAL_HELPER_SHA256:
        raise _TerminalEvidenceError("terminal helper source pin mismatch")
    module = types.ModuleType("_proof_track_fixed_terminal_hold")
    module.__file__ = str(path)
    exec(compile(data, str(path), "exec"), module.__dict__)
    return module, path, data


def _authenticated_terminal_context(control_root: Path, package: Path) -> dict[str, Any]:
    """Delegate authentication to c131; no reporter-side trust or checker bypass.

    Positive tests may replace this private adapter to test reporting logic.
    Such synthetic cases do not authenticate the fixed allowlisted receipt.
    """
    helper, helper_path, helper_bytes = _load_terminal_helper(control_root)
    certificate_root = control_root / "RESEARCH_PIPELINE_v2/lean_certificates"
    evidence = helper.terminal_hold(package, certificate_root)
    if evidence is None:
        raise _TerminalEvidenceError("unchanged terminal helper did not authenticate expected trusted object")
    if (evidence.get("run_id") != package.name or
            evidence.get("status") != "TERMINAL_PREMISE_HOLD" or
            evidence.get("certifies") is not False or
            evidence.get("clears_certification_debt") is not False or
            evidence.get("publication_admitted") is not False):
        raise _TerminalEvidenceError("unexpected terminal helper result")
    filename, receipt_sha = TERMINAL_RECEIPTS[package.name]
    folder = certificate_root / package.name
    snapshots = {helper_path: helper_bytes}
    # The helper authenticates these sources and documents itself. Retain a
    # second window through our later SOURCE/mirror/certificate joins as well.
    for path, data in helper._checker_sources().items():
        if _remember(snapshots, path) != data:
            raise _TerminalEvidenceError("terminal checker source changed after authentication")
    receipt_path = folder / filename
    receipt = _remember(snapshots, receipt_path)
    if _terminal_sha(receipt) != receipt_sha or evidence.get("receipt_sha256") != receipt_sha:
        raise _TerminalEvidenceError("terminal receipt changed after authentication")
    bindings = _terminal_object(receipt)["bindings"]
    for role, name in helper.BOUND_FILES.items():
        if _terminal_sha(_remember(snapshots, folder / name)) != bindings.get(role):
            raise _TerminalEvidenceError("terminal staged input changed after authentication")
    stage = folder / "ENGINE3_VERIFICATION_REQUEST.json"
    if _terminal_sha(snapshots[stage]) != evidence.get("request_sha256"):
        raise _TerminalEvidenceError("authenticated staged request changed")
    manifest = package / "PAPER_PACKAGE_MANIFEST.json"
    if _terminal_sha(_remember(snapshots, manifest)) != bindings.get("sealed_manifest_sha256"):
        raise _TerminalEvidenceError("selected terminal package changed after authentication")
    return {"evidence": evidence, "snapshots": snapshots, "stage": stage,
            "folder": folder, "manifest": manifest}


def _certificate_terminal_join(
    record: tuple[Path, dict[str, Any]], control_root: Path,
    context: dict[str, Any], snapshots: dict[Path, bytes],
) -> dict[str, Any]:
    path, certificate = record
    raw = _remember(snapshots, path)
    if _terminal_object(raw) != certificate:
        raise _TerminalEvidenceError("current certificate changed after selection")
    bindings = certificate["bindings"]

    def bound(binding):
        if not isinstance(binding, dict) or not isinstance(binding.get("path"), str):
            raise _TerminalEvidenceError("unresolved current certificate binding")
        target = Path(binding["path"])
        choices = [target] if target.is_absolute() else [
            control_root / target, control_root / "RESEARCH_PIPELINE_v2" / target]
        for choice in choices:
            try:
                data = _terminal_bytes(choice)
            except (OSError, ValueError):
                continue
            if _terminal_sha(data) == binding.get("sha256"):
                if choice in snapshots and snapshots[choice] != data:
                    raise _TerminalEvidenceError("current certificate binding drifted")
                snapshots[choice] = data
                return data
        raise _TerminalEvidenceError("current certificate binding is no longer current")

    expected = {
        "request": context["stage"],
        "formal_statement": context["folder"] / "VERIFICATION_STATEMENT.lean",
        "candidate_proof": context["folder"] / "VERIFICATION_CANDIDATE.lean",
    }
    for role, target in expected.items():
        if bound(bindings.get(role)) != snapshots[target]:
            raise _TerminalEvidenceError("same-run certificate object linkage unresolved")
    # Recheck current certificate file bindings, rather than treating an old
    # certificate's filename, run ID, or status as exact-object evidence.
    for role, binding in bindings.items():
        if role != "sealed_paper_inputs" and isinstance(binding, dict) and "path" in binding:
            bound(binding)
    sealed = bindings["sealed_paper_inputs"]
    for name in ("SEALED_RUN_MANIFEST.json", "SEALED_CLAIM_INVENTORY.json", "SEALED_paper.tex"):
        if bound(sealed.get(name)) != snapshots[context["folder"] / name]:
            raise _TerminalEvidenceError("same-run certificate sealed linkage unresolved")
    for binding in sealed.values():
        bound(binding)
    return {"path": str(path), "sha256": _terminal_sha(raw),
            "status": certificate.get("status"), "same_exact_terminal_object": True}


def _terminal_observation(
    control_root: Path, run_id: str, mirror_run: Path | None,
    requests: list[Path], certificate_record: tuple[Path, dict[str, Any]] | None,
) -> dict[str, Any]:
    """Report tri-state evidence; uncertainty is never proof or dispatch authority."""
    result = {"status": "NOT_APPLICABLE", "certifies": False,
              "clears_certification_debt": False, "publication_admitted": False,
              "authorizes_retry_or_transport": False}
    if run_id not in TERMINAL_RECEIPTS:
        return result
    result.update(status=TERMINAL_UNRESOLVED, expected_trusted_run=run_id,
                  expected_receipt_sha256=TERMINAL_RECEIPTS[run_id][1])
    if certificate_record is not None:
        result["selected_current_certificate"] = {
            "path": str(certificate_record[0]), "status": certificate_record[1].get("status"),
            "object_linkage": "unresolved until exact binding join completes",
        }
    try:
        finalized = control_root / "RESEARCH_PIPELINE_v2/finalized_runs" / run_id
        package = finalized if finalized.exists() or finalized.is_symlink() else control_root / "RESEARCH_PIPELINE_v2/nightly_packages" / run_id
        context = _authenticated_terminal_context(control_root, package)
        snapshots = context["snapshots"]
        result["authenticated_terminal_evidence"] = context["evidence"]
        if _terminal_sha(snapshots[context["stage"]]) != context["evidence"].get("request_sha256"):
            raise _TerminalEvidenceError("authenticated staged request readback does not match helper result")
        stage = _terminal_object(snapshots[context["stage"]])
        if stage.get("source_run") != run_id:
            raise _TerminalEvidenceError("authenticated staged run identity unresolved")
        source_sha = stage["input_sha256"]["SOURCE_ENGINE3_REQUEST.json"]
        source_path = context["folder"] / "SOURCE_ENGINE3_REQUEST.json"
        source_bytes = _remember(snapshots, source_path)
        if _terminal_sha(source_bytes) != source_sha:
            raise _TerminalEvidenceError("staged SOURCE input binding does not match actual SOURCE")
        if mirror_run is None:
            raise _TerminalEvidenceError("reported mirror is missing for terminal lineage join")
        mirror_path = mirror_run / "formalization/ENGINE3_VERIFICATION_REQUEST.json"
        if mirror_path not in requests:
            raise _TerminalEvidenceError("reported mirror request is not in proof-track provenance")
        mirror_bytes = _remember(snapshots, mirror_path)
        if mirror_bytes != source_bytes:
            raise _TerminalEvidenceError("reported mirror request does not match held SOURCE lineage")
        source = _terminal_object(source_bytes)
        if (source.get("source_run") != run_id or
                not isinstance(stage.get("candidate_id"), str) or
                not stage["candidate_id"] or source.get("candidate_id") != stage["candidate_id"]):
            raise _TerminalEvidenceError("SOURCE/staged candidate identity unresolved")
        manifest_sha = _terminal_sha(snapshots[context["manifest"]])
        if (stage["input_sha256"].get("SEALED_RUN_MANIFEST.json") != manifest_sha or
                source["input_sha256"].get("PAPER_PACKAGE_MANIFEST.json") != manifest_sha or
                snapshots[context["manifest"]] != snapshots[context["folder"] / "SEALED_RUN_MANIFEST.json"]):
            raise _TerminalEvidenceError("staged/SOURCE selected manifest bridge unresolved")
        if certificate_record is not None:
            result["current_certificate"] = _certificate_terminal_join(
                certificate_record, control_root, context, snapshots)
        # There is no authenticated distinct-successor identity in this input
        # schema. Mismatches stay unresolved, rather than becoming a new gate
        # or being promoted to successor readiness based on a changed hash.
        for path, data in snapshots.items():
            if _terminal_bytes(path) != data:
                raise _TerminalEvidenceError("terminal evidence changed during report join window")
        selected_again = finalized if finalized.exists() or finalized.is_symlink() else control_root / "RESEARCH_PIPELINE_v2/nightly_packages" / run_id
        if selected_again != package:
            raise _TerminalEvidenceError("selected terminal package changed during report join window")
        result.update(
            status=TERMINAL_CONFLICT if certificate_record is not None else "TERMINAL_PREMISE_HOLD",
            lineage={"staged_request_sha256": _terminal_sha(snapshots[context["stage"]]),
                     "source_and_reported_mirror_sha256": source_sha,
                     "selected_manifest_sha256": manifest_sha},
            readbacks=[{"path": str(path), "sha256": _terminal_sha(data), "bytes": len(data)}
                       for path, data in sorted(snapshots.items(), key=lambda row: str(row[0]))],
            currentness="byte equality across the helper and reporter read windows; not an atomic report transaction",
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError, ImportError, SyntaxError) as exc:
        result["diagnostic"] = f"{type(exc).__name__}: {exc}"
    return result


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON root must be an object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding_is_current(binding: object, control_root: Path) -> bool:
    """Resolve immutable bindings exactly as the foundry continuity gate does."""
    if not isinstance(binding, dict):
        return False
    path_value = binding.get("path")
    digest = binding.get("sha256")
    if not isinstance(path_value, str) or not isinstance(digest, str):
        return False
    path = Path(path_value)
    candidates = [path]
    if not path.is_absolute():
        candidates = [control_root / path, control_root / "RESEARCH_PIPELINE_v2" / path]
    for candidate in candidates:
        try:
            if candidate.is_file() and sha256_file(candidate) == digest:
                return True
        except OSError:
            continue
    return False


def current_certificate(control_root: Path, run_id: str) -> tuple[Path, dict[str, Any]] | None:
    root = control_root / "RESEARCH_PIPELINE_v2/lean_certificates" / run_id
    current: list[tuple[str, Path, dict[str, Any]]] = []
    for path in sorted(root.glob("LEAN_ZERO_SORRY_CERTIFICATE*.json")):
        try:
            certificate = read_json(path)
        except (OSError, json.JSONDecodeError, RuntimeError):
            continue
        if certificate.get("standard") != "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1":
            continue
        if certificate.get("status") != CERTIFIED_STATUS or certificate.get("run_id") != run_id:
            continue
        bindings = certificate.get("bindings")
        if not isinstance(bindings, dict):
            continue
        required = ["request", "independent_cloud_receipt"]
        if certificate.get("verification_standard") == "VRS-COMPARATOR-DUAL-KERNEL-1":
            required.extend(["formal_statement", "candidate_proof"])
        elif "aristotle_audit" in bindings:
            required.append("aristotle_audit")
        else:
            required.append("legacy_aristotle_audit")
        if any(not binding_is_current(bindings.get(name), control_root) for name in required):
            continue
        sealed = bindings.get("sealed_paper_inputs")
        if not isinstance(sealed, dict) or not sealed:
            continue
        if any(not binding_is_current(binding, control_root) for binding in sealed.values()):
            continue
        issued = str(certificate.get("issued_at_utc", ""))
        current.append((issued, path, certificate))
    if not current:
        return None
    _, path, certificate = max(current, key=lambda row: (row[0], row[1].name))
    return path, certificate


def canonical_run_id(value: str | int) -> str:
    match = re.fullmatch(r"(?:Run-)?(\d+)(?:[_-].*)?", str(value), re.I)
    if match is None:
        raise RuntimeError(f"invalid run identity: {value!r}")
    return f"Run-{int(match.group(1)):03d}"


def find_run(root: Path, run_id: str) -> Path | None:
    matches = sorted(path for path in root.glob(f"{run_id}_*") if path.is_dir())
    if len(matches) > 1:
        raise RuntimeError(f"multiple run directories found for {run_id}")
    return matches[0] if matches else None


def request_for_run(path: Path, run_id: str) -> dict[str, Any] | None:
    try:
        request = read_json(path)
        if canonical_run_id(request.get("source_run", "")) == run_id:
            return request
    except (OSError, json.JSONDecodeError, RuntimeError):
        pass
    return None


def request_paths_for_run(control_root: Path, run_id: str) -> list[Path]:
    root = control_root / "RESEARCH_PIPELINE_v2/aristotle_submissions"
    result = []
    if root.is_dir():
        result.extend(
            path for path in root.rglob("*.json")
            if path.name in {"ARISTOTLE_FORGE_REQUEST.json", "FORGE_REQUEST.json"}
            and not (path.parent / "FORMALIZATION_HOLD.json").is_file()
            and request_for_run(path, run_id) is not None
        )
    mirror_run = find_run(control_root / "science-engine" / RUNS_REL, run_id)
    if mirror_run is not None:
        engine3 = mirror_run / "formalization/ENGINE3_VERIFICATION_REQUEST.json"
        if engine3.is_file() and request_for_run(engine3, run_id) is not None:
            result.append(engine3)
    return sorted(result)


def row_for_request(state: dict[str, Any], request_path: Path) -> dict[str, Any] | None:
    expected = request_path.resolve()
    active = state.get("active")
    if isinstance(active, dict):
        active_path = Path(str(active.get("request_path", "")))
        if active_path.is_file() and active_path.resolve() == expected:
            return active
    for row in state.get("history", []):
        if not isinstance(row, dict):
            continue
        row_path = Path(str(row.get("request_path", "")))
        if row_path.is_file() and row_path.resolve() == expected:
            return row
    return None


def audit_for_row(row: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    value = row.get("audit_path")
    if not isinstance(value, str) or not value:
        return {}
    path = Path(value)
    if not path.is_absolute():
        path = CONTROL_ROOT / path
    try:
        return read_json(path)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return {}


def audit_recheck_for_row(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return a sibling immutable audit recheck without rewriting history."""
    if not isinstance(row, dict):
        return {}
    value = row.get("audit_path")
    if not isinstance(value, str) or not value:
        return {}
    path = Path(value)
    if not path.is_absolute():
        path = CONTROL_ROOT / path
    recheck = path.parent / "FORGE_AUDIT_RECHECK.json"
    try:
        return read_json(recheck)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return {}


def significance_hold_for_gate(control_root: Path, gate: dict[str, Any]) -> dict[str, Any]:
    """Return a bound pre-Aristotle significance HOLD, if one exists."""

    manifest_value = gate.get("manifest_path")
    if not isinstance(manifest_value, str) or not manifest_value:
        return {}
    manifest_path = Path(manifest_value)
    if not manifest_path.is_absolute():
        manifest_path = control_root / manifest_path
    try:
        manifest = read_json(manifest_path)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return {}
    binding = manifest.get("pre_aristotle_correction")
    if not isinstance(binding, dict):
        return {}
    receipt_value = binding.get("path")
    if not isinstance(receipt_value, str) or not receipt_value:
        return {}
    receipt_path = Path(receipt_value)
    if not receipt_path.is_absolute():
        receipt_path = control_root / receipt_path
    screen_path = receipt_path.parent / "SIGNIFICANCE_SCREEN_HOLD.json"
    try:
        screen = read_json(screen_path)
    except (OSError, json.JSONDecodeError, RuntimeError):
        return {}
    verdict = screen.get("verdict")
    return screen if isinstance(verdict, str) and verdict.startswith("HOLD_SIGNIFICANCE") else {}


def evaluate(
    run_value: str | int | None = None,
    *,
    control_root: Path = CONTROL_ROOT,
    live_root: Path = LIVE_ROOT,
) -> dict[str, Any]:
    live_state = read_json(live_root / STATE_REL)
    run_id = canonical_run_id(run_value if run_value is not None else live_state["current_run"])
    live_run = find_run(live_root / RUNS_REL, run_id)
    mirror_run = find_run(control_root / "science-engine" / RUNS_REL, run_id)
    mirror_receipt_path = control_root / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts" / f"{run_id}.json"
    gate_path = control_root / "RESEARCH_PIPELINE_v2/nightly_packages" / run_id / "QUALITY_GATE.json"
    state_path = control_root / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json"
    mirror_receipt = read_json(mirror_receipt_path) if mirror_receipt_path.is_file() else {}
    gate = read_json(gate_path) if gate_path.is_file() else {}
    forge_state = read_json(state_path) if state_path.is_file() else {"active": None, "history": []}
    requests = request_paths_for_run(control_root, run_id)
    request_records = [
        (path, request_for_run(path, run_id), row_for_request(forge_state, path))
        for path in requests
    ]
    request_kinds = {
        str(request.get("request_kind", "LEAN_PROOF"))
        for _, request, _ in request_records
        if request is not None
    }
    completed_proofs = [
        row for _, request, row in request_records
        if request is not None
        and request.get("request_kind", "LEAN_PROOF") != "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and row.get("status") in PROOF_GATE_PASS_STATUSES
        and audit_recheck_for_row(row).get("audit_integrity_pass") is not False
    ]
    invalidated_proofs = [
        row for _, request, row in request_records
        if request is not None
        and request.get("request_kind", "LEAN_PROOF") != "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and row.get("status") == "AUDITED_VERIFIED"
        and audit_recheck_for_row(row).get("audit_integrity_pass") is False
    ]
    active = [
        row for _, _, row in request_records
        if isinstance(row, dict)
        and row.get("status") not in PROOF_GATE_PASS_STATUSES | {"AUDIT_FAILED_TERMINAL", "AUDIT_FAILED_REPAIR_REQUIRED"}
        and row.get("status") != PROVIDER_WARNING_STATUS
    ]
    ready_proofs = [
        request for _, request, row in request_records
        if request is not None
        and request.get("request_kind", "LEAN_PROOF") != "PAPER_TO_LEAN_FORMALIZATION"
        and row is None
    ]
    engine3_ready_proofs = [
        request for request in ready_proofs
        if request.get("primary_verifier") == "COMPARATOR_CLOUD"
        and request.get("aristotle_required") is False
    ]
    failed_proofs = [
        row for _, request, row in request_records
        if request is not None
        and request.get("request_kind", "LEAN_PROOF") != "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and str(row.get("status", "")).startswith("AUDIT_FAILED")
    ]
    provider_warning_proofs = [
        row for _, request, row in request_records
        if request is not None
        and request.get("request_kind", "LEAN_PROOF") != "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and row.get("status") == PROVIDER_WARNING_STATUS
    ]
    formalization_audited = any(
        request is not None
        and request.get("request_kind") == "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and (
            row.get("status") in PROOF_GATE_PASS_STATUSES
            or audit_for_row(row).get("formalization_contract_pass") is True
        )
        for _, request, row in request_records
    )
    failed_formalizations = [
        row for _, request, row in request_records
        if request is not None
        and request.get("request_kind") == "PAPER_TO_LEAN_FORMALIZATION"
        and isinstance(row, dict)
        and str(row.get("status", "")).startswith("AUDIT_FAILED")
    ]
    significance_hold = significance_hold_for_gate(control_root, gate)
    certificate_record = current_certificate(control_root, run_id)
    significance_status = significance_hold.get("verdict")
    if not significance_status:
        for _, request, row in reversed(request_records):
            if request is None:
                continue
            audit = audit_for_row(row)
            audit_significance = audit.get("evidence", {}).get("significance", {})
            audit_verdict = audit_significance.get("verdict")
            if isinstance(audit_verdict, str) and audit_verdict.startswith("HOLD_SIGNIFICANCE"):
                significance_status = audit_verdict
                break
            request_status = request.get("significance_status")
            if isinstance(request_status, str) and request_status.startswith("HOLD_SIGNIFICANCE"):
                significance_status = request_status
                break

    generated = live_run is not None and (live_run / "RUN_MANIFEST.json").is_file()
    mirrored = mirror_run is not None and mirror_receipt.get("status") == "MIRRORED"
    if not generated:
        proof_status = "NOT_GENERATED"
    elif not mirrored:
        proof_status = "WAITING_FOR_MIRROR"
    # Engine-3's hash-bound dual-kernel certificate is the current proof
    # authority.  Legacy Aristotle rows remain provenance and must not mask a
    # clean Comparator certificate, including when those rows are terminal.
    elif certificate_record is not None:
        proof_status = CERTIFIED_STATUS
    elif completed_proofs:
        proof_status = "HOLD_INDEPENDENT_CLOUD_CERTIFICATE_REQUIRED"
    elif invalidated_proofs:
        proof_status = "HOLD_AUDIT_INTEGRITY_RECHECK"
    elif engine3_ready_proofs:
        proof_status = "READY_FOR_COMPARATOR_CERTIFICATION"
    elif active:
        # Legacy provider activity is retained as provenance, but it must not
        # block or impersonate the production Engine-3 certification route.
        proof_status = "HOLD_ENGINE3_MIGRATION_REQUIRED"
    elif ready_proofs:
        proof_status = "HOLD_ENGINE3_MIGRATION_REQUIRED"
    elif failed_proofs:
        proof_status = str(failed_proofs[-1].get("status"))
    elif provider_warning_proofs:
        proof_status = "HOLD_CLEAN_CERTIFICATE_REQUIRED"
    elif formalization_audited:
        proof_status = "HOLD_PROOF_REQUEST_NOT_STAGED"
    elif failed_formalizations:
        proof_status = str(failed_formalizations[-1].get("status"))
    elif requests:
        proof_status = "HOLD_ENGINE3_MIGRATION_REQUIRED"
    else:
        proof_status = "HOLD_MISSING_FROZEN_PROOF_REQUEST"

    terminal_statement_drift = (
        proof_status == "AUDIT_FAILED_TERMINAL"
        and bool(failed_proofs)
        and "statement_freeze_pass" in failed_proofs[-1].get("failed_checks", [])
    )
    paper_saturday_status = gate.get("saturday_status")
    if paper_saturday_status == "HOLD_ARISTOTLE":
        paper_saturday_status = "HOLD_CORRECTION" if terminal_statement_drift else "HOLD_CERTIFICATE"
    # An older pre-proof quality receipt must not keep advertising missing
    # certification after a current exact-hash certificate has landed. This
    # changes no quality failure or independent-review/finalization evidence.
    if certificate_record is not None and paper_saturday_status == "HOLD_CERTIFICATE":
        paper_saturday_status = "HOLD_RECONCILIATION"

    original_proof_status = proof_status
    terminal_evidence = _terminal_observation(
        control_root, run_id, mirror_run, requests, certificate_record)
    terminal_evidence["original_proof_status"] = original_proof_status
    terminal_applies = terminal_evidence["status"] != "NOT_APPLICABLE"
    # Generation/mirror debt remains visible independently. Once both exist,
    # exact terminal evidence, uncertainty, or a certificate conflict must take
    # precedence over nominal readiness/certification without deleting either.
    if terminal_applies and generated and mirrored:
        proof_status = terminal_evidence["status"]

    return {
        "schema_version": 1,
        "standard": "VRS-MANDATORY-PROOF-TRACK-1",
        "run_id": run_id,
        "proof_status": proof_status,
        "proof_required": True,
        "generated": generated,
        "mirrored": mirrored,
        "paper_quality_verdict": gate.get("quality_verdict"),
        "paper_saturday_status": paper_saturday_status,
        "significance_gate_status": significance_status,
        "terminal_evidence": terminal_evidence,
        "request_paths": [str(path) for path in requests],
        "request_kinds": sorted(request_kinds),
        "aristotle_rows": [
            {**row, "request_kind": request.get("request_kind", "LEAN_PROOF")}
            for _, request, row in request_records
            if request is not None and isinstance(row, dict)
        ],
        "audit_rechecks": [
            audit_recheck_for_row(row)
            for _, request, row in request_records
            if request is not None and audit_recheck_for_row(row)
        ],
        "next_action": (
            "retain both the exact terminal premise hold and selected certificate for independent conflict review; this report authorizes no retry, transport, certificate issuance or publication" if terminal_evidence["status"] == TERMINAL_CONFLICT
            else "retain the expected trusted terminal hold as unresolved evidence pending exact-lineage review; this report authorizes no retry, transport, successor generation, certificate issuance or publication" if terminal_evidence["status"] == TERMINAL_UNRESOLVED
            else "retain the authenticated terminal premise hold and independent quality, significance and certification debt; recovery requires separate authorization and this report authorizes no retry or transport" if terminal_applies
            else "complete paper reconciliation and later independent review before finalization and local assembly" if proof_status == CERTIFIED_STATUS
            else "audit the returned project" if proof_status == "DOWNLOADED_UNAUDITED"
            else "deliberately reformulate the false or drifted target and freeze a new paper/claim/Lean contract; automatic repair is prohibited" if terminal_statement_drift
            else "reconcile the manager history against the immutable audit recheck before treating the proof as landed" if proof_status == "HOLD_AUDIT_INTEGRITY_RECHECK"
            else "retain the disclosed provider warning and continue only to internal paper reconciliation" if proof_status == "PROOF_GATE_ACCEPTED_ZERO_SORRY_PROVIDER_WARNING"
            else "freeze a fresh exact-source Engine-3 candidate and verify it with Comparator; provider-warning-only evidence remains certificate debt" if proof_status == "HOLD_CLEAN_CERTIFICATE_REQUIRED"
            else "run exact-byte independent cloud Lean verification, then issue the immutable dual-gate certificate" if proof_status == "HOLD_INDEPENDENT_CLOUD_CERTIFICATE_REQUIRED"
            else "verify the exact frozen statement and zero-sorry candidate with Comparator, then issue the immutable certificate" if proof_status == "READY_FOR_COMPARATOR_CERTIFICATION"
            else "freeze an Engine-3 exact-byte Comparator request and zero-sorry candidate without creating or retrying an Aristotle project" if proof_status == "HOLD_ENGINE3_MIGRATION_REQUIRED"
            else "submit the oldest paper-to-Lean formalization request when the one-project slot is free; a returned formalization is not yet a proof certificate" if proof_status == "READY_FOR_PAPER_TO_LEAN_FORMALIZATION"
            else "stage the separate exact proof request from the audited formalization contract" if proof_status == "HOLD_PROOF_REQUEST_NOT_STAGED"
            else "stage a hash-bound Engine-3 Lean statement, zero-sorry candidate, and Comparator request" if proof_status == "HOLD_MISSING_FROZEN_PROOF_REQUEST"
            else "stage or submit the frozen proof request while retaining the independent significance hold as a separate classification gate" if proof_status.startswith("HOLD_SIGNIFICANCE")
            else "continue the recorded proof-track state without inferring proof" 
        ),
        "external_mutation": False,
        "lean_certificate": (
            {"path": str(certificate_record[0]), "status": certificate_record[1].get("status")}
            if certificate_record is not None else None
        ),
    }


def saturday_report(run_values: list[str], date: str, *, control_root: Path, live_root: Path) -> dict[str, Any]:
    rows = [evaluate(run, control_root=control_root, live_root=live_root) for run in run_values]
    return {
        "schema_version": 1,
        "standard": "VRS-MANDATORY-PROOF-TRACK-1",
        "date": date,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "runs": rows,
        "all_runs_have_frozen_request": all(bool(row["request_paths"]) for row in rows),
        "external_mutation": False,
    }


def assert_report_output_is_mutable(output: Path) -> None:
    """Refuse to rewrite evidence inside an already sealed Saturday packet."""
    seal = output.parent / "SATURDAY_PACKAGE_MANIFEST.json"
    if seal.is_file():
        raise RuntimeError(
            f"sealed Saturday packet is immutable: {output}; write the live proof-track report "
            "to the current unsealed packet instead"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", help="run number; repeat for a Saturday report")
    parser.add_argument("--saturday-report", metavar="YYYY-MM-DD", help="write a local packet proof-track report")
    parser.add_argument("--output", type=Path, help="required with --saturday-report")
    args = parser.parse_args()
    try:
        if args.saturday_report:
            if not args.output:
                raise RuntimeError("--saturday-report requires --output")
            if not args.run:
                raise RuntimeError("--saturday-report requires at least one --run")
            assert_report_output_is_mutable(args.output)
            result = saturday_report(args.run, args.saturday_report, control_root=CONTROL_ROOT, live_root=LIVE_ROOT)
            write_json_atomic(args.output, result)
        else:
            result = evaluate(args.run[-1] if args.run else None)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc), "external_mutation": False}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
