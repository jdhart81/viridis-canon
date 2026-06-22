/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# AxiomAudit — ENFORCING axiom allowlist for the Viridis Canon spine (INV-3)

This is a build target. Building it walks the environment, finds every
declaration that originates in a verified-spine module, collects the axioms each
one depends on, and **throws** (failing `lake build`) if any declaration depends
on an axiom outside the allowlist `{propext, Classical.choice, Quot.sound}` — or
on `sorryAx` (i.e. a `sorry`). It is name-free: it does not enumerate theorem
names, so it cannot silently miss a theorem and is robust to namespaces.

Replaces the previous informational "axiom audit" step that only printed a
message. If a declaration sneaks in a `sorry` or an extra axiom, CI goes red.

NB: this is the one file in v9.1.0 that has not been locally compiled (no Lean
toolchain in the authoring sandbox). It uses only stable `Lean` APIs; validate on
the first CI run and adjust the three flagged API calls if the pinned toolchain
differs. The shell gates in `.github/workflows/ci.yml` enforce the no-`sorry`
property independently, so enforcement does not rest on this file alone.
-/
import Mathlib
-- Verified-spine modules (P9 is QUARANTINED and intentionally absent):
import P0_IntelligenceBound_COMPILED
import P1_DScore
import P2_HDFM_POC
import P3_Impossibility
import P4_ThermodynamicEconomics
import Bridge_MissionFeasibility
import PSIT_Symplectic
import EcoChain_DendriticCorridor
import Book_HeatAndDisorder
import ConservationOperator
import Bridge_EcoChainInstrument
import Bridge_BiosphereProductivity
import BiosphereErasureBound
import BoundedMemoryLearning
import BoundedMemoryDissipation
import SymbioticIntelligenceBound
import MRAB
import P5_SLSPT.IntelligenceBound
import P5_SLSPT.InverseSquare
import P5_SLSPT.ShadowPrice
import P5_SLSPT.ShadowPriceLevelCurves
import P5_SLSPT.SLSPTTowerOrdering
import P7_PlasmaNFix.Foundations
import P7_PlasmaNFix.Energy
import P7_PlasmaNFix.Integration

open Lean

/-- Axioms permitted anywhere in the verified spine. -/
def viridisAllowedAxioms : List Name :=
  [``propext, ``Classical.choice, ``Quot.sound]

/-- Modules whose declarations constitute the verified spine. Keep in lockstep
    with `lakefile.toml` `defaultTargets` (minus quarantined modules). -/
def viridisSpineModules : List Name :=
  [`P0_IntelligenceBound_COMPILED, `P1_DScore, `P2_HDFM_POC, `P3_Impossibility,
   `P4_ThermodynamicEconomics, `Bridge_MissionFeasibility, `PSIT_Symplectic,
   `EcoChain_DendriticCorridor, `Book_HeatAndDisorder, `ConservationOperator,
   `Bridge_EcoChainInstrument, `Bridge_BiosphereProductivity,
   `BiosphereErasureBound, `BoundedMemoryLearning, `BoundedMemoryDissipation,
   `SymbioticIntelligenceBound, `MRAB,
   `P5_SLSPT.IntelligenceBound, `P5_SLSPT.InverseSquare, `P5_SLSPT.ShadowPrice,
   `P5_SLSPT.ShadowPriceLevelCurves, `P5_SLSPT.SLSPTTowerOrdering,
   `P7_PlasmaNFix.Foundations, `P7_PlasmaNFix.Energy, `P7_PlasmaNFix.Integration]

run_cmd do
  let env ← getEnv
  let modNames := env.header.moduleNames
  let mut spineIdxs : Array Nat := #[]
  for h : i in [0:modNames.size] do
    if viridisSpineModules.contains modNames[i]! then
      spineIdxs := spineIdxs.push i
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
          unless viridisAllowedAxioms.contains a do
            violations := violations.push (declName, a)
  unless violations.isEmpty do
    throwError s!"AXIOM AUDIT FAILED — {violations.size} declaration(s) depend on \
disallowed axioms (e.g. sorryAx): {violations}"
  logInfo s!"Axiom audit PASSED — {checked} spine declarations, axioms ⊆ \
{viridisAllowedAxioms}"
