import Mathlib

noncomputable section

namespace Viridis.IntelligenceBound.SymbioticTransferThreshold

def effectiveA (a b eta cost : ℝ) : ℝ := a + eta * b - cost
def effectiveB (a b eta cost : ℝ) : ℝ := b + eta * a - cost
def cooperativeBottleneck (a b eta cost : ℝ) : ℝ :=
  min (effectiveA a b eta cost) (effectiveB a b eta cost)

theorem effective_gap_identity (a b eta cost : ℝ) :
    effectiveB a b eta cost - effectiveA a b eta cost =
      (1 - eta) * (b - a) := by
  unfold effectiveA effectiveB
  ring

theorem ordered_effective_rates (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    effectiveA a b eta cost ≤ effectiveB a b eta cost := by
  unfold effectiveA effectiveB
  nlinarith

theorem bottleneck_reduction (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    cooperativeBottleneck a b eta cost = effectiveA a b eta cost := by
  unfold cooperativeBottleneck
  rw [min_eq_left (ordered_effective_rates a b eta cost hab heta)]

theorem bottleneck_formula (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    cooperativeBottleneck a b eta cost = a + eta * b - cost := by
  rw [bottleneck_reduction a b eta cost hab heta]
  rfl

theorem cooperation_gain_identity (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    cooperativeBottleneck a b eta cost - a = eta * b - cost := by
  rw [bottleneck_formula a b eta cost hab heta]
  ring

theorem positive_gain_iff (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    0 < cooperativeBottleneck a b eta cost - a ↔ cost < eta * b := by
  rw [cooperation_gain_identity a b eta cost hab heta]
  exact sub_pos

theorem nonnegative_bottleneck_iff (a b eta cost : ℝ)
    (hab : a ≤ b) (heta : eta ≤ 1) :
    0 ≤ cooperativeBottleneck a b eta cost ↔ cost ≤ a + eta * b := by
  rw [bottleneck_formula a b eta cost hab heta]
  exact sub_nonneg

theorem transfer_efficiency_monotone (a b etaOne etaTwo cost : ℝ)
    (hab : a ≤ b) (hetaOne : etaOne ≤ 1) (hetaTwo : etaTwo ≤ 1)
    (hetaOrder : etaOne ≤ etaTwo) (hb : 0 ≤ b) :
    cooperativeBottleneck a b etaOne cost ≤
      cooperativeBottleneck a b etaTwo cost := by
  rw [bottleneck_formula a b etaOne cost hab hetaOne]
  rw [bottleneck_formula a b etaTwo cost hab hetaTwo]
  nlinarith

theorem symbiotic_transfer_witness :
    effectiveA 2 5 (1 / 2) 1 = 7 / 2 ∧
    effectiveB 2 5 (1 / 2) 1 = 5 ∧
    cooperativeBottleneck 2 5 (1 / 2) 1 = 7 / 2 := by
  norm_num [effectiveA, effectiveB, cooperativeBottleneck]

theorem coordination_cost_negative_control :
    cooperativeBottleneck 2 5 (1 / 2) 3 = 3 / 2 ∧
    cooperativeBottleneck 2 5 (1 / 2) 3 - 2 < 0 := by
  norm_num [effectiveA, effectiveB, cooperativeBottleneck]

end Viridis.IntelligenceBound.SymbioticTransferThreshold
