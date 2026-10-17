"""TEST ONLY source-derived binding/selection provider, never production admission.
The four functions below are exact AST bodies from the pinned provider; the
synthetic envelope is built locally and is never genuine Comparator evidence.
"""
from pathlib import Path
from typing import Any
import hashlib,json
CERTIFIED_STATUS='LEAN_ZERO_SORRY_CERTIFIED'


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path}: JSON root must be an object")
    return value

def binding_is_current(binding: object, control_root: Path) -> bool:
    """Resolve immutable bindings exactly as the foundry continuity gate does."""
    if not isinstance(binding, dict):
        return False
    path_value = binding.get("path")
    digest = binding.get("sha256")
    if not isinstance(path_value, str) or not isinstance(digest, str):
        return False
    path = Path(path_value)
    candidates = [path]
    if not path.is_absolute():
        candidates = [control_root / path, control_root / "RESEARCH_PIPELINE_v2" / path]
    for candidate in candidates:
        try:
            if candidate.is_file() and sha256_file(candidate) == digest:
                return True
        except OSError:
            continue
    return False

def current_certificate(control_root: Path, run_id: str) -> tuple[Path, dict[str, Any]] | None:
    root = control_root / "RESEARCH_PIPELINE_v2/lean_certificates" / run_id
    current: list[tuple[str, Path, dict[str, Any]]] = []
    for path in sorted(root.glob("LEAN_ZERO_SORRY_CERTIFICATE*.json")):
        try:
            certificate = read_json(path)
        except (OSError, json.JSONDecodeError, RuntimeError):
            continue
        if certificate.get("standard") != "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1":
            continue
        if certificate.get("status") != CERTIFIED_STATUS or certificate.get("run_id") != run_id:
            continue
        bindings = certificate.get("bindings")
        if not isinstance(bindings, dict):
            continue
        required = ["request", "independent_cloud_receipt"]
        if certificate.get("verification_standard") == "VRS-COMPARATOR-DUAL-KERNEL-1":
            required.extend(["formal_statement", "candidate_proof"])
        elif "aristotle_audit" in bindings:
            required.append("aristotle_audit")
        else:
            required.append("legacy_aristotle_audit")
        if any(not binding_is_current(bindings.get(name), control_root) for name in required):
            continue
        sealed = bindings.get("sealed_paper_inputs")
        if not isinstance(sealed, dict) or not sealed:
            continue
        if any(not binding_is_current(binding, control_root) for binding in sealed.values()):
            continue
        issued = str(certificate.get("issued_at_utc", ""))
        current.append((issued, path, certificate))
    if not current:
        return None
    _, path, certificate = max(current, key=lambda row: (row[0], row[1].name))
    return path, certificate
