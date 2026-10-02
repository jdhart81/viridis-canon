#!/usr/bin/env python3
"""Label public claims from existing Comparator certificates, never verify Lean.

Certificate inspection only checks the issuer's recorded evidence and current
bytes. The Comparator remains the sole verifier of record.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

CONJECTURE_LABEL = "CONJECTURE — not machine-verified"
DISCLAIMER = ("Machine-checked: logical validity given the stated model. "
              "NOT an empirical validation of the model's assumptions.")


def read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return value


def ledger_entities(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    """Use the two ledger tables; never recreate status from directory names."""
    result = []
    for key in ("file_entities", "run_entities"):
        values = ledger.get(key)
        if not isinstance(values, list):
            raise ValueError(f"ledger is missing its {key} table")
        if any(not isinstance(value, dict) for value in values):
            raise ValueError(f"ledger {key} contains a malformed entity")
        result.extend(values)
    return result


def tree_root(ledger: dict[str, Any]) -> Path:
    value = ledger.get("tree_root") or ledger.get("scan_root")
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError("ledger must stamp an absolute tree_root")
    return Path(value).resolve(strict=True)


def find_entity(ledger: dict[str, Any], path: Path, entity_id: str | None = None) -> dict[str, Any]:
    root = tree_root(ledger)
    absolute = path.resolve(strict=True)
    matches = []
    for entity in ledger_entities(ledger):
        if entity_id is not None:
            matched = entity.get("id") == entity_id
        else:
            value = entity.get("path")
            matched = isinstance(value, str) and (root / value).resolve() == absolute
        if matched:
            matches.append(entity)
    if len(matches) != 1:
        raise ValueError(f"artifact must match exactly one ledger entity, found {len(matches)}")
    return matches[0]


def inspect_entity_certificate(
    entity: dict[str, Any], ledger: dict[str, Any],
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Recheck provenance using the shared ledger consumer, with no trust fallback."""
    if entity.get("status") != "CERTIFIED" or entity.get("certificate_valid") is not True:
        raise ValueError("ledger entity does not hold CERTIFIED certificate status")
    if entity.get("has_sorry") is True or entity.get("status") == "UNSOUND":
        raise ValueError("quarantined or incomplete objects cannot carry certified claims")
    root = tree_root(ledger)
    cert_value = entity.get("certificate")
    if not isinstance(cert_value, str) or not cert_value:
        raise ValueError("ledger entity has no certificate path")
    cert_path = (root / cert_value).resolve(strict=True)
    if not cert_path.is_relative_to(root):
        raise ValueError("certificate path lies outside the canonical tree")
    if inspector is None:
        inspector = importlib.import_module("certificate_inspection").inspect_certificate
    inspected = inspector(cert_path, root)
    if not isinstance(inspected, dict):
        raise ValueError("certificate inspection returned malformed evidence")
    valid = inspected.get("certificate_valid", inspected.get("valid"))
    if valid is not True:
        reasons = inspected.get("reasons", [])
        raise ValueError("certificate failed current byte/provenance inspection: " + str(reasons))
    expected_run = entity.get("id")
    if isinstance(expected_run, str) and re.fullmatch(r"Run-\d+", expected_run):
        source = re.match(r"^Run-(\d+)(?:[_-]|$)", str(inspected.get("source_run", "")))
        if source is None or f"Run-{int(source.group(1)):03d}" != expected_run:
            raise ValueError("certificate is bound to a different run entity")
    elif isinstance(entity.get("path"), str) and Path(entity["path"]).suffix == ".lean":
        import hashlib
        source_path = (root / entity["path"]).resolve(strict=True)
        actual_hash = hashlib.sha256(source_path.read_bytes()).hexdigest()
        if actual_hash != entity.get("sha256") or actual_hash != inspected.get("candidate_sha256"):
            raise ValueError("file entity bytes are not the current certified candidate")
    return inspected


def _names(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(v, str) or not v for v in value):
        raise ValueError(f"certificate lacks {label}")
    if len(set(value)) != len(value):
        raise ValueError(f"certificate contains duplicate {label}")
    return value


