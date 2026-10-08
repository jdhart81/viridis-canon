#!/usr/bin/env python3
"""Build the fail-closed ViridisOS disposition included with a release package.

Scientific eligibility does not imply that a paper is an operational decision
kernel.  This writer records that distinction before Saturday assembly.  A
methods paper receives a durable ``NO_RUNTIME_KERNEL`` disposition.  A genuine
runtime candidate must provide a complete, hash-bound adapter specification,
engine, tests, and fixtures before it can become
``KERNEL_IMPLEMENTATION_READY``.

The writer is local and deterministic.  It never activates a module, grants
certificate authority, deploys ViridisOS, or mutates an external surface.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any


HERE = Path(__file__).resolve().parent
FINALIZED_ROOT = HERE / "finalized_runs"
OUTPUT_ROOT = HERE / "viridisos_kernel_packages"
STANDARD = "VRS-VIRIDISOS-KERNEL-PACKAGE-1"
SPEC_STANDARD = "VRS-VIRIDISOS-KERNEL-SPEC-1"
ADMISSION_STANDARD = "VRS-VIRIDISOS-KERNEL-ADMISSION-1"
RUN_RE = re.compile(r"(?:Run-)?(\d{1,})", re.IGNORECASE)
NO_RUNTIME_DISPOSITIONS = {
    "BACKLOG_NO_WRAPPER",
    "BACKLOG_NO_WRAPPER_METHODS_NOTE",
    "NO_RUNTIME_KERNEL",
}
PUBLICATION_RANKS = {"FLAGSHIP", "SOLID", "MINOR", "MERGE", "RETIRE", "UNREVIEWED"}
KERNEL_ROLES = {
    "NOVEL_SCIENCE_CANDIDATE",
    "KNOWN_METHOD_FORMALIZATION",
    "MODEL_ASSUMPTION_KERNEL",
    "INTERNAL_VALIDATION_ONLY",
    "EMPIRICAL_VALIDATION_REQUIRED",
    "NO_RUNTIME_KERNEL",
}
ADMITTABLE_KERNEL_ROLES = {
    "NOVEL_SCIENCE_CANDIDATE",
    "KNOWN_METHOD_FORMALIZATION",
    "MODEL_ASSUMPTION_KERNEL",
}
DECISION_FAMILIES = {
    "restoration-design",
    "continuity-monitoring",
    "governance-integrity",
    "natural-capital-risk",
}
CERTIFICATE_GATES = {
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


class KernelPackageError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise KernelPackageError(f"{path}: missing or invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise KernelPackageError(f"{path}: expected a JSON object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_run_id(value: str) -> str:
    match = RUN_RE.fullmatch(value)
    if match is None:
        raise KernelPackageError(f"invalid run identity: {value!r}")
    return f"Run-{int(match.group(1)):03d}"


def relative_artifact(root: Path, value: Any, field: str) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise KernelPackageError(f"{field} must be a non-empty relative path")
    path = root / value
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise KernelPackageError(f"{field} escapes the finalized package") from exc
    if not path.is_file() or path.is_symlink():
        raise KernelPackageError(f"{field} does not name a regular package file: {value}")
    return path


def validate_digest(path: Path, expected: Any, field: str) -> str:
    if not isinstance(expected, str) or re.fullmatch(r"[0-9a-f]{64}", expected) is None:
        raise KernelPackageError(f"{field} must be a lowercase SHA-256 digest")
    actual = sha256(path)
    if actual != expected:
        raise KernelPackageError(f"{field} does not match {path.name}")
    return actual


def validate_certificate(run_id: str, root: Path, expected_sha256: Any, field: str) -> str:
    """Shared exact-identity Comparator certificate gate for current evidence."""
    certificate_path = root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    if certificate_path.is_symlink() or not certificate_path.is_file():
        raise KernelPackageError(f"{run_id}: Lean zero-sorry certificate is missing")
    validate_digest(certificate_path, expected_sha256, field)
    certificate = read_json(certificate_path)
    certificate_gates = certificate.get("gates")
    if (
        certificate.get("run_id") != run_id
        or certificate.get("status") != "LEAN_ZERO_SORRY_CERTIFIED"
        or certificate.get("verification_standard") != "VRS-COMPARATOR-DUAL-KERNEL-1"
        or not isinstance(certificate_gates, dict)
        or any(certificate_gates.get(field) is not True for field in CERTIFICATE_GATES)
    ):
        raise KernelPackageError("kernel admission requires a clean exact-run Comparator dual-kernel certificate")
    if certificate_gates.get("local_lean_execution") is not False:
        raise KernelPackageError("local Lean execution is not the Viridis production certificate authority")

    return sha256(certificate_path)


def validate_declared_scientific_bindings(
    root: Path, finalized: dict[str, Any], review: dict[str, Any],
) -> None:
    """Preserve legacy review formats while checking every hash they declare."""
    from verification_state_metadata import reviewed_text_contradictions
    manifest = read_json(root / "PAPER_PACKAGE_MANIFEST.json")
    source_name = manifest.get("artifacts", {}).get("paper_source")
    if review.get("verdict") == "pass" and source_name:
        source = relative_artifact(root, source_name, "artifacts.paper_source")
        if reviewed_text_contradictions(source.read_text(encoding="utf-8")):
            raise KernelPackageError(
                "HOLD_REVIEW_STATUS_CONTRADICTION: finalized manuscript still says "
                "its independent review is pending; preserve the sealed package and "
                "prepare a corrected successor with a later independent review"
            )
    for label, bindings in (
        ("finalized.artifact_sha256", finalized.get("artifact_sha256")),
        ("review.artifacts", review.get("artifacts")),
        ("review.reviewed_evidence_sha256", review.get("reviewed_evidence_sha256")),
    ):
        if bindings is None:
            continue
        if not isinstance(bindings, dict):
            raise KernelPackageError(f"{label} must be a hash map")
        for name, expected in bindings.items():
            artifact = relative_artifact(root, name, f"{label}.{name}")
            validate_digest(artifact, expected, f"{label}.{name}")


def validate_admission_review(
    run_id: str,
    root: Path,
    review: dict[str, Any],
    required: dict[str, Path],
    *,
    no_runtime: bool,
) -> dict[str, Any]:
    if (
        review.get("schema_version") != 1
        or review.get("standard") != ADMISSION_STANDARD
        or review.get("run_id") != run_id
    ):
        raise KernelPackageError("kernel admission review standard, schema, or run identity is invalid")
    reviewer = review.get("reviewer")
    if not isinstance(reviewer, dict):
        raise KernelPackageError("kernel admission review requires reviewer attribution")
    for field in ("system", "model", "review_invocation_id", "draft_invocation_id"):
        if not isinstance(reviewer.get(field), str) or not reviewer[field].strip():
            raise KernelPackageError(f"reviewer.{field} is required")
    if (
        reviewer.get("independent_from_draft_invocation") is not True
        or reviewer["review_invocation_id"] == reviewer["draft_invocation_id"]
    ):
        raise KernelPackageError("kernel admission review must come from an independent later invocation")
    if review.get("g7_verdict") != "PASS" or review.get("complete_pdf_review") is not True:
        raise KernelPackageError("kernel admission requires G7 PASS and complete PDF review")

    bindings = review.get("reviewed_artifact_sha256")
    if not isinstance(bindings, dict):
        raise KernelPackageError("reviewed_artifact_sha256 is required")
    for field, path in required.items():
        validate_digest(path, bindings.get(field), f"reviewed_artifact_sha256.{field}")

    if int(run_id.removeprefix("Run-")) >= 151:
        finalized = read_json(required["finalized_package"])
        def timestamp(value):
            try:
                result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if result.tzinfo is None: raise ValueError("timezone required")
                return result
            except (AttributeError, TypeError, ValueError) as exc:
                raise KernelPackageError("admission chronology requires timezone-aware timestamps") from exc
        reviewed = timestamp(review.get("reviewed_at_utc"))
        sealed = timestamp(finalized.get("finalized_at_utc"))
        if not sealed < reviewed <= dt.datetime.now(dt.timezone.utc):
            raise KernelPackageError("admission review must be later than the exact finalized package, and not in the future")

    certificate_sha256 = validate_certificate(
        run_id, root, bindings.get("lean_zero_sorry_certificate"),
        "reviewed_artifact_sha256.lean_zero_sorry_certificate",
    )

    publication_rank = review.get("publication_rank")
    science_score = review.get("science_score")
    kernel_role = review.get("kernel_role")
    if publication_rank not in PUBLICATION_RANKS:
        raise KernelPackageError("publication_rank is invalid")
    if not isinstance(science_score, int) or isinstance(science_score, bool) or not 1 <= science_score <= 10:
        raise KernelPackageError("science_score must be an integer from 1 through 10")
    if kernel_role not in KERNEL_ROLES:
        raise KernelPackageError("kernel_role is invalid")
    claims = review.get("claim_separation")
    if not isinstance(claims, dict) or any(
        not isinstance(claims.get(field), list)
        for field in ("formally_proved", "numeric_or_code", "empirical", "assumed", "cited", "conjectured_or_deferred")
    ):
        raise KernelPackageError("claim_separation must classify every evidence channel")
    probes = review.get("scientific_probes")
    if not isinstance(probes, dict) or any(
        probes.get(field) not in {"PASS", "CLASSIFIED", "NOT_APPLICABLE"}
        for field in ("triviality", "nonvacuity", "hypothesis_rearrangement", "numeric_consistency", "prior_art", "metadata_hygiene")
    ):
        raise KernelPackageError("all scientific probes must be recorded and resolved")

    runtime_verdict = review.get("runtime_verdict")
    if kernel_role == "EMPIRICAL_VALIDATION_REQUIRED":
        raise KernelPackageError("unresolved empirical dependency must remain HOLD, not NO_RUNTIME_KERNEL")
    if no_runtime:
        if runtime_verdict != "NO_RUNTIME_KERNEL":
            raise KernelPackageError("product no-runtime route requires a matching admission verdict")
        if not isinstance(review.get("no_runtime_reason"), str) or not review["no_runtime_reason"].strip():
            raise KernelPackageError("NO_RUNTIME_KERNEL requires a reviewed reason")
    else:
        if runtime_verdict != "ADMIT_CANDIDATE" or kernel_role not in ADMITTABLE_KERNEL_ROLES:
            raise KernelPackageError("runtime candidate lacks an admissible reviewed kernel role")
        if review.get("decision_family_id") not in DECISION_FAMILIES:
            raise KernelPackageError("runtime candidate requires a known Conservation decision family")
        if review.get("empirical_validation_status") not in {"PASS", "NOT_APPLICABLE"}:
            raise KernelPackageError("runtime candidate has unresolved empirical validation")
        prior_art = review.get("nearest_prior_results")
        if not isinstance(prior_art, list) or not prior_art or any(not isinstance(item, str) or not item.strip() for item in prior_art):
            raise KernelPackageError("runtime candidate requires at least one named nearest prior result")
        for field in ("scope", "refusal_boundary"):
            if not isinstance(review.get(field), str) or not review[field].strip():
                raise KernelPackageError(f"runtime candidate requires {field}")
    return {
        "reviewer": reviewer,
        "g7_verdict": review["g7_verdict"],
        "complete_pdf_review": True,
        "publication_rank": publication_rank,
        "science_score": science_score,
        "kernel_role": kernel_role,
        "runtime_verdict": runtime_verdict,
        "decision_family_id": review.get("decision_family_id"),
        "empirical_validation_status": review.get("empirical_validation_status"),
        "claim_separation": claims,
        "scientific_probes": probes,
        "scope": review.get("scope"),
        "refusal_boundary": review.get("refusal_boundary"),
        "lean_zero_sorry_certificate_sha256": certificate_sha256,
    }


def validate_spec(run_id: str, root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    if spec.get("standard") != SPEC_STANDARD or spec.get("run_id") != run_id:
        raise KernelPackageError("kernel spec standard or run identity is invalid")
    module = spec.get("module")
    backing = spec.get("backing")
    engine = spec.get("engine")
    if not all(isinstance(value, dict) for value in (module, backing, engine)):
        raise KernelPackageError("kernel spec requires module, backing, and engine objects")
    assert isinstance(module, dict) and isinstance(backing, dict) and isinstance(engine, dict)
    for field in ("id", "name", "line", "version"):
        if not isinstance(module.get(field), str) or not module[field].strip():
            raise KernelPackageError(f"module.{field} is required")
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(module["id"])) is None:
        raise KernelPackageError("module.id must be a lowercase kebab-case identifier")
    for field in ("lean_module", "verification_receipt_id"):
        if not isinstance(backing.get(field), str) or not backing[field].strip():
            raise KernelPackageError(f"backing.{field} is required")
    schema = spec.get("input_schema")
    if not isinstance(schema, dict) or schema.get("type") != "object" or schema.get("additionalProperties") is not False:
        raise KernelPackageError("input_schema must be a closed JSON object schema")
    if not isinstance(spec.get("units"), dict) or not isinstance(spec.get("scope"), str) or not spec["scope"].strip():
        raise KernelPackageError("units and a non-empty scope are required")

    engine_path = relative_artifact(root, engine.get("path"), "engine.path")
    engine_hash = validate_digest(engine_path, engine.get("sha256"), "engine.sha256")
    if not isinstance(engine.get("entrypoint"), str) or not engine["entrypoint"].strip():
        raise KernelPackageError("engine.entrypoint is required")

    tests = spec.get("tests")
    fixtures = spec.get("fixtures")
    if not isinstance(tests, list) or not tests or not isinstance(fixtures, list) or not fixtures:
        raise KernelPackageError("at least one test and one input/output fixture are required")
    bound_tests = []
    for index, row in enumerate(tests):
        if not isinstance(row, dict):
            raise KernelPackageError(f"tests[{index}] must be an object")
        path = relative_artifact(root, row.get("path"), f"tests[{index}].path")
        bound_tests.append({"path": str(path.relative_to(root)), "sha256": validate_digest(path, row.get("sha256"), f"tests[{index}].sha256")})
    bound_fixtures = []
    for index, row in enumerate(fixtures):
        if not isinstance(row, dict):
            raise KernelPackageError(f"fixtures[{index}] must be an object")
        input_path = relative_artifact(root, row.get("input"), f"fixtures[{index}].input")
        expected_path = relative_artifact(root, row.get("expected"), f"fixtures[{index}].expected")
        bound_fixtures.append({
            "input": str(input_path.relative_to(root)),
            "input_sha256": validate_digest(input_path, row.get("input_sha256"), f"fixtures[{index}].input_sha256"),
            "expected": str(expected_path.relative_to(root)),
            "expected_sha256": validate_digest(expected_path, row.get("expected_sha256"), f"fixtures[{index}].expected_sha256"),
        })
    evidence = {}
    for label, standard in (("execution_receipt", "VRS-KERNEL-EXECUTION-1"),
                            ("correspondence_review", "VRS-KERNEL-CORRESPONDENCE-1")):
        binding = spec.get(label)
        if not isinstance(binding, dict):
            raise KernelPackageError(f"{label} exact-engine evidence is required")
        evidence_path = relative_artifact(root, binding.get("path"), label + ".path")
        evidence_hash = validate_digest(evidence_path, binding.get("sha256"), label + ".sha256")
        record = read_json(evidence_path)
        if (record.get("standard") != standard or record.get("run_id") != run_id
            or record.get("status") != "PASS" or record.get("engine_sha256") != engine_hash
            or record.get("module_id") != module["id"] or record.get("module_version") != module["version"]):
            raise KernelPackageError(f"{label} identity, version, engine binding, or verdict is invalid")
        if label == "execution_receipt":
            if (record.get("tests") != bound_tests or record.get("fixtures") != bound_fixtures
                or record.get("exit_code") != 0 or type(record.get("exit_code")) is not int
                or not isinstance(record.get("runtime"), str) or not record["runtime"].strip()
                or not isinstance(record.get("command"), list) or not record["command"]
                or not all(isinstance(x,str) and x for x in record["command"])):
                raise KernelPackageError("execution receipt must bind the passing exact-engine test and fixture execution")
            log = relative_artifact(root, record.get("output_path"), "execution.output_path")
            validate_digest(log, record.get("output_sha256"), "execution.output_sha256")
            evidence[label] = {"path": str(evidence_path.relative_to(root)), "sha256": evidence_hash,
                               "output_path": str(log.relative_to(root)), "output_sha256": sha256(log)}
        else:
            if (record.get("backing") != backing or not isinstance(record.get("reviewer"), dict)
                or any(not isinstance(record["reviewer"].get(key),str) or not record["reviewer"][key].strip()
                       for key in ("system", "model", "review_invocation_id", "implementation_invocation_id"))
                or record["reviewer"]["review_invocation_id"] == record["reviewer"]["implementation_invocation_id"]
                or record.get("execution_receipt_sha256") != evidence["execution_receipt"]["sha256"]
                or not isinstance(record.get("limitations"), list) or not record["limitations"]
                or any(not isinstance(record.get(key), str) or not record[key].strip()
                       for key in ("formal_to_runtime_mapping", "numerical_error_policy", "units_and_domain_review"))):
                raise KernelPackageError("correspondence review must separately bind model, execution, numerical policy, units, and limitations")
            evidence[label] = {"path": str(evidence_path.relative_to(root)), "sha256": evidence_hash}
    return {
        **evidence,
        "evidence_limit": "Receipts record attributed engineering evidence; they are not a proof of executable correctness or empirical validity.",
        "module": module,
        "backing": backing,
        "input_schema": schema,
        "units": spec["units"],
        "scope": spec["scope"],
        "engine": {"path": str(engine_path.relative_to(root)), "sha256": engine_hash, "entrypoint": engine["entrypoint"]},
        "tests": bound_tests,
        "fixtures": bound_fixtures,
    }


def build_kernel_package(
    run_value: str,
    *,
    finalized_root: Path = FINALIZED_ROOT,
    output_root: Path = OUTPUT_ROOT,
    validate_only: bool = False,
) -> dict[str, Any]:
    """Rebuild from current evidence; validation-only compares without writing."""
    run_id = canonical_run_id(run_value)
    run_number = int(run_id.removeprefix("Run-"))
    root = finalized_root / run_id
    # Historical certificate success cannot override a later independent paper counterexample.
    # Isolated fixture roots have their own explicit advisory registry when supplied.
    advisory_root = finalized_root.parent
    if finalized_root.resolve() == FINALIZED_ROOT.resolve() or (advisory_root / "SCIENTIFIC_ADVISORIES.json").exists():
        from scientific_advisories import check_scientific_advisory, ScientificHoldError
        try:
            check_scientific_advisory(run_id, pipeline_root=advisory_root)
        except ScientificHoldError as error:
            raise KernelPackageError(str(error)) from error
    required = {
        "finalized_package": root / "FINALIZED_PACKAGE.json",
        "independent_review": root / "POST_ARISTOTLE_REVIEW.json",
        "product_route": root / "CANON_PRODUCT_ROUTE.json",
        "paper_manifest": root / "PAPER_PACKAGE_MANIFEST.json",
    }
    admission_path = root / "KERNEL_ADMISSION_REVIEW.json"
    if run_number >= 151 or admission_path.is_file():
        required["kernel_admission_review"] = admission_path
    for field, path in required.items():
        if path.is_symlink():
            raise KernelPackageError(f"{run_id}: {field} must not be a symlink")
        if not path.is_file():
            raise KernelPackageError(f"{run_id}: {field} is missing")
    finalized = read_json(required["finalized_package"])
    review = read_json(required["independent_review"])
    route = read_json(required["product_route"])
    manifest = read_json(required["paper_manifest"])
    if finalized.get("status") != "FINALIZED" or review.get("verdict") != "pass":
        raise KernelPackageError(f"{run_id}: finalized scientific gate has not passed")
    validate_declared_scientific_bindings(root, finalized, review)
    if not admission_path.is_file():
        # Existing pre-admission-era packages keep their immutable receipt format.
        # Revalidate any Comparator evidence already declared by that format.
        formal = manifest.get("formal_verification", {})
        binding = formal.get("certificate", {}) if isinstance(formal, dict) else {}
        certificate_path = root / "LEAN_ZERO_SORRY_CERTIFICATE.json"
        if certificate_path.exists() or binding:
            if not isinstance(binding, dict) or binding.get("path") != certificate_path.name:
                raise KernelPackageError("legacy Comparator certificate requires its existing manifest hash binding")
            validate_certificate(run_id, root, binding.get("sha256"), "formal_verification.certificate.sha256")

    disposition = str(route.get("product_disposition") or "")
    wrapper_candidate = route.get("wrapper_candidate")
    # Publication merit / Canon candidacy do not determine runtime utility.
    # A missing wrapper is unfinished classification, not evidence of no utility.
    no_runtime = (
        disposition in NO_RUNTIME_DISPOSITIONS
        or disposition.startswith("BACKLOG_NO_WRAPPER")
    )
    if no_runtime:
        if wrapper_candidate:
            raise KernelPackageError("explicit no-runtime route conflicts with a wrapper candidate")
        if not isinstance(route.get("product_reason"), str) or not route["product_reason"].strip():
            raise KernelPackageError("explicit no-runtime route requires a documented product reason")
    elif not isinstance(wrapper_candidate, dict) or not wrapper_candidate:
        raise KernelPackageError("runtime role is unresolved; missing wrapper requires review, not NO_RUNTIME_KERNEL")
    admission = None
    if admission_path.is_file():
        admission = validate_admission_review(
            run_id,
            root,
            read_json(admission_path),
            {field: path for field, path in required.items() if field != "kernel_admission_review"},
            no_runtime=no_runtime,
        )
    source_sha256 = {name: sha256(path) for name, path in required.items()}
    if no_runtime:
        receipt: dict[str, Any] = {
            "schema_version": 1,
            "standard": STANDARD,
            "run_id": run_id,
            "status": "NO_RUNTIME_KERNEL",
            "eligible_for_runtime_module": False,
            "product_disposition": disposition or "BACKLOG_NO_WRAPPER",
            "reason": str(route.get("product_reason") or "The reviewed result has no justified operational decision wrapper."),
            "source_sha256": source_sha256,
            "authority": {
                "automatic_module_activation": False,
                "automatic_certification_authority": False,
                "production_deployment_authorized": False,
            },
            "external_mutation": False,
        }
        if admission is not None:
            receipt["admission_review"] = admission
    else:
        spec_path = root / "VIRIDISOS_KERNEL_SPEC.json"
        if not spec_path.is_file():
            raise KernelPackageError(f"{run_id}: wrapper candidate lacks VIRIDISOS_KERNEL_SPEC.json")
        implementation = validate_spec(run_id, root, read_json(spec_path))
        receipt = {
            "schema_version": 1,
            "standard": STANDARD,
            "run_id": run_id,
            "status": "KERNEL_IMPLEMENTATION_READY",
            "eligible_for_runtime_module": True,
            "product_disposition": disposition,
            "implementation": implementation,
            "source_sha256": {**source_sha256, "kernel_spec": sha256(spec_path)},
            "authority": {
                "automatic_module_activation": False,
                "automatic_certification_authority": False,
                "production_deployment_authorized": False,
            },
            "external_mutation": False,
        }
        if admission is not None:
            receipt["admission_review"] = admission
    destination = output_root / run_id / "VIRIDISOS_KERNEL_PACKAGE.json"
    if destination.is_symlink():
        raise KernelPackageError(f"{run_id}: existing kernel package must not be a symlink")
    if destination.is_file():
        existing = read_json(destination)
        if existing != receipt:
            raise KernelPackageError(f"{run_id}: existing kernel package differs; immutable overwrite refused")
        return receipt
    if validate_only:
        raise KernelPackageError(f"{run_id}: existing kernel package is missing; validation-only never creates receipts")
    write_json_atomic(destination, receipt)
    return receipt


def validate_existing_kernel_package(
    run_value: str,
    *,
    finalized_root: Path = FINALIZED_ROOT,
    output_root: Path = OUTPUT_ROOT,
) -> dict[str, Any]:
    """Validate current evidence and exact immutable receipt equality, read-only."""
    return build_kernel_package(
        run_value, finalized_root=finalized_root, output_root=output_root,
        validate_only=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--finalized-root", type=Path, default=FINALIZED_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--validate-only", action="store_true",
                        help="revalidate current evidence against an existing package; never write")
    args = parser.parse_args()
    try:
        result = build_kernel_package(args.run, finalized_root=args.finalized_root,
                                      output_root=args.output_root, validate_only=args.validate_only)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (KernelPackageError, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc), "external_mutation": False}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
