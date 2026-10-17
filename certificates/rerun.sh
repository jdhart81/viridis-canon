#!/usr/bin/env bash
# Re-check one Viridis certificate on your own machine.
#
#   certificates/rerun.sh Run-129               # full check with leanprover/comparator
#   certificates/rerun.sh Run-129 --axioms-only # elaborate the solution and audit its axioms
#
# Needs: elan (https://github.com/leanprover/elan), git, python3.
# Full mode also needs leanprover/comparator and its prerequisites (landrun,
# lean4export, optionally nanoda); point COMPARATOR at the comparator binary or
# put it on PATH. See https://github.com/leanprover/comparator.
#
# The script builds a throwaway Lake project pinned to the run's exact Lean
# toolchain and Mathlib revision (from certificates/index.json), copies the
# run's challenge and solution files in as Challenge.lean and Solution.lean,
# fetches the Mathlib build cache, and runs the check. Nothing in this
# repository is modified.
set -euo pipefail

RUN="${1:?usage: certificates/rerun.sh Run-NNN [--axioms-only]}"
MODE="${2:-full}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$HERE/$RUN"
[ -d "$RUN_DIR" ] || { echo "no such run: $RUN" >&2; exit 2; }

python3 "$HERE/verify_bundle.py" "$HERE" >/dev/null || { echo "bundle integrity check failed; refusing to continue" >&2; exit 3; }

read -r TOOLCHAIN MATHLIB_REV SOLUTION CHALLENGE < <(python3 - "$HERE/index.json" "$RUN" <<'PY'
import json, sys
ix = json.load(open(sys.argv[1]))
r = next(r for r in ix["runs"] if r["run"] == sys.argv[2])
print(r["toolchain"], r["mathlib_rev"], r["files"]["solution"]["file"], r["files"]["challenge"]["file"])
PY
)

WORK="$(mktemp -d "${TMPDIR:-/tmp}/viridis-$RUN-XXXXXX")"
echo "work dir: $WORK"
cd "$WORK"
echo "$TOOLCHAIN" > lean-toolchain
cat > lakefile.toml <<EOF
name = "viridis_certificate_check"
version = "0.1.0"
defaultTargets = ["Solution", "Challenge"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4"
rev = "$MATHLIB_REV"

[[lean_lib]]
name = "Solution"

[[lean_lib]]
name = "Challenge"
EOF
cp "$RUN_DIR/$SOLUTION" Solution.lean
cp "$RUN_DIR/$CHALLENGE" Challenge.lean
cp "$RUN_DIR/comparator.config.json" config.json

echo "fetching Mathlib $MATHLIB_REV build cache (several GB the first time)..."
lake exe cache get

if [ "$MODE" = "--axioms-only" ]; then
  python3 - > Check.lean <<'PY'
import json
cfg = json.load(open("config.json"))
print(open("Solution.lean").read().rstrip("\n"))
print()
for n in cfg["theorem_names"]:
    print(f"#print axioms {n}")
PY
  echo "elaborating the solution and printing axioms..."
  lake env lean Check.lean 2>&1 | tee check.log
  python3 - <<'PY'
import json, re, sys
cfg = json.load(open("config.json"))
allowed = set(cfg["permitted_axioms"])
log = open("check.log").read()
seen = {}
for m in re.finditer(r"'([^']+)' depends on axioms: \[([^\]]*)\]", log):
    seen[m.group(1)] = {a.strip() for a in m.group(2).split(",") if a.strip()}
for m in re.finditer(r"'([^']+)' does not depend on any axioms", log):
    seen[m.group(1)] = set()
missing = [n for n in cfg["theorem_names"] if n not in seen]
extra = {n: sorted(a - allowed) for n, a in seen.items() if a - allowed}
errors = re.findall(r"^.*error.*$", log, re.M)
print(f"theorems audited: {len(seen)}/{len(cfg['theorem_names'])}")
if missing: print("not found:", missing)
if extra: print("axioms outside the permitted set:", extra)
if errors: print("elaboration errors:", len(errors))
ok = not missing and not extra and not errors
print("AXIOM AUDIT:", "PASSED" if ok else "FAILED")
sys.exit(0 if ok else 1)
PY
  exit $?
fi

COMPARATOR_BIN="${COMPARATOR:-$(command -v comparator || true)}"
[ -n "$COMPARATOR_BIN" ] || { echo "comparator not found; set COMPARATOR or rerun with --axioms-only" >&2; exit 4; }
echo "running comparator..."
lake env "$COMPARATOR_BIN" config.json
