/-
  HarmonicValuation.lean — Viridis Aristotle Forge — STAGING SKELETON (NOT SUBMITTED)
  Nightly Run 059 — The Harmonic Valuation Theorem (HVT), integrability core.

  CLAIM (finding §3.3 / line 145): a D-Capital price 1-form ω admits a unique,
  path-independent valuation potential V (ω is EXACT, the market is
  arbitrage-free) IFF ω is CLOSED (dω = 0) — the Poincaré-lemma instance on a
  "simply-connected D-Capital chart":  dω = 0 ↔ ∃ V, ω = dV.

  WHY STAGED (not auto-submitted): the precise statement is well-posed, but the
  faithful Lean encoding of "simply-connected D-Capital chart" forces a
  load-bearing modeling choice the forge will not make silently:

    (A) CONVEX / star-shaped coordinate chart in a real inner-product space E
        (the standard Poincaré-lemma domain). Closedness = symmetric Jacobian
        (∂ⱼpᵢ = ∂ᵢpⱼ); exactness = ∃ V, ∀ x ∈ U, ∇V x = p x. This is a faithful
        *instance* of the claim (a chart can always be taken star-shaped), and
        is tractable from Mathlib's calculus (line-integral primitive
        V(x) = ∫₀¹ ⟨p(a + t(x−a)), x−a⟩ dt + Clairaut symmetry).  ← RECOMMENDED.

    (B) GENERAL simply-connected domain / de-Rham H¹(U)=0 statement: requires
        algebraic-topology machinery Mathlib does not currently package as a
        ready 1-form Poincaré lemma. High risk of non-termination within the
        Aristotle budget, or of the prover silently weakening the hypothesis to
        a contractible/convex set (a flagged tightening).

  The two differ in *what is claimed* (a calculus result vs. a topological
  theorem), so per the well-posedness gate + "flag ambiguity before building",
  the forge stages this for a one-word confirm. Confirm (A) and the next MODE-S
  slot proves it.

  ACCEPTANCE (when submitted): 0 sorry; axioms ⊆ {propext, Classical.choice,
  Quot.sound}; both directions non-vacuous (the closed⟹exact direction must
  genuinely use convexity — it is false on non-simply-connected U, e.g. the
  punctured plane with the angle form, so the hypothesis is load-bearing).
  Toolchain leanprover/lean4:v4.28.0, Mathlib pin 8f9d9cff.
-/
import Mathlib

open scoped InnerProductSpace
open Set

namespace Viridis.DCapital.HVT

-- NOTE (flagged): `HasGradientAt` is defined via the Riesz isometry `toDual`, which
-- requires the inner product space to be complete (a Hilbert space).  We therefore add
-- the instance assumption `[CompleteSpace E]`; without it the theorem statement below does
-- not even type-check (`failed to synthesize CompleteSpace E`).  This is a typeclass
-- hypothesis only: it does not weaken the conclusion, and convexity remains load-bearing.
variable {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E] [CompleteSpace E]

/-
Clairaut / exact ⟹ closed direction.  If the price field `p` is the gradient of a
    potential `V` on the open set `U`, then `fderiv ℝ p` is symmetric on `U` (this is the
    symmetry of the second derivative of `V`).
-/
lemma exact_implies_closed
    (U : Set E) (hU : IsOpen U)
    (p : E → E) (hp : ∀ x ∈ U, DifferentiableAt ℝ p x)
    (h : ∃ V : E → ℝ, ∀ x ∈ U, HasGradientAt V (p x) x) :
    ∀ x ∈ U, ∀ u v : E, ⟪fderiv ℝ p x u, v⟫_ℝ = ⟪fderiv ℝ p x v, u⟫_ℝ := by
  -- Fix `x ∈ U` and `u v : E`.
  intro x hx u v
  obtain ⟨V, hV⟩ := h;
  have h_symm : (fderiv ℝ (fun y => (InnerProductSpace.toDual ℝ E) (p y)) x) u v = (fderiv ℝ (fun y => (InnerProductSpace.toDual ℝ E) (p y)) x) v u := by
    -- Apply the symmetry of the second derivative to the function $f(y) = (InnerProductSpace.toDual ℝ E) (p y)$.
    have h_symm : ∀ᶠ y in nhds x, HasFDerivAt V ((InnerProductSpace.toDual ℝ E) (p y)) y := by
      filter_upwards [ hU.mem_nhds hx ] with y hy using by simpa only [ hasGradientAt_iff_hasFDerivAt ] using hV y hy;
    apply_rules [ second_derivative_symmetric_of_eventually ];
    exact DifferentiableAt.hasFDerivAt ( by exact DifferentiableAt.comp x ( by exact ( InnerProductSpace.toDual ℝ E ).differentiableAt ) ( hp x hx ) );
  convert h_symm using 1;
  · erw [ fderiv_comp x ( show DifferentiableAt ℝ ( InnerProductSpace.toDual ℝ E ) ( p x ) from ( InnerProductSpace.toDual ℝ E ).differentiableAt ) ( hp x hx ) ] ; simp +decide;
    erw [ LinearIsometryEquiv.fderiv ] ; aesop;
  · rw [ fderiv ];
    rw [ fderivWithin_univ, show ( fun y => ( InnerProductSpace.toDual ℝ E ) ( p y ) ) = ( InnerProductSpace.toDual ℝ E ) ∘ p from rfl, fderiv_comp ] <;> norm_num [ hp x hx ];
    · erw [ LinearIsometryEquiv.fderiv ] ; aesop;
    · exact ( InnerProductSpace.toDual ℝ E ).differentiableAt

