#!/usr/bin/env python3
"""Report whether nightly generation and rolling Lean certification can flow."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from autonomous_pipeline_controller import certificate_clean
from nightly_science_preflight import RUNS_REL, SCIENCE_ROOT, _latest_run, preflight
from viridis_paths import CONTROL_ROOT
from nightly_generation_window import generation_window


BACKENDS_REL = Path("RESEARCH_PIPELINE_v2/LEAN_VERIFIER_BACKENDS.json")
COMPARATOR_HEALTH_REL = Path("RESEARCH_PIPELINE_v2/COMPARATOR_LIVE_HEALTH.json")
CERT_ROOT_REL = Path("RESEARCH_PIPELINE_v2/lean_certificates")
NIGHTLY_PACKAGES_REL = Path("RESEARCH_PIPELINE_v2/nightly_packages")
GENERATION_SLO_HOURS = 36
CERTIFICATION_SLO_HOURS = 36
BACKLOG_TARGET = 0
BACKLOG_CRITICAL = 7
COMPARATOR_HEALTH_SLO_MINUTES = 30
RECEIPT_ERA_FIRST_RUN = 116


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root must be an object: {path}")
    return value


def parse_utc(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise RuntimeError(f"timestamp is not timezone-aware: {value}")
    return parsed.astimezone(dt.timezone.utc)


def verifier_readiness(control_root: Path, now: dt.datetime | None = None) -> dict[str, Any]:
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    config = read_json(control_root / BACKENDS_REL)
    rows = []
    for backend in config.get("backends", []):
        if not isinstance(backend, dict):
            continue
        enabled = backend.get("status") == "ENABLED"
        credential = backend.get("credential_env")
        credential_ready = credential is None or bool(os.environ.get(str(credential)))
        keychain = backend.get("keychain")
        if not credential_ready and isinstance(keychain, dict):
            account = keychain.get("account")
            service = keychain.get("service")
            if isinstance(account, str) and isinstance(service, str):
                try:
                    lookup = subprocess.run(
                        ["/usr/bin/security", "find-generic-password", "-a", account, "-s", service],
                        check=False,
                        capture_output=True,
                        timeout=10,
                    )
                    credential_ready = lookup.returncode == 0
                except (OSError, subprocess.SubprocessError):
                    credential_ready = False
        endpoint_ready = isinstance(backend.get("endpoint"), str) and bool(backend.get("endpoint"))
        live_health_ready = True
        live_health_age_minutes = None
        if backend.get("id") == "COMPARATOR_CLOUD" and enabled:
            try:
                health = read_json(control_root / COMPARATOR_HEALTH_REL)
                checked = parse_utc(str(health["checked_at_utc"]))
                live_health_age_minutes = (now - checked).total_seconds() / 60
                live_health_ready = bool(
                    health.get("status") == "READY"
                    and health.get("standard") == "VRS-COMPARATOR-LIVE-HEALTH-1"
                    and health.get("project") == "viridis-lean-4.28"
                    and 0 <= live_health_age_minutes <= COMPARATOR_HEALTH_SLO_MINUTES
                )
            except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError):
                live_health_ready = False
        rows.append({
            "id": backend.get("id"),
            "enabled": enabled,
            "credential_ready": credential_ready,
            "endpoint_ready": endpoint_ready,
            "live_health_ready": live_health_ready,
            "live_health_age_minutes": round(live_health_age_minutes, 3) if live_health_age_minutes is not None else None,
            "ready": bool(enabled and credential_ready and endpoint_ready and live_health_ready),
        })
    required = int(config.get("required_independent_successes", 1))
    return {
        "standard": config.get("standard"),
        "required": required,
        "ready_count": sum(bool(row["ready"]) for row in rows),
        "ready": sum(bool(row["ready"]) for row in rows) >= required,
        "backends": rows,
        "local_lean_fallback_authorized": config.get("local_lean_fallback_authorized") is True,
    }


def evaluate(
    *,
    science_root: Path = SCIENCE_ROOT,
    control_root: Path = CONTROL_ROOT,
    now: dt.datetime | None = None,
    forge_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    runs_dir = science_root / RUNS_REL
    latest_number, latest_path = _latest_run(runs_dir)
    manifest = read_json(latest_path / "RUN_MANIFEST.json")
    generated_at = parse_utc(str(manifest["generated_at_utc"]))
    window = generation_window(generated_at, now)
    generation_age_hours = (now - generated_at).total_seconds() / 3600
    generation_preflight = preflight(science_root, control_root)
    package_inventory = control_root / NIGHTLY_PACKAGES_REL
    run_numbers = {
        int(match.group(1))
        for path in package_inventory.glob("Run-*")
        if path.is_dir() and (match := re.fullmatch(r"Run-(\d+)", path.name))
    }
    # Derived intake can be missing or partially installed after interruption.
    # Its presence must never hide a sealed source run's proof obligation.
    run_numbers.update(
        int(match.group(1))
        for path in runs_dir.glob("Run-*_*")
        if path.is_dir() and (match := re.match(r"Run-(\d+)_", path.name))
        and int(match.group(1)) >= RECEIPT_ERA_FIRST_RUN
    )
    run_numbers = sorted(run_numbers)
    certificate_root = control_root / CERT_ROOT_REL
    debt = [
        number for number in run_numbers
        if not certificate_clean(
            f"Run-{number:03d}",
            control_root / "RESEARCH_PIPELINE_v2/finalized_runs" / f"Run-{number:03d}",
            certificate_root,
        )
    ]
    certified_runs = [f"Run-{number:03d}" for number in run_numbers if number not in debt]
    certificates = []
    for path in (control_root / CERT_ROOT_REL).glob("Run-*/LEAN_ZERO_SORRY_CERTIFICATE*.json"):
        if path.parent.name not in certified_runs:
            continue
        try:
            certificate = read_json(path)
            issued = parse_utc(str(certificate["issued_at_utc"]))
        except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError):
            continue
        if issued > now:
            raise RuntimeError(f"certificate issuance is in the future: {path.parent.name}")
        certificates.append((issued, path, certificate))
    latest_certificate = max(certificates, default=None, key=lambda row: row[0])
    certification_age_hours = (
        (now - latest_certificate[0]).total_seconds() / 3600 if latest_certificate else None
    )
    verifier = verifier_readiness(control_root, now)
    forge = forge_snapshot if forge_snapshot is not None else {
        "status": "RETIRED_NOT_REQUIRED",
        "authority": "NONE",
        "reason": "Comparator is the production certificate authority; Aristotle is optional provenance only",
    }
    generation_ready = generation_preflight.get("status") == "READY"
    generation_fresh = generation_age_hours <= GENERATION_SLO_HOURS
    certification_recent = not debt or (
        certification_age_hours is not None and certification_age_hours <= CERTIFICATION_SLO_HOURS
    )
    proof_lane_ready = bool(verifier["ready"])
    certification_ready = proof_lane_ready
    if not generation_ready:
        status = "HOLD_GENERATION_PREFLIGHT"
    elif window["overdue"]:
        status = "DEGRADED_GENERATION_WINDOW_MISSED"
    elif not generation_fresh:
        status = "DEGRADED_GENERATION_OVERDUE"
    elif not certification_ready:
        status = "RUNNING_DEGRADED_CERTIFIER"
    elif not certification_recent:
        status = "RUNNING_CERTIFICATION_OVERDUE"
    elif len(debt) > BACKLOG_CRITICAL:
        status = "RUNNING_BACKLOG_CRITICAL"
    elif len(debt) > BACKLOG_TARGET:
        status = "RUNNING_BACKLOG_ABOVE_TARGET"
    elif window["generation_due"]:
        status = "RUNNING_GENERATION_DUE"
    else:
        status = "READY_CONTINUOUS_FOUNDRY"
    return {
        "schema_version": 1,
        "standard": "VRS-SCIENCE-FOUNDRY-CONTINUITY-1",
        "evaluated_at_utc": now.isoformat(),
        "status": status,
        "main_invariant": "one sealed paper generated nightly and at least one eligible zero-sorry certificate issued nightly through a rolling pipeline",
        "generation": {
            "ready": generation_ready,
            "fresh": generation_fresh,
            "due": window["generation_due"],
            "window": window,
            "latest_run": f"Run-{latest_number:03d}",
            "generated_at_utc": generated_at.isoformat(),
            "age_hours": round(generation_age_hours, 3),
            "slo_hours": GENERATION_SLO_HOURS,
            "certificate_debt_blocks_generation": False,
            "preflight_status": generation_preflight.get("status"),
            "preflight_failures": generation_preflight.get("failures", []),
        },
        "certification": {
            "ready": certification_ready,
            "recent": certification_recent,
            "latest_certificate": str(latest_certificate[1]) if latest_certificate else None,
            "age_hours": round(certification_age_hours, 3) if certification_age_hours is not None else None,
            "slo_hours": CERTIFICATION_SLO_HOURS,
            "certified_runs": certified_runs,
            "backlog_count": len(debt),
            "backlog_runs": [f"Run-{number:03d}" for number in debt],
            "backlog_target": BACKLOG_TARGET,
            "backlog_critical": BACKLOG_CRITICAL,
            "proof_lane_ready": proof_lane_ready,
            "legacy_aristotle_status": forge.get("status"),
            "verifier": verifier,
        },
        "truth_boundary": "generation is not certification; only a current LEAN_ZERO_SORRY_CERTIFIED receipt marks a verified paper",
        "next_action": (
            "repair generation preflight immediately" if not generation_ready
            else "generate the due nightly paper now" if window["generation_due"] or not generation_fresh
            else "configure at least one independent cloud verifier backend; do not use local Lean" if not verifier["ready"]
            else "verify the oldest FIFO frozen request with Comparator and issue one certificate" if debt
            else "generate the next due paper and keep the rolling lane warm"
        ),
        "external_mutation": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = evaluate()
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            temporary = args.output.with_suffix(args.output.suffix + ".tmp")
            temporary.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(args.output)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2 if (
            not result["generation"]["ready"]
            or not result["generation"]["fresh"]
            or result["generation"]["window"]["overdue"]
            or not result["certification"]["ready"]
            or not result["certification"]["recent"]
            or result["certification"]["backlog_count"] > BACKLOG_CRITICAL
        ) else 0
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc), "external_mutation": False}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
