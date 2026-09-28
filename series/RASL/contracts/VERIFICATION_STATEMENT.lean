import Mathlib

namespace Viridis.SpeedLimits.ReservedActivity

theorem reserved_activity_bound
    (progress ticks usable reserve : Nat)
    (hprogress : progress ≤ ticks * usable) :
    progress + ticks * reserve ≤ ticks * (usable + reserve) := by
  sorry

theorem zero_usable_forces_zero
    (progress ticks : Nat)
    (hprogress : progress ≤ ticks * 0) :
    progress = 0 := by
  sorry

theorem reserve_monotone
    (progress ticks reserve₁ reserve₂ : Nat)
    (hreserve : reserve₁ ≤ reserve₂) :
    progress + ticks * reserve₁ ≤ progress + ticks * reserve₂ := by
  sorry

theorem reserved_activity_witness :
    3 + 4 * 2 ≤ 4 * (1 + 2) := by
  sorry

end Viridis.SpeedLimits.ReservedActivity
