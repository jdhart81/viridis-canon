#!/usr/bin/env python3
"""Compile census: every Lean file in the canon, compiled and axiom-audited, with nothing skipped silently.

The canon CI builds the spine (`lakefile.toml` defaultTargets), the historical P0 module and the modules in
`DEPOSIT_MANIFEST.txt`. Most of `series/`, `certificates/` and `releases/` is outside those builds. This tool
closes that gap: it compiles each `.lean` file on its own, under the toolchain its project declares, and then
audits every declaration the file contributes.

Invariants
    C1 Complete     Every `*.lean` file in the repository (outside `.git` and `.lake`) has exactly one ledger
                    entry. `merge` fails if a file is missing, duplicated or unknown.
    C2 Bytes        Each entry records the SHA-256 of the bytes that were compiled.
    C3 Name-free    The audit walks the environment. Every non-internal declaration that originates in the
                    file is checked; nothing is looked up by name. Allowed axioms are `propext`,
                    `Classical.choice` and `Quot.sound`. `sorryAx` is a violation like any other.
    C4 No silent    A compile error, a timeout, a failed dependency, a missing toolchain environment or a file
       pass         that contributes no declaration is never reported as CLEAN.
    C5 Read-only    Nothing is written outside `--out`.

Statuses
    CLEAN              compiled; every declaration depends only on the three standard axioms
    NONSTANDARD_AXIOM  compiled; at least one declaration depends on another axiom (listed)
    NO_DECLARATIONS    compiled; the file adds no declaration (an auditor or an import hub)
    COMPILE_FAILED     `lean` returned an error (first error line recorded)
    DEP_FAILED         a canon file it imports did not compile
    TIMEOUT            compile or audit exceeded the time limit
    NO_ENVIRONMENT     no `--env` was given for the toolchain this file declares

What CLEAN does not mean: that a theorem says what its paper claims, that a hypothesis is satisfiable, or
that a result is new. It means the file compiles at its declared pins and rests on the standard axioms.

Usage
    python3 tools/compile_census.py plan
    python3 tools/compile_census.py run --env leanprover/lean4:v4.28.0=. \\
        --env leanprover/lean4:v4.24.0=compat/v4_24 --shard 0/4 --out build/census
    python3 tools/compile_census.py merge build/census/shard-*.json --ledger reports/compile_census/ledger.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".lake", "node_modules", "__pycache__"}
EXTERNAL = {"Mathlib", "Lean", "Std", "Init", "Batteries", "Aesop", "Qq", "ProofWidgets", "Plausible",
            "ImportGraph", "LeanSearchClient", "Cli", "Lake"}
ALLOWED_AXIOMS = ("propext", "Classical.choice", "Quot.sound")
STATUSES = ("CLEAN", "NONSTANDARD_AXIOM", "NO_DECLARATIONS", "COMPILE_FAILED", "DEP_FAILED", "TIMEOUT",
            "NO_ENVIRONMENT")
IMPORT_RE = re.compile(r"^\s*(?:public\s+|private\s+|meta\s+)*import\s+(?:all\s+)?(\S+)")
RESULT_RE = re.compile(r"^CENSUS_RESULT checked=(\d+) theorems=(\d+) axioms=\[(.*?)\] violations=\[(.*)\]$", re.M)

AUDIT_TEMPLATE = """import {module}
import Lean
open Lean Elab Command

