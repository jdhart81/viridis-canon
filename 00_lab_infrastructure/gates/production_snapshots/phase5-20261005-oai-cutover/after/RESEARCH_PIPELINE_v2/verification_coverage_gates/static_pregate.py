#!/usr/bin/env python3
"""Report-only source triage. This is not a Lean verifier or certificate issuer."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ALLOWLIST = {"propext", "Quot.sound", "Classical.choice"}


def code_only(source):
    """Mask nested comments and strings while preserving line positions and tokens."""
    out = list(source)
    i, depth, string = 0, 0, False
    while i < len(source):
        pair = source[i:i + 2]
        if depth:
            if pair == "/-":
                depth += 1
            elif pair == "-/":
                depth -= 1
            else:
                out[i] = "\n" if source[i] == "\n" else " "
                i += 1
                continue
            out[i:i + 2] = "  "
            i += 2
        elif string:
            if source[i] == "\\":
                out[i:i + 2] = "  "
                i += 2
                continue
            if source[i] == '"':
                string = False
            out[i] = "\n" if source[i] == "\n" else " "
            i += 1
        elif pair == "/-":
            depth = 1
            out[i:i + 2] = "  "
            i += 2
        elif pair == "--":
            end = source.find("\n", i)
            end = len(source) if end < 0 else end
            out[i:end] = " " * (end - i)
            i = end
        else:
            if source[i] == '"':
                string = True
                out[i] = " "
            i += 1
    if depth or string:
        raise ValueError("unterminated comment or string")
    return "".join(out)


def scan(path):
    result = {"path": str(path), "decls": [], "declared_axioms": [],
              "has_sorry": False, "flags": [], "errors": []}
    try:
        raw = Path(path).read_bytes()
        result["sha256"] = hashlib.sha256(raw).hexdigest()
        source = code_only(raw.decode("utf-8"))
        result["decls"] = re.findall(r"\b(?:theorem|lemma)\s+([\w'.]+)", source)
        result["declared_axioms"] = re.findall(r"\baxiom\s+([\w'.]+)", source)
        patterns = {
            "axiom_declaration": r"\baxiom\b",
            "proof_hole": r"\b(?:sorry|admit|sorryAx)\b",
            "native_decide": r"\bnative_decide\b",
            "forbidden_escape": r"\bunsafe\b|\bopen\s+private\b",
            "unsatisfiable_hypothesis_shape": r"[({]\s*\w+\s*:\s*\(*\s*False\s*\)*\s*[)}]|[({]\s*\w+\s*:\s*(\w+)\s*<\s*\1\s*[)}]",
            "vacuous_shape": r"(?::|→|↔)\s*\(*\s*True\b|(?s:∃(?:(?!:=).)*?,\s*\(*\s*True\b)",
        }
        for kind, pattern in patterns.items():
            for match in re.finditer(pattern, source):
                result["flags"].append({"kind": kind,
                    "line": source.count("\n", 0, match.start()) + 1,
                    "text": match.group()})
        result["has_sorry"] = bool(re.search(patterns["proof_hole"], source))
        result["unexpected_axioms"] = sorted(set(result["declared_axioms"]) - ALLOWLIST)
        result["has_sorryAx"] = bool(re.search(r"\bsorryAx\b", source))
    except (OSError, UnicodeError, ValueError) as exc:
        result["errors"].append(str(exc))
    result["static_pass"] = not result["flags"] and not result["errors"]
    result["mode"] = "REPORT_ONLY"
    result["certifies"] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    paths = sorted(args.path.rglob("*.lean")) if args.path.is_dir() else [args.path]
    results = [scan(path) for path in paths]
    print(json.dumps({"mode": "REPORT_ONLY", "results": results}, indent=2))
    return 0 if results and all(r["static_pass"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
