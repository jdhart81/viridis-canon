import PaperFormalization

/-!
# Non-vacuity witnesses

For every formal target of `STATEMENT_CONTRACT.md` this file exhibits explicit data
satisfying *all* hypotheses of the corresponding theorem, together with the concrete
numerical conclusion obtained by instantiating the theorem at that data.  This rules out
vacuous formalizations.

The running witness is the two-dimensional model `m = 2` with the rank-one orthogonal
projector `P₂ = diag(1,0)`, mirroring the paper's own aligned / null-space controls
(`κ = 4.5` gives the aligned gain `5.5` and the orthogonal gain `1.0`).
-/

namespace Viridis.Run125.PaperFormalization

open Matrix

/-- The rank-one orthogonal projector `diag(1,0)` in dimension two. -/
def P₂ : Matrix (Fin 2) (Fin 2) ℝ := !![1, 0; 0, 0]

theorem P₂_isOrthProjector : IsOrthProjector P₂ where
  isSymm := by
    ext i j
    fin_cases i <;> fin_cases j <;> simp [P₂]
  isIdem := by
    ext i j
    fin_cases i <;> fin_cases j <;> simp [P₂, Matrix.mul_apply, Fin.sum_univ_two]

theorem P₂_trace : Matrix.trace P₂ = 1 := by
  simp [P₂, Matrix.trace, Matrix.diag, Fin.sum_univ_two]

theorem P₂_rank : P₂.rank = 1 := by
  have h := trace_eq_rank_of_idem P₂_isOrthProjector.isIdem
  rw [P₂_trace] at h
  exact_mod_cast h.symm

/-! ### C1 — `shared_channel_inverse` is non-vacuous -/

/-- Witness for C1: `(I + 3P₂)⁻¹ = I - (3/4) P₂`. -/
theorem witness_shared_channel_inverse :
    (mobility (3 : ℝ) P₂)⁻¹ = 1 - ((3:ℝ) / 4) • P₂ := by
  have h := shared_channel_inverse P₂_isOrthProjector (κ := (3:ℝ)) (by norm_num)
  norm_num at h ⊢
  exact h

/-! ### C2 — `directional_gain_bounds` is non-vacuous -/

