/-
  MRAB.lean — The Multi-Ring Alignment Bound (MRAB), Theorem 1.

  Source: Viridis nightly engine Run-016 "aligned-polymath-bound"
  (`science-engine/.../Run-016_aligned-polymath-bound/paper.tex`, Thm 1, eq. (3)).
  Canon backlog Rank 8; spine (IB specialization). Aristotle Forge submission.

  INTENDED MEANING.  A polymath AI scientist operating across `K` rings of the
  Planetary Thermodynamic Market Stack has joint mutual-information rate bounded by

        dI_joint/dt  ≤  (P · D̄ / (k_B T ln 2)) · ∏_{k} cos²Θ_k,

  where  D̄ = (∏_k D_k)^{1/K}  is the geometric-mean dissipation factor and
  cos²Θ_k ∈ [0,1] is the per-ring Fisher–Wasserstein alignment factor.

  We model the per-ring data as finite real families on `Fin K`:
    • `c k = cos²Θ_k ∈ [0,1]`   (Cauchy–Schwarz, assumption 2 of the paper),
    • `D k ∈ [0,1]`             (structured dissipation fraction, by definition),
    • `κ = k_B T ln 2 > 0`      (positive temperature).

  NON-VACUITY.  Every theorem below carries explicit positivity / unit-interval
  hypotheses and a non-trivial conclusion:
    - the alignment factor genuinely lies in [0,1] (product structure),
    - D̄ lies in [0,1] and is bounded by the arithmetic mean (AM–GM),
    - the MRAB ceiling is non-negative and never exceeds the unaligned base rate
      `P D̄ / κ` (the *Polymath Paradox* collapse direction of Theorem 1),
    - equality (saturation) holds exactly at perfect alignment (the wu-wei polymath),
    - the bound reduces to the Master Intelligence Bound at `K = 1`, `Θ = 0`
      (the Universal Aligned Intelligence Bound / UAIB reduction).
-/
import Mathlib

open Finset
open scoped BigOperators

namespace MRAB

noncomputable section

/-- Effective Landauer constant `κ = k_B · T · ln 2`. -/
def kappa (kB T : ℝ) : ℝ := kB * T * Real.log 2

/-- Geometric-mean dissipation factor `D̄ = (∏_k D_k)^{1/K}`. -/
def Dbar (K : ℕ) (D : Fin K → ℝ) : ℝ := (∏ k, D k) ^ ((1 : ℝ) / K)

/-- The MRAB alignment factor `∏_k cos²Θ_k`. -/
def alignFactor (K : ℕ) (c : Fin K → ℝ) : ℝ := ∏ k, c k

/-- Unaligned single-scale base rate `P · D̄ / κ`. -/
def baseRate (K : ℕ) (P kB T : ℝ) (D : Fin K → ℝ) : ℝ :=
  P * Dbar K D / kappa kB T

/-- The MRAB ceiling `(P · D̄ / κ) · ∏_k cos²Θ_k`. -/
def mrabBound (K : ℕ) (P kB T : ℝ) (D c : Fin K → ℝ) : ℝ :=
  baseRate K P kB T D * alignFactor K c

/-
The alignment factor is non-negative.
-/
theorem alignFactor_nonneg (K : ℕ) (c : Fin K → ℝ) (hc : ∀ k, 0 ≤ c k) :
    0 ≤ alignFactor K c := by
  exact Finset.prod_nonneg fun _ _ => hc _

/-
The alignment factor `∏_k cos²Θ_k` lies below unity (the multiplicative
    collapse: any single misaligned ring drags the whole product down).
-/
theorem alignFactor_le_one (K : ℕ) (c : Fin K → ℝ)
    (hc0 : ∀ k, 0 ≤ c k) (hc1 : ∀ k, c k ≤ 1) :
    alignFactor K c ≤ 1 := by
  exact Finset.prod_le_one ( fun _ _ => hc0 _ ) fun _ _ => hc1 _

/-
The geometric-mean dissipation factor is non-negative.
-/
theorem Dbar_nonneg (K : ℕ) (D : Fin K → ℝ) (hD : ∀ k, 0 ≤ D k) :
    0 ≤ Dbar K D := by
  exact Real.rpow_nonneg ( Finset.prod_nonneg fun _ _ => hD _ ) _

/-
The geometric-mean dissipation factor lies below unity.
-/
theorem Dbar_le_one (K : ℕ) (hK : 0 < K) (D : Fin K → ℝ)
    (hD0 : ∀ k, 0 ≤ D k) (hD1 : ∀ k, D k ≤ 1) :
    Dbar K D ≤ 1 := by
  exact Real.rpow_le_one ( Finset.prod_nonneg fun _ _ => hD0 _ ) ( Finset.prod_le_one ( fun _ _ => hD0 _ ) fun _ _ => hD1 _ ) ( by positivity )

