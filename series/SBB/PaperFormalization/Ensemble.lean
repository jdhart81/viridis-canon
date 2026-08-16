import PaperFormalization.Algebra

/-!
# Auxiliary results for the ensemble design claims (C5, C6)
-/

namespace Viridis.Run125.PaperFormalization

open Matrix

variable {m : ℕ}

/-- Paper Eq. 8: the mean cost splits as `tr C - (κ/(1+κ)) tr(PC)`. -/
theorem meanCostTau_eq {P : Matrix (Fin m) (Fin m) ℝ} (hPP : P * P = P) {κ : ℝ} (hκ : 0 ≤ κ)
    (C : Matrix (Fin m) (Fin m) ℝ) :
    meanCostTau κ P C = Matrix.trace C - (κ / (1 + κ)) * Matrix.trace (P * C) := by
  unfold meanCostTau
  rw [inv_mobility hPP hκ, Matrix.sub_mul, Matrix.trace_sub, Matrix.smul_mul,
    Matrix.trace_smul, one_mul, smul_eq_mul]

/-- Diagonal entries of a symmetric idempotent matrix lie in `[0,1]`. -/
theorem diag_mem_Icc_of_symm_idem {W : Matrix (Fin m) (Fin m) ℝ} (hs : Wᵀ = W)
    (hi : W * W = W) (i : Fin m) : 0 ≤ W i i ∧ W i i ≤ 1 := by
  have hsq : W i i = ∑ k, (W i k) ^ 2 := by
    have := congrFun (congrFun hi i) i
    rw [← this]
    simp only [Matrix.mul_apply]
    refine Finset.sum_congr rfl (fun k _ => ?_)
    have : W k i = W i k := by
      have := congrFun (congrFun hs i) k
      simpa [Matrix.transpose_apply] using this
    rw [this]
    ring
  have h0 : 0 ≤ W i i := by
    rw [hsq]
    exact Finset.sum_nonneg (fun k _ => sq_nonneg _)
  have hge : (W i i) ^ 2 ≤ W i i :=
    calc (W i i) ^ 2 ≤ ∑ k, (W i k) ^ 2 :=
          Finset.single_le_sum (f := fun k => (W i k) ^ 2) (fun k _ => sq_nonneg _)
            (Finset.mem_univ i)
      _ = W i i := hsq.symm
  refine ⟨h0, ?_⟩
  nlinarith

section Conjugation

variable {U : Matrix (Fin m) (Fin m) ℝ}

theorem mul_transpose_eq_one (hU : Uᵀ * U = 1) : U * Uᵀ = 1 :=
  mul_eq_one_comm.mpr hU

/-- Conjugation by an orthogonal matrix preserves the orthogonal-projector property. -/
theorem isOrthProjector_conj (hU : Uᵀ * U = 1) {E : Matrix (Fin m) (Fin m) ℝ}
    (hEs : Eᵀ = E) (hEi : E * E = E) : IsOrthProjector (U * E * Uᵀ) where
  isSymm := by
    rw [Matrix.transpose_mul, Matrix.transpose_mul, Matrix.transpose_transpose, hEs,
      Matrix.mul_assoc]
  isIdem := by
    have h := mul_transpose_eq_one hU
    calc U * E * Uᵀ * (U * E * Uᵀ) = U * E * (Uᵀ * U) * E * Uᵀ := by
          simp [Matrix.mul_assoc]
      _ = U * (E * E) * Uᵀ := by rw [hU]; simp [Matrix.mul_assoc]
      _ = U * E * Uᵀ := by rw [hEi]

theorem trace_conj (hU : Uᵀ * U = 1) (A : Matrix (Fin m) (Fin m) ℝ) :
    Matrix.trace (U * A * Uᵀ) = Matrix.trace A := by
  rw [Matrix.trace_mul_comm, ← Matrix.mul_assoc, hU, Matrix.one_mul]

/-- Conjugating by `Uᵀ` : `Uᵀ P U` is an orthogonal projector when `P` is. -/
theorem isOrthProjector_conj' (hU : Uᵀ * U = 1) {P : Matrix (Fin m) (Fin m) ℝ}
    (hP : IsOrthProjector P) : IsOrthProjector (Uᵀ * P * U) := by
  have h := isOrthProjector_conj (U := Uᵀ)
    (by rw [Matrix.transpose_transpose]; exact mul_transpose_eq_one hU) hP.isSymm hP.isIdem
  rwa [Matrix.transpose_transpose] at h

theorem trace_conj' (hU : Uᵀ * U = 1) (A : Matrix (Fin m) (Fin m) ℝ) :
    Matrix.trace (Uᵀ * A * U) = Matrix.trace A := by
  rw [Matrix.trace_mul_comm, ← Matrix.mul_assoc, mul_transpose_eq_one hU, Matrix.one_mul]

/-- Cyclic rearrangement used for `tr (P C)` with `C = U D Uᵀ`. -/
theorem trace_mul_conj (U D P : Matrix (Fin m) (Fin m) ℝ) :
    Matrix.trace (P * (U * D * Uᵀ)) = Matrix.trace ((Uᵀ * P * U) * D) := by
  rw [show P * (U * D * Uᵀ) = (P * U * D) * Uᵀ by simp [Matrix.mul_assoc],
    Matrix.trace_mul_comm]
  congr 1
  simp [Matrix.mul_assoc]

theorem trace_mul_diagonal (W : Matrix (Fin m) (Fin m) ℝ) (d : Fin m → ℝ) :
    Matrix.trace (W * Matrix.diagonal d) = ∑ i, W i i * d i := by
  simp [Matrix.trace, Matrix.diag, Matrix.mul_diagonal]

end Conjugation

