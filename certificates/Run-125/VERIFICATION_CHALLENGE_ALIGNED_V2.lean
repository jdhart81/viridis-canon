/- Engine-3 immutable source unit: Defs.lean -/
import Mathlib.Analysis.Matrix.Spectrum
import Mathlib.LinearAlgebra.Matrix.NonsingularInverse
import Mathlib.Data.Fin.Tuple.Sort
import Mathlib.Analysis.InnerProductSpace.PiL2
import Mathlib.Tactic

/-!
# Run-125 "Symbiotic Bandwidth Bound" — definitions

This file fixes the formal counterparts of the model of the sealed paper
(`SEALED_paper.tex`, Section "Model and assumptions").

Everything happens in `ℝ^m`, represented as `Fin m → ℝ`, with matrices
`Matrix (Fin m) (Fin m) ℝ`.  The Euclidean structure is the standard dot
product; `sqNorm_eq_euclideanNorm_sq` below certifies that our `sqNorm`
really is the squared Euclidean norm `‖·‖²`.
-/

namespace Viridis.Run125.PaperFormalization

open Matrix

variable {m : ℕ}

/-- `sqNorm u = ‖u‖²`, written as a dot product (see `sqNorm_eq_euclideanNorm_sq`). -/
noncomputable def sqNorm (u : Fin m → ℝ) : ℝ := u ⬝ᵥ u

/-- `P` is an orthogonal projector: `P = Pᵀ = P²` (paper Eq. 2). -/
structure IsOrthProjector (P : Matrix (Fin m) (Fin m) ℝ) : Prop where
  /-- `P` is symmetric. -/
  isSymm : Pᵀ = P
  /-- `P` is idempotent. -/
  isIdem : P * P = P

/-- The shared-channel mobility `M_P = I + κ P` (paper Eq. 2). -/
def mobility (κ : ℝ) (P : Matrix (Fin m) (Fin m) ℝ) : Matrix (Fin m) (Fin m) ℝ :=
  1 + κ • P

/-- The baseline (independent-mobility) dissipation `Σ₀(u,τ) = ‖u‖²/τ` (paper Eq. 1). -/
noncomputable def baselineCost (u : Fin m → ℝ) (τ : ℝ) : ℝ := sqNorm u / τ

/-- The coupled dissipation `Σ_P(u,τ) = uᵀ M_P⁻¹ u / τ` (paper Eq. 3). -/
noncomputable def channelCost (κ : ℝ) (P : Matrix (Fin m) (Fin m) ℝ) (u : Fin m → ℝ) (τ : ℝ) : ℝ :=
  (u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u) / τ

/-- The captured fraction `a(u;P) = ‖Pu‖²/‖u‖²` (paper, Theorem 1). -/
noncomputable def capturedFraction (P : Matrix (Fin m) (Fin m) ℝ) (u : Fin m → ℝ) : ℝ :=
  sqNorm (P *ᵥ u) / sqNorm u

/-- The directional gain `G(u;P) = Σ₀/Σ_P` (paper Eq. 6); it does not depend on `τ`,
see `gain_eq_cost_ratio`. -/
noncomputable def gain (κ : ℝ) (P : Matrix (Fin m) (Fin m) ℝ) (u : Fin m → ℝ) : ℝ :=
  sqNorm u / (u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u)

/-- The mean cost `𝔼[Σ_P] τ = tr (M_P⁻¹ C)` for a task ensemble with second moment `C`
(paper Eq. 8, left-hand side); `mean_quadratic_eq_trace` certifies that this trace really
is the ensemble average of `uᵀ M_P⁻¹ u`. -/
noncomputable def meanCostTau (κ : ℝ) (P C : Matrix (Fin m) (Fin m) ℝ) : ℝ :=
  Matrix.trace ((mobility κ P)⁻¹ * C)

/-- The deadline lower bound of paper Eq. 7: `uᵀ (I+κP)⁻¹ u / B`. -/
noncomputable def deadlineBound (κ : ℝ) (P : Matrix (Fin m) (Fin m) ℝ) (B : ℝ) (u : Fin m → ℝ) : ℝ :=
  (u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u) / B

