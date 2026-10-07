#!/usr/bin/env python3
"""Issue an immutable Viridis certificate from a frozen dual-kernel receipt."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from engine3_align_challenge import align_challenge
from job_observation_policy import assess_job_observation


class CertificateError(RuntimeError):
    pass


AUDIT_CHECKS = (
    "build_pass",
    "statement_freeze_pass",
    "proof_completeness_pass",
    "zero_sorry_textscan_pass",
    "forbidden_constructs_pass",
    "axiom_audit_pass",
    "nonvacuity_pass",
)

PERMITTED_AXIOMS = ["propext", "Quot.sound", "Classical.choice"]
COMPARATOR_CHECKS = (
    "comparator_accepted",
    "nanoda_kernel_accepted",
    "lean_kernel_accepted",
    "solution_ok_terminal",
    "candidate_forbidden_constructs_empty",
    "contract_declarations_present",
    "targeted_export_complete",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CertificateError(f"JSON root must be an object: {path}")
    return value


def bound_file(value: Any, label: str) -> tuple[Path, str]:
    if not isinstance(value, dict) or not isinstance(value.get("path"), str) or not isinstance(value.get("sha256"), str):
        raise CertificateError(f"missing {label} path/hash binding")
    path = Path(value["path"])
    if not path.is_file() or sha256_file(path) != value["sha256"]:
        raise CertificateError(f"{label} byte binding failed")
    return path, value["sha256"]


def validate_comparator_witness_evidence(request: dict[str, Any], cloud: dict[str, Any]) -> bool:
    """Check named witness exports against the hash-bound raw provider response.

    This checks formal witness presence, not scientific relevance to a model;
    hypothesis correspondence remains an independent scientific review gate.
    """
    witnesses = request.get("nonvacuity_obligations")
    if (
        not isinstance(witnesses, list)
        or not witnesses
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*", value) is None
            for value in witnesses
        )
        or len(set(witnesses)) != len(witnesses)
    ):
        raise CertificateError("nonvacuity_obligations must be a nonempty unique list of Lean declaration names")
    if cloud.get("contract", {}).get("named_nonvacuity_obligations") != witnesses:
        raise CertificateError("cloud receipt named nonvacuity contract does not match the request")
    response = cloud.get("provider_response")
    if not isinstance(response, dict):
        raise CertificateError("Comparator receipt is missing its raw provider response")
    digest = hashlib.sha256(
        (json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()
    if cloud.get("provider_response_sha256") != digest:
        raise CertificateError("Comparator provider response byte binding failed")
    markers = (
        "Nanoda kernel accepts the solution",
        "Lean default kernel accepts the solution",
        "Your solution is okay!",
    )
    output = response.get("output")
    if (
        response.get("type") != "verification-ok"
        or response.get("project") != "viridis-lean-4.28"
        or not isinstance(output, str)
        or not all(marker in output for marker in markers)
    ):
        raise CertificateError("raw Comparator response does not establish dual-kernel acceptance")
    expected = request.get("expected_theorem_names")
    if not isinstance(expected, list) or not expected or not all(isinstance(v, str) and v for v in expected):
        raise CertificateError("request expected theorem contract is invalid")
    exports = response.get("theoremNames")
    complete = isinstance(exports, list) and all(
        any(
            isinstance(actual, str) and (actual == name or actual.endswith("." + name))
            for actual in exports
        )
        for name in expected + witnesses
    )
    if not complete:
        raise CertificateError("raw Comparator response is missing a required theorem or nonvacuity witness export")
    return complete


def issue(
    *,
    request_path: Path,
    cloud_receipt_path: Path,
    output_path: Path,
    audit_path: Path | None = None,
    require_premise_declaration: bool = False,
) -> dict[str, Any]:
    request_path = request_path.resolve()
    cloud_receipt_path = cloud_receipt_path.resolve()
    output_path = output_path.resolve()
    if audit_path is not None:
        audit_path = audit_path.resolve()
    if output_path.exists():
        raise CertificateError(f"immutable certificate already exists: {output_path}")
    request = read_json(request_path)
    cloud = read_json(cloud_receipt_path)
    run_match = re.fullmatch(r"Run-(\d+)(?:[_-][A-Za-z0-9][A-Za-z0-9._-]*)?", str(request.get("source_run", "")))
    if run_match is None or request.get("request_kind", "LEAN_PROOF") != "LEAN_PROOF":
        raise CertificateError("certificate requires a numbered frozen LEAN_PROOF request")
    request_hash = sha256_file(request_path)
    cloud_standard = cloud.get("standard")
    if cloud.get("status") != "VERIFIED" or cloud_standard not in {
        "VRS-COMPARATOR-DUAL-KERNEL-1",
        "VRS-INDEPENDENT-CLOUD-LEAN-1",
    }:
        raise CertificateError("independent cloud Lean verification did not pass")
    cloud_request, cloud_request_hash = bound_file(cloud.get("request"), "cloud request")
    if cloud_request.resolve() != request_path.resolve() or cloud_request_hash != request_hash:
        raise CertificateError("cloud receipt is bound to a different request")
    formal_path, formal_hash = bound_file(cloud.get("formal_statement"), "formal statement")
    candidate_path, candidate_hash = bound_file(cloud.get("candidate"), "candidate proof")
    if cloud.get("contract", {}).get("candidate_id") != request.get("candidate_id"):
        raise CertificateError("cloud verification candidate does not match")
    if cloud.get("contract", {}).get("expected_theorem_names") != request.get("expected_theorem_names"):
        raise CertificateError("cloud verification theorem contract does not match")
    legacy_audit: dict[str, Any] | None = None
    nonvacuity_verified = False
    runtime_observation = None
    if cloud_standard == "VRS-COMPARATOR-DUAL-KERNEL-1":
        if cloud.get("provider") != "VIRIDIS_COMPARATOR_CLOUD":
            raise CertificateError("Comparator receipt has the wrong provider identity")
        if cloud.get("project") != "viridis-lean-4.28":
            raise CertificateError("Comparator receipt has the wrong pinned project")
        if cloud.get("local_lean_execution") is not False:
            raise CertificateError("Comparator receipt does not preserve the no-local-Lean invariant")
        contract_axioms = cloud.get("contract", {}).get("permitted_axioms")
        if contract_axioms != PERMITTED_AXIOMS:
            raise CertificateError("Comparator receipt has the wrong permitted axiom set")
        failed = [name for name in COMPARATOR_CHECKS if cloud.get("checks", {}).get(name) is not True]
        if failed:
            raise CertificateError("Comparator dual-kernel receipt is not clean: " + ", ".join(failed))
        nonvacuity_verified = validate_comparator_witness_evidence(request, cloud)
        runtime_observation = assess_job_observation(cloud["provider_response"], request, formal_hash, candidate_hash)
        if runtime_observation["status"] == "INVALID_OBSERVATION":
            raise CertificateError("runtime observations failed independent consumer checks: " + ", ".join(runtime_observation["failures"]))
        alignment = request.get("statement_alignment")
        if alignment is not None:
            if not isinstance(alignment, dict) or alignment.get("standard") != "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1":
                raise CertificateError("request has an unsupported statement alignment contract")
            if cloud.get("checks", {}).get("sealed_statement_signature_alignment") is not True:
                raise CertificateError("Comparator receipt did not verify sealed statement alignment")
            cloud_alignment = cloud.get("statement_alignment")
            if not isinstance(cloud_alignment, dict):
                raise CertificateError("Comparator receipt is missing statement alignment bindings")
            for key, label in (("sealed_statement", "sealed statement"), ("receipt", "statement alignment receipt")):
                cloud_path, cloud_hash = bound_file(cloud_alignment.get(key), label)
                request_value = alignment.get(key)
                if not isinstance(request_value, dict):
                    raise CertificateError(f"request is missing {label} binding")
                filename = request_value.get("filename")
                digest = request_value.get("sha256")
                expected_path = request_path.parent / str(filename)
                if cloud_path.resolve() != expected_path.resolve() or cloud_hash != digest:
                    raise CertificateError(f"{label} request/cloud binding mismatch")
        # Recompute the dependency/context check at issuance too. A locally
        # forged PASS alignment receipt cannot turn changed definitions into
        # the sealed scientific statement, even with a green raw proof result.
        sealed_source = (
            Path(cloud["statement_alignment"]["sealed_statement"]["path"]).read_text(encoding="utf-8")
            if alignment is not None else formal_path.read_text(encoding="utf-8")
        )
        targets = list(dict.fromkeys(request["expected_theorem_names"] + request["nonvacuity_obligations"]))
        try:
            recomputed_challenge, _ = align_challenge(
                sealed_source, candidate_path.read_text(encoding="utf-8"), targets
            )
        except ValueError as exc:
            raise CertificateError(f"independent frozen-context comparison failed: {exc}") from exc
        if alignment is not None and recomputed_challenge != formal_path.read_text(encoding="utf-8"):
            raise CertificateError("aligned challenge differs from independently recomputed frozen context")
    else:
        if audit_path is None:
            raise CertificateError("legacy AXLE verification requires its Aristotle audit")
        legacy_audit = read_json(audit_path)
        if legacy_audit.get("candidate_id") != request.get("candidate_id"):
            raise CertificateError("Aristotle audit candidate does not match the frozen request")
        if legacy_audit.get("request_sha256") != request_hash:
            raise CertificateError("Aristotle audit request hash does not match")
        failed = [name for name in AUDIT_CHECKS if legacy_audit.get(name) is not True]
        if failed or legacy_audit.get("failed_checks"):
            raise CertificateError(
                "Aristotle audit is not clean: "
                + ", ".join(failed or legacy_audit.get("failed_checks", []))
            )
        if legacy_audit.get("evidence", {}).get("local_lean_execution") is not False:
            raise CertificateError("Aristotle audit does not preserve the no-local-Lean invariant")
        nonvacuity_verified = legacy_audit.get("nonvacuity_pass") is True
    required_input_hashes = {
        name: digest for name, digest in request.get("input_sha256", {}).items()
        if name in {"SEALED_paper.pdf", "SEALED_paper.tex", "SEALED_CLAIM_INVENTORY.json", "SEALED_RUN_MANIFEST.json"}
    }
    required_sealed_names = {
        "SEALED_paper.pdf", "SEALED_paper.tex", "SEALED_CLAIM_INVENTORY.json", "SEALED_RUN_MANIFEST.json"
    }
    if set(required_input_hashes) != required_sealed_names:
        missing = sorted(required_sealed_names - set(required_input_hashes))
        raise CertificateError("request must bind the complete sealed paper input set; missing: " + ", ".join(missing))
    required_inputs: dict[str, dict[str, str]] = {}
    for name, expected_hash in required_input_hashes.items():
        source = request_path.parent / name
        if not source.is_file() or sha256_file(source) != expected_hash:
            raise CertificateError(f"sealed paper input byte binding failed: {name}")
        required_inputs[name] = {"path": str(source), "sha256": expected_hash}
    premise_declaration = None
    if require_premise_declaration:
        # Approved INV-9 intake only; all receipt, kernel, axiom, alignment and
        # byte-binding checks above remain unchanged. Historical default output
        # is unchanged. New nightly callers explicitly enable this cutover gate.
        paths = [Path(__file__).parent / "verification_coverage_gates" / "premise_declaration.py",
                 Path(__file__).parent.parent / "00_lab_infrastructure" / "gates" / "premise_declaration.py"]
        modules = [path for path in paths if path.is_file()]
        if len(modules) != 1:
            raise CertificateError("PREMISE_INTAKE_ERROR: exact premise declaration module missing or ambiguous")
        try:
            spec = importlib.util.spec_from_file_location("_issuer_premise_declaration", modules[0])
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            premise_declaration = module.validate_envelope(request_path, formal_path, candidate_path, required=True)
        except Exception as exc:
            raise CertificateError("PREMISE_INTAKE_ERROR: " + type(exc).__name__ + ": " + str(exc)) from exc
        if premise_declaration.get("status") != "PASS":
            raise CertificateError("INV-9 HOLD: " + "; ".join(premise_declaration.get("reasons", [])))
    bindings: dict[str, Any] = {
        "request": {"path": str(request_path), "sha256": request_hash},
        "independent_cloud_receipt": {
            "path": str(cloud_receipt_path),
            "sha256": sha256_file(cloud_receipt_path),
        },
        "formal_statement": cloud.get("formal_statement"),
        "candidate_proof": cloud.get("candidate"),
        "sealed_paper_inputs": required_inputs,
    }
    if request.get("statement_alignment") is not None:
        bindings["sealed_statement_contract"] = cloud.get("statement_alignment", {}).get("sealed_statement")
        bindings["statement_alignment_receipt"] = cloud.get("statement_alignment", {}).get("receipt")
    if legacy_audit is not None and audit_path is not None:
        bindings["legacy_aristotle_audit"] = {
            "path": str(audit_path),
            "sha256": sha256_file(audit_path),
        }
        bindings["legacy_aristotle_output_tree_sha256"] = legacy_audit.get("output_tree_sha256")

    gates = {
        "frozen_statement_and_candidate_hash_bound": True,
        "independent_cloud_kernel_verification": True,
        "zero_sorries_or_admits": True,
        "allowed_axioms_only": True,
        "nonvacuity_witnesses": nonvacuity_verified,
        "local_lean_execution": False,
    }
    if cloud_standard == "VRS-COMPARATOR-DUAL-KERNEL-1":
        gates.update(
            {
                "comparator_statement_identity": True,
                "comparator_lean_kernel": True,
                "comparator_nanoda_kernel": True,
                "aristotle_required": False,
            }
        )
        if request.get("statement_alignment") is not None:
            gates["sealed_statement_signature_alignment"] = True
    else:
        gates["legacy_aristotle_exact_contract_audit"] = True

    certificate = {
        "schema_version": "1.0",
        "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
        "status": "LEAN_ZERO_SORRY_CERTIFIED",
        "run_id": f"Run-{int(run_match.group(1)):03d}",
        "candidate_id": request.get("candidate_id"),
        "issued_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "verification_standard": cloud_standard,
        "bindings": bindings,
        "gates": gates,
        "scope": "formal Lean claims only; novelty, empirical validity, rights, publication, deployment, and outcomes remain separate gates",
    }
    if runtime_observation is not None:
        certificate["runtime_observation_assessment"] = runtime_observation
    if premise_declaration is not None:
        certificate["foundation_basis"] = premise_declaration["foundation_basis"]
        certificate["premise_declaration"] = premise_declaration
        certificate["gates"]["premise_declaration"] = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return certificate


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--cloud-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--require-premise-declaration", action="store_true",
                        help="INV-9 cutover: require sealed foundation basis for new nightly runs")
    args = parser.parse_args()
    try:
        result = issue(
            request_path=args.request,
            audit_path=args.audit,
            cloud_receipt_path=args.cloud_receipt,
            output_path=args.output,
            require_premise_declaration=args.require_premise_declaration,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, CertificateError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
