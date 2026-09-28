import Mathlib

namespace Viridis.HDFM.SharedCorridorFootprint

theorem shared_saving
    (a b s : Nat) (hsa : s ≤ a) (hsb : s ≤ b) :
    a + b - (a + b - s) = s := by
  sorry

theorem combined_le_gross
    (a b s : Nat) :
    a + b - s ≤ a + b := by
  sorry

theorem combined_covers_left
    (a b s : Nat) (hsb : s ≤ b) :
    a ≤ a + b - s := by
  sorry

theorem combined_covers_right
    (a b s : Nat) (hsa : s ≤ a) :
    b ≤ a + b - s := by
  sorry

theorem left_footprint_contained
    (a b : Nat) (hab : a ≤ b) :
    a + b - a = b := by
  sorry

theorem shared_corridor_witness :
    8 + 11 - 5 = 14 := by
  sorry

end Viridis.HDFM.SharedCorridorFootprint
