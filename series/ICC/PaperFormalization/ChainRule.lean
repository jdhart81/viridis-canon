import PaperFormalization.Entropy

/-!
# Chain rules and nonnegativity for the finite-alphabet information measures

The information quantities of `PaperFormalization.Entropy` are defined in divergence form.
Here we prove:

* the marginalisation lemmas relating the six marginals of a `JointLaw`;
* the *entropy-algebra* formulas for each information quantity (`I_RY_eq`, `I_RS_eq`,
  `I_RY_given_S_eq`, `I_RS_given_Y_eq`, `H_Y_given_S_eq`, `H_Y_given_RS_eq`);
* nonnegativity of `I(R;Y)`, `I(R;S|Y)` (Gibbs' inequality) and of `H(Y|R,S)`.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-! ### Elementary `x * logb` manipulations, valid with the `0 log 0 = 0` convention -/

lemma mul_logb_two {x c : ℝ} (hx : 0 ≤ x) (hc : x ≠ 0 → 0 < c) :
    x * Real.logb 2 (x / c) = x * (Real.logb 2 x - Real.logb 2 c) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    rw [Real.logb_div hxne (ne_of_gt (hc hxne))]

lemma mul_logb_three {x c d : ℝ} (hx : 0 ≤ x) (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (x / (c * d)) = x * (Real.logb 2 x - Real.logb 2 c - Real.logb 2 d) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div hxne (by positivity), Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]
    ring

lemma mul_logb_four {x b c d : ℝ} (hx : 0 ≤ x) (hb : x ≠ 0 → 0 < b)
    (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (x * b / (c * d))
      = x * (Real.logb 2 x + Real.logb 2 b - Real.logb 2 c - Real.logb 2 d) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hbp := hb hxne
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div (by positivity) (by positivity), Real.logb_mul hxne (ne_of_gt hbp),
      Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]
    ring

lemma mul_logb_quot3 {x b c d : ℝ} (hx : 0 ≤ x) (hb : x ≠ 0 → 0 < b)
    (hc : x ≠ 0 → 0 < c) (hd : x ≠ 0 → 0 < d) :
    x * Real.logb 2 (c * d / b)
      = x * (Real.logb 2 c + Real.logb 2 d - Real.logb 2 b) := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · have hxne : x ≠ 0 := ne_of_gt hpos
    have hbp := hb hxne
    have hcp := hc hxne
    have hdp := hd hxne
    rw [Real.logb_div (by positivity) (by positivity),
      Real.logb_mul (ne_of_gt hcp) (ne_of_gt hdp)]

namespace JointLaw

variable {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ] (J : JointLaw ρ η σ)

/-! ### Marginalisation -/

lemma sum_s_p (r : ρ) (y : η) : ∑ s, J.p r y s = J.pRY (r, y) := rfl
lemma sum_y_p (r : ρ) (s : σ) : ∑ y, J.p r y s = J.pRS (r, s) := rfl
lemma sum_r_p (y : η) (s : σ) : ∑ r, J.p r y s = J.pYS (y, s) := rfl
lemma sum_y_pRY (r : ρ) : ∑ y, J.pRY (r, y) = J.pR r := rfl
lemma sum_r_pRY (y : η) : ∑ r, J.pRY (r, y) = J.pY y := rfl
lemma sum_r_pRS (s : σ) : ∑ r, J.pRS (r, s) = J.pS s := rfl

lemma sum_s_pRS (r : ρ) : ∑ s, J.pRS (r, s) = J.pR r := by
  simp only [pRS, pR]; exact Finset.sum_comm

lemma sum_s_pYS (y : η) : ∑ s, J.pYS (y, s) = J.pY y := by
  simp only [pYS, pY]; exact Finset.sum_comm

lemma sum_y_pYS (s : σ) : ∑ y, J.pYS (y, s) = J.pS s := by
  simp only [pYS, pS]; exact Finset.sum_comm

/-! ### Reduction of triple sums to marginal sums -/

lemma sum3_of_RY (f : ρ → η → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r y = ∑ r, ∑ y, J.pRY (r, y) * f r y :=
  Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => by
    rw [← Finset.sum_mul, sum_s_p]

lemma sum3_of_RS (f : ρ → σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r s = ∑ r, ∑ s, J.pRS (r, s) * f r s := by
  refine Finset.sum_congr rfl fun r _ => ?_
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_y_p]

lemma sum3_of_YS (f : η → σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f y s = ∑ y, ∑ s, J.pYS (y, s) * f y s := by
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun y _ => ?_
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_p]

lemma sum3_of_R (f : ρ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f r = ∑ r, J.pR r * f r := by
  rw [J.sum3_of_RY (fun r _ => f r)]
  exact Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_y_pRY]

lemma sum3_of_Y (f : η → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f y = ∑ y, J.pY y * f y := by
  rw [J.sum3_of_RY (fun _ y => f y), Finset.sum_comm]
  exact Finset.sum_congr rfl fun y _ => by rw [← Finset.sum_mul, sum_r_pRY]

lemma sum3_of_S (f : σ → ℝ) :
    ∑ r, ∑ y, ∑ s, J.p r y s * f s = ∑ s, J.pS s * f s := by
  rw [J.sum3_of_RS (fun _ s => f s), Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_pRS]

lemma sum2RY_of_R (f : ρ → ℝ) :
    ∑ r, ∑ y, J.pRY (r, y) * f r = ∑ r, J.pR r * f r :=
  Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_y_pRY]

lemma sum2RY_of_Y (f : η → ℝ) :
    ∑ r, ∑ y, J.pRY (r, y) * f y = ∑ y, J.pY y * f y := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun y _ => by rw [← Finset.sum_mul, sum_r_pRY]

lemma sum2RS_of_R (f : ρ → ℝ) :
    ∑ r, ∑ s, J.pRS (r, s) * f r = ∑ r, J.pR r * f r :=
  Finset.sum_congr rfl fun r _ => by rw [← Finset.sum_mul, sum_s_pRS]

lemma sum2RS_of_S (f : σ → ℝ) :
    ∑ r, ∑ s, J.pRS (r, s) * f s = ∑ s, J.pS s * f s := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_r_pRS]

lemma sum2YS_of_S (f : σ → ℝ) :
    ∑ y, ∑ s, J.pYS (y, s) * f s = ∑ s, J.pS s * f s := by
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun s _ => by rw [← Finset.sum_mul, sum_y_pYS]

/-! ### Entropies as explicit sums -/

lemma H_RYS_eq_sum :
    J.H_RYS = -∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (J.p r y s) := by
  simp [H_RYS, Hs, pRYS, Fintype.sum_prod_type]

lemma H_RY_eq_sum :
    J.H_RY = -∑ r, ∑ y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y)) := by
  simp [H_RY, Hs, Fintype.sum_prod_type]

