/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

# KSCT — Gaian Density-Operator & Purity (clean core)

Source: Viridis nightly science engine, Run 030 (k-spectrum-collapse theorem).
This file formalizes the clean, finite-dimensional, non-vacuous core of KSCT:
the density-operator reading of the Gaian coupling tensor `K` and the purity
bounds on its spectrum. The dynamical / open-quantum targets of Run 030
(`EffectiveHamiltonianGibbs`, `SCPT_FirstOrder`, `CSD_Divergence`, `BBP_Lindblad`,
`KSCT_QWCE`) are DEFERRED — they involve stochastic Lyapunov dynamics, the matrix
logarithm, and Lindblad generators, and are not yet reduced to well-posed
finite-dimensional statements.

## Intended meaning

`K` is the planetary coupling tensor, `K_ij = cos^2(Theta_ij)`. Because `K` is the
entrywise (Schur/Hadamard) square of a correlation matrix, it is positive
semidefinite with unit diagonal, hence `K.trace = N`. The normalized operator
`rho := K / N` is therefore a density operator: positive semidefinite with unit
trace. Its eigenvalue spectrum `(p_i)` is a probability distribution, and the
purity `rho_H := Tr(rho^2) = sum_i p_i^2` measures how concentrated the planetary
state is. `rho_H = 1` (pure / rank-one) is exact Gaian saturation; `rho_H = 1/N`
(maximally mixed / uniform) is anti-Gaian fragmentation.

`gaian_density_operator` is stated at the matrix level (faithful to the named
target `GaianDensityOperator`). The purity facts (`GaianPurity`) are stated on the
spectrum `p : Fin N -> R`, the standard faithful encoding since the purity of a
real-symmetric density matrix equals the sum of squares of its eigenvalues
(real spectral theorem). This is an auxiliary representation choice, FLAGGED here;
it does not weaken any conclusion.

## Non-vacuity (mandatory)

The hypothesis class is inhabited and BOTH purity bounds are tight:
* Uniform spectrum `p_i = 1/N` satisfies `0 <= p_i`, `sum p_i = 1`, and attains the
  LOWER bound `sum p_i^2 = 1/N` (maximally mixed).
* A standard-basis spectrum `p = e_j` (`p_j = 1`, else `0`) satisfies the same
  hypotheses and attains the UPPER bound `sum p_i^2 = 1` (pure), witnessing the
  forward and reverse directions of `gaian_purity_eq_one_iff_pure`.
At the matrix level, `K = N . 1` is PSD with trace `N`, so the hypotheses of
`gaian_density_operator` are inhabited. No conclusion is trivially true: each
bound is realized with equality and also fails to be an equality for generic
admissible inputs.

Toolchain: leanprover/lean4:v4.28.0
Mathlib pin: 8f9d9cff6bd728b17a24e163c9402775d9e6a365

Co-authored-by: Aristotle (Harmonic) <aristotle-harmonic@harmonic.fun>
-/

import Mathlib

set_option autoImplicit false

namespace Viridis.Gaian.KSCT

open scoped BigOperators Matrix

