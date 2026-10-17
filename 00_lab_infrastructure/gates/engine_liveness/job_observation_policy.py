"""Conservative receipt-consumer policy: observations are never complete build attestation.

Pure JSON validation only: no network, files, subprocesses or certificate writes.
"""
from __future__ import annotations
import re
from typing import Any

STANDARD = "VRS-COMPARATOR-JOB-OBSERVATION-1"
POLICY = "VRS-COMPARATOR-OBSERVATION-CONSUMER-1"
PHASES = ("compile-Challenge", "compile-Solution", "collect-theorems", "compare-kernels")
COMMON_FILES = ("launcher", "observerModule", "sandboxExecutable", "lean", "lake", "projectManifest", "projectConfig", "toolchainDeclaration")
KERNEL_FILES = ("comparator", "exporter", "nanoda", "kernelConfig")


def _digest(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def assess_job_observation(response: dict[str, Any], request: dict[str, Any], challenge_sha256: str, solution_sha256: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "policy": POLICY, "status": "UNAVAILABLE_LEGACY", "failures": [],
        "source_binding_status": "UNKNOWN", "approved_build_status": "UNREVIEWED",
        "full_toolchain_attested": False, "compiled_dependency_closure_sha256": None,
        "disk_cache_admitted": False,
        "scope": "Source-bound observations only. Manifest declarations are not approved executable or compiled-dependency pins; full attestation and cache admission remain unavailable.",
    }
    evidence = response.get("executionEvidence")
    if evidence is None:
        return result
    failures: list[str] = result["failures"]
    def require(condition: bool, reason: str) -> None:
        if not condition: failures.append(reason)
    def observed(value: Any) -> bool:
        return isinstance(value, dict) and value.get("status") == "OBSERVED" and _digest(value.get("sha256")) and isinstance(value.get("actualPath"), str) and bool(value["actualPath"])
    if not isinstance(evidence, dict):
        result.update(status="INVALID_OBSERVATION", failures=["EVIDENCE_NOT_OBJECT"])
        return result
    require(evidence.get("standard") == STANDARD, "UNSUPPORTED_OBSERVATION_STANDARD")
    require(evidence.get("status") == "OBSERVED_PARTIAL", "OBSERVATION_NOT_CLEAN_PARTIAL")
    require(evidence.get("failures") == [], "PRODUCER_INTEGRITY_FAILURE")
    require(evidence.get("cacheEligible") is False, "DISK_CACHE_NOT_ADMISSIBLE")
    require(evidence.get("compiledDependencyClosureSha256") is None, "UNSUPPORTED_CLOSURE_ASSERTION")
    inputs = {"Challenge": challenge_sha256, "Solution": solution_sha256}
    require(all(_digest(v) for v in inputs.values()) and evidence.get("inputSha256") == inputs, "REQUEST_SOURCE_BINDING_MISMATCH")
    execution_id, request_id = evidence.get("executionId"), response.get("requestId")
    require(isinstance(execution_id, str) and bool(execution_id), "MISSING_EXECUTION_ID")
    require(isinstance(request_id, str) and bool(request_id), "MISSING_RESPONSE_REQUEST_ID")
    delivery = evidence.get("delivery")
    if not isinstance(delivery, dict):
        failures.append("MISSING_DELIVERY_PROVENANCE")
    else:
        require(delivery.get("servedForRequestId") == request_id, "SERVED_REQUEST_ID_MISMATCH")
        if delivery.get("mode") == "FRESH_EXECUTION": require(execution_id == request_id, "FRESH_EXECUTION_ID_MISMATCH")
        elif delivery.get("mode") == "IN_FLIGHT_REUSE": require(execution_id != request_id, "REUSED_EXECUTION_NOT_DISTINCT")
        else: failures.append("UNSUPPORTED_DELIVERY_OR_DISK_CACHE")
    worker = evidence.get("worker")
    require(isinstance(worker, dict) and observed(worker.get("nodeExecutable")) and observed(worker.get("sourceAtLoad")), "WORKER_IDENTITY_UNAVAILABLE")
    expected_toolchain, expected_mathlib = request.get("toolchain"), request.get("mathlib_rev")
    require(isinstance(expected_toolchain, str) and bool(expected_toolchain), "REQUEST_TOOLCHAIN_UNAVAILABLE")
    require(isinstance(expected_mathlib, str) and re.fullmatch(r"[a-f0-9]{40}", expected_mathlib) is not None, "REQUEST_MATHLIB_REVISION_UNAVAILABLE")
    phases = evidence.get("phases")
    if not isinstance(phases, list) or len(phases) != len(PHASES) or not all(isinstance(p, dict) for p in phases):
        failures.append("INCOMPLETE_PHASE_SET")
        phases = []
    require(sorted(str(p.get("phase")) for p in phases) == sorted(PHASES), "PHASE_NAMES_MISMATCH")
    hashes: dict[str, set[str]] = {name: set() for name in ("lean", "lake", "projectManifest", "projectConfig", "toolchainDeclaration")}
    for phase in phases:
        name = phase.get("phase")
        require(phase.get("standard") == STANDARD and phase.get("executionId") == execution_id, "PHASE_IDENTITY_MISMATCH:" + str(name))
        require(phase.get("toolchainDeclaration") == expected_toolchain, "DECLARED_TOOLCHAIN_MISMATCH:" + str(name))
        source_names = ["Solution"] if name == "compile-Solution" else ["Challenge", "Solution"] if name == "compare-kernels" else ["Challenge"]
        sources = phase.get("sources") if isinstance(phase.get("sources"), dict) else {}
        for key in source_names:
            require(observed(sources.get(key)) and sources[key].get("sha256") == inputs[key], "PHASE_SOURCE_MISMATCH:" + str(name) + ":" + key)
        files = phase.get("files") if isinstance(phase.get("files"), dict) else {}
        for key in COMMON_FILES + (KERNEL_FILES if name == "compare-kernels" else ()):
            require(observed(files.get(key)), "RUNTIME_FILE_UNAVAILABLE:" + str(name) + ":" + key)
        for key in hashes:
            value = files.get(key)
            if isinstance(value, dict) and _digest(value.get("sha256")): hashes[key].add(value["sha256"])
        packages = phase.get("packages")
        mathlib = [p for p in packages if isinstance(p, dict) and p.get("name") == "mathlib"] if isinstance(packages, list) else []
        require(len(mathlib) == 1 and mathlib[0].get("manifestRevision") == expected_mathlib, "DECLARED_MATHLIB_MISMATCH:" + str(name))
        if len(mathlib) == 1 and mathlib[0].get("checkoutHead") is not None:
            require(mathlib[0]["checkoutHead"] == expected_mathlib, "OBSERVED_MATHLIB_CHECKOUT_MISMATCH:" + str(name))
    for name, values in hashes.items(): require(len(values) == 1, "PHASE_RUNTIME_MISMATCH:" + name)
    result["status"] = "INVALID_OBSERVATION" if failures else "OBSERVATION_MATCH_PARTIAL"
    if not failures: result["source_binding_status"] = "MATCH"
    result["execution_id"] = execution_id
    result["served_request_id"] = request_id
    return result
