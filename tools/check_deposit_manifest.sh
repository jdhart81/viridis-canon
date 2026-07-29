#!/usr/bin/env bash
# check_deposit_manifest.sh — fast, compiler-independent drift check.
#
# DEPOSIT_MANIFEST.txt, the imports in DepositAudit.lean, its
# `viridisDepositModules` list, and the lakefile targets must all agree. If they
# drift, a deposit can be listed as audited while nothing actually audits it —
# a silent pass, which is worse than a red build.
#
# DepositAudit.lean also fails closed at build time if the counts disagree. This
# script exists so the failure surfaces in ~1 second in the `verify` job instead
# of 90 minutes into a Lean build.
#
# Usage: bash tools/check_deposit_manifest.sh [repo-root]
set -euo pipefail
ROOT="${1:-.}"
cd "$ROOT"

MANIFEST="DEPOSIT_MANIFEST.txt"
AUDIT="DepositAudit.lean"
LAKEFILE="lakefile.toml"

for f in "$MANIFEST" "$AUDIT" "$LAKEFILE"; do
  [ -f "$f" ] || { echo "::error::missing $f"; exit 1; }
done

fail=0

# Manifest paths -> Lean module names (series/DualCorridor.lean -> series.DualCorridor)
paths=$(grep -vE '^[[:space:]]*(#|$)' "$MANIFEST" || true)
if [ -z "$paths" ]; then
  echo "note: DEPOSIT_MANIFEST.txt lists no deposits; nothing to check"
  exit 0
fi

count=0
while IFS= read -r p; do
  [ -n "$p" ] || continue
  count=$((count + 1))

  if [ ! -f "$p" ]; then
    echo "::error::DEPOSIT_MANIFEST.txt lists '$p' but that file does not exist"
    fail=1
    continue
  fi

  mod="${p%.lean}"
  mod="${mod//\//.}"

  grep -qE "^import[[:space:]]+${mod}[[:space:]]*$" "$AUDIT" \
    || { echo "::error::$AUDIT is missing 'import ${mod}' (from $MANIFEST)"; fail=1; }

  esc_mod="${mod//./\\.}"
  grep -qE "\`${esc_mod}([^A-Za-z0-9_.]|\$)" "$AUDIT" \
    || { echo "::error::$AUDIT viridisDepositModules is missing \`${mod}"; fail=1; }

  grep -qF "globs = [\"${mod}\"]" "$LAKEFILE" \
    || { echo "::error::$LAKEFILE has no [[lean_lib]] with globs = [\"${mod}\"]"; fail=1; }

  # A deposit is a published artifact: it must be traceable to a DOI.
  grep -qF "\"$p\"" catalog/config.json \
    || { echo "::error::catalog/config.json has no doi_by_path entry for '$p'"; fail=1; }
done <<< "$paths"

# Reverse direction: an import in DepositAudit.lean that no manifest line justifies
while IFS= read -r mod; do
  [ -n "$mod" ] || continue
  [ "$mod" = "Mathlib" ] && continue
  src="${mod//./\/}.lean"
  grep -qxF "$src" <<< "$paths" \
    || { echo "::error::$AUDIT imports '$mod' but $MANIFEST does not list '$src'"; fail=1; }
done < <(grep -oE '^import[[:space:]]+[A-Za-z0-9_.]+' "$AUDIT" | awk '{print $2}')

if [ "$fail" -ne 0 ]; then
  echo "::error::deposit manifest drift — a deposit may be listed as audited while nothing audits it"
  exit 1
fi

echo "deposit manifest consistent: $count deposit(s) wired through manifest, lakefile, audit imports and catalog DOI map"
