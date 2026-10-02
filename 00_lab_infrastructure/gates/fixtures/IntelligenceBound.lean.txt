import Mathlib

noncomputable def cap (P D C : ℝ) : ℝ := P * D / C

theorem cap_nonneg (P D C : ℝ) (hP : 0 ≤ P) (hD : 0 ≤ D) (hC : 0 < C) :
    0 ≤ cap P D C := by
  exact div_nonneg ( mul_nonneg hP hD ) hC.le

theorem cap_eq_zero_iff (P D C : ℝ) (_hP : 0 ≤ P) (_hD : 0 ≤ D) (hC : 0 < C) :
    cap P D C = 0 ↔ P = 0 ∨ D = 0 := by
  unfold cap;
  aesop

theorem cap_strictMono_P (P1 P2 D C : ℝ) (hP : P1 < P2) (hD : 0 < D) (hC : 0 < C) :
    cap P1 D C < cap P2 D C := by
  unfold cap; gcongr;

theorem cap_strictMono_D (P D1 D2 C : ℝ) (hP : 0 < P) (hD : D1 < D2) (hC : 0 < C) :
    cap P D1 C < cap P D2 C := by
  exact div_lt_div_iff_of_pos_right hC |>.2 ( mul_lt_mul_of_pos_left hD hP )

theorem cap_strictAnti_C (P D C1 C2 : ℝ) (hP : 0 < P) (hD : 0 < D) (hC1 : 0 < C1) (hC2 : C1 < C2) :
    cap P D C2 < cap P D C1 := by
  exact div_lt_div_of_pos_left ( mul_pos hP hD ) hC1 hC2