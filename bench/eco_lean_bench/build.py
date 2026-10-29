#!/usr/bin/env python3
"""Build the Eco-Lean Bench task set from the published comparator certificates.

    python3 bench/eco_lean_bench/build.py          # write data/tasks.jsonl and data/manifest.json
    python3 bench/eco_lean_bench/build.py --check  # exit 1 if the checked-in data is stale

Each task is one certified run: the frozen challenge file (statements with
`sorry` proofs), the theorems a prover must prove, the exact toolchain and
Mathlib revision, and the permitted axioms. The reference solution is named
by path and SHA-256 only, never inlined, so the task file can be handed to a
prover as is.

--- INVARIANTS ---
B1  Only runs whose challenge differs from their solution become tasks; the
    others are listed in the manifest under `excluded` with the reason.
B2  Every exported challenge's SHA-256 equals the hash bound in
    certificates/index.json; a mismatch aborts the build.
B3  In every exported challenge, each target theorem's proof is exactly
    `sorry` (`:= by sorry` or `:= sorry`), and `sorry` appears nowhere else
    in code.
B4  Each target theorem's statement in the challenge equals its statement in
    the certified reference solution (the parser agrees with comparator).
B5  Output is byte-deterministic: the same certificates give the same files.
    Standard library only; no Lean needed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CERTS = ROOT / "certificates"
DATA = HERE / "data"
sys.path.insert(0, str(HERE))
import lean_text  # noqa: E402

BENCH = "eco-lean-bench"
BENCH_VERSION = "0.1.0"
TASK_SCHEMA = "eco-lean-bench-task/1"
SORRY_PROOFS = (":= by sorry", ":= sorry")


class BuildError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def qualify(short: str, theorems: dict) -> str:
    hits = [q for q in theorems if q == short or q.endswith("." + short)]
    if len(hits) != 1:
        raise BuildError(f"theorem {short!r}: expected one declaration, found {hits}")
    return hits[0]


def build_task(run: dict) -> dict:
    run_dir = CERTS / run["run"]
    ch_meta, so_meta = run["files"]["challenge"], run["files"]["solution"]
    ch_bytes = (run_dir / ch_meta["file"]).read_bytes()
    so_bytes = (run_dir / so_meta["file"]).read_bytes()
    if sha256(ch_bytes) != ch_meta["sha256"]:                                    # B2
        raise BuildError(f"{run['run']}: challenge hash does not match index.json")
    if sha256(so_bytes) != so_meta["sha256"]:
        raise BuildError(f"{run['run']}: solution hash does not match index.json")
    challenge = ch_bytes.decode("utf-8")
    ch_thms = lean_text.theorem_map(challenge)
    so_thms = lean_text.theorem_map(so_bytes.decode("utf-8"))
    targets = [qualify(t, ch_thms) for t in run["theorems"]]
    for q in targets:
        if ch_thms[q].proof() not in SORRY_PROOFS:                               # B3
            raise BuildError(f"{run['run']}: target {q} is not a bare sorry in the challenge")
        if q not in so_thms or so_thms[q].statement() != ch_thms[q].statement():  # B4
            raise BuildError(f"{run['run']}: target {q} statement differs from the reference")
    code = lean_text.strip(challenge)
    if len(lean_text.has_token(code, "sorry")) != len(targets):                  # B3
        raise BuildError(f"{run['run']}: sorry appears outside the target theorems")
    num = run["run"].split("-", 1)[1]
    return {
        "schema": TASK_SCHEMA,
        "task_id": f"ELB-{num}",
        "source_run": run["run"],
        "toolchain": run["toolchain"],
        "mathlib_rev": run["mathlib_rev"],
        "namespace": run.get("namespace", ""),
        "challenge": challenge,
        "challenge_file": f"certificates/{run['run']}/{ch_meta['file']}",
        "challenge_sha256": ch_meta["sha256"],
        "targets": targets,
        "target_count": len(targets),
        "permitted_axioms": run["permitted_axioms"],
        "depth": run["depth"]["label"],
        "reference_median_proof_lines": run["depth"]["median_proof_lines"],
        "reference_solution": {"file": f"certificates/{run['run']}/{so_meta['file']}",
                               "sha256": so_meta["sha256"]},
        "public_since": run["issued_at_utc"][:10],
        "os_functions": [f["id"] if isinstance(f, dict) else f for f in run.get("os_functions", [])],
    }


def build() -> tuple[str, str]:
    index = json.loads((CERTS / "index.json").read_text(encoding="utf-8"))
    tasks, excluded = [], []
    for run in sorted(index["runs"], key=lambda r: r["run"]):
        if run.get("challenge_identical_to_solution"):                           # B1
            excluded.append({"run": run["run"], "reason": "challenge file is byte-identical to the "
                             "solution: statements were frozen together with their proofs"})
            continue
        tasks.append(build_task(run))
    lines = "".join(dumps(t) + "\n" for t in tasks)
    by_depth: dict[str, dict] = {}
    for t in tasks:
        d = by_depth.setdefault(t["depth"], {"tasks": 0, "theorems": 0})
        d["tasks"] += 1
        d["theorems"] += t["target_count"]
    manifest = {
        "bench": BENCH,
        "version": BENCH_VERSION,
        "task_schema": TASK_SCHEMA,
        "source": "certificates/index.json",
        "source_sha256": sha256((CERTS / "index.json").read_bytes()),
        "tasks_file": "tasks.jsonl",
        "tasks_sha256": sha256(lines.encode("utf-8")),
        "counts": {"tasks": len(tasks), "theorems": sum(t["target_count"] for t in tasks),
                   "by_depth": dict(sorted(by_depth.items()))},
        "task_ids": [t["task_id"] for t in tasks],
        "excluded": excluded,
        "toolchains": sorted({t["toolchain"] for t in tasks}),
        "mathlib_revs": sorted({t["mathlib_rev"] for t in tasks}),
    }
    return lines, json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if data/ is not current")
    args = ap.parse_args(argv)
    try:
        lines, manifest = build()
    except BuildError as exc:
        print(f"build failed: {exc}", file=sys.stderr)
        return 2
    files = {DATA / "tasks.jsonl": lines, DATA / "manifest.json": manifest}
    if args.check:
        stale = [p.name for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        if stale:
            print("stale: " + ", ".join(stale) + " (run bench/eco_lean_bench/build.py)", file=sys.stderr)
            return 1
        print("eco-lean-bench data is current")
        return 0
    DATA.mkdir(exist_ok=True)
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    m = json.loads(manifest)
    print(f"wrote {m['counts']['tasks']} tasks, {m['counts']['theorems']} theorems to {DATA.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
