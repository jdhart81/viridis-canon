/- Enforcing audit for the local research candidate; no admission claim. -/
import InformationWeightedStewardship

open Lean

/-- Axioms permitted in this review candidate. -/
def iwsAllowedAxioms : List Name :=
  [``propext, ``Classical.choice, ``Quot.sound]

/-- Every module in the candidate family; coverage is enforced at build time. -/
def iwsModules : List Name :=
  [`InformationWeightedStewardship, `InformationWeightedStewardship.Algebra,
   `InformationWeightedStewardship.Trajectory, `InformationWeightedStewardship.Lifetime,
   `InformationWeightedStewardship.Equality, `InformationWeightedStewardship.Raw]

run_cmd do
  let env ← getEnv
  let modNames := env.header.moduleNames
  let mut spineIdxs : Array Nat := #[]
  for h : i in [0:modNames.size] do
    if iwsModules.contains modNames[i]! then
      spineIdxs := spineIdxs.push i
  unless spineIdxs.size == iwsModules.length do
    throwError "Candidate audit module coverage mismatch"
  let mut violations : Array (Name × Name) := #[]
  let mut checked : Nat := 0
  for (declName, _) in env.constants.toList do
    -- skip internal / compiler-generated names
    if declName.isInternal then continue
    match env.getModuleIdxFor? declName with
    | none => pure ()
    | some midx =>
      if spineIdxs.contains midx.toNat then
        checked := checked + 1
        let axs ← Lean.collectAxioms declName
        for a in axs do
          unless iwsAllowedAxioms.contains a do
            violations := violations.push (declName, a)
  unless violations.isEmpty do
    throwError s!"AXIOM AUDIT FAILED — {violations.size} declaration(s) depend on \
disallowed axioms (e.g. sorryAx): {violations}"
  logInfo s!"Information-weighted stewardship axiom audit PASSED — {checked} candidate declarations, axioms ⊆ \
{iwsAllowedAxioms}"
