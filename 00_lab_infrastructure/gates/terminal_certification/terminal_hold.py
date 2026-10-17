"""Read-only dispatch exclusion for an exact, reviewed terminal premise HOLD.

This does not certify a run, clear certification debt, or admit publication.
New receipts require an independently reviewed source/allowlist update.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys
import types


TRUSTED_RECEIPTS = {
    "Run-194": (
        "PREMISE_DECLARATION_HOLD_ENGINE_20261015.json",
        "0c03ddd7ff286fb114d19354616b04006529c3bf650bf21936ed6e695737c065",
    ),
}
CHECKER_SHA256 = "e00404ad578efa7dcd9299a5d947be594f36c15e53fd44479d22d578caab5137"
TITLE_SHA256 = "5c9981fe2536a6cde3c8a1d2e7cdc9684c1369aeb145be4fda635c8af8dfec81"
ALIGNER_SHA256 = "d8d06e582d80bddae73dbb68a23a866ed8cac241f5c9780c3bc779a50fcd4870"
BOUND_FILES = {
    "request_sha256": "ENGINE3_VERIFICATION_REQUEST.json",
    "formal_statement_sha256": "VERIFICATION_STATEMENT.lean",
    "candidate_sha256": "VERIFICATION_CANDIDATE.lean",
    "sealed_manifest_sha256": "SEALED_RUN_MANIFEST.json",
    "sealed_inventory_sha256": "SEALED_CLAIM_INVENTORY.json",
    "sealed_paper_tex_sha256": "SEALED_paper.tex",
}


def _bytes(path: Path) -> bytes:
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("symlink in terminal evidence ancestry")
    if not path.is_file() or path.stat().st_size > 4_000_000:
        raise ValueError("missing or oversized terminal evidence")
    return path.read_bytes()


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object(data: bytes) -> dict:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate terminal evidence key")
            result[key] = value
        return result
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError("terminal evidence must be a JSON object")
    return value


def _checker_sources() -> dict[Path, bytes]:
    gate_root = Path(__file__).resolve().parent.parent
    sources = {
        gate_root / "premise_declaration.py": CHECKER_SHA256,
        gate_root / "inv9_title_basis.py": TITLE_SHA256,
    }
    aligners = [gate_root.parent / "engine3_align_challenge.py",
                gate_root.parent.parent / "comparator-deploy/engine3_align_challenge.py"]
    present = [path for path in aligners if path.is_file()]
    if len(present) != 1:
        raise ValueError("unchanged checker parser missing or ambiguous")
    sources[present[0]] = ALIGNER_SHA256
    loaded = {path: _bytes(path) for path in sources}
    if any(_sha(loaded[path]) != expected for path, expected in sources.items()):
        raise ValueError("terminal checker source pin mismatch")
    return loaded


def _pure_check(sources: dict[Path, bytes], documents: dict[str, bytes]) -> dict:
    # Execute only the already checked static checker definitions. A foreign
    # sys.path or previously imported title helper cannot replace this closure.
    title_path = next(path for path in sources if path.name == "inv9_title_basis.py")
    checker_path = next(path for path in sources if path.name == "premise_declaration.py")
    title = types.ModuleType("inv9_title_basis")
    title.__file__ = str(title_path)
    exec(compile(sources[title_path], str(title_path), "exec"), title.__dict__)
    checker = types.ModuleType("_terminal_pinned_premise")
    checker.__file__ = str(checker_path)
    previous = sys.modules.get("inv9_title_basis")
    sys.modules["inv9_title_basis"] = title
    try:
        exec(compile(sources[checker_path], str(checker_path), "exec"), checker.__dict__)
        request = _object(documents["ENGINE3_VERIFICATION_REQUEST.json"])
        names = request["expected_theorem_names"]
        obligations = request.get("nonvacuity_obligations", [])
        if (not isinstance(names, list) or not names or
                not all(isinstance(name, str) and name for name in names) or
                len(set(names)) != len(names) or not isinstance(obligations, list) or
                not set(obligations).issubset(names)):
            raise ValueError("invalid frozen theorem contract")
        targets = [name for name in names if name not in obligations]
        if not targets:
            raise ValueError("no proof target")
        return checker.evaluate(
            _object(documents["SEALED_RUN_MANIFEST.json"]),
            _object(documents["SEALED_CLAIM_INVENTORY.json"]),
            formal_statement=documents["VERIFICATION_STATEMENT.lean"].decode("utf-8"),
            candidate=documents["VERIFICATION_CANDIDATE.lean"].decode("utf-8"),
            paper_text=documents["SEALED_paper.tex"].decode("utf-8"),
            theorem_names=targets, required=True,
        )
    finally:
        if previous is None:
            sys.modules.pop("inv9_title_basis", None)
        else:
            sys.modules["inv9_title_basis"] = previous


def terminal_hold(package: Path, certificate_root: Path) -> dict | None:
    """Return authenticated exclusion evidence, or preserve ordinary FIFO work.

    Only the selected package's unchanged manifest and frozen Comparator object
    may be excluded. A successor, changed input, malformed receipt, checker
    error, or missing pin never becomes a terminal dispatch exclusion.
    """
    try:
        package = Path(package)
        certificate_root = Path(certificate_root)
        run_id = package.name
        if not re.fullmatch(r"Run-[0-9]{3,}", run_id) or run_id not in TRUSTED_RECEIPTS:
            return None
        filename, trusted_sha = TRUSTED_RECEIPTS[run_id]
        folder = certificate_root / run_id
        receipt_path = folder / filename
        receipt_bytes = _bytes(receipt_path)
        if _sha(receipt_bytes) != trusted_sha:
            return None
        receipt = _object(receipt_bytes)
        if not (receipt.get("schema_version") == "VRS-CERTIFICATION-PREMISE-HOLD-1"
                and receipt.get("run_id") == run_id
                and receipt.get("status") == "HOLD_PREMISE_DECLARATION"
                and receipt.get("terminal_for_sealed_object") is True
                and receipt.get("transport_performed_this_checkpoint") is False
                and receipt.get("certificate_issued") is False):
            return None
        bindings = receipt["bindings"]
        if bindings.get("premise_checker_sha256") != CHECKER_SHA256:
            return None
        documents = {filename: _bytes(folder / filename) for filename in BOUND_FILES.values()}
        if any(_sha(documents[filename]) != bindings.get(key)
               for key, filename in BOUND_FILES.items()):
            return None
        if _sha(_bytes(package / "PAPER_PACKAGE_MANIFEST.json")) != bindings["sealed_manifest_sha256"]:
            return None
        request = _object(documents["ENGINE3_VERIFICATION_REQUEST.json"])
        if request.get("source_run") != run_id or request.get("local_lean_execution") is not False:
            return None
        for key, filename in BOUND_FILES.items():
            if key != "request_sha256" and request["input_sha256"].get(filename) != bindings[key]:
                return None
        sources = _checker_sources()
        result = _pure_check(sources, documents)
        if not (result == receipt.get("checker_result")
                and result.get("status") == "HOLD"
                and result.get("local_lean_execution") is False
                and result.get("certifies") is False
                and result.get("reasons") == ["PREMISE_DECLARATION_MISSING_OR_UNKNOWN"]
                and receipt.get("reason") == result["reasons"][0]):
            return None
        # Detect drift during the read/check window without rewriting evidence.
        reread = {path: _bytes(path) for path in sources}
        if reread != sources or _bytes(receipt_path) != receipt_bytes:
            return None
        if any(_bytes(folder / filename) != data for filename, data in documents.items()):
            return None
        if _sha(_bytes(package / "PAPER_PACKAGE_MANIFEST.json")) != bindings["sealed_manifest_sha256"]:
            return None
        return {"run_id": run_id, "receipt_sha256": trusted_sha,
                "request_sha256": bindings["request_sha256"],
                "status": "TERMINAL_PREMISE_HOLD", "certifies": False,
                "clears_certification_debt": False, "publication_admitted": False}
    except (OSError, ValueError, KeyError, TypeError, AttributeError, UnicodeError):
        return None
