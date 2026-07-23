"""Deterministic serialization used by the public research catalog."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_bytes(value: Any) -> bytes:
    """Return stable UTF-8 JSON bytes for JSON-compatible ``value``."""

    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    """Return the SHA-256 hex digest of ``value``'s canonical bytes."""

    return hashlib.sha256(canonical_bytes(value)).hexdigest()
