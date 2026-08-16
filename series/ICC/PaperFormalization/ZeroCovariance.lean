import PaperFormalization.Claims

/-!
# The nonlinear negative control (paper claim C7)

The paper's negative control (Section "Boundary cases and controls", inventory claim C7,
evidence class NUMERIC) states: let `S` be uniform on `{-1, 0, 1}` and `R = S²`.  Then
`Cov(R, S) = 0` by symmetry, but `R` reveals whether `S = 0`, giving
`I(R;S) = H(R) = 0.918296…` bit.

This claim is *not* one of the five frozen formal targets, but it is formalized here as an
exact statement: the covariance vanishes while the mutual information equals
`log₂ 3 - 2/3 = 0.9182958…` bit, which is strictly positive.
-/

namespace Viridis.Run126.PaperFormalization

open Finset

/-- Covariance of real-valued codings `f ∘ R` and `g ∘ S` under a joint law. -/
noncomputable def JointLaw.cov {ρ η σ : Type*} [Fintype ρ] [Fintype η] [Fintype σ]
    (J : JointLaw ρ η σ) (f : ρ → ℝ) (g : σ → ℝ) : ℝ :=
  (∑ r, ∑ s, J.pRS (r, s) * (f r * g s)) - (∑ r, J.pR r * f r) * (∑ s, J.pS s * g s)

/-- The real value coded by the proxy alphabet `Fin 3`: `-1, 0, 1`. -/
noncomputable def sval : Fin 3 → ℝ := fun s => (s : ℝ) - 1

/-- The real value coded by the representation alphabet `Bool`: `1` and `0`. -/
noncomputable def rval : Bool → ℝ := fun b => if b then 1 else 0

/-- The representation `R = S²`, as a map of alphabets. -/
def rmap : Fin 3 → Bool := fun s => if s = 1 then false else true

/-- `rmap` really codes `R = S²`. -/
lemma rval_rmap (s : Fin 3) : rval (rmap s) = (sval s) ^ 2 := by
  fin_cases s <;> norm_num [rval, rmap, sval]

/-- The negative-control law: `S` uniform on `{-1, 0, 1}`, `R = S²`, `Y` trivial. -/
noncomputable def squareLaw : JointLaw Bool Unit (Fin 3) where
  p r _ s := if r = rmap s then 1 / 3 else 0
  nonneg := by intro r y s; split <;> norm_num
  total := by simp [Fin.sum_univ_three, rmap]; norm_num

private lemma logb2_three_pos : 0 < Real.logb 2 (3 : ℝ) :=
  Real.logb_pos (by norm_num) (by norm_num)

private lemma logb2_third : Real.logb 2 (1 / 3 : ℝ) = -Real.logb 2 3 := by
  rw [one_div, Real.logb_inv]

private lemma logb2_two_thirds : Real.logb 2 (2 / 3 : ℝ) = 1 - Real.logb 2 3 := by
  rw [Real.logb_div (by norm_num) (by norm_num), logb2_two]

lemma squareLaw_pS (s : Fin 3) : squareLaw.pS s = 1 / 3 := by
  fin_cases s <;> simp [JointLaw.pS, squareLaw, rmap]

lemma squareLaw_pR_true : squareLaw.pR true = 2 / 3 := by
  simp [JointLaw.pR, squareLaw, rmap]
  rw [Fin.sum_univ_three]
  norm_num [Fin.ext_iff]

lemma squareLaw_pR_false : squareLaw.pR false = 1 / 3 := by
  simp [JointLaw.pR, squareLaw, rmap]

lemma squareLaw_pRS (r : Bool) (s : Fin 3) :
    squareLaw.pRS (r, s) = if r = rmap s then 1 / 3 else 0 := by
  simp [JointLaw.pRS, squareLaw]

lemma squareLaw_H_S : squareLaw.H_S = Real.logb 2 3 := by
  rw [JointLaw.H_S_eq_sum]
  simp only [Fin.sum_univ_three, squareLaw_pS]
  rw [logb2_third]
  ring

lemma squareLaw_H_RS : squareLaw.H_RS = Real.logb 2 3 := by
  rw [JointLaw.H_RS_eq_sum]
  simp only [Fintype.sum_bool, Fin.sum_univ_three, squareLaw_pRS, rmap, Fin.reduceEq, reduceIte,
    Bool.false_eq_true, Bool.true_eq_false, zero_mul, add_zero, zero_add]
  rw [logb2_third]
  ring

lemma squareLaw_H_R : squareLaw.H_R = Real.logb 2 3 - 2 / 3 := by
  rw [JointLaw.H_R_eq_sum]
  simp only [Fintype.sum_bool, squareLaw_pR_true, squareLaw_pR_false]
  rw [logb2_third, logb2_two_thirds]
  ring

/-- **Paper claim C7 (negative control).** For `S` uniform on `{-1,0,1}` and `R = S²`,
the covariance of `R` and `S` vanishes, yet the mutual information is
`I(R;S) = log₂ 3 - 2/3 = 0.9182958…` bit, which is strictly positive.
Hence zero covariance does not certify representation–proxy independence. -/
theorem zero_covariance_does_not_certify_invariance :
    squareLaw.cov rval sval = 0 ∧
      squareLaw.I_RS = Real.logb 2 3 - 2 / 3 ∧ 0 < squareLaw.I_RS := by
  have hI : squareLaw.I_RS = Real.logb 2 3 - 2 / 3 := by
    rw [JointLaw.I_RS_eq, squareLaw_H_R, squareLaw_H_S, squareLaw_H_RS]
    ring
  refine ⟨?_, hI, ?_⟩
  · simp only [JointLaw.cov, Fintype.sum_bool, Fin.sum_univ_three, squareLaw_pRS,
      squareLaw_pR_true, squareLaw_pR_false, squareLaw_pS, rmap, rval, sval]
    norm_num [Fin.ext_iff]
  · rw [hI]
    have h : (2 : ℝ) / 3 < Real.logb 2 3 := by
      have h2 : Real.logb 2 (2 : ℝ) < Real.logb 2 3 :=
        Real.logb_lt_logb (by norm_num) (by norm_num) (by norm_num)
      rw [logb2_two] at h2
      linarith
    linarith

end Viridis.Run126.PaperFormalization
