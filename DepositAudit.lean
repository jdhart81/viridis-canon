/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# DepositAudit — ENFORCING axiom allowlist for standalone / journal-branch deposits

Sibling of `AxiomAudit.lean`. That file audits the verified **spine**; this one
audits **deposits** — the `series/` modules that carry their own Zenodo DOI.

## Why this file exists

Until 2026-07-29 the canon CI compiled only `lakefile.toml` `defaultTargets`.
No `series/` journal-branch deposit was ever in that list. A green
`lean-build-current` therefore proved that the pre-existing corpus still built
and said nothing at all about the artifact that had just been deposited: every
standalone DOI rested on the depositor's own unreproduced run.

That is precisely the failure mode the canon exists to rule out. On *Trees
Cannot Cut* (`series/DualCorridor.lean`, DOI 10.5281/zenodo.21686447) Aristotle
run 1 returned a file that **compiled** while the theorem the paper is named
after was still unproved — it went through on `sorryAx`. Only `#print axioms`
caught it. A CI that goes green without ever touching the deposit is that same
misleading green light, one level up.

## What it does

Building this target imports every module named in `DEPOSIT_MANIFEST.txt`, walks
the environment, collects the axioms every declaration originating in those
modules depends on, and **throws** — failing `lake build` — if any depends on an
axiom outside `{propext, Classical.choice, Quot.sound}`, `sorryAx` included.

It is **name-free**: it does not enumerate theorem names, so it cannot silently
miss a declaration and is robust to namespaces and to later edits that add new
results to an audited file.

Non-vacuity is a *separate* gate and is not checked here — a conditional theorem
whose hypothesis is unsatisfiable passes an axiom audit cleanly. See
`tools/vacuity_lint.py` and the exhibited-witness requirement in
`VIRIDIS_ZENODO_SUBMISSION_PROTOCOL.md` §4 gate 2.

## Adding a deposit

Three edits, all in the PR that adds the `.lean`:
  1. `DEPOSIT_MANIFEST.txt`  — add the source path
  2. `lakefile.toml`         — add a `[[lean_lib]]` for the module
  3. this file               — add the `import` and the `viridisDepositModules` entry

The `deposit-verify` CI job then rebuilds and re-audits it on every push.
-/
import Mathlib
-- Deposit modules under re-verification. Keep in lockstep with
-- DEPOSIT_MANIFEST.txt and the `[[lean_lib]]` entries in lakefile.toml.
import series.DualCorridor

open Lean

/-- Axioms permitted in a deposited artifact. Identical to the spine allowlist:
    a deposit carrying its own DOI is held to the same standard as the spine. -/
def viridisDepositAllowedAxioms : List Name :=
  [``propext, ``Classical.choice, ``Quot.sound]

/-- Modules whose declarations are re-verified as deposits.
    Keep in lockstep with `DEPOSIT_MANIFEST.txt`. -/
def viridisDepositModules : List Name :=
  [`series.DualCorridor]

run_cmd do
  let env ← getEnv
  let modNames := env.header.moduleNames
  let mut depositIdxs : Array Nat := #[]
  for h : i in [0:modNames.size] do
    if viridisDepositModules.contains modNames[i]! then
      depositIdxs := depositIdxs.push i
  -- Fail closed: a manifest entry that produced no module means the import list
  -- and the manifest have drifted apart, and the deposit is silently unaudited.
  unless depositIdxs.size = viridisDepositModules.length do
    throwError s!"DEPOSIT AUDIT FAILED — expected {viridisDepositModules.length} deposit \
module(s) in the environment, found {depositIdxs.size}. DEPOSIT_MANIFEST.txt, the imports \
in DepositAudit.lean and viridisDepositModules have drifted apart."
  let mut violations : Array (Name × Name) := #[]
  let mut checked : Nat := 0
  for (declName, _) in env.constants.toList do
    if declName.isInternal then continue
    match env.getModuleIdxFor? declName with
    | none => pure ()
    | some midx =>
      if depositIdxs.contains midx.toNat then
        checked := checked + 1
        let axs ← Lean.collectAxioms declName
        for a in axs do
          unless viridisDepositAllowedAxioms.contains a do
            violations := violations.push (declName, a)
  unless violations.isEmpty do
    throwError s!"DEPOSIT AXIOM AUDIT FAILED — {violations.size} declaration(s) in deposited \
artifacts depend on disallowed axioms (e.g. sorryAx): {violations}"
  -- A deposit that contributes no declarations is a broken import, not a pass.
  unless checked > 0 do
    throwError "DEPOSIT AUDIT FAILED — zero declarations audited. The deposit modules \
resolved but contributed nothing to the environment."
  logInfo s!"Deposit axiom audit PASSED — {checked} declarations across \
{depositIdxs.size} deposit module(s), axioms ⊆ {viridisDepositAllowedAxioms}"
