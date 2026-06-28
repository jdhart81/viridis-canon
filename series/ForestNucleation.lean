/-
===============================================================================
  The Forest Nucleation Theorem (FNT) — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
===============================================================================

CONTEXT (nightly Run 061, forest-nucleation-theorem; [11] Afforestation × 🔥).
  A cluster of planted trees on degraded land is a *nucleus of the forest phase*
  inside the metastable degraded phase.  Classical nucleation theory (CNT) gives
  its free energy as a competition between a favorable bulk (interior) term and
  an unfavorable surface (perimeter) term:

        ΔG(n) = -Δμ · n + a σ · n^(2/3)

  • n   — trees established in the cluster (extensive order parameter; area
          A ∝ n^(2/3)).
  • Δμ  — per-tree driving force (forest gain over degraded state); bulk term.
  • σ   — facilitation deficit / edge mortality excess (ecological "surface
          tension"); surface term.
  • a   — geometric shape factor.

  CNT delivers a critical nucleus n* below which the cluster dissolves and above
  which it grows, a barrier ΔG* = ½ Δμ n*, and — under a fixed seed budget — a
  non-monotonic colonized-area law whose maximum is the dispersal–establishment
  paradox: uniform broadcast covers the least ground.

CLEAN-CORE ENCODING (this file — no `sorry`, axioms ⊆ Mathlib).
  We reparametrize by the cube-root order parameter r := n^(1/3) (so n = r^3 and
  the surface term n^(2/3) = r^2), turning the rpow free energy into a clean
  polynomial  G(r) = -Δμ r^3 + a σ r^2.  The critical radius is
        rStar = 2 a σ / (3 Δμ),     n* = rStar^3.
  All three named nightly targets are then exact, non-vacuous statements:

  1. `critical_nucleus`      — rStar > 0 and is the UNIQUE global maximizer of the
        free energy G over r ≥ 0 (the critical nucleus is the barrier top; below
        it the cluster dissolves, above it interior seed is redundant).
        [factorization: G(rStar) - G(r) = Δμ (r - rStar)^2 (r + rStar/2) ≥ 0]
  2. `barrier_half_identity` — the clean CNT identity  ΔG* = ½ Δμ n*:
        G(rStar) = ½ Δμ rStar^3.
  3. `broadcast_suboptimal`  — sharp-threshold colonized area
        A_col(n) = (S/n) · p(n) · C  with  p(n) = 𝟙[n ≥ n*]  is maximized
        UNIQUELY at n = n*; sub-critical (broadcast) clusters colonize zero area.
        This is the spatial Dispersal–Establishment Paradox.
  4. `FNT_nonvacuous`        — the hypothesis class is inhabited by concrete
        positive (Δμ, a, σ) with a STRICTLY POSITIVE barrier, so 1–2 are not
        vacuous (witness Δμ=1, a=1, σ=3/2 ⇒ rStar=1, n*=1, ΔG*=½).

THE HONEST BOUNDARY (the input, NOT formalized here):
  The CNT free-energy form itself, the Arrhenius nucleation rate
  J = J₀ exp(-ΔG*/T_eco), the ecological-temperature T_eco, the general
  monotone-sigmoid committor p(n), and the tempo-coupled deadline t_dead are the
  ecological/thermodynamic modeling inputs.  This file proves everything
  downstream of the clean polynomial reduction: the critical-point geometry, the
  half-barrier identity, and the sharp-threshold concentration-beats-broadcast
  optimum that the drone-deposition design law depends on.
===============================================================================
-/
import Mathlib

namespace Viridis.Afforestation.ForestNucleation

/-- Critical radius (cube-root order parameter) `rStar = 2 a σ / (3 Δμ)`;
    the critical nucleus is `n* = rStar ^ 3`. -/
noncomputable def rStar (Δμ a σ : ℝ) : ℝ := 2 * a * σ / (3 * Δμ)

/-- CNT free energy in the cube-root order parameter `r` (with `n = r^3`,
    `n^(2/3) = r^2`):  `G(r) = -Δμ r^3 + a σ r^2`. -/
noncomputable def G (Δμ a σ r : ℝ) : ℝ := -Δμ * r ^ 3 + a * σ * r ^ 2

/-- Sharp-threshold establishment indicator: a cluster establishes iff it is at
    least the critical size `n*`. -/
noncomputable def estab (nStar n : ℝ) : ℝ := if nStar ≤ n then 1 else 0

/-- Colonized area for `m = S/n` clusters of size `n`, each established cluster
    expanding (front-driven, nucleus-size-independent) to a fixed area `C`:
    `A_col(n) = (S/n) · p(n) · C`. -/
noncomputable def Acol (nStar S C n : ℝ) : ℝ := S / n * estab nStar n * C

/-
**FNT-1 — the critical nucleus.**
    For positive driving force, shape factor and surface tension, the critical
    radius `rStar = 2aσ/(3Δμ)` is strictly positive and is the UNIQUE global
    maximizer of the nucleation free energy `G` over `r ≥ 0`.  (The critical
    nucleus is the top of the barrier: smaller clusters dissolve, larger ones
    waste interior seed.)
-/
theorem critical_nucleus (Δμ a σ : ℝ) (hΔμ : 0 < Δμ) (ha : 0 < a) (hσ : 0 < σ) :
    0 < rStar Δμ a σ ∧
    (∀ r : ℝ, 0 ≤ r → G Δμ a σ r ≤ G Δμ a σ (rStar Δμ a σ)) ∧
    (∀ r : ℝ, 0 ≤ r → G Δμ a σ r = G Δμ a σ (rStar Δμ a σ) → r = rStar Δμ a σ) := by
  refine' ⟨ _, fun r hr => _, _ ⟩;
  · exact div_pos ( by positivity ) ( by positivity );
  · -- We'll use the algebraic identity $G(rStar) - G(r) = Δμ * (r - rStar)^2 * (r + rStar / 2)$.
    have h_identity : G Δμ a σ (rStar Δμ a σ) - G Δμ a σ r = Δμ * (r - rStar Δμ a σ)^2 * (r + rStar Δμ a σ / 2) := by
      unfold G rStar; field_simp; ring
    exact le_of_sub_nonneg ( h_identity.symm ▸ mul_nonneg ( mul_nonneg hΔμ.le ( sq_nonneg _ ) ) ( add_nonneg hr ( div_nonneg ( show 0 ≤ rStar Δμ a σ by exact div_nonneg ( mul_nonneg ( mul_nonneg zero_le_two ha.le ) hσ.le ) ( mul_nonneg zero_le_three hΔμ.le ) ) zero_le_two ) ) );
  · intro r hr h;
    -- Using the algebraic identity, we have G(rStar) - G(r) = Δμ*(r - rStar)^2*(r + rStar/2).
    have h_identity : G Δμ a σ (rStar Δμ a σ) - G Δμ a σ r = Δμ * (r - rStar Δμ a σ) ^ 2 * (r + rStar Δμ a σ / 2) := by
      unfold G rStar; field_simp; ring
    exact eq_of_sub_eq_zero ( by contrapose! h_identity; exact ne_of_lt ( by exact lt_of_le_of_lt ( by linarith ) ( mul_pos ( mul_pos hΔμ ( sq_pos_of_ne_zero h_identity ) ) ( by linarith [ show 0 < rStar Δμ a σ from div_pos ( by positivity ) ( by positivity ) ] ) ) ) )

/-
**FNT-2 — the half-barrier identity.**
    The nucleation barrier equals half the driving energy stored in the critical
    nucleus:  `ΔG* = G(rStar) = ½ Δμ (rStar)^3 = ½ Δμ n*`.
-/
theorem barrier_half_identity (Δμ a σ : ℝ) (hΔμ : 0 < Δμ) :
    G Δμ a σ (rStar Δμ a σ) = (1 / 2) * Δμ * (rStar Δμ a σ) ^ 3 := by
  unfold G rStar;
  grind

/-
**FNT-3 — broadcast is suboptimal (the Dispersal–Establishment Paradox).**
    Under a fixed seed budget `S` and sharp establishment threshold at `n*`, the
    colonized area `A_col(n) = (S/n)·𝟙[n ≥ n*]·C` is maximized UNIQUELY at the
    critical size `n = n*`, with positive value `S·C/n*`, while every
    sub-critical (broadcast) cluster colonizes zero area.  Spreading seed thinly
    to "cover maximum ground" covers the least.
-/
theorem broadcast_suboptimal (nStar S C : ℝ) (hn : 0 < nStar) (hS : 0 < S) (hC : 0 < C) :
    (∀ n : ℝ, 0 < n → Acol nStar S C n ≤ Acol nStar S C nStar) ∧
    Acol nStar S C nStar = S * C / nStar ∧
    0 < Acol nStar S C nStar ∧
    (∀ n : ℝ, 0 < n → Acol nStar S C n = Acol nStar S C nStar → n = nStar) ∧
    (∀ n : ℝ, 0 < n → n < nStar → Acol nStar S C n = 0) := by
  refine' ⟨ _, _, _, _, _ ⟩;
  · unfold Acol;
    intro n hn; by_cases h : nStar ≤ n <;> simp_all +decide [ div_eq_mul_inv ] ;
    · unfold estab; split_ifs <;> nlinarith [ show 0 < S * n⁻¹ by positivity, show 0 < S * nStar⁻¹ by positivity, mul_inv_cancel₀ ( ne_of_gt hn ), mul_inv_cancel₀ ( ne_of_gt ‹0 < nStar› ) ] ;
    · unfold estab; split_ifs <;> nlinarith [ show 0 < S * n⁻¹ by positivity, show 0 < S * nStar⁻¹ by positivity ] ;
  · unfold Acol estab; rw [if_pos le_rfl]; ring
  · exact mul_pos ( mul_pos ( div_pos hS hn ) ( by unfold estab; aesop ) ) hC;
  · unfold Acol;
    unfold estab;
    intro n hn h; split_ifs at h <;> simp_all +decide [ ne_of_gt, division_def ] ;
  · exact fun n hn hn' => by unfold Acol; unfold estab; split_ifs <;> linarith;

/-
**Non-vacuity witness.**
    The hypotheses of `critical_nucleus` / `barrier_half_identity` are inhabited
    by a concrete positive triple `(Δμ, a, σ) = (1, 1, 3/2)` for which the
    critical nucleus and the barrier are STRICTLY POSITIVE (`n* = 1`, `ΔG* = ½`),
    so the results above are not vacuously true.
-/
theorem FNT_nonvacuous :
    ∃ Δμ a σ : ℝ, 0 < Δμ ∧ 0 < a ∧ 0 < σ ∧
      0 < (rStar Δμ a σ) ^ 3 ∧
      G Δμ a σ (rStar Δμ a σ) = (1 / 2) * Δμ * (rStar Δμ a σ) ^ 3 ∧
      0 < G Δμ a σ (rStar Δμ a σ) := by
  exact ⟨ 6, 1, 3, by norm_num, by norm_num, by norm_num, by unfold rStar G; norm_num ⟩

end Viridis.Afforestation.ForestNucleation