/-- Witness for C2, aligned direction: with `κ = 4.5`, a displacement inside `range P₂`
has gain exactly `5.5`. -/
theorem witness_directional_gain_aligned :
    gain (4.5 : ℝ) P₂ ![1, 0] = 5.5 := by
  have hu : (![1, 0] : Fin 2 → ℝ) ≠ 0 := by
    intro h
    have := congrFun h 0
    norm_num at this
  have hPu : P₂ *ᵥ ![1, 0] = ![1, 0] := by
    ext i
    fin_cases i <;> simp [P₂, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  have h := (directional_gain_bounds P₂_isOrthProjector (κ := (4.5:ℝ)) (by norm_num) hu
    (1:ℝ)).2.2.2.2.2.1 hPu
  rw [h]
  norm_num

/-- Witness for C2, orthogonal direction: with `κ = 4.5`, a displacement in `ker P₂`
has gain exactly `1`. -/
theorem witness_directional_gain_orthogonal :
    gain (4.5 : ℝ) P₂ ![0, 1] = 1 := by
  have hu : (![0, 1] : Fin 2 → ℝ) ≠ 0 := by
    intro h
    have := congrFun h 1
    norm_num at this
  have hPu : P₂ *ᵥ ![0, 1] = 0 := by
    ext i
    fin_cases i <;> simp [P₂, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  exact (directional_gain_bounds P₂_isOrthProjector (κ := (4.5:ℝ)) (by norm_num) hu
    (1:ℝ)).2.2.2.2.2.2 hPu

/-! ### C3 — `rank_deficient_unit_gain` is non-vacuous -/

/-- Witness for C3: the hypotheses `rank P₂ = 1 < 2` are met, so a unit direction of
gain one exists. -/
theorem witness_rank_deficient_unit_gain :
    ∃ v : Fin 2 → ℝ, v ≠ 0 ∧ sqNorm v = 1 ∧ P₂ *ᵥ v = 0 ∧
      capturedFraction P₂ v = 0 ∧ gain (4.5 : ℝ) P₂ v = 1 :=
  rank_deficient_unit_gain P₂_isOrthProjector (κ := (4.5:ℝ)) (by norm_num) P₂_rank
    (by norm_num)

/-! ### C4 — `worstcase_deadline` is non-vacuous -/

/-- Witness for C4: with budget `B = 2`, the worst-case unit-displacement deadline is
exactly `1/2`, the independent baseline. -/
theorem witness_worstcase_deadline :
    IsGreatest {t : ℝ | ∃ u : Fin 2 → ℝ, sqNorm u = 1 ∧ t = deadlineBound (4.5 : ℝ) P₂ 2 u}
      (1 / 2) := by
  have h := worstcase_deadline P₂_isOrthProjector (κ := (4.5:ℝ)) (by norm_num) P₂_rank
    (by norm_num) (B := (2:ℝ)) (by norm_num)
  exact h.2

/-! ### C5 — `top_subspace_mean_cost` is non-vacuous -/

/-- The sorted spectrum `(2,1)` of the two-dimensional witness ensemble. -/
def lam₂ : Fin 2 → ℝ := ![2, 1]

theorem lam₂_antitone : Antitone lam₂ := by
  intro i j hij
  fin_cases i <;> fin_cases j <;> simp_all [lam₂, Fin.le_def]

/-- Witness for C5: with `U = I`, `C = diag(2,1)` and `r = 1`, the top-`1` eigenprojector
`Q = diag(1,0)` is a rank-one orthogonal projector capturing the mass `2`, and no rank-one
orthogonal projector captures more. -/
theorem witness_top_subspace_mean_cost :
    IsOrthProjector ((1 : Matrix (Fin 2) (Fin 2) ℝ) * topIndicator 2 1 * (1 : Matrix (Fin 2) (Fin 2) ℝ)ᵀ) ∧
      ((1 : Matrix (Fin 2) (Fin 2) ℝ) * topIndicator 2 1 * (1 : Matrix (Fin 2) (Fin 2) ℝ)ᵀ).rank = 1 ∧
      Matrix.trace (((1 : Matrix (Fin 2) (Fin 2) ℝ) * topIndicator 2 1 *
        (1 : Matrix (Fin 2) (Fin 2) ℝ)ᵀ) * Matrix.diagonal lam₂) = 2 ∧
      ∀ P : Matrix (Fin 2) (Fin 2) ℝ, IsOrthProjector P → P.rank = 1 →
        Matrix.trace (P * Matrix.diagonal lam₂) ≤ 2 := by
  have hU : ((1 : Matrix (Fin 2) (Fin 2) ℝ))ᵀ * (1 : Matrix (Fin 2) (Fin 2) ℝ) = 1 := by simp
  have hC : (Matrix.diagonal lam₂)
      = (1 : Matrix (Fin 2) (Fin 2) ℝ) * Matrix.diagonal lam₂ *
        (1 : Matrix (Fin 2) (Fin 2) ℝ)ᵀ := by simp
  obtain ⟨h1, h2, -, h4, h5⟩ :=
    top_subspace_mean_cost (m := 2) (r := 1) (by norm_num) hU lam₂_antitone hC
      (κ := (4.5:ℝ)) (by norm_num)
  have hfil : (Finset.univ.filter (fun i : Fin 2 => (i : ℕ) < 1)) = {0} := by decide
  have hmass : ∑ i ∈ Finset.univ.filter (fun i : Fin 2 => (i : ℕ) < 1), lam₂ i = 2 := by
    rw [hfil]
    simp [lam₂]
  refine ⟨h1, h2, ?_, ?_⟩
  · rw [h4, hmass]
  · intro P hP hPrank
    have := (h5 P hP hPrank).1
    rw [h4, hmass] at this
    exact this

/-! ### C6 — `isotropic_rank_fraction` is non-vacuous -/

/-- Witness for C6: in dimension two the rank-one projector `P₂` captures exactly the
isotropic fraction `1/2`. -/
theorem witness_isotropic_rank_fraction :
    Matrix.trace (P₂ * ((2 : ℝ)⁻¹ • (1 : Matrix (Fin 2) (Fin 2) ℝ))) = 1 / 2 ∧
      meanCostTau (4.5 : ℝ) P₂ ((2 : ℝ)⁻¹ • (1 : Matrix (Fin 2) (Fin 2) ℝ))
        = 1 - (4.5 / (1 + 4.5) : ℝ) * (1 / 2) := by
  have h := isotropic_rank_fraction (m := 2) (by norm_num) P₂_isOrthProjector P₂_rank
    (κ := (4.5:ℝ)) (by norm_num)
  norm_num at h ⊢
  exact h

end Viridis.Run125.PaperFormalization
