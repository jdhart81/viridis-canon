/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# Stewardship Bottleneck Reserve: proofs of the deposited statements

`StewardshipBottleneckReserve.lean` in this folder is the deposited statement file. It closes every theorem
with `sorry`. The compile census of 2026-11-13 recorded that as an open gap. This file proves the same six
statements, over the same definitions, with no `sorry`. The deposited file is left byte-for-byte unchanged.

Each theorem here has the name of its statement in the namespace `Proved`. The `example`s at the end check
that every proved statement is the deposited one.

These are elementary facts about a three-stage minimum. They do not show that any real system has three
stages or meets the reserve.
-/
import StewardshipBottleneckReserve

namespace Viridis.IntelligenceCapacity.StewardshipBottleneckReserve.Proved

open Viridis.IntelligenceCapacity.StewardshipBottleneckReserve (residualCapacity optimumBound)

theorem stewardedCapacity_le_baseBottleneck
    (c r : Fin 3 -> Real)
    (hr : forall i, 0 <= r i) :
    residualCapacity c r <= min (c 0) (min (c 1) (c 2)) := by
  unfold residualCapacity
  have h0 := hr 0
  have h1 := hr 1
  have h2 := hr 2
  refine le_min ?_ (le_min ?_ ?_)
  · exact (min_le_left _ _).trans (by linarith)
  · exact ((min_le_right _ _).trans (min_le_left _ _)).trans (by linarith)
  · exact ((min_le_right _ _).trans (min_le_right _ _)).trans (by linarith)

theorem stewardedCapacity_le_averageRemainder
    (c r : Fin 3 -> Real) (B : Real)
    (hB : r 0 + r 1 + r 2 = B) :
    residualCapacity c r <= (c 0 + c 1 + c 2 - B) / 3 := by
  unfold residualCapacity
  have a0 : min (c 0 - r 0) (min (c 1 - r 1) (c 2 - r 2)) ≤ c 0 - r 0 := min_le_left _ _
  have a1 : min (c 0 - r 0) (min (c 1 - r 1) (c 2 - r 2)) ≤ c 1 - r 1 :=
    (min_le_right _ _).trans (min_le_left _ _)
  have a2 : min (c 0 - r 0) (min (c 1 - r 1) (c 2 - r 2)) ≤ c 2 - r 2 :=
    (min_le_right _ _).trans (min_le_right _ _)
  linarith

theorem stewardship_upper_bound
    (c r : Fin 3 -> Real) (B : Real)
    (hr : forall i, 0 <= r i)
    (hB : r 0 + r 1 + r 2 = B) :
    residualCapacity c r <= optimumBound c B := by
  unfold optimumBound
  exact le_min (stewardedCapacity_le_baseBottleneck c r hr) (stewardedCapacity_le_averageRemainder c r B hB)

private lemma c0 : (![2, 5, 8] : Fin 3 -> Real) 0 = 2 := rfl
private lemma c1 : (![2, 5, 8] : Fin 3 -> Real) 1 = 5 := rfl
private lemma c2 : (![2, 5, 8] : Fin 3 -> Real) 2 = 8 := rfl
private lemma s0 : (![0, 1, 5] : Fin 3 -> Real) 0 = 0 := rfl
private lemma s1 : (![0, 1, 5] : Fin 3 -> Real) 1 = 1 := rfl
private lemma s2 : (![0, 1, 5] : Fin 3 -> Real) 2 = 5 := rfl
private lemma e0 : (![1, 4, 7] : Fin 3 -> Real) 0 = 1 := rfl
private lemma e1 : (![1, 4, 7] : Fin 3 -> Real) 1 = 4 := rfl
private lemma e2 : (![1, 4, 7] : Fin 3 -> Real) 2 = 7 := rfl

theorem slack_regime_witness :
    residualCapacity (![2, 5, 8] : Fin 3 -> Real) (![0, 1, 5] : Fin 3 -> Real) = 2 := by
  unfold residualCapacity
  rw [c0, c1, c2, s0, s1, s2]
  norm_num [min_def]

theorem equalization_regime_witness :
    residualCapacity (![2, 5, 8] : Fin 3 -> Real) (![1, 4, 7] : Fin 3 -> Real) = 1 := by
  unfold residualCapacity
  rw [c0, c1, c2, e0, e1, e2]
  norm_num [min_def]

theorem worked_nonvacuity :
    optimumBound (![2, 5, 8] : Fin 3 -> Real) 12 = 1 := by
  unfold optimumBound
  rw [c0, c1, c2]
  norm_num [min_def]

end Viridis.IntelligenceCapacity.StewardshipBottleneckReserve.Proved

namespace Viridis.IntelligenceCapacity.StewardshipBottleneckReserve

example : type_of% @stewardedCapacity_le_baseBottleneck := @Proved.stewardedCapacity_le_baseBottleneck
example : type_of% @stewardedCapacity_le_averageRemainder := @Proved.stewardedCapacity_le_averageRemainder
example : type_of% @stewardship_upper_bound := @Proved.stewardship_upper_bound
example : type_of% @slack_regime_witness := @Proved.slack_regime_witness
example : type_of% @equalization_regime_witness := @Proved.equalization_regime_witness
example : type_of% @worked_nonvacuity := @Proved.worked_nonvacuity

end Viridis.IntelligenceCapacity.StewardshipBottleneckReserve
