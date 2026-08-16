import PaperFormalization.Defs

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
