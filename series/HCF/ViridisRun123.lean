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
  rfl

theorem kl_ge_binary_habitable_mass
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    binaryKL q alpha ≤ partitionLedger q alpha withinH withinC := by
  unfold partitionLedger
  nlinarith [mul_nonneg hq0 hH, mul_nonneg (sub_nonneg.mpr hq1) hC]

theorem binary_kl_monotone_above_reference
    (q tau alpha : ℝ)
    (ha0 : 0 < alpha) (ha1 : alpha < 1)
    (ht0 : 0 < tau) (ht1 : tau < 1)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hat : alpha ≤ tau) (htq : tau ≤ q) :
    binaryKL tau alpha ≤ binaryKL q alpha := by
  have hratio : (1 - tau) / (1 - alpha) ≤ tau / alpha := by
    rw [div_le_div_iff₀ (sub_pos.mpr ha1) ha0]
    nlinarith
  have hlog :
      Real.log ((1 - tau) / (1 - alpha)) ≤ Real.log (tau / alpha) :=
    Real.log_le_log (div_pos (sub_pos.mpr ht1) (sub_pos.mpr ha1)) hratio
  have hkl : 0 ≤ binaryKL q tau :=
    binaryKL_nonneg q tau hq0 hq1 ht0 ht1
  have hidentity :
      binaryKL q alpha =
        binaryKL tau alpha + binaryKL q tau +
          (q - tau) *
            (Real.log (tau / alpha) -
              Real.log ((1 - tau) / (1 - alpha))) := by
    have hqa := Real.log_div hq0.ne' ha0.ne'
    have hqca := Real.log_div (by linarith : 1 - q ≠ 0)
      (by linarith : 1 - alpha ≠ 0)
    have hta := Real.log_div ht0.ne' ha0.ne'
    have htca := Real.log_div (by linarith : 1 - tau ≠ 0)
      (by linarith : 1 - alpha ≠ 0)
    have hqt := Real.log_div hq0.ne' ht0.ne'
    have hqct := Real.log_div (by linarith : 1 - q ≠ 0)
      (by linarith : 1 - tau ≠ 0)
    unfold binaryKL
    rw [hqa, hqca, hta, htca, hqt, hqct]
    ring
  rw [hidentity]
  have hsum :
      0 ≤ binaryKL q tau +
        (q - tau) *
          (Real.log (tau / alpha) - Real.log ((1 - tau) / (1 - alpha))) :=
    add_nonneg hkl (mul_nonneg (sub_nonneg.mpr htq) (sub_nonneg.mpr hlog))
  linarith

theorem habitable_threshold_free_energy_floor
    (W kBT q tau alpha : ℝ)
    (hk : 0 ≤ kBT)
    (ha0 : 0 < alpha) (ha1 : alpha < 1)
    (ht0 : 0 < tau) (ht1 : tau < 1)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hat : alpha ≤ tau) (htq : tau ≤ q)
    (hwork : kBT * binaryKL q alpha ≤ W) :
    kBT * binaryKL tau alpha ≤ W := by
  have hmono := binary_kl_monotone_above_reference q tau alpha
    ha0 ha1 ht0 ht1 hq0 hq1 hat htq
  exact (mul_le_mul_of_nonneg_left hmono hk).trans hwork

theorem equality_iff_reference_conditionals
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    partitionLedger q alpha withinH withinC = binaryKL q alpha ↔
      withinH = 0 ∧ withinC = 0 := by
  unfold partitionLedger
  constructor
  · intro h
    have hqH : 0 ≤ q * withinH := mul_nonneg (le_of_lt hq0) hH
    have hqC : 0 ≤ (1 - q) * withinC :=
      mul_nonneg (sub_nonneg.mpr (le_of_lt hq1)) hC
    have hz : q * withinH + (1 - q) * withinC = 0 := by linarith
    have h1 : q * withinH = 0 := by nlinarith
    have h2 : (1 - q) * withinC = 0 := by nlinarith
    constructor
    · exact (mul_eq_zero.mp h1).resolve_left (ne_of_gt hq0)
    · exact (mul_eq_zero.mp h2).resolve_left (by linarith)
  · rintro ⟨rfl, rfl⟩
    ring

theorem reference_shaped_conditionals_witness :
    partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 0 0 =
      binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) := by
  unfold partitionLedger
  ring

theorem within_class_excess_witness :
    binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) <
      partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 2 0 := by
  unfold partitionLedger
  norm_num

end

end Viridis.Run123
