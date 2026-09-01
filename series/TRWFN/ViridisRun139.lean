import Mathlib

namespace Viridis.ThermodynamicEconomics.RetrofitWaterFilling

/- Frozen algebraic targets for Run 139. These do not validate input prices,
measurements, policy authority, empirical impact, novelty, or product value. -/

/- Codex authored and froze this zero-sorry candidate after reviewing the
original contract and preserved historical provider artifact. That artifact is
diagnostic input only; only the aligned private Comparator receipt and issued
certificate establish verification. -/

noncomputable def clippedAllocation (b c q lambda : Real) : Real :=
  min 1 (max 0 ((b - lambda * c) / q))

theorem clippedAllocation_nonnegative (b c q lambda : Real) :
    0 <= clippedAllocation b c q lambda := by
  unfold clippedAllocation
  exact le_min zero_le_one (le_max_left 0 _)

theorem clippedAllocation_le_one (b c q lambda : Real) :
    clippedAllocation b c q lambda <= 1 := by
  exact min_le_left 1 _

theorem interior_stationarity
    (b c q lambda x : Real) (hq : q != 0)
    (hx : x = (b - lambda * c) / q) :
    b - q * x - lambda * c = 0 := by
  have hq' : q ≠ 0 := by simpa using hq
  subst hx
  field_simp
  ring

theorem coordinate_improvement_identity
    (b q x y : Real) :
    (b * x - q / 2 * x ^ 2) - (b * y - q / 2 * y ^ 2) =
      (x - y) * (b - q / 2 * (x + y)) := by
  ring

theorem embodied_burden_lowers_benefit
    (gross s1 s2 : Real) (h : s1 <= s2) :
    gross - s2 <= gross - s1 := by
  linarith

theorem retrofit_allocation_nonvacuous :
    clippedAllocation 2 1 2 1 = (1 : Real) / 2 /\
    clippedAllocation 2 1 2 1 = (1 : Real) / 2 := by
  constructor <;>
  · unfold clippedAllocation
    norm_num

end Viridis.ThermodynamicEconomics.RetrofitWaterFilling
