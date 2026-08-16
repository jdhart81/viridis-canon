import PaperFormalization.Defs
import PaperFormalization.Algebra
import PaperFormalization.Ensemble

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
    (mobility κ P)⁻¹ = 1 - (κ / (1 + κ)) • P :=
  inv_mobility hP.isIdem hκ

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
  have h1 : (0:ℝ) < 1 + κ := one_add_kappa_pos hκ
  set s : ℝ := sqNorm u with hs
  set q : ℝ := sqNorm (P *ᵥ u) with hq
  have hspos : 0 < s := sqNorm_pos hu
  have hqnn : 0 ≤ q := sqNorm_nonneg _
  have hqs : q ≤ s := sqNorm_proj_le hP u
  have hquad : u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u = s - (κ / (1 + κ)) * q := quadForm_inv hP hκ u
  have hpos : 0 < u ⬝ᵥ (mobility κ P)⁻¹ *ᵥ u := quadForm_inv_pos hP hκ hu
  have hdpos : 0 < s - (κ / (1 + κ)) * q := by rw [← hquad]; exact hpos
  have ha : capturedFraction P u = q / s := rfl
  have hgain : gain κ P u = s / (s - (κ / (1 + κ)) * q) := by
    rw [gain, ← hs, hquad]
  have hden : 1 + κ * (1 - q / s) > 0 := by
    have : κ * (1 - q / s) ≥ 0 := by
      have : q / s ≤ 1 := (div_le_one hspos).2 hqs
      nlinarith
    linarith
  refine ⟨⟨capturedFraction_nonneg P u, capturedFraction_le_one hP u⟩, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · unfold channelCost baselineCost
    rw [hquad, ha, ← hs]
    field_simp
  · rw [hgain, ha, div_eq_div_iff hdpos.ne' hden.ne']
    field_simp
    ring
  · rw [hgain, le_div_iff₀ hdpos]
    nlinarith [div_nonneg hκ h1.le, mul_nonneg (div_nonneg hκ h1.le) hqnn]
  · rw [hgain, div_le_iff₀ hdpos]
    have hk : κ / (1 + κ) * (1 + κ) = κ := by field_simp
    nlinarith [mul_nonneg hκ (sub_nonneg.2 hqs)]
  · intro hPu
    have hqs' : q = s := by rw [hq, hPu, ← hs]
    have he : s - κ / (1 + κ) * s = s / (1 + κ) := by
      field_simp
      ring
    rw [hgain, hqs', he]
    field_simp
  · intro hPu
    have hq0 : q = 0 := by rw [hq, hPu]; simp [sqNorm, dotProduct]
    rw [hgain, hq0]
    simp
    exact hspos.ne'

/-! ## C3 — `rank_deficient_unit_gain` (Theorem 2) -/

/-- **C3.** If `rank P = r < m`, then there is a nonzero unit displacement in `ker P`,
whose captured fraction is `0` and whose gain is exactly `1`. -/
theorem rank_deficient_unit_gain {P : Matrix (Fin m) (Fin m) ℝ} (hP : IsOrthProjector P)
    {κ : ℝ} (hκ : 0 ≤ κ) {r : ℕ} (hrank : P.rank = r) (hr : r < m) :
    ∃ v : Fin m → ℝ, v ≠ 0 ∧ sqNorm v = 1 ∧ P *ᵥ v = 0 ∧
      capturedFraction P v = 0 ∧ gain κ P v = 1 := by
  obtain ⟨v, hv1, hv0⟩ := exists_unit_mem_ker (P := P) (by omega)
  have hvne : v ≠ 0 := by
    intro h
    rw [h] at hv1
    simp [sqNorm, dotProduct] at hv1
  refine ⟨v, hvne, hv1, hv0, ?_, ?_⟩
  · simp [capturedFraction, hv0, sqNorm, dotProduct]
  · have := directional_gain_bounds hP hκ hvne 1
    exact this.2.2.2.2.2.2 hv0

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
  have h1 : (0:ℝ) < 1 + κ := one_add_kappa_pos hκ
  constructor
  · intro u τ hτ hbud
    unfold channelCost at hbud
    unfold deadlineBound
    rw [div_le_iff₀ hτ] at hbud
    rw [div_le_iff₀ hB]
    linarith
  constructor
  · obtain ⟨v, hv1, hv0⟩ := exists_unit_mem_ker (P := P) (by omega)
    refine ⟨v, hv1, ?_⟩
    unfold deadlineBound
    rw [quadForm_inv hP hκ, hv1, hv0]
    simp [sqNorm, dotProduct]
  · rintro t ⟨u, hu1, rfl⟩
    unfold deadlineBound
    rw [quadForm_inv hP hκ, hu1]
    have hqnn : 0 ≤ sqNorm (P *ᵥ u) := sqNorm_nonneg _
    have hk : 0 ≤ κ / (1 + κ) := div_nonneg hκ h1.le
    gcongr
    nlinarith [mul_nonneg hk hqnn]

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
  classical
  have h1 : (0:ℝ) < 1 + κ := one_add_kappa_pos hκ
  have hk0 : 0 ≤ κ / (1 + κ) := div_nonneg hκ h1.le
  set E : Matrix (Fin m) (Fin m) ℝ := topIndicator m r with hE
  set Q : Matrix (Fin m) (Fin m) ℝ := U * E * Uᵀ with hQdef
  have hQ : IsOrthProjector Q :=
    isOrthProjector_conj hU (topIndicator_symm m r) (topIndicator_idem m r)
  -- rank of `Q`
  have htrQ : Matrix.trace Q = (r : ℝ) := by
    rw [hQdef, trace_conj hU, hE, trace_topIndicator hr]
  have hQrank : Q.rank = r := by
    have := trace_eq_rank_of_idem hQ.isIdem
    rw [htrQ] at this
    exact_mod_cast this.symm
  -- conjugation identity
  have hconjQ : Uᵀ * Q * U = E := by
    have h2 := mul_transpose_eq_one hU
    calc Uᵀ * (U * E * Uᵀ) * U = (Uᵀ * U) * E * (Uᵀ * U) := by
          simp [Matrix.mul_assoc]
      _ = E := by rw [hU]; simp
  -- captured mass of `Q`
  have htrQC : Matrix.trace (Q * C) = ∑ i ∈ Finset.univ.filter (fun i : Fin m => (i : ℕ) < r),
      lam i := by
    rw [hC, trace_mul_conj, hconjQ, trace_mul_diagonal]
    have hpt : ∀ i : Fin m, E i i * lam i = if (i : ℕ) < r then lam i else 0 := by
      intro i
      rw [hE, topIndicator, Matrix.diagonal_apply_eq]
      by_cases h : (i : ℕ) < r <;> simp [h]
    rw [Finset.sum_congr rfl (fun i _ => hpt i), Finset.sum_ite, Finset.sum_const_zero,
      add_zero]
  refine ⟨hQ, hQrank, fun P hP => meanCostTau_eq hP.isIdem hκ C, htrQC, ?_⟩
  intro P hP hPrank
  -- the Ky Fan bound
  have hcap : Matrix.trace (P * C) ≤ Matrix.trace (Q * C) := by
    set W : Matrix (Fin m) (Fin m) ℝ := Uᵀ * P * U with hW
    have hWproj : IsOrthProjector W := isOrthProjector_conj' hU hP
    have hdiag : ∀ i, 0 ≤ W i i ∧ W i i ≤ 1 :=
      fun i => diag_mem_Icc_of_symm_idem hWproj.isSymm hWproj.isIdem i
    have hsum : ∑ i, W i i = (r : ℝ) := by
      have h3 : Matrix.trace W = Matrix.trace P := by rw [hW, trace_conj' hU]
      have h4 := trace_eq_rank_of_idem hP.isIdem
      have : Matrix.trace W = (r : ℝ) := by rw [h3, h4, hPrank]
      simpa [Matrix.trace, Matrix.diag] using this
    have hPC : Matrix.trace (P * C) = ∑ i, lam i * W i i := by
      rw [hC, trace_mul_conj, ← hW, trace_mul_diagonal]
      exact Finset.sum_congr rfl (fun i _ => mul_comm _ _)
    rw [hPC, htrQC]
    exact sum_le_top_sum hr hlam (fun i => (hdiag i).1) (fun i => (hdiag i).2) hsum
  refine ⟨hcap, ?_⟩
  rw [meanCostTau_eq hQ.isIdem hκ C, meanCostTau_eq hP.isIdem hκ C]
  have := mul_le_mul_of_nonneg_left hcap hk0
  linarith

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
  have hm0 : (m : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hm.ne'
  have htrP : Matrix.trace P = (r : ℝ) := by
    rw [trace_eq_rank_of_idem hP.isIdem, hPrank]
  have hcap : Matrix.trace (P * ((m : ℝ)⁻¹ • (1 : Matrix (Fin m) (Fin m) ℝ)))
      = (r : ℝ) / m := by
    rw [Matrix.mul_smul, Matrix.mul_one, Matrix.trace_smul, smul_eq_mul, htrP]
    field_simp
  refine ⟨hcap, ?_⟩
  rw [meanCostTau_eq hP.isIdem hκ, hcap, Matrix.trace_smul, smul_eq_mul, Matrix.trace_one]
  field_simp
  simp

end Viridis.Run125.PaperFormalization
