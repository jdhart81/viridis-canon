#!/usr/bin/env python3
"""Verify a frozen Viridis Lean pair on the private dual-kernel droplet."""

from __future__ import annotations

import argparse
import datetime as dt
import contextvars
import functools
import locale
import os
import stat
import time
import uuid
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from engine3_align_challenge import align_challenge
from job_observation_policy import assess_job_observation


DEFAULT_HOST = "root@138.197.18.27"
DEFAULT_KEY = Path("/Users/justinhart/.ssh/codex_calm-reef-71f4_ed25519")
REMOTE_COMMAND = "/usr/local/bin/viridis-comparator-verify"
FORBIDDEN = re.compile(r"\b(?:sorry|admit|sorryAx)\b|\bunsafe\b|open\s+private")
DUAL_KERNEL_MARKERS = (
    "Nanoda kernel accepts the solution",
    "Lean default kernel accepts the solution",
    "Your solution is okay!",
)


class VerificationError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request_bound_path(request_path: Path, value: Any, label: str) -> tuple[Path, str]:
    if not isinstance(value, dict):
        raise VerificationError(f"missing {label} binding")
    filename = value.get("filename")
    digest = value.get("sha256")
    if not isinstance(filename, str) or Path(filename).name != filename or not isinstance(digest, str):
        raise VerificationError(f"invalid {label} filename/hash binding")
    path = request_path.parent / filename
    if not path.is_file() or sha256_file(path) != digest:
        raise VerificationError(f"{label} byte binding failed")
    return path, digest


def strip_lean_comments(source: str) -> str:
    output: list[str] = []
    index = 0
    depth = 0
    in_string = False
    while index < len(source):
        pair = source[index : index + 2]
        char = source[index]
        if depth:
            if pair == "/-":
                depth += 1
                index += 2
            elif pair == "-/":
                depth -= 1
                index += 2
            else:
                index += 1
            continue
        if not in_string and pair == "/-":
            depth = 1
            index += 2
            continue
        if not in_string and pair == "--":
            newline = source.find("\n", index)
            index = len(source) if newline < 0 else newline
            continue
        output.append(char)
        if char == '"' and (index == 0 or source[index - 1] != "\\"):
            in_string = not in_string
        index += 1
    if depth:
        raise VerificationError("candidate contains an unterminated Lean block comment")
    return "".join(output)


def contains_name(source: str, name: str) -> bool:
    return re.search(rf"\b(?:theorem|lemma|def)\s+(?:[\w.]+\.)?{re.escape(name)}\b", source) is not None


DIAGNOSTIC_CAP = 1024 * 1024
_RESOURCE_REQUEST = contextvars.ContextVar("comparator_resource_request", default={})
_DIAGNOSTICS_DIR = contextvars.ContextVar("comparator_attempt_diagnostics", default=None)


def _attempt_diagnostics(function):
    """Bind only the caller's known output parent; acceptance body is untouched."""
    @functools.wraps(function)
    def invoke(*args, **kwargs):
        output = kwargs.get("output_path")
        token = _DIAGNOSTICS_DIR.set(Path(output).parent if output is not None else None)
        resource_token = _RESOURCE_REQUEST.set(_resource_request(kwargs.get("request_path")))
        try:
            return function(*args, **kwargs)
        finally:
            _RESOURCE_REQUEST.reset(resource_token)
            _DIAGNOSTICS_DIR.reset(token)
    return invoke



def _resource_request(request_path):
    # Routing metadata from the existing frozen request; verification body stays byte-identical.
    # Invalid/missing requests retain their existing acceptance errors.
    try:
        source_run = json.loads(Path(request_path).read_text(encoding="utf-8")).get("source_run")
    except (OSError, ValueError, TypeError, AttributeError):
        return {}
    if not isinstance(source_run, str):
        return {}
    match = re.fullmatch(r"Run-(\d{3})(?:[_-].*)?", source_run)
    if match is None:
        return {}
    run_id = "Run-" + match.group(1)
    return {"runId": run_id, "resourceProfile": "foundational" if 900 <= int(match.group(1)) <= 999 else "nightly"}