/-! ### Faithfulness bridges -/

/-- `sqNorm` is the squared Euclidean norm. -/
theorem sqNorm_eq_euclideanNorm_sq (u : Fin m → ℝ) :
    sqNorm u = ‖(WithLp.toLp 2 u : EuclideanSpace ℝ (Fin m))‖ ^ 2 := by
  rw [EuclideanSpace.norm_eq, Real.sq_sqrt (by positivity)]
  simp [sqNorm, dotProduct, sq_abs, ← pow_two]

theorem sqNorm_nonneg (u : Fin m → ℝ) : 0 ≤ sqNorm u := by
  simpa [sqNorm, dotProduct] using
    Finset.sum_nonneg (fun i (_ : i ∈ Finset.univ) => mul_self_nonneg (u i))

theorem sqNorm_pos {u : Fin m → ℝ} (hu : u ≠ 0) : 0 < sqNorm u := by
  rcases Function.ne_iff.mp hu with ⟨i, hi⟩
  simp only [sqNorm, dotProduct]
  exact Finset.sum_pos' (fun j _ => mul_self_nonneg _)
    ⟨i, Finset.mem_univ i, mul_self_pos.mpr (by simpa using hi)⟩

/-- For a finite task ensemble with weights `w`, the average of the quadratic cost
`uᵀ A u` is `tr (A C)` with `C = 𝔼[u uᵀ]` (paper Eq. 4).  This justifies the definition
`meanCostTau`. -/
theorem mean_quadratic_eq_trace {ι : Type*} [Fintype ι] (w : ι → ℝ) (u : ι → Fin m → ℝ)
    (A : Matrix (Fin m) (Fin m) ℝ) :
    ∑ k, w k * ((u k) ⬝ᵥ A *ᵥ (u k))
      = Matrix.trace (A * ∑ k, w k • Matrix.vecMulVec (u k) (u k)) := by
  simp only [Matrix.mul_sum, Matrix.trace_sum, Matrix.mul_smul, Matrix.trace_smul,
    smul_eq_mul]
  refine Finset.sum_congr rfl (fun k _ => ?_)
  congr 1
  simp only [Matrix.trace, Matrix.diag, Matrix.mul_apply, Matrix.vecMulVec_apply,
    dotProduct, Matrix.mulVec, Finset.mul_sum]
  exact Finset.sum_congr rfl (fun i _ => Finset.sum_congr rfl (fun j _ => by ring))

/-- The gain is the cost ratio `Σ₀/Σ_P` for every positive duration `τ`. -/
theorem gain_eq_cost_ratio (κ : ℝ) (P : Matrix (Fin m) (Fin m) ℝ) (u : Fin m → ℝ)
    {τ : ℝ} (hτ : τ ≠ 0) :
    gain κ P u = baselineCost u τ / channelCost κ P u τ := by
  unfold gain baselineCost channelCost
  rw [div_div_div_cancel_right₀]
  exact hτ

end Viridis.Run125.PaperFormalization

/- Engine-3 immutable source unit: Algebra.lean -/

/-!
# Auxiliary algebra for the Run-125 formalization

Projector algebra, the exact inverse of `I + κ P`, the quadratic form of that inverse,
the identity `trace P = rank P` for idempotent matrices, existence of unit kernel
vectors in the rank-deficient case, and the combinatorial core of the Ky Fan bound.
-/

namespace Viridis.Run125.PaperFormalization

open Matrix

variable {m : ℕ}

section Projector

variable {P : Matrix (Fin m) (Fin m) ℝ} {κ : ℝ}

theorem one_add_kappa_pos (hκ : 0 ≤ κ) : (0:ℝ) < 1 + κ := by linarith

theorem one_add_kappa_ne_zero (hκ : 0 ≤ κ) : (1:ℝ) + κ ≠ 0 := (one_add_kappa_pos hκ).ne'

theorem sqNorm_smul (c : ℝ) (v : Fin m → ℝ) : sqNorm (c • v) = c ^ 2 * sqNorm v := by
  simp [sqNorm, dotProduct, Finset.mul_sum]
  exact Finset.sum_congr rfl (fun i _ => by ring)