lemma H_RS_eq_sum :
    J.H_RS = -∑ r, ∑ s, J.pRS (r, s) * Real.logb 2 (J.pRS (r, s)) := by
  simp [H_RS, Hs, Fintype.sum_prod_type]

lemma H_YS_eq_sum :
    J.H_YS = -∑ y, ∑ s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s)) := by
  simp [H_YS, Hs, Fintype.sum_prod_type]

lemma H_R_eq_sum : J.H_R = -∑ r, J.pR r * Real.logb 2 (J.pR r) := rfl
lemma H_Y_eq_sum : J.H_Y = -∑ y, J.pY y * Real.logb 2 (J.pY y) := rfl
lemma H_S_eq_sum : J.H_S = -∑ s, J.pS s * Real.logb 2 (J.pS s) := rfl

/-! ### Chain rules: divergence forms equal entropy combinations -/

/-- `H(Y|S) = H(Y,S) - H(S)`. -/
theorem H_Y_given_S_eq : J.H_Y_given_S = J.H_YS - J.H_S := by
  have hterm : ∀ y s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s) / J.pS s)
      = J.pYS (y, s) * Real.logb 2 (J.pYS (y, s)) - J.pYS (y, s) * Real.logb 2 (J.pS s) := by
    intro y s
    rw [mul_logb_two (J.pYS_nonneg (y, s))
      (fun h => lt_of_lt_of_le (lt_of_le_of_ne (J.pYS_nonneg (y, s)) (Ne.symm h))
        (J.pYS_le_pS y s))]
    ring
  simp only [H_Y_given_S]
  rw [Finset.sum_congr rfl fun y _ => Finset.sum_congr rfl fun s _ => hterm y s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2YS_of_S (fun s => Real.logb 2 (J.pS s)), H_YS_eq_sum, H_S_eq_sum]
  ring

