import Mathlib

/-!
# Thermodynamic Corridor Theorem (TCT) — Run 022

Formalization targets for the Viridis nightly finding **Run 022 — Thermodynamic
Corridor Theorem**, which derives the HDFM corridor bifurcation optimum
`μ_opt ∈ [2,3]` and the PTMS Ring-3 pricing kernel `f(k) = μ^{k-1}` from
thermodynamic first principles (Prigogine minimum-entropy-production on a
balanced Strahler tree, with a Maximum-Entropy-Production boundary condition).

Source: `science-engine/.../Run-022_thermodynamic-corridor-theorem/finding.md`, §6.

This file states the four verification targets as **well-posed, non-vacuous**
Lean 4 propositions. Proofs are left as `sorry` for the Aristotle forge to
discharge. Each statement is accompanied by its intended physical meaning and an
explicit non-vacuity note: none of the conclusions is trivially true.

Toolchain: leanprover/lean4:v4.28.0 ; Mathlib pin 8f9d9cff.
-/

namespace TCT

open Finset

/--
**TCT.OnsagerVariational** — least-dissipation / Onsager variational principle.

Physical content: model the corridor network as a linear dissipative structure.
The local rate of entropy production for flux vector `J` across edges with
positive Onsager resistances `R i > 0` is the quadratic dissipation functional
`Φ(J) = ∑ᵢ Rᵢ · Jᵢ²`.  Prigogine's minimum-entropy-production principle says the
steady-state flux is the dissipation **minimizer** subject to the linear
flux-conservation (Kirchhoff) constraints, which carve out a convex set `s`.

This theorem states the *uniqueness* half of well-posedness: on any convex
constraint set, the dissipation-minimizing flux is unique. (Existence follows
from coercivity + closedness by the standard argument; uniqueness is the
non-trivial physical content — it is exactly strict convexity of `Φ` for
`Rᵢ > 0`.)

NON-VACUITY: the hypotheses are simultaneously satisfiable (take `s = Set.univ`,
`J₁ = J₂ = 0`, which is the minimizer when unconstrained), and the conclusion is
a genuine uniqueness claim, not vacuously true — for `Rᵢ ≤ 0` it would FAIL, so
the positivity hypothesis is load-bearing.
-/
theorem OnsagerVariational {n : ℕ} (R : Fin n → ℝ) (hR : ∀ i, 0 < R i)
    (s : Set (Fin n → ℝ)) (hs : Convex ℝ s)
    {J₁ J₂ : Fin n → ℝ}
    (hJ₁s : J₁ ∈ s) (hJ₂s : J₂ ∈ s)
    (h₁ : IsMinOn (fun J => ∑ i : Fin n, R i * (J i) ^ 2) s J₁)
    (h₂ : IsMinOn (fun J => ∑ i : Fin n, R i * (J i) ^ 2) s J₂) :
    J₁ = J₂ := by
  contrapose! h₁; contrapose! h₂; simp_all +decide [ IsMinOn, IsMinFilter ] ; (
  -- Consider the midpoint $M = \frac{J₁ + J₂}{2}$. Since $s$ is convex, $M \in s$.
  set M : Fin n → ℝ := fun i => (J₁ i + J₂ i) / 2
  have hM : M ∈ s := by
    convert hs hJ₁s hJ₂s ( by norm_num : ( 0 : ℝ ) ≤ 1 / 2 ) ( by norm_num : ( 0 : ℝ ) ≤ 1 / 2 ) ( by norm_num ) using 1 ; ext i ; norm_num ; ring;
  have hM_sum : ∑ i, R i * M i ^ 2 < (∑ i, R i * J₁ i ^ 2 + ∑ i, R i * J₂ i ^ 2) / 2 := by
    -- Since $J₁ \neq J₂$, there exists some $i$ such that $J₁ i \neq J₂ i$.
    obtain ⟨i, hi⟩ : ∃ i, J₁ i ≠ J₂ i := by
      exact Function.ne_iff.mp h₁
    generalize_proofs at *; (
    rw [ ← Finset.sum_add_distrib, Finset.sum_div _ _ _ ] ; refine' ( Finset.sum_lt_sum _ _ ) ; (
    exact fun i _ => by rw [ show M i = ( J₁ i + J₂ i ) / 2 by rfl ] ; nlinarith only [ sq_nonneg ( J₁ i - J₂ i ), hR i ] ;);
    exact ⟨ i, Finset.mem_univ _, by rw [ show M i = ( J₁ i + J₂ i ) / 2 by rfl ] ; nlinarith only [ mul_self_pos.mpr ( sub_ne_zero.mpr hi ), hR i ] ⟩ ;)
  generalize_proofs at *; (
  exact ⟨ M, hM, by linarith [ h₂ _ hM, h₂ _ hJ₂s ] ⟩);)

/--
**TCT.LambertOptimum** — closed-form corridor bifurcation optimum.

Physical content: minimizing the global dissipation `Σ̇` over balanced Strahler
trees of bifurcation ratio `μ`, subject to the MEP boundary condition and a land
budget, yields the first-order condition `2·μ²·ln μ = R`, where
`R = D_target / D_min` is the landscape D-capital ratio.  Writing `u = 2 ln μ`
gives `u·eᵘ = R`, i.e. `u = W(R)` (Lambert W), hence the finding's closed form
`μ_opt = exp(W(R)/2)`.  For biome ratios `R ∈ [4,12]` this lands `μ_opt ∈ [2,3]`,
recovering the HDFM empirical range.

