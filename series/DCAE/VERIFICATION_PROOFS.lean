/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# D-Score Component Alignment: proofs of the deposited statements

`VERIFICATION_STATEMENT.lean` in this folder states six claims with `sorry`. The deposited
`VERIFICATION_CANDIDATE.lean` does not compile at this project's pins (compile census, 2026-11-13:
`rw [dscore]` unfolds only one of the two scores, so `ring` is left with unsolved goals). This file proves
the same six statements, over the same definition, with no `sorry`. Both deposited files are left unchanged.

Each theorem here has the name of its statement in the namespace `Proved`. The `example`s at the end check
that every proved statement is the deposited one.

These are elementary facts about a weighted average of three components. They do not validate the D-Score
as a measure of ecological recovery.
-/
import VERIFICATION_STATEMENT

noncomputable section

namespace Viridis.DScore.ComponentAlignment.Proved

open Viridis.DScore.ComponentAlignment (dscore)

theorem dscore_difference_identity
    (wS wP wG s₁ p₁ g₁ s₀ p₀ g₀ : ℝ) :
    dscore wS wP wG s₁ p₁ g₁ - dscore wS wP wG s₀ p₀ g₀ =
      wS * (s₁ - s₀) + wP * (p₁ - p₀) + wG * (g₁ - g₀) := by
  simp only [dscore]
  ring

theorem aligned_component_envelope
    (wS wP wG ε s₁ p₁ g₁ s₀ p₀ g₀ : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hsum : wS + wP + wG = 1)
    (hs : |s₁ - s₀| ≤ ε) (hp : |p₁ - p₀| ≤ ε) (hg : |g₁ - g₀| ≤ ε) :
    |dscore wS wP wG s₁ p₁ g₁ - dscore wS wP wG s₀ p₀ g₀| ≤ ε := by
  have hslo' := mul_le_mul_of_nonneg_left (abs_le.mp hs).1 hwS
  have hshi' := mul_le_mul_of_nonneg_left (abs_le.mp hs).2 hwS
  have hplo' := mul_le_mul_of_nonneg_left (abs_le.mp hp).1 hwP
  have hphi' := mul_le_mul_of_nonneg_left (abs_le.mp hp).2 hwP
  have hglo' := mul_le_mul_of_nonneg_left (abs_le.mp hg).1 hwG
  have hghi' := mul_le_mul_of_nonneg_left (abs_le.mp hg).2 hwG
  have hbudget : wS * ε + wP * ε + wG * ε = ε := by
    calc
      wS * ε + wP * ε + wG * ε = (wS + wP + wG) * ε := by ring
      _ = ε := by rw [hsum]; ring
  rw [dscore_difference_identity, abs_le]
  constructor <;> linarith

theorem aligned_margin_preserves_threshold
    (wS wP wG ε τ s₁ p₁ g₁ s₀ p₀ g₀ : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hsum : wS + wP + wG = 1)
    (hs : |s₁ - s₀| ≤ ε) (hp : |p₁ - p₀| ≤ ε) (hg : |g₁ - g₀| ≤ ε)
    (hmargin : τ + ε ≤ dscore wS wP wG s₀ p₀ g₀) :
    τ ≤ dscore wS wP wG s₁ p₁ g₁ := by
  have henv := aligned_component_envelope wS wP wG ε s₁ p₁ g₁ s₀ p₀ g₀
    hwS hwP hwG hsum hs hp hg
  have hlo := (abs_le.mp henv).1
  linarith

theorem common_shift_exact
    (wS wP wG ε s p g : ℝ) (hsum : wS + wP + wG = 1) :
    dscore wS wP wG (s + ε) (p + ε) (g + ε) - dscore wS wP wG s p g = ε := by
  simp only [dscore]
  have h : wS * (s + ε) + wP * (p + ε) + wG * (g + ε) - (wS * s + wP * p + wG * g)
      = (wS + wP + wG) * ε := by ring
  rw [h, hsum, one_mul]

theorem zero_weight_component_inert
    (wS wP s p g g' : ℝ) :
    dscore wS wP 0 s p g = dscore wS wP 0 s p g' := by
  simp [dscore]

theorem envelope_sharp_witness :
    dscore (1/2 : ℝ) (1/3 : ℝ) (1/6 : ℝ) (3/10 : ℝ) (1/2 : ℝ) (7/10 : ℝ) -
      dscore (1/2 : ℝ) (1/3 : ℝ) (1/6 : ℝ) (1/5 : ℝ) (2/5 : ℝ) (3/5 : ℝ) = 1/10 := by
  norm_num [dscore]

end Viridis.DScore.ComponentAlignment.Proved

namespace Viridis.DScore.ComponentAlignment

example : type_of% @dscore_difference_identity := @Proved.dscore_difference_identity
example : type_of% @aligned_component_envelope := @Proved.aligned_component_envelope
example : type_of% @aligned_margin_preserves_threshold := @Proved.aligned_margin_preserves_threshold
example : type_of% @common_shift_exact := @Proved.common_shift_exact
example : type_of% @zero_weight_component_inert := @Proved.zero_weight_component_inert
example : type_of% @envelope_sharp_witness := @Proved.envelope_sharp_witness

end Viridis.DScore.ComponentAlignment
