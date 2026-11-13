/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# Corridor Alignment: proofs of the deposited statements

`CorridorAlignment.lean` in this folder is the deposited statement file. It closes every theorem with
`sorry`. The compile census of 2026-11-13 recorded that as an open gap: the Lean in this repository did
not establish the results. This file proves the same six statements, over the same definitions, with no
`sorry`. The deposited file is left byte-for-byte unchanged.

Each theorem here has the name of its statement in the namespace `Proved`. The `example`s at the end check
that every proved statement is the deposited one (same type, up to definitional unfolding).

These are elementary facts about a defined ceiling. They do not show that any corridor attains it.
-/
import CorridorAlignment

noncomputable section

namespace Viridis.HDFMCorridors.Alignment.Proved

open Viridis.HDFMCorridors.Alignment (alignmentCeiling)

theorem minimum_le_average (a b : ℝ) :
    min a b ≤ (a + b) / 2 := by
  have h1 := min_le_left a b
  have h2 := min_le_right a b
  linarith

theorem two_direction_alignment_ceiling
    (a b c : ℝ) (hc : -1 ≤ c)
    (hquad : ((a + b) / 2)^2 ≤ (1 + c) / 2) :
    min a b ≤ alignmentCeiling c := by
  unfold alignmentCeiling
  exact (minimum_le_average a b).trans ((le_abs_self _).trans (Real.abs_le_sqrt hquad))

theorem bisector_scalar_attains_ceiling
    (c : ℝ) (hc : -1 ≤ c) :
    min (alignmentCeiling c) (alignmentCeiling c) = alignmentCeiling c :=
  min_self _

theorem antipodal_ceiling_zero :
    alignmentCeiling (-1) = 0 := by
  unfold alignmentCeiling
  norm_num

theorem two_segment_alignment_persists
    (l₁ l₂ m a₁ a₂ : ℝ)
    (hl₁ : 0 ≤ l₁) (hl₂ : 0 ≤ l₂)
    (ha₁ : m ≤ a₁) (ha₂ : m ≤ a₂) :
    m * (l₁ + l₂) ≤ l₁ * a₁ + l₂ * a₂ := by
  nlinarith [mul_le_mul_of_nonneg_left ha₁ hl₁, mul_le_mul_of_nonneg_left ha₂ hl₂]

theorem orthogonal_alignment_nonvacuous :
    0 < alignmentCeiling 0 ∧
    min (alignmentCeiling 0) (alignmentCeiling 0) = alignmentCeiling 0 := by
  refine ⟨?_, min_self _⟩
  unfold alignmentCeiling
  exact Real.sqrt_pos.mpr (by norm_num)

end Viridis.HDFMCorridors.Alignment.Proved

namespace Viridis.HDFMCorridors.Alignment

example : type_of% @minimum_le_average := @Proved.minimum_le_average
example : type_of% @two_direction_alignment_ceiling := @Proved.two_direction_alignment_ceiling
example : type_of% @bisector_scalar_attains_ceiling := @Proved.bisector_scalar_attains_ceiling
example : type_of% @antipodal_ceiling_zero := @Proved.antipodal_ceiling_zero
example : type_of% @two_segment_alignment_persists := @Proved.two_segment_alignment_persists
example : type_of% @orthogonal_alignment_nonvacuous := @Proved.orthogonal_alignment_nonvacuous

end Viridis.HDFMCorridors.Alignment
