import PaperFormalization.ChainRule

/-!
# The frozen Run-126 claims C1–C4

This file states and proves the first four named targets of `STATEMENT_CONTRACT.md`:

* `mutual_information_chain_balance`      (C1, Theorem 1, Eq. 1);
* `forbidden_proxy_capacity_ceiling`      (C2, Corollary 1, Eq. 2);
* `capacity_ceiling_slack_decomposition`  (C3, Theorem 1, Eq. 3);
* `perfect_invariance_target_proxy_collapse` (C4, Boundary cases).

Target C5 (`erasure_family_tightness`, Proposition 1) is in
`PaperFormalization.ErasureFamily`.

Each claim is followed by explicit non-vacuity witnesses: concrete finite joint laws for
which the hypotheses hold and all quantities appearing in the statement are computed.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-! ### Numerical values of `logb 2` used by the witnesses -/

lemma logb2_two : Real.logb 2 (2 : ℝ) = 1 := Real.logb_self_eq_one (by norm_num)

lemma logb2_half : Real.logb 2 (1 / 2 : ℝ) = -1 := by
  rw [one_div, Real.logb_inv, logb2_two]

lemma logb2_quarter : Real.logb 2 (1 / 4 : ℝ) = -2 := by
  have h : (1 / 4 : ℝ) = (1 / 2) * (1 / 2) := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_half]
  norm_num

lemma logb2_eighth : Real.logb 2 (1 / 8 : ℝ) = -3 := by
  have h : (1 / 8 : ℝ) = (1 / 4) * (1 / 2) := by norm_num
  rw [h, Real.logb_mul (by norm_num) (by norm_num), logb2_half, logb2_quarter]
  norm_num

/-! ### C1 — `mutual_information_chain_balance` (Theorem 1, Eq. 1)

Paper statement: for finite `R, Y, S`, `I(R;Y) = I(R;Y|S) + I(R;S) - I(R;S|Y)`. -/

/-- **C1 (Theorem 1, Eq. 1).** For every finite joint law of `(R, Y, S)`,
`I(R;Y) = I(R;Y|S) + I(R;S) - I(R;S|Y)`. -/
theorem mutual_information_chain_balance {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) :
    J.I_RY = J.I_RY_given_S + J.I_RS - J.I_RS_given_Y := by
  rw [J.I_RY_eq, J.I_RY_given_S_eq, J.I_RS_eq, J.I_RS_given_Y_eq]
  ring

/-! ### C2 — `forbidden_proxy_capacity_ceiling` (Corollary 1, Eq. 2)

Paper statement: if `I(R;S) ≤ δ` then `I(R;Y) ≤ H(Y|S) + δ`. -/

/-- **C2 (Corollary 1, Eq. 2).** A forbidden-proxy leakage budget `I(R;S) ≤ δ` implies the
task-information ceiling `I(R;Y) ≤ H(Y|S) + δ`. -/
theorem forbidden_proxy_capacity_ceiling {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) (δ : ℝ) (hδ : J.I_RS ≤ δ) :
    J.I_RY ≤ J.H_Y_given_S + δ := by
  have h1 := J.H_Y_given_RS_nonneg
  have h2 := J.I_RS_given_Y_nonneg
  have hbal : J.H_Y_given_S + J.I_RS - J.I_RY = J.H_Y_given_RS + J.I_RS_given_Y := by
    rw [J.H_Y_given_S_eq, J.I_RS_eq, J.I_RY_eq, J.H_Y_given_RS_eq, J.I_RS_given_Y_eq]
    ring
  linarith

/-- **C2, Eq. 4 (combined ceiling).** If an independently justified ceiling `C` also holds,
then `I(R;Y) ≤ min C (H(Y|S) + δ)`. -/
theorem forbidden_proxy_capacity_ceiling_combined {ρ η σ : Type*} [Fintype ρ] [Fintype η]
    [Fintype σ] (J : JointLaw ρ η σ) (δ C : ℝ) (hδ : J.I_RS ≤ δ) (hC : J.I_RY ≤ C) :
    J.I_RY ≤ min C (J.H_Y_given_S + δ) :=
  le_min hC (forbidden_proxy_capacity_ceiling J δ hδ)

