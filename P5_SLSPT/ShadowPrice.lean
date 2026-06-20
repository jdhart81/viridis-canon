import Mathlib

/-! # Shadow Price Function — Thermodynamic Speed Limit Theory

The shadow price function is `p(σ) = d² / (A · τ · σ�)` where `d, A, τ, σ` are positive reals.
We prove four key properties establishing the quadratic divergence (Performance Cliff Theorem).
-/

/-
Theorem 1: The shadow price function is strictly decreasing in σ.
-/
theorem shadow_price_strict_decreasing
    (d A tau sigma1 sigma2 : ℝ)
    (hd : 0 < d) (hA : 0 < A) (htau : 0 < tau)
    (hs1 : 0 < sigma1) (hs12 : sigma1 < sigma2) :
    d ^ 2 / (A * tau * sigma2 ^ 2) < d ^ 2 / (A * tau * sigma1 ^ 2) := by
  gcongr

/-
Theorem 2: The shadow price diverges as σ → 0⁺.
-/
theorem shadow_price_diverges
    (d A tau : ℝ) (hd : 0 < d) (hA : 0 < A) (htau : 0 < tau) :
    ∀ M : ℝ, ∃ δ > 0, ∀ sigma : ℝ, 0 < sigma → sigma < δ →
    M < d ^ 2 / (A * tau * sigma ^ 2) := by
  intro M;
  -- Choose δ = d / sqrt(max 1 (M * A * tau)).
  use d / Real.sqrt (max 1 (M * A * tau));
  refine' ⟨ by positivity, fun sigma hsigma₁ hsigma₂ ↦ _ ⟩;
  rw [ lt_div_iff₀ ( by positivity ) ] at *;
  nlinarith [ show 0 ≤ sigma * Real.sqrt ( Max.max 1 ( M * A * tau ) ) by positivity, show M * A * tau ≤ Max.max 1 ( M * A * tau ) by exact le_max_right _ _, Real.mul_self_sqrt ( show 0 ≤ Max.max 1 ( M * A * tau ) by positivity ) ]

/-
Theorem 3: Quadratic scaling law — x² · (1/x²) = 1 for x ≠ 0.
-/
theorem quadratic_scaling (x : ℝ) (hx : x ≠ 0) :
    x ^ 2 * (1 / x ^ 2) = 1 := by
  exact mul_div_cancel₀ _ ( pow_ne_zero 2 hx )

/-
Theorem 4: Shadow price lower bound — 1/(2ε)² < 1/ε² for 0 < ε < 1.
    This is actually FALSE as stated: 1/(2ε)² = 1/(4ε²) < 1/ε² implies 1/4 < 1,
    which is true. So it IS true. Let me verify: 1/(2ε)² means 1/((2ε)²) = 1/(4ε²).
    And 1/(4ε²) < 1/ε² since 4ε² > ε² for έ > 0. Yes, this is correct.
-/
theorem shadow_price_lower_bound (epsilon : ℝ) (hpos : 0 < epsilon) (_hlt : epsilon < 1) :
    1 / (2 * epsilon) ^ 2 < 1 / epsilon ^ 2 := by
  gcongr ; nlinarith