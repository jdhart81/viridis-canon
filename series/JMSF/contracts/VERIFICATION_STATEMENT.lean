import Mathlib

namespace Viridis.Ecoservices.JointMinimumFloor

theorem joint_floor_iff
    (a b x : Nat) :
    max a b ≤ x ↔ a ≤ x ∧ b ≤ x := by
  sorry

theorem joint_floor_dominates_left
    (a b : Nat) :
    a ≤ max a b := by
  sorry

theorem joint_floor_dominates_right
    (a b : Nat) :
    b ≤ max a b := by
  sorry

theorem agreed_floor_sufficient
    (a b x : Nat) (ha : a ≤ x) (hb : b ≤ x) :
    max a b ≤ x := by
  sorry

theorem joint_floor_witness :
    max 3 5 ≤ 7 := by
  sorry

end Viridis.Ecoservices.JointMinimumFloor
