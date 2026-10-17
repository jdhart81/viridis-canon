"""Production draft-and-discard primitives; never admit a publication action."""
from datetime import datetime, timezone
from contextvars import ContextVar
from contextlib import contextmanager
from functools import wraps
import time
import hashlib
import json
import os
from pathlib import Path
import stat


_DEADLINE = ContextVar("production_rehearsal_deadline", default=None)
_REHEARSING = ContextVar("production_rehearsal_active", default=False)
_OUTPUT = ContextVar("production_rehearsal_output", default=None)


class RehearsalHold(ValueError):
    pass


def time_bounded(operation):
    @wraps(operation)
    def run(*args, **kwargs):
        token = _DEADLINE.set(time.monotonic() + 540)
        active = _REHEARSING.set(True)
        try:
            return operation(*args, **kwargs)
        finally:
            _DEADLINE.reset(token)
            _REHEARSING.reset(active)
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
    if rehearse or _REHEARSING.get():
        raise RehearsalHold("publication action is forbidden during rehearsal")
    if not str(identifier).isdigit():
        raise RehearsalHold("canonical draft identifier required")
    return "https://zenodo.org/api/deposit/depositions/" + str(identifier) + "/actions/publish"


def output_directory(output=None, *, forbidden_roots=()):
    root = os.environ.get("VIRIDIS_ENGINE_ROOT")
    if not root:
        raise RehearsalHold("VIRIDIS_ENGINE_ROOT must name the runbook engine directory")
    base = Path(root).resolve(strict=True) / "rehearsals"
    destination = Path(output).resolve() if output else base / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    if not destination.is_relative_to(base) or destination == base:
        raise RehearsalHold("rehearsal receipts must be inside ENGINE/rehearsals/<UTC>")
    if any(destination.is_relative_to(Path(path).resolve()) for path in forbidden_roots):
        raise RehearsalHold("rehearsal receipts must not be inside a bundle")
    destination.mkdir(parents=True, exist_ok=False)
    return destination


@contextmanager
def evidence_scope(output):
    token = _OUTPUT.set(Path(output))
    try:
        yield
    finally:
        _OUTPUT.reset(token)


def evidence_output():
    return _OUTPUT.get()


def tree_hashes(bundle):
    return {str(p.relative_to(bundle)): {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                                       "mode": stat.S_IMODE(p.stat().st_mode)}
            for p in sorted(Path(bundle).rglob("*")) if p.is_file()}


def discard(call, identifier):
    """Retry bounded cleanup, accept a gone draft and retain uncertain identity."""
    url = "https://zenodo.org/api/deposit/depositions/" + str(identifier)
    errors = []
    for attempt in range(2):
        try:
            call("DELETE", url, allow_not_found=True)
        except Exception as exc:
            errors.append({"operation":"DELETE","error_type":type(exc).__name__})
        statuses = []
        try:
            result = call("GET", url, allow_not_found=True, not_found_status=statuses)
        except Exception as exc:
            errors.append({"operation":"GET","error_type":type(exc).__name__})
        else:
            if result is None and len(statuses) == 1 and statuses[0] in (404, 410):
                return {"draft_id":str(identifier),"deleted":True,"http_status":statuses[0],"attempts":attempt+1}
    return {"draft_id":str(identifier),"deleted":False,"state":"HOLD_DRAFT_CLEANUP_REQUIRED","attempts":2,"errors":errors}


def save(output, receipt, *, token=""):
    serialized = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False)
    if token:
        serialized = serialized.replace(token, "***")
    with (output / "REHEARSAL.json").open("x", encoding="utf-8") as stream:
        stream.write(serialized)
        stream.write("\n")