/-- `H(Y|R,S) = H(R,Y,S) - H(R,S)`. -/
theorem H_Y_given_RS_eq : J.H_Y_given_RS = J.H_RYS - J.H_RS := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s / J.pRS (r, s))
      = J.p r y s * Real.logb 2 (J.p r y s) - J.p r y s * Real.logb 2 (J.pRS (r, s)) := by
    intro r y s
    rw [mul_logb_two (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)) (J.p_le_pRS r y s))]
    ring
  simp only [H_Y_given_RS]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum3_of_RS (fun r s => Real.logb 2 (J.pRS (r, s))), H_RYS_eq_sum, H_RS_eq_sum]
  ring

/-- `I(R;Y) = H(R) + H(Y) - H(R,Y)`. -/
theorem I_RY_eq : J.I_RY = J.H_R + J.H_Y - J.H_RY := by
  have hterm : ∀ r y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y) / (J.pR r * J.pY y))
      = J.pRY (r, y) * Real.logb 2 (J.pRY (r, y)) - J.pRY (r, y) * Real.logb 2 (J.pR r)
        - J.pRY (r, y) * Real.logb 2 (J.pY y) := by
    intro r y
    have hpos : J.pRY (r, y) ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    rw [mul_logb_three (J.pRY_nonneg (r, y))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRY_le_pR r y))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRY_le_pY r y))]
    ring
  simp only [I_RY]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => hterm r y]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2RY_of_R (fun r => Real.logb 2 (J.pR r)), J.sum2RY_of_Y (fun y => Real.logb 2 (J.pY y)),
    H_RY_eq_sum, H_R_eq_sum, H_Y_eq_sum]
  ring

/-- `I(R;S) = H(R) + H(S) - H(R,S)`. -/
theorem I_RS_eq : J.I_RS = J.H_R + J.H_S - J.H_RS := by
  have hterm : ∀ r s, J.pRS (r, s) * Real.logb 2 (J.pRS (r, s) / (J.pR r * J.pS s))
      = J.pRS (r, s) * Real.logb 2 (J.pRS (r, s)) - J.pRS (r, s) * Real.logb 2 (J.pR r)
        - J.pRS (r, s) * Real.logb 2 (J.pS s) := by
    intro r s
    have hpos : J.pRS (r, s) ≠ 0 → 0 < J.pRS (r, s) := fun h =>
      lt_of_le_of_ne (J.pRS_nonneg (r, s)) (Ne.symm h)
    rw [mul_logb_three (J.pRS_nonneg (r, s))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRS_le_pR r s))
      (fun h => lt_of_lt_of_le (hpos h) (J.pRS_le_pS r s))]
    ring
  simp only [I_RS]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun s _ => hterm r s]
  simp only [Finset.sum_sub_distrib]
  rw [J.sum2RS_of_R (fun r => Real.logb 2 (J.pR r)), J.sum2RS_of_S (fun s => Real.logb 2 (J.pS s)),
    H_RS_eq_sum, H_R_eq_sum, H_S_eq_sum]
  ring

/-- `I(R;Y|S) = H(R,S) + H(Y,S) - H(R,Y,S) - H(S)`. -/
theorem I_RY_given_S_eq : J.I_RY_given_S = J.H_RS + J.H_YS - J.H_RYS - J.H_S := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pS s / (J.pRS (r, s) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) + J.p r y s * Real.logb 2 (J.pS s)
        - J.p r y s * Real.logb 2 (J.pRS (r, s)) - J.p r y s * Real.logb 2 (J.pYS (y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    rw [mul_logb_four (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (hpos h) (le_trans (J.p_le_pRS r y s) (J.pRS_le_pS r s)))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pRS r y s))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s))]
    ring
  simp only [I_RY_given_S]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib]
  rw [J.sum3_of_S (fun s => Real.logb 2 (J.pS s)),
    J.sum3_of_RS (fun r s => Real.logb 2 (J.pRS (r, s))),
    J.sum3_of_YS (fun y s => Real.logb 2 (J.pYS (y, s))),
    H_RYS_eq_sum, H_RS_eq_sum, H_YS_eq_sum, H_S_eq_sum]
  ring

/-- `I(R;S|Y) = H(R,Y) + H(Y,S) - H(R,Y,S) - H(Y)`. -/
theorem I_RS_given_Y_eq : J.I_RS_given_Y = J.H_RY + J.H_YS - J.H_RYS - J.H_Y := by
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pY y / (J.pRY (r, y) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) + J.p r y s * Real.logb 2 (J.pY y)
        - J.p r y s * Real.logb 2 (J.pRY (r, y)) - J.p r y s * Real.logb 2 (J.pYS (y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    rw [mul_logb_four (J.nonneg r y s)
      (fun h => lt_of_lt_of_le (hpos h) (le_trans (J.p_le_pRY r y s) (J.pRY_le_pY r y)))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s))
      (fun h => lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s))]
    ring
  simp only [I_RS_given_Y]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib, Finset.sum_add_distrib]
  rw [J.sum3_of_Y (fun y => Real.logb 2 (J.pY y)),
    J.sum3_of_RY (fun r y => Real.logb 2 (J.pRY (r, y))),
    J.sum3_of_YS (fun y s => Real.logb 2 (J.pYS (y, s))),
    H_RYS_eq_sum, H_RY_eq_sum, H_YS_eq_sum, H_Y_eq_sum]
  ring