/-
Poincaré / closed ⟹ exact direction.  On a *convex* open chart, a symmetric (closed)
    price field is a gradient field.  Convexity is load-bearing: the result is false on
    non-simply-connected charts (e.g. the punctured plane with the angle form).
-/
lemma closed_implies_exact
    (U : Set E) (hU : IsOpen U) (hUc : Convex ℝ U) (_hUne : U.Nonempty)
    (p : E → E) (hp : ∀ x ∈ U, DifferentiableAt ℝ p x)
    (h : ∀ x ∈ U, ∀ u v : E, ⟪fderiv ℝ p x u, v⟫_ℝ = ⟪fderiv ℝ p x v, u⟫_ℝ) :
    ∃ V : E → ℝ, ∀ x ∈ U, HasGradientAt V (p x) x := by
  convert Convex.exists_forall_hasFDerivAt_of_fderiv_symmetric hUc hU ( show DifferentiableOn ℝ ( fun x => ( InnerProductSpace.toDual ℝ E ) ( p x ) ) U from ?_ ) ( show ∀ a ∈ U, ∀ x y, fderiv ℝ ( fun x => ( InnerProductSpace.toDual ℝ E ) ( p x ) ) a x y = fderiv ℝ ( fun x => ( InnerProductSpace.toDual ℝ E ) ( p x ) ) a y x from ?_ );
  · exact fun x hx => DifferentiableAt.differentiableWithinAt ( by exact DifferentiableAt.comp x ( by exact ( InnerProductSpace.toDual ℝ E ).differentiableAt ) ( hp x hx ) );
  · intro a ha x y;
    convert h a ha x y using 1;
    · convert ( HasFDerivAt.fderiv ( HasFDerivAt.comp a ( InnerProductSpace.toDual ℝ E |> LinearIsometryEquiv.hasFDerivAt ) ( hp a ha |> DifferentiableAt.hasFDerivAt ) ) ) |> congr_arg ( fun f => f x y ) using 1;
    · convert ( HasFDerivAt.fderiv ( HasFDerivAt.comp a ( InnerProductSpace.toDual ℝ E |> LinearIsometryEquiv.hasFDerivAt ) ( hp a ha |> DifferentiableAt.hasFDerivAt ) ) ) |> congr_arg ( fun f => f y x ) using 1

/-- Representative encoding (A): on a convex open chart `U`, a C¹ price field
    `p` (components of the 1-form ω = Σ pᵢ dxᵢ) is a GRADIENT field (exact:
    a unique-up-to-constant valuation potential `V` exists) IFF its derivative
    is symmetric (closed: dω = 0).  NON-VACUITY: the ⟸ direction is the genuine
    Poincaré content and requires `Convex ℝ U`; it fails on non-simply-connected
    charts. The ⟹ direction is Clairaut symmetry of second derivatives. -/
theorem closed_iff_exact_on_convex_chart
    (U : Set E) (hU : IsOpen U) (hUc : Convex ℝ U) (hUne : U.Nonempty)
    (p : E → E) (hp : ∀ x ∈ U, DifferentiableAt ℝ p x) :
    (∀ x ∈ U, ∀ u v : E, ⟪fderiv ℝ p x u, v⟫_ℝ = ⟪fderiv ℝ p x v, u⟫_ℝ)
      ↔ (∃ V : E → ℝ, ∀ x ∈ U, HasGradientAt V (p x) x) :=
  ⟨fun hclosed => closed_implies_exact U hU hUc hUne p hp hclosed,
   fun hexact => exact_implies_closed U hU p hp hexact⟩

end Viridis.DCapital.HVT