/-! ### C3 — `capacity_ceiling_slack_decomposition` (Theorem 1, Eq. 3)

Paper statement: `H(Y|S) + I(R;S) - I(R;Y) = H(Y|R,S) + I(R;S|Y) ≥ 0`. -/

/-- **C3 (Theorem 1, Eq. 3).** The ceiling slack decomposes exactly as
`H(Y|S) + I(R;S) - I(R;Y) = H(Y|R,S) + I(R;S|Y)`, and this common value is nonnegative. -/
theorem capacity_ceiling_slack_decomposition {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) :
    J.H_Y_given_S + J.I_RS - J.I_RY = J.H_Y_given_RS + J.I_RS_given_Y ∧
      0 ≤ J.H_Y_given_RS + J.I_RS_given_Y := by
  constructor
  · rw [J.H_Y_given_S_eq, J.I_RS_eq, J.I_RY_eq, J.H_Y_given_RS_eq, J.I_RS_given_Y_eq]
    ring
  · linarith [J.H_Y_given_RS_nonneg, J.I_RS_given_Y_nonneg]

/-! ### C4 — `perfect_invariance_target_proxy_collapse` (Boundary cases)

Paper statement: when `Y = S`, perfect invariance (`I(R;S) = 0`) forces `I(R;Y) = 0`.

`Y = S` is formalized as: the joint law is supported on the diagonal `y = s`, which is
exactly the statement that the random variables `Y` and `S` are almost surely equal. -/

/-- If the joint law is supported on `y = s`, then `H(Y|S) = 0`. -/
theorem H_Y_given_S_eq_zero_of_diagonal {ρ η : Type*} [Fintype ρ] [Fintype η]
    (J : JointLaw ρ η η) (hdiag : ∀ r y s, y ≠ s → J.p r y s = 0) :
    J.H_Y_given_S = 0 := by
  have hoff : ∀ y s : η, y ≠ s → J.pYS (y, s) = 0 := by
    intro y s hys
    simp only [JointLaw.pYS]
    exact Finset.sum_eq_zero fun r _ => hdiag r y s hys
  have hdiagS : ∀ s : η, J.pYS (s, s) = J.pS s := by
    intro s
    rw [← J.sum_y_pYS s]
    refine (Finset.sum_eq_single s (fun y _ hy => hoff y s hy) (by simp)).symm
  rw [J.H_Y_given_S_eq, JointLaw.H_YS_eq_sum, JointLaw.H_S_eq_sum]
  have hrow : ∀ y : η, ∑ s, J.pYS (y, s) * Real.logb 2 (J.pYS (y, s))
      = J.pS y * Real.logb 2 (J.pS y) := by
    intro y
    rw [Finset.sum_eq_single y (fun s _ hs => by rw [hoff y s (Ne.symm hs)]; ring) (by simp)]
    rw [hdiagS y]
  rw [Finset.sum_congr rfl fun y _ => hrow y]
  ring

/-- **C4 (Boundary cases).** If the task target equals the forbidden proxy (`Y = S`, i.e. the
law is supported on the diagonal) and the representation is perfectly invariant
(`I(R;S) = 0`), then the representation carries no task information: `I(R;Y) = 0`. -/
theorem perfect_invariance_target_proxy_collapse {ρ η : Type*} [Fintype ρ] [Fintype η]
    (J : JointLaw ρ η η) (hdiag : ∀ r y s, y ≠ s → J.p r y s = 0) (hinv : J.I_RS = 0) :
    J.I_RY = 0 := by
  have hceil := forbidden_proxy_capacity_ceiling J 0 (le_of_eq hinv)
  rw [H_Y_given_S_eq_zero_of_diagonal J hdiag] at hceil
  have := J.I_RY_nonneg
  linarith

