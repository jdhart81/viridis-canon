import Mathlib.Analysis.SpecialFunctions.Log.Basic

set_option autoImplicit false

namespace Viridis.Run123

noncomputable section

/-- Bernoulli relative entropy from the paper, on the interior of the unit interval. -/
def binaryKL (q alpha : ℝ) : ℝ :=
  q * Real.log (q / alpha) +
    (1 - q) * Real.log ((1 - q) / (1 - alpha))

/-- The exact coarse/fine ledger appearing on the right side of the partition chain rule. -/
def partitionLedger (q alpha withinH withinC : ℝ) : ℝ :=
  binaryKL q alpha + q * withinH + (1 - q) * withinC

/-- Paper Proposition 1, frozen at the algebraic ledger boundary. -/
theorem kl_chain_rule_habitable_partition
    (q alpha withinH withinC : ℝ) :
    partitionLedger q alpha withinH withinC =
      binaryKL q alpha + q * withinH + (1 - q) * withinC := by
  sorry

/-- Paper Corollary 1: nonnegative within-class divergences can only add cost. -/
theorem kl_ge_binary_habitable_mass
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 ≤ q) (hq1 : q ≤ 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    binaryKL q alpha ≤ partitionLedger q alpha withinH withinC := by
  sorry

/-- Paper Proposition 2: Bernoulli KL is monotone above its reference mass. -/
theorem binary_kl_monotone_above_reference
    (q tau alpha : ℝ)
    (ha0 : 0 < alpha) (ha1 : alpha < 1)
    (ht0 : 0 < tau) (ht1 : tau < 1)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hat : alpha ≤ tau) (htq : tau ≤ q) :
    binaryKL tau alpha ≤ binaryKL q alpha := by
  sorry

/-- Paper Corollary 2 after supplying the fixed-reference work inequality. -/
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

/-- Paper equality discussion: with positive class weights, excess vanishes iff both conditional costs vanish. -/
theorem equality_iff_reference_conditionals
    (q alpha withinH withinC : ℝ)
    (hq0 : 0 < q) (hq1 : q < 1)
    (hH : 0 ≤ withinH) (hC : 0 ≤ withinC) :
    partitionLedger q alpha withinH withinC = binaryKL q alpha ↔
      withinH = 0 ∧ withinC = 0 := by
  sorry

/-- Named non-vacuity witness: reference-shaped conditionals attain the binary floor. -/
theorem reference_shaped_conditionals_witness :
    partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 0 0 =
      binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) := by
  sorry

/-- Named non-vacuity witness: a positive within-H cost produces a strict excess. -/
theorem within_class_excess_witness :
    binaryKL (1 / 2 : ℝ) (1 / 3 : ℝ) <
      partitionLedger (1 / 2 : ℝ) (1 / 3 : ℝ) 2 0 := by
  sorry

end


end Viridis.Run123
