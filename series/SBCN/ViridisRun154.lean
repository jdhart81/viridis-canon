import Mathlib

noncomputable section

namespace Viridis.CognitiveModeling.SignedBiasCancellation

def pooledError (w e1 e2 : ℝ) : ℝ := w * e1 + (1 - w) * e2

theorem pooled_error_at_zero (e1 e2 : ℝ) : pooledError 0 e1 e2 = e2 := by
  simp [pooledError]

theorem pooled_error_at_one (e1 e2 : ℝ) : pooledError 1 e1 e2 = e1 := by
  simp [pooledError]

theorem cancellation_weight_balance (a b : ℝ) (h : a + b ≠ 0) :
    (b / (a + b)) * a = (1 - b / (a + b)) * b := by
  field_simp [h]
  ring

theorem opposite_error_cancellation (a b : ℝ) (h : a + b ≠ 0) :
    pooledError (b / (a + b)) (-a) b = 0 := by
  unfold pooledError
  field_simp [h]
  ring

theorem cancellation_weight_interior (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    0 < b / (a + b) ∧ b / (a + b) < 1 := by
  have hsum : 0 < a + b := add_pos ha hb
  constructor
  · exact div_pos hb hsum
  · exact (div_lt_one hsum).2 (by linarith)

theorem same_sign_nonnegative (w e1 e2 : ℝ)
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1) (he1 : 0 ≤ e1) (he2 : 0 ≤ e2) :
    0 ≤ pooledError w e1 e2 := by
  unfold pooledError
  exact add_nonneg (mul_nonneg hw0 he1)
    (mul_nonneg (sub_nonneg.mpr hw1) he2)

theorem same_sign_nonpositive (w e1 e2 : ℝ)
    (hw0 : 0 ≤ w) (hw1 : w ≤ 1) (he1 : e1 ≤ 0) (he2 : e2 ≤ 0) :
    pooledError w e1 e2 ≤ 0 := by
  unfold pooledError
  exact add_nonpos (mul_nonpos_of_nonneg_of_nonpos hw0 he1)
    (mul_nonpos_of_nonneg_of_nonpos (sub_nonneg.mpr hw1) he2)

theorem signed_bias_cancellation_witness :
    pooledError (3 / 5 : ℝ) (-2) 3 = 0 := by
  norm_num [pooledError]

end Viridis.CognitiveModeling.SignedBiasCancellation
