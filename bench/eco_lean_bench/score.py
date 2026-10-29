#!/usr/bin/env python3
"""Score Eco-Lean Bench submissions.

A submission is a folder with one Lean file per attempted task, named by task
id (`ELB-139.lean`). Each file is a complete solution: the challenge with the
target theorems proved. Tasks without a file score zero.

    python3 bench/eco_lean_bench/score.py SUBMISSION_DIR                 # precheck, seconds, no Lean
    python3 bench/eco_lean_bench/score.py SUBMISSION_DIR --kernel        # authoritative: Lean + axiom audit
    python3 bench/eco_lean_bench/score.py SUBMISSION_DIR --kernel --dry-run   # write the Lean projects only
    python3 bench/eco_lean_bench/score.py --reference                    # score the certified solutions

The precheck is a fast filter. Only `--kernel` results go on the leaderboard:
they elaborate the submission at the task's pinned toolchain and Mathlib
revision and audit every target theorem's axioms with `#print axioms`, as
certificates/rerun.sh does. With COMPARATOR set, comparator also confirms
that each statement matches the challenge in the kernel.

--- INVARIANTS ---
S1  A target counts only if the submission declares it under the same
    qualified name with a statement identical to the challenge's.
S2  A target counts only if its proof, and every declaration it mentions
    (transitively, by name), is free of `sorry` and `admit`.
S3  A file that declares an `axiom`, uses `native_decide` / `ofReduceBool`
    / `ofReduceNat`, skips the kernel (`debug.skipKernelTC`), stops early
    (`#exit`), or redefines syntax (`macro`, `syntax`, `elab`, `notation`,
    `macro_rules`) scores zero.
S4  Every non-theorem declaration of the challenge (def, structure,
    instance, ...) must appear in the submission unchanged; otherwise the
    file scores zero.
S5  Kernel mode credits a target only if elaboration has no errors and the
    target depends on no axiom outside the task's permitted set.
S6  The result records the dataset hash, the mode, and each scored file's
    SHA-256, so anyone can reproduce it. Kernel mode never touches the
    repository; it works in a temporary directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import lean_text  # noqa: E402


def _load_build():
    # Loaded by path under a private name: "build" is also a common PyPI package.
    import importlib.util
    spec = importlib.util.spec_from_file_location("eco_lean_bench_build", HERE / "build.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


_build = _load_build()
BENCH, BENCH_VERSION, DATA, sha256 = _build.BENCH, _build.BENCH_VERSION, _build.DATA, _build.sha256

RESULT_SCHEMA = "eco-lean-bench-result/1"
FORBIDDEN_TOKENS = ("native_decide", "ofReduceBool", "ofReduceNat", "#exit",
                    "macro", "macro_rules", "syntax", "elab", "notation", "skipKernelTC")
GAP_TOKENS = ("sorry", "admit")
NON_THEOREM_KINDS = ("def", "abbrev", "structure", "instance", "inductive", "class", "opaque")


def load_tasks() -> list[dict]:
    text = (DATA / "tasks.jsonl").read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][\w'!?.]*", text))


def precheck(task: dict, solution: str) -> dict:
    """S1 to S4 on one file. Returns {"file_ok", "file_reasons", "targets": {name: reason|None}}."""
    code = lean_text.strip(solution)
    reasons = []
    decls = lean_text.declarations(solution)
    if any(d.kind == "axiom" for d in decls):                                    # S3
        reasons.append("declares an axiom")
    for tok in FORBIDDEN_TOKENS:
        if lean_text.has_token(code, tok) or (tok == "skipKernelTC" and "skipKernelTC" in code):
            reasons.append(f"uses {tok}")
    challenge_decls = [d for d in lean_text.declarations(task["challenge"]) if d.kind in NON_THEOREM_KINDS]
    have = Counter((d.kind, lean_text.normalize(d.text)) for d in decls if d.kind in NON_THEOREM_KINDS)
    need = Counter((d.kind, lean_text.normalize(d.text)) for d in challenge_decls)
    for (kind, text), n in need.items():                                         # S4
        if have[(kind, text)] < n:
            name = next((d.qualname for d in challenge_decls
                         if lean_text.normalize(d.text) == text), "") or "(anonymous)"
            reasons.append(f"changes or drops {kind} {name}")
    challenge_thms = lean_text.theorem_map(task["challenge"])
    sol_thms = {d.qualname: d for d in decls if d.kind in ("theorem", "lemma") and d.qualname}

    # S2: which declarations reach a gap, by name, transitively.
    by_name: dict[str, list] = {}
    for d in decls:
        if d.qualname:
            by_name.setdefault(d.qualname, []).append(d)
            by_name.setdefault(d.qualname.rsplit(".", 1)[-1], []).append(d)
    gap = {id(d) for d in decls if any(t in _tokens(d.text) for t in GAP_TOKENS)}
    changed = True
    while changed:
        changed = False
        for d in decls:
            if id(d) in gap:
                continue
            if any(id(x) in gap for tok in _tokens(d.text) for x in by_name.get(tok, ()) if x is not d):
                gap.add(id(d))
                changed = True

    targets = {}
    for q in task["targets"]:
        if q not in sol_thms:
            targets[q] = "missing"                                               # S1
        elif sol_thms[q].statement() != challenge_thms[q].statement():
            targets[q] = "statement differs from the challenge"
        elif id(sol_thms[q]) in gap:
            targets[q] = "proof uses sorry or admit"                            # S2
        else:
            targets[q] = None
    return {"file_ok": not reasons, "file_reasons": reasons, "targets": targets}


# ---- kernel mode (S5) --------------------------------------------------------

LAKEFILE = """name = "eco_lean_bench_check"
version = "0.1.0"
defaultTargets = ["Solution", "Challenge"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4"
rev = "{rev}"

[[lean_lib]]
name = "Solution"

[[lean_lib]]
name = "Challenge"
"""

_DEPENDS = re.compile(r"'([^']+)' depends on axioms: \[([^\]]*)\]")
_NO_AXIOMS = re.compile(r"'([^']+)' does not depend on any axioms")


def write_project(task: dict, solution: str, work: Path) -> list[list[str]]:
    """Lay out a throwaway Lake project; return the commands that check it."""
    (work / "lean-toolchain").write_text(task["toolchain"] + "\n", encoding="utf-8")
    (work / "lakefile.toml").write_text(LAKEFILE.format(rev=task["mathlib_rev"]), encoding="utf-8")
    (work / "Challenge.lean").write_text(task["challenge"], encoding="utf-8")
    (work / "Solution.lean").write_text(solution, encoding="utf-8")
    config = {"challenge_module": "Challenge", "solution_module": "Solution",
              "theorem_names": task["targets"], "permitted_axioms": task["permitted_axioms"]}
    (work / "config.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    check = solution.rstrip("\n") + "\n\n" + "".join(f"#print axioms {q}\n" for q in task["targets"])
    (work / "Check.lean").write_text(check, encoding="utf-8")
    cmds = [["lake", "exe", "cache", "get"], ["lake", "env", "lean", "Check.lean"]]
    comparator = os.environ.get("COMPARATOR")
    if comparator:
        cmds.append(["lake", "env", comparator, "config.json"])
    return cmds


def parse_axiom_log(task: dict, log: str) -> dict:
    """Map each target to None (credited) or a reason, from `#print axioms` output."""
    allowed = set(task["permitted_axioms"])
    seen = {m.group(1): {a.strip() for a in m.group(2).split(",") if a.strip()} for m in _DEPENDS.finditer(log)}
    seen.update({m.group(1): set() for m in _NO_AXIOMS.finditer(log)})
    errors = bool(re.search(r"^[^\n]*: error", log, re.M))
    out = {}
    for q in task["targets"]:
        if errors:
            out[q] = "elaboration error"
        elif q not in seen:
            out[q] = "not found by Lean"
        elif seen[q] - allowed:
            out[q] = "uses axioms " + ", ".join(sorted(seen[q] - allowed))
        else:
            out[q] = None
    return out


def kernel_check(task: dict, solution: str, dry_run: bool, keep: Path | None) -> dict:
    work = Path(tempfile.mkdtemp(prefix=f"elb-{task['task_id']}-", dir=keep))
    cmds = write_project(task, solution, work)
    if dry_run:
        return {"work_dir": str(work), "commands": cmds, "targets": None}
    log = ""
    for cmd in cmds:
        p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=7200)
        if cmd[:3] == ["lake", "env", "lean"]:
            log = p.stdout + p.stderr
        elif p.returncode != 0:
            return {"work_dir": str(work), "targets": {q: f"{cmd[-1]} failed" for q in task["targets"]}}
    return {"work_dir": str(work), "targets": parse_axiom_log(task, log)}


# ---- scoring -----------------------------------------------------------------

def score(files: dict[str, str], mode: str = "precheck", dry_run: bool = False,
          keep: Path | None = None, only: set[str] | None = None) -> dict:
    tasks = [t for t in load_tasks() if not only or t["task_id"] in only]
    rows, solved, total = [], 0, 0
    depth: dict[str, list[int]] = {}
    for task in tasks:
        n = task["target_count"]
        total += n
        sol = files.get(task["task_id"])
        row = {"task_id": task["task_id"], "depth": task["depth"], "targets": n}
        if sol is None:
            row.update(solved=0, status="not attempted")
        else:
            row["file_sha256"] = sha256(sol.encode("utf-8"))
            pc = precheck(task, sol)
            reasons = dict(pc["targets"])
            if mode == "kernel":
                kc = kernel_check(task, sol, dry_run, keep)
                row["work_dir"] = kc["work_dir"]
                if dry_run:
                    row["commands"] = kc["commands"]
                else:
                    reasons = {q: reasons[q] or kc["targets"][q] for q in reasons}
            if not pc["file_ok"]:
                reasons = {q: "; ".join(pc["file_reasons"]) for q in reasons}
            row["failures"] = {q: r for q, r in reasons.items() if r}
            row["solved"] = 0 if (mode == "kernel" and dry_run) else sum(1 for r in reasons.values() if not r)
            row["status"] = "scored" if not (mode == "kernel" and dry_run) else "dry run"
        solved += row["solved"]
        d = depth.setdefault(task["depth"], [0, 0])
        d[0] += row["solved"]
        d[1] += n
        rows.append(row)
    return {
        "schema": RESULT_SCHEMA,
        "bench": BENCH,
        "bench_version": BENCH_VERSION,
        "tasks_sha256": sha256((DATA / "tasks.jsonl").read_bytes()),
        "mode": mode + (" (dry run)" if dry_run else ""),
        "authoritative": mode == "kernel" and not dry_run,
        "solved": solved,
        "total": total,
        "by_depth": {k: {"solved": v[0], "total": v[1]} for k, v in sorted(depth.items())},
        "tasks": rows,
    }


def reference_files() -> dict[str, str]:
    return {t["task_id"]: (ROOT / t["reference_solution"]["file"]).read_text(encoding="utf-8")
            for t in load_tasks()}


def read_submission(folder: Path) -> dict[str, str]:
    known = {t["task_id"] for t in load_tasks()}
    files = {}
    for p in sorted(folder.glob("*.lean")):
        if p.stem not in known:
            raise SystemExit(f"{p.name}: not a task id (expected one of ELB-123 ...)")
        files[p.stem] = p.read_text(encoding="utf-8")
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("submission", nargs="?", type=Path, help="folder of ELB-NNN.lean files")
    ap.add_argument("--reference", action="store_true", help="score the certified reference solutions")
    ap.add_argument("--kernel", action="store_true", help="authoritative check with Lean")
    ap.add_argument("--dry-run", action="store_true", help="with --kernel: write projects, run nothing")
    ap.add_argument("--task", action="append", help="score only this task id (repeatable)")
    ap.add_argument("--work", type=Path, help="with --kernel: parent folder for the Lean projects")
    ap.add_argument("--out", type=Path, help="write the result JSON here")
    args = ap.parse_args(argv)
    if bool(args.submission) == args.reference:
        ap.error("give a submission folder or --reference, not both")
    files = reference_files() if args.reference else read_submission(args.submission)
    result = score(files, "kernel" if args.kernel else "precheck", args.dry_run, args.work,
                   set(args.task) if args.task else None)
    text = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    print(f"{result['mode']}: {result['solved']}/{result['total']} theorems", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