/-! ## Non-vacuity witnesses

Three explicit finite joint laws on `Bool × Bool × Bool`, with all information quantities
of the claims computed exactly. -/

section Witnesses

/-- Witness law 1: `R`, `Y`, `S` are all equal to one fair bit. -/
noncomputable def diagLaw : JointLaw Bool Bool Bool where
  p r y s := if r = y ∧ y = s then 1 / 2 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp; norm_num

/-- Witness law 2: `Y = S` is a fair bit and `R` is an independent fair bit. -/
noncomputable def indepRLaw : JointLaw Bool Bool Bool where
  p _ y s := if y = s then 1 / 4 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp; norm_num

/-- Witness law 3: `R`, `Y`, `S` are three independent fair bits. -/
noncomputable def uniformLaw : JointLaw Bool Bool Bool where
  p _ _ _ := 1 / 8
  nonneg := by intro r y s; norm_num
  total := by norm_num [Fintype.sum_bool]

/-- Every information quantity of the diagonal witness law. -/
theorem diagLaw_values :
    diagLaw.I_RY = 1 ∧ diagLaw.I_RS = 1 ∧ diagLaw.I_RY_given_S = 0 ∧
      diagLaw.I_RS_given_Y = 0 ∧ diagLaw.H_Y_given_S = 0 ∧ diagLaw.H_Y_given_RS = 0 := by
  have hR : diagLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : diagLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : diagLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : diagLaw.H_RY = 1 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRS : diagLaw.H_RS = 1 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hYS : diagLaw.H_YS = 1 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRYS : diagLaw.H_RYS = 1 := by
    simp only [JointLaw.H_RYS_eq_sum, diagLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩
  · rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num
  · rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num
  · rw [JointLaw.I_RY_given_S_eq, hRS, hYS, hRYS, hS]; norm_num
  · rw [JointLaw.I_RS_given_Y_eq, hRY, hYS, hRYS, hY]; norm_num
  · rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num
  · rw [JointLaw.H_Y_given_RS_eq, hRYS, hRS]; norm_num

/-- Every information quantity of the independent-`R`, `Y = S` witness law. -/
theorem indepRLaw_values :
    indepRLaw.H_R = 1 ∧ indepRLaw.I_RY = 0 ∧ indepRLaw.I_RS = 0 ∧
      indepRLaw.H_Y_given_S = 0 := by
  have hR : indepRLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : indepRLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : indepRLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : indepRLaw.H_RY = 2 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRS : indepRLaw.H_RS = 2 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hYS : indepRLaw.H_YS = 1 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, indepRLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  exact ⟨hR, by rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num,
    by rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num,
    by rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num⟩

/-- Every information quantity of the three-independent-bits witness law. -/
theorem uniformLaw_values :
    uniformLaw.I_RY = 0 ∧ uniformLaw.I_RS = 0 ∧ uniformLaw.H_Y_given_S = 1 ∧
      uniformLaw.H_Y_given_RS = 1 ∧ uniformLaw.I_RS_given_Y = 0 := by
  have hR : uniformLaw.H_R = 1 := by
    simp only [JointLaw.H_R, Hs, JointLaw.pR, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hY : uniformLaw.H_Y = 1 := by
    simp only [JointLaw.H_Y, Hs, JointLaw.pY, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hS : uniformLaw.H_S = 1 := by
    simp only [JointLaw.H_S, Hs, JointLaw.pS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_half]
  have hRY : uniformLaw.H_RY = 2 := by
    simp only [JointLaw.H_RY_eq_sum, JointLaw.pRY, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRS : uniformLaw.H_RS = 2 := by
    simp only [JointLaw.H_RS_eq_sum, JointLaw.pRS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hYS : uniformLaw.H_YS = 2 := by
    simp only [JointLaw.H_YS_eq_sum, JointLaw.pYS, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_quarter]
  have hRYS : uniformLaw.H_RYS = 3 := by
    simp only [JointLaw.H_RYS_eq_sum, uniformLaw, Fintype.sum_bool]
    norm_num [logb2_eighth]
  refine ⟨?_, ?_, ?_, ?_, ?_⟩
  · rw [JointLaw.I_RY_eq, hR, hY, hRY]; norm_num
  · rw [JointLaw.I_RS_eq, hR, hS, hRS]; norm_num
  · rw [JointLaw.H_Y_given_S_eq, hYS, hS]; norm_num
  · rw [JointLaw.H_Y_given_RS_eq, hRYS, hRS]; norm_num
  · rw [JointLaw.I_RS_given_Y_eq, hRY, hYS, hRYS, hY]; norm_num

/-- **Non-vacuity for C1.** The chain balance has non-trivial content: for `diagLaw` it reads
`1 = 0 + 1 - 0`, with both sides equal to `1 ≠ 0`. -/
theorem mutual_information_chain_balance_nonvacuity :
    diagLaw.I_RY = 1 ∧ diagLaw.I_RY_given_S + diagLaw.I_RS - diagLaw.I_RS_given_Y = 1 := by
  obtain ⟨h1, h2, h3, h4, -, -⟩ := diagLaw_values
  exact ⟨h1, by rw [h2, h3, h4]; norm_num⟩

/-- **Non-vacuity for C2.** The hypothesis `I(R;S) ≤ δ` is satisfiable with a nonzero
conclusion: for `uniformLaw` and `δ = 0` the ceiling reads `0 = I(R;Y) ≤ H(Y|S) + 0 = 1`. -/
theorem forbidden_proxy_capacity_ceiling_nonvacuity :
    uniformLaw.I_RS ≤ 0 ∧ uniformLaw.I_RY = 0 ∧ uniformLaw.H_Y_given_S = 1 := by
  obtain ⟨h1, h2, h3, -, -⟩ := uniformLaw_values
  exact ⟨le_of_eq h2, h1, h3⟩

/-- **Non-vacuity for C3.** The slack is strictly positive for `uniformLaw`
(`H(Y|S) + I(R;S) - I(R;Y) = 1 > 0`, decomposing as `H(Y|R,S) = 1` plus `I(R;S|Y) = 0`),
and it vanishes for `diagLaw`; so the decomposition is neither always trivial nor
always strict. -/
theorem capacity_ceiling_slack_decomposition_nonvacuity :
    uniformLaw.H_Y_given_S + uniformLaw.I_RS - uniformLaw.I_RY = 1 ∧
      uniformLaw.H_Y_given_RS + uniformLaw.I_RS_given_Y = 1 ∧
      diagLaw.H_Y_given_S + diagLaw.I_RS - diagLaw.I_RY = 0 := by
  obtain ⟨h1, h2, h3, h4, h5⟩ := uniformLaw_values
  obtain ⟨d1, d2, -, -, d5, -⟩ := diagLaw_values
  exact ⟨by rw [h1, h2, h3]; norm_num, by rw [h4, h5]; norm_num,
    by rw [d1, d2, d5]; norm_num⟩

/-- **Non-vacuity for C4.** The hypotheses of C4 are satisfiable by a law whose
representation is *not* degenerate: `indepRLaw` is supported on `Y = S`, has
`I(R;S) = 0`, and its representation carries a full bit of entropy `H(R) = 1`,
yet `I(R;Y) = 0`. -/
theorem perfect_invariance_target_proxy_collapse_nonvacuity :
    (∀ r y s, y ≠ s → indepRLaw.p r y s = 0) ∧ indepRLaw.I_RS = 0 ∧
      indepRLaw.H_R = 1 ∧ indepRLaw.I_RY = 0 := by
  obtain ⟨hR, hRY, hRS, -⟩ := indepRLaw_values
  refine ⟨?_, hRS, hR, hRY⟩
  intro r y s hys
  simp [indepRLaw, hys]

end Witnesses

end Viridis.Run126.PaperFormalization
