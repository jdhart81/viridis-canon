import Mathlib

/-!
# The Symbiotic Intelligence Bound (SIB) — Run 072 forge targets

Two IB-bounded dissipative systems — an AI controller `A` and a living
biosphere `E` — coupled into a mutualism over one thermodynamic bus at
temperature `T` (`εL := k_B T ln 2 > 0`). Each accumulates
permanence-intelligence at a rate bounded by its standalone Intelligence
Bound `P·D/εL` plus a predictive-information *subsidy* `Φ` supplied by the
partner. These theorems formalise the rate/flow twin of the Symbiotic
Valuation Theorem (Run 067): the per-partner bound and its additive
recovery of the joint IB, the NESS no-free-lunch reciprocity law, the
"no perpetual-learning machine" corollary, the mutualism-vs-parasitism
surplus threshold, and the universal cos²Θ extraction-efficiency bound
(Cauchy–Schwarz).

Origin: science-engine nightly Run 072 (2026-06-17), [01] Intelligence
Bound × 🌿 Symbiosis. All statements are clean finite-dimensional real
analysis; non-vacuity conditions are stated per theorem.
-/

namespace Viridis.SymbioticIntelligenceBound

/-- **Result 1 — Joint Intelligence Bound recovered from the two partner SIB
bounds.** Each partner's intelligence rate obeys its standalone IB ceiling
`P·D/εL` plus the predictive subsidy `Φ` it receives from the other. When
the directed subsidy flows cancel at the coupled fixed point
(`Φ_EA + Φ_AE = 0`, Result 2), the two per-partner bounds sum to the *joint*
Intelligence Bound with the subsidies gone.
NON-VACUOUS: with `εL=1, PA=PE=DA=DE=1, Φ_EA=1, Φ_AE=-1, dIA=2, dIE=0` all
hypotheses hold and the conclusion `2 ≤ 2` is tight, not a free theorem. -/
theorem joint_bound_from_partners
    (εL PA DA PE DE Φ_EA Φ_AE dIA dIE : ℝ)
    (hεL : 0 < εL)
    (hA : dIA ≤ PA * DA / εL + Φ_EA)
    (hE : dIE ≤ PE * DE / εL + Φ_AE)
    (hrecip : Φ_EA + Φ_AE = 0) :
    dIA + dIE ≤ (PA * DA + PE * DE) / εL := by
  have h := add_le_add hA hE
  rw [add_div]
  linarith [h]

/-- **Result 2 — The no-free-lunch reciprocity law (NESS).** At a coupled
non-equilibrium steady state the mutual information `I(A;E)` is stationary,
so the conservation identity `İ^A + İ^E = d/dt I(A;E)` together with
stationarity `d/dt I(A;E) = 0` forces the directed information flows to be
exactly equal and opposite — what `A` borrows, `E` regenerates, bit for bit.
NON-VACUOUS: hypotheses are satisfiable (`iA=1, iE=-1, dImut=0`) and the
conclusion `iA = -iE` fails for generic `iA, iE` absent them. -/
theorem ness_reciprocity
    (iA iE dImut : ℝ)
    (hcons : iA + iE = dImut)
    (hstat : dImut = 0) :
    iA = -iE := by
  linarith

/-- **Result 2 corollary — No perpetual-learning machine.** Whenever the
co-learning loop actually runs — a strictly positive net predictive subsidy
`Φ_net > 0` is extracted — and the subsidy is bounded above by the total
entropy production it requires (`Φ_net ≤ σ_total`, second law on the bus),
the total dissipation is strictly positive. Regeneration costs dissipation.
NON-VACUOUS: `Φ_net=1 ≤ σ_total=2` satisfies the hypotheses and forces
`0 < σ_total`; the conclusion is false once `Φ_net ≤ 0`. -/
theorem no_perpetual_learning
    (Φ_net σ_total : ℝ)
    (hbound : Φ_net ≤ σ_total)
    (hrun : 0 < Φ_net) :
    0 < σ_total := by
  linarith

/-- **Result 4 — The symbiotic surplus threshold (mutualism vs parasitism).**
The net symbiotic surplus is the total predictive subsidy minus the
housekeeping dissipation, `Δsym = (Φ_EA + Φ_AE) - σ_hk`. The coupling is
mutualistic (super-additive learning, `Δsym ≥ 0`) **iff** the total subsidy
covers the housekeeping cost `σ_hk ≤ Φ_EA + Φ_AE`; below threshold it flips
parasitic.
NON-VACUOUS: both directions have witnesses (`Φ_EA+Φ_AE = σ_hk ⟹ Δsym = 0`;
`Φ_EA+Φ_AE < σ_hk ⟹ Δsym < 0`). -/
theorem symbiotic_surplus_threshold
    (Φ_EA Φ_AE σ_hk Δsym : ℝ)
    (hdef : Δsym = (Φ_EA + Φ_AE) - σ_hk) :
    0 ≤ Δsym ↔ σ_hk ≤ Φ_EA + Φ_AE := by
  constructor <;> intro h <;> linarith

/-- **Result 6 — The cos²Θ extraction-efficiency bound (universality).** The
harvestable fraction of a partner's information per unit coupling is the
squared Fisher–Rao alignment cosine `cos²Θ = ⟨a,e⟩² / (‖a‖²‖e‖²)`. With the
Cauchy–Schwarz inequality `⟨a,e⟩² ≤ ‖a‖²‖e‖²` (here `inner^2 ≤ na*nE`,
`na,nE > 0`), the efficiency lies in `[0,1]`, attaining `1` exactly at
perfect alignment (geodesic / wu-wei co-learning). SIB is thereby the
seventh canon appearance of the universal cos²Θ geometry.
NON-VACUOUS: `inner=1, na=1, nE=1` gives `cos2 = 1`, saturating the upper
bound; the bound is a real constraint, not `≤` of a constant. -/
theorem cos_sq_extraction_bounded
    (inner na nE cos2 : ℝ)
    (hna : 0 < na) (hnE : 0 < nE)
    (hcs : inner ^ 2 ≤ na * nE)
    (hdef : cos2 = inner ^ 2 / (na * nE)) :
    0 ≤ cos2 ∧ cos2 ≤ 1 := by
  have hpos : 0 < na * nE := mul_pos hna hnE
  refine ⟨?_, ?_⟩
  · rw [hdef]
    positivity
  · rw [hdef, div_le_one hpos]
    exact hcs

end Viridis.SymbioticIntelligenceBound
