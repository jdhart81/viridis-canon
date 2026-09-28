import Mathlib

noncomputable section

namespace Viridis.HDFM.ReciprocalCorridorBottleneck

def reciprocalService (x y : ℝ) : ℝ := min x y

def spend (c d x y : ℝ) : ℝ := c * x + d * y

theorem reciprocal_service_nonnegative (x y : ℝ)
    (hx : 0 ≤ x) (hy : 0 ≤ y) : 0 ≤ reciprocalService x y := by
  exact le_min hx hy

theorem reciprocal_service_le_left (x y : ℝ) : reciprocalService x y ≤ x := by
  simpa [reciprocalService] using min_le_left x y

theorem reciprocal_service_le_right (x y : ℝ) : reciprocalService x y ≤ y := by
  simpa [reciprocalService] using min_le_right x y

theorem reciprocal_budget_bound
    (c d x y B : ℝ)
    (hc : 0 ≤ c) (hd : 0 ≤ d)
    (hbudget : spend c d x y ≤ B) :
    (c + d) * reciprocalService x y ≤ B := by
  have hcx := mul_le_mul_of_nonneg_left (reciprocal_service_le_left x y) hc
  have hdy := mul_le_mul_of_nonneg_left (reciprocal_service_le_right x y) hd
  unfold spend at hbudget
  nlinarith

theorem left_deficit_decomposition
    (c d x y B : ℝ) (hxy : x ≤ y) :
    B - (c + d) * reciprocalService x y =
      (B - spend c d x y) + d * (y - x) := by
  rw [show reciprocalService x y = x by simp [reciprocalService, min_eq_left hxy]]
  unfold spend
  ring

theorem right_deficit_decomposition
    (c d x y B : ℝ) (hyx : y ≤ x) :
    B - (c + d) * reciprocalService x y =
      (B - spend c d x y) + c * (x - y) := by
  rw [show reciprocalService x y = y by simp [reciprocalService, min_eq_right hyx]]
  unfold spend
  ring

theorem balanced_iff_tight
    (c d x y : ℝ) (hc : 0 < c) (hd : 0 < d) :
    (c + d) * reciprocalService x y = spend c d x y ↔ x = y := by
  constructor
  · intro h
    by_cases hxy : x ≤ y
    · rw [show reciprocalService x y = x by simp [reciprocalService, min_eq_left hxy]] at h
      unfold spend at h
      nlinarith
    · have hyx : y ≤ x := le_of_not_ge hxy
      rw [show reciprocalService x y = y by simp [reciprocalService, min_eq_right hyx]] at h
      unfold spend at h
      nlinarith
  · intro h
    subst y
    simp [reciprocalService, spend, add_mul]

theorem balanced_positive_witness :
    reciprocalService (5 : ℝ) 5 = 5 ∧ spend 2 3 5 5 = 25 := by
  norm_num [reciprocalService, spend]

theorem imbalance_deficit_witness :
    reciprocalService (2 : ℝ) 5 = 2 ∧
      25 - (2 + 3) * reciprocalService (2 : ℝ) 5 = 15 := by
  norm_num [reciprocalService]

end Viridis.HDFM.ReciprocalCorridorBottleneck
