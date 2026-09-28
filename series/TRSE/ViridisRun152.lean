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
  unfold routeOne routeTwo balanceAllocation
  field_simp
  ring

theorem allocation_gap_identity (a b p q B x : ℝ) (hpq : p + q ≠ 0) :
    routeOne a p x - routeTwo b q B x =
      (p + q) * (x - balanceAllocation a b p q B) := by
  unfold routeOne routeTwo balanceAllocation
  field_simp
  ring

theorem left_bottleneck (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : x ≤ balanceAllocation a b p q B) :
    bottleneck a b p q B x = routeOne a p x := by
  apply min_eq_left
  have hpq : p + q ≠ 0 := ne_of_gt (add_pos hp hq)
  have hgap := allocation_gap_identity a b p q B x hpq
  have hprod : (p + q) * (x - balanceAllocation a b p q B) ≤ 0 :=
    mul_nonpos_of_nonneg_of_nonpos (le_of_lt (add_pos hp hq)) (sub_nonpos.mpr hx)
  linarith

theorem right_bottleneck (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : balanceAllocation a b p q B ≤ x) :
    bottleneck a b p q B x = routeTwo b q B x := by
  apply min_eq_right
  have hpq : p + q ≠ 0 := ne_of_gt (add_pos hp hq)
  have hgap := allocation_gap_identity a b p q B x hpq
  have hprod : 0 ≤ (p + q) * (x - balanceAllocation a b p q B) :=
    mul_nonneg (le_of_lt (add_pos hp hq)) (sub_nonneg.mpr hx)
  linarith

theorem balanced_bottleneck_maximal (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q) :
    bottleneck a b p q B x ≤
      bottleneck a b p q B (balanceAllocation a b p q B) := by
  let xs := balanceAllocation a b p q B
  have hpq : p + q ≠ 0 := ne_of_gt (add_pos hp hq)
  have hbal := balance_identity a b p q B hpq
  by_cases hx : x ≤ xs
  · rw [left_bottleneck a b p q B x hp hq hx]
    rw [left_bottleneck a b p q B xs hp hq (le_refl xs)]
    unfold routeOne
    dsimp [xs]
    nlinarith
  · have hxsx : xs ≤ x := le_of_lt (lt_of_not_ge hx)
    rw [right_bottleneck a b p q B x hp hq hxsx]
    rw [right_bottleneck a b p q B xs hp hq (le_refl xs)]
    unfold routeTwo
    dsimp [xs]
    nlinarith

theorem bottleneck_deficit_left (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : x ≤ balanceAllocation a b p q B) :
    bottleneck a b p q B (balanceAllocation a b p q B) -
      bottleneck a b p q B x = p * (balanceAllocation a b p q B - x) := by
  rw [left_bottleneck a b p q B x hp hq hx]
  rw [left_bottleneck a b p q B (balanceAllocation a b p q B) hp hq le_rfl]
  unfold routeOne
  ring

theorem bottleneck_deficit_right (a b p q B x : ℝ) (hp : 0 < p) (hq : 0 < q)
    (hx : balanceAllocation a b p q B ≤ x) :
    bottleneck a b p q B (balanceAllocation a b p q B) -
      bottleneck a b p q B x = q * (x - balanceAllocation a b p q B) := by
  rw [right_bottleneck a b p q B x hp hq hx]
  rw [right_bottleneck a b p q B (balanceAllocation a b p q B) hp hq le_rfl]
  unfold routeTwo
  ring

theorem nonmidpoint_balance_witness :
    balanceAllocation 1 4 2 1 4 = (7 / 3 : ℝ) ∧
    bottleneck 1 4 2 1 4 (7 / 3) = (17 / 3 : ℝ) ∧
    bottleneck 1 4 2 1 4 2 = 5 := by
  norm_num [balanceAllocation, bottleneck, routeOne, routeTwo, min_def]

end Viridis.HDFM.TwoRouteStewardship
