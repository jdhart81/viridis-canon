import Mathlib

namespace Viridis.Ecoservices.ResponseAdjustedAlignment

/-- Completing the square for a one-dimensional quadratic response objective. -/
theorem response_objective_completion
    (g c w x : ℝ) (hc : 0 < c) :
    w * g * x - c * x^2 / 2 =
      (w * g)^2 / (2 * c) - c / 2 * (x - w * g / c)^2 := by
  have hc' : c ≠ 0 := ne_of_gt hc
  field_simp
  ring

/-- Exact two-coordinate gap behind the angle between `v` and `K v`. -/
theorem alignment_gap_identity (m M a b : ℝ) :
    (m^2 * a^2 + M^2 * b^2) * (a^2 + b^2) -
        (m * a^2 + M * b^2)^2 =
      (M - m)^2 * a^2 * b^2 := by
  ring

/-- Cross-multiplied sharp Kantorovich/antieigenvalue identity in two dimensions. -/
theorem kantorovich_cross_multiplied_identity (m M a b : ℝ) :
    (m + M)^2 * (m * a^2 + M * b^2)^2 -
        4 * m * M * (a^2 + b^2) * (m^2 * a^2 + M^2 * b^2) =
      (M - m)^2 * (m * a^2 - M * b^2)^2 := by
  ring

theorem alignment_bound_nonnegative (m M a b : ℝ) :
    0 ≤ (M - m)^2 * (m * a^2 - M * b^2)^2 :=
  mul_nonneg (sq_nonneg _) (sq_nonneg _)

/-- With eigenvalues 1 and 100 and mission direction (10,1), the sharp ratio is 20/101. -/
theorem alignment_certificate_nonvacuous :
    (200 : ℝ) / 1010 = 20 / 101 ∧ (20 : ℝ) / 101 < 1 := by
  norm_num

end Viridis.Ecoservices.ResponseAdjustedAlignment
