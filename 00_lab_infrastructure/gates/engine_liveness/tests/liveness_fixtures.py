"""Synthetic but fully source-bound provider fixtures; no transport or Lean."""
import hashlib
import json
from pathlib import Path

from job_observation_policy import STANDARD, PHASES, COMMON_FILES, KERNEL_FILES


def write_rejection(identity, entry, goal="exact failing goal"):
    request_path = Path(entry["request"]["path"])
    request = json.loads(request_path.read_text())
    def observed(digest="3" * 64):
        return {"status": "OBSERVED", "sha256": digest, "actualPath": "/fixture/file"}
    phases = []
    request_id = "fixture-" + identity.key[:16]
    for name in PHASES:
        sources = {"Solution": observed(identity.candidate_sha256)} if name == "compile-Solution" else {"Challenge": observed(identity.statement_sha256)}
        if name == "compare-kernels":
            sources["Solution"] = observed(identity.candidate_sha256)
        phases.append({"standard": STANDARD, "phase": name, "executionId": request_id,
            "toolchainDeclaration": request["toolchain"], "sources": sources,
            "files": {key: observed() for key in COMMON_FILES + (KERNEL_FILES if name == "compare-kernels" else ())},
            "packages": [{"name": "mathlib", "manifestRevision": request["mathlib_rev"], "checkoutHead": request["mathlib_rev"]}]})
    response = {"requestId": request_id, "type": "verification-failed", "project": "viridis-lean-4.28", "output": goal,
        "executionEvidence": {"standard": STANDARD, "status": "OBSERVED_PARTIAL", "failures": [], "cacheEligible": False,
            "compiledDependencyClosureSha256": None, "inputSha256": {"Challenge": identity.statement_sha256, "Solution": identity.candidate_sha256},
            "executionId": request_id, "delivery": {"mode": "FRESH_EXECUTION", "servedForRequestId": request_id},
            "worker": {"nodeExecutable": observed(), "sourceAtLoad": observed()}, "phases": phases},
        "terminationDiagnostics": {"standard": "VRS-COMPARATOR-TERMINATION-1", "capture_status": "RECORDED", "requestId": request_id,
            "records": [{"requestId": request_id, "phase": "compile-Solution", "exitCode": 1, "reason": "exited", "signal": None,
                         "guard_fired": False, "end": "2026-10-15T23:00:00Z"}]}}
    cloud = {"standard": "VRS-COMPARATOR-DUAL-KERNEL-1", "status": "HOLD", "provider": "VIRIDIS_COMPARATOR_CLOUD",
        "project": "viridis-lean-4.28", "local_lean_execution": False, "credentials_recorded": False,
        **{key: entry[key] for key in ("request", "formal_statement", "candidate")}, "provider_response": response,
        "provider_response_sha256": hashlib.sha256((json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()}
    path = Path(entry["receipt_output"])
    path.write_text(json.dumps(cloud))
    return cloud