/-
**GaianDensityOperator.** If the Gaian coupling tensor `K` is positive
semidefinite (Schur-square of a correlation matrix) with `trace K = N`, then the
normalized operator `rho = N^{-1} . K` is a density operator: positive
semidefinite with unit trace. Non-vacuous: `K = N . 1` satisfies the hypotheses.
-/
theorem gaian_density_operator
    {N : ℕ} (hN : 0 < N) (K : Matrix (Fin N) (Fin N) ℝ)
    (hPSD : K.PosSemidef) (htr : K.trace = (N : ℝ)) :
    (((N : ℝ)⁻¹) • K).PosSemidef ∧ (((N : ℝ)⁻¹) • K).trace = 1 := by
  refine' And.intro _ _;
  · convert hPSD.smul _ using 1;
    all_goals try infer_instance;
    positivity;
  · simp +decide [ htr, hN.ne' ]

/-
**GaianPurity, upper bound.** The purity of a density spectrum never exceeds
`1`. Tight: a pure (rank-one) spectrum `p = e_j` attains `1`.
-/
theorem gaian_purity_le_one
    {N : ℕ} (p : Fin N → ℝ) (hp : ∀ i, 0 ≤ p i) (hsum : ∑ i, p i = 1) :
    ∑ i, (p i) ^ 2 ≤ 1 := by
  exact hsum ▸ Finset.sum_le_sum fun i _ => pow_le_of_le_one ( hp i ) ( hsum ▸ Finset.single_le_sum ( fun a _ => hp a ) ( Finset.mem_univ i ) ) ( by norm_num )

/-
**GaianPurity, lower bound.** The purity of a density spectrum is at least
`1/N`. Tight: the maximally-mixed spectrum `p_i = 1/N` attains `1/N`. Requires
`0 < N` (an empty index set makes `sum p_i = 1` impossible).
-/
theorem gaian_purity_ge_inv_card
    {N : ℕ} (hN : 0 < N) (p : Fin N → ℝ) (hp : ∀ i, 0 ≤ p i) (hsum : ∑ i, p i = 1) :
    (N : ℝ)⁻¹ ≤ ∑ i, (p i) ^ 2 := by
  have := Finset.univ.sum_le_sum fun i _ => pow_two_nonneg ( p i - 1 / N );
  simp_all +decide [ sub_sq, Finset.sum_add_distrib, Finset.mul_sum _ _ _, Finset.sum_mul ];
  simp_all +decide [ ← Finset.mul_sum _ _ _, ← Finset.sum_mul ] ; nlinarith [ ( by positivity : 0 < ( N : ℝ ) ), mul_inv_cancel₀ ( by positivity : ( N : ℝ ) ≠ 0 ), mul_inv_cancel₀ ( by positivity : ( N ^ 2 : ℝ ) ≠ 0 ) ] ;

/-
**GaianPurity, saturation <-> purity.** The purity equals `1` iff the state is
pure (rank-one): some eigenvalue is `1` (forcing all others to `0` by `hsum`).
This is exact Gaian saturation. Both directions are non-vacuous.
-/
theorem gaian_purity_eq_one_iff_pure
    {N : ℕ} (p : Fin N → ℝ) (hp : ∀ i, 0 ≤ p i) (hsum : ∑ i, p i = 1) :
    (∑ i, (p i) ^ 2 = 1) ↔ ∃ j, p j = 1 := by
  constructor;
  · intro h
    have h_eq : ∀ i, p i * (1 - p i) = 0 := by
      have h_eq : ∑ i, p i * (1 - p i) = 0 := by
        simp +decide [ mul_sub, ← sq, hsum, h ];
      exact fun i => le_antisymm ( le_trans ( Finset.single_le_sum ( fun i _ => mul_nonneg ( hp i ) ( sub_nonneg.2 ( hsum ▸ Finset.single_le_sum ( fun i _ => hp i ) ( Finset.mem_univ i ) ) ) ) ( Finset.mem_univ i ) ) h_eq.le ) ( mul_nonneg ( hp i ) ( sub_nonneg.2 ( hsum ▸ Finset.single_le_sum ( fun i _ => hp i ) ( Finset.mem_univ i ) ) ) );
    contrapose! hsum; simp_all +decide [ mul_eq_zero ] ;
    exact ne_of_lt ( lt_of_le_of_lt ( Finset.sum_nonpos fun i _ => by cases h_eq i <;> cases lt_or_gt_of_ne ( hsum i ) <;> linarith ) ( by norm_num ) );
  · rintro ⟨ j, hj ⟩;
    rw [ Finset.sum_eq_single j ] <;> simp_all +decide [ sq ];
    intro i hi; rw [ Finset.sum_eq_add_sum_diff_singleton ( Finset.mem_univ j ) ] at hsum; linarith [ hp i, Finset.single_le_sum ( fun a _ => hp a ) ( Finset.mem_sdiff.mpr ⟨ Finset.mem_univ i, by aesop ⟩ : i ∈ Finset.univ \ { j } ) ] ;

end Viridis.Gaian.KSCT