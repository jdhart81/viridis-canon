import Mathlib

noncomputable section

namespace Viridis.IntelligenceCapacity.SequentialAlignmentRetention

def retained (C a b : ℝ) : ℝ := C * a * b
def firstLoss (C a : ℝ) : ℝ := C * (1 - a)
def secondLoss (C a b : ℝ) : ℝ := C * a * (1 - b)

theorem retained_nonnegative (C a b : ℝ)
    (hC : 0 ≤ C) (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ retained C a b := by
  unfold retained
  positivity

theorem retained_le_after_first (C a b : ℝ)
    (hC : 0 ≤ C) (ha : 0 ≤ a) (hb1 : b ≤ 1) : retained C a b ≤ C * a := by
  have hCa : 0 ≤ C * a := mul_nonneg hC ha
  have hgap : 0 ≤ (C * a) * (1 - b) := mul_nonneg hCa (sub_nonneg.mpr hb1)
  unfold retained
  nlinarith

theorem retained_le_capacity (C a b : ℝ)
    (hC : 0 ≤ C) (ha : 0 ≤ a) (ha1 : a ≤ 1)
    (hb : 0 ≤ b) (hb1 : b ≤ 1) : retained C a b ≤ C := by
  have hfirst : retained C a b ≤ C * a := retained_le_after_first C a b hC ha hb1
  have hgap : 0 ≤ C * (1 - a) := mul_nonneg hC (sub_nonneg.mpr ha1)
  nlinarith

theorem serial_loss_decomposition (C a b : ℝ) :
    C - retained C a b = firstLoss C a + secondLoss C a b := by
  unfold retained firstLoss secondLoss
  ring

theorem stage_order_invariant (C a b : ℝ) : retained C a b = retained C b a := by
  unfold retained
  ring

theorem attribution_sum_invariant (C a b : ℝ) :
    firstLoss C a + secondLoss C a b = firstLoss C b + secondLoss C b a := by
  unfold firstLoss secondLoss
  ring

theorem full_retention_witness : retained (12 : ℝ) 1 1 = 12 := by
  norm_num [retained]

theorem partial_retention_witness :
    retained (12 : ℝ) (3 / 4) (2 / 3) = 6 ∧
    firstLoss (12 : ℝ) (3 / 4) = 3 ∧
    secondLoss (12 : ℝ) (3 / 4) (2 / 3) = 3 := by
  norm_num [retained, firstLoss, secondLoss]

end Viridis.IntelligenceCapacity.SequentialAlignmentRetention
