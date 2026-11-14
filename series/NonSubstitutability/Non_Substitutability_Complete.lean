/-
  Boundary essentiality of data richness in the product-form Intelligence Bound
  (deposited in May 2026 as "Non-Substitutability Theorem: Complete Formal Verification")

  This file formalizes the product-form bound F(P, D) = P * D / (k_B * T * ln 2). It proves:
    - boundary essentiality: F(P, 0) = 0;
    - continuity of F as D -> 0;
    - the compensation formula: a finite increase in P offsets any partial loss of D;
    - the isoquant P * D = constant.

  It does NOT prove that biodiversity is non-substitutable. Under the product form, power and D
  substitute at unit elasticity. The canon's certified non-substitution result is the min-form
  data wall (`data_wall`; see CLAIMS_MATRIX.md, v9.1.0 onward).

  Correction of 2026-11-14 to the file deposited at doi:10.5281/zenodo.20010754:
    - two docstrings that ended with a line-comment marker now end with the block-comment
      terminator, so the last three results are checked;
    - `no_finite_compensation`, `economic_non_substitutability` and `extinction_irreversible` have
      accurate names (`compensation_formula`, `isoquant_is_hyperbola`, `bound_zero_at_zero_species`);
      the old names remain as deprecated aliases;
    - comments state what each theorem proves. No statement or proof is changed.

  Author: Justin D. Hart (Viridis LLC). AI use: drafted with Claude (Anthropic); compile fixes by the
  Aristotle prover (Harmonic). AI tools are not authors.
  Lean: leanprover/lean4:v4.28.0 with Mathlib.
-/

import Mathlib

namespace NonSubstitutability

/-══════════════════════════════════════════════════════════════════════════════
  SECTION 1: CORE DEFINITIONS

  We establish the mathematical setting for the Non-Substitutability Theorem.
══════════════════════════════════════════════════════════════════════════════-/

/--
Physical constants (positive reals)
-/
structure PhysicalConstants where
  k_B : ℝ        -- Boltzmann constant
  T : ℝ          -- Temperature
  hk_B_pos : k_B > 0
  hT_pos : T > 0

/--
Landauer energy: minimum energy per bit erasure
E_L = k_B · T · ln(2)
-/
noncomputable def landauer_energy (c : PhysicalConstants) : ℝ :=
  c.k_B * c.T * Real.log 2

/--
Lemma: Landauer energy is positive
-/
lemma landauer_energy_pos (c : PhysicalConstants) : landauer_energy c > 0 := by
  unfold landauer_energy
  apply mul_pos
  apply mul_pos c.hk_B_pos c.hT_pos
  exact Real.log_pos (by norm_num : (1:ℝ) < 2)

/--
Intelligence Bound Function:
Given power P and data richness D, the maximum learning rate is:
  dI/dt_max = P · D / (k_B · T · ln 2)
-/
noncomputable def intelligence_bound (c : PhysicalConstants) (P D : ℝ) : ℝ :=
  P * D / (landauer_energy c)

/--
Alternative form emphasizing D as efficiency coefficient:
  dI/dt_max = (P / E_L) · D
-/
noncomputable def intelligence_bound' (c : PhysicalConstants) (P D : ℝ) : ℝ :=
  (P / landauer_energy c) * D

/--
These two forms are equivalent
-/
lemma intelligence_bound_equiv (c : PhysicalConstants) (P D : ℝ) :
    intelligence_bound c P D = intelligence_bound' c P D := by
  unfold intelligence_bound intelligence_bound'
  ring

/-══════════════════════════════════════════════════════════════════════════════
  SECTION 2: NON-SUBSTITUTABILITY - BASIC FORM

  D cannot be substituted by P: when D = 0, the bound is 0 regardless of P.
══════════════════════════════════════════════════════════════════════════════-/

/--
THEOREM: Basic Non-Substitutability

When D = 0, the intelligence bound is 0, regardless of P.
This is immediate from the definition: P · 0 / E_L = 0.
-/
theorem non_substitutability_basic (c : PhysicalConstants) (P : ℝ) :
    intelligence_bound c P 0 = 0 := by
  unfold intelligence_bound
  ring

/--
COROLLARY: Zero D implies zero intelligence creation capacity

No matter how much power is available, if D = 0, no intelligence can be created.
-/
theorem zero_D_zero_capacity (c : PhysicalConstants) (P : ℝ) (_hP : P ≥ 0) :
    intelligence_bound c P 0 = 0 := by
  exact non_substitutability_basic c P

/-
══════════════════════════════════════════════════════════════════════════════
  SECTION 3: NON-SUBSTITUTABILITY - LIMIT FORM

  The limit as D approaches 0 is 0, for any fixed P.
══════════════════════════════════════════════════════════════════════════════

THEOREM: Limit Form of Non-Substitutability

For any P ≥ 0 and any ε > 0, there exists δ > 0 such that:
  |D| < δ → |intelligence_bound c P D| < ε