def _persist_transport_diagnostics(stdout, stderr, *, started, elapsed, timeout,
                                   returncode=None, exception_class=None, complete=True):
    """Private failure evidence only; never part of a verification receipt."""
    base = _DIAGNOSTICS_DIR.get()
    if base is None:
        return
    base = Path(base)
    if ".." in base.parts:
        raise OSError("diagnostic traversal rejected")
    base = Path(os.path.abspath(base))
    if any(p.is_symlink() for p in (base, *base.parents)):
        raise OSError("diagnostic symlink rejected")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptors = []
    try:
        parent = os.open(base, flags)
        descriptors.append(parent)
        try:
            os.mkdir("transport-diagnostics", 0o700, dir_fd=parent)
        except FileExistsError:
            pass
        root = os.open("transport-diagnostics", flags, dir_fd=parent)
        descriptors.append(root)
        mode = os.fstat(root)
        if stat.S_IMODE(mode.st_mode) != 0o700 or mode.st_uid != os.getuid():
            raise OSError("insecure diagnostic directory")
        name = uuid.uuid4().hex
        os.mkdir(name, 0o700, dir_fd=root)
        directory = os.open(name, flags, dir_fd=root)
        descriptors.append(directory)
        manifest = {
            "standard": "VRS-TRANSPORT-FAILURE-DIAGNOSTICS-1",
            "started_at_utc": started,
            "ended_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "elapsed_seconds": elapsed, "configured_wait_seconds": timeout,
            "ssh_wall_clock_seconds": timeout + 60, "returncode": returncode,
            "signal": -returncode if returncode is not None and returncode < 0 else None,
            "exception_class": exception_class, "capture_complete": complete,
            "hash_scope": "captured bytes only; no assertion about uncaptured bytes",
            "streams": {}, "receipt_evidence": False,
        }
        def write(filename, data):
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=directory)
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
        for label, data in (("stdout", stdout), ("stderr", stderr)):
            if data is None:
                manifest["streams"][label] = {"available": False}
                continue
            if not isinstance(data, bytes):
                raise TypeError("diagnostics require raw bytes")
            retained = data[:DIAGNOSTIC_CAP]
            write(label + ".bin", retained)
            manifest["streams"][label] = {
                "available": True, "captured_length": len(data),
                "captured_sha256": hashlib.sha256(data).hexdigest(),
                "retained_length": len(retained),
                "retained_sha256": hashlib.sha256(retained).hexdigest(),
                "truncated": len(data) > len(retained), "filename": label + ".bin",
            }
        write("manifest.json", canonical_json_bytes(manifest))
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _text_mode_decode(data, encoding):
    # Same strict encoding and universal-newline conversion as subprocess text=True.
    return data.decode(encoding).replace("\r\n", "\n").replace("\r", "\n")


