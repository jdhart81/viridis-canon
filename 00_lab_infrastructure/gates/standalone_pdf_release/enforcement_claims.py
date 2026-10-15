#!/usr/bin/env python3
"""Generate truthful status blocks and inspect source ASTs without importing them.

This is an instruction drift check, not publication admission or an installer.
Installed-source validation requires an explicit core root; portable CI checks
the repository sources and the claim model, and reports that scope honestly.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

BEGIN = "<!-- ENFORCEMENT-STATUS:BEGIN -->"
END = "<!-- END -->"
DEFAULT_CLAIMS = Path(__file__).with_name("ENFORCEMENT_CLAIMS.json")


class EnforcementDrift(ValueError):
    """A source observation or generated instruction differs from its claim."""


def call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return call_name(node.value) + "." + node.attr
    return ""


def direct_function_calls(source: bytes) -> dict[str, Counter]:
    """Count real calls in a named function, excluding nested function bodies."""
    result = {}
    tree = ast.parse(source)
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = Counter()

        def visit(node):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                return
            if isinstance(node, ast.Call):
                calls[call_name(node.func)] += 1
            for child in ast.iter_child_nodes(node):
                visit(child)

        for statement in function.body:
            visit(statement)
        result[function.name] = calls
    return result


def validate_source(source: bytes, entry: dict) -> dict:
    observed = direct_function_calls(source)
    digest = hashlib.sha256(source).hexdigest()
    if digest != entry["sha256"]:
        raise EnforcementDrift(f"source hash changed: {entry['path']}")
    gates = {"manuscript_pdf_gate.require_local", "manuscript_pdf_gate.require_public"}
    present = any(gates.intersection(calls) for calls in observed.values())
    if present != entry["gate_calls_present"]:
        raise EnforcementDrift(f"gate AST observation changed: {entry['path']}")
    for requirement in entry["required_calls"]:
        actual = observed.get(requirement["function"], Counter())[requirement["call"]]
        if actual < requirement.get("minimum", 1):
            raise EnforcementDrift(
                f"missing AST call {requirement['function']} -> {requirement['call']}: {entry['path']}"
            )
    return {"path": entry["path"], "sha256": digest, "gate_calls_present": present}


def validate_model(claims: dict) -> None:
    if claims.get("schema") != "VRS-ENFORCEMENT-CLAIMS-1":
        raise EnforcementDrift("unknown claims schema")
    if set(claims["routes"]) != {"digest_guard", "successor", "dated"}:
        raise EnforcementDrift("exactly the three publishing routes are required")
    for route_id, route in claims["routes"].items():
        sources = route["sources"]
        enforcing = [row for row in sources if row.get("enforcement_source", True)]
        if {row["root"] for row in enforcing} != {"repo", "core"}:
            raise EnforcementDrift(f"repo and installed sources required: {route_id}")
        actual = all(row["gate_calls_present"] for row in enforcing)
        if route["enforced"] is not actual:
            raise EnforcementDrift(f"route claim exceeds source observations: {route_id}")
        for row in enforcing:
            if row["gate_calls_present"]:
                calls = {item["call"] for item in row["required_calls"]}
                if not {"manuscript_pdf_gate.require_local", "manuscript_pdf_gate.require_public"} <= calls:
                    raise EnforcementDrift(f"local and public AST requirements missing: {route_id}")


def render_status(claims: dict) -> str:
    validate_model(claims)
    routes = claims["routes"]
    status = f"Enforcement status (verified {claims['verified_on']}): "
    if all(route["enforced"] for route in routes.values()):
        status += "the Methods Digest guard, successor publisher and installed dated publisher enforce this gate. "
        for route in routes.values():
            installed = next(row for row in route["sources"] if row["root"] == "core")
            status += f"`{Path(installed['path']).name}` installed SHA-256 `{installed['sha256']}`. "
    elif routes["digest_guard"]["enforced"] and routes["successor"]["enforced"] and not routes["dated"]["enforced"]:
        status += (
            "the Methods Digest guard (`guard_methods_digest_release.py`) and the successor publisher "
            "(`publish_successor_wave.py`) enforce this gate. The installed dated publisher "
            "(`publish_dated_bundles.py`, reached through `weekend_canon_lockstep.py`) does not yet "
            "enforce it. Until the reviewed gated version is installed, a Saturday wave must not "
            "publish any bundle whose actual manuscript lacks a separate top-level PDF, and every "
            "published PDF must be downloaded anonymously and hash-checked after publication."
        )
    else:
        raise EnforcementDrift("no reviewed instruction template for this enforcement state")
    return BEGIN + "\n" + status.rstrip() + "\n" + END


def replace_status(text: str, claims: dict) -> str:
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise EnforcementDrift("expected exactly one generated status block")
    before, body = text.split(BEGIN, 1)
    _, after = body.split(END, 1)
    return before + render_status(claims) + after


def verify(claims: dict, repo_root: Path, core_root: Path | None = None) -> dict:
    validate_model(claims)
    roots = {"repo": repo_root}
    if core_root is not None:
        roots["core"] = core_root
    observations = []
    for route in claims["routes"].values():
        for entry in route["sources"]:
            if entry["root"] not in roots:
                continue
            observations.append(validate_source((roots[entry["root"]] / entry["path"]).read_bytes(), entry))
    return {
        "status": "PASS",
        "scope": "repo_and_installed" if core_root else "repo_only_installed_not_verified",
        "observations": observations,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", type=Path, default=DEFAULT_CLAIMS)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--core-root", type=Path)
    parser.add_argument("--instruction-file", type=Path, action="append", default=[])
    parser.add_argument("--render", action="store_true")
    args = parser.parse_args(argv)
    try:
        claims = json.loads(args.claims.read_text())
        if args.render:
            print(render_status(claims))
            return 0
        if args.repo_root is None:
            raise EnforcementDrift("--repo-root required for source inspection")
        result = verify(claims, args.repo_root, args.core_root)
        for path in args.instruction_file:
            text = path.read_text()
            if replace_status(text, claims) != text:
                raise EnforcementDrift(f"instruction status differs: {path}")
        result["instruction_files_checked"] = len(args.instruction_file)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (EnforcementDrift, OSError, ValueError, KeyError, TypeError, SyntaxError) as exc:
        print(f"HOLD_ENFORCEMENT_CLAIMS: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
