import Mathlib

namespace Viridis.ThermodynamicEconomics.StewardshipReserve

theorem reserve_preserved
    (spendable reserve spend : Nat) (hspend : spend ≤ spendable) :
    spend + reserve ≤ spendable + reserve := by
  exact Nat.add_le_add_right hspend reserve

theorem zero_spendable_forces_zero
    (reserve spend : Nat) (hspend : spend ≤ 0) :
    spend = 0 := by
  exact Nat.le_zero.mp hspend

theorem reserve_monotone
    (spend reserve₁ reserve₂ : Nat) (hreserve : reserve₁ ≤ reserve₂) :
    spend + reserve₁ ≤ spend + reserve₂ := by
  exact Nat.add_le_add_left hreserve spend

theorem stewardship_reserve_witness :
    4 + 6 ≤ 7 + 6 := by
  norm_num

end Viridis.ThermodynamicEconomics.StewardshipReserve