def ssh_transport(
    payload: dict[str, Any], host: str, key: Path, timeout: int
) -> tuple[int, dict[str, Any]]:
    command = [
        "ssh",
        "-i",
        str(key),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=30",
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        host,
        REMOTE_COMMAND,
    ]
    payload = {**payload, **_RESOURCE_REQUEST.get()}
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    began = time.monotonic()
    saved = False
    def capture(stdout, stderr, **metadata):
        nonlocal saved
        if saved:
            return
        saved = True
        try:
            _persist_transport_diagnostics(
                stdout, stderr, started=started, elapsed=time.monotonic() - began,
                timeout=timeout, **metadata)
        except Exception as logging_error:
            # Diagnostic storage failure cannot mask or alter the transport result.
            try:
                print("Comparator diagnostic capture unavailable: " + type(logging_error).__name__,
                      file=sys.stderr)
            except Exception:
                pass  # Even a closed diagnostic stderr must not mask the original failure.
    encoding = locale.getpreferredencoding(False)
    try:
        result = subprocess.run(
            command,
            input=json.dumps(payload).encode(encoding),
            capture_output=True,
            timeout=timeout + 60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        capture(getattr(exc, "stdout", None), getattr(exc, "stderr", None),
                exception_class=type(exc).__name__, complete=False)
        raise VerificationError(f"Comparator SSH transport failed: {type(exc).__name__}") from exc
    if result.returncode != 0:
        capture(result.stdout, result.stderr, returncode=result.returncode)
    try:
        stdout = _text_mode_decode(result.stdout, encoding)
        _text_mode_decode(result.stderr, encoding)
    except UnicodeError as exc:
        capture(result.stdout, result.stderr, returncode=result.returncode,
                exception_class=type(exc).__name__)
        raise
    try:
        response = json.loads(stdout)
    except json.JSONDecodeError as exc:
        capture(result.stdout, result.stderr, returncode=result.returncode,
                exception_class=type(exc).__name__)
        raise VerificationError("Comparator returned non-JSON data") from exc
    if not isinstance(response, dict):
        capture(result.stdout, result.stderr, returncode=result.returncode,
                exception_class="VerificationError")
        raise VerificationError("Comparator response root is not an object")
    return result.returncode, response


@_attempt_diagnostics

def verify(
    *,
    request_path: Path,
    formal_statement_path: Path,
    candidate_path: Path,
    output_path: Path,
    host: str = DEFAULT_HOST,
    key: Path = DEFAULT_KEY,
    timeout: int = 300,
    transport: Callable[[dict[str, Any], str, Path, int], tuple[int, dict[str, Any]]] = ssh_transport,
) -> dict[str, Any]:
    if output_path.exists():
        raise VerificationError(f"immutable verification receipt already exists: {output_path}")
    if not 1 <= timeout <= 1800:
        raise VerificationError("timeout must be between 1 and 1800 seconds")
    if not key.is_file():
        raise VerificationError(f"dedicated Comparator SSH key is missing: {key}")
    try:
        request = json.loads(request_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VerificationError(f"invalid frozen request: {request_path}") from exc
    if not isinstance(request, dict) or request.get("request_kind", "LEAN_PROOF") != "LEAN_PROOF":
        raise VerificationError("only a frozen LEAN_PROOF request can be certified")
    if request.get("toolchain") != "leanprover/lean4:v4.28.0":
        raise VerificationError("Comparator project is pinned to leanprover/lean4:v4.28.0")

    formal_statement = formal_statement_path.read_text(encoding="utf-8")
    candidate = candidate_path.read_text(encoding="utf-8")
    formal_hash = sha256_file(formal_statement_path)
    candidate_hash = sha256_file(candidate_path)
    input_hashes = request.get("input_sha256")
    if not isinstance(input_hashes, dict):
        raise VerificationError("frozen request has no input hash map")
    if input_hashes.get(formal_statement_path.name) != formal_hash:
        raise VerificationError("formal statement is not the exact request-bound input")
    if input_hashes.get(candidate_path.name) != candidate_hash:
        raise VerificationError("candidate is not the exact request-bound input")

    alignment_receipt: dict[str, Any] | None = None
    alignment_binding: dict[str, Any] | None = None
    alignment = request.get("statement_alignment")
    if alignment is None:
        if request.get("statement_contract_sha256") != formal_hash:
            raise VerificationError("formal statement does not match statement_contract_sha256")
    else:
        if not isinstance(alignment, dict) or alignment.get("standard") != "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1":
            raise VerificationError("unsupported statement alignment contract")
        sealed_path, sealed_hash = request_bound_path(
            request_path, alignment.get("sealed_statement"), "sealed statement"
        )
        receipt_path, receipt_hash = request_bound_path(
            request_path, alignment.get("receipt"), "statement alignment receipt"
        )
        if request.get("statement_contract_sha256") != sealed_hash:
            raise VerificationError("sealed statement does not match statement_contract_sha256")
        try:
            alignment_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise VerificationError("invalid statement alignment receipt") from exc
        if not isinstance(alignment_receipt, dict) or alignment_receipt.get("status") != "FROZEN":
            raise VerificationError("statement alignment receipt is not frozen")
        if alignment_receipt.get("standard") != "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1":
            raise VerificationError("statement alignment receipt has the wrong standard")
        if alignment_receipt.get("sealed_statement", {}).get("sha256") != sealed_hash:
            raise VerificationError("statement alignment receipt sealed hash mismatch")
        if alignment_receipt.get("aligned_challenge", {}).get("sha256") != formal_hash:
            raise VerificationError("statement alignment receipt challenge hash mismatch")
        if alignment_receipt.get("candidate", {}).get("sha256") != candidate_hash:
            raise VerificationError("statement alignment receipt candidate hash mismatch")
        alignment_binding = {
            "sealed_statement": {"path": str(sealed_path), "sha256": sealed_hash},
            "receipt": {"path": str(receipt_path), "sha256": receipt_hash},
        }
    forbidden = sorted(set(FORBIDDEN.findall(strip_lean_comments(candidate))))
    if forbidden:
        raise VerificationError("candidate contains forbidden proof constructs: " + ", ".join(forbidden))

    expected = request.get("expected_theorem_names", [])
    nonvacuity = request.get("nonvacuity_obligations", [])
    if not isinstance(expected, list) or not expected or not all(isinstance(v, str) for v in expected):
        raise VerificationError("frozen request has no expected theorem names")
    if alignment_receipt is not None:
        if alignment_receipt.get("expected_theorem_names") != expected:
            raise VerificationError("statement alignment theorem list mismatch")
        if alignment_receipt.get("target_signatures_match_sealed_statement") is not True:
            raise VerificationError("statement alignment did not preserve sealed signatures")
        if alignment_receipt.get("candidate_forbidden_constructs_empty") is not True:
            raise VerificationError("statement alignment candidate scan is not clean")
    # Named witnesses are mandatory in a production proof contract. Silently
    # filtering a prose/malformed obligation would falsely certify non-vacuity.
    if (
        not isinstance(nonvacuity, list)
        or not nonvacuity
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*", value) is None
            for value in nonvacuity
        )
        or len(set(nonvacuity)) != len(nonvacuity)
    ):
        raise VerificationError("nonvacuity_obligations must be a nonempty unique list of Lean declaration names")
    named_nonvacuity = nonvacuity
    missing_formal = [name for name in expected + named_nonvacuity if not contains_name(formal_statement, name)]
    missing_candidate = [name for name in expected + named_nonvacuity if not contains_name(candidate, name)]
    if missing_formal or missing_candidate:
        raise VerificationError(
            f"contract declarations missing; formal={missing_formal}, candidate={missing_candidate}"
        )

    # The author can write a plausible alignment receipt. Recompute its claim
    # from the frozen bytes before any egress; its boolean is not authority.
    targets = list(dict.fromkeys(expected + named_nonvacuity))
    sealed_source = sealed_path.read_text(encoding="utf-8") if alignment is not None else formal_statement
    try:
        recomputed_challenge, _ = align_challenge(sealed_source, candidate, targets)
    except ValueError as exc:
        raise VerificationError(f"independent frozen-context comparison failed: {exc}") from exc
    if alignment is not None and recomputed_challenge != formal_statement:
        raise VerificationError("aligned challenge differs from independently recomputed frozen context")

    requested_exports = expected + named_nonvacuity
    returncode, response = transport(
        {
            "challenge": formal_statement,
            "solution": candidate,
            "theoremNames": requested_exports,
        },
        host,
        key,
        timeout,
    )
    output = response.get("output", "")
    returned_exports = response.get("theoremNames", [])
    targeted_export_complete = bool(
        isinstance(returned_exports, list)
        and all(
            any(
                isinstance(returned, str)
                and (returned == requested or returned.endswith("." + requested))
                for returned in returned_exports
            )
            for requested in requested_exports
        )
    )
    markers = {marker: isinstance(output, str) and marker in output for marker in DUAL_KERNEL_MARKERS}
    observation = assess_job_observation(response, request, formal_hash, candidate_hash)
    passed = bool(
        returncode == 0
        and response.get("type") == "verification-ok"
        and response.get("project") == "viridis-lean-4.28"
        and targeted_export_complete
        and all(markers.values())
        and observation["status"] != "INVALID_OBSERVATION"
    )
    receipt = {
        "schema_version": "1.0",
        "standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
        "status": "VERIFIED" if passed else "HOLD",
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "provider": "VIRIDIS_COMPARATOR_CLOUD",
        "transport": "DEDICATED_SSH_TO_PRIVATE_LOOPBACK_SERVICE",
        "project": "viridis-lean-4.28",
        "request": {"path": str(request_path), "sha256": sha256_file(request_path)},
        "formal_statement": {
            "path": str(formal_statement_path),
            "sha256": formal_hash,
        },
        "candidate": {"path": str(candidate_path), "sha256": candidate_hash},
        "contract": {
            "source_run": request.get("source_run"),
            "candidate_id": request.get("candidate_id"),
            "expected_theorem_names": expected,
            "named_nonvacuity_obligations": named_nonvacuity,
            "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"],
            "permitted_sorries": [],
        },
        "checks": {
            "comparator_accepted": response.get("type") == "verification-ok",
            "nanoda_kernel_accepted": markers[DUAL_KERNEL_MARKERS[0]],
            "lean_kernel_accepted": markers[DUAL_KERNEL_MARKERS[1]],
            "solution_ok_terminal": markers[DUAL_KERNEL_MARKERS[2]],
            "candidate_forbidden_constructs_empty": not forbidden,
            "contract_declarations_present": True,
            "targeted_export_complete": targeted_export_complete,
            "independent_frozen_context_match": True,
        },
        "runtime_observation_assessment": observation,
        "provider_response_sha256": hashlib.sha256(canonical_json_bytes(response)).hexdigest(),
        "provider_response": response,
        "local_lean_execution": False,
        "credentials_recorded": False,
    }
    if alignment_binding is not None:
        receipt["statement_alignment"] = alignment_binding
        receipt["checks"]["sealed_statement_signature_alignment"] = True
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(output_path.name + ".tmp")
    temporary.write_bytes(canonical_json_bytes(receipt))
    temporary.replace(output_path)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--formal-statement", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        receipt = verify(
            request_path=args.request,
            formal_statement_path=args.formal_statement,
            candidate_path=args.candidate,
            output_path=args.output,
            host=args.host,
            key=args.key,
            timeout=args.timeout,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0 if receipt["status"] == "VERIFIED" else 2
    except (OSError, VerificationError) as exc:
        print(json.dumps({"status": "HOLD", "error": str(exc), "local_lean_execution": False}, indent=2))
        return 2


if __name__ == "__main__":
    sys.exit(main())
