import Mathlib.Analysis.SpecialFunctions.Log.Basic

set_option autoImplicit false

namespace Viridis.Run123

noncomputable section

def binaryKL (q alpha : ℝ) : ℝ :=
  q * Real.log (q / alpha) +
    (1 - q) * Real.log ((1 - q) / (1 - alpha))

def partitionLedger (q alpha withinH withinC : ℝ) : ℝ :=
  binaryKL q alpha + q * withinH + (1 - q) * withinC

private theorem weighted_log_ratio_lower
    (x a : ℝ) (hx : 0 < x) (ha : 0 < a) :
    x - a ≤ x * Real.log (x / a) := by
  have h := Real.one_sub_inv_le_log_of_pos (div_pos hx ha)
  have hm := mul_le_mul_of_nonneg_left h (le_of_lt hx)
  convert hm using 1 <;> field_simp [ne_of_gt hx, ne_of_gt ha] <;> ring

private theorem binaryKL_nonneg
    (q alpha : ℝ)
    (hq0 : 0 < q) (hq1 : q < 1)
    (ha0 : 0 < alpha) (ha1 : alpha < 1) :
    0 ≤ binaryKL q alpha := by
  have hq := weighted_log_ratio_lower q alpha hq0 ha0
  have hc := weighted_log_ratio_lower (1 - q) (1 - alpha)
    (sub_pos.mpr hq1) (sub_pos.mpr ha1)
  unfold binaryKL
  linarith

theorem kl_chain_rule_habitable_partition
    (q alpha withinH withinC : ℝ) :
    partitionLedger q alpha withinH withinC =
      binaryKL q alpha + q * withinH + (1 - q) * withinC := by
  sorry

theorem kl_ge_binary_habitable_mass
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    binaryKL q alpha ≤ partitionLedger q alpha withinH withinC := by
  sorry

theorem binary_kl_monotone_above_reference
    (q tau alpha : ℝ)
    (ha0 : 0 < alpha) (ha1 : alpha < 1)
    (ht0 : 0 < tau) (ht1 : tau < 1)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hat : alpha ≤ tau) (htq : tau ≤ q) :
    binaryKL tau alpha ≤ binaryKL q alpha := by
  sorry

theorem habitable_threshold_free_energy_floor
    (W kBT q tau alpha : ℝ)
    (hk : 0 ≤ kBT)
    (ha0 : 0 < alpha) (ha1 : alpha < 1)
    (ht0 : 0 < tau) (ht1 : tau < 1)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hat : alpha ≤ tau) (htq : tau ≤ q)
    (hwork : kBT * binaryKL q alpha ≤ W) :
    kBT * binaryKL tau alpha ≤ W := by
  sorry

theorem equality_iff_reference_conditionals
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    partitionLedger q alpha withinH withinC = binaryKL q alpha ↔
      withinH = 0 ∧ withinC = 0 := by
  sorry

theorem reference_shaped_conditionals_witness :
    partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 0 0 =
      binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) := by
  sorry

theorem within_class_excess_witness :
    binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) <
      partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 2 0 := by
  sorry

end

end Viridis.Run123
