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
  classical
  set M : ℝ := Finset.univ.sup' univ_nonempty_fin z with hMdef
  set m : ℝ := Finset.univ.inf' univ_nonempty_fin z with hmdef
  have hzu : ∀ i, z i ≤ M := fun i => le_span_sup z i
  have hzl : ∀ i, m ≤ z i := fun i => span_inf_le z i
  have hspan : span z = M - m := by
    simp only [span, hMdef, hmdef]
  set c : ℝ := (M + m) / 2 with hcdef
  have key : ∑ i, (w i - v i) * (z i - c) = score w z - score v z := by
    simp only [score, sub_mul, mul_sub, Finset.sum_sub_distrib, ← Finset.sum_mul, hsw, hsv]
    ring
  rw [← key]
  calc |∑ i, (w i - v i) * (z i - c)| ≤ ∑ i, |(w i - v i) * (z i - c)| :=
        Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ i, |w i - v i| * ((M - m) / 2) := by
        refine Finset.sum_le_sum fun i _ => ?_
        rw [abs_mul]
        refine mul_le_mul_of_nonneg_left ?_ (abs_nonneg _)
        rw [abs_le]
        constructor
        · have := hzl i; simp only [hcdef]; linarith
        · have := hzu i; simp only [hcdef]; linarith
    _ = tv w v * span z := by
        rw [← Finset.sum_mul, hspan]
        simp only [tv]
        ring

theorem strict_rank_stability {n : ℕ} [NeZero n]
    (w v z : Fin n → ℝ) (rho : ℝ)
    (hw : ∀ i, 0 ≤ w i) (hv : ∀ i, 0 ≤ v i)
    (hsw : ∑ i, w i = 1) (hsv : ∑ i, v i = 1)
    (hr : tv w v ≤ rho) (hm : rho * span z < score v z) :
    0 < score w z := by
  have hcert := tv_range_certificate w v z hw hv hsw hsv
  have hsp : 0 ≤ span z := span_nonneg z
  have hmono : tv w v * span z ≤ rho * span z :=
    mul_le_mul_of_nonneg_right hr hsp
  have hlb : -(tv w v * span z) ≤ score w z - score v z := by
    have := abs_le.mp hcert
    linarith [this.1]
  linarith

/-! The delivered proof-indexed supremum target is false. In `ℝ` the supremum
of an empty family is `0`, so every weight vector outside the simplex contributes
zero. The right-hand side therefore equals `max (⨆ i, z i) 0`, which differs from
`⨆ i, z i` whenever all coordinates are negative. The next declaration preserves
an explicit counterexample. -/

