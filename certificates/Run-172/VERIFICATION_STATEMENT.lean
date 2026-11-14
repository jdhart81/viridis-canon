import Mathlib

namespace Viridis.ThermodynamicEconomics.StewardshipReserve

theorem reserve_preserved
    (spendable reserve spend : Nat) (hspend : spend ≤ spendable) :
    spend + reserve ≤ spendable + reserve := by
  sorry

theorem zero_spendable_forces_zero
    (reserve spend : Nat) (hspend : spend ≤ 0) :
    spend = 0 := by
  sorry

theorem reserve_monotone
    (spend reserve₁ reserve₂ : Nat) (hreserve : reserve₁ ≤ reserve₂) :
    spend + reserve₁ ≤ spend + reserve₂ := by
  sorry

theorem stewardship_reserve_witness :
    4 + 6 ≤ 7 + 6 := by
  sorry

end Viridis.ThermodynamicEconomics.StewardshipReserve
