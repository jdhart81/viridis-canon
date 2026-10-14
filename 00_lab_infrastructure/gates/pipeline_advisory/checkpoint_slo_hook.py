"""Bounded report hook for the existing checkpoint owner; no pipeline actions.

Install beside pipeline_slo.py only from an independently reviewed source
closure. The companion hash-bound patch calls this after checkpoint writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

import pipeline_slo

MAX_INPUT_BYTES = 1024 * 1024


def ancestry(path: Path, root: Path) -> tuple:
    cursor = root
    observed = root.lstat()
    if not stat.S_ISDIR(observed.st_mode):
        raise ValueError("regular root required")
    frames = [(str(root), observed.st_dev, observed.st_ino, observed.st_mode)]
    for part in path.relative_to(root).parts[:-1]:
        cursor /= part
        observed = cursor.lstat()
        if not stat.S_ISDIR(observed.st_mode):
            raise ValueError("regular input parent required")
        frames.append((str(cursor), observed.st_dev, observed.st_ino, observed.st_mode))
    return tuple(frames)


def read_json(path: Path, root: Path) -> tuple[dict, str]:
    """Read one scoped regular file with the five-field stable identity."""
    before_parents = ancestry(path, root)
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_INPUT_BYTES:
            raise ValueError("bounded regular input required")
        def bounded_bytes():
            chunks, remaining = [], MAX_INPUT_BYTES + 1
            while remaining:
                block = os.read(descriptor, remaining)
                if not block:
                    break
                chunks.append(block)
                remaining -= len(block)
            return b"".join(chunks)
        raw = bounded_bytes()
        os.lseek(descriptor, 0, os.SEEK_SET)
        repeated = bounded_bytes()
        after = os.fstat(descriptor)
        final = path.lstat()
        fields = lambda value: (value.st_size, value.st_mtime_ns, value.st_ino, value.st_dev)
        if (len(raw) != before.st_size or raw != repeated or fields(before) != fields(after)
                or fields(after) != fields(final) or ancestry(path, root) != before_parents):
            raise ValueError("input changed during observation")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("object input required")
        return value, hashlib.sha256(raw).hexdigest()
    finally:
        os.close(descriptor)


def atomic_report(path: Path, value: dict, root: Path) -> None:
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("report exceeds receipt budget")
    parent_frames = ancestry(path, root)
    # Walk with directory descriptors. Neither a parent-link race nor a replaced
    # output symlink can redirect this write to a different filesystem location.
    descriptors = [os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)]
    temporary = ".pipeline-slo-" + uuid.uuid4().hex
    try:
        for part in path.parent.relative_to(root).parts:
            descriptors.append(os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                       dir_fd=descriptors[-1]))
        parent = descriptors[-1]
        try:
            existing = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            existing = None
        if existing is not None and not stat.S_ISREG(existing.st_mode):
            raise ValueError("regular output required")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        if ancestry(path, root) != parent_frames:
            raise ValueError("output parent changed")
        os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
        if ancestry(path, root) != parent_frames:
            raise ValueError("output parent changed")
    finally:
        try:
            os.unlink(temporary, dir_fd=descriptors[-1])
        except FileNotFoundError:
            pass
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def emit(root: Path, checkpoint: Path, *, as_of: str | None = None) -> dict:
    """Update a derived report without modifying checkpoint or science state.

    Missing coverage/weekly/leak inputs remain unavailable. A supplied footprint
    list is capped at 195, leaving five fixed source/data input slots.
    """
    root = root.resolve(strict=True)
    checkpoint = Path(checkpoint).absolute()
    base = root / "RESEARCH_PIPELINE_v2"
    relative = checkpoint.relative_to(base / "nightly_checkpoints")
    if len(relative.parts) != 2 or relative.name not in {"START.json", "FINISH.json"}:
        raise ValueError("canonical checkpoint input required")
    invocation = relative.parts[0]
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}", invocation):
        raise ValueError("invalid checkpoint invocation")
    completed, checkpoint_hash = read_json(checkpoint, root)
    if completed.get("standard") != "VRS-NIGHTLY-CHECKPOINT-1" or completed.get("invocation_id") != invocation:
        raise ValueError("checkpoint identity differs")
    observer, observer_hash = read_json(base / "FOUNDRY_OBSERVER_STATUS.json", root)
    supplied_path = base / "PIPELINE_SLO_INPUTS.json"
    if supplied_path.exists() or supplied_path.is_symlink():
        supplied, supplied_hash = read_json(supplied_path, root)
    else:
        supplied, supplied_hash = {}, None
    files = supplied.get("new_evidence", {}).get("files", [])
    if not isinstance(files, list) or len(files) > 195:
        raise ValueError("scoped input limit exceeded")
    report = pipeline_slo.collect(observer, supplied,
        as_of or datetime.now(timezone.utc).isoformat(), root)
    report.update(activation="EXISTING_CHECKPOINT_REPORT_ONLY", checkpoint={
        "invocation_id": invocation, "stage": relative.name[:-5],
        "sha256": checkpoint_hash, "status": completed.get("status")},
        input_sha256={"observer": observer_hash, "supplied_snapshot": supplied_hash},
        input_file_limit=200)
    atomic_report(base / "PIPELINE_SLO_STATUS.json", report, root)
    return {"status": "REPORTED", "certifies": False, "external_mutations": 0}


def observe(root: Path, checkpoint: Path) -> dict:
    """Advisory errors cannot change generation, FIFO or checkpoint exit status."""
    try:
        return emit(root, checkpoint)
    except Exception:
        # Never include exception text, traceback or controller output.
        return {"status": "ADVISORY_UNAVAILABLE", "certifies": False, "external_mutations": 0}


def monday_summary(report: dict, adoption_snapshot: str) -> str:
    """Pure existing-report adapter; it never runs a checkpoint or schedule."""
    return adoption_snapshot.rstrip() + "\n\n" + pipeline_slo.weekly_summary(report)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(observe(arguments.root, arguments.checkpoint), sort_keys=True))
