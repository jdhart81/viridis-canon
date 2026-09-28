import Mathlib

noncomputable section

namespace Viridis.DScore.ComponentAlignment

def dscore (wS wP wG s p g : ℝ) : ℝ := wS * s + wP * p + wG * g

theorem dscore_difference_identity
    (wS wP wG s₁ p₁ g₁ s₀ p₀ g₀ : ℝ) :
    dscore wS wP wG s₁ p₁ g₁ - dscore wS wP wG s₀ p₀ g₀ =
      wS * (s₁ - s₀) + wP * (p₁ - p₀) + wG * (g₁ - g₀) := by
  rw [dscore]
  ring

theorem aligned_component_envelope
    (wS wP wG ε s₁ p₁ g₁ s₀ p₀ g₀ : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hsum : wS + wP + wG = 1)
    (hs : |s₁ - s₀| ≤ ε) (hp : |p₁ - p₀| ≤ ε) (hg : |g₁ - g₀| ≤ ε) :
    |dscore wS wP wG s₁ p₁ g₁ - dscore wS wP wG s₀ p₀ g₀| ≤ ε := by
  have hslo := (abs_le.mp hs).1
  have hshi := (abs_le.mp hs).2
  have hplo := (abs_le.mp hp).1
  have hphi := (abs_le.mp hp).2
  have hglo := (abs_le.mp hg).1
  have hghi := (abs_le.mp hg).2
  have hslo' := mul_le_mul_of_nonneg_left hslo hwS
  have hshi' := mul_le_mul_of_nonneg_left hshi hwS
  have hplo' := mul_le_mul_of_nonneg_left hplo hwP
  have hphi' := mul_le_mul_of_nonneg_left hphi hwP
  have hglo' := mul_le_mul_of_nonneg_left hglo hwG
  have hghi' := mul_le_mul_of_nonneg_left hghi hwG
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
  rw [dscore]
  nlinarith [hsum]

theorem zero_weight_component_inert
    (wS wP s p g g' : ℝ) :
    dscore wS wP 0 s p g = dscore wS wP 0 s p g' := by
  simp [dscore]

theorem envelope_sharp_witness :
    dscore (1/2 : ℝ) (1/3 : ℝ) (1/6 : ℝ) (3/10 : ℝ) (1/2 : ℝ) (7/10 : ℝ) -
      dscore (1/2 : ℝ) (1/3 : ℝ) (1/6 : ℝ) (1/5 : ℝ) (2/5 : ℝ) (3/5 : ℝ) = 1/10 := by
  norm_num [dscore]

end Viridis.DScore.ComponentAlignment
