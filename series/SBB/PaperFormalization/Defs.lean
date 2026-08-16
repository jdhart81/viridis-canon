import Mathlib

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