/-- The candidate inverse of `I + κP` is a right inverse. -/
theorem mobility_mul_inv_candidate (hPP : P * P = P) (hκ : 0 ≤ κ) :
    mobility κ P * (1 - (κ / (1 + κ)) • P) = 1 := by
  have h1 : (1:ℝ) + κ ≠ 0 := one_add_kappa_ne_zero hκ
  unfold mobility
  simp only [Matrix.mul_sub, Matrix.add_mul, Matrix.mul_smul, Matrix.smul_mul, mul_one,
    one_mul, hPP]
  match_scalars
  · field_simp
  · field_simp
    ring

/-- The exact inverse of the shared-channel mobility (paper Eq. 5). -/
theorem inv_mobility (hPP : P * P = P) (hκ : 0 ≤ κ) :
    (mobility κ P)⁻¹ = 1 - (κ / (1 + κ)) • P :=
  Matrix.inv_eq_right_inv (mobility_mul_inv_candidate hPP hκ)

/-- For an orthogonal projector, `uᵀPu = ‖Pu‖²`. -/
theorem proj_quadratic (hP : IsOrthProjector P) (u : Fin m → ℝ) :
    u ⬝ᵥ P *ᵥ u = sqNorm (P *ᵥ u) := by
  symm
  rw [sqNorm, Matrix.dotProduct_mulVec, ← Matrix.mulVec_transpose, Matrix.mulVec_mulVec,
    hP.isSymm, hP.isIdem, dotProduct_comm]

/-- Pythagoras for an orthogonal projector: `‖u‖² = ‖Pu‖² + ‖u-Pu‖²`. -/
theorem sqNorm_split (hP : IsOrthProjector P) (u : Fin m → ℝ) :
    sqNorm u = sqNorm (P *ᵥ u) + sqNorm (u - P *ᵥ u) := by
  have h := proj_quadratic hP u
  have hcomm : (P *ᵥ u) ⬝ᵥ u = u ⬝ᵥ (P *ᵥ u) := dotProduct_comm _ _
  simp only [sqNorm, dotProduct_sub, sub_dotProduct] at *
  rw [h] at *
  linarith [hcomm]

theorem sqNorm_proj_le (hP : IsOrthProjector P) (u : Fin m → ℝ) :
    sqNorm (P *ᵥ u) ≤ sqNorm u := by
  have := sqNorm_split hP u
  have := sqNorm_nonneg (u - P *ᵥ u)
  linarith

/-- The captured fraction lies in `[0,1]`. -/
theorem capturedFraction_nonneg (P : Matrix (Fin m) (Fin m) ℝ) (u : Fin m → ℝ) :
    0 ≤ capturedFraction P u :=
  div_nonneg (sqNorm_nonneg _) (sqNorm_nonneg _)

theorem capturedFraction_le_one (hP : IsOrthProjector P) (u : Fin m → ℝ) :
    capturedFraction P u ≤ 1 := by
  rcases eq_or_ne u 0 with rfl | hu
  · simp [capturedFraction, sqNorm, dotProduct]
  · exact (div_le_one (sqNorm_pos hu)).2 (sqNorm_proj_le hP u)

/-- The quadratic form of the inverse mobility. -/
theorem quadForm_inv (hP : IsOrthProjector P) (hκ : 0 ≤ κ) (u : Fin m → ℝ) :
    u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u = sqNorm u - (κ / (1 + κ)) * sqNorm (P *ᵥ u) := by
  rw [inv_mobility hP.isIdem hκ]
  rw [Matrix.sub_mulVec, Matrix.one_mulVec, dotProduct_sub, Matrix.smul_mulVec,
    dotProduct_smul, proj_quadratic hP]
  rfl

theorem quadForm_inv_pos (hP : IsOrthProjector P) (hκ : 0 ≤ κ) {u : Fin m → ℝ} (hu : u ≠ 0) :
    0 < u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u := by
  have h1 : (0:ℝ) < 1 + κ := one_add_kappa_pos hκ
  have hup : 0 < sqNorm u := sqNorm_pos hu
  have hle : sqNorm (P *ᵥ u) ≤ sqNorm u := sqNorm_proj_le hP u
  have hk : κ / (1 + κ) < 1 := by
    rw [div_lt_one h1]; linarith
  have hk0 : 0 ≤ κ / (1 + κ) := div_nonneg hκ h1.le
  rw [quadForm_inv hP hκ]
  nlinarith [sqNorm_nonneg (P *ᵥ u)]

