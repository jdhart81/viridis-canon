import PaperFormalization.Claims

/-!
# C5 — the tight erasure family (Proposition 1)

Paper statement (Proposition 1, Eq. 5): let `S` and `U` be independent fair bits, let
`Y = (S, U)`, and let `L` reveal `S` with probability `q` and otherwise output an erasure
symbol.  For `R = (U, L)`,
`I(R;S) = q`, `H(Y|S) = 1`, `I(R;Y) = 1 + q`,
so the ceiling `I(R;Y) ≤ H(Y|S) + δ` of Corollary 1 is tight for every `q ∈ [0,1]` bit.

Formalization: the alphabets are `ρ = Bool × Option Bool` (the pair `(U, L)`, with `none`
the erasure symbol), `η = Bool × Bool` (the pair `(S, U)`) and `σ = Bool` (the proxy `S`),
and the joint mass function is
`p (u,l) (y₁,y₂) s = ¼ · leak q l s` when `y₁ = s` and `y₂ = u`, and `0` otherwise.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-- The binary erasure channel used by Proposition 1: on input `s` it outputs `some s`
with probability `q` and the erasure symbol `none` with probability `1 - q`. -/
noncomputable def leak (q : ℝ) : Option Bool → Bool → ℝ :=
  fun l s => if l = some s then q else if l = none then 1 - q else 0

lemma leak_nonneg {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1) (l : Option Bool) (s : Bool) :
    0 ≤ leak q l s := by
  unfold leak
  split
  · exact hq0
  · split
    · linarith
    · exact le_refl 0

lemma leak_none (q : ℝ) (s : Bool) : leak q none s = 1 - q := by simp [leak]

lemma leak_some_self (q : ℝ) (b : Bool) : leak q (some b) b = q := by simp [leak]

lemma leak_some_tf (q : ℝ) : leak q (some true) false = 0 := by simp [leak]

lemma leak_some_ft (q : ℝ) : leak q (some false) true = 0 := by simp [leak]

