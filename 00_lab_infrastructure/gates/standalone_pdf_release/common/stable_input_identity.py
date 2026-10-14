"""Prepared content-bound input reader; no activation or admission authority."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

Identity = tuple[str, int, int, int, int]


class StableInputHold(ValueError):
    pass


@dataclass(frozen=True)
class InputSnapshot:
    data: bytes
    identity: Identity


def _metadata(observed):
    return (observed.st_size, observed.st_mtime_ns, observed.st_ino, observed.st_dev)


def _regular(observed):
    if not stat.S_ISREG(observed.st_mode):
        raise StableInputHold("regular input required")


def _no_artifact_links(path):
    for component in (path, *path.parents):
        if component.is_symlink() and component not in {Path("/var"), Path("/tmp")}:
            raise StableInputHold("artifact-controlled input link refused")


def _read_once(descriptor, limit):
    os.lseek(descriptor, 0, os.SEEK_SET)
    blocks = []; size = 0
    while block := os.read(descriptor, min(1024 * 1024, limit - size + 1)):
        size += len(block)
        if size > limit:
            raise StableInputHold("input exceeds approved byte limit")
        blocks.append(block)
    return b"".join(blocks)


def read_stable(path: Path, *, expected: Identity | None = None,
                max_bytes: int = 200 * 1024 * 1024) -> InputSnapshot:
    """Bind SHA-256, size, modification time, inode and device in that order.

    File kind and no-link checks remain safety predicates. Permission and xattr
    metadata are outside content identity. Both bounded reads must agree, and
    the final path must still name the opened descriptor's regular file.
    """
    if type(max_bytes) is not int or not 0 <= max_bytes <= 2 * 1024 * 1024 * 1024:
        raise StableInputHold("explicit bounded input size required")
    path = Path(path).absolute()
    if ".." in path.parts:
        raise StableInputHold("canonical lexical input path required")
    try:
        _no_artifact_links(path)
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            before = os.fstat(descriptor); _regular(before)
            if before.st_size > max_bytes:
                raise StableInputHold("input exceeds approved byte limit")
            raw = _read_once(descriptor, max_bytes)
            middle = os.fstat(descriptor); _regular(middle)
            readback = _read_once(descriptor, max_bytes)
            after = os.fstat(descriptor); _regular(after)
            _no_artifact_links(path)
            final = path.stat(follow_symlinks=False); _regular(final)
            if (_metadata(before) != _metadata(middle) or _metadata(before) != _metadata(after)
                    or _metadata(after) != _metadata(final) or len(raw) != after.st_size
                    or raw != readback):
                raise StableInputHold("content or stable input identity changed during read")
            identity = (hashlib.sha256(raw).hexdigest(), *_metadata(after))
            if expected is not None and identity != expected:
                raise StableInputHold("input differs from approved content identity")
            return InputSnapshot(raw, identity)
        finally:
            os.close(descriptor)
    except OSError:
        raise StableInputHold("input cannot be read as a stable regular file") from None