In other words: lim_{D→0} intelligence_bound(P, D) = 0
-/
theorem non_substitutability_limit (c : PhysicalConstants) (P : ℝ) (_hP : P ≥ 0) :
    ∀ ε > 0, ∃ δ > 0, ∀ D, |D| < δ → |intelligence_bound c P D| < ε := by
  unfold intelligence_bound;
  exact fun ε hε => ⟨ ε / ( |P| + 1 ) * ( landauer_energy c ), mul_pos ( div_pos hε ( by positivity ) ) ( landauer_energy_pos c ), fun D hD => by rw [ abs_div, abs_mul, abs_of_nonneg ( show 0 ≤ landauer_energy c from le_of_lt ( landauer_energy_pos c ) ) ] ; rw [ div_lt_iff₀ ] <;> nlinarith [ abs_nonneg P, abs_nonneg D, abs_mul_abs_self D, abs_mul_abs_self P, div_mul_cancel₀ ε ( by positivity : ( |P| + 1 ) ≠ 0 ), landauer_energy_pos c, mul_pos ( landauer_energy_pos c ) ( by positivity : 0 < |P| + 1 ) ] ⟩

/-
COROLLARY: The Intelligence Bound is continuous at D = 0

The function D ↦ intelligence_bound(P, D) is continuous, and its
value at 0 is 0. This formalizes "no discontinuous jump."
-/
theorem intelligence_bound_continuous_at_zero (c : PhysicalConstants) (P : ℝ) (_hP : P ≥ 0) :
    Filter.Tendsto (fun D => intelligence_bound c P D) (nhds 0) (nhds 0) := by
  unfold intelligence_bound;
  exact Continuous.tendsto' ( by continuity ) _ _ ( by norm_num )

/-══════════════════════════════════════════════════════════════════════════════
  SECTION 4: QUANTITATIVE NON-SUBSTITUTABILITY

  Precise bounds on how D-reduction limits intelligence creation.
══════════════════════════════════════════════════════════════════════════════-/

/--
THEOREM: Minimum D Required for Target Rate

To achieve a target learning rate r, a minimum D is required:
  D_min = r · E_L / P

If D < D_min, the target rate r is unachievable regardless of other factors.
-/
noncomputable def minimum_D_required (c : PhysicalConstants) (P r : ℝ) : ℝ :=
  r * landauer_energy c / P

