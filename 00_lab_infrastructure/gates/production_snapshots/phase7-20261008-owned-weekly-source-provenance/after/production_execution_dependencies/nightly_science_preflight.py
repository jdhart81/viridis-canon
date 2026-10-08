#!/usr/bin/env python3
"""Fail-closed preflight for the Codex nightly science generator."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from viridis_paths import CONTROL_ROOT


SCIENCE_ROOT = Path("/Users/justinhart/Desktop/science ")
RUNS_REL = Path("07_nightly_engine/compound research papers")
STATE_REL = Path("07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json")
LEGACY_STATE_REL = Path("07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.md")
POLICY_REL = Path("RESEARCH_PIPELINE_v2/NIGHTLY_SELECTION_POLICY_v1.json")
RECEIPT_GATED_FIRST_RUN = 117
ENGINE3_ATOMIC_FIRST_RUN = 148

REQUIRED_CONTROL = (
    "RESEARCH_PIPELINE_v2/CODEX_NIGHTLY_SCIENCE_GENERATION_STANDARD.md",
    "RESEARCH_PIPELINE_v2/NIGHTLY_PAPER_PACKAGE_STANDARD.md",
    "RESEARCH_PIPELINE_v2/VIRIDIS_RESEARCH_SUBMISSION_GATE_STANDARD.md",
    "RESEARCH_PIPELINE_v2/LEAN_CERTIFICATION_STANDARD.md",
    "RESEARCH_PIPELINE_v2/NIGHTLY_SCIENCE_CANON_LOGIC_AUDIT_2026-08-01.md",
    "RESEARCH_PIPELINE_v2/CANON_BACKLOG.md",
    "RESEARCH_PIPELINE_v2/canon_fingerprint_index.json",
    "ZENODO_SUBMISSION_LEDGER.md",
    "CANON_MAP.md",
    "CANON_SPINE_DOCTRINE.md",
)


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _latest_run(runs_dir: Path) -> tuple[int, Path]:
    found = []
    for child in runs_dir.iterdir():
        match = re.fullmatch(r"Run-(\d{3})_.+", child.name)
        if child.is_dir() and match:
            found.append((int(match.group(1)), child))
    if not found:
        raise ValueError(f"no numbered run directories under {runs_dir}")
    return max(found, key=lambda item: item[0])


def _formal_target_run(run_dir: Path) -> bool:
    inventory_path = run_dir / "CLAIM_INVENTORY.json"
    try:
        inventory = _load_json(inventory_path)
    except (OSError, json.JSONDecodeError):
        return False
    claims = inventory.get("claims")
    if not isinstance(claims, list):
        return False
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        classifications = claim.get("classification")
        if claim.get("evidence_class") == "FORMAL_TARGET" or (
            isinstance(classifications, list) and "FORMAL_TARGET" in classifications
        ):
            return True
    return False


def _request_runs(control_root: Path) -> set[int]:
    result: set[int] = set()
    root = control_root / "RESEARCH_PIPELINE_v2/aristotle_submissions"
    if root.is_dir():
        for path in root.rglob("ARISTOTLE_FORGE_REQUEST.json"):
            if (path.parent / "FORMALIZATION_HOLD.json").is_file():
                continue
            try:
                request = _load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            match = re.fullmatch(r"Run-(\d+)", str(request.get("source_run", "")))
            if match and int(match.group(1)) < ENGINE3_ATOMIC_FIRST_RUN and isinstance(request.get("input_sha256"), dict) and request.get("statement_contract_sha256"):
                result.add(int(match.group(1)))

    # Engine 3 freezes its exact-byte Comparator request inside the mirrored
    # nightly package. Aristotle requests remain immutable legacy provenance,
    # but they are not a scheduled-generation dependency.
    mirror_root = control_root / "science-engine" / RUNS_REL
    if mirror_root.is_dir():
        for path in mirror_root.glob("Run-*/formalization/ENGINE3_VERIFICATION_REQUEST.json"):
            try:
                request = _load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            match = re.fullmatch(r"Run-(\d+)", str(request.get("source_run", "")))
            if (
                match
                and request.get("request_kind") == "LEAN_PROOF"
                and request.get("primary_verifier") == "COMPARATOR_CLOUD"
                and request.get("aristotle_required") is False
                and isinstance(request.get("input_sha256"), dict)
                and request.get("statement_contract_sha256")
            ):
                result.add(int(match.group(1)))
    certificate_root = control_root / "RESEARCH_PIPELINE_v2/lean_certificates"
    if certificate_root.is_dir():
        for path in certificate_root.glob("Run-*/ENGINE3_VERIFICATION_REQUEST*.json"):
            try:
                request = _load_json(path)
            except (OSError, json.JSONDecodeError):
                continue
            match = re.fullmatch(r"Run-(\d+)", str(request.get("source_run", "")))
            if (
                match
                and request.get("request_kind") == "LEAN_PROOF"
                and request.get("primary_verifier") == "COMPARATOR_CLOUD"
                and request.get("aristotle_required") is False
                and isinstance(request.get("input_sha256"), dict)
                and request.get("statement_contract_sha256")
            ):
                result.add(int(match.group(1)))
    return result


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binding_is_current(binding: object, base: Path | None = None) -> bool:
    if not isinstance(binding, dict):
        return False
    path_value = binding.get("path")
    digest = binding.get("sha256")
    if not isinstance(path_value, str) or not isinstance(digest, str):
        return False
    path = Path(path_value)
    candidates = [path]
    if base is not None:
        if not path.is_absolute():
            candidates = [base / path, base / "RESEARCH_PIPELINE_v2" / path]
        elif "RESEARCH_PIPELINE_v2" in path.parts:
            # Early Engine-3 receipts captured a legacy control-root spelling
            # with two spaces before ``2.0``. Resolve the immutable suffix
            # against the configured control root without rewriting the receipt.
            marker = path.parts.index("RESEARCH_PIPELINE_v2")
            candidates.append(base.joinpath(*path.parts[marker:]))
    for candidate in candidates:
        try:
            if candidate.is_file() and _sha256(candidate) == digest:
                return True
        except OSError:
            continue
    return False


def _has_current_certificate(control_root: Path, run_number: int) -> bool:
    run_id = f"Run-{run_number:03d}"
    certificate_root = control_root / "RESEARCH_PIPELINE_v2/lean_certificates" / run_id
    if (certificate_root / "CERTIFICATION_INTEGRITY_HOLD.json").is_file():
        from nightly_proof_track import current_certificate
        return current_certificate(control_root, run_id) is not None
    path = (
        certificate_root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    )
    try:
        certificate = _load_json(path)
    except (OSError, json.JSONDecodeError):
        return False
    if certificate.get("status") != "LEAN_ZERO_SORRY_CERTIFIED":
        return False
    if certificate.get("standard") != "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1":
        return False
    if certificate.get("run_id") != f"Run-{run_number:03d}":
        return False
    bindings = certificate.get("bindings")
    if not isinstance(bindings, dict):
        return False
    core_current = all(
        _binding_is_current(bindings.get(name), control_root)
        for name in ("request", "independent_cloud_receipt")
    )
    if certificate.get("verification_standard") == "VRS-COMPARATOR-DUAL-KERNEL-1":
        core_current = core_current and all(
            _binding_is_current(bindings.get(name), control_root)
            for name in ("formal_statement", "candidate_proof")
        )
    else:
        core_current = core_current and (
            _binding_is_current(bindings.get("aristotle_audit"), control_root)
            or _binding_is_current(bindings.get("legacy_aristotle_audit"), control_root)
        )
    sealed = bindings.get("sealed_paper_inputs")
    return bool(
        core_current
        and isinstance(sealed, dict)
        and sealed
        and all(_binding_is_current(binding, control_root) for binding in sealed.values())
    )


def _open_proof_obligations(runs_dir: Path, control_root: Path, latest_num: int) -> dict[str, list[int]]:
    request_runs = _request_runs(control_root)
    missing_mirror: list[int] = []
    missing_request: list[int] = []
    missing_certificate: list[int] = []
    for number in range(RECEIPT_GATED_FIRST_RUN, latest_num + 1):
        matches = sorted(path for path in runs_dir.glob(f"Run-{number:03d}_*") if path.is_dir())
        if len(matches) != 1:
            continue
        receipt_path = control_root / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts" / f"Run-{number:03d}.json"
        try:
            receipt = _load_json(receipt_path)
        except (OSError, json.JSONDecodeError):
            receipt = {}
        if receipt.get("status") != "MIRRORED":
            missing_mirror.append(number)
        if number not in request_runs:
            missing_request.append(number)
        if not _has_current_certificate(control_root, number):
            missing_certificate.append(number)
    return {
        "missing_mirror": missing_mirror,
        "missing_request": missing_request,
        "missing_certificate": missing_certificate,
    }


def preflight(science_root: Path, control_root: Path, expected_next: int | None = None) -> dict:
    failures: list[str] = []
    continuity_warnings: list[str] = []
    checks: dict[str, object] = {}

    checks["science_root"] = str(science_root)
    if not str(science_root).endswith("science "):
        failures.append("science root does not preserve the required trailing space")
    if not science_root.is_dir():
        failures.append("exact science root is missing")
    shadow = Path(str(science_root).rstrip())
    if shadow != science_root and shadow.exists():
        failures.append(f"ambiguous shadow science root exists: {shadow}")

    for rel in REQUIRED_CONTROL:
        if not (control_root / rel).is_file():
            failures.append(f"missing control document: {rel}")
    if not (control_root / "new leans").is_dir():
        failures.append("missing landed Lean artifact root: new leans")

    runs_dir = science_root / RUNS_REL
    state_path = science_root / STATE_REL
    legacy_path = science_root / LEGACY_STATE_REL
    policy_path = control_root / POLICY_REL
    if not runs_dir.is_dir():
        failures.append(f"missing run root: {runs_dir}")
    if not state_path.is_file():
        failures.append(f"missing machine state: {state_path}")
    if not legacy_path.is_file():
        failures.append(f"missing historical state: {legacy_path}")
    if not policy_path.is_file():
        failures.append(f"missing policy: {policy_path}")

    latest_num = None
    latest_path = None
    state = None
    policy = None
    if not failures:
        try:
            latest_num, latest_path = _latest_run(runs_dir)
            state = _load_json(state_path)
            policy = _load_json(policy_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failures.append(str(exc))

    if state is not None and latest_num is not None:
        current = state.get("current_run")
        next_run = current + 1 if isinstance(current, int) else None
        checks.update({"latest_run": latest_num, "latest_path": str(latest_path), "state_current_run": current, "next_run": next_run})
        if current != latest_num:
            failures.append(f"machine state current_run {current!r} != latest run directory {latest_num}")
        if expected_next is not None and next_run != expected_next:
            failures.append(f"expected next run {expected_next}, state requires {next_run}")
        if next_run is not None and any(runs_dir.glob(f"Run-{next_run:03d}_*")):
            failures.append(f"next run directory already exists for Run-{next_run:03d}")
        directives = [item for item in state.get("locked_directives", []) if item.get("run") == next_run]
        if len(directives) != 1:
            failures.append(f"next run requires exactly one locked directive; found {len(directives)}")
        else:
            checks["directive"] = directives[0]
        if sum(item.get("staleness", 0) for item in state.get("areas", [])) != state.get("sum_staleness"):
            failures.append("machine-state staleness checksum does not match sum_staleness")
        obligations = _open_proof_obligations(runs_dir, control_root, latest_num)
        checks["proof_obligations"] = obligations
        if obligations["missing_mirror"]:
            failures.append(
                "older formal targets lack MIRRORED receipts: "
                + ", ".join(f"Run-{number:03d}" for number in obligations["missing_mirror"])
            )
        if obligations["missing_request"]:
            failures.append(
                "older formal targets lack hash-bound formal requests: "
                + ", ".join(f"Run-{number:03d}" for number in obligations["missing_request"])
            )
        if obligations["missing_certificate"]:
            continuity_warnings.append(
                "rolling certificate debt must be drained in parallel; missing current independent zero-sorry certificates: "
                + ", ".join(f"Run-{number:03d}" for number in obligations["missing_certificate"])
            )

    if state is not None and policy is not None:
        if state.get("selection_policy_id") != policy.get("policy_id"):
            failures.append("machine state and selection policy IDs disagree")
        if policy.get("generator_exit_state") != "DISPOSITION_ASSIGNED":
            failures.append("policy generator exit state does not require disposition")

    checks["status"] = "READY" if not failures else "HOLD"
    checks["foundry_mode"] = "CONTINUOUS_GENERATION_ROLLING_CERTIFICATION"
    checks["generation_blocked_by_certificate_debt"] = False
    checks["continuity_warnings"] = continuity_warnings
    checks["failures"] = failures
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--science-root", type=Path, default=SCIENCE_ROOT)
    parser.add_argument("--control-root", type=Path, default=CONTROL_ROOT)
    parser.add_argument("--expected-next", type=int)
    args = parser.parse_args()
    result = preflight(args.science_root, args.control_root, args.expected_next)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "READY" else 2


if __name__ == "__main__":
    sys.exit(main())
