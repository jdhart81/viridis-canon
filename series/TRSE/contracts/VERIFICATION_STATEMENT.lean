import Mathlib

noncomputable section

namespace Viridis.HDFM.TwoRouteStewardship

def routeOne (a p x : ℝ) : ℝ := a + p * x
def routeTwo (b q B x : ℝ) : ℝ := b + q * (B - x)
def balanceAllocation (a b p q B : ℝ) : ℝ := (b + q * B - a) / (p + q)
def bottleneck (a b p q B x : ℝ) : ℝ := min (routeOne a p x) (routeTwo b q B x)

theorem balance_identity (a b p q B : ℝ) (hpq : p + q ≠ 0) :
    routeOne a p (balanceAllocation a b p q B) =
      routeTwo b q B (balanceAllocation a b p q B) := by
  sorry

theorem allocation_gap_identity (a b p q B x : ℝ) (hpq : p + q ≠ 0) :
    routeOne a p x - routeTwo b q B x =
      (p + q) * (x - balanceAllocation a b p q B) := by
  sorry

theorem left_bottleneck (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : x ≤ balanceAllocation a b p q B) :
    bottleneck a b p q B x = routeOne a p x := by
  sorry

theorem right_bottleneck (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : balanceAllocation a b p q B ≤ x) :
    bottleneck a b p q B x = routeTwo b q B x := by
  sorry

theorem balanced_bottleneck_maximal (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q) :
    bottleneck a b p q B x ≤
      bottleneck a b p q B (balanceAllocation a b p q B) := by
  sorry

theorem bottleneck_deficit_left (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : x ≤ balanceAllocation a b p q B) :
    bottleneck a b p q B (balanceAllocation a b p q B) -
      bottleneck a b p q B x = p * (balanceAllocation a b p q B - x) := by
  sorry

theorem bottleneck_deficit_right (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : balanceAllocation a b p q B ≤ x) :
    bottleneck a b p q B (balanceAllocation a b p q B) -
      bottleneck a b p q B x = q * (x - balanceAllocation a b p q B) := by
  sorry

theorem nonmidpoint_balance_witness :
    balanceAllocation 1 4 2 1 4 = (7 / 3 : ℝ) ∧
    bottleneck 1 4 2 1 4 (7 / 3) = (17 / 3 : ℝ) ∧
    bottleneck 1 4 2 1 4 2 = 5 := by
  sorry

end Viridis.HDFM.TwoRouteStewardship
