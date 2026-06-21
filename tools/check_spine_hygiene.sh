#!/usr/bin/env bash
# check_spine_hygiene.sh — fast, compiler-independent integrity gates (INV-1/3).
# Run from the Aristotle-Pipeline dir. Exits nonzero on any violation.
#
# Gates:
#   1. No raw `sorry` / `admit` in CODE (comments/docstrings stripped first).
#   2. No homemade `axiom` declarations in the spine.
#   3. Vacuity linter clean on the spine (delegates to tools/vacuity_lint.py).
#
# The quarantined module P9_AI_Safety.lean is excluded by design.
set -uo pipefail
DIR="${1:-.}"
TOOLS="$(cd "$(dirname "$0")" && pwd)"
fail=0

# The verified-spine files (P9 quarantined → excluded).
mapfile -t SPINE < <(ls "$DIR"/*.lean 2>/dev/null | grep -v 'P9_AI_Safety.lean')

strip_comments() {  # remove /- ... -/ block comments and -- line comments
  python3 - "$1" <<'PY'
import re,sys
t=open(sys.argv[1],encoding="utf-8",errors="replace").read()
t=re.sub(r"/-.*?-/", "", t, flags=re.S)      # block comments (incl. /-! -/)
t=re.sub(r"--[^\n]*", "", t)                  # line comments
print(t)
PY
}

echo "== Gate 1/3: no raw sorry/admit in code =="
for f in "${SPINE[@]}"; do
  if strip_comments "$f" | grep -nE '\b(sorry|admit)\b' >/dev/null; then
    echo "  VIOLATION: $f contains sorry/admit in code"; fail=1
  fi
done
[ "$fail" -eq 0 ] && echo "  clean"

echo "== Gate 2/3: no homemade axiom declarations =="
for f in "${SPINE[@]}"; do
  if strip_comments "$f" | grep -nE '(^|\s)axiom\s' >/dev/null; then
    echo "  VIOLATION: $f declares its own axiom"; fail=1
  fi
done
[ "$fail" -eq 0 ] && echo "  clean"

echo "== Gate 3/3: vacuity linter =="
if ! python3 "$TOOLS/vacuity_lint.py" "${SPINE[@]}"; then
  echo "  VIOLATION: vacuity linter flagged CRITICAL pattern(s)"; fail=1
fi

echo "----------------------------------------"
if [ "$fail" -ne 0 ]; then
  echo "SPINE HYGIENE: FAILED"; exit 1
fi
echo "SPINE HYGIENE: PASSED (${#SPINE[@]} files)"