/-- The indicator diagonal matrix of the first `r` coordinates. -/
noncomputable def topIndicator (m r : ℕ) : Matrix (Fin m) (Fin m) ℝ :=
  Matrix.diagonal (fun i => if (i : ℕ) < r then (1:ℝ) else 0)

theorem topIndicator_symm (m r : ℕ) : (topIndicator m r)ᵀ = topIndicator m r :=
  Matrix.diagonal_transpose _

theorem topIndicator_idem (m r : ℕ) : topIndicator m r * topIndicator m r = topIndicator m r := by
  unfold topIndicator
  rw [Matrix.diagonal_mul_diagonal]
  congr 1
  funext i
  by_cases h : (i : ℕ) < r <;> simp [h]

theorem trace_topIndicator {r : ℕ} (hr : r ≤ m) :
    Matrix.trace (topIndicator m r) = (r : ℝ) := by
  classical
  unfold topIndicator
  rw [Matrix.trace_diagonal]
  rw [Finset.sum_ite, Finset.sum_const_zero, add_zero, Finset.sum_const, nsmul_eq_mul,
    mul_one]
  have hmap : (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r))
      = Finset.map (Fin.castLEEmb hr) Finset.univ := by
    ext i
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_map]
    exact ⟨fun h => ⟨⟨i, h⟩, Fin.ext (by simp)⟩, by rintro ⟨j, rfl⟩; simp⟩
  rw [hmap]
  simp

/-- Cardinality of the top-`r` index set. -/
theorem card_top_filter {r : ℕ} (hr : r ≤ m) :
    (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r)).card = r := by
  classical
  have hmap : (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r))
      = Finset.map (Fin.castLEEmb hr) Finset.univ := by
    ext i
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_map]
    exact ⟨fun h => ⟨⟨i, h⟩, Fin.ext (by simp)⟩, by rintro ⟨j, rfl⟩; simp⟩
  rw [hmap]
  simp

/-! ### Existence of a sorted spectral decomposition

The hypotheses of C5 (`top_subspace_mean_cost`) ask for an orthogonal `U` and an antitone
`lam` with `C = U diag(lam) Uᵀ`.  The next theorem shows that this data exists for *every*
symmetric `C`, so those hypotheses restrict nothing. -/

/-- Permuting the columns of an orthogonal matrix keeps it orthogonal. -/
theorem submatrix_perm_orthogonal {U : Matrix (Fin m) (Fin m) ℝ} (hU : Uᵀ * U = 1)
    (σ : Equiv.Perm (Fin m)) : (U.submatrix id σ)ᵀ * (U.submatrix id σ) = 1 := by
  ext i j
  have h := congrFun (congrFun hU (σ i)) (σ j)
  simp only [Matrix.mul_apply, Matrix.transpose_apply, Matrix.submatrix_apply, id] at *
  rw [h]
  by_cases hij : i = j
  · subst hij; simp
  · simp [hij]

/-- Permuting eigenvalues and the matching eigenvectors leaves the matrix unchanged. -/
theorem spectral_permute (U : Matrix (Fin m) (Fin m) ℝ) (lam : Fin m → ℝ)
    (σ : Equiv.Perm (Fin m)) :
    U * Matrix.diagonal lam * Uᵀ
      = (U.submatrix id σ) * Matrix.diagonal (lam ∘ σ) * (U.submatrix id σ)ᵀ := by
  ext i j
  rw [Matrix.mul_apply, Matrix.mul_apply]
  simp only [Matrix.mul_diagonal, Matrix.transpose_apply, Matrix.submatrix_apply, id,
    Function.comp_apply]
  exact (Equiv.sum_comp σ (fun l => U i l * lam l * U j l)).symm

/-- Every symmetric real matrix admits a spectral decomposition with an orthogonal matrix
and *sorted* (antitone) eigenvalues. -/
theorem exists_sorted_spectral_decomposition {C : Matrix (Fin m) (Fin m) ℝ} (hCs : Cᵀ = C) :
    ∃ (U : Matrix (Fin m) (Fin m) ℝ) (lam : Fin m → ℝ),
      Uᵀ * U = 1 ∧ Antitone lam ∧ C = U * Matrix.diagonal lam * Uᵀ := by
  have hH : C.IsHermitian := by
    unfold Matrix.IsHermitian
    simpa [Matrix.conjTranspose] using hCs
  set U₀ : Matrix (Fin m) (Fin m) ℝ := (hH.eigenvectorUnitary : Matrix (Fin m) (Fin m) ℝ)
    with hU₀
  have hU₀orth : U₀ᵀ * U₀ = 1 := by
    have h := hH.eigenvectorUnitary.2
    rw [Matrix.mem_unitaryGroup_iff'] at h
    simpa [hU₀, Matrix.star_eq_conjTranspose, Matrix.conjTranspose] using h
  have hspec : C = U₀ * Matrix.diagonal hH.eigenvalues * U₀ᵀ := by
    have h := hH.spectral_theorem
    rw [Unitary.conjStarAlgAut_apply] at h
    simpa [hU₀, Matrix.star_eq_conjTranspose, Matrix.conjTranspose, Function.comp] using h
  set σ : Equiv.Perm (Fin m) := Tuple.sort (fun i => -hH.eigenvalues i) with hσ
  refine ⟨U₀.submatrix id σ, hH.eigenvalues ∘ σ, submatrix_perm_orthogonal hU₀orth σ, ?_, ?_⟩
  · intro i j hij
    have h := Tuple.monotone_sort (fun i => -hH.eigenvalues i) hij
    simp only [Function.comp_apply] at *
    linarith
  · exact hspec.trans (spectral_permute U₀ hH.eigenvalues σ)

end Viridis.Run125.PaperFormalization