/-
AM–GM: the geometric-mean dissipation is bounded by the arithmetic mean
    (the conservative step used in the paper's derivation of `D̄`).
-/
theorem Dbar_le_arith_mean (K : ℕ) (hK : 0 < K) (D : Fin K → ℝ)
    (hD : ∀ k, 0 ≤ D k) :
    Dbar K D ≤ (∑ k, D k) / K := by
  unfold Dbar; have := @Real.geom_mean_le_arith_mean;
  simpa using this Finset.univ ( fun _ => 1 ) D ( fun _ _ => zero_le_one ) ( by simpa ) ( fun _ _ => hD _ )

/-
The unaligned base rate `P D̄ / κ` is non-negative.
-/
theorem baseRate_nonneg (K : ℕ) (P kB T : ℝ) (D : Fin K → ℝ)
    (hP : 0 ≤ P) (hkB : 0 < kB) (hT : 0 < T) (hD : ∀ k, 0 ≤ D k) :
    0 ≤ baseRate K P kB T D := by
  exact div_nonneg ( mul_nonneg hP ( Dbar_nonneg K D hD ) ) ( mul_nonneg ( mul_nonneg hkB.le hT.le ) ( Real.log_nonneg ( by norm_num ) ) )

/-
The MRAB ceiling is non-negative (physicality / non-vacuity).
-/
theorem mrabBound_nonneg (K : ℕ) (P kB T : ℝ) (D c : Fin K → ℝ)
    (hP : 0 ≤ P) (hkB : 0 < kB) (hT : 0 < T)
    (hD : ∀ k, 0 ≤ D k) (hc : ∀ k, 0 ≤ c k) :
    0 ≤ mrabBound K P kB T D c := by
  exact mul_nonneg ( div_nonneg ( mul_nonneg hP ( Real.rpow_nonneg ( Finset.prod_nonneg fun _ _ => hD _ ) _ ) ) ( mul_nonneg ( mul_nonneg hkB.le hT.le ) ( Real.log_nonneg one_le_two ) ) ) ( Finset.prod_nonneg fun _ _ => hc _ )

/-
**Theorem 1 (MRAB), Polymath-Paradox form.**  The joint aligned MRAB ceiling
    never exceeds the unaligned single-scale ceiling `P D̄ / κ`: adding rings can
    only shrink the joint information-rate budget.
-/
theorem mrab_bound_le_baseRate (K : ℕ) (P kB T : ℝ) (D c : Fin K → ℝ)
    (hP : 0 ≤ P) (hkB : 0 < kB) (hT : 0 < T)
    (hD : ∀ k, 0 ≤ D k) (hc0 : ∀ k, 0 ≤ c k) (hc1 : ∀ k, c k ≤ 1) :
    mrabBound K P kB T D c ≤ baseRate K P kB T D := by
  exact mul_le_of_le_one_right ( by exact div_nonneg ( mul_nonneg hP ( Real.rpow_nonneg ( Finset.prod_nonneg fun _ _ => hD _ ) _ ) ) ( mul_nonneg ( mul_nonneg hkB.le hT.le ) ( Real.log_nonneg one_le_two ) ) ) ( Finset.prod_le_one ( fun _ _ => hc0 _ ) fun _ _ => hc1 _ )

/-
**Saturation (the wu-wei polymath).**  Perfect alignment in every ring
    (`cos²Θ_k = 1`, i.e. `Θ_k = 0`) saturates the bound to the base rate.
-/
theorem mrab_saturation (K : ℕ) (P kB T : ℝ) (D c : Fin K → ℝ)
    (hc : ∀ k, c k = 1) :
    mrabBound K P kB T D c = baseRate K P kB T D := by
  unfold mrabBound baseRate;
  unfold alignFactor; aesop;

/-
**UAIB reduction.**  At `K = 1` and perfect alignment (`Θ = 0`), MRAB
    collapses to the Master Intelligence Bound `P · D / κ`.
-/
theorem mrab_reduces_to_IB (P kB T : ℝ) (D c : Fin 1 → ℝ) (hc : c 0 = 1) :
    mrabBound 1 P kB T D c = P * D 0 / kappa kB T := by
  unfold mrabBound baseRate Dbar alignFactor;
  simp +decide [ Fin.eq_zero, hc ]

end

end MRAB