We state existence-and-uniqueness of the optimum *without* requiring a Lambert-W
constant in the library: the optimum is the unique `μ > 1` solving the
first-order condition.  (The map `μ ↦ 2μ² ln μ` is continuous, vanishes at
`μ = 1`, is strictly increasing on `(1,∞)`, and is unbounded above — hence a
bijection `(1,∞) → (0,∞)`.)

NON-VACUITY: `0 < R` guarantees a solution with `1 < μ` (the conclusion is a
`∃!`, not a tautology); for `R ≤ 0` no `μ > 1` solves it, so the hypothesis is
load-bearing.
-/
theorem LambertOptimum (R : ℝ) (hR : 0 < R) :
    ∃! μ : ℝ, 1 < μ ∧ 2 * μ ^ 2 * Real.log μ = R := by
  obtain ⟨μ, hμ⟩ : ∃ μ : ℝ, 1 < μ ∧ 2 * μ ^ 2 * Real.log μ = R := by
    -- We'll use the intermediate value theorem to show there exists a μ in the interval (1, ∞) such that 2 * μ^2 * Real.log μ = R.
    have h_ivt : ∃ μ ∈ Set.Ioo 1 (Real.exp (R / 2)), 2 * μ ^ 2 * Real.log μ = R := by
      apply_rules [ intermediate_value_Ioo ] <;> norm_num;
      · positivity;
      · exact ContinuousOn.mul ( ContinuousOn.mul continuousOn_const ( continuousOn_pow 2 ) ) ( Real.continuousOn_log.mono <| by norm_num );
      · exact ⟨ hR, by nlinarith [ Real.add_one_le_exp ( R / 2 ), Real.exp_pos ( R / 2 ), mul_pos hR ( Real.exp_pos ( R / 2 ) ) ] ⟩;
    aesop;
  refine' ⟨ μ, hμ, _ ⟩;
  intros y hy; exact le_antisymm ( le_of_not_gt fun h => by nlinarith [ mul_pos ( sub_pos.mpr h ) ( sub_pos.mpr hy.1 ), mul_pos ( sub_pos.mpr h ) ( sub_pos.mpr hμ.1 ), Real.log_pos hy.1, Real.log_lt_log ( by linarith ) h ] ) ( le_of_not_gt fun h => by nlinarith [ mul_pos ( sub_pos.mpr h ) ( sub_pos.mpr hy.1 ), mul_pos ( sub_pos.mpr h ) ( sub_pos.mpr hμ.1 ), Real.log_pos hy.1, Real.log_lt_log ( by linarith ) h ] ) ;

/--
**TCT.PricingKernelUniqueness** — uniqueness of the Ring-3 discount kernel.

Physical content: the PTMS Ring-3 D-ESU pricing multiplier across corridor scales
must commute with the dissipation cascade, i.e. it is a multiplicative cocycle in
the scale index.  Reindexing the per-order kernel `f(k) = g(k-1)` for `k ≥ 1`,
the cocycle becomes the Cauchy multiplicative equation `g(a+b) = g(a)·g(b)` with
normalization `g(0) = 1`.  Its unique solution is `g(k) = μ^k` with `μ = g(1)`,
i.e. `f(k) = μ^{k-1}` — exactly the Ring-3 kernel, now derived rather than
assumed.

NON-VACUITY: the conclusion pins down `g` *uniquely* on all of `ℕ` from two
hypotheses; it is not vacuous because the family `g(k) = μ^k` genuinely satisfies
the hypotheses for every `μ`, and the theorem asserts these are the only
solutions.
-/
theorem PricingKernelUniqueness (g : ℕ → ℝ)
    (h0 : g 0 = 1) (hcoc : ∀ a b : ℕ, g (a + b) = g a * g b) :
    ∀ k : ℕ, g k = (g 1) ^ k := by
  intro k; induction' k with n ih <;> simp_all +decide [ pow_succ ]

/--
**TCT.PhaseTransition** — corridor percolation threshold `μ_c = 1 + ln 2`.

Physical content: the dissipation cost per unit D-capital flux on the corridor
network is a geometric cascade with ratio `r(μ) = (1 + ln 2)/μ` across scales.
The cost is finite (the network can support flux) iff the geometric series
converges, i.e. iff `μ > μ_c = 1 + ln 2 ≈ 1.693`.  Below `μ_c` the cost
diverges: any conservation plan with `μ < 1.693` is thermodynamically condemned
regardless of total corridor area — a hard regulatory phase transition.

NON-VACUITY: the threshold constant `1 + Real.log 2` is positive and the
equivalence is sharp (the ratio is exactly `1` at `μ = μ_c`); both directions are
non-trivial.
-/
theorem PhaseTransition (μ : ℝ) (hμ : 0 < μ) :
    Summable (fun k : ℕ => ((1 + Real.log 2) / μ) ^ k) ↔ 1 + Real.log 2 < μ := by
  rw [ summable_geometric_iff_norm_lt_one ];
  rw [ Real.norm_of_nonneg ( by positivity ), div_lt_one ( by positivity ) ]

end TCT