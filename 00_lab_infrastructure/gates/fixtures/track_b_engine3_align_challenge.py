#!/usr/bin/env python3
"""Derive a Comparator challenge from a zero-sorry candidate without statement drift."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


FORBIDDEN = re.compile(r"\b(?:sorry|admit|sorryAx)\b|\bunsafe\b|open\s+private")
DECLARATION = re.compile(r"(?m)^(?:theorem|lemma)\s+([A-Za-z_][\w'.]*)\b")
# Comparator challenges currently require tactic proofs.  Restricting the
# boundary to `:= by` avoids confusing a `let x := value` inside a theorem
# statement with the theorem's proof assignment.
ASSIGNMENT = re.compile(r":=(?=\s*by\b)")
TOP_LEVEL = re.compile(
    r"^(?:/[-*!]|--|theorem\b|lemma\b|def\b|abbrev\b|example\b|instance\b|"
    r"structure\b|class\b|inductive\b|namespace\b|section\b|end\b|open\b|"
    r"variable\b|include\b|omit\b|attribute\b|noncomputable\b|private\b)"
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def strip_comments(source: str) -> str:
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
    if depth or in_string:
        raise ValueError("unterminated Lean comment or string")
    return "".join(output)


def _declaration_start(source: str, name: str) -> int:
    matches = [match.start() for match in DECLARATION.finditer(source) if match.group(1) == name]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one top-level theorem/lemma named {name}; found {len(matches)}")
    return matches[0]


def _assignment(source: str, start: int, name: str) -> re.Match[str]:
    match = ASSIGNMENT.search(source, start)
    if match is None:
        raise ValueError(f"target {name} must use an explicit ':= by' proof assignment")
    next_decl = DECLARATION.search(source, start + 1)
    if next_decl is not None and next_decl.start() < match.start():
        raise ValueError(f"target {name} has no proof assignment before the next declaration")
    return match


def _proof_end(source: str, proof_start: int, name: str) -> int:
    cursor = source.find("\n", proof_start)
    if cursor < 0:
        return len(source)
    cursor += 1
    while cursor < len(source):
        newline = source.find("\n", cursor)
        end = len(source) if newline < 0 else newline
        line = source[cursor:end]
        if line and not line[0].isspace():
            return cursor
        cursor = len(source) if newline < 0 else newline + 1
    return len(source)


def normalized_signature(source: str, name: str) -> str:
    clean = strip_comments(source)
    start = _declaration_start(clean, name)
    assignment = _assignment(clean, start, name)
    return " ".join(clean[start : assignment.start()].split())


def align_challenge(sealed_statement: str, candidate: str, expected_names: list[str]) -> tuple[str, dict[str, str]]:
    if not expected_names or len(set(expected_names)) != len(expected_names):
        raise ValueError("expected theorem names must be nonempty and unique")
    forbidden = sorted(set(FORBIDDEN.findall(strip_comments(candidate))))
    if forbidden:
        raise ValueError("candidate contains forbidden proof constructs: " + ", ".join(forbidden))

    signatures: dict[str, str] = {}
    replacements: list[tuple[int, int, str]] = []
    for name in expected_names:
        sealed_signature = normalized_signature(sealed_statement, name)
        candidate_signature = normalized_signature(candidate, name)
        if sealed_signature != candidate_signature:
            raise ValueError(f"target theorem signature drift: {name}")
        signatures[name] = sha256_bytes((sealed_signature + "\n").encode())
        start = _declaration_start(candidate, name)
        assignment = _assignment(candidate, start, name)
        end = _proof_end(candidate, assignment.end(), name)
        proof_text = candidate[assignment.end() : end]
        if not proof_text.strip():
            raise ValueError(f"target theorem has an empty proof body: {name}")
        replacements.append((assignment.start(), end, ":= by\n  sorry\n\n"))

    # A theorem's textual signature can retain its spelling while a referenced
    # definition, import, section variable, notation, or instance changes its
    # meaning. Keep every non-proof byte fixed; even whitespace inside strings
    # and syntax/layout can be meaningful.
    # Candidate-only helpers and reordered declarations therefore require a
    # separately reviewed alignment, not automatic semantic approval here.
    def nonproof_context(source: str) -> str:
        clean = source
        spans: list[tuple[int, int]] = []
        for name in expected_names:
            start = _declaration_start(clean, name)
            assignment = _assignment(clean, start, name)
            spans.append((assignment.start(), _proof_end(clean, assignment.end(), name)))
        for start, end in sorted(spans, reverse=True):
            clean = clean[:start] + ":= by __VIRIDIS_PROOF_BODY__\n" + clean[end:]
        return clean

    if nonproof_context(sealed_statement) != nonproof_context(candidate):
        raise ValueError("non-proof context drift: definitions, imports, or declaration context require separate semantic review")

    result = candidate
    for start, end, replacement in sorted(replacements, reverse=True):
        result = result[:start] + replacement + result[end:]
    clean_result = strip_comments(result)
    introduced = re.findall(r"\bsorry\b", clean_result)
    if len(introduced) != len(expected_names):
        raise ValueError("aligned challenge does not contain exactly one sorry per target")
    return result, signatures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sealed-statement", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--expected-theorem", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    sealed = args.sealed_statement.read_text(encoding="utf-8")
    candidate = args.candidate.read_text(encoding="utf-8")
    aligned, signatures = align_challenge(sealed, candidate, args.expected_theorem)
    args.output.write_text(aligned, encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "standard": "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1",
        "status": "FROZEN",
        "operation": "candidate-order challenge with only expected theorem proof bodies replaced by sorry",
        "sealed_statement": {
            "path": str(args.sealed_statement),
            "sha256": sha256_bytes(args.sealed_statement.read_bytes()),
        },
        "candidate": {
            "path": str(args.candidate),
            "sha256": sha256_bytes(args.candidate.read_bytes()),
        },
        "aligned_challenge": {
            "path": str(args.output),
            "sha256": sha256_bytes(args.output.read_bytes()),
        },
        "expected_theorem_names": args.expected_theorem,
        "signature_sha256": signatures,
        "target_signatures_match_sealed_statement": True,
        "candidate_forbidden_constructs_empty": True,
        "shared_declaration_order_source": "candidate",
        "introduced_sorry_count": len(args.expected_theorem),
        "local_lean_execution": False,
        "external_mutation": False,
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
