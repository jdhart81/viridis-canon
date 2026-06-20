/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Intelligence–Biosphere Productivity Duality
===========================================

A bridge theorem connecting the Intelligence Bound (P0; Hart 2025/2026)
to the information-thermodynamic ceiling on planetary biosphere
productivity (Turyshev, "Information-Thermodynamic Bounds on Planetary
Biosphere Productivity", arXiv:2512.07199; gate framework
arXiv:2606.02648 / Discover Life 2026).

Both results live on a single "thermodynamic ledger": a usable
free-energy budget is partitioned between processing heritable /
predictive information (an irreducible Landauer cost) and the work that
remains for the system's objective. The two papers read the SAME
Landauer inequality from opposite sides:

  • Intelligence Bound (maintenance / cost view): information is the objective,
    power is the budget. Thermodynamic branch:
        İ ≤ P / (k_B T ln 2).
  • Turyshev biosphere productivity (cost view): information processing
    is a power TAX  P_info = (k_B T ln 2)·İ  subtracted from the usable
    free-energy flux before the remainder is converted to biomass (net
    primary productivity, NPP).

This module makes the correspondence precise:

  1. `landauer_duality` — the IB thermodynamic ceiling and the biosphere
     information-power tax are literally the same inequality.
  2. `conserved_ledger` — the information-allocated budget splits exactly
     into information power plus productivity-equivalent power
     (Turyshev's "common thermodynamic ledger", stated as an identity).
  3. `info_productivity_tradeoff` — the NPP ceiling is monotone
     decreasing in the heritable-information rate (the
     "information–productivity trade-off").
  4. `positive_productivity_iff_landauer` — a biosphere has non-negative
     productivity ceiling iff its heritable-information rate obeys the
     SAME Landauer ceiling the IB imposes on learning rate.
  5. `min_branch_decomposition` — the full IB bound
        İ ≤ min(ρB, P/(k_B T ln 2))
     splits into a Shannon coding-capacity branch (ρB) and the
     thermodynamic info-power-tax branch.
  6. `intelligence_productivity_duality` (headline) — any biosphere
     obeying the Intelligence Bound automatically pays an info-power tax
     within budget and therefore has a non-negative productivity ceiling
     equal to η·(P − (k_B T ln 2)·İ).

CAVEAT (assumptions flagged for review, since part of the duality is
interpretive — these are the assumptions Turyshev asked to scrutinise):
  • The thermodynamic-branch correspondence (theorems 1,2,3,4,6) is
    EXACT: both sides are the Landauer cost k_B T ln 2 per bit. Here `P`
    is the information-allocated slice of the planetary flux Φ, namely
    `P = Φ − P_habitability − P_metabolism`.
  • The data-branch correspondence (theorem 5: ρB ↔ fidelity × copy
    rate) is INTERPRETIVE: it requires identifying the IB observation
    channel with the biosphere's heredity channel (genome → phenotype),
    with B = template-copying throughput and ρ = information per template
    (copying fidelity × log alphabet size). This identification is
    carried as a definitional hypothesis, NOT a derived fact.

Lean: leanprover/lean4:v4.28.0
Mathlib: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Acceptance criteria:
  • Zero `sorry`; axiom audit limited to {propext, Classical.choice, Quot.sound}.
  • Each theorem's conclusion encodes the physical claim non-vacuously
    (no `True`, no `∃ x, x = formula` shells).
-/

/-! ## v8 FRAMING CORRECTION (2026-06-16) — both sides of this duality are the COST
(maintenance/erasure) side of the ledger. The "Intelligence Bound" side is read as
the cost of maintaining heritable predictive information (Landauer-valid), NOT as a
floor on acquisition (Wolpert). This makes the correspondence with Turyshev's NPP
bound exact on the heritable-information cost ledger. Theorem statements UNCHANGED. -/

import Mathlib

set_option linter.mathlibStandardSet false
open scoped BigOperators Real Nat Pointwise
set_option maxHeartbeats 800000
set_option maxRecDepth 4000
set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

namespace Viridis.BiosphereProductivity

/-! ## §1 The planetary information–energy ledger -/

/-- A planet's coarse-grained free-energy ledger. `Phi` is the usable
    free-energy flux; `P_hab` and `P_met` are the powers committed to
    maintaining habitability and driving metabolism; `eta` is the
    biomass conversion efficiency; `kT = k_B T ln 2` is the Landauer
    cost per processed bit. -/
structure Planet where
  Phi    : ℝ
  P_hab  : ℝ
  P_met  : ℝ
  eta    : ℝ
  kT     : ℝ
  hPhi   : 0 ≤ Phi
  hP_hab : 0 ≤ P_hab
  hP_met : 0 ≤ P_met
  heta   : 0 < eta
  hkT    : 0 < kT

/-- Power available for heritable-information processing after the
    habitability and metabolic commitments: the IB "budget" `P`. -/
def infoBudget (pl : Planet) : ℝ := pl.Phi - pl.P_hab - pl.P_met

/-- Landauer information-power cost of processing heritable information
    at rate `Idot` (bits / s):  `P_info = (k_B T ln 2)·İ`. -/
def infoPower (pl : Planet) (Idot : ℝ) : ℝ := pl.kT * Idot

/-- Turyshev net-primary-productivity ceiling at heritable-information
    rate `Idot`:  efficiency × (info budget − Landauer info cost). -/
def nppCeiling (pl : Planet) (Idot : ℝ) : ℝ :=
  pl.eta * (infoBudget pl - infoPower pl Idot)

/-! ## §2 The thermodynamic branch is a shared Landauer inequality -/

/-- **T1 — Landauer duality.**  The Intelligence-Bound thermodynamic
    ceiling `İ ≤ P/(k_B T ln 2)` and the biosphere information-power tax
    `(k_B T ln 2)·İ ≤ P` are the same inequality. -/
theorem landauer_duality (pl : Planet) (Idot P : ℝ) :
    Idot ≤ P / pl.kT ↔ infoPower pl Idot ≤ P := by
  rw [infoPower, le_div_iff₀ pl.hkT, mul_comm Idot pl.kT]

/-- **T2 — Conserved ledger.**  The information-allocated budget splits
    exactly into the Landauer information power and the productivity-
    equivalent power `NPP/η`.  This is Turyshev's "common thermodynamic
    ledger", stated as an identity:  every watt of the budget is either
    spent processing heritable information or available for biomass. -/
theorem conserved_ledger (pl : Planet) (Idot : ℝ) :
    infoBudget pl = infoPower pl Idot + nppCeiling pl Idot / pl.eta := by
  have hη : pl.eta ≠ 0 := ne_of_gt pl.heta
  rw [nppCeiling, infoPower]
  field_simp
  ring

/-! ## §3 The information–productivity trade-off -/

/-- **T3 — Information–productivity trade-off.**  At fixed planetary
    budget, the NPP ceiling is monotone decreasing in the heritable-
    information rate: a biosphere that processes heritable information
    faster has a lower biomass ceiling. -/
theorem info_productivity_tradeoff (pl : Planet) {Idot₁ Idot₂ : ℝ}
    (h : Idot₁ ≤ Idot₂) :
    nppCeiling pl Idot₂ ≤ nppCeiling pl Idot₁ := by
  rw [nppCeiling, nppCeiling, infoPower, infoPower]
  have hk : pl.kT * Idot₁ ≤ pl.kT * Idot₂ :=
    mul_le_mul_of_nonneg_left h (le_of_lt pl.hkT)
  exact mul_le_mul_of_nonneg_left (by linarith) (le_of_lt pl.heta)

/-- **T4 — Positive productivity ⟺ Landauer feasibility.**  A biosphere
    has a non-negative productivity ceiling iff its heritable-information
    rate satisfies the same Landauer ceiling the IB imposes on learning
    rate.  The IB feasibility condition and the "biosphere can sustain
    positive productivity" condition are one and the same. -/
theorem positive_productivity_iff_landauer (pl : Planet) (Idot : ℝ) :
    0 ≤ nppCeiling pl Idot ↔ infoPower pl Idot ≤ infoBudget pl := by
  rw [nppCeiling]
  constructor
  · intro h
    by_contra hc
    push_neg at hc
    have hpos : 0 < infoPower pl Idot - infoBudget pl := by linarith
    nlinarith [mul_pos pl.heta hpos]
  · intro h
    have hnn : 0 ≤ infoBudget pl - infoPower pl Idot := by linarith
    exact mul_nonneg (le_of_lt pl.heta) hnn

/-! ## §4 The two IB branches, in biosphere terms -/

/-- **T5 — Branch decomposition.**  The full Intelligence Bound
    `İ ≤ min(ρB, P/(k_B T ln 2))` decomposes into the Shannon coding-
    capacity branch `İ ≤ ρB` and the thermodynamic info-power-tax branch
    `(k_B T ln 2)·İ ≤ P`.  Under the heredity-channel identification
    (B = template-copy rate, ρ = information per template), `ρB` is the
    biosphere's heritable coding capacity. -/
theorem min_branch_decomposition (pl : Planet) (Idot rhoB P : ℝ) :
    Idot ≤ min rhoB (P / pl.kT) ↔ (Idot ≤ rhoB ∧ infoPower pl Idot ≤ P) := by
  rw [le_min_iff, landauer_duality]

/-! ## §5 Headline duality theorem -/

/-- **T6 — Intelligence–Productivity Duality (headline).**  Any biosphere
    whose heritable-information rate obeys the Intelligence Bound
    `İ ≤ min(ρB, P/(k_B T ln 2))`, with `P = Φ − P_hab − P_met` the
    information-allocated budget, automatically (i) pays a Landauer
    info-power tax within budget and (ii) has a non-negative productivity
    ceiling, equal to `η·(P − (k_B T ln 2)·İ)`.

    Thus the same Landauer ceiling that bounds learning rate from above
    is precisely the condition guaranteeing the biosphere can sustain
    positive productivity: the Intelligence Bound and the biosphere
    productivity bound are dual faces of one inequality. -/
theorem intelligence_productivity_duality (pl : Planet) (Idot rhoB : ℝ)
    (hIB : Idot ≤ min rhoB (infoBudget pl / pl.kT)) :
    infoPower pl Idot ≤ infoBudget pl ∧
      0 ≤ nppCeiling pl Idot ∧
      nppCeiling pl Idot = pl.eta * (infoBudget pl - pl.kT * Idot) := by
  have hsplit := (min_branch_decomposition pl Idot rhoB (infoBudget pl)).mp hIB
  have htax : infoPower pl Idot ≤ infoBudget pl := hsplit.2
  refine ⟨htax, (positive_productivity_iff_landauer pl Idot).mpr htax, ?_⟩
  rw [nppCeiling, infoPower]

end Viridis.BiosphereProductivity
