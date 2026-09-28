import Mathlib

noncomputable section

namespace Viridis.EntropyLearning.RelativeEntropyChangeBudget

def totalChange (d1 d2 : ℝ) : ℝ := d1 + d2
def stewardshipLoad (d1 d2 r1 r2 : ℝ) : ℝ := r1 * d1 + r2 * d2
def modeledSlack (d1 d2 r1 r2 : ℝ) : ℝ :=
  (1 - r1) * d1 + (1 - r2) * d2

theorem load_nonnegative (d1 d2 r1 r2 : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2) (hr1 : 0 ≤ r1) (hr2 : 0 ≤ r2) :
    0 ≤ stewardshipLoad d1 d2 r1 r2 := by
  unfold stewardshipLoad
  positivity

theorem modeled_slack_nonnegative (d1 d2 r1 r2 : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2) (hr1 : r1 ≤ 1) (hr2 : r2 ≤ 1) :
    0 ≤ modeledSlack d1 d2 r1 r2 := by
  unfold modeledSlack
  exact add_nonneg (mul_nonneg (sub_nonneg.mpr hr1) hd1)
    (mul_nonneg (sub_nonneg.mpr hr2) hd2)

theorem change_partition (d1 d2 r1 r2 : ℝ) :
    stewardshipLoad d1 d2 r1 r2 + modeledSlack d1 d2 r1 r2 = totalChange d1 d2 := by
  unfold stewardshipLoad modeledSlack totalChange
  ring

theorem load_le_total (d1 d2 r1 r2 : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2) (hr1 : r1 ≤ 1) (hr2 : r2 ≤ 1) :
    stewardshipLoad d1 d2 r1 r2 ≤ totalChange d1 d2 := by
  have hs := modeled_slack_nonnegative d1 d2 r1 r2 hd1 hd2 hr1 hr2
  have hp := change_partition d1 d2 r1 r2
  linarith

theorem slack_le_total (d1 d2 r1 r2 : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2) (hr1 : 0 ≤ r1) (hr2 : 0 ≤ r2) :
    modeledSlack d1 d2 r1 r2 ≤ totalChange d1 d2 := by
  have hl := load_nonnegative d1 d2 r1 r2 hd1 hd2 hr1 hr2
  have hp := change_partition d1 d2 r1 r2
  linarith

theorem uniform_weight_bound (d1 d2 r1 r2 rmax : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2)
    (hr1 : r1 ≤ rmax) (hr2 : r2 ≤ rmax) :
    stewardshipLoad d1 d2 r1 r2 ≤ rmax * totalChange d1 d2 := by
  have hgap1 : 0 ≤ (rmax - r1) * d1 := mul_nonneg (sub_nonneg.mpr hr1) hd1
  have hgap2 : 0 ≤ (rmax - r2) * d2 := mul_nonneg (sub_nonneg.mpr hr2) hd2
  unfold stewardshipLoad totalChange
  nlinarith

theorem budgeted_load_bound (d1 d2 r1 r2 rmax budget : ℝ)
    (hd1 : 0 ≤ d1) (hd2 : 0 ≤ d2)
    (hr1 : r1 ≤ rmax) (hr2 : r2 ≤ rmax) (hmax : 0 ≤ rmax)
    (hbudget : totalChange d1 d2 ≤ budget) :
    stewardshipLoad d1 d2 r1 r2 ≤ rmax * budget := by
  have hl := uniform_weight_bound d1 d2 r1 r2 rmax hd1 hd2 hr1 hr2
  have hm := mul_le_mul_of_nonneg_left hbudget hmax
  exact le_trans hl hm

theorem balanced_change_witness :
    stewardshipLoad (3 : ℝ) 5 (1 / 3) (3 / 5) = 4 ∧
    modeledSlack (3 : ℝ) 5 (1 / 3) (3 / 5) = 4 ∧
    totalChange (3 : ℝ) 5 = 8 := by
  norm_num [stewardshipLoad, modeledSlack, totalChange]

theorem budget_witness :
    stewardshipLoad (3 : ℝ) 5 (1 / 3) (3 / 5) ≤ (3 / 5 : ℝ) * 8 := by
  norm_num [stewardshipLoad]

end Viridis.EntropyLearning.RelativeEntropyChangeBudget
