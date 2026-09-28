import Mathlib

noncomputable section

namespace Viridis.GaianSystems.ReciprocalRescue

def loopDenom (m n : ℝ) : ℝ := 1 - m * n
def equilibriumA (rA rB m n : ℝ) : ℝ := (rA + m * rB) / loopDenom m n
def equilibriumB (rA rB m n : ℝ) : ℝ := (rB + n * rA) / loopDenom m n

theorem equilibrium_balance_a (rA rB m n : ℝ) (h : loopDenom m n ≠ 0) :
    equilibriumA rA rB m n - m * equilibriumB rA rB m n = rA := by
  unfold equilibriumA equilibriumB loopDenom at *
  field_simp
  ring

theorem equilibrium_balance_b (rA rB m n : ℝ) (h : loopDenom m n ≠ 0) :
    equilibriumB rA rB m n - n * equilibriumA rA rB m n = rB := by
  have hn : loopDenom n m ≠ 0 := by
    simpa [loopDenom, mul_comm] using h
  simpa [equilibriumA, equilibriumB, loopDenom, mul_comm] using
    (equilibrium_balance_a rB rA n m hn)

theorem positive_equilibrium_of_positive_numerators
    (rA rB m n : ℝ) (hd : 0 < loopDenom m n)
    (hA : 0 < rA + m * rB) (hB : 0 < rB + n * rA) :
    0 < equilibriumA rA rB m n ∧ 0 < equilibriumB rA rB m n := by
  constructor
  · exact div_pos hA hd
  · exact div_pos hB hd

theorem no_two_decliner_positive_equilibrium
    (rA rB m n : ℝ) (hd : 0 < loopDenom m n)
    (hrA : rA ≤ 0) (hrB : rB ≤ 0) (hm : 0 ≤ m) (hn : 0 ≤ n) :
    equilibriumA rA rB m n ≤ 0 ∧ equilibriumB rA rB m n ≤ 0 := by
  have hmrB : m * rB ≤ 0 := mul_nonpos_of_nonneg_of_nonpos hm hrB
  have hnrA : n * rA ≤ 0 := mul_nonpos_of_nonneg_of_nonpos hn hrA
  constructor
  · exact div_nonpos_of_nonpos_of_nonneg (add_nonpos hrA hmrB) (le_of_lt hd)
  · exact div_nonpos_of_nonpos_of_nonneg (add_nonpos hrB hnrA) (le_of_lt hd)

theorem one_sided_rescue_window
    (rA rB m n : ℝ) (hd : 0 < loopDenom m n)
    (hhelp : -rA < m * rB) (hburden : n * (-rA) < rB) :
    0 < equilibriumA rA rB m n ∧ 0 < equilibriumB rA rB m n := by
  apply positive_equilibrium_of_positive_numerators rA rB m n hd
  · linarith
  · nlinarith

theorem reciprocal_rescue_witness :
    loopDenom (1 / 2 : ℝ) (1 / 4 : ℝ) = 7 / 8 ∧
    equilibriumA (-1) 3 (1 / 2) (1 / 4) = 4 / 7 ∧
    equilibriumB (-1) 3 (1 / 2) (1 / 4) = 22 / 7 := by
  norm_num [loopDenom, equilibriumA, equilibriumB]

theorem unit_loop_boundary : loopDenom (1 : ℝ) 1 = 0 := by
  norm_num [loopDenom]

end Viridis.GaianSystems.ReciprocalRescue