/-- The delivered `unrestricted_simplex_optimum` is refuted at `n = 1`, `z = ![-1]`. -/
theorem unrestricted_simplex_optimum_counterexample :
    ¬ (∀ (n : ℕ) (_ : NeZero n) (z : Fin n → ℝ),
        (⨆ i, z i) = ⨆ (w : Fin n → ℝ) (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w z) := by
  intro h
  have hz : (fun _ : Fin 1 => (-1 : ℝ)) = ![(-1 : ℝ)] := by
    funext i; fin_cases i; rfl
  have hspec := h 1 inferInstance ![(-1 : ℝ)]
  -- left-hand side
  have hL : (⨆ i, (![(-1 : ℝ)] : Fin 1 → ℝ) i) = -1 := by
    rw [← hz]
    exact ciSup_const
  -- the family appearing on the right-hand side
  set g : (Fin 1 → ℝ) → ℝ :=
    fun w => ⨆ (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w ![(-1 : ℝ)] with hg
  have hle : ∀ w : Fin 1 → ℝ, g w ≤ 0 := by
    intro w
    by_cases hc : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1
    · rw [hg]
      simp only [ciSup_pos hc]
      have hw0 : w 0 = 1 := by
        have := hc.2
        simpa using this
      simp [score, hw0]
    · rw [hg]
      simp only [hc, ciSup_neg, not_false_iff]
      exact le_of_eq Real.sSup_empty
  have hbdd : BddAbove (Set.range g) := ⟨0, by rintro _ ⟨w, rfl⟩; exact hle w⟩
  have hR0 : (0 : ℝ) ≤ ⨆ w : Fin 1 → ℝ, g w := by
    have hnot : ¬ ((∀ i, 0 ≤ (0 : Fin 1 → ℝ) i) ∧ ∑ i, (0 : Fin 1 → ℝ) i = 1) := by
      intro hc
      have := hc.2
      simp at this
    have hg0 : g 0 = 0 := by
      rw [hg]
      simp only [hnot, ciSup_neg, not_false_iff]
      exact Real.sSup_empty
    calc (0 : ℝ) = g 0 := hg0.symm
      _ ≤ ⨆ w : Fin 1 → ℝ, g w := le_ciSup hbdd 0
  rw [hL] at hspec
  rw [hg] at hR0
  rw [← hspec] at hR0
  norm_num at hR0

/-- Unconditional form of the simplex-optimum identity: the right-hand side, read with
Lean's convention `sSup ∅ = 0` for real suprema, computes `max (⨆ i, z i) 0`. -/
theorem unrestricted_simplex_optimum_max {n : ℕ} [NeZero n] (z : Fin n → ℝ) :
    max (⨆ i, z i) 0 = ⨆ (w : Fin n → ℝ) (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w z := by
  classical
  have hA : (⨆ i, z i) = Finset.univ.sup' univ_nonempty_fin z :=
    (Finset.sup'_univ_eq_ciSup z).symm
  set A : ℝ := ⨆ i, z i with hAdef
  have hzA : ∀ i, z i ≤ A := by
    intro i; rw [hA]; exact le_span_sup z i
  set g : (Fin n → ℝ) → ℝ :=
    fun w => ⨆ (_ : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1), score w z with hg
  have hle : ∀ w : Fin n → ℝ, g w ≤ max A 0 := by
    intro w
    by_cases hc : (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1
    · rw [hg]
      simp only [ciSup_pos hc]
      refine le_trans ?_ (le_max_left _ _)
      have : score w z ≤ ∑ i, w i * A := by
        refine Finset.sum_le_sum fun i _ => ?_
        exact mul_le_mul_of_nonneg_left (hzA i) (hc.1 i)
      calc score w z ≤ ∑ i, w i * A := this
        _ = A := by rw [← Finset.sum_mul, hc.2, one_mul]
    · rw [hg]
      simp only [hc, ciSup_neg, not_false_iff]
      rw [Real.sSup_empty]
      exact le_max_right _ _
  have hbdd : BddAbove (Set.range g) := ⟨max A 0, by rintro _ ⟨w, rfl⟩; exact hle w⟩
  refine le_antisymm ?_ (ciSup_le hle)
  refine max_le ?_ ?_
  · -- pick the argmax coordinate and use the corresponding vertex of the simplex
    obtain ⟨i0, -, hi0⟩ := Finset.exists_mem_eq_sup' univ_nonempty_fin z
    have hAi : A = z i0 := by rw [hA, hi0]
    set e : Fin n → ℝ := fun i => if i = i0 then 1 else 0 with hedef
    have hcond : (∀ i, 0 ≤ e i) ∧ ∑ i, e i = 1 := by
      refine ⟨fun i => ?_, ?_⟩
      · simp only [hedef]
        split <;> norm_num
      · simp [hedef]
    have hval : g e = z i0 := by
      rw [hg]
      simp only [ciSup_pos hcond]
      simp [score, hedef, ite_mul]
    calc A = z i0 := hAi
      _ = g e := hval.symm
      _ ≤ ⨆ w : Fin n → ℝ, g w := le_ciSup hbdd _
  · have hnot : ¬ ((∀ i, 0 ≤ (0 : Fin n → ℝ) i) ∧ ∑ i, (0 : Fin n → ℝ) i = 1) := by
      intro hc
      have := hc.2
      simp at this
    have hg0 : g 0 = 0 := by
      rw [hg]
      simp only [hnot, ciSup_neg, not_false_iff]
      exact Real.sSup_empty
    calc (0 : ℝ) = g 0 := hg0.symm
      _ ≤ ⨆ w : Fin n → ℝ, g w := le_ciSup hbdd 0

def SimplexWeights (n : ℕ) :=
  {w : Fin n → ℝ // (∀ i, 0 ≤ w i) ∧ ∑ i, w i = 1}

/-- Corrected formalization of the paper's unrestricted simplex optimum.

The proof-bearing weights are packaged as a subtype, so invalid weight vectors do not
contribute an empty proof-indexed supremum.  This statement is valid even when every
coordinate of `z` is negative. -/
theorem unrestricted_simplex_optimum {n : ℕ} [NeZero n]
    (z : Fin n → ℝ) :
    (⨆ i, z i) = ⨆ (w : SimplexWeights n), score w.1 z := by
  classical
  have hA : (⨆ i, z i) = Finset.univ.sup' univ_nonempty_fin z :=
    (Finset.sup'_univ_eq_ciSup z).symm
  set A : ℝ := ⨆ i, z i with hAdef
  have hzA : ∀ i, z i ≤ A := by
    intro i
    rw [hA]
    exact le_span_sup z i
  have hle : ∀ w : SimplexWeights n, score w.1 z ≤ A := by
    intro w
    have hsum : score w.1 z ≤ ∑ i, w.1 i * A := by
      refine Finset.sum_le_sum fun i _ => ?_
      exact mul_le_mul_of_nonneg_left (hzA i) (w.2.1 i)
    calc
      score w.1 z ≤ ∑ i, w.1 i * A := hsum
      _ = A := by rw [← Finset.sum_mul, w.2.2, one_mul]
  have hbdd : BddAbove (Set.range (fun w : SimplexWeights n => score w.1 z)) :=
    ⟨A, by rintro _ ⟨w, rfl⟩; exact hle w⟩
  apply le_antisymm
  · obtain ⟨i0, -, hi0⟩ := Finset.exists_mem_eq_sup' univ_nonempty_fin z
    let e : SimplexWeights n :=
      ⟨fun i => if i = i0 then 1 else 0, by
        constructor
        · intro i
          by_cases h : i = i0
          · simp [h]
          · simp [h]
        · simp⟩
    letI : Nonempty (SimplexWeights n) := ⟨e⟩
    have hAi : A = z i0 := by rw [hA, hi0]
    calc
      A = z i0 := hAi
      _ = score e.1 z := by simp [score, e]
      _ ≤ ⨆ w : SimplexWeights n, score w.1 z := le_ciSup hbdd e
  · let i0 : Fin n := Classical.arbitrary (Fin n)
    let e : SimplexWeights n :=
      ⟨fun i => if i = i0 then 1 else 0, by
        constructor
        · intro i
          by_cases h : i = i0
          · simp [h]
          · simp [h]
        · simp⟩
    letI : Nonempty (SimplexWeights n) := ⟨e⟩
    exact ciSup_le hle

theorem charter_nonvacuous :
    let w0 : Fin 2 → ℝ := ![0.6, 0.4]
    let w : Fin 2 → ℝ := ![0.3, 0.7]
    let z : Fin 2 → ℝ := ![0, 5]
    tv w w0 = 0.3 ∧ score w z - score w0 z = 1.5 := by
  refine ⟨?_, ?_⟩ <;>
    · simp only [tv, score, Fin.sum_univ_two, Matrix.cons_val_zero, Matrix.cons_val_one]
      norm_num [abs_of_nonneg, abs_of_nonpos]

end Viridis.DScore.WeightCharter
