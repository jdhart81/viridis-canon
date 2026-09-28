import Mathlib

noncomputable section

namespace Viridis.EntropyLearning.ReciprocalDistillationAccounting

def baselineLoss (lossA lossB : ℝ) : ℝ := lossA + lossB

def reciprocityPenalty (klAB klBA : ℝ) : ℝ := klAB + klBA

def mutualObjective (lossA lossB klAB klBA weight : ℝ) : ℝ :=
  baselineLoss lossA lossB + weight * reciprocityPenalty klAB klBA

theorem reciprocity_penalty_nonnegative (klAB klBA : ℝ)
    (hAB : 0 ≤ klAB) (hBA : 0 ≤ klBA) :
    0 ≤ reciprocityPenalty klAB klBA := by
  unfold reciprocityPenalty
  linarith

theorem mutual_objective_ge_baseline (lossA lossB klAB klBA weight : ℝ)
    (hAB : 0 ≤ klAB) (hBA : 0 ≤ klBA) (hw : 0 ≤ weight) :
    baselineLoss lossA lossB ≤ mutualObjective lossA lossB klAB klBA weight := by
  have hp : 0 ≤ reciprocityPenalty klAB klBA :=
    reciprocity_penalty_nonnegative klAB klBA hAB hBA
  have hprod : 0 ≤ weight * reciprocityPenalty klAB klBA := mul_nonneg hw hp
  unfold mutualObjective
  linarith

theorem mutual_objective_zero_weight (lossA lossB klAB klBA : ℝ) :
    mutualObjective lossA lossB klAB klBA 0 = baselineLoss lossA lossB := by
  simp [mutualObjective]

theorem mutual_objective_monotone_weight (lossA lossB klAB klBA w1 w2 : ℝ)
    (hAB : 0 ≤ klAB) (hBA : 0 ≤ klBA) (hw : w1 ≤ w2) :
    mutualObjective lossA lossB klAB klBA w1 ≤
      mutualObjective lossA lossB klAB klBA w2 := by
  have hp : 0 ≤ reciprocityPenalty klAB klBA :=
    reciprocity_penalty_nonnegative klAB klBA hAB hBA
  have hmul := mul_le_mul_of_nonneg_right hw hp
  unfold mutualObjective
  linarith

theorem mutual_objective_eq_baseline_iff (lossA lossB klAB klBA weight : ℝ)
    (hAB : 0 ≤ klAB) (hBA : 0 ≤ klBA) (hw : 0 < weight) :
    mutualObjective lossA lossB klAB klBA weight = baselineLoss lossA lossB ↔
      reciprocityPenalty klAB klBA = 0 := by
  constructor
  · intro h
    have hp : 0 ≤ reciprocityPenalty klAB klBA :=
      reciprocity_penalty_nonnegative klAB klBA hAB hBA
    unfold mutualObjective at h
    nlinarith
  · intro h
    simp [mutualObjective, h]

theorem reciprocal_objective_positive_witness :
    mutualObjective (2 : ℝ) 3 (1 / 2) (1 / 4) (3 / 2) = 49 / 8 := by
  norm_num [mutualObjective, baselineLoss, reciprocityPenalty]

end Viridis.EntropyLearning.ReciprocalDistillationAccounting