/-! ### Nonnegativity -/

/-- Conditional entropy is nonnegative: `H(Y|R,S) ≥ 0`. -/
theorem H_Y_given_RS_nonneg : 0 ≤ J.H_Y_given_RS := by
  simp only [H_Y_given_RS, neg_nonneg]
  refine Finset.sum_nonpos fun r _ => Finset.sum_nonpos fun y _ => Finset.sum_nonpos fun s _ => ?_
  rcases eq_or_lt_of_le (J.nonneg r y s) with h0 | hpos
  · simp [← h0]
  · refine mul_nonpos_of_nonneg_of_nonpos (J.nonneg r y s) ?_
    refine Real.logb_nonpos (by norm_num)
      (div_nonneg (J.nonneg r y s) (J.pRS_nonneg (r, s))) ?_
    rw [div_le_one (lt_of_lt_of_le hpos (J.p_le_pRS r y s))]
    exact J.p_le_pRS r y s

/-- Mutual information is nonnegative: `I(R;Y) ≥ 0`. -/
theorem I_RY_nonneg : 0 ≤ J.I_RY := by
  have hQnonneg : ∀ x : ρ × η, 0 ≤ J.pR x.1 * J.pY x.2 := fun x =>
    mul_nonneg (J.pR_nonneg x.1) (J.pY_nonneg x.2)
  have hac : ∀ x : ρ × η, J.pRY x ≠ 0 → J.pR x.1 * J.pY x.2 ≠ 0 := by
    rintro ⟨r, y⟩ h
    have hpos : 0 < J.pRY (r, y) := lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    exact ne_of_gt (mul_pos (lt_of_lt_of_le hpos (J.pRY_le_pR r y))
      (lt_of_lt_of_le hpos (J.pRY_le_pY r y)))
  have hsum : ∑ x : ρ × η, J.pR x.1 * J.pY x.2 ≤ ∑ x : ρ × η, J.pRY x := by
    rw [Fintype.sum_prod_type, Fintype.sum_prod_type]
    have h1 : ∑ r, ∑ y, J.pR r * J.pY y = 1 := by
      rw [Finset.sum_congr rfl fun r _ => by rw [← Finset.mul_sum, J.sum_pY, mul_one]]
      exact J.sum_pR
    rw [h1, J.sum_pRY]
  have gibbs := sum_mul_logb_le J.pRY (fun x => J.pR x.1 * J.pY x.2)
    (fun x => J.pRY_nonneg x) hQnonneg hac hsum
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type] at gibbs
  have hterm : ∀ r y, J.pRY (r, y) * Real.logb 2 (J.pRY (r, y) / (J.pR r * J.pY y))
      = J.pRY (r, y) * Real.logb 2 (J.pRY (r, y))
        - J.pRY (r, y) * Real.logb 2 (J.pR r * J.pY y) := by
    intro r y
    have hpos : J.pRY (r, y) ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_le_of_ne (J.pRY_nonneg (r, y)) (Ne.symm h)
    rcases eq_or_lt_of_le (J.pRY_nonneg (r, y)) with h0 | hp
    · simp [← h0]
    · have hRpos := lt_of_lt_of_le hp (J.pRY_le_pR r y)
      have hYpos := lt_of_lt_of_le hp (J.pRY_le_pY r y)
      rw [Real.logb_div (ne_of_gt hp) (by positivity)]
      ring
  simp only [I_RY]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ => hterm r y]
  simp only [Finset.sum_sub_distrib]
  linarith

