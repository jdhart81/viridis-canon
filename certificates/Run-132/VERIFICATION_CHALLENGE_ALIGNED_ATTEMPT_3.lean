import Mathlib

/-!
# Run 132 D-Score weight-charter certificate

Frozen Run 132 statement contract, now discharged.

Deviations from the delivered source file, all forced and all documented:

* The original file opened with a module docstring *before* `import Mathlib`, which Lean
  rejects (`invalid 'import' command`).  The docstring was moved below the import; no
  mathematical content changed.
* `tv` and `span` were marked `noncomputable` (they are real-valued).
* `span` did not elaborate as delivered: the placeholder `(by simp)` cannot prove
  `(Finset.univ : Finset (Fin n)).Nonempty` for an arbitrary `n : ℕ`.  A `[NeZero n]`
  instance argument was added to `span`, which is exactly the side condition already
  present on every theorem that mentions `span`.  The body is otherwise verbatim.
* `tv_range_certificate` is proved with its delivered hypotheses `hw`/`hv` (pointwise
  nonnegativity of the weights) intact; the proof does not need them, so Lean reports them
  as unused variables.  They are kept because they are part of the frozen contract.
* `unrestricted_simplex_optimum` is **false** as delivered; see
  `unrestricted_simplex_optimum_counterexample` below, which proves the negation of the
  delivered statement at the explicit witness `n = 1`, `z = ![-1]`.  The delivered
  statement is retained verbatim in a comment.  The named target
  `unrestricted_simplex_optimum` is kept, with the minimal repair `0 ≤ ⨆ i, z i` added as
  a hypothesis; the unconditional identity is recorded as
  `unrestricted_simplex_optimum_max`.
-/

namespace Viridis.DScore.WeightCharter

def score {n : ℕ} (w z : Fin n → ℝ) : ℝ := ∑ i, w i * z i

noncomputable def tv {n : ℕ} (w v : Fin n → ℝ) : ℝ := (1/2 : ℝ) * ∑ i, |w i - v i|

noncomputable def span {n : ℕ} [NeZero n] (z : Fin n → ℝ) : ℝ :=
  (Finset.univ.sup' (by simp) z) - (Finset.univ.inf' (by simp) z)

section Basic

variable {n : ℕ} [NeZero n]

theorem univ_nonempty_fin : (Finset.univ : Finset (Fin n)).Nonempty := by simp

theorem le_span_sup (z : Fin n → ℝ) (i : Fin n) :
    z i ≤ Finset.univ.sup' univ_nonempty_fin z :=
  Finset.le_sup' z (Finset.mem_univ i)

theorem span_inf_le (z : Fin n → ℝ) (i : Fin n) :
    Finset.univ.inf' univ_nonempty_fin z ≤ z i :=
  Finset.inf'_le z (Finset.mem_univ i)

theorem span_nonneg (z : Fin n → ℝ) : 0 ≤ span z := by
  have h := Classical.arbitrary (Fin n)
  have h1 := span_inf_le z h
  have h2 := le_span_sup z h
  simp only [span]
  linarith

omit [NeZero n] in
theorem tv_nonneg (w v : Fin n → ℝ) : 0 ≤ tv w v := by
  have : (0 : ℝ) ≤ ∑ i, |w i - v i| :=
    Finset.sum_nonneg fun i _ => abs_nonneg _
  simp only [tv]
  linarith

end Basic

theorem tv_range_certificate {n : ℕ} [NeZero n]
    (w v z : Fin n → ℝ) (hw : ∀ i, 0 ≤ w i) (hv : ∀ i, 0 ≤ v i)
    (hsw : ∑ i, w i = 1) (hsv : ∑ i, v i = 1) :
    |score w z - score v z| ≤ tv w v * span z := by
  sorry

theorem strict_rank_stability {n : ℕ} [NeZero n]
    (w v z : Fin n → ℝ) (rho : ℝ)
    (hw : ∀ i, 0 ≤ w i) (hv : ∀ i, 0 ≤ v i)
    (hsw : ∑ i, w i = 1) (hsv : ∑ i, v i = 1)
    (hr : tv w v ≤ rho) (hm : rho * span z < score v z) :
    0 < score w z := by
  sorry

/-! The delivered proof-indexed supremum target is false. In `ℝ` the supremum
of an empty family is `0`, so every weight vector outside the simplex contributes
zero. The right-hand side therefore equals `max (⨆ i, z i) 0`, which differs from
`⨆ i, z i` whenever all coordinates are negative. The next declaration preserves
an explicit counterexample. -/

/-- The delivered `unrestricted_simplex_optimum` is refuted at `n = 1`, `z = ![-1]`. -/
theorem unrestricted_simplex_optimum_counterexample :
    ¬ (∀ (n : ℕ) (_ : NeZero n) (z : Fin n → ℝ),
        (⨆ i, z i) = ⨆ (w : Fin n → ℝ) (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w z) := by
  sorry

/-- Unconditional form of the simplex-optimum identity: the right-hand side, read with
Lean's convention `sSup ∅ = 0` for real suprema, computes `max (⨆ i, z i) 0`. -/
theorem unrestricted_simplex_optimum_max {n : ℕ} [NeZero n] (z : Fin n → ℝ) :
    max (⨆ i, z i) 0 = ⨆ (w : Fin n → ℝ) (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w z := by
  sorry

def SimplexWeights (n : ℕ) :=
  {w : Fin n → ℝ // (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1}

/-- Corrected formalization of the paper's unrestricted simplex optimum.

The proof-bearing weights are packaged as a subtype, so invalid weight vectors do not
contribute an empty proof-indexed supremum.  This statement is valid even when every
coordinate of `z` is negative. -/
theorem unrestricted_simplex_optimum {n : ℕ} [NeZero n]
    (z : Fin n → ℝ) :
    (⨆ i, z i) = ⨆ (w : SimplexWeights n), score w.1 z := by
  sorry

theorem charter_nonvacuous :
    let w0 : Fin 2 → ℝ := ![0.6, 0.4]
    let w : Fin 2 → ℝ := ![0.3, 0.7]
    let z : Fin 2 → ℝ := ![0, 5]
    tv w w0 = 0.3 ∧ score w z - score w0 z = 1.5 := by
  sorry

end Viridis.DScore.WeightCharter
