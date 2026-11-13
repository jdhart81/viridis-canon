/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# Symbiotic Agreement: proofs of the deposited statements

`VERIFICATION_STATEMENT.lean` in this folder states seven claims with `sorry`. The deposited
`VERIFICATION_CANDIDATE.lean` does not compile at this project's pins (compile census, 2026-11-13: a type
mismatch at line 35, and a `positivity` step that cannot see `0 < 1 - p`). This file proves the same seven
statements, over the same definitions, with no `sorry`. Both deposited files are left unchanged.

Each theorem here has the name of its statement in the namespace `Proved`. The `example`s at the end check
that every proved statement is the deposited one.

These are elementary identities about a two-agent agreement model with independent, equally reliable
agents. They do not show that real agents are independent.
-/
import VERIFICATION_STATEMENT

noncomputable section

namespace Viridis.AIWavefunctionCollapse.SymbioticAgreement.Proved

open Viridis.AIWavefunctionCollapse.SymbioticAgreement (agreementMass agreementConfidence)

theorem agreement_mass_positive
    (p : ℝ) (hp0 : 0 < p) (hp1 : p < 1) :
    0 < agreementMass p := by
  unfold agreementMass
  have h1 : 0 < p^2 := pow_pos hp0 2
  have h2 : 0 ≤ (1 - p)^2 := sq_nonneg _
  linarith

theorem agreement_gain_identity
    (p : ℝ) (hM : agreementMass p ≠ 0) :
    agreementConfidence p - p =
      p * (1 - p) * (2 * p - 1) / agreementMass p := by
  unfold agreementConfidence
  rw [eq_div_iff hM, sub_mul, div_mul_cancel₀ _ hM]
  unfold agreementMass
  ring

theorem competent_agreement_not_worse
    (p : ℝ) (hp0 : 0 < p) (hp : 1 / 2 ≤ p) (hp1 : p ≤ 1) :
    p ≤ agreementConfidence p := by
  have hMpos : 0 < agreementMass p := by
    unfold agreementMass
    have h1 : 0 < p^2 := pow_pos hp0 2
    have h2 : 0 ≤ (1 - p)^2 := sq_nonneg _
    linarith
  have hgain := agreement_gain_identity p (ne_of_gt hMpos)
  have hnum : 0 ≤ p * (1 - p) * (2 * p - 1) :=
    mul_nonneg (mul_nonneg hp0.le (by linarith)) (by linarith)
  have hfrac : 0 ≤ p * (1 - p) * (2 * p - 1) / agreementMass p :=
    div_nonneg hnum hMpos.le
  linarith

theorem competent_interior_strict_gain
    (p : ℝ) (hp : 1 / 2 < p) (hp1 : p < 1) :
    p < agreementConfidence p := by
  have hp0 : 0 < p := by linarith
  have hMpos := agreement_mass_positive p hp0 hp1
  have hgain := agreement_gain_identity p (ne_of_gt hMpos)
  have hnum : 0 < p * (1 - p) * (2 * p - 1) :=
    mul_pos (mul_pos hp0 (by linarith)) (by linarith)
  have hfrac : 0 < p * (1 - p) * (2 * p - 1) / agreementMass p :=
    div_pos hnum hMpos
  linarith

theorem disagreement_probability_identity (p : ℝ) :
    agreementMass p + 2 * p * (1 - p) = 1 := by
  unfold agreementMass
  ring

theorem copied_agent_no_gain (p : ℝ) : p = p := rfl

theorem agreement_witness_three_quarters :
    agreementMass (3 / 4 : ℝ) = 5 / 8 ∧
    agreementConfidence (3 / 4 : ℝ) = 9 / 10 ∧
    (3 / 4 : ℝ) < agreementConfidence (3 / 4 : ℝ) := by
  unfold agreementConfidence agreementMass
  norm_num

end Viridis.AIWavefunctionCollapse.SymbioticAgreement.Proved

namespace Viridis.AIWavefunctionCollapse.SymbioticAgreement

example : type_of% @agreement_mass_positive := @Proved.agreement_mass_positive
example : type_of% @agreement_gain_identity := @Proved.agreement_gain_identity
example : type_of% @competent_agreement_not_worse := @Proved.competent_agreement_not_worse
example : type_of% @competent_interior_strict_gain := @Proved.competent_interior_strict_gain
example : type_of% @disagreement_probability_identity := @Proved.disagreement_probability_identity
example : type_of% @copied_agent_no_gain := @Proved.copied_agent_no_gain
example : type_of% @agreement_witness_three_quarters := @Proved.agreement_witness_three_quarters

end Viridis.AIWavefunctionCollapse.SymbioticAgreement
