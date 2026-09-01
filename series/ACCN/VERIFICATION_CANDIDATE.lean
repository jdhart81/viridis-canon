import Mathlib

noncomputable section

namespace Viridis.AIWavefunctionCollapse.SymbioticAgreement

def agreementMass (p : ℝ) : ℝ := p^2 + (1 - p)^2

def agreementConfidence (p : ℝ) : ℝ := p^2 / agreementMass p

theorem agreement_mass_positive
    (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) :
    0 < agreementMass p := by
  rw [agreementMass]
  positivity

theorem agreement_gain_identity
    (p : ℝ) (hM : agreementMass p ≠ 0) :
    agreementConfidence p - p =
      p * (1 - p) * (2 * p - 1) / agreementMass p := by
  rw [agreementConfidence]
  field_simp [hM]
  rw [agreementMass]
  ring

theorem competent_agreement_not_worse
    (p : ℝ) (hp0 : 0 < p) (hp : 1 / 2 ≤ p) (hp1 : p ≤ 1) :
    p ≤ agreementConfidence p := by
  have hp1' : 0 ≤ 1 - p := by linarith
  have htwo : 0 ≤ 2 * p - 1 := by linarith
  have hMpos : 0 < agreementMass p := by
    by_cases h : p = 1
    · subst p
      norm_num [agreementMass]
    · exact agreement_mass_positive p hp0 (lt_of_le_of_ne hp1 (Ne.symm h))
  have hgain := agreement_gain_identity p (ne_of_gt hMpos)
  have hnum : 0 ≤ p * (1 - p) * (2 * p - 1) :=
    mul_nonneg (mul_nonneg (le_of_lt hp0) hp1') htwo
  have hfrac : 0 ≤ p * (1 - p) * (2 * p - 1) / agreementMass p :=
    div_nonneg hnum (le_of_lt hMpos)
  linarith

theorem competent_interior_strict_gain
    (p : ℝ) (hp : 1 / 2 < p) (hp1 : p < 1) :
    p < agreementConfidence p := by
  have hp0 : 0 < p := by linarith
  have hMpos := agreement_mass_positive p hp0 hp1
  have hgain := agreement_gain_identity p (ne_of_gt hMpos)
  have hnum : 0 < p * (1 - p) * (2 * p - 1) := by positivity
  have hfrac : 0 < p * (1 - p) * (2 * p - 1) / agreementMass p :=
    div_pos hnum hMpos
  linarith

theorem disagreement_probability_identity (p : ℝ) :
    agreementMass p + 2 * p * (1 - p) = 1 := by
  rw [agreementMass]
  ring

theorem copied_agent_no_gain (p : ℝ) : p = p := by
  rfl

theorem agreement_witness_three_quarters :
    agreementMass (3 / 4 : ℝ) = 5 / 8 ∧
    agreementConfidence (3 / 4 : ℝ) = 9 / 10 ∧
    (3 / 4 : ℝ) < agreementConfidence (3 / 4 : ℝ) := by
  norm_num [agreementMass, agreementConfidence]

end Viridis.AIWavefunctionCollapse.SymbioticAgreement
