"""Plan/apply the reviewed PR109 -> PR108 patch stack against exact source bytes.

No production path is selected by default. Apply requires explicit merged-review
proof and an immutable rollback receipt; this tool never enables S8 policy.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

from scheduler_liveness import LivenessHold, file_digest, immutable_json

HERE = Path(__file__).resolve().parent
HELPERS = ("scheduler_liveness.py", "checkpoint_certification_lane.py", "checkpoint_advisory.py")


def plan(pipeline: Path) -> tuple[dict, dict[str, bytes]]:
    pipeline = pipeline.resolve(strict=True)
    binding = json.loads((HERE / "INTEGRATION_BINDING.json").read_text())
    for name, expected in binding["source_files"].items():
        if file_digest(HERE / name) != expected:
            raise LivenessHold("HOLD_INSTALL_SOURCE_HASH")
    before = {}
    # Validate every before-file before patch staging, helper writes or receipts.
    for row in binding["files"]:
        name = Path(row["path"]).name
        target = pipeline / name
        if file_digest(target) != row["before_sha256"]:
            raise LivenessHold("HOLD_INSTALL_BEFORE_HASH")
        before[name] = target.read_bytes()
    terminal = pipeline / "verification_coverage_gates/terminal_certification/terminal_hold.py"
    if file_digest(terminal) != binding["terminal_helper_sha256"]:
        raise LivenessHold("HOLD_INSTALL_TERMINAL_HELPER_HASH")
    spec = importlib.util.spec_from_file_location("_checked_terminal_helper", terminal)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(module.terminal_hold):
        raise LivenessHold("HOLD_INSTALL_TERMINAL_HELPER_IMPORT")
    if file_digest(pipeline / "job_observation_policy.py") != binding["unchanged_job_observation_sha256"]:
        raise LivenessHold("HOLD_INSTALL_UNCHANGED_VALIDATOR_HASH")
    staged = {}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "RESEARCH_PIPELINE_v2"
        target.mkdir()
        for name, raw in before.items():
            (target / name).write_bytes(raw)
        for patch in ("G1_CONTROLLER_EXECUTOR.patch", "G2_EXISTING_CHECKPOINT.patch"):
            result = subprocess.run(["git", "apply", "--unidiff-zero", str(HERE / patch)],
                                    cwd=root, capture_output=True, timeout=30)
            if result.returncode:
                raise LivenessHold("HOLD_INSTALL_PATCH_APPLY")
        for row in binding["files"]:
            name = Path(row["path"]).name
            raw = (target / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != row["after_sha256"]:
                raise LivenessHold("HOLD_INSTALL_AFTER_HASH")
            compile(raw, name, "exec")
            staged[name] = raw
    for name in HELPERS:
        staged[name] = (HERE / name).read_bytes()
    return {"standard": "VRS-ENGINE-LIVENESS-INSTALL-1", "status": "PLANNED_INACTIVE",
            "binding_sha256": file_digest(HERE / "INTEGRATION_BINDING.json"),
            "source_sha256": binding["source_files"],
            "before_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in before.items()},
            "after_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in staged.items()},
            "terminal_helper_sha256": file_digest(terminal), "policy_activation": False}, staged


def install(pipeline: Path, receipt: Path, evidence: Path, expected: str) -> dict:
    value, staged = plan(pipeline)
    if file_digest(evidence) != expected:
        raise LivenessHold("HOLD_INSTALL_REVIEW_EVIDENCE_HASH")
    review = json.loads(evidence.read_text())
    if (review.get("merged_by") != "Justin" or review.get("ci") != "PASS"
            or review.get("independent_review") != "PASS"
            or review.get("source_sha256") != value["source_sha256"]):
        raise LivenessHold("HOLD_INSTALL_REVIEW_EVIDENCE")
    if receipt.exists() or receipt.parent.exists():
        raise LivenessHold("HOLD_INSTALL_FRESH_RECEIPT_DIRECTORY")
    pipeline = pipeline.resolve(strict=True)
    original = {name: (pipeline / name).read_bytes() if (pipeline / name).exists() else None
                for name in staged}
    if any((pipeline / name).is_symlink() for name in staged):
        raise LivenessHold("HOLD_INSTALL_SOURCE_SYMLINK")
    receipt.parent.mkdir(parents=True)
    rollback = receipt.parent / "rollback"
    rollback.mkdir()
    for name, raw in original.items():
        if raw is not None:
            (rollback / name).write_bytes(raw)
    immutable_json(receipt.parent / "PLAN.json", {**value, "review_evidence_sha256": expected,
                   "rollback": {name: str(rollback / name) if raw is not None else "REMOVE_NEW_HELPER"
                                for name, raw in original.items()}})
    changed = []
    try:
        for name in (*HELPERS, *(name for name in staged if name not in HELPERS)):
            raw = staged[name]
            destination = pipeline / name
            with tempfile.NamedTemporaryFile(dir=pipeline, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, destination)
            changed.append(name)
        if any(file_digest(pipeline / name) != expected for name, expected in value["after_sha256"].items()):
            raise LivenessHold("HOLD_INSTALL_READBACK")
    except Exception:
        for name in reversed(changed):
            if original[name] is None:
                (pipeline / name).unlink()
            else:
                (pipeline / name).write_bytes(original[name])
        raise
    return immutable_json(receipt, {**value, "status": "INSTALLED_INACTIVE",
                          "review_evidence_sha256": expected, "readback": "EXACT"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--review-evidence", type=Path)
    parser.add_argument("--expected-review-evidence-sha256")
    args = parser.parse_args()
    try:
        if args.apply:
            if not all((args.receipt, args.review_evidence, args.expected_review_evidence_sha256)):
                raise LivenessHold("HOLD_INSTALL_EXACT_REVIEW_REQUIRED")
            value = install(args.pipeline, args.receipt, args.review_evidence,
                            args.expected_review_evidence_sha256)
        else:
            value, _ = plan(args.pipeline)
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, LivenessHold) as exc:
        code = str(exc) if isinstance(exc, LivenessHold) else "HOLD_INSTALL_INPUT"
        print(json.dumps({"status": "HOLD", "error": code}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
