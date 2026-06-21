#!/usr/bin/env python3
"""
vacuity_lint.py — Viridis Canon integrity linter (INV-1).

Flags Lean proofs whose *form* betrays a vacuous or trivial discharge, where a
named theorem may claim far more than it formally establishes. This does NOT
replace Lean type-checking; it catches the specific failure mode that
type-checking cannot: a theorem that compiles but is logically empty because
its hypotheses are unsatisfiable (e.g. an existential witnessed by the top
element so that `T > top` can never fire) or because the conclusion is
trivially weaker than the name advertises.

Two tiers:
  CRITICAL  — vacuity fingerprints. A spine theorem must not match these.
              Exit code 1 if any CRITICAL match is found.
  REVIEW    — "smells": a strong-sounding theorem name discharged by a
              one-shot trivial tactic. Not necessarily wrong; must appear in
              CLAIMS_MATRIX.md with an honest status label.

Usage:
    python3 vacuity_lint.py FILE.lean [FILE.lean ...]
    python3 vacuity_lint.py --dir path/to/lean   (lints *.lean recursively)

Exit codes: 0 = clean, 1 = CRITICAL found, 2 = usage error.
"""
from __future__ import annotations
import re
import sys
import os
import glob

CRITICAL_PATTERNS = [
    (re.compile(r"absurd\b[^\n]*\bnot_top_lt\b"),
     "discharge via `absurd _ not_top_lt`: a `T > top` hypothesis can never "
     "hold -> any forall over it is vacuously true"),
    (re.compile(r"absurd\b[^\n]*\bnot_lt_top\b"),
     "discharge via `absurd _ not_lt_top`: unsatisfiable strict-bound hyp"),
    (re.compile(r"absurd\b[^\n]*\bnot_top_le\b"),
     "discharge via `absurd _ not_top_le`: unsatisfiable `top <=` hypothesis"),
    (re.compile(r"⟨\s*⊤\s*,"),
     "existential witnessed by top: body almost certainly relies on the "
     "resulting hypothesis being unsatisfiable (vacuous forall)"),
    (re.compile(r"⟨\s*\(\s*⊤\s*:"),
     "existential witnessed by a typed top: same vacuity risk"),
    (re.compile(r"\bfun\s+\w+\s+\w+\s*=>\s*absurd\b"),
     "forall-binder immediately discharged by `absurd`: hypothesis is being "
     "shown contradictory rather than used"),
    (re.compile(r"\bnomatch\b"),
     "`nomatch` discharge: proof proceeds by an impossible case -- verify the "
     "case is impossible by intent, not by a vacuous hypothesis"),
]

STRONG_NAME = re.compile(
    r"(bound|cost|necessity|necessary|impossib|must|lower|upper|strict|"
    r"collapse|foreclosure|self_defeat|defeat|substitut|complement|"
    r"conserv|align|deception|wall|ceiling|floor|dichotomy|threshold|tipping)",
    re.IGNORECASE,
)
TRIVIAL_TACTIC = re.compile(
    r":=\s*by\s+(simp|positivity|trivial|rfl|decide|aesop|tauto)\b[^\n]*$",
    re.MULTILINE,
)
THEOREM_HDR = re.compile(r"^\s*(theorem|lemma)\s+([A-Za-z0-9_']+)", re.MULTILINE)


def split_decls(text):
    hdrs = list(THEOREM_HDR.finditer(text))
    for i, m in enumerate(hdrs):
        start = m.start()
        end = hdrs[i + 1].start() if i + 1 < len(hdrs) else len(text)
        name = m.group(2)
        line = text.count("\n", 0, start) + 1
        yield name, line, text[start:end]


def lint_file(path):
    crit, review = [], []
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    for name, line, body in split_decls(text):
        for rx, why in CRITICAL_PATTERNS:
            m = rx.search(body)
            if m:
                bline = line + body.count("\n", 0, m.start())
                crit.append((path, bline, name, why, m.group(0).strip()))
        if STRONG_NAME.search(name):
            proof = body.split(":=", 1)[-1]
            if TRIVIAL_TACTIC.search(body) and proof.count(":=") == 0 \
               and len(proof.strip().splitlines()) <= 2:
                review.append((path, line, name,
                               "strong-sounding name discharged by a single "
                               "trivial tactic -- confirm conclusion matches "
                               "the name in CLAIMS_MATRIX.md"))
    return crit, review


def collect(args):
    if args and args[0] == "--dir":
        return sorted(glob.glob(os.path.join(args[1], "**", "*.lean"),
                                recursive=True))
    return [f for f in args if os.path.isfile(f)]


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    files = collect(argv[1:])
    if not files:
        print("vacuity_lint: no .lean files found", file=sys.stderr)
        return 2
    all_crit, all_review = [], []
    for p in files:
        c, r = lint_file(p)
        all_crit += c
        all_review += r
    if all_crit:
        print("=" * 70)
        print(f"CRITICAL -- {len(all_crit)} vacuity fingerprint(s): "
              "must NOT appear in the verified spine")
        print("=" * 70)
        for path, line, name, why, snip in all_crit:
            print(f"\n  {os.path.basename(path)}:{line}  <{name}>")
            print(f"     match : {snip}")
            print(f"     why   : {why}")
    if all_review:
        print("\n" + "-" * 70)
        print(f"REVIEW -- {len(all_review)} triviality smell(s): "
              "must be honestly labeled in CLAIMS_MATRIX.md")
        print("-" * 70)
        for path, line, name, why in all_review:
            print(f"\n  {os.path.basename(path)}:{line}  <{name}>")
            print(f"     why   : {why}")
    print("\n" + "=" * 70)
    print(f"Scanned {len(files)} file(s): "
          f"{len(all_crit)} CRITICAL, {len(all_review)} REVIEW")
    print("=" * 70)
    return 1 if all_crit else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
