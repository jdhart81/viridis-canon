"""Synthetic but fully source-bound provider fixtures; no transport or Lean."""
import hashlib
import json
from pathlib import Path



def write_rejection(identity, entry, goal="exact failing goal"):
    request_path = Path(entry["request"]["path"])
    request = json.loads(request_path.read_text())
    request_id = "fixture-" + identity.key[:16]
    response = {"requestId": request_id, "type": "verification-failed", "project": "viridis-lean-4.28", "output": goal,
        "executionEvidence": {"delivery": {"mode": "FRESH_EXECUTION", "servedForRequestId": request_id}},
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
