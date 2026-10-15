"""Bounded child-only Lean lint and SLO reporting; never changes a gate."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import types

PINS = {
    "checkpoint_slo_hook.py": "d337a83712ecda5a1645ffc63786d56b850d75dc1832430e774058cb87285cc6",
    "pipeline_slo.py": "4f8fd3b627e365baca5186fcc074d75b85227aeec88e8594e922a9ff2caea254",
    "lean_repair_lint.py": "ba47973f5834764289b9626e2592f446857eab1e9b8c6de104515b103b5c2ed2",
}
PLAYBOOK_SHA256 = "87ded0138f522738aeb4dbe68be3861f4c46e11bc61ae65c2be0e0557de2c8eb"
LIMIT = 1024 * 1024


def read_regular(path: Path, root: Path) -> bytes:
    path.relative_to(root)
    cursor = root
    for part in path.relative_to(root).parts:
        cursor /= part
        if cursor.is_symlink():
            raise ValueError("advisory symlink refused")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > LIMIT:
            raise ValueError("bounded advisory input required")
        raw = os.read(descriptor, LIMIT + 1)
        after = os.fstat(descriptor)
        final = path.lstat()
        fields = lambda row: (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns)
        if len(raw) != before.st_size or fields(before) != fields(after) or fields(after) != fields(final):
            raise ValueError("advisory input changed")
        return raw
    finally:
        os.close(descriptor)


def report(path: Path, value: dict, root: Path) -> None:
    path.relative_to(root)
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("advisory output symlink refused")
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if len(raw) > LIMIT:
        raise ValueError("advisory output budget")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def load(root: Path) -> dict:
    base = root / "RESEARCH_PIPELINE_v2/pipeline_advisory"
    modules = {}
    for name in ("pipeline_slo.py", "checkpoint_slo_hook.py", "lean_repair_lint.py"):
        raw = read_regular(base / name, root)
        if hashlib.sha256(raw).hexdigest() != PINS[name]:
            raise ValueError("advisory source binding")
        module = types.ModuleType(name[:-3]); module.__file__ = str(base / name)
        sys.modules[name[:-3]] = module
        exec(compile(raw, str(base / name), "exec"), module.__dict__)
        modules[name[:-3]] = module
    return modules


def observe(root: Path, checkpoint: Path) -> dict:
    root = root.resolve(strict=True)
    pipeline = root / "RESEARCH_PIPELINE_v2"
    relative = checkpoint.relative_to(pipeline / "nightly_checkpoints")
    if len(relative.parts) != 2 or relative.name not in {"START.json", "FINISH.json"}:
        raise ValueError("canonical advisory checkpoint required")
    raw = read_regular(checkpoint, root)
    current = json.loads(raw)
    if (current.get("standard") != "VRS-NIGHTLY-CHECKPOINT-1"
            or current.get("invocation_id") != relative.parts[0]):
        raise ValueError("advisory checkpoint binding")
    modules = None
    lint_status = "ADVISORY_UNAVAILABLE"
    try:
        modules = load(root)
        source = read_regular(pipeline / "LEAN_REPAIR_PLAYBOOK.json", root)
        if hashlib.sha256(source).hexdigest() != PLAYBOOK_SHA256:
            raise ValueError("advisory playbook binding")
        playbook = json.loads(source)
        debt = current.get("science", {}).get("certification", {}).get("backlog_runs",
               current.get("certification", {}).get("remaining_debt", []))
        rows = []
        for run in debt[:2]:
            if not isinstance(run, str) or not re.fullmatch(r"Run-[0-9]{3,}", run):
                raise ValueError("advisory run identity")
            path = pipeline / "lean_certificates" / run / "VERIFICATION_CANDIDATE.lean"
            try:
                result = modules["lean_repair_lint"].lint(read_regular(path, root), playbook)
                rows.append({"run_id": run, "result": result})
            except Exception:
                rows.append({"run_id": run, "status": "ADVISORY_UNAVAILABLE", "certifies": False})
        report(checkpoint.parent / "LEAN_REPAIR_LINT_ADVISORY.json", {
            "standard": "VRS-CHECKPOINT-LEAN-LINT-1", "certifies": False,
            "checkpoint_sha256": hashlib.sha256(raw).hexdigest(), "results": rows,
            "status": "ADVISORY_REPORTED" if rows else "NO_EXPLICIT_PROOF_DEBT"}, root)
        lint_status = "ADVISORY_REPORTED"
    except Exception:
        # No exception/proof/controller/credential prose crosses this boundary.
        pass
    slo = {"status": "ADVISORY_UNAVAILABLE"}
    if modules is not None:
        slo = modules["checkpoint_slo_hook"].observe(root, checkpoint)
    if slo.get("status") != "REPORTED":
        report(pipeline / "PIPELINE_SLO_STATUS.json", {
            "standard": "VRS-PIPELINE-SLO-STATUS-1", "status": "ADVISORY_UNAVAILABLE",
            "certifies": False, "checkpoint_sha256": hashlib.sha256(raw).hexdigest(),
            "fifo_liveness": {"status": "UNAVAILABLE", "failing_goal": None},
            "reason": "Bound advisory inputs or source unavailable; science state unchanged."}, root)
    else:
        path = pipeline / "PIPELINE_SLO_STATUS.json"
        value = json.loads(read_regular(path, root))
        fifo = value.get("fifo_liveness", {})
        if isinstance(fifo.get("held_hours"), (float, int)) and fifo["held_hours"] >= 24:
            fifo["status"] = "ALERT"
            report(path, value, root)
    return {"status": "ADVISORY_ONLY", "lint": lint_status, "slo": slo.get("status"), "certifies": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()
    try:
        observe(args.root, args.checkpoint)
    except Exception:
        pass