/-- The independent-bit plus erasure-leakage family of Proposition 1:
`S, U` independent fair bits, `Y = (S, U)`, `L` the erasure-channel output on `S`,
and `R = (U, L)`. -/
noncomputable def erasureLaw (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    JointLaw (Bool × Option Bool) (Bool × Bool) Bool where
  p r y s := if y.1 = s ∧ y.2 = r.1 then (1 / 4) * leak q r.2 s else 0
  nonneg := by
    intro r y s
    split
    · have h := leak_nonneg hq0 hq1 r.2 s
      positivity
    · exact le_refl 0
  total := by
    simp [Fintype.sum_prod_type, Fintype.sum_option, leak]
    ring

section
variable {q : ℝ} (hq0 : 0 ≤ q) (hq1 : q ≤ 1)

/-! ### Marginals of the erasure family -/

lemma erasure_pS (s : Bool) : (erasureLaw q hq0 hq1).pS s = 1 / 2 := by
  cases s <;> simp [JointLaw.pS, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pY (y : Bool × Bool) : (erasureLaw q hq0 hq1).pY y = 1 / 4 := by
  obtain ⟨y1, y2⟩ := y
  cases y1 <;> cases y2 <;>
    simp [JointLaw.pY, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pYS (y1 y2 s : Bool) :
    (erasureLaw q hq0 hq1).pYS ((y1, y2), s) = if y1 = s then 1 / 4 else 0 := by
  cases y1 <;> cases y2 <;> cases s <;>
    simp [JointLaw.pYS, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pR_none (u : Bool) : (erasureLaw q hq0 hq1).pR (u, none) = (1 - q) / 2 := by
  cases u <;> simp [JointLaw.pR, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pR_some (u b : Bool) : (erasureLaw q hq0 hq1).pR (u, some b) = q / 4 := by
  cases u <;> cases b <;> simp [JointLaw.pR, erasureLaw, Fintype.sum_prod_type, leak] <;> ring

lemma erasure_pRY_diag (u : Bool) (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((u, l), (y1, u)) = leak q l y1 / 4 := by
  cases u <;> cases y1 <;> simp [JointLaw.pRY, erasureLaw] <;> ring

lemma erasure_pRY_tf (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((true, l), (y1, false)) = 0 := by
  cases y1 <;> simp [JointLaw.pRY, erasureLaw]

lemma erasure_pRY_ft (l : Option Bool) (y1 : Bool) :
    (erasureLaw q hq0 hq1).pRY ((false, l), (y1, true)) = 0 := by
  cases y1 <;> simp [JointLaw.pRY, erasureLaw]

lemma erasure_pRS (u : Bool) (l : Option Bool) (s : Bool) :
    (erasureLaw q hq0 hq1).pRS ((u, l), s) = leak q l s / 4 := by
  cases u <;> cases s <;> simp [JointLaw.pRS, erasureLaw, Fintype.sum_prod_type] <;> ring

/-! ### Entropies of the erasure family -/

/-- The binary-entropy shorthand `A q = -q log₂ q - (1-q) log₂ (1-q)`. -/
noncomputable def binEnt (q : ℝ) : ℝ :=
  -(q * Real.logb 2 q) - (1 - q) * Real.logb 2 (1 - q)

private lemma div_mul_logb_div {x c : ℝ} (hx : 0 ≤ x) (hc : 0 < c) :
    x / c * Real.logb 2 (x / c) = (x * Real.logb 2 x - x * Real.logb 2 c) / c := by
  rcases eq_or_lt_of_le hx with h0 | hpos
  · simp [← h0]
  · rw [Real.logb_div (ne_of_gt hpos) (ne_of_gt hc)]
    ring

private lemma logb2_four : Real.logb 2 (4 : ℝ) = 2 := by
  have h : (4 : ℝ) = 2 * 2 := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_two]
  norm_num

private lemma logb_q_div_four (hq0 : 0 ≤ q) :
    q / 4 * Real.logb 2 (q / 4) = (q * Real.logb 2 q - 2 * q) / 4 := by
  rw [div_mul_logb_div hq0 (by norm_num : (0:ℝ) < 4), logb2_four]
  ring

private lemma logb_one_sub_q_div_four (hq1 : q ≤ 1) :
    (1 - q) / 4 * Real.logb 2 ((1 - q) / 4) = ((1 - q) * Real.logb 2 (1 - q) - 2 * (1 - q)) / 4 := by
  rw [div_mul_logb_div (by linarith) (by norm_num : (0:ℝ) < 4), logb2_four]
  ring

private lemma logb_one_sub_q_div_two (hq1 : q ≤ 1) :
    (1 - q) / 2 * Real.logb 2 ((1 - q) / 2) = ((1 - q) * Real.logb 2 (1 - q) - (1 - q)) / 2 := by
  rw [div_mul_logb_div (by linarith) (by norm_num : (0:ℝ) < 2), logb2_two]
  ring

lemma erasure_H_S : (erasureLaw q hq0 hq1).H_S = 1 := by
  rw [JointLaw.H_S_eq_sum]
  simp only [Fintype.sum_bool, erasure_pS]
  norm_num [logb2_half]

lemma erasure_H_Y : (erasureLaw q hq0 hq1).H_Y = 2 := by
  rw [JointLaw.H_Y_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, erasure_pY]
  norm_num [logb2_quarter]

lemma erasure_H_YS : (erasureLaw q hq0 hq1).H_YS = 2 := by
  rw [JointLaw.H_YS_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, erasure_pYS]
  norm_num [logb2_quarter]

lemma erasure_H_R : (erasureLaw q hq0 hq1).H_R = binEnt q + 1 + q := by
  rw [JointLaw.H_R_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pR_none, erasure_pR_some]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_two hq1]
  unfold binEnt
  ring

lemma erasure_H_RY : (erasureLaw q hq0 hq1).H_RY = binEnt q + 2 := by
  rw [JointLaw.H_RY_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pRY_diag, erasure_pRY_tf, erasure_pRY_ft, leak_none, leak_some_self, leak_some_tf,
    leak_some_ft, zero_div, zero_mul, add_zero, zero_add]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_four hq1]
  unfold binEnt
  ring

lemma erasure_H_RS : (erasureLaw q hq0 hq1).H_RS = binEnt q + 2 := by
  rw [JointLaw.H_RS_eq_sum]
  simp only [Fintype.sum_prod_type, Fintype.sum_bool, Fintype.sum_option,
    erasure_pRS, leak_none, leak_some_self, leak_some_tf, leak_some_ft, zero_div, zero_mul,
    add_zero, zero_add]
  rw [logb_q_div_four hq0, logb_one_sub_q_div_four hq1]
  unfold binEnt
  ring

/-! ### C5 -/

/-- **C5 (Proposition 1).** For the independent-bit plus erasure-leakage family with
erasure-channel reliability `q ∈ [0,1]`:
`I(R;S) = q`, `H(Y|S) = 1` and `I(R;Y) = 1 + q`; consequently the forbidden-proxy
capacity ceiling `I(R;Y) ≤ H(Y|S) + δ` of Corollary 1 is attained with equality at the
leakage budget `δ = q`, for every `q ∈ [0,1]`. -/
theorem erasure_family_tightness (q : ℝ) (hq0 : 0 ≤ q) (hq1 : q ≤ 1) :
    (erasureLaw q hq0 hq1).I_RS = q ∧
      (erasureLaw q hq0 hq1).H_Y_given_S = 1 ∧
      (erasureLaw q hq0 hq1).I_RY = 1 + q ∧
      (erasureLaw q hq0 hq1).I_RY = (erasureLaw q hq0 hq1).H_Y_given_S + q := by
  have hR := erasure_H_R hq0 hq1
  have hY := erasure_H_Y hq0 hq1
  have hS := erasure_H_S hq0 hq1
  have hRY := erasure_H_RY hq0 hq1
  have hRS := erasure_H_RS hq0 hq1
  have hYS := erasure_H_YS hq0 hq1
  have hIRS : (erasureLaw q hq0 hq1).I_RS = q := by
    rw [JointLaw.I_RS_eq, hR, hS, hRS]; ring
  have hHYS : (erasureLaw q hq0 hq1).H_Y_given_S = 1 := by
    rw [JointLaw.H_Y_given_S_eq, hYS, hS]; ring
  have hIRY : (erasureLaw q hq0 hq1).I_RY = 1 + q := by
    rw [JointLaw.I_RY_eq, hR, hY, hRY]; ring
  exact ⟨hIRS, hHYS, hIRY, by rw [hIRY, hHYS]⟩

end

/-! ### Non-vacuity witness for C5 -/

/-- **Non-vacuity for C5.** At `q = 1/2` the family is a concrete finite law with
`I(R;S) = 1/2`, `H(Y|S) = 1` and `I(R;Y) = 3/2`: the leakage budget is nonzero, the task
information is nonzero, and the ceiling of C2 is attained. -/
theorem erasure_family_tightness_nonvacuity :
    (erasureLaw (1/2) (by norm_num) (by norm_num)).I_RS = 1/2 ∧
      (erasureLaw (1/2) (by norm_num) (by norm_num)).H_Y_given_S = 1 ∧
      (erasureLaw (1/2) (by norm_num) (by norm_num)).I_RY = 3/2 := by
  obtain ⟨h1, h2, h3, -⟩ := erasure_family_tightness (1/2) (by norm_num) (by norm_num)
  exact ⟨h1, h2, by rw [h3]; norm_num⟩

end Viridis.Run126.PaperFormalization
