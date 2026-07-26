/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# Historical P0 axiom audit

Runs under the exact Lean 4.24 / Mathlib f897ebcf toolchain declared by
`P0_IntelligenceBound_COMPILED.lean`. The current-toolchain spine is audited
separately by `AxiomAudit.lean`.
-/
import P0_IntelligenceBound_COMPILED

open Lean

def viridisP0AllowedAxioms : List Name :=
  [``propext, ``Classical.choice, ``Quot.sound]

run_cmd do
  let env ← getEnv
  let modNames := env.header.moduleNames
  let mut p0Idxs : Array Nat := #[]
  for h : i in [0:modNames.size] do
    if modNames[i]! == `P0_IntelligenceBound_COMPILED then
      p0Idxs := p0Idxs.push i
  if p0Idxs.isEmpty then
    throwError "P0 module not found in environment"
  let mut violations : Array (Name × Name) := #[]
  let mut checked : Nat := 0
  for (declName, _) in env.constants.toList do
    if declName.isInternal then continue
    match env.getModuleIdxFor? declName with
    | none => pure ()
    | some midx =>
      if p0Idxs.contains midx.toNat then
        checked := checked + 1
        let axs ← Lean.collectAxioms declName
        for axiomName in axs do
          unless viridisP0AllowedAxioms.contains axiomName do
            violations := violations.push (declName, axiomName)
  unless violations.isEmpty do
    throwError s!"P0 AXIOM AUDIT FAILED — {violations.size} declaration(s): {violations}"
  logInfo s!"P0 axiom audit PASSED — {checked} declarations, axioms ⊆ \
{viridisP0AllowedAxioms}"
