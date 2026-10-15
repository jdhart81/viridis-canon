#!/usr/bin/env python3
"""Advisory text lint for algebraic Lean proof candidates; never runs Lean.

This conservative heuristic has no Lean parser or elaborator. Unsupported
proof syntax is UNASSESSED, and no outcome is a verification certificate.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

ALGEBRA = {"ring", "ring_nf", "linarith", "nlinarith", "field_simp", "positivity", "norm_num"}
IDENTIFIER = r"[A-Za-z_][A-Za-z0-9_']*"
DECLARATION = re.compile(r"(?m)^\s*(?:(?:private|protected|noncomputable)\s+)*(?:theorem|lemma|def|abbrev|end|namespace|section)\b")


def strip_comments_and_strings(text: str) -> str:
    """Erase nested Lean comments and strings while preserving line locations."""
    out = list(text)
    depth = 0
    i = 0
    while i < len(text):
        if depth:
            if text.startswith("/-", i):
                out[i:i + 2] = "  "; depth += 1; i += 2
            elif text.startswith("-/", i):
                out[i:i + 2] = "  "; depth -= 1; i += 2
            else:
                if text[i] != "\n": out[i] = " "
                i += 1
        elif text.startswith("/-", i):
            out[i:i + 2] = "  "; depth = 1; i += 2
        elif text.startswith("--", i):
            end = text.find("\n", i)
            end = len(text) if end == -1 else end
            out[i:end] = " " * (end - i); i = end
        elif text[i] == '"':
            out[i] = " "; i += 1
            while i < len(text):
                char = text[i]
                if char != "\n": out[i] = " "
                i += 1
                if char == "\\" and i < len(text):
                    if text[i] != "\n": out[i] = " "
                    i += 1
                elif char == '"': break
        else:
            i += 1
    if depth:
        raise ValueError("unterminated Lean comment")
    return "".join(out)


def lint(source: bytes, playbook: dict) -> dict:
    if playbook.get("schema") != "VRS-LEAN-REPAIR-PLAYBOOK-1":
        raise ValueError("unsupported playbook")
    rule_ids = {rule["id"] for rule in playbook["rules"]}
    if not {"UNFOLD_LOCAL_ALGEBRA_DEFINITIONS", "RFL_ALGEBRA_REASSOCIATION"} <= rule_ids:
        raise ValueError("required advisory rules missing")
    text = strip_comments_and_strings(source.decode("utf-8"))
    definitions = set(re.findall(r"(?m)^\s*(?:(?:private|protected|noncomputable)\s+)*def\s+(" + IDENTIFIER + r")\b", text))
    declarations = list(DECLARATION.finditer(text))
    results = []
    for index, declaration in enumerate(declarations):
        end = declarations[index + 1].start() if index + 1 < len(declarations) else len(text)
        body = text[declaration.start():end]
        match = re.match(r"\s*(?:(?:private|protected)\s+)*(?:theorem|lemma)\s+(" + IDENTIFIER + r")(.*?)\s*:=\s*by\b(.*)", body, re.S)
        if not match:
            term = re.match(r"\s*(?:(?:private|protected|noncomputable)\s+)*(?:theorem|lemma)\s+(" + IDENTIFIER + r")\b", body)
            if term:
                results.append({"theorem": term.group(1), "referenced_local_definitions": [],
                                "status": "ADVISORY_UNASSESSED", "flags": [], "certifies": False})
            continue
        name, goal, proof = match.groups()
        referenced = sorted(definitions.intersection(re.findall(IDENTIFIER, goal)))
        row = {"theorem": name, "referenced_local_definitions": referenced,
               "status": "ADVISORY_UNASSESSED", "flags": [], "certifies": False}
        lines = [line.strip() for line in proof.splitlines() if line.strip()]
        tactics = [line.split()[0] for line in lines]
        supported = all(tactic in ALGEBRA | {"unfold", "rfl"} for tactic in tactics)
        # Explicit simp sets and tactic combinators require a richer parser.
        supported &= not any(character in proof for character in "[];<>|`")
        unfolded = set()
        for line in lines:
            if line.startswith("unfold "):
                unfolded.update(re.findall(IDENTIFIER, line)[1:])
        missing = sorted(set(referenced) - unfolded)
        if supported and tactics:
            row["status"] = "ADVISORY_PASS_NOT_CERTIFICATION"
            if missing and "rfl" in tactics:
                row["flags"].append("FLAG_RFL_ALGEBRA_REASSOCIATION")
            elif missing and any(tactic in ALGEBRA for tactic in tactics):
                row["flags"].append("FLAG_UNFOLD_LOCAL_ALGEBRA_DEFINITIONS")
            if row["flags"]:
                row.update(status="ADVISORY_REVIEW_REQUIRED", definitions_to_unfold=missing)
        results.append(row)
    return {"schema": "VRS-LEAN-REPAIR-LINT-1", "certifies": False,
            "authoritative_execution": "COMPARATOR_ONLY",
            "source_sha256": hashlib.sha256(source).hexdigest(),
            "parser": "conservative_text_heuristic_not_lean_elaboration",
            "flag_count": sum(len(row["flags"]) for row in results), "theorems": results}


def weekly_first_attempt_rate(attempts: list[dict], iso_week: str) -> dict:
    terminal = []
    unavailable = 0
    seen = set()
    for row in attempts:
        if row.get("attempt") != 1:
            continue
        if row["run_id"] in seen:
            raise ValueError("duplicate first attempt")
        seen.add(row["run_id"])
        if row.get("terminal_status") not in {"ACCEPTED", "REJECTED"} or not row.get("submitted_at_utc"):
            unavailable += 1
            continue
        when = datetime.fromisoformat(row["submitted_at_utc"].replace("Z", "+00:00"))
        if when.tzinfo is None:
            raise ValueError("attempt timestamp must include timezone")
        year, week, _ = when.astimezone(ZoneInfo("America/New_York")).isocalendar()
        if f"{year}-W{week:02}" == iso_week:
            terminal.append(row)
    accepted = sum(row["terminal_status"] == "ACCEPTED" for row in terminal)
    return {"iso_week": iso_week, "timezone": "America/New_York", "target": 0.9, "terminal_first_attempts": len(terminal),
            "accepted": accepted, "unavailable_first_attempts": unavailable,
            "rate": accepted / len(terminal) if terminal else None,
            "status": "KNOWN" if terminal and not unavailable else "PARTIAL" if terminal else "UNAVAILABLE",
            "certifies": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--playbook", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = lint(args.candidate.read_bytes(), json.loads(args.playbook.read_text()))
    # Never overwrite an evidence object or treat a lint flag as proof failure.
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"status": "ADVISORY_ONLY", "flag_count": result["flag_count"], "certifies": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
