#!/usr/bin/env python3
"""Build the ordered, fail-closed work queue for the Viridis research foundry.

This controller is deliberately local and reversible.  It discovers the next
eligible state transition for every finalized run, records the first blocker,
and exposes exactly one human boundary: authorization of a sealed publication
or production deployment transaction.  It never publishes, pushes, deploys,
assigns rights, or invents a ledger row.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any
from verification_state_metadata import certified_metadata_contradictions
from comparator_data_egress_authorization import validate_authorization
import viridisos_kernel_packager as kernel_packager



HERE = Path(__file__).resolve().parent
FINALIZED_ROOT = HERE / "finalized_runs"
CERTIFICATE_ROOT = HERE / "lean_certificates"
NIGHTLY_PACKAGES_ROOT = HERE / "nightly_packages"
RELEASE_CANDIDATES_ROOT = HERE / "saturday_candidates"
VIRIDISOS_KERNEL_PACKAGES_ROOT = HERE / "viridisos_kernel_packages"
VIRIDISOS_INTAKE = HERE.parent / "ViridisOS/runtime/research_intake.json"
SUBMISSION_MAP = HERE / "RESEARCH_SUBMISSION_MAP_LIVE_2026-08-30.json"
COMPARATOR_AUTHORIZATION = HERE / "COMPARATOR_DATA_EGRESS_AUTHORIZATION.json"
VERIFIER_BACKENDS = HERE / "LEAN_VERIFIER_BACKENDS.json"
DEFAULT_RECEIPT = Path(
    "/Users/justinhart/Desktop/science /07_nightly_engine/viridis-science-agent/nightly/"
    "AUTONOMOUS_PIPELINE_STATE.json"
)
RUN_RE = re.compile(r"Run-(\d{3,})$")
REQUIRED_CERT_GATES = {
    "allowed_axioms_only",
    "comparator_lean_kernel",
    "comparator_nanoda_kernel",
    "comparator_statement_identity",
    "frozen_statement_and_candidate_hash_bound",
    "independent_cloud_kernel_verification",
    "nonvacuity_witnesses",
    "sealed_statement_signature_alignment",
    "zero_sorries_or_admits",
}


@dataclass(frozen=True)
class WorkItem:
    run_id: str
    state: str
    next_action: str
    human_gate: bool
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def run_number(path: Path) -> int:
    match = RUN_RE.fullmatch(path.name)
    if match is None:
        raise ValueError(f"invalid run directory: {path}")
    return int(match.group(1))


def certificate_clean(run_id: str, finalized: Path, certificate_root: Path) -> bool:
    certificate_dir = certificate_root / run_id
    if (certificate_dir / "CERTIFICATION_INTEGRITY_HOLD.json").is_file():
        from nightly_proof_track import current_certificate
        control_root = certificate_root.parents[1]
        return current_certificate(control_root, run_id) is not None
    candidates = [finalized / "LEAN_ZERO_SORRY_CERTIFICATE.json"]
    if certificate_dir.is_dir():
        candidates.extend(sorted(certificate_dir.glob("LEAN_ZERO_SORRY_CERTIFICATE*.json")))
    for path in candidates:
        if not path.is_file():
            continue
        try:
            cert = read_json(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        gates = cert.get("gates", {})
        if (
            cert.get("run_id") == run_id
            and cert.get("status") == "LEAN_ZERO_SORRY_CERTIFIED"
            and cert.get("verification_standard") == "VRS-COMPARATOR-DUAL-KERNEL-1"
            and isinstance(gates, dict)
            and all(gates.get(key) is True for key in REQUIRED_CERT_GATES)
            and gates.get("local_lean_execution") is False
        ):
            return True
    return False


def review_passes(finalized: Path) -> bool:
    path = finalized / "POST_ARISTOTLE_REVIEW.json"  # compatibility filename
    if not path.is_file():
        return False
    try:
        review = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False
    return (
        review.get("schema_version") == 2
        and review.get("verdict") == "pass"
        and bool(review.get("reviewer_system"))
        and bool(review.get("reviewer_model"))
        and all(review.get("checks", {}).values())
    )


def review_hold(finalized: Path) -> str | None:
    path = finalized / "POST_ARISTOTLE_REVIEW.json"  # compatibility filename
    if not path.is_file():
        return None
    try:
        review = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    if review.get("schema_version") != 2 or review.get("verdict") != "hold":
        return None
    hold = review.get("hold", {})
    if isinstance(hold, dict) and hold.get("code"):
        return str(hold["code"])
    return "HOLD_INDEPENDENT_REVIEW"


def release_metadata(finalized: Path) -> dict[str, Any]:
    path = finalized / "PAPER_PACKAGE_MANIFEST.json"
    if not path.is_file():
        return {}
    try:
        return dict(read_json(path).get("release_metadata", {}))
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return {}


def published_runs(intake_path: Path) -> set[str]:
    if not intake_path.is_file():
        return set()
    try:
        payload = read_json(intake_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return set()
    return {
        str(row.get("run_id"))
        for row in payload.get("records", [])
        if isinstance(row, dict) and row.get("doi")
    }


def published_source_hashes(submission_map_path: Path) -> set[str]:
    """Return artifact hashes already attached to an immutable public DOI.

    The research map is deliberately a second publication authority.  A run
    can predate ViridisOS intake while already existing on Zenodo and Git.  In
    that case it must be reconciled, never sent down the new-publication path.
    """
    if not submission_map_path.is_file():
        return set()
    try:
        payload = read_json(submission_map_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return set()
    hashes: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            source_hash = value.get("source_sha256")
            if value.get("doi") and isinstance(source_hash, str) and re.fullmatch(r"[0-9a-f]{64}", source_hash):
                hashes.add(source_hash)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return hashes


def finalized_lean_hashes(finalized: Path) -> set[str]:
    import hashlib

    hashes: set[str] = set()
    for path in finalized.glob("*.lean"):
        if path.is_file():
            hashes.add(hashlib.sha256(path.read_bytes()).hexdigest())
    return hashes


def complete_submission_package(run_id: str, candidates_root: Path) -> bool:
    """Require the complete reversible release object before any human gate."""
    required = {
        "paper.pdf", "paper.tex", "CITATION.cff", "RIGHTS_AND_LICENSE.md",
        "RELEASE_README.md", "REPRODUCTION_BUNDLE.zip", "SHA256SUMS.txt",
        "GIT_PAYLOAD_MANIFEST.json", "zenodo_metadata.json",
    }
    for manifest_path in sorted(candidates_root.glob("*/*/BUNDLE_MANIFEST.json")):
        try:
            manifest = read_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if manifest.get("run_id") != run_id:
            continue
        bundle = manifest_path.parent
        completeness = manifest.get("package_completeness", {})
        if not isinstance(completeness, dict) or completeness.get("status") != "READY_EXCEPT_RIGHTS_LICENSE_LEDGER_AUTHORIZATION":
            continue
        if not all((bundle / name).is_file() for name in required):
            continue
        try:
            lines = (bundle / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            continue
        seen: set[str] = set()
        valid = bool(lines)
        for line in lines:
            try:
                expected, relative = line.split("  ", 1)
                parts = relative.split("/")
                if (
                    re.fullmatch(r"[0-9a-f]{64}", expected) is None
                    or relative != relative.strip()
                    or "\\" in relative
                    or any(part in {"", ".", ".."} for part in parts)
                    or Path(relative).is_absolute()
                    or relative in seen
                    or relative == "SHA256SUMS.txt"
                ):
                    raise ValueError("invalid or duplicate checksum path")
                artifact = bundle / relative
                artifact.resolve().relative_to(bundle.resolve())
                if any(bundle.joinpath(*parts[:index]).is_symlink() for index in range(1, len(parts) + 1)):
                    raise ValueError("checksum paths must not follow symlinks")
                actual = hashlib.sha256(artifact.read_bytes()).hexdigest()
            except (OSError, ValueError):
                valid = False
                break
            if actual != expected:
                valid = False
                break
            seen.add(relative)
        # The checksum file cannot bind itself. Every other mandatory artifact
        # must have a verified row; optional listed files are verified above too.
        if valid and (required - {"SHA256SUMS.txt"}).issubset(seen):
            return True
    return False


def complete_kernel_package(run_id: str, kernel_packages_root: Path, finalized_run: Path | None = None) -> bool:
    """Revalidate all current package evidence without creating or refreshing it."""
    finalized_run = finalized_run or FINALIZED_ROOT / run_id
    if finalized_run.name != run_id:
        return False
    try:
        kernel_packager.validate_existing_kernel_package(
            run_id, finalized_root=finalized_run.parent,
            output_root=kernel_packages_root,
        )
    except (kernel_packager.KernelPackageError, OSError, ValueError, TypeError, KeyError):
        return False
    return True


def inspect_run(
    path: Path,
    certificate_root: Path,
    ingested: set[str],
    public_source_hashes: set[str],
    release_candidates_root: Path,
    comparator_authorized: bool,
    kernel_packages_root: Path,
) -> WorkItem:
    run_id = path.name
    if run_id in ingested:
        return WorkItem(run_id, "VIRIDISOS_TRACKED", "VERIFY_WRAPPER_OR_EXPLICIT_BACKLOG", False,
                        "Published DOI is in ViridisOS intake; maintain LIVE, PREVIEW/BLOCKED, or BACKLOG_NO_WRAPPER.")
    if finalized_lean_hashes(path) & public_source_hashes:
        if (path / "PUBLIC_IDENTITY_RECONCILIATION.json").is_file():
            return WorkItem(run_id, "READY_FOR_EXISTING_IDENTITY_BINDING_AUTHORIZATION",
                            "WAIT_FOR_EXACT_RECONCILIATION_AUTHORIZATION", True,
                            "Existing DOI/Git identity is sealed for reconciliation; never republish this run.")
        return WorkItem(run_id, "PUBLICATION_RECONCILIATION_REQUIRED",
                        "SEAL_EXISTING_DOI_GIT_IDENTITY", False,
                        "An immutable public DOI already matches the Lean source; reconcile it into the ledger and ViridisOS without republishing.")
    legacy_final_pass = (path / "FINALIZED_PACKAGE.json").is_file() and review_passes(path)
    if not legacy_final_pass and not certificate_clean(run_id, path, certificate_root):
        if not comparator_authorized:
            return WorkItem(run_id, "READY_FOR_COMPARATOR_TRANSPORT_AUTHORIZATION",
                            "WAIT_FOR_EXACT_COMPARATOR_PAYLOAD_DESTINATION_AUTHORIZATION", True,
                            "Frozen proof inputs may not leave the workspace because the standing private-Comparator authorization is missing or invalid.")
        return WorkItem(run_id, "CERTIFICATE_REQUIRED", "CERTIFY_COMPARATOR_FIFO", False,
                        "No clean dual-kernel zero-sorry certificate is bound.")
    if not (path / "CURATOR_DRAFT_READY.json").is_file():
        return WorkItem(run_id, "RECONCILIATION_REQUIRED", "CURATE_PROOF_RECONCILED_DRAFT", False,
                        "Certificate is clean; a sealed paper-to-proof draft is absent.")
    manifest_path = path / "PAPER_PACKAGE_MANIFEST.json"
    if manifest_path.is_file():
        try:
            contradictions = certified_metadata_contradictions(read_json(manifest_path))
        except (OSError, ValueError, json.JSONDecodeError):
            contradictions = []
        if contradictions:
            return WorkItem(run_id, "VERIFICATION_METADATA_RECONCILIATION_REQUIRED",
                            "CREATE_VERSIONED_VERIFICATION_METADATA_CORRECTION", False,
                            "Certified package prose contradicts its bound Comparator certificate: " + ", ".join(contradictions))
    hold_code = review_hold(path)
    if hold_code:
        return WorkItem(run_id, "REVIEW_HOLD_REPAIR_REQUIRED", "CREATE_VERSIONED_CORRECTION_OVERLAY", False,
                        f"Independent review stopped the package at {hold_code}; preserve the held overlay and repair by revision.")
    if not review_passes(path):
        return WorkItem(run_id, "INDEPENDENT_REVIEW_REQUIRED", "REVIEW_PRIOR_INVOCATION_DRAFT", False,
                        "Review must occur in an invocation later than draft creation.")
    if not (path / "FINALIZED_PACKAGE.json").is_file():
        return WorkItem(run_id, "FINALIZATION_REQUIRED", "FINALIZE_REVIEWED_PACKAGE", False,
                        "Independent review passes; deterministic finalizer has not sealed the package.")
    if not (path / "CANON_PRODUCT_ROUTE.json").is_file():
        return WorkItem(run_id, "CANON_SCAN_REQUIRED", "RUN_CANON_AND_PRODUCT_ROUTE", False,
                        "Apply significance, five-gate Canon scan, and ViridisOS disposition.")
    if int(run_id.removeprefix("Run-")) >= 151 and not (path / "KERNEL_ADMISSION_REVIEW.json").is_file():
        return WorkItem(run_id, "KERNEL_ADMISSION_REVIEW_REQUIRED", "REVIEW_KERNEL_ADMISSION", False,
                        "A later independent invocation must rank the science and review its exact paper, Comparator certificate, runtime role, empirical status, decision family, scope, and refusal boundary.")
    if not complete_kernel_package(run_id, kernel_packages_root, path):
        if (kernel_packages_root / run_id / "VIRIDISOS_KERNEL_PACKAGE.json").exists():
            return WorkItem(run_id, "KERNEL_PACKAGE_RECONCILIATION_REQUIRED", "REVIEW_EXISTING_KERNEL_PACKAGE_BINDINGS", False,
                            "Existing kernel package no longer binds current evidence; preserve it and review a versioned successor.")
        return WorkItem(run_id, "VIRIDISOS_KERNEL_PACKAGE_REQUIRED", "BUILD_VIRIDISOS_KERNEL_PACKAGE", False,
                        "Seal a hash-bound runtime adapter package or an explicit NO_RUNTIME_KERNEL disposition before release assembly.")
    if not complete_submission_package(run_id, release_candidates_root):
        return WorkItem(run_id, "FULL_PACKAGE_ASSEMBLY_REQUIRED",
                        "ASSEMBLE_AUGMENT_AND_VERIFY_SUBMISSION_PACKAGE", False,
                        "Nightly production is incomplete until the sealed paper, metadata, citation, rights proposal, reproduction archive, checksums, Git payload, and Zenodo dry-run surface all exist.")
    metadata = release_metadata(path)
    if not metadata.get("license") or metadata.get("ledger_row") is None:
        proposal_path = path / "RELEASE_BINDING_PROPOSAL.json"
        if proposal_path.is_file():
            try:
                proposal = read_json(proposal_path)
            except (OSError, ValueError, json.JSONDecodeError):
                proposal = {}
            if (
                proposal.get("status") == "READY_FOR_EXACT_AUTHORIZATION"
                and proposal.get("run_id") == run_id
                and isinstance(proposal.get("proposed_ledger_row"), int)
                and proposal.get("proposed_ledger_row") > 0
                and proposal.get("proposed_license")
            ):
                return WorkItem(run_id, "READY_FOR_RELEASE_BINDING_AUTHORIZATION",
                                "WAIT_FOR_EXACT_RELEASE_BINDING_AUTHORIZATION", True,
                                "Exact license, proposed ledger row, and artifact hashes are sealed; no binding or publication has occurred.")
        return WorkItem(run_id, "RELEASE_BINDING_REQUIRED", "PREPARE_LICENSE_LEDGER_AND_HASH_SURFACE", False,
                        "Prepare all reversible release bindings; do not guess rights or ledger identity.")
    return WorkItem(run_id, "READY_FOR_EXACT_PUBLICATION_AUTHORIZATION", "WAIT_FOR_EXACT_AUTHORIZATION", True,
                    "Sealed release may proceed Zenodo then Git Canon; authorization must bind exact hashes.")

def inspect_open_run(path: Path, certificate_root: Path, comparator_authorized: bool) -> WorkItem:
    """Expose a sealed nightly package that has not entered finalized overlays."""
    run_id = path.name
    if certificate_clean(run_id, path, certificate_root):
        gate_path = path / "QUALITY_GATE.json"
        if gate_path.is_file():
            try:
                gate = read_json(gate_path)
            except (OSError, ValueError, json.JSONDecodeError):
                gate = {}
            if gate.get("quality_verdict") == "HOLD":
                failed = [
                    str(row.get("code"))
                    for row in gate.get("checks", [])
                    if isinstance(row, dict) and row.get("passed") is False and row.get("code")
                ]
                suffix = f" Failed checks: {', '.join(failed)}." if failed else ""
                return WorkItem(
                    run_id,
                    "PAPER_PACKAGE_REPAIR_REQUIRED",
                    "CREATE_VERSIONED_PRE_CURATOR_PAPER_CORRECTION",
                    False,
                    "The proof certificate is clean, but the nightly manuscript gate is on HOLD; "
                    "repair only a versioned paper overlay before curation." + suffix,
                )
        return WorkItem(run_id, "RECONCILIATION_REQUIRED", "CURATE_PROOF_RECONCILED_DRAFT", False,
                        "Open nightly package has a clean certificate and is ready for reversible paper reconciliation.")
    hold_path = certificate_root / run_id / "COMPARATOR_SUBMISSION_HOLD.json"
    if hold_path.is_file():
        try:
            hold = read_json(hold_path)
        except (OSError, ValueError, json.JSONDecodeError):
            hold = {}
        status = str(hold.get("status", ""))
        if "AUTHORIZATION" in status and "PAYLOAD" in status and not comparator_authorized:
            return WorkItem(run_id, "READY_FOR_COMPARATOR_TRANSPORT_AUTHORIZATION",
                            "WAIT_FOR_EXACT_COMPARATOR_PAYLOAD_DESTINATION_AUTHORIZATION", True,
                            "Frozen statement and candidate exist, but no proof payload may be transmitted without exact destination authorization.")
    if not comparator_authorized:
        return WorkItem(run_id, "READY_FOR_COMPARATOR_TRANSPORT_AUTHORIZATION",
                        "WAIT_FOR_EXACT_COMPARATOR_PAYLOAD_DESTINATION_AUTHORIZATION", True,
                        "Frozen proof inputs may not leave the workspace because the standing private-Comparator authorization is missing or invalid.")
    return WorkItem(run_id, "CERTIFICATE_REQUIRED", "CERTIFY_COMPARATOR_FIFO", False,
                    "Open nightly package lacks a clean certificate; the active standing authorization covers exact frozen transport to the private Comparator.")



def build_state(
    finalized_root: Path = FINALIZED_ROOT,
    certificate_root: Path = CERTIFICATE_ROOT,
    intake_path: Path = VIRIDISOS_INTAKE,
    submission_map_path: Path = SUBMISSION_MAP,
    nightly_packages_root: Path | None = None,
    release_candidates_root: Path | None = None,
    kernel_packages_root: Path | None = None,
    comparator_authorization_path: Path = COMPARATOR_AUTHORIZATION,
    verifier_backends_path: Path = VERIFIER_BACKENDS,
) -> dict[str, Any]:
    comparator_authorization = validate_authorization(
        comparator_authorization_path,
        verifier_backends_path,
    )
    comparator_authorized = comparator_authorization["status"] == "AUTHORIZED"
    ingested = published_runs(intake_path)
    public_hashes = published_source_hashes(submission_map_path)
    roots = sorted(
        (path for path in finalized_root.glob("Run-*") if path.is_dir()),
        key=run_number,
    ) if finalized_root.is_dir() else []
    if release_candidates_root is None:
        release_candidates_root = (
            RELEASE_CANDIDATES_ROOT
            if finalized_root == FINALIZED_ROOT
            else finalized_root.parent / "saturday_candidates"
        )
    if kernel_packages_root is None:
        kernel_packages_root = (
            VIRIDISOS_KERNEL_PACKAGES_ROOT
            if finalized_root == FINALIZED_ROOT
            else finalized_root.parent / "viridisos_kernel_packages"
        )
    items = [
        inspect_run(
            path, certificate_root, ingested, public_hashes, release_candidates_root,
            comparator_authorized, kernel_packages_root,
        )
        for path in roots
    ]
    if nightly_packages_root is None:
        nightly_packages_root = (
            NIGHTLY_PACKAGES_ROOT
            if finalized_root == FINALIZED_ROOT
            else finalized_root.parent / "nightly_packages"
        )
    known = {item.run_id for item in items}
    if nightly_packages_root.is_dir():
        for path in sorted((p for p in nightly_packages_root.glob("Run-*") if p.is_dir()), key=run_number):
            # A historical run can remain open even after newer runs have
            # entered finalized overlays. Numeric frontier filtering hid that
            # backlog, so identity membership is the only safe dedup rule.
            if path.name not in known:
                items.append(inspect_open_run(path, certificate_root, comparator_authorized))
    items.sort(key=lambda item: int(item.run_id.split("-")[1]))
    actionable = [item for item in items if item.state != "VIRIDISOS_TRACKED"]
    human = [item for item in actionable if item.human_gate]
    machine = [item for item in actionable if not item.human_gate]
    first = machine[0] if machine else (human[0] if human else None)
    submission_ready_states = {
        "READY_FOR_RELEASE_BINDING_AUTHORIZATION",
        "READY_FOR_EXACT_PUBLICATION_AUTHORIZATION",
    }
    submission_ready = [item for item in items if item.state in submission_ready_states]
    return {
        "schema_version": 1,
        "standard": "VRS-AUTONOMOUS-PIPELINE-STATE-1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scheduler_id": "viridis-nightly-science-generator",
        "autonomy": {
            "reversible_transitions": "AUTHORIZED",
            "scheduled_publication": False,
            "scheduled_production_deployment": False,
            "resume_after_exact_authorization": True,
        },
        "counts": {
            "total": len(items),
            "machine_actionable": len(machine),
            "human_gated": len(human),
            "viridisos_tracked": sum(item.state == "VIRIDISOS_TRACKED" for item in items),
            "viridisos_kernel_packages": sum(complete_kernel_package(item.run_id, kernel_packages_root, finalized_root / item.run_id) for item in items),
            "submission_ready_packages": len(submission_ready),
        },
        "submission_readiness_definition": (
            "All reversible science, review, reconciliation, routing, and package work is complete; "
            "only an exact irreversible release binding or publication transaction remains."
        ),
        "comparator_data_egress_authorization": comparator_authorization,
        "first_action": asdict(first) if first else None,
        "items": [asdict(item) for item in items],
        "external_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-receipt", action="store_true")
    parser.add_argument("--count-only", action="store_true")
    parser.add_argument("--output", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    state = build_state()
    if args.write_receipt:
        write_json_atomic(args.output, state)
    if args.count_only:
        print(f"SUBMISSION_READY_PACKAGES: {state['counts']['submission_ready_packages']}")
    else:
        print(json.dumps(state, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