run_cmd do
  let env ← getEnv
  let target : Name := `{module}
  let modNames := env.header.moduleNames
  let mut idx : Option Nat := none
  for h : i in [0:modNames.size] do
    if modNames[i]! == target then
      idx := some i
  let some midx := idx | throwError "CENSUS_AUDIT_ERROR target module is not in the environment"
  let allowed : List Name := [``propext, ``Classical.choice, ``Quot.sound]
  let mut checked : Nat := 0
  let mut theorems : Nat := 0
  let mut seen : Array Name := #[]
  let mut violations : Array String := #[]
  for (declName, info) in env.constants.toList do
    if declName.isInternal then continue
    match env.getModuleIdxFor? declName with
    | none => pure ()
    | some m =>
      if m.toNat == midx then
        checked := checked + 1
        if info matches .thmInfo _ then theorems := theorems + 1
        let axs ← Lean.collectAxioms declName
        for a in axs do
          unless seen.contains a do seen := seen.push a
          unless allowed.contains a do
            if violations.size < 40 then violations := violations.push s!"{{declName}}:{{a}}"
  let axs := ", ".intercalate (seen.toList.map toString)
  let vio := "; ".intercalate violations.toList
  IO.println s!"CENSUS_RESULT checked={{checked}} theorems={{theorems}} axioms=[{{axs}}] violations=[{{vio}}]"
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lean_files(repo: Path) -> list[str]:
    """C1: every .lean file, as a sorted list of POSIX paths relative to the repository."""
    out = []
    for base, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in files:
            if name.endswith(".lean"):
                out.append((Path(base) / name).relative_to(repo).as_posix())
    return sorted(out)


def parse_imports(text: str) -> list[str]:
    """Module names imported in the file header. Comments before and between imports are skipped."""
    imports, depth = [], 0
    for raw in text.splitlines():
        line = raw
        if depth:
            while depth and "-/" in line:
                line = line.split("-/", 1)[1]
                depth -= 1
            if depth:
                continue
        while "/-" in line:
            head, rest = line.split("/-", 1)
            if "-/" in rest:
                line = head + " " + rest.split("-/", 1)[1]
            else:
                line, depth = head, depth + 1
        line = line.split("--", 1)[0].strip()
        if not line or line == "module" or line.startswith("prelude"):
            continue
        m = IMPORT_RE.match(line)
        if not m:
            break                       # first real command: the header is over
        imports.append(m.group(1))
    return imports


def projects(repo: Path, files: list[str]) -> dict[str, dict]:
    """Lake projects in the repository: directory -> {toolchain, options, claims}.

    `claims` are files outside the project directory that it builds through a `srcDir` (the historical P0
    module is built by `compat/v4_24` from a source at the repository root).
    """
    out: dict[str, dict] = {}
    known = set(files)
    for lakefile in sorted(repo.rglob("lakefile.toml")):
        if SKIP_DIRS & set(lakefile.relative_to(repo).parts):
            continue
        root = lakefile.parent
        rel = root.relative_to(repo).as_posix()
        try:
            data = tomllib.loads(lakefile.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            data = {}
        tc_file = root / "lean-toolchain"
        toolchain = tc_file.read_text(encoding="utf-8").strip() if tc_file.is_file() else ""
        claims = []
        for lib in data.get("lean_lib", []) or []:
            src = lib.get("srcDir", ".")
            if src in (".", ""):
                continue
            src_dir = (root / src).resolve()
            for glob in lib.get("globs", [lib.get("name", "")]):
                cand = src_dir / (str(glob).replace(".", "/") + ".lean")
                try:
                    c = cand.relative_to(repo.resolve()).as_posix()
                except ValueError:
                    continue
                if c in known:
                    claims.append(c)
        out[rel] = {"toolchain": toolchain, "options": data.get("leanOptions", {}) or {}, "claims": sorted(claims)}
    return out


def unit_of(path: str, projs: dict[str, dict]) -> str:
    """The project directory a file is compiled in: the nearest enclosing lakefile, else the repository root."""
    parts = Path(path).parts[:-1]
    for n in range(len(parts), 0, -1):
        cand = "/".join(parts[:n])
        if cand in projs:
            return cand
    return "."


def module_name(path: str, unit: str) -> str:
    rel = path if unit == "." else path[len(unit) + 1:]
    return ".".join(_quote(p) for p in Path(rel).with_suffix("").parts)


def _quote(part: str) -> str:
    return part if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_'!?]*", part) else f"«{part}»"


def build_plan(repo: Path) -> dict:
    files = lean_files(repo)
    projs = projects(repo, files)
    claimed = {c: p for p, info in projs.items() for c in info["claims"] if p != "."}
    known = set(files)
    root_tc = projs.get(".", {}).get("toolchain", "")
    entries = {}
    for path in files:
        unit = unit_of(path, projs)
        owner = claimed.get(path, unit)                       # whose toolchain and options apply
        info = projs.get(owner, {})
        deps = []
        for imp in parse_imports((repo / path).read_text(encoding="utf-8", errors="replace")):
            rel = imp.replace("«", "").replace("»", "").replace(".", "/") + ".lean"
            for base in ([unit] if unit != "." else []) + ["."]:
                cand = rel if base == "." else f"{base}/{rel}"
                if cand in known and cand != path:
                    deps.append(cand)
                    break
        entries[path] = {"path": path, "unit": unit, "env_project": owner, "module": module_name(path, unit),
                         "toolchain": info.get("toolchain") or root_tc, "options": info.get("options", {}),
                         "deps": sorted(set(deps))}
    return {"files": entries, "order": _topological(entries)}


def _topological(entries: dict[str, dict]) -> list[str]:
    order, state = [], {}

    def visit(p: str, stack: tuple[str, ...]) -> None:
        if state.get(p) == 2:
            return
        if state.get(p) == 1:
            raise SystemExit(f"import cycle: {' -> '.join(stack + (p,))}")
        state[p] = 1
        for d in entries[p]["deps"]:
            visit(d, stack + (p,))
        state[p] = 2
        order.append(p)

    for p in sorted(entries):
        visit(p, ())
    return order


def shard_of(path: str, shards: int) -> int:
    return int(hashlib.sha256(path.encode()).hexdigest(), 16) % shards


def closure(paths: list[str], entries: dict[str, dict]) -> set[str]:
    need, todo = set(), list(paths)
    while todo:
        p = todo.pop()
        if p not in need:
            need.add(p)
            todo.extend(entries[p]["deps"])
    return need


# ------------------------------------------------------------------------------------------------ running

class LeanEnvironment:
    """`lean` and LEAN_PATH for one toolchain, taken from a lake project whose packages are already fetched."""

    def __init__(self, toolchain: str, project: Path):
        self.toolchain, self.project = toolchain, project
        self.lean = self._lake("which", "lean")
        self.lean_path = self._lake("printenv", "LEAN_PATH")
        version = subprocess.run([self.lean, "--version"], capture_output=True, text=True, timeout=120).stdout.strip()
        want = toolchain.rsplit(":", 1)[-1].lstrip("v")
        if want not in version:
            raise SystemExit(f"--env {toolchain}={project}: lean there is '{version}', not {want}")
        self.version = version

    def _lake(self, *cmd: str) -> str:
        proc = subprocess.run(["lake", "env", *cmd], cwd=self.project, capture_output=True, text=True, timeout=1800)
        if proc.returncode != 0 or not proc.stdout.strip():
            raise SystemExit(f"lake env {' '.join(cmd)} failed in {self.project}: {proc.stderr.strip()[:400]}")
        return proc.stdout.strip().splitlines()[-1]


def _first_error(text: str) -> str:
    for line in text.splitlines():
        if "error" in line.lower():
            return line.strip()[:400]
    return (text.strip().splitlines() or ["no output"])[-1][:400]


def _lean(env: LeanEnvironment, args: list[str], lean_path: list[Path], cwd: Path, timeout: int) -> tuple[int, str]:
    penv = dict(os.environ, LEAN_PATH=os.pathsep.join([*map(str, lean_path), env.lean_path]))
    try:
        proc = subprocess.run([env.lean, *args], cwd=cwd, env=penv, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return -1, "TIMEOUT"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def check_file(entry: dict, repo: Path, out: Path, env: LeanEnvironment, timeout: int, serial: int) -> dict:
    """Compile one file and audit it. Returns the ledger entry (C2, C3, C4)."""
    src = repo / entry["path"]
    result = {"path": entry["path"], "sha256": sha256(src), "toolchain": entry["toolchain"],
              "module": entry["module"], "unit": entry["unit"], "lean": env.version}
    root_out = out / "olean" / "_root"
    unit_out = root_out if entry["unit"] == "." else out / "olean" / entry["unit"].replace("/", "__")
    olean = unit_out / (entry["module"].replace("«", "").replace("»", "").replace(".", "/") + ".olean")
    olean.parent.mkdir(parents=True, exist_ok=True)
    options = [f"-D{k}={str(v).lower() if isinstance(v, bool) else v}" for k, v in sorted(entry["options"].items())]
    started = time.time()
    code, text = _lean(env, [*options, "-o", str(olean), str(src)], [unit_out, root_out], repo, timeout)
    result["options"] = "project" if options else "lean-defaults"
    if code not in (0, -1) and options:
        # The project's leanOptions bind only the libraries its lakefile names. A file outside them may have
        # been written under Lean's defaults, so try those once and record which configuration compiled.
        first = _first_error(text)
        code, text = _lean(env, ["-o", str(olean), str(src)], [unit_out, root_out], repo, timeout)
        if code == 0:
            result.update(options="lean-defaults", project_options_error=first)
    result["compile_seconds"] = round(time.time() - started, 1)
    if code == -1:
        return {**result, "status": "TIMEOUT", "detail": f"compile exceeded {timeout}s"}
    if code < -1:
        return {**result, "status": "COMPILE_FAILED", "detail": f"lean was killed by signal {-code} (out of memory?)"}
    if code != 0 or not olean.is_file():
        return {**result, "status": "COMPILE_FAILED", "detail": _first_error(text.replace(str(repo) + os.sep, ""))}
    audit_dir = out / "audit" / f"m{serial}"
    audit_dir.mkdir(parents=True, exist_ok=True)
    alias = f"CensusTarget{serial}"
    shutil.copyfile(olean, audit_dir / f"{alias}.olean")
    (audit_dir / "Audit.lean").write_text(AUDIT_TEMPLATE.format(module=alias), encoding="utf-8")
    code, text = _lean(env, [str(audit_dir / "Audit.lean")], [audit_dir, unit_out, root_out], audit_dir, timeout)
    shutil.rmtree(audit_dir, ignore_errors=True)
    if code == -1:
        return {**result, "status": "TIMEOUT", "detail": f"audit exceeded {timeout}s"}
    m = RESULT_RE.search(text)
    if code != 0 or not m:
        return {**result, "status": "COMPILE_FAILED", "detail": "audit failed: " + _first_error(text)}
    checked, theorems = int(m.group(1)), int(m.group(2))
    axioms = sorted(a.strip() for a in m.group(3).split(",") if a.strip())
    violations = [v.strip() for v in m.group(4).split(";") if v.strip()]
    result.update(declarations=checked, theorems=theorems, axioms=axioms)
    if checked == 0:
        return {**result, "status": "NO_DECLARATIONS", "detail": "the file contributes no declaration"}
    if violations or any(a not in ALLOWED_AXIOMS for a in axioms):
        return {**result, "status": "NONSTANDARD_AXIOM", "violations": violations,
                "detail": "axioms outside the allowlist: " + ", ".join(a for a in axioms if a not in ALLOWED_AXIOMS)}
    return {**result, "status": "CLEAN"}


def run(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    plan = build_plan(repo)
    entries = plan["files"]
    index, shards = (int(x) for x in args.shard.split("/"))
    owned = [p for p in plan["order"] if shard_of(p, shards) == index]
    if args.only:
        owned = [p for p in owned if any(p.startswith(prefix) for prefix in args.only)]
    if args.toolchain:
        owned = [p for p in owned if entries[p]["toolchain"] in args.toolchain]
    need = closure(owned, entries)
    envs: dict[str, LeanEnvironment] = {}
    for spec in args.env:
        toolchain, project = spec.split("=", 1)
        envs[toolchain] = LeanEnvironment(toolchain, (repo / project).resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    for serial, path in enumerate(p for p in plan["order"] if p in need):
        entry = entries[path]
        base = {"path": path, "sha256": sha256(repo / path), "toolchain": entry["toolchain"],
                "module": entry["module"], "unit": entry["unit"]}
        failed = [d for d in entry["deps"] if results[d]["status"] in
                  ("COMPILE_FAILED", "DEP_FAILED", "TIMEOUT", "NO_ENVIRONMENT")]
        if failed:
            results[path] = {**base, "status": "DEP_FAILED", "detail": "imports " + ", ".join(failed)}
        elif entry["toolchain"] not in envs:
            results[path] = {**base, "status": "NO_ENVIRONMENT",
                             "detail": f"no --env for {entry['toolchain'] or 'an undeclared toolchain'}"}
        else:
            results[path] = check_file(entry, repo, out, envs[entry["toolchain"]], args.timeout, serial)
        if path in owned:
            r = results[path]
            print(f"[{index}/{shards}] {r['status']:<17} {path} {r.get('detail', '')}"[:300], flush=True)
    report = {"schema": "viridis-canon/compile-census-shard/v1", "shard": args.shard,
              "commit": args.commit or _commit(repo), "entries": [results[p] for p in owned]}
    tag = "-" + re.sub(r"[^0-9A-Za-z.]+", "_", "+".join(args.toolchain)) if args.toolchain else ""
    target = out / f"shard-{index}-of-{shards}{tag}.json"
    target.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {target} ({len(owned)} files)")
    return 0


def _commit(repo: Path) -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


# ------------------------------------------------------------------------------------------------ merging

def merge_reports(reports: list[dict], expected: list[str]) -> dict:
    """C1: combine shard reports into one ledger, or raise ValueError naming what is missing or doubled."""
    entries: dict[str, dict] = {}
    commits = set()
    for rep in reports:
        commits.add(rep.get("commit", "unknown"))
        for e in rep["entries"]:
            if e["path"] in entries:
                raise ValueError(f"duplicate entry: {e['path']}")
            if e.get("status") not in STATUSES:
                raise ValueError(f"unknown status for {e['path']}: {e.get('status')}")
            entries[e["path"]] = e
    missing = sorted(set(expected) - set(entries))
    extra = sorted(set(entries) - set(expected))
    if missing or extra:
        raise ValueError(f"ledger incomplete: missing {missing[:10]} ({len(missing)}), unknown {extra[:10]} ({len(extra)})")
    if len(commits) != 1:
        raise ValueError(f"shards ran at different commits: {sorted(commits)}")
    counts = {s: 0 for s in STATUSES}
    for e in entries.values():
        counts[e["status"]] += 1
    return {"schema": "viridis-canon/compile-census/v1", "commit": commits.pop(), "files": len(entries),
            "counts": counts, "declarations": sum(e.get("declarations", 0) for e in entries.values()),
            "theorems": sum(e.get("theorems", 0) for e in entries.values()),
            "allowed_axioms": list(ALLOWED_AXIOMS), "entries": [entries[p] for p in sorted(entries)]}


def regressions(ledger: dict, known_gaps: dict) -> list[str]:
    """Files that are not CLEAN / NO_DECLARATIONS and are not listed, with the same status, in known gaps."""
    allowed = {g["path"]: g["status"] for g in known_gaps.get("gaps", [])}
    out = []
    for e in ledger["entries"]:
        if e["status"] in ("CLEAN", "NO_DECLARATIONS"):
            continue
        if allowed.get(e["path"]) != e["status"]:
            out.append(f"{e['path']}: {e['status']} {e.get('detail', '')}"[:300])
    return out


def summary_md(ledger: dict, known_gaps: dict | None = None) -> str:
    kinds = {g["path"]: g.get("kind", "") for g in (known_gaps or {}).get("gaps", [])}
    c = ledger["counts"]
    lines = ["# Canon compile census", "",
             f"Commit `{ledger['commit']}`. {ledger['files']} Lean files, {ledger['declarations']} declarations "
             f"({ledger['theorems']} theorems) audited.", "", "| Status | Files |", "|---|---|"]
    lines += [f"| {s} | {c[s]} |" for s in STATUSES]
    bad = [e for e in ledger["entries"] if e["status"] not in ("CLEAN", "NO_DECLARATIONS")]
    if bad:
        by_kind: dict[str, int] = {}
        for e in bad:
            k = kinds.get(e["path"], "not recorded")
            by_kind[k] = by_kind.get(k, 0) + 1
        lines += ["", "## Not clean", "", "| Kind (from known_gaps.json) | Files |", "|---|---|"]
        lines += [f"| {k} | {n} |" for k, n in sorted(by_kind.items())]
        show = [e for e in bad if kinds.get(e["path"], "not recorded") in ("open_gap", "not recorded", "quarantined")]
        if show:
            lines += ["", "| File | Kind | Status | Detail |", "|---|---|---|---|"]
            lines += [f"| `{e['path']}` | {kinds.get(e['path'], 'not recorded')} | {e['status']} | "
                      f"{str(e.get('detail', '')).replace('|', '/')[:200]} |" for e in show]
    return "\n".join(lines) + "\n"


def merge(args: argparse.Namespace) -> int:
    repo = args.repo.resolve()
    reports = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.reports]
    try:
        ledger = merge_reports(reports, lean_files(repo))
    except ValueError as exc:
        print(f"CENSUS INCOMPLETE: {exc}", file=sys.stderr)
        return 2
    if args.ledger:
        args.ledger.parent.mkdir(parents=True, exist_ok=True)
        args.ledger.write_text(json.dumps(ledger, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    gaps = None
    if args.known_gaps:
        gaps = json.loads(args.known_gaps.read_text(encoding="utf-8")) if args.known_gaps.is_file() else {"gaps": []}
    md = summary_md(ledger, gaps)
    if args.summary:
        args.summary.write_text(md, encoding="utf-8")
    print(md)
    if gaps is not None:
        reg = regressions(ledger, gaps)
        closed = sorted(g["path"] for g in gaps.get("gaps", [])
                        if {e["path"]: e["status"] for e in ledger["entries"]}.get(g["path"]) in ("CLEAN", "NO_DECLARATIONS"))
        if closed:
            print("Recorded gaps that are now clean (remove them from known_gaps.json): " + ", ".join(closed))
        if reg:
            print("CENSUS REGRESSIONS (not clean and not a recorded known gap):", file=sys.stderr)
            for r in reg:
                print("  " + r, file=sys.stderr)
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="compile_census", description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", type=Path, default=REPO)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="print the files, their units, toolchains and canon imports")
    r = sub.add_parser("run", help="compile and audit one shard")
    r.add_argument("--env", action="append", default=[], metavar="TOOLCHAIN=LAKE_PROJECT",
                   help="a lake project (packages fetched) that provides lean and LEAN_PATH for a toolchain")
    r.add_argument("--shard", default="0/1")
    r.add_argument("--only", action="append", default=[], help="restrict to paths with this prefix (for trials)")
    r.add_argument("--toolchain", action="append", default=[],
                   help="only files that declare this toolchain; the others belong to another job")
    r.add_argument("--commit", help="commit to record (a pull request builds a merge commit; pass its head)")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--timeout", type=int, default=2700, help="seconds per compile and per audit")
    m = sub.add_parser("merge", help="combine shard reports into the ledger; exit 2 if incomplete (C1)")
    m.add_argument("reports", nargs="+")
    m.add_argument("--ledger", type=Path)
    m.add_argument("--summary", type=Path)
    m.add_argument("--known-gaps", type=Path, help="exit 1 if a file is not clean and not recorded here")
    args = ap.parse_args(argv)
    if args.cmd == "plan":
        plan = build_plan(args.repo.resolve())
        print(json.dumps(plan, indent=1, sort_keys=True))
        return 0
    return run(args) if args.cmd == "run" else merge(args)


if __name__ == "__main__":
    sys.exit(main())
