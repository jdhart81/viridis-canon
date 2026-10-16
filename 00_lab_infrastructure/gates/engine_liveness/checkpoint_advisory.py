"""Bounded child-only Lean lint and SLO reporting; never changes a gate."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import uuid
from datetime import datetime, timezone
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
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
    if len(raw) > LIMIT:
        raise ValueError("advisory output budget")
    descriptors = [os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)]
    temporary = ".checkpoint-advisory-" + uuid.uuid4().hex
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
            raise ValueError("regular advisory output required")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
        os.fsync(parent)
    finally:
        try:
            os.unlink(temporary, dir_fd=descriptors[-1])
        except FileNotFoundError:
            pass
        for descriptor in reversed(descriptors):
            os.close(descriptor)


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


def _json(path: Path, root: Path, expected: str | None = None) -> dict:
    raw = read_regular(path, root)
    if expected is not None and hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("FIFO evidence binding")
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("FIFO evidence object required")
    return value


def _time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("FIFO timestamp timezone required")
    return parsed.astimezone(timezone.utc)


def _premise_head(path: Path, root: Path, run: str) -> dict:
    hold = _json(path, root)
    if (hold.get("schema_version") != "VRS-CERTIFICATION-PREMISE-HOLD-1"
            or hold.get("run_id") != run or hold.get("status") != "HOLD_PREMISE_DECLARATION"
            or hold.get("terminal_for_sealed_object") is not True
            or hold.get("certificate_issued") is not False
            or hold.get("checker_result", {}).get("status") != "HOLD"):
        raise ValueError("FIFO premise HOLD identity")
    folder = root / "RESEARCH_PIPELINE_v2/lean_certificates" / run
    bindings = hold.get("bindings", {})
    for key, name in (("request_sha256", "ENGINE3_VERIFICATION_REQUEST.json"),
                      ("formal_statement_sha256", "VERIFICATION_STATEMENT.lean"),
                      ("candidate_sha256", "VERIFICATION_CANDIDATE.lean")):
        if hashlib.sha256(read_regular(folder / name, root)).hexdigest() != bindings.get(key):
            raise ValueError("FIFO premise source drift")
    checker = root / "RESEARCH_PIPELINE_v2/verification_coverage_gates/premise_declaration.py"
    if hashlib.sha256(read_regular(checker, root)).hexdigest() != bindings.get("premise_checker_sha256"):
        raise ValueError("FIFO premise checker drift")
    return {"run_id": run, "held_since_utc": hold["recorded_at_utc"],
            "candidate_sha256": bindings["candidate_sha256"],
            "failing_goal": "UNAVAILABLE", "provider_receipt": "UNAVAILABLE",
            "terminal_hold": {"path": str(path), "sha256": hashlib.sha256(read_regular(path, root)).hexdigest()},
            "terminal_hold_detail": hold.get("detail", hold.get("reason", "UNAVAILABLE")),
            "evidence_basis": "HASH_BOUND_PREMISE_HOLD"}


def fifo_head(root: Path, current: dict, *, as_of: datetime | None = None) -> dict:
    """Derive the named head from immutable evidence; missing fields stay explicit."""
    now = as_of or datetime.now(timezone.utc)
    debt = current.get("science", {}).get("certification", {}).get("backlog_runs",
           current.get("certification", {}).get("remaining_debt", []))
    run = debt[0] if debt else "UNAVAILABLE"
    fields = {key: "UNAVAILABLE" for key in
              ("run_id", "held_since_utc", "failing_goal", "candidate_sha256", "provider_receipt")}
    fields.update(status="UNAVAILABLE", held_hours=None, held_seconds=None,
                  alert_threshold_hours=24, activation="REPORT_ONLY_NO_TRANSPORT_OR_FIFO_CHANGE")
    if isinstance(run, str) and re.fullmatch(r"Run-[0-9]{3,}", run):
        fields["run_id"] = run
    pipeline = root / "RESEARCH_PIPELINE_v2"
    supplied = pipeline / "PIPELINE_SLO_INPUTS.json"
    if supplied.exists():
        try:
            head = _json(supplied, root).get("fifo_head", {})
            if isinstance(head, dict) and head.get("run_id", run) == run:
                for key in fields.keys() & head.keys():
                    if head[key] is not None:
                        fields[key] = head[key]
                fields["evidence_basis"] = "SUPPLIED_SNAPSHOT"
        except Exception:
            pass
    if fields["run_id"] != "UNAVAILABLE":
        # A bounded, exact per-run folder is inspected; never a whole-tree scan.
        folder = pipeline / "lean_certificates" / run
        candidates = sorted(folder.glob("PREMISE_DECLARATION_HOLD*.json"))
        if len(candidates) > 20:
            raise ValueError("FIFO HOLD evidence budget")
        for path in candidates:
            try:
                fields.update(_premise_head(path, root, run))
                break
            except Exception:
                pass
        lane = pipeline / "parallel_certification"
        requests = sorted((lane / "requests").glob("*.json"))
        if len(requests) > 200:
            raise ValueError("FIFO reservation evidence budget")
        for path in requests:
            try:
                reservation = _json(path, root)
                identity = reservation["identity"]
                key = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if identity.get("run_id") != run or key != path.stem:
                    continue
                context = _json(lane / "contexts" / (key + ".json"), root)
                if context.get("identity") != identity:
                    continue
                entry = context["entry"]
                for name, field in (("request", "request_sha256"), ("formal_statement", "statement_sha256"), ("candidate", "candidate_sha256")):
                    binding = entry[name]
                    raw = read_regular(Path(binding["path"]), root)
                    if hashlib.sha256(raw).hexdigest() != identity[field] or binding["sha256"] != identity[field]:
                        raise ValueError("FIFO request source drift")
                fields.update(held_since_utc=reservation["recorded_at_utc"],
                              candidate_sha256=identity["candidate_sha256"], evidence_basis="HASH_BOUND_LANE_RESERVATION")
                terminal_path = lane / "terminal" / (key + ".json")
                if terminal_path.exists():
                    terminal = _json(terminal_path, root)
                    receipt = Path(terminal["provider_receipt"])
                    _json(receipt, root, terminal["provider_receipt_sha256"])
                    from scheduler_liveness import RequestIdentity, validate_terminal_rejection
                    cloud = validate_terminal_rejection(RequestIdentity(**identity), receipt, terminal["provider_receipt_sha256"])
                    if terminal.get("identity") != identity or cloud.get("request", {}).get("sha256") != identity["request_sha256"]:
                        raise ValueError("FIFO terminal identity")
                    goal = terminal.get("failing_goal")
                    if not isinstance(goal, str) or goal not in str(cloud.get("provider_response", {}).get("output", "")):
                        raise ValueError("FIFO terminal goal")
                    fields.update(failing_goal=goal, provider_receipt={"path": str(receipt), "sha256": terminal["provider_receipt_sha256"]})
                break
            except Exception:
                continue
    # Every required field exists even when no production input producer exists.
    for key in ("run_id", "held_since_utc", "failing_goal", "candidate_sha256", "provider_receipt"):
        if fields.get(key) is None:
            fields[key] = "UNAVAILABLE"
    try:
        seconds = (now - _time(fields["held_since_utc"])).total_seconds()
        if seconds < 0:
            raise ValueError("FIFO timestamp is in the future")
        fields.update(held_seconds=seconds, held_hours=round(seconds / 3600, 3))
        if seconds >= 24 * 3600:
            fields["status"] = "ALERT"
        else:
            fields["status"] = "BELOW_ALERT_THRESHOLD"
    except (ValueError, TypeError, AttributeError):
        fields.update(status="UNAVAILABLE", held_seconds=None, held_hours=None)
    fields["failing_goal_status"] = "UNAVAILABLE" if fields["failing_goal"] == "UNAVAILABLE" else "KNOWN"
    return fields


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
        value = {"standard": "VRS-PIPELINE-SLO-STATUS-1", "status": "ADVISORY_UNAVAILABLE",
                 "certifies": False, "checkpoint_sha256": hashlib.sha256(raw).hexdigest(),
                 "fifo_liveness": {"status": "UNAVAILABLE", "failing_goal": None},
                 "reason": "Bound advisory inputs or source unavailable; science state unchanged."}
    else:
        value = json.loads(read_regular(pipeline / "PIPELINE_SLO_STATUS.json", root))
    value["fifo_liveness"] = fifo_head(root, current)
    report(pipeline / "PIPELINE_SLO_STATUS.json", value, root)
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
