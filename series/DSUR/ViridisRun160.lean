import Mathlib

noncomputable section

namespace Viridis.DScore.StewardshipUncertaintyReserve

def dscore (wS wP wG s p g : ℝ) : ℝ := wS * s + wP * p + wG * g

def reserve (wS wP wG rS rP rG : ℝ) : ℝ :=
  wS * rS + wP * rP + wG * rG

def lowerScore (wS wP wG s p g rS rP rG : ℝ) : ℝ :=
  dscore wS wP wG s p g - reserve wS wP wG rS rP rG

theorem score_difference_identity
    (wS wP wG s p g s₀ p₀ g₀ : ℝ) :
    dscore wS wP wG s p g - dscore wS wP wG s₀ p₀ g₀ =
      wS * (s - s₀) + wP * (p - p₀) + wG * (g - g₀) := by
  unfold dscore
  ring

theorem reserve_nonnegative
    (wS wP wG rS rP rG : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hrS : 0 ≤ rS) (hrP : 0 ≤ rP) (hrG : 0 ≤ rG) :
    0 ≤ reserve wS wP wG rS rP rG := by
  unfold reserve
  positivity

theorem componentwise_error_envelope
    (wS wP wG rS rP rG s p g s₀ p₀ g₀ : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hs : |s - s₀| ≤ rS) (hp : |p - p₀| ≤ rP)
    (hg : |g - g₀| ≤ rG) :
    |dscore wS wP wG s p g - dscore wS wP wG s₀ p₀ g₀| ≤
      reserve wS wP wG rS rP rG := by
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
  rw [score_difference_identity, abs_le]
  unfold reserve
  constructor <;> linarith

theorem stewardship_floor_sound
    (wS wP wG rS rP rG s p g s₀ p₀ g₀ τ : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hs : |s - s₀| ≤ rS) (hp : |p - p₀| ≤ rP)
    (hg : |g - g₀| ≤ rG)
    (hmargin : τ + reserve wS wP wG rS rP rG ≤
      dscore wS wP wG s₀ p₀ g₀) :
    τ ≤ dscore wS wP wG s p g := by
  have henv := componentwise_error_envelope wS wP wG rS rP rG
    s p g s₀ p₀ g₀ hwS hwP hwG hs hp hg
  have hlo := (abs_le.mp henv).1
  linarith

theorem lower_corner_exact
    (wS wP wG rS rP rG s p g : ℝ) :
    dscore wS wP wG (s - rS) (p - rP) (g - rG) =
      lowerScore wS wP wG s p g rS rP rG := by
  unfold lowerScore dscore reserve
  ring

theorem upper_corner_exact
    (wS wP wG rS rP rG s p g : ℝ) :
    dscore wS wP wG (s + rS) (p + rP) (g + rG) =
      dscore wS wP wG s p g + reserve wS wP wG rS rP rG := by
  unfold dscore reserve
  ring

theorem zero_uncertainty_recovers_nominal
    (wS wP wG s p g : ℝ) :
    lowerScore wS wP wG s p g 0 0 0 = dscore wS wP wG s p g := by
  simp [lowerScore, reserve]

theorem reserve_monotone
    (wS wP wG rS rP rG qS qP qG : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hS : rS ≤ qS) (hP : rP ≤ qP) (hG : rG ≤ qG) :
    reserve wS wP wG rS rP rG ≤ reserve wS wP wG qS qP qG := by
  unfold reserve
  have hS' := mul_le_mul_of_nonneg_left hS hwS
  have hP' := mul_le_mul_of_nonneg_left hP hwP
  have hG' := mul_le_mul_of_nonneg_left hG hwG
  linarith

theorem lower_score_positive_witness :
    lowerScore (1/2 : ℝ) (3/10 : ℝ) (1/5 : ℝ)
      (4/5 : ℝ) (7/10 : ℝ) (3/5 : ℝ)
      (1/10 : ℝ) (1/5 : ℝ) (1/20 : ℝ) = 61/100 := by
  norm_num [lowerScore, dscore, reserve]

theorem lower_corner_threshold_witness :
    (3/5 : ℝ) ≤ dscore (1/2 : ℝ) (3/10 : ℝ) (1/5 : ℝ)
      (7/10 : ℝ) (1/2 : ℝ) (11/20 : ℝ) := by
  norm_num [dscore]

end Viridis.DScore.StewardshipUncertaintyReserve

