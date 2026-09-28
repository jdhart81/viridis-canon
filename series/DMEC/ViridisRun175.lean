import Mathlib

noncomputable section

namespace Viridis.DScore.MeasurementEnergyCeiling

def dscore (wS wP wG s p g : ℝ) : ℝ :=
  wS * s + wP * p + wG * g

def energyEnvelope (wS wP wG kS kP kG eS eP eG : ℝ) : ℝ :=
  wS * (kS * eS) + wP * (kP * eP) + wG * (kG * eG)

theorem energy_envelope_nonnegative
    (wS wP wG kS kP kG eS eP eG : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hkS : 0 ≤ kS) (hkP : 0 ≤ kP) (hkG : 0 ≤ kG)
    (heS : 0 ≤ eS) (heP : 0 ≤ eP) (heG : 0 ≤ eG) :
    0 ≤ energyEnvelope wS wP wG kS kP kG eS eP eG := by
  unfold energyEnvelope
  positivity

theorem componentwise_energy_ceiling
    (wS wP wG kS kP kG eS eP eG s p g : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hS : s ≤ kS * eS) (hP : p ≤ kP * eP) (hG : g ≤ kG * eG) :
    dscore wS wP wG s p g ≤
      energyEnvelope wS wP wG kS kP kG eS eP eG := by
  have hS' := mul_le_mul_of_nonneg_left hS hwS
  have hP' := mul_le_mul_of_nonneg_left hP hwP
  have hG' := mul_le_mul_of_nonneg_left hG hwG
  unfold dscore energyEnvelope
  linarith

theorem energy_envelope_monotone
    (wS wP wG kS kP kG eS eP eG qS qP qG : ℝ)
    (hwS : 0 ≤ wS) (hwP : 0 ≤ wP) (hwG : 0 ≤ wG)
    (hkS : 0 ≤ kS) (hkP : 0 ≤ kP) (hkG : 0 ≤ kG)
    (hS : eS ≤ qS) (hP : eP ≤ qP) (hG : eG ≤ qG) :
    energyEnvelope wS wP wG kS kP kG eS eP eG ≤
      energyEnvelope wS wP wG kS kP kG qS qP qG := by
  have hkS' := mul_le_mul_of_nonneg_left hS hkS
  have hkP' := mul_le_mul_of_nonneg_left hP hkP
  have hkG' := mul_le_mul_of_nonneg_left hG hkG
  have hwS' := mul_le_mul_of_nonneg_left hkS' hwS
  have hwP' := mul_le_mul_of_nonneg_left hkP' hwP
  have hwG' := mul_le_mul_of_nonneg_left hkG' hwG
  unfold energyEnvelope
  linarith

theorem zero_energy_envelope (wS wP wG kS kP kG : ℝ) :
    energyEnvelope wS wP wG kS kP kG 0 0 0 = 0 := by
  simp [energyEnvelope]

theorem energy_ceiling_positive_witness :
    dscore (1/2 : ℝ) (3/10 : ℝ) (1/5 : ℝ) 4 3 2 = 33/10 ∧
    energyEnvelope (1/2 : ℝ) (3/10 : ℝ) (1/5 : ℝ) 2 3 1 2 1 2 = 33/10 := by
  constructor <;> norm_num [dscore, energyEnvelope]

end Viridis.DScore.MeasurementEnergyCeiling
