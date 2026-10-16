"""Scheduler-owned reservations and immutable verification results.

This module has no transport, certificate issuer, publisher or scheduler. Only
the existing scheduler may call it. Reserving precedes transport; an uncertain
transport remains reserved until its original request is reconciled. A result
is only a holding-area record, never publication or oldest-target credit.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import sys
from typing import Callable


class LivenessHold(RuntimeError):
    pass


SCHEDULER_ID = "viridis-nightly-science-generator"
DIGEST = re.compile(r"[a-f0-9]{64}")
RUN = re.compile(r"Run-[0-9]{3,}")


def digest_json(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def file_digest(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise LivenessHold("HOLD_EVIDENCE_FILE")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recorded_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def durable_file_sync(descriptor: int) -> None:
    os.fsync(descriptor)
    # macOS fsync may leave data in the drive cache. Dispatch waits for the
    # stronger flush where the platform exposes it; errors fail closed.
    if sys.platform == "darwin" and hasattr(fcntl, "F_FULLFSYNC"):
        fcntl.fcntl(descriptor, fcntl.F_FULLFSYNC)


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_mkdir(path: Path) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir()
        fsync_directory(directory.parent)


def validate_terminal_rejection(identity: RequestIdentity, path: Path, expected: str) -> dict:
    """Authenticate a failed request from the deployed failure evidence envelope."""
    if file_digest(path) != expected:
        raise LivenessHold("HOLD_REJECTION_RECEIPT_HASH")
    cloud = json.loads(path.read_text())
    if any(cloud.get(key) != value for key, value in {
        "standard": "VRS-COMPARATOR-DUAL-KERNEL-1", "status": "HOLD",
        "provider": "VIRIDIS_COMPARATOR_CLOUD", "project": "viridis-lean-4.28",
        "local_lean_execution": False, "credentials_recorded": False}.items()):
        raise LivenessHold("HOLD_REJECTION_PROVIDER")
    for field, expected_hash in (("request", identity.request_sha256),
                                 ("formal_statement", identity.statement_sha256),
                                 ("candidate", identity.candidate_sha256)):
        binding = cloud.get(field, {})
        if not isinstance(binding, dict) or binding.get("sha256") != expected_hash:
            raise LivenessHold("HOLD_REJECTION_BINDING")
        bound_path = Path(binding.get("path", ""))
        if not bound_path.is_absolute() or file_digest(bound_path) != expected_hash:
            raise LivenessHold("HOLD_REJECTION_BINDING")
    request = json.loads(Path(cloud["request"]["path"]).read_text())
    if (request.get("source_run") != identity.run_id
            or hashlib.sha256(str(request.get("toolchain", "")).encode()).hexdigest() != identity.toolchain_sha256
            or hashlib.sha256(str(request.get("mathlib_rev", "")).encode()).hexdigest() != identity.mathlib_sha256):
        raise LivenessHold("HOLD_REJECTION_REQUEST_IDENTITY")
    response = cloud.get("provider_response")
    if not isinstance(response, dict) or response.get("type") != "verification-failed" or response.get("project") != cloud["project"]:
        raise LivenessHold("HOLD_REJECTION_NOT_TERMINAL")
    canonical = (json.dumps(response, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if hashlib.sha256(canonical).hexdigest() != cloud.get("provider_response_sha256"):
        raise LivenessHold("HOLD_REJECTION_RESPONSE_HASH")
    request_id = response.get("requestId")
    execution = response.get("executionEvidence", {})
    delivery = execution.get("delivery", {}) if isinstance(execution, dict) else {}
    if (not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200
            or not isinstance(delivery, dict) or delivery.get("mode") != "FRESH_EXECUTION"
            or delivery.get("servedForRequestId") != request_id):
        raise LivenessHold("HOLD_REJECTION_SERVED_REQUEST_ID")
    terminal = response.get("terminationDiagnostics", {})
    if not isinstance(terminal, dict) or not isinstance(terminal.get("records"), list):
        raise LivenessHold("HOLD_REJECTION_TERMINAL_EVIDENCE")
    records = terminal["records"]
    if (terminal.get("standard") != "VRS-COMPARATOR-TERMINATION-1"
            or terminal.get("capture_status") != "RECORDED"
            or terminal.get("requestId") != response.get("requestId")
            or not any(isinstance(row, dict) and row.get("requestId") == response.get("requestId")
                and row.get("phase") in {"compile-Challenge", "compile-Solution", "collect-theorems", "compare-kernels"}
                and type(row.get("exitCode")) is int and row["exitCode"] != 0
                and row.get("reason") == "exited" and row.get("signal") is None
                and row.get("guard_fired") is False and isinstance(row.get("end"), str) and row["end"]
                for row in records)):
        raise LivenessHold("HOLD_REJECTION_TERMINAL_EVIDENCE")
    return cloud



def certification_action(certificate_root: Path) -> str:
    """An active S8 lane owns dispatch; malformed present policy also fails closed."""
    policy = certificate_root.parent / "PARALLEL_CERTIFICATION_POLICY.json"
    if not policy.exists():
        return "CERTIFY_COMPARATOR_FIFO"
    try:
        value = json.loads(policy.read_text())
        if isinstance(value, dict) and value.get("active") is False:
            return "CERTIFY_COMPARATOR_FIFO"
    except (OSError, ValueError, TypeError):
        pass
    return "DRAIN_SCHEDULER_CERTIFICATION_LANE"


def writer_hold_code(stdout: str) -> str:
    """Surface only an authenticated writer's bounded HOLD identifier.

    Arbitrary stdout and error prose may contain credentials, so never copy
    either into the executor error. Existing output hashes preserve identity.
    """
    try:
        value = json.loads(stdout)
    except (ValueError, TypeError):
        return "UNAVAILABLE"
    if not isinstance(value, dict) or value.get("status") != "HOLD":
        return "UNAVAILABLE"
    error = value.get("error")
    match = re.match(r"(HOLD_[A-Z][A-Z0-9_]{0,99})(?=:|$)", error) if isinstance(error, str) else None
    return match.group(1) if match else "UNAVAILABLE"


def redacted_stderr_tail(stderr: str) -> str:
    """Retain bounded diagnostics while removing URLs and credential-shaped text."""
    text = str(stderr)[-2000:]
    text = re.sub(r"(?i)bearer\s+[^\s]+|https?://[^\s]+", "[REDACTED]", text)
    text = re.sub(r"[A-Za-z0-9_+/=.\-]{24,}", "[REDACTED]", text)
    return text[-1000:]


def paper_review_pending(root: Path) -> bool:
    """Inspect final paper wording; never rewrite a reviewed or sealed package."""
    manifest = json.loads((root / "PAPER_PACKAGE_MANIFEST.json").read_text())
    source_name = manifest.get("artifacts", {}).get("paper_source")
    if not isinstance(source_name, str) or not source_name:
        # Match the existing packager's support for legacy review formats.
        # Its full binding validator remains authoritative below this routing check.
        return False
    source = root / source_name
    try:
        source.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise LivenessHold("HOLD_PAPER_SOURCE_ESCAPE") from exc
    if root.is_symlink() or any(root.joinpath(*Path(source_name).parts[:index]).is_symlink()
                                for index in range(1, len(Path(source_name).parts) + 1)):
        raise LivenessHold("HOLD_PAPER_SOURCE_SYMLINK")
    text = source.read_text()
    try:
        from verification_state_metadata import reviewed_text_contradictions
    except ImportError:
        reviewed_text_contradictions = None
    if reviewed_text_contradictions is not None:
        return bool(reviewed_text_contradictions(text))
    return bool(re.search(
        r"\bindependent\s+(?:paper|manuscript)\s+review\s+remains?\s+pending\b"
        r"|\bmanuscript\s+remains?\s+subject\s+to\s+later\s+independent\s+review\b", text, re.I))


@dataclass(frozen=True)
class RequestIdentity:
    run_id: str
    request_sha256: str
    candidate_sha256: str
    statement_sha256: str
    toolchain_sha256: str
    mathlib_sha256: str

    def __post_init__(self):
        if not isinstance(self.run_id, str) or not RUN.fullmatch(self.run_id):
            raise LivenessHold("HOLD_RUN_IDENTITY")
        for name, value in asdict(self).items():
            if name != "run_id" and (not isinstance(value, str) or not DIGEST.fullmatch(value)):
                raise LivenessHold("HOLD_REQUEST_BINDING")

    @property
    def key(self) -> str:
        return digest_json(asdict(self))


def immutable_json(path: Path, value: dict) -> dict:
    """Exclusive same-filesystem creation; identical replay is read-only."""
    encoded = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if path.is_symlink() or path.parent.is_symlink():
        raise LivenessHold("HOLD_RECEIPT_SYMLINK")
    durable_mkdir(path.parent)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            durable_file_sync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != encoded:
                raise LivenessHold("HOLD_IMMUTABLE_RECEIPT_COLLISION")
        # A successful file fsync does not make the new directory entry durable.
        # Dispatch authority must never escape before this link is persisted.
        fsync_directory(path.parent)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return value


def timed_record(path: Path, value: dict) -> dict:
    if path.is_symlink():
        raise LivenessHold("HOLD_RECEIPT_SYMLINK")
    existing = json.loads(path.read_text()) if path.exists() else None
    stamp = existing.get("recorded_at_utc") if existing else recorded_time()
    if not isinstance(stamp, str):
        raise LivenessHold("HOLD_RECORD_TIMESTAMP")
    return immutable_json(path, {**value, "recorded_at_utc": stamp})


class SchedulerLane:
    """One process owns all mutations during each existing-scheduler checkpoint."""
    def __init__(self, root: Path, scheduler_id: str = SCHEDULER_ID):
        if scheduler_id != SCHEDULER_ID:
            raise LivenessHold("HOLD_SCHEDULER_OWNER")
        self.root = Path(root).resolve()
        self.scheduler_id = scheduler_id
        self._owned = False

    @contextmanager
    def checkpoint(self):
        if self._owned:
            raise LivenessHold("HOLD_NESTED_CHECKPOINT")
        durable_mkdir(self.root)
        if self.root.is_symlink() or (self.root / "OWNER.lock").is_symlink():
            raise LivenessHold("HOLD_OWNER_SYMLINK")
        with (self.root / "OWNER.lock").open("a+") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise LivenessHold("HOLD_CONCURRENT_SCHEDULER") from exc
            self._owned = True
            try:
                yield self
            finally:
                self._owned = False
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _require_owner(self):
        if not self._owned:
            raise LivenessHold("HOLD_SCHEDULER_LOCK_REQUIRED")

    def _rows(self, directory: str) -> list[dict]:
        folder = self.root / directory
        if folder.is_symlink():
            raise LivenessHold("HOLD_RECEIPT_SYMLINK")
        result = []
        for path in sorted(folder.glob("*.json")):
            if path.is_symlink():
                raise LivenessHold("HOLD_RECEIPT_SYMLINK")
            value = json.loads(path.read_text())
            identity = RequestIdentity(**value["identity"])
            if path.stem != identity.key:
                raise LivenessHold("HOLD_RECEIPT_IDENTITY")
            if directory == "terminal":
                receipt = value.get("provider_receipt")
                if (value.get("standard") != "VRS-IMMUTABLE-REJECTED-REQUEST-1"
                        or not isinstance(receipt, str) or not Path(receipt).is_absolute()):
                    raise LivenessHold("HOLD_TERMINAL_RECEIPT_BINDING")
                cloud = validate_terminal_rejection(identity, Path(receipt), value.get("provider_receipt_sha256"))
                goal = value.get("failing_goal")
                output = str(cloud["provider_response"].get("output", ""))
                if value.get("provider_output_sha256") != hashlib.sha256(output.encode()).hexdigest():
                    raise LivenessHold("HOLD_REJECTION_OUTPUT_BINDING")
                if not isinstance(goal, str) or not goal.strip() or len(goal) > 32768 or goal not in output:
                    raise LivenessHold("HOLD_REJECTION_GOAL_BINDING")
            result.append(value)
        return result

    def reserve(self, identity: RequestIdentity, *, terminal_hold: bool = False) -> dict:
        self._require_owner()
        if terminal_hold:
            raise LivenessHold("HOLD_TERMINAL_OBJECT_NO_DISPATCH")
        requests = self._rows("requests")
        completed = {RequestIdentity(**row["identity"]).key
                     for folder in ("results", "terminal") for row in self._rows(folder)}
        for row in requests:
            previous = RequestIdentity(**row["identity"])
            if previous == identity:
                # Never return dispatch=True after a crash or transport ambiguity.
                return {"dispatch": False, "request": row}
            if previous.request_sha256 == identity.request_sha256:
                raise LivenessHold("HOLD_RUN_BINDING_DRIFT" if previous.run_id == identity.run_id else "HOLD_REQUEST_DIGEST_REUSED")
            if previous.run_id == identity.run_id and previous.key not in completed:
                raise LivenessHold("HOLD_PREDECESSOR_RECONCILIATION_REQUIRED")
        active = [row for row in requests if RequestIdentity(**row["identity"]).key not in completed]
        if len(active) >= 2:
            raise LivenessHold("HOLD_TWO_REQUEST_LIMIT")
        row = {"standard": "VRS-HASH-BOUND-RESERVATION-1", "scheduler_id": self.scheduler_id,
               "identity": asdict(identity), "recorded_at_utc": recorded_time()}
        immutable_json(self.root / "requests" / (identity.key + ".json"), row)
        return {"dispatch": True, "request": row}

    def accept(self, identity: RequestIdentity, result: dict,
               validate_certificate: Callable[[RequestIdentity, dict], bool]) -> dict:
        """Only accept an issuer-validated certificate with exact original bindings."""
        self._require_owner()
        if (self.root / "requests").is_symlink():
            raise LivenessHold("HOLD_RECEIPT_SYMLINK")
        path = self.root / "requests" / (identity.key + ".json")
        if path.is_symlink() or not path.is_file():
            raise LivenessHold("HOLD_RESERVATION_MISSING")
        request = json.loads(path.read_text())
        if request.get("identity") != asdict(identity) or result.get("identity") != asdict(identity):
            raise LivenessHold("HOLD_RESULT_BINDING_DRIFT")
        if any(row["identity"] == asdict(identity) for row in self._rows("terminal")):
            raise LivenessHold("HOLD_REJECTED_REQUEST_IMMUTABLE")
        if any(result.get(name) is not True for name in (
            "nanoda_accepted", "default_kernel_accepted", "zero_holes", "premise_gate", "nonvacuity_gate")):
            raise LivenessHold("HOLD_RESULT_SCIENCE_GATE")
        for name in ("certificate_sha256", "proof_sha256", "provider_receipt_sha256"):
            if not isinstance(result.get(name), str) or not DIGEST.fullmatch(result[name]):
                raise LivenessHold("HOLD_RESULT_ARTIFACT_BINDING")
        if validate_certificate(identity, result) is not True:
            raise LivenessHold("HOLD_ISSUER_CERTIFICATE_VALIDATION")
        value = {**result, "standard": "VRS-IMMUTABLE-VERIFIED-RESULT-1"}
        return timed_record(self.root / "results" / (identity.key + ".json"), value)

    def record_rejection(self, identity: RequestIdentity, provider_receipt: Path,
                         provider_receipt_sha256: str, failing_goal: str) -> dict:
        """Free only an authenticated terminal slot; the request may never retry."""
        self._require_owner()
        reservations = self._rows("requests")
        if not any(row["identity"] == asdict(identity) for row in reservations):
            raise LivenessHold("HOLD_RESERVATION_MISSING")
        if any(row["identity"] == asdict(identity) for row in self._rows("results")):
            raise LivenessHold("HOLD_ACCEPTED_REQUEST_IMMUTABLE")
        if (not isinstance(provider_receipt_sha256, str) or not DIGEST.fullmatch(provider_receipt_sha256)
                or not isinstance(failing_goal, str) or not failing_goal.strip()):
            raise LivenessHold("HOLD_REJECTION_EVIDENCE_REQUIRED")
        cloud = validate_terminal_rejection(identity, provider_receipt, provider_receipt_sha256)
        if failing_goal not in str(cloud["provider_response"].get("output", "")):
            raise LivenessHold("HOLD_REJECTION_GOAL_BINDING")
        value = {"standard": "VRS-IMMUTABLE-REJECTED-REQUEST-1", "identity": asdict(identity),
                 "provider_receipt_sha256": provider_receipt_sha256,
                 "provider_receipt": str(provider_receipt.resolve()), "failing_goal": failing_goal[:32768],
                 "provider_output_sha256": hashlib.sha256(str(cloud["provider_response"].get("output", "")).encode()).hexdigest()}
        return timed_record(self.root / "terminal" / (identity.key + ".json"), value)

    def eligible_dispatches(self, ordered: list[tuple[RequestIdentity, bool]]) -> list[dict]:
        """Caller supplies reviewed terminal holds; ambiguous reservations stay active."""
        self._require_owner()
        dispatched = []
        for identity, terminal_hold in ordered:
            if terminal_hold:
                continue
            try:
                reservation = self.reserve(identity)
            except LivenessHold as exc:
                if str(exc) == "HOLD_TWO_REQUEST_LIMIT":
                    break
                if str(exc) == "HOLD_PREDECESSOR_RECONCILIATION_REQUIRED":
                    continue
                raise
            if reservation["dispatch"]:
                dispatched.append(reservation)
        return dispatched

    def publication_prefix(self, ordered: list[RequestIdentity], admitted: set[str]) -> list[str]:
        """Every existing science/review/package/authority gate must supply admission."""
        self._require_owner()
        completed = {RequestIdentity(**row["identity"]).key for row in self._rows("results")}
        prefix = []
        for identity in ordered:
            if identity.key not in completed or identity.key not in admitted:
                break
            prefix.append(identity.run_id)
        return prefix


def oldest_target_credit(targets: list[str], certified_runs: set[str]) -> list[str]:
    """Do not weaken START's immutable named oldest-target predicate."""
    return [run for run in targets if run in certified_runs]


def scheduler_checkpoint(*, generation_due: bool, generation_step: Callable[[], object],
                         certification_step: Callable[[], object]) -> dict:
    """An existing-scheduler hook; a proof-lane HOLD cannot suppress a due run."""
    generation = generation_step() if generation_due else None
    try:
        certification = {"status": "COMPLETED", "result": certification_step()}
    except LivenessHold as exc:
        certification = {"status": "HOLD", "code": str(exc)}
    return {"generation": generation, "certification": certification}
