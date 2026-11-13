/-
Copyright (c) 2026 Justin Hart, Viridis LLC. Released under Apache 2.0.

# Checkpoint Balance: proofs of the deposited statements

`CheckpointBalance.lean` in this folder is the deposited statement file. It closes every theorem with
`sorry`. The compile census of 2026-11-13 recorded that as an open gap. This file proves the same six
statements, over the same definitions, with no `sorry`. The deposited file is left byte-for-byte unchanged.

Each theorem here has the name of its statement in the namespace `Proved`. The `example`s at the end check
that every proved statement is the deposited one.

These are elementary facts about a defined loss. They do not show that any system attains the balance.
-/
import CheckpointBalance

noncomputable section

namespace Viridis.Computation.Thermodynamic.Proved

open Viridis.Computation.Thermodynamic (checkpointLoss normalizedPenalty)

private lemma gap_identity (u : ℝ) (hu : 0 < u) : (u - 1)^2 / u = u + 1 / u - 2 := by
  field_simp
  ring

theorem normalized_penalty_floor (u : ℝ) (hu : 0 < u) :
    1 ≤ normalizedPenalty u := by
  have h : 0 ≤ (u - 1)^2 / u := div_nonneg (sq_nonneg _) hu.le
  have e := gap_identity u hu
  unfold normalizedPenalty
  linarith

theorem normalized_penalty_eq_one_iff (u : ℝ) (hu : 0 < u) :
    normalizedPenalty u = 1 ↔ u = 1 := by
  unfold normalizedPenalty
  constructor
  · intro h
    have hz : (u - 1)^2 / u = 0 := by
      rw [gap_identity u hu]
      linarith
    have hsq : (u - 1)^2 = 0 := by
      rcases div_eq_zero_iff.mp hz with h0 | h0
      · exact h0
      · exact absurd h0 hu.ne'
    have h1 : u - 1 = 0 := (pow_eq_zero_iff (by norm_num)).mp hsq
    linarith
  · rintro rfl
    norm_num

theorem reciprocal_mistuning_symmetry (u : ℝ) (hu : u ≠ 0) :
    normalizedPenalty (1 / u) = normalizedPenalty u := by
  unfold normalizedPenalty
  rw [one_div_one_div]
  ring

theorem checkpoint_balance_floor
    (q lambda r tau tauStar : ℝ)
    (hq : 0 < q) (hlambda : 0 < lambda) (hr : 0 < r)
    (htau : 0 < tau) (htauStar : 0 < tauStar)
    (hbalance : q / tauStar = lambda * r * tauStar / 2) :
    checkpointLoss q lambda r tauStar ≤ checkpointLoss q lambda r tau := by
  unfold checkpointLoss
  have hq' : q = lambda * r * tauStar / 2 * tauStar := (div_eq_iff htauStar.ne').mp hbalance
  have key : q / tau + lambda * r * tau / 2 - (q / tauStar + lambda * r * tauStar / 2)
      = lambda * r / 2 * ((tau - tauStar)^2 / tau) := by
    rw [hq']
    field_simp
    ring
  have hnn : 0 ≤ lambda * r / 2 * ((tau - tauStar)^2 / tau) := by positivity
  linarith

theorem landauer_checkpoint_component
    (q qMin tau : ℝ) (hq : qMin ≤ q) (htau : 0 < tau) :
    qMin / tau ≤ q / tau := by
  gcongr

theorem worked_nonvacuity :
    checkpointLoss 2 1 1 2 = 2 ∧
    checkpointLoss 2 1 1 2 < checkpointLoss 2 1 1 1 := by
  unfold checkpointLoss
  constructor <;> norm_num

end Viridis.Computation.Thermodynamic.Proved

namespace Viridis.Computation.Thermodynamic

example : type_of% @normalized_penalty_floor := @Proved.normalized_penalty_floor
example : type_of% @normalized_penalty_eq_one_iff := @Proved.normalized_penalty_eq_one_iff
example : type_of% @reciprocal_mistuning_symmetry := @Proved.reciprocal_mistuning_symmetry
example : type_of% @checkpoint_balance_floor := @Proved.checkpoint_balance_floor
example : type_of% @landauer_checkpoint_component := @Proved.landauer_checkpoint_component
example : type_of% @worked_nonvacuity := @Proved.worked_nonvacuity

end Viridis.Computation.Thermodynamic
