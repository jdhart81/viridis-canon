"""Production draft-and-discard primitives; never admit a publication action."""
from datetime import datetime, timezone
from contextvars import ContextVar
from functools import wraps
import time
import hashlib
import json
import os
from pathlib import Path


_DEADLINE = ContextVar("production_rehearsal_deadline", default=None)


class RehearsalHold(ValueError):
    pass


def time_bounded(operation):
    @wraps(operation)
    def run(*args, **kwargs):
        token = _DEADLINE.set(time.monotonic() + 540)
        try:
            return operation(*args, **kwargs)
        finally:
            _DEADLINE.reset(token)
    return run


def timeout(requested):
    end = _DEADLINE.get()
    if end is None:
        return requested
    left = end - time.monotonic()
    if left <= 0:
        raise RehearsalHold("rehearsal deadline exceeded")
    return min(requested, left)


def cleanup_window():
    if _DEADLINE.get() is not None:
        _DEADLINE.set(time.monotonic() + 20)


def require_production():
    if "VIRIDIS_ZENODO_API_BASE" in os.environ:
        raise RehearsalHold("VIRIDIS_ZENODO_API_BASE is forbidden; production endpoint is fixed")


def publish_action_url(identifier, *, rehearse=False):
    require_production()
    if rehearse:
        raise RehearsalHold("publication action is forbidden during rehearsal")
    if not str(identifier).isdigit():
        raise RehearsalHold("canonical draft identifier required")
    return "https://zenodo.org/api/deposit/depositions/" + str(identifier) + "/actions/publish"


def output_directory(output=None):
    root = os.environ.get("VIRIDIS_ENGINE_ROOT")
    if not root:
        raise RehearsalHold("VIRIDIS_ENGINE_ROOT must name the runbook engine directory")
    base = Path(root).resolve(strict=True) / "rehearsals"
    destination = Path(output).resolve() if output else base / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    if not destination.is_relative_to(base) or destination == base:
        raise RehearsalHold("rehearsal receipts must be inside ENGINE/rehearsals/<UTC>")
    destination.mkdir(parents=True, exist_ok=False)
    return destination


def tree_hashes(bundle):
    return {str(p.relative_to(bundle)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(Path(bundle).rglob("*")) if p.is_file()}


def discard(call, identifier):
    url = "https://zenodo.org/api/deposit/depositions/" + str(identifier)
    call("DELETE", url)
    try:
        call("GET", url)
    except Exception as exc:
        if getattr(exc, "code", None) in (404, 410):
            return {"draft_id": str(identifier), "deleted": True, "http_status": exc.code}
        raise RehearsalHold("draft deletion requires exact 404 or 410 readback") from None
    raise RehearsalHold("draft still exists after deletion")


def save(output, receipt, *, token=""):
    serialized = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)
    if token:
        serialized = serialized.replace(token, "***")
    with (output / "REHEARSAL.json").open("x", encoding="utf-8") as stream:
        stream.write(serialized)
        stream.write("\n")
