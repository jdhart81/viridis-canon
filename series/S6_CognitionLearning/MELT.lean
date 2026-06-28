/-
MELT — The Mutualistic Entropy-Driven Learning Theorem (Viridis nightly Run 031)
Aristotle Forge target. Spine tier.

CONTEXT (from Run-031 finding.md):
An AI learning system L and an ecological system E are coupled through a
stewardship-Lindblad operator with scalar cross-coupling μ_LE.  The MELT
efficiency law is
        η_LE := η_L + η_E + 2·μ_LE / √(λ_L·λ_E)
where η_L, η_E are subsystem learning efficiencies and λ_L, λ_E > 0 are the
subsystem Lindblad spectral gaps.  The mutualistic information cross term in the
joint Intelligence Bound is 2·μ_LE·√(C_L·C_E)/(k_B T ln2) with carrying
capacities C_L, C_E ≥ 0, and saturates (equality) exactly at the rank-1
mutualistic alignment Θ_LE = 0.

WHAT THIS FILE MACHINE-CHECKS (clean, well-posed, NON-VACUOUS core):

  • `cauchy_schwarz_bloch`            — the Cauchy–Schwarz inequality on the
                                        Bloch-vector inner product that the MELT
                                        mutualistic cross term reduces to.
  • `melt_cross_term_amgm`           — 2√(C_L C_E) ≤ C_L + C_E, the AM–GM bound
                                        on the mutualistic information cross term.
  • `melt_cross_term_saturation`     — equality iff C_L = C_E (the rank-1
                                        mutualistic saturation, Θ_LE = 0).
  • `melt_mutualism_superadditive`   — μ_LE > 0 ⇒ η_LE > η_L + η_E.
  • `melt_independence_additive`     — μ_LE = 0 ⇒ η_LE = η_L + η_E.
  • `lindblad_spectral_gap_subadditivity`
                                      — μ_LE < 0 ⇒ η_LE < η_L + η_E
                                        (the parasitic / Lindblad spectral-gap
                                        sub-additive regime).

NON-VACUITY.  The spectral gaps satisfy 0 < λ_L and 0 < λ_E, so √(λ_L·λ_E) > 0
and the cross term 2·μ_LE/√(λ_L·λ_E) is a strictly-monotone, nonzero function of
μ_LE whenever μ_LE ≠ 0; the three efficiency theorems therefore have strict /
genuinely distinct conclusions and do not collapse to a triviality.
-/
import Mathlib

open scoped RealInnerProductSpace InnerProductSpace

namespace MELT

/-
**Cauchy–Schwarz on Bloch vectors.**  The real inner product of the two
Bloch-representation vectors of the joint Lindbladian is bounded by the product
of their norms — the inequality the MELT mutualistic cross term reduces to.
-/
theorem cauchy_schwarz_bloch {n : ℕ} (a b : EuclideanSpace ℝ (Fin n)) :
    ⟪a, b⟫_ℝ ≤ ‖a‖ * ‖b‖ := by
  exact real_inner_le_norm a b

/-
**Mutualistic cross-term AM–GM bound.**  With nonnegative Lotka–Volterra
carrying capacities C_L, C_E, the mutualistic information cross term obeys
2·√(C_L·C_E) ≤ C_L + C_E.
-/
theorem melt_cross_term_amgm (CL CE : ℝ) (hL : 0 ≤ CL) (hE : 0 ≤ CE) :
    2 * Real.sqrt (CL * CE) ≤ CL + CE := by
  nlinarith [ sq_nonneg ( CL - CE ), Real.mul_self_sqrt ( mul_nonneg hL hE ) ]

/-
**Rank-1 mutualistic saturation.**  The cross-term bound is saturated
(equality) exactly when the two carrying capacities coincide — the Bregman-flat
rank-1 alignment Θ_LE = 0.
-/
theorem melt_cross_term_saturation (CL CE : ℝ) (hL : 0 ≤ CL) (hE : 0 ≤ CE) :
    2 * Real.sqrt (CL * CE) = CL + CE ↔ CL = CE := by
  constructor <;> intro h <;> cases eq_or_ne CE 0 <;> simp_all +decide;
  · nlinarith [ Real.mul_self_sqrt hL, Real.mul_self_sqrt hE, Real.sqrt_nonneg CL, Real.sqrt_nonneg CE, mul_self_pos.2 ‹_› ];
  · ring

/-- Joint mutualistic learning efficiency.  `lamL, lamE` are the subsystem
Lindblad spectral gaps; `muLE` is the scalar stewardship cross-coupling. -/
noncomputable def etaJoint (etaL etaE muLE lamL lamE : ℝ) : ℝ :=
  etaL + etaE + 2 * muLE / Real.sqrt (lamL * lamE)

/-
**Mutualism ⇒ super-additive efficiency.**  Positive stewardship coupling
lifts the joint learning efficiency strictly above the sum of subsystem
efficiencies.
-/
theorem melt_mutualism_superadditive
    (etaL etaE muLE lamL lamE : ℝ)
    (hlamL : 0 < lamL) (hlamE : 0 < lamE) (hμ : 0 < muLE) :
    etaL + etaE < etaJoint etaL etaE muLE lamL lamE := by
  exact lt_add_of_pos_right _ ( by exact div_pos ( mul_pos zero_lt_two hμ ) ( Real.sqrt_pos.mpr ( mul_pos hlamL hlamE ) ) )

/-
**Independence ⇒ additive efficiency.**  Zero coupling recovers the standard
non-coupled additive efficiency.
-/
theorem melt_independence_additive
    (etaL etaE lamL lamE : ℝ) (hlamL : 0 < lamL) (hlamE : 0 < lamE) :
    etaJoint etaL etaE 0 lamL lamE = etaL + etaE := by
  unfold etaJoint; ring;

/-
**Lindblad spectral-gap sub-additivity (parasitic regime).**  Negative
stewardship coupling drops the joint efficiency strictly below the sum of
subsystem efficiencies — AI training that extracts predictive information at the
cost of ecological coherence.
-/
theorem lindblad_spectral_gap_subadditivity
    (etaL etaE muLE lamL lamE : ℝ)
    (hlamL : 0 < lamL) (hlamE : 0 < lamE) (hμ : muLE < 0) :
    etaJoint etaL etaE muLE lamL lamE < etaL + etaE := by
  unfold etaJoint; nlinarith [ show 0 < Real.sqrt ( lamL * lamE ) by positivity, div_mul_cancel₀ ( 2 * muLE ) ( ne_of_gt ( Real.sqrt_pos.mpr ( mul_pos hlamL hlamE ) ) ) ] ;

end MELT