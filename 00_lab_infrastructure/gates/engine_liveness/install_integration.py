"""Plan/apply the reviewed PR109 -> PR108 patch stack against exact source bytes.

No production path is selected by default. Apply requires explicit merged-review
proof and an immutable rollback receipt; this tool never enables S8 policy.
"""
from __future__ import annotations

import argparse
import hashlib
import fcntl
import json
import os
from pathlib import Path
import subprocess
import stat
import sys
import tempfile
import types

class LivenessHold(RuntimeError):
    pass


def file_digest(path: Path) -> str:
    return hashlib.sha256(captured(path)).hexdigest()


def immutable_json(path: Path, value: dict) -> dict:
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            if sys.platform == "darwin" and hasattr(fcntl, "F_FULLFSYNC"):
                fcntl.fcntl(stream.fileno(), fcntl.F_FULLFSYNC)
        try:
            os.link(temporary, path)
        except FileExistsError:
            if captured(path) != raw:
                raise LivenessHold("HOLD_INSTALL_RECEIPT_COLLISION")
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return value

HERE = Path(__file__).resolve().parent
HELPERS = ("scheduler_liveness.py", "checkpoint_certification_lane.py", "checkpoint_advisory.py")



def captured(path: Path) -> bytes:
    """Read one stable regular source object without following a leaf symlink."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > 16_000_000:
            raise LivenessHold("HOLD_INSTALL_REGULAR_BOUNDED_SOURCE")
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
        final = path.lstat()
        fields = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns)
        if fields(before) != fields(after) or fields(after) != fields(final):
            raise LivenessHold("HOLD_INSTALL_INPUT_CHANGED")
        return raw
    finally:
        os.close(descriptor)


def verify_current_inputs(pipeline: Path, value: dict) -> None:
    """Compare the checked closure again immediately before installation writes."""
    if (file_digest(HERE / "INTEGRATION_BINDING.json") != value["binding_sha256"]
            or any(file_digest(HERE / name) != digest for name, digest in value["source_sha256"].items())):
        raise LivenessHold("HOLD_INSTALL_SOURCE_CAS")
    if any(file_digest(pipeline / name) != digest for name, digest in value["before_sha256"].items()):
        raise LivenessHold("HOLD_INSTALL_BEFORE_CAS")
    if (file_digest(pipeline / "verification_coverage_gates/terminal_certification/terminal_hold.py") != value["terminal_helper_sha256"]
            or file_digest(pipeline / "job_observation_policy.py") != value["unchanged_job_observation_sha256"]):
        raise LivenessHold("HOLD_INSTALL_DEPENDENCY_CAS")


def plan(pipeline: Path) -> tuple[dict, dict[str, bytes]]:
    pipeline = pipeline.resolve(strict=True)
    binding_raw = captured(HERE / "INTEGRATION_BINDING.json")
    binding = json.loads(binding_raw)
    sources = {name: captured(HERE / name) for name in binding["source_files"]}
    for name, expected in binding["source_files"].items():
        if hashlib.sha256(sources[name]).hexdigest() != expected:
            raise LivenessHold("HOLD_INSTALL_SOURCE_HASH")
    before = {}
    # Validate every before-file before patch staging, helper writes or receipts.
    for row in binding["files"]:
        name = Path(row["path"]).name
        target = pipeline / name
        raw = captured(target)
        if hashlib.sha256(raw).hexdigest() != row["before_sha256"]:
            raise LivenessHold("HOLD_INSTALL_BEFORE_HASH")
        before[name] = raw
    terminal = pipeline / "verification_coverage_gates/terminal_certification/terminal_hold.py"
    terminal_raw = captured(terminal)
    if hashlib.sha256(terminal_raw).hexdigest() != binding["terminal_helper_sha256"]:
        raise LivenessHold("HOLD_INSTALL_TERMINAL_HELPER_HASH")
    module = types.ModuleType("_checked_terminal_helper")
    module.__file__ = str(terminal)
    exec(compile(terminal_raw, str(terminal), "exec"), module.__dict__)
    if not callable(module.terminal_hold):
        raise LivenessHold("HOLD_INSTALL_TERMINAL_HELPER_IMPORT")
    observation_raw = captured(pipeline / "job_observation_policy.py")
    if hashlib.sha256(observation_raw).hexdigest() != binding["unchanged_job_observation_sha256"]:
        raise LivenessHold("HOLD_INSTALL_UNCHANGED_VALIDATOR_HASH")
    staged = {}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "RESEARCH_PIPELINE_v2"
        target.mkdir()
        for name, raw in before.items():
            (target / name).write_bytes(raw)
        for patch in ("G1_CONTROLLER_EXECUTOR.patch", "G2_EXISTING_CHECKPOINT.patch"):
            patch_path = root / patch
            patch_path.write_bytes(sources[patch])
            result = subprocess.run(["git", "apply", "--unidiff-zero", str(patch_path)],
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
        staged[name] = sources[name]
    value = {"standard": "VRS-ENGINE-LIVENESS-INSTALL-1", "status": "PLANNED_INACTIVE",
            "binding_sha256": hashlib.sha256(binding_raw).hexdigest(),
            "source_sha256": binding["source_files"],
            "before_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in before.items()},
            "after_sha256": {name: hashlib.sha256(raw).hexdigest() for name, raw in staged.items()},
            "terminal_helper_sha256": hashlib.sha256(terminal_raw).hexdigest(),
            "unchanged_job_observation_sha256": hashlib.sha256(observation_raw).hexdigest(), "policy_activation": False}
    verify_current_inputs(pipeline, value)
    return value, staged


def install(pipeline: Path, receipt: Path, evidence: Path, expected: str) -> dict:
    value, staged = plan(pipeline)
    evidence_raw = captured(evidence)
    if hashlib.sha256(evidence_raw).hexdigest() != expected:
        raise LivenessHold("HOLD_INSTALL_REVIEW_EVIDENCE_HASH")
    review = json.loads(evidence_raw)
    if (review.get("merged_by") != "Justin" or review.get("ci") != "PASS"
            or review.get("independent_review") != "PASS"
            or review.get("source_sha256") != value["source_sha256"]
            or review.get("binding_sha256") != value["binding_sha256"]):
        raise LivenessHold("HOLD_INSTALL_REVIEW_EVIDENCE")
    if receipt.exists() or receipt.parent.exists():
        raise LivenessHold("HOLD_INSTALL_FRESH_RECEIPT_DIRECTORY")
    pipeline = pipeline.resolve(strict=True)
    original = {name: captured(pipeline / name) if (pipeline / name).exists() else None
                for name in staged}
    if any(hashlib.sha256(original[name]).hexdigest() != expected for name, expected in value["before_sha256"].items()):
        raise LivenessHold("HOLD_INSTALL_BEFORE_CAS")
    if any((pipeline / name).is_symlink() for name in staged):
        raise LivenessHold("HOLD_INSTALL_SOURCE_SYMLINK")
    verify_current_inputs(pipeline, value)
    if file_digest(evidence) != expected:
        raise LivenessHold("HOLD_INSTALL_REVIEW_EVIDENCE_HASH")
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
