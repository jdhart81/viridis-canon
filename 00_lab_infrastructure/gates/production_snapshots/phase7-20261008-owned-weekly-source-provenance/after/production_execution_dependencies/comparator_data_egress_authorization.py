#!/usr/bin/env python3
"""Validate the standing private-Comparator data-egress authorization.

The receipt is authority only for exact frozen proof traffic to the configured
private Comparator. Any destination, project, scope, invariant, or exclusion
drift fails closed and grants no publication or deployment authority.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DEFAULT_AUTHORIZATION = HERE / "COMPARATOR_DATA_EGRESS_AUTHORIZATION.json"
DEFAULT_BACKENDS = HERE / "LEAN_VERIFIER_BACKENDS.json"

REQUIRED_INPUTS = {
    "Viridis paper inputs required to bind a frozen verification request",
    "Lean formal statements",
    "Lean proof candidates",
}
REQUIRED_OUTPUTS = {
    "immutable dual-kernel verification receipts",
    "zero-sorry certificates",
}
REQUIRED_RUN_SCOPE = {
    "current FIFO certification backlog",
    "future nightly science runs",
}
REQUIRED_INVARIANTS = {
    "backlog_first_fifo": True,
    "nanoda_kernel_required": True,
    "lean_default_kernel_required": True,
    "zero_sorries_required": True,
    "local_lean_execution": False,
    "aristotle_required": False,
    "fail_closed": True,
}
REQUIRED_EXCLUSIONS = {
    "publication": True,
    "credential_recording_in_receipts": True,
    "weakening_or_rewriting_frozen_claims": True,
}


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root is not an object")
    return value


def validate_authorization(
    authorization_path: Path = DEFAULT_AUTHORIZATION,
    backends_path: Path = DEFAULT_BACKENDS,
) -> dict[str, Any]:
    failures: list[str] = []
    authorization: dict[str, Any] = {}
    backends: dict[str, Any] = {}
    try:
        authorization = _read_object(authorization_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"authorization receipt unreadable: {type(exc).__name__}")
    try:
        backends = _read_object(backends_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"verifier backend contract unreadable: {type(exc).__name__}")

    primary = next(
        (
            row for row in backends.get("backends", [])
            if isinstance(row, dict) and row.get("id") == backends.get("primary_backend")
        ),
        {},
    )
    endpoint = str(primary.get("endpoint", ""))
    configured_host = endpoint.split(":", 1)[0] if endpoint else ""
    destination = authorization.get("destination", {})
    scope = authorization.get("scope", {})
    invariants = authorization.get("required_invariants", {})
    exclusions = authorization.get("excluded_actions", {})

    if authorization.get("status") != "ACTIVE_STANDING_AUTHORIZATION":
        failures.append("standing authorization is not active")
    if authorization.get("authorized_by") != "Justin D. Hart":
        failures.append("authorization principal mismatch")
    if primary.get("id") != "COMPARATOR_CLOUD" or primary.get("status") != "ENABLED":
        failures.append("private Comparator is not the enabled primary backend")
    if destination.get("host") != configured_host or not configured_host:
        failures.append("authorized host does not match the configured private Comparator")
    if destination.get("project") != primary.get("project") or not primary.get("project"):
        failures.append("authorized project does not match the configured Comparator project")
    if destination.get("service_visibility") != "PRIVATE_LOOPBACK_BEHIND_DEDICATED_SSH":
        failures.append("authorization does not bind the private SSH-only service")
    if primary.get("public_http_exposure") is not False:
        failures.append("Comparator backend is not private")
    if set(scope.get("inputs", [])) != REQUIRED_INPUTS:
        failures.append("authorized input scope drift")
    if set(scope.get("outputs", [])) != REQUIRED_OUTPUTS:
        failures.append("authorized output scope drift")
    if set(scope.get("runs", [])) != REQUIRED_RUN_SCOPE:
        failures.append("authorized run scope does not cover backlog and future nightly runs")
    for key, expected in REQUIRED_INVARIANTS.items():
        if invariants.get(key) is not expected:
            failures.append(f"required invariant mismatch: {key}")
    for key, expected in REQUIRED_EXCLUSIONS.items():
        if exclusions.get(key) is not expected:
            failures.append(f"required exclusion mismatch: {key}")
    if backends.get("local_lean_fallback_authorized") is not False:
        failures.append("backend contract permits local Lean fallback")
    if backends.get("aristotle_required") is not False:
        failures.append("backend contract requires Aristotle")
    if sorted(primary.get("kernels", [])) != ["LEAN_DEFAULT_KERNEL", "NANODA"]:
        failures.append("configured Comparator kernels drifted")
    if primary.get("permitted_sorries") != []:
        failures.append("configured Comparator permits proof holes")

    receipt_sha256 = None
    try:
        receipt_sha256 = hashlib.sha256(authorization_path.read_bytes()).hexdigest()
    except OSError:
        pass
    return {
        "status": "AUTHORIZED" if not failures else "HOLD",
        "authorization_id": authorization.get("authorization_id"),
        "authorization_sha256": receipt_sha256,
        "destination_host": destination.get("host"),
        "project": destination.get("project"),
        "covers_future_nightly_runs": not failures,
        "publication_authorized": False,
        "production_deployment_authorized": False,
        "failures": failures,
    }


if __name__ == "__main__":
    print(json.dumps(validate_authorization(), indent=2, sort_keys=True))