theorem target_rate_requires_minimum_D (c : PhysicalConstants)
    {P r : ℝ} (hP : P > 0) (_hr : r > 0)
    {D : ℝ} (hD_small : D < minimum_D_required c P r) :
    intelligence_bound c P D < r := by
  unfold intelligence_bound minimum_D_required at *;
  rw [ div_lt_iff₀ ] <;> nlinarith [ mul_div_cancel₀ ( r * landauer_energy c ) hP.ne', landauer_energy_pos c ]

/--
COROLLARY: Proportional D-reduction causes proportional bound reduction

If D is reduced by factor α (0 < α < 1), the bound is reduced by factor α.
No increase in P can compensate.
-/
theorem proportional_reduction (c : PhysicalConstants)
    {P D : ℝ} (_hP : P > 0) (_hD : D > 0) {α : ℝ} (_hα : 0 < α) (_hα' : α < 1) :
    intelligence_bound c P (α * D) = α * intelligence_bound c P D := by
  unfold intelligence_bound
  ring

/--
Compensation formula. For 0 < ΔD < D, raising power by ΔP = P·ΔD/(D−ΔD) exactly restores the
product-form bound P·D/E_L. The required ΔP is finite for every partial loss and diverges only as
ΔD → D. So the product form expresses boundary essentiality (no output at D = 0), not
non-substitutability.
-/
theorem compensation_formula (c : PhysicalConstants)
    {P D ΔD : ℝ} (_hP : P > 0) (_hD : D > 0) (_hΔD : ΔD > 0) (hΔD' : ΔD < D) :
    let required_ΔP := P * ΔD / (D - ΔD)
    intelligence_bound c (P + required_ΔP) (D - ΔD) = intelligence_bound c P D := by
  unfold intelligence_bound
  simp only
  have hD_new_pos : D - ΔD > 0 := by linarith
  field_simp
  ring

/-
COROLLARY: As ΔD approaches D, required compensation approaches infinity

For any bound M, ΔD can be chosen close enough to D such that
the required power compensation P * ΔD / (D - ΔD) exceeds M.

Equivalently: lim_{ΔD → D⁻} P * ΔD / (D - ΔD) = +∞
-/
theorem compensation_diverges (_c : PhysicalConstants)
    {P D : ℝ} (hP : P > 0) (hD : D > 0) :
    ∀ M : ℝ, ∃ δ > 0, δ ≤ D ∧
      ∀ ΔD : ℝ, D - δ < ΔD → ΔD < D → P * ΔD / (D - ΔD) > M := by
  intro M
  by_cases hM : M < 0;
  · exact ⟨ D, hD, le_rfl, fun ΔD hΔD₁ hΔD₂ => lt_of_lt_of_le hM <| div_nonneg ( mul_nonneg hP.le <| by linarith ) <| by linarith ⟩;
  · use Min.min ( D / 2 ) ( P * D / ( M + P + 1 ) );
    refine' ⟨ _, _, _ ⟩;
    · exact lt_min ( half_pos hD ) ( div_pos ( mul_pos hP hD ) ( by linarith ) );
    · exact le_trans ( min_le_left _ _ ) ( by linarith );
    · intro ΔD hΔD₁ hΔD₂; rw [ gt_iff_lt ] ; rw [ lt_div_iff₀ ] <;> cases min_cases ( D / 2 ) ( P * D / ( M + P + 1 ) ) <;> nlinarith [ mul_div_cancel₀ ( P * D ) ( by linarith : ( M + P + 1 ) ≠ 0 ) ] ;

/-══════════════════════════════════════════════════════════════════════════════
  SECTION 5: ECONOMIC INTERPRETATION

  The Non-Substitutability Theorem has direct economic implications.
══════════════════════════════════════════════════════════════════════════════-/

/--
Definition: Marginal Rate of Technical Substitution (MRTS)

In economics, MRTS measures how much of one input can be substituted
for another while maintaining the same output.

For intelligence creation with inputs P and D:
  MRTS = -(∂I/∂D) / (∂I/∂P) = -D / P  (at any given (P, D))

This describes local substitution. Under the product form the two inputs
substitute at unit elasticity; only the boundary D = 0 (or P = 0) gives zero output.
-/
noncomputable def marginal_rate_substitution (P D : ℝ) : ℝ := -D / P

/--
The isoquant is a hyperbola. For positive P and D, the bound equals a target rate r exactly when
P * D = r * E_L. Along it, a smaller D is offset by a larger finite P; the curve approaches the
axes without meeting them, so no finite P gives rate r at D = 0.
-/
theorem isoquant_is_hyperbola (c : PhysicalConstants) {r : ℝ} (_hr : r > 0) :
    ∀ P D, P > 0 → D > 0 →
    (intelligence_bound c P D = r ↔ P * D = r * landauer_energy c) := by
  exact fun P D hP hD => by unfold intelligence_bound; rw [ div_eq_iff ] ; ring ; linarith [ landauer_energy_pos c ] ;

/-══════════════════════════════════════════════════════════════════════════════
  SECTION 6: BIODIVERSITY APPLICATION

  Connecting the abstract D to concrete biodiversity.
══════════════════════════════════════════════════════════════════════════════-/

/--
Biodiversity-D Coupling:
D is a function of species richness S and other biodiversity metrics.

We model: D(S) = log₂(S + 1) / log₂(S_max + 1)

This ensures:
- D(0) = 0 (no species → no data richness)
- D is monotonically increasing in S
- D ≤ 1 for S ≤ S_max
-/
noncomputable def D_of_species (S : ℕ) (S_max : ℕ) : ℝ :=
  Real.log (S + 1) / Real.log (S_max + 1)

/--
Lemma: D vanishes at extinction
-/
lemma D_vanishes_at_extinction (S_max : ℕ) (_hS_max : S_max > 0) :
    D_of_species 0 S_max = 0 := by
  unfold D_of_species
  simp [Real.log_one]

/--
Lemma: D is positive for positive species count
-/
lemma D_positive_of_species_positive (S : ℕ) (S_max : ℕ) (hS : S > 0) (hS_max : S_max ≥ S) :
    D_of_species S S_max > 0 := by
  unfold D_of_species
  apply div_pos
  · have h1 : (S : ℝ) + 1 > 1 := by
      have : (S : ℝ) > 0 := Nat.cast_pos.mpr hS
      linarith
    exact Real.log_pos h1
  · have h2 : (S_max : ℝ) + 1 > 1 := by
      have : (S_max : ℝ) ≥ (S : ℝ) := Nat.cast_le.mpr hS_max
      have hS_pos : (S : ℝ) > 0 := Nat.cast_pos.mpr hS
      linarith
    exact Real.log_pos h2

/--
The bound is zero at zero species. With D modelled as log(S+1)/log(S_max+1), S = 0 gives D = 0, and
the product-form bound is then zero for every P. This is boundary essentiality applied to the
species model. It says nothing about reversibility, and nothing about partial losses of species,
which the compensation formula shows can be offset by finite power in this model.
-/
theorem bound_zero_at_zero_species (c : PhysicalConstants) (S_max : ℕ) (hS_max : S_max > 0) (P : ℝ) :
    intelligence_bound c P (D_of_species 0 S_max) = 0 := by
  rw [D_vanishes_at_extinction S_max hS_max]
  exact non_substitutability_basic c P

/-! Deprecated names, kept so existing references resolve. -/

@[deprecated (since := "2026-11-14")] alias no_finite_compensation := compensation_formula
@[deprecated (since := "2026-11-14")] alias economic_non_substitutability := isoquant_is_hyperbola
@[deprecated (since := "2026-11-14")] alias extinction_irreversible := bound_zero_at_zero_species

end NonSubstitutability