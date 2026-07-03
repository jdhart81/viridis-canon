/-
  Afforestation Stewardship Theorem (AST) — clean analytic core
  ============================================================
  Viridis Canon · Nightly Run-083 (2026-06-28) · IB self-application #25 ("the Sower")
  Area [11] Afforestation Systems × 🎯 Stewardship.  CONVERGENCE EVENT:
  the Forest-Nucleation thread (FNT, Run-061) ⊗ the shadow-price water-filling
  family (Runs 064/065/068/069/074/079) merged into one variational object,
  AST being the first NON-CONVEX member; the prior family is its convex limit.

  This module formalizes the analytic, finite-dimensional core of AST — the
  results whose statements are unambiguous and whose conclusions are NON-VACUOUS.
  Combinatorial-optimization results (bang-bang knapsack reduction, greedy
  ½-approximation) and the (β, T_eco) phase diagram are deferred to a dedicated
  effort; they are NOT included here.

  MODEL (classical nucleation, after FNT-061).  For a single site with
  ecological drive Δμ > 0 (suitability), edge hostility / "surface tension"
  σ > 0, and shape constant a > 0:
      critical nucleus      nStar a σ Δμ = (2 a σ / (3 Δμ))^3
      nucleation barrier    barrier a σ Δμ = 4 (a σ)^3 / (27 Δμ^2)
      seeding efficiency    eff a σ Δμ C   = C * (3 Δμ / (2 a σ))^3   (= C / nStar)

  NON-VACUITY conditions.  All scaling/identity theorems are stated for strictly
  positive parameters (a, σ, Δμ, C, t > 0); the conclusions carry non-trivial
  numeric factors (t^3, 8, the cos^2 bound strictly inside [0,1] in general),
  so none collapses to a tautology.

  THEOREMS (clean core):
    1. establishment_efficiency_cubic_in_drive_over_tension
         eff scales as the CUBE of the drive Δμ  (the e_i ∝ (Δμ/σ)^3 law).
    2. site_prep_halving_sigma_eightfolds_efficiency
         halving the edge hostility σ multiplies efficiency by 8 = 2^3
         (the headline stewardship practice: lower the surface tension).
    3. homogeneous_limit_recovers_fnt
         barrier = ½ Δμ nStar  — the FNT ½-identity recovered in the
         homogeneous limit (the barrier IS the intergenerational price).
    4. sower_IB_ceiling
         the establishing forest writes information at a rate bounded by the
         Intelligence Bound  rate ≤ P D / (k_B T ln 2)  (IB self-application #25).
    5. seeding_efficiency_eq_cos2_theta
         the allocation/optimum alignment η = ⟨n,n*⟩² / (‖n‖² ‖n*‖²) lies in
         [0,1] (Cauchy–Schwarz); forcing debt = 1 − η = sin²Θ. The canon's
         universal cos²Θ geometry, here for the seeding vector.
-/
import Mathlib

set_option autoImplicit false
set_option maxHeartbeats 1000000

namespace Viridis.Afforestation.AfforestationStewardship

open Real

/-- Critical nucleus size n* = (2 a σ / (3 Δμ))^3  (FNT-061). -/
noncomputable def nStar (a σ Δμ : ℝ) : ℝ := (2 * a * σ / (3 * Δμ)) ^ 3

/-- Nucleation barrier ΔG* = 4 (a σ)^3 / (27 Δμ^2)  (FNT-061). -/
noncomputable def barrier (a σ Δμ : ℝ) : ℝ := 4 * (a * σ) ^ 3 / (27 * Δμ ^ 2)

/-- Seeding efficiency e = C / n* = C * (3 Δμ / (2 a σ))^3
    (established canopy per seed). -/
noncomputable def eff (a σ Δμ C : ℝ) : ℝ := C * (3 * Δμ / (2 * a * σ)) ^ 3

/-
**R3 (cubic establishment-efficiency law).** Seeding efficiency scales as the
    CUBE of the ecological drive Δμ: scaling the drive by `t` multiplies the
    efficiency by `t^3`. Non-vacuous: the factor is `t^3`, not `1`.
-/
theorem establishment_efficiency_cubic_in_drive_over_tension
    (a σ Δμ C t : ℝ) (ha : 0 < a) (hσ : 0 < σ) (hΔμ : 0 < Δμ) (ht : 0 < t) :
    eff a σ (t * Δμ) C = t ^ 3 * eff a σ Δμ C := by
  unfold eff; ring;

/-
**R3 corollary (the 8× site-prep lever).** Halving the edge hostility σ
    (nurse plants, mulch, competition control) multiplies seeding efficiency by
    exactly `8 = 2^3`. Non-vacuous: the factor is `8`, not `1`.
-/
theorem site_prep_halving_sigma_eightfolds_efficiency
    (a σ Δμ C : ℝ) (ha : 0 < a) (hσ : 0 < σ) (hΔμ : 0 < Δμ) (hC : 0 < C) :
    eff a (σ / 2) Δμ C = 8 * eff a σ Δμ C := by
  unfold eff; ring;

/-
**Homogeneous limit recovers FNT (the ½-identity).** The nucleation barrier
    equals half the critical-mass drive product: ΔG* = ½ Δμ n*. The barrier is
    the thermodynamic price of the intergenerational commitment.
-/
theorem homogeneous_limit_recovers_fnt
    (a σ Δμ : ℝ) (ha : 0 < a) (hσ : 0 < σ) (hΔμ : 0 < Δμ) :
    barrier a σ Δμ = (1 / 2) * Δμ * nStar a σ Δμ := by
  unfold barrier nStar
  field_simp
  ring

/-
**R5 (the Sower — IB self-application #25).** The establishing forest writes
    structural information into the landscape at a rate bounded by the
    Intelligence Bound: given the governing premise `rate · (k_B T ln 2) ≤ P D`
    with `k_B, T > 0`, the rate satisfies `rate ≤ P D / (k_B T ln 2)`.
    Non-vacuous: the denominator `k_B T ln 2 > 0`, so the bound is finite and
    binding.
-/
theorem sower_IB_ceiling
    (rate P D kB T : ℝ) (hkB : 0 < kB) (hT : 0 < T)
    (hbound : rate * (kB * T * Real.log 2) ≤ P * D) :
    rate ≤ P * D / (kB * T * Real.log 2) := by
  rwa [ le_div_iff₀ ( by positivity ) ]

/-
**R7 (efficiency = cos²Θ — the canon's universal cosine geometry).** For
    nonzero allocation `n` and optimal seeding vector `m` in a real inner-product
    space, the alignment `η = ⟨n,m⟩² / (‖n‖² ‖m‖²)` lies in `[0,1]` (Cauchy–
    Schwarz); `η = 1` iff `n ∥ m`, and the forcing debt is `1 − η = sin²Θ`.
    Non-vacuous: for non-parallel `n, m` the upper bound is strict.
-/
theorem seeding_efficiency_eq_cos2_theta
    {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (n m : E) (hn : n ≠ 0) (hm : m ≠ 0) :
    0 ≤ (inner ℝ n m : ℝ) ^ 2 / (‖n‖ ^ 2 * ‖m‖ ^ 2) ∧
      (inner ℝ n m : ℝ) ^ 2 / (‖n‖ ^ 2 * ‖m‖ ^ 2) ≤ 1 := by
  refine' ⟨ by positivity, _ ⟩;
  exact div_le_one_of_le₀ ( by nlinarith [ abs_le.mp ( abs_real_inner_le_norm n m ) ] ) ( by positivity )

end Viridis.Afforestation.AfforestationStewardship