/-- Conditional mutual information is nonnegative: `I(R;S|Y) ≥ 0`.
This is Gibbs' inequality applied to the joint law against the product-form kernel
`p(r,y) p(y,s) / p(y)`. -/
theorem I_RS_given_Y_nonneg : 0 ≤ J.I_RS_given_Y := by
  set Q : ρ × η × σ → ℝ :=
    fun x => J.pRY (x.1, x.2.1) * J.pYS (x.2.1, x.2.2) / J.pY x.2.1 with hQ
  have hQnonneg : ∀ x, 0 ≤ Q x := by
    rintro ⟨r, y, s⟩
    exact div_nonneg (mul_nonneg (J.pRY_nonneg (r, y)) (J.pYS_nonneg (y, s))) (J.pY_nonneg y)
  have hac : ∀ x, J.pRYS x ≠ 0 → Q x ≠ 0 := by
    rintro ⟨r, y, s⟩ h
    have hpos : 0 < J.p r y s := lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    have h1 : 0 < J.pRY (r, y) := lt_of_lt_of_le hpos (J.p_le_pRY r y s)
    have h2 : 0 < J.pYS (y, s) := lt_of_lt_of_le hpos (J.p_le_pYS r y s)
    have h3 : 0 < J.pY y := lt_of_lt_of_le h1 (J.pRY_le_pY r y)
    exact ne_of_gt (div_pos (mul_pos h1 h2) h3)
  have hsum : ∑ x, Q x ≤ ∑ x, J.pRYS x := by
    have hQsum : ∑ x, Q x = ∑ y, (J.pY y * J.pY y) / J.pY y := by
      simp only [hQ, Fintype.sum_prod_type]
      rw [Finset.sum_comm]
      refine Finset.sum_congr rfl fun y _ => ?_
      have h1 : ∀ r, ∑ s, J.pRY (r, y) * J.pYS (y, s) / J.pY y
          = J.pRY (r, y) * J.pY y / J.pY y := by
        intro r
        rw [← Finset.sum_div, ← Finset.mul_sum, J.sum_s_pYS]
      rw [Finset.sum_congr rfl fun r _ => h1 r, ← Finset.sum_div, ← Finset.sum_mul, J.sum_r_pRY]
    have hle : ∑ y, (J.pY y * J.pY y) / J.pY y ≤ ∑ y, J.pY y := by
      refine Finset.sum_le_sum fun y _ => ?_
      rcases eq_or_lt_of_le (J.pY_nonneg y) with h0 | hp
      · simp [← h0]
      · rw [mul_div_assoc, div_self (ne_of_gt hp), mul_one]
    rw [hQsum]
    calc ∑ y, (J.pY y * J.pY y) / J.pY y ≤ ∑ y, J.pY y := hle
      _ = 1 := J.sum_pY
      _ = ∑ x, J.pRYS x := by
          rw [Fintype.sum_prod_type]
          simpa [pRYS, Fintype.sum_prod_type] using J.total.symm
  have gibbs := sum_mul_logb_le J.pRYS Q (fun x => J.pRYS_nonneg x) hQnonneg hac hsum
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type] at gibbs
  simp only [Fintype.sum_prod_type] at gibbs
  have hterm : ∀ r y s, J.p r y s * Real.logb 2 (J.p r y s * J.pY y / (J.pRY (r, y) * J.pYS (y, s)))
      = J.p r y s * Real.logb 2 (J.p r y s) - J.p r y s * Real.logb 2 (Q (r, y, s)) := by
    intro r y s
    have hpos : J.p r y s ≠ 0 → 0 < J.p r y s := fun h =>
      lt_of_le_of_ne (J.nonneg r y s) (Ne.symm h)
    have hb : J.p r y s ≠ 0 → 0 < J.pY y := fun h =>
      lt_of_lt_of_le (lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s)) (J.pRY_le_pY r y)
    have hc : J.p r y s ≠ 0 → 0 < J.pRY (r, y) := fun h =>
      lt_of_lt_of_le (hpos h) (J.p_le_pRY r y s)
    have hd : J.p r y s ≠ 0 → 0 < J.pYS (y, s) := fun h =>
      lt_of_lt_of_le (hpos h) (J.p_le_pYS r y s)
    rw [mul_logb_four (J.nonneg r y s) hb hc hd]
    simp only [hQ]
    rw [mul_logb_quot3 (J.nonneg r y s) hb hc hd]
    ring
  simp only [I_RS_given_Y]
  rw [Finset.sum_congr rfl fun r _ => Finset.sum_congr rfl fun y _ =>
    Finset.sum_congr rfl fun s _ => hterm r y s]
  simp only [Finset.sum_sub_distrib]
  have : ∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (Q (r, y, s))
      ≤ ∑ r, ∑ y, ∑ s, J.p r y s * Real.logb 2 (J.p r y s) := gibbs
  linarith

end JointLaw

end Viridis.Run126.PaperFormalization