def _one_name(value: Any, names: list[str], label: str) -> str:
    if not isinstance(value, str) or not value or re.fullmatch(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*", value) is None:
        raise ValueError(f"{label} must name exactly one Lean declaration")
    matches = [name for name in names if name == value or name.endswith("." + value)]
    if len(matches) != 1:
        raise ValueError(f"{label} must bind exactly one certified declaration, found {len(matches)}")
    return matches[0]


def _static_vacuity(inspection: dict[str, Any], entity: dict[str, Any]) -> bool:
    # This is an early rejection of already-recorded static flags, not a proof.
    for value in (inspection, entity):
        if value.get("vacuous") is True or value.get("vacuous_declarations"):
            return True
        flags = value.get("static_flags", value.get("flags", []))
        if isinstance(flags, list) and any("vacu" in str(flag).lower() or "unsatisf" in str(flag).lower() for flag in flags):
            return True
    return False


def _check_inventory(
    inspection: dict[str, Any], ledger: dict[str, Any], results: list[dict[str, Any]],
    certified_theorems: list[str],
) -> list[dict[str, Any]]:
    """Check public formal claim completeness against the existing sealed inventory."""
    sealed = inspection.get("sealed_paper_inputs")
    binding = sealed.get("SEALED_CLAIM_INVENTORY.json") if isinstance(sealed, dict) else None
    if not isinstance(binding, dict):
        raise ValueError("bound SEALED_CLAIM_INVENTORY.json is required to establish claim completeness")
    resolve_binding = importlib.import_module("certificate_inspection").resolve_binding
    inventory_path = resolve_binding(binding, tree_root(ledger))
    inventory = read_object(inventory_path)
    claims = inventory.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("sealed claim inventory must enumerate its claims")
    formal_seen: set[str] = set()
    unverified = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
            raise ValueError(f"sealed claim inventory item {index} is malformed")
        evidence_class = claim.get("evidence_class")
        if evidence_class in {"FORMAL_TARGET", "FORMALLY_VERIFIED"}:
            english = claim["claim"]
            if english in formal_seen:
                raise ValueError("sealed inventory repeats a public formal claim")
            formal_seen.add(english)
            target = claim.get("lean_theorem", claim.get("aristotle_target"))
            expected = _one_name(target, certified_theorems, "sealed inventory theorem")
            matches = [result for result in results if result.get("english_claim") == english]
            if len(matches) != 1 or matches[0].get("status") != "PASS" or matches[0].get("lean_theorem") != expected:
                raise ValueError(f"sealed public formal claim lacks its exact unique binding: {english}")
        elif evidence_class in {"NUMERIC", "DEFERRED", "CONJECTURED"}:
            unverified.append({"id": claim.get("id"), "english_claim": claim["claim"],
                               "evidence_class": evidence_class, "verification_status": "NOT_FORMALLY_VERIFIED",
                               "empirical_validation": "NOT_ESTABLISHED_BY_LEAN_CERTIFICATE"})
        else:
            raise ValueError(f"unknown sealed inventory evidence_class: {evidence_class!r}")
    if not formal_seen:
        raise ValueError("sealed inventory contains no public formal claims")
    if {result.get("english_claim") for result in results} != formal_seen:
        raise ValueError("claim binding contains claims absent from the sealed formal inventory")
    return unverified


def check_bindings(
    binding: dict[str, Any], entity: dict[str, Any], ledger: dict[str, Any], *,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "entity_id": entity.get("id"), "status": "HOLD", "verification_status": "CONJECTURE",
        "label": CONJECTURE_LABEL, "disclaimer": DISCLAIMER, "claims": [], "reasons": [],
        "local_lean_execution": False, "unverified_claims": [],
    }
    try:
        inspection = inspect_entity_certificate(entity, ledger, inspector)
        theorems = _names(inspection.get("certified_theorems", inspection.get("theorems")), "certified theorem contract")
        witnesses = _names(inspection.get("nonvacuity", inspection.get("nonvacuity_obligations")), "certified nonvacuity contract")
        if _static_vacuity(inspection, entity):
            raise ValueError("vacuous conclusions or unsatisfiable hypotheses cannot carry certified claims")
        candidate_path = inspection.get("candidate_path")
        if not isinstance(candidate_path, str):
            raise ValueError("certificate inspection lacks its bound candidate path")
        scanner = importlib.import_module("static_pregate").scan
        candidate_scan = scanner(Path(candidate_path))
        if not isinstance(candidate_scan, dict) or candidate_scan.get("static_pass") is not True:
            raise ValueError("bound candidate failed the advisory static pre-gate")
        claims = binding.get("claims")
        if not isinstance(claims, list) or not claims:
            raise ValueError("claim_binding must enumerate at least one public claim")
        english_seen: set[str] = set()
        for index, claim in enumerate(claims):
            outcome: dict[str, Any] = {"index": index, "status": "HOLD", "reasons": []}
            result["claims"].append(outcome)
            try:
                if not isinstance(claim, dict):
                    raise ValueError("claim must be a JSON object")
                english = claim.get("english_claim", claim.get("english"))
                if not isinstance(english, str) or not english.strip():
                    raise ValueError("public English claim is missing")
                if "english_claim" in claim and "english" in claim and claim["english_claim"] != claim["english"]:
                    raise ValueError("English claim aliases disagree")
                if english in english_seen:
                    raise ValueError("a public claim is bound more than once")
                english_seen.add(english)
                outcome["english_claim"] = english
                outcome["lean_theorem"] = _one_name(claim.get("lean_theorem"), theorems, "lean_theorem")
                outcome["nonvacuity_obligation"] = _one_name(claim.get("nonvacuity_obligation"), witnesses, "nonvacuity_obligation")
                fidelity = claim.get("model_fidelity")
                if not isinstance(fidelity, dict):
                    raise ValueError("model_fidelity is missing")
                for key in ("defined", "empirically_identified"):
                    symbols = fidelity.get(key)
                    if not isinstance(symbols, list) or any(not isinstance(s, str) or not s.strip() for s in symbols):
                        raise ValueError(f"model_fidelity.{key} must explicitly list its symbols")
                    if len(set(symbols)) != len(symbols):
                        raise ValueError(f"model_fidelity.{key} contains duplicate symbols")
                if not fidelity["defined"] and not fidelity["empirically_identified"]:
                    raise ValueError("model_fidelity must identify at least one model symbol")
                if set(fidelity["defined"]) & set(fidelity["empirically_identified"]):
                    raise ValueError("model symbols cannot be both defined and empirically identified")
                if claim.get("disclaimer") != DISCLAIMER:
                    raise ValueError("the exact INV-4 model-validity disclaimer is required")
                outcome["model_fidelity"] = fidelity
                outcome["disclaimer"] = DISCLAIMER
                outcome["status"] = "PASS"
            except (TypeError, ValueError) as exc:
                outcome["reasons"].append(str(exc))
        failed = [item for item in result["claims"] if item["status"] != "PASS"]
        if failed:
            result["reasons"].extend(f"claim {item['index']}: {reason}" for item in failed for reason in item["reasons"])
        else:
            result["unverified_claims"] = _check_inventory(inspection, ledger, result["claims"], theorems)
            result.update(status="PASS", verification_status="CERTIFIED", label="CERTIFIED")
    except Exception as exc:
        # A missing helper, malformed input or unavailable receipt is a HOLD.
        result["reasons"].append(f"{type(exc).__name__}: {exc}")
    return result


def check_run(
    run: Path, ledger: dict[str, Any], *, entity_id: str | None = None,
    inspector: Callable[[Path, Path], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    try:
        entity = find_entity(ledger, run, entity_id)
        binding = read_object(run / "claim_binding.json")
        return check_bindings(binding, entity, ledger, inspector=inspector)
    except Exception as exc:
        return {"entity_id": entity_id, "status": "HOLD", "verification_status": "CONJECTURE",
                "label": CONJECTURE_LABEL, "disclaimer": DISCLAIMER, "claims": [],
                "reasons": [f"{type(exc).__name__}: {exc}"], "local_lean_execution": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--entity-id")
    args = parser.parse_args(argv)
    try:
        result = check_run(args.run, read_object(args.ledger), entity_id=args.entity_id)
    except Exception as exc:
        result = {"status": "HOLD", "verification_status": "CONJECTURE", "label": CONJECTURE_LABEL,
                  "disclaimer": DISCLAIMER, "reasons": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
