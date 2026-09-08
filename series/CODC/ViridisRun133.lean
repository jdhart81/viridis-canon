import Mathlib

namespace Viridis.HDFM.CorridorOverlapDuality

/-- The path-product factorization supplied by finite independent edge sets. -/
def ProductFactorization (qA qB qUnion qShared : ℝ) : Prop :=
  qA * qB = qUnion * qShared

theorem synchrony_dividend_identity
    (qA qB qUnion qShared : ℝ)
    (hfactor : ProductFactorization qA qB qUnion qShared) :
    qUnion - qA * qB = qUnion * (1 - qShared) := by
  unfold ProductFactorization at hfactor
  rw [hfactor]
  ring

theorem availability_penalty_eq_synchrony_dividend
    (qA qB qUnion qShared : ℝ)
    (hfactor : ProductFactorization qA qB qUnion qShared) :
    (qA + qB - qA * qB) - (qA + qB - qUnion) =
      qUnion - qA * qB := by
  ring

theorem overlap_tradeoff_nonnegative
    (qA qB qUnion qShared : ℝ)
    (hfactor : ProductFactorization qA qB qUnion qShared)
    (hUnion : 0 ≤ qUnion) (hShared : qShared ≤ 1) :
    0 ≤ qUnion - qA * qB := by
  rw [synchrony_dividend_identity qA qB qUnion qShared hfactor]
  exact mul_nonneg hUnion (by linarith)

theorem overlap_tradeoff_strict
    (qA qB qUnion qShared : ℝ)
    (hfactor : ProductFactorization qA qB qUnion qShared)
    (hUnion : 0 < qUnion) (hShared : qShared < 1) :
    0 < qUnion - qA * qB := by
  rw [synchrony_dividend_identity qA qB qUnion qShared hfactor]
  exact mul_pos hUnion (by linarith)

theorem additive_shared_cost_saving
    (costA costB costUnion costShared : ℝ)
    (hcost : costA + costB = costUnion + costShared) :
    costA + costB - costUnion = costShared := by
  linarith

theorem corridor_overlap_nonvacuous :
    ProductFactorization (1 / 4 : ℝ) (1 / 4 : ℝ) (1 / 8 : ℝ) (1 / 2 : ℝ) ∧
      (0 : ℝ) < (1 / 8 : ℝ) - (1 / 4 : ℝ) * (1 / 4 : ℝ) := by
  constructor
  · unfold ProductFactorization
    norm_num
  · norm_num

end Viridis.HDFM.CorridorOverlapDuality