end Projector

section TraceRank

/-- For an idempotent real matrix, the trace equals the rank. -/
theorem trace_eq_rank_of_idem {P : Matrix (Fin m) (Fin m) ℝ} (hPP : P * P = P) :
    P.trace = (P.rank : ℝ) := by
  have hidem : IsIdempotentElem P.mulVecLin := by
    unfold IsIdempotentElem
    rw [show P.mulVecLin * P.mulVecLin = (P * P).mulVecLin from (Matrix.mulVecLin_mul P P).symm,
      hPP]
  have h2 := ((LinearMap.isProj_range_iff_isIdempotentElem P.mulVecLin).mpr hidem).trace
  have h3 : P.rank = Module.finrank ℝ (LinearMap.range P.mulVecLin) := rfl
  rw [h3, ← h2, ← Matrix.trace_toLin'_eq P]
  rfl

/-- A rank-deficient matrix kills a unit vector. -/
theorem exists_unit_mem_ker {P : Matrix (Fin m) (Fin m) ℝ} (hr : P.rank < m) :
    ∃ v : Fin m → ℝ, sqNorm v = 1 ∧ P *ᵥ v = 0 := by
  classical
  have hrn := LinearMap.finrank_range_add_finrank_ker P.mulVecLin
  have hdim : Module.finrank ℝ (Fin m → ℝ) = m := by simp
  have hrank : P.rank = Module.finrank ℝ (LinearMap.range P.mulVecLin) := rfl
  have hker : 0 < Module.finrank ℝ (LinearMap.ker P.mulVecLin) := by omega
  have hne : LinearMap.ker P.mulVecLin ≠ ⊥ := by
    intro h
    rw [h] at hker
    simp at hker
  obtain ⟨w, hw, hw0⟩ := Submodule.exists_mem_ne_zero_of_ne_bot hne
  have hwP : P *ᵥ w = 0 := hw
  have hpos : 0 < sqNorm w := sqNorm_pos hw0
  refine ⟨(Real.sqrt (sqNorm w))⁻¹ • w, ?_, ?_⟩
  · rw [sqNorm_smul]
    rw [inv_pow, Real.sq_sqrt hpos.le]
    field_simp
  · rw [Matrix.mulVec_smul, hwP, smul_zero]

end TraceRank

section KyFan

/-- The combinatorial core of the Ky Fan maximum principle: if `lam` is antitone and the
weights `p` lie in `[0,1]` with total mass `r`, then `∑ lam i * p i ≤ ∑_{i < r} lam i`. -/
theorem sum_le_top_sum {lam p : Fin m → ℝ} {r : ℕ} (hr : r ≤ m) (hlam : Antitone lam)
    (hp0 : ∀ i, 0 ≤ p i) (hp1 : ∀ i, p i ≤ 1) (hsum : ∑ i, p i = r) :
    ∑ i, lam i * p i ≤ ∑ i ∈ Finset.univ.filter (fun i : Fin m => (i : ℕ) < r), lam i := by
  classical
  rcases eq_or_lt_of_le hr with heq | hrm
  · -- `r = m`: the mass constraint forces `p ≡ 1`
    have h0 : ∑ i : Fin m, (1 - p i) = 0 := by
      rw [Finset.sum_sub_distrib, hsum, heq]
      simp
    have hall : ∀ i : Fin m, p i = 1 := by
      intro i
      have := (Finset.sum_eq_zero_iff_of_nonneg
        (fun j (_ : j ∈ Finset.univ) => by linarith [hp1 j])).1 h0 i (Finset.mem_univ i)
      linarith
    have hfil : (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r)) = Finset.univ := by
      ext i
      simp only [Finset.mem_filter, Finset.mem_univ, true_and, iff_true]
      have := i.isLt
      omega
    rw [hfil]
    exact le_of_eq (Finset.sum_congr rfl (fun i _ => by rw [hall i, mul_one]))
  · -- `r < m`: use the threshold `t = lam ⟨r, _⟩`
    set t : ℝ := lam ⟨r, hrm⟩ with ht
    have hsplit : ∀ i : Fin m, lam i * p i - (if (i : ℕ) < r then lam i else 0)
        ≤ t * (p i - (if (i : ℕ) < r then 1 else 0)) := by
      intro i
      by_cases h : (i : ℕ) < r
      · simp only [h, if_true]
        have hli : t ≤ lam i := hlam (by exact_mod_cast h.le)
        nlinarith [hp1 i, hp0 i]
      · simp only [h, if_false]
        have hli : lam i ≤ t := hlam (by
          simp only [Fin.le_def]
          omega)
        nlinarith [hp0 i]
    have hsum' : ∑ i, (lam i * p i - (if (i:ℕ) < r then lam i else 0))
        ≤ ∑ i, t * (p i - (if (i:ℕ) < r then 1 else 0)) :=
      Finset.sum_le_sum (fun i _ => hsplit i)
    have hcard : (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r)).card = r := by
      have hmap : (Finset.univ.filter (fun i : Fin m => (i : ℕ) < r))
          = Finset.map (Fin.castLEEmb hr) Finset.univ := by
        ext i
        simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_map]
        exact ⟨fun h => ⟨⟨i, h⟩, Fin.ext (by simp)⟩, by rintro ⟨j, rfl⟩; simp⟩
      rw [hmap]; simp
    have hR : ∑ i, t * (p i - (if (i:ℕ) < r then 1 else 0)) = 0 := by
      rw [← Finset.mul_sum]
      have : ∑ i : Fin m, (p i - (if (i:ℕ) < r then 1 else 0)) = 0 := by
        rw [Finset.sum_sub_distrib, hsum]
        simp [hcard]
      rw [this, mul_zero]
    have hL : ∑ i, (lam i * p i - (if (i:ℕ) < r then lam i else 0))
        = (∑ i, lam i * p i)
          - ∑ i ∈ Finset.univ.filter (fun i : Fin m => (i : ℕ) < r), lam i := by
      rw [Finset.sum_sub_distrib, Finset.sum_ite, Finset.sum_const_zero, add_zero]
    linarith [hsum'.trans_eq hR, hL]

end KyFan

end Viridis.Run125.PaperFormalization

/- Engine-3 immutable source unit: Ensemble.lean -/

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

/- Engine-3 immutable source unit: PaperFormalization.lean -/

/-!
# Run-125 — "The Symbiotic Bandwidth Bound": Lean formalization of the frozen claims

This module contains the six formal targets named in `STATEMENT_CONTRACT.md`:

* `shared_channel_inverse`     (C1, paper Theorem 1 / Eq. 5)
* `directional_gain_bounds`    (C2, paper Theorem 1 / Eq. 6)
* `rank_deficient_unit_gain`   (C3, paper Theorem 2)
* `worstcase_deadline`         (C4, paper Theorem 2 / Eq. 7)
* `top_subspace_mean_cost`     (C5, paper Theorem 3 / Eq. 8)
* `isotropic_rank_fraction`    (C6, paper Eq. 9)

All model notions (`mobility`, `baselineCost`, `channelCost`, `capturedFraction`, `gain`,
`meanCostTau`, `deadlineBound`, `IsOrthProjector`) are defined in `PaperFormalization/Defs.lean`,
together with the bridges certifying that `sqNorm` is the squared Euclidean norm and that
`meanCostTau` is the ensemble average of the quadratic cost.

Non-vacuity witnesses for every target are in `PaperFormalization/Witnesses.lean`.
Toolchain and mathlib revision are recorded in `TOOLCHAIN.md`.
-/

namespace Viridis.Run125.PaperFormalization

open Matrix

variable {m : ℕ}

/-! ## C1 — `shared_channel_inverse` (Theorem 1, Eq. 5) -/

/-- **C1.** For every orthogonal projector `P` and every `κ ≥ 0`,
`(I + κP)⁻¹ = I - (κ/(1+κ)) P`. -/
theorem shared_channel_inverse {P : Matrix (Fin m) (Fin m) ℝ} (hP : IsOrthProjector P)
    {κ : ℝ} (hκ : 0 ≤ κ) :
    (mobility κ P)⁻¹ = 1 - (κ / (1 + κ)) • P := by
  sorry

/-! ## C2 — `directional_gain_bounds` (Theorem 1, Eq. 6) -/

/-- **C2.** For an orthogonal projector `P`, `κ ≥ 0` and a nonzero displacement `u`:
the captured fraction `a = ‖Pu‖²/‖u‖²` lies in `[0,1]`; the cost ratio is
`Σ_P/Σ₀ = 1 - (κ/(1+κ)) a`; the gain is `G = (1+κ)/(1+κ(1-a))`; `1 ≤ G ≤ 1+κ`;
`G = 1+κ` on `range P` and `G = 1` on `ker P`. -/
theorem directional_gain_bounds {P : Matrix (Fin m) (Fin m) ℝ} (hP : IsOrthProjector P)
    {κ : ℝ} (hκ : 0 ≤ κ) {u : Fin m → ℝ} (hu : u ≠ 0) (τ : ℝ) :
    capturedFraction P u ∈ Set.Icc (0:ℝ) 1 ∧
      channelCost κ P u τ
        = (1 - (κ / (1 + κ)) * capturedFraction P u) * baselineCost u τ ∧
      gain κ P u = (1 + κ) / (1 + κ * (1 - capturedFraction P u)) ∧
      1 ≤ gain κ P u ∧
      gain κ P u ≤ 1 + κ ∧
      (P *ᵥ u = u → gain κ P u = 1 + κ) ∧
      (P *ᵥ u = 0 → gain κ P u = 1) := by
  sorry

/-! ## C3 — `rank_deficient_unit_gain` (Theorem 2) -/

/-- **C3.** If `rank P = r < m`, then there is a nonzero unit displacement in `ker P`,
whose captured fraction is `0` and whose gain is exactly `1`. -/
theorem rank_deficient_unit_gain {P : Matrix (Fin m) (Fin m) ℝ} (hP : IsOrthProjector P)
    {κ : ℝ} (hκ : 0 ≤ κ) {r : ℕ} (hrank : P.rank = r) (hr : r < m) :
    ∃ v : Fin m → ℝ, v ≠ 0 ∧ sqNorm v = 1 ∧ P *ᵥ v = 0 ∧
      capturedFraction P v = 0 ∧ gain κ P v = 1 := by
  sorry

/-! ## C4 — `worstcase_deadline` (Theorem 2, Eq. 7) -/

/-- **C4.** Under the declared dissipation-budget model with budget `B > 0`:
every schedule meeting the budget obeys the deadline bound `τ ≥ uᵀ(I+κP)⁻¹u/B`, and over
unit displacements the greatest such bound is exactly `1/B` — the independent baseline —
whenever `rank P = r < m`.  Hence a rank-deficient shared channel does not improve the
worst-case unit-displacement deadline, for any finite `κ ≥ 0`. -/
theorem worstcase_deadline {P : Matrix (Fin m) (Fin m) ℝ} (hP : IsOrthProjector P)
    {κ : ℝ} (hκ : 0 ≤ κ) {r : ℕ} (hrank : P.rank = r) (hr : r < m) {B : ℝ} (hB : 0 < B) :
    (∀ (u : Fin m → ℝ) (τ : ℝ), 0 < τ → channelCost κ P u τ ≤ B →
        deadlineBound κ P B u ≤ τ) ∧
      IsGreatest {t : ℝ | ∃ u : Fin m → ℝ, sqNorm u = 1 ∧ t = deadlineBound κ P B u}
        (1 / B) := by
  sorry

/-! ## C5 — `top_subspace_mean_cost` (Theorem 3, Eq. 8) -/

/-- **C5.** Let `C = U diag(lam) Uᵀ` be a spectral decomposition of the task second moment
with an orthogonal `U` and *sorted* (antitone) eigenvalues `lam₁ ≥ ⋯ ≥ lamₘ`, and let
`Q = U diag(𝟙_{i<r}) Uᵀ` be the orthogonal projector onto the corresponding top-`r`
eigenspace.  Then `Q` is a rank-`r` orthogonal projector, the mean cost obeys paper Eq. 8,
`Q` captures the mass `∑_{i<r} lam i`, and no rank-`r` orthogonal projector captures more
mass or achieves a smaller expected cost. -/
theorem top_subspace_mean_cost {r : ℕ} (hr : r ≤ m)
    {C U : Matrix (Fin m) (Fin m) ℝ} {lam : Fin m → ℝ}
    (hU : Uᵀ * U = 1) (hlam : Antitone lam) (hC : C = U * Matrix.diagonal lam * Uᵀ)
    {κ : ℝ} (hκ : 0 ≤ κ) :
    IsOrthProjector (U * topIndicator m r * Uᵀ) ∧
      (U * topIndicator m r * Uᵀ).rank = r ∧
      (∀ P : Matrix (Fin m) (Fin m) ℝ, IsOrthProjector P →
        meanCostTau κ P C = Matrix.trace C - (κ / (1 + κ)) * Matrix.trace (P * C)) ∧
      Matrix.trace ((U * topIndicator m r * Uᵀ) * C)
        = ∑ i ∈ Finset.univ.filter (fun i : Fin m => (i : ℕ) < r), lam i ∧
      (∀ P : Matrix (Fin m) (Fin m) ℝ, IsOrthProjector P → P.rank = r →
        Matrix.trace (P * C) ≤ Matrix.trace ((U * topIndicator m r * Uᵀ) * C) ∧
        meanCostTau κ (U * topIndicator m r * Uᵀ) C ≤ meanCostTau κ P C) := by
  sorry

/-- Unconditional corollary of C5: for *every* symmetric task second moment `C` a
minimizing rank-`r` orthogonal projector exists and is the projector onto a top-`r`
eigenspace.  Together with `exists_sorted_spectral_decomposition` this shows that the
spectral hypotheses of `top_subspace_mean_cost` restrict nothing. -/
theorem top_subspace_mean_cost_of_isSymm {r : ℕ} (hr : r ≤ m)
    {C : Matrix (Fin m) (Fin m) ℝ} (hCs : Cᵀ = C) {κ : ℝ} (hκ : 0 ≤ κ) :
    ∃ Q : Matrix (Fin m) (Fin m) ℝ, IsOrthProjector Q ∧ Q.rank = r ∧
      ∀ P : Matrix (Fin m) (Fin m) ℝ, IsOrthProjector P → P.rank = r →
        Matrix.trace (P * C) ≤ Matrix.trace (Q * C) ∧
          meanCostTau κ Q C ≤ meanCostTau κ P C := by
  obtain ⟨U, lam, hU, hlam, hC⟩ := exists_sorted_spectral_decomposition hCs
  obtain ⟨h1, h2, -, -, h5⟩ := top_subspace_mean_cost hr hU hlam hC hκ
  exact ⟨_, h1, h2, h5⟩

/-! ## C6 — `isotropic_rank_fraction` (Eq. 9) -/

/-- **C6.** For an isotropic task second moment `C = I/m`, every rank-`r` orthogonal
projector captures exactly the fraction `r/m`, and the mean cost is
`1 - (κ/(1+κ)) (r/m)` (paper Eq. 9). -/
theorem isotropic_rank_fraction (hm : 0 < m) {r : ℕ} {P : Matrix (Fin m) (Fin m) ℝ}
    (hP : IsOrthProjector P) (hPrank : P.rank = r) {κ : ℝ} (hκ : 0 ≤ κ) :
    Matrix.trace (P * ((m : ℝ)⁻¹ • (1 : Matrix (Fin m) (Fin m) ℝ))) = (r : ℝ) / m ∧
      meanCostTau κ P ((m : ℝ)⁻¹ • (1 : Matrix (Fin m) (Fin m) ℝ))
        = 1 - (κ / (1 + κ)) * ((r : ℝ) / m) := by
  sorry

end Viridis.Run125.PaperFormalization

/- Engine-3 immutable source unit: Witnesses.lean -/

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
