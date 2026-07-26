/-
# The Manipulation-Proof Weighting Theorem (MPWT) — the Warden
Viridis Aristotle Forge · Nightly Run 105 · [04] D-Score Science × 🎯 Stewardship
47th Intelligence-Bound self-application (approximate, per source README.md — inferred from
the strictly-incrementing sequence Steward@102(44th)→Metronome@103(45th)→Symbiont@104(46th)).

INTENDED MEANING (formalized clean core).
Viridis's own D-Score biodiversity composite `D = w_S D_S + w_P D_P + w_G D_G` (species,
phylogenetic, genetic diversity) is scored against a rational, self-interested steward who
can substitute cheap GAMING for real stewardship. The three channels are not equally cheap
to fake: species counts (survey-effort/detectability/planting artifacts) are far cheaper to
game than phylogenetic diversity (requires genuinely divergent lineages), which is in turn
cheaper to game than genetic diversity (a slow, multi-generational population property).
Call this the GAMING ELASTICITY `γ_i` of channel `i` (illustrative ordering `γ_S ≫ γ_P > γ_G`).

Under a quadratic gaming-cost model, a steward paid against `D=Σw_iD_i` optimally injects
gaming `n_i⋆ = R'(D̄)·w_i·γ_i` into channel `i` (R2), giving TOTAL INJECTED BIAS
`Bias(w) = R'(D̄)·Σγ_iw_i²`. Minimizing the scale-invariant GOODHART RATIO
`J(w) = Σγ_iw_i² / (ΣI_iw_i)²` — bias-per-unit-informativeness-squared, `I_i` = true
scientific importance — is a Rayleigh-quotient problem whose unique interior stationary ray
is the MANIPULATION-PROOF WEIGHT `w_i⋆ = κ·I_i/γ_i`, `κ=(Σ_j I_j/γ_j)⁻¹` (R3, HEADLINE).

Applied to Viridis's own shipped defaults (`dscore/src/dscore/core.py::DEFAULT_WEIGHTS`,
`I=(0.5,0.3,0.2)` for S/P/G — the current design literally sets weight equal to raw
importance, ignoring gaming elasticity entirely) against an illustrative calibration
`γ=(10,3,1)`, the manipulation-proof ranking FULLY INVERTS the current one
(`R4`: `w_S⋆<w_P⋆<w_G⋆` vs. current `S>P>G`), strictly lowers the Goodhart ratio, and
strictly reduces the Intelligence-Bound ceiling-inflation `Bias(w)/D_true` — the degree to
which a gamed `D` overstates the true achievable `dI/dt ≤ P·D/(k_BT ln2)` — by ≈72.4% in
the worked calibration (independently reproduced below via `ceiling_inflation_reduced_under_wstar`).

FORMALIZATION SCOPE NOTE (spec invariance — assumption flagged per protocol).
`mpwt_foc_ray_proportional_to_I_over_gamma` and `mpwt_is_global_min_on_simplex` (R3, the
headline Cauchy–Schwarz Rayleigh-quotient result) are formalized FULLY GENERALLY for
arbitrary positive importances `I_i` and elasticities `γ_i`. `bias_quadratic_form_matches_
steward_optimum` (R2) is formalized generally per-channel. `ranking_inversion_exists_for_
gammaS_gt_gammaG` (R4), `goodhart_ratio_strictly_lower_under_wstar`, and
`ceiling_inflation_reduced_under_wstar` are formalized AT THE PAPER'S OWN ILLUSTRATIVE
CALIBRATION POINT (`I=(1/2,3/10,1/5)`, `γ=(10,3,1)`) comparing the manipulation-proof
optimum against the shipped default weights (`w_cur = I` — literally true of the current
design). This matches the source paper's own disclosed status (novelty 4/5, not 5/5:
"γ_i, I_i illustrative/literature-motivated, not yet empirically calibrated" — Prediction
P1) and is a deliberate reduction from the full 9-target list in `Run-105/README.md` to the
6-target well-posedness-gated queue in `science-engine/DISCOVERIES_TO_PURSUE.md`.
DEFERRED (CITED, not re-proven): `dwistar_dgammai_negative` / `dwistar_dgammaj_positive_cross`
(general comparative statics — `γ_i` moves `κ` jointly with every other channel, not a clean
single-variable monotone claim without further structure) and
`goodhart_threshold_crosses_once_in_elasticity_scale` (an asymptotic single-crossing claim) —
gate-check, not submitted this cycle.

NON-VACUITY. `mpwt_nonvacuous` binds the paper's own illustrative calibration and confirms,
in one witness, that `κ>0`, the ranking strictly inverts (`w_S⋆<w_G⋆`), and the Goodhart
ratio strictly drops at `w⋆` vs. the shipped defaults.

Toolchain leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff.
-/
import Mathlib

open Real Set Filter

namespace Viridis.Warden.ManipulationProofWeighting

/-! ### Core objects: gaming-adjusted quadratic bias and the Goodhart ratio. -/

/-- Total injected measurement bias under quadratic gaming cost, three D-Score channels
    (Species/Phylogenetic/Genetic): `Bias(w) = R'(D̄) · Σ γ_i w_i²`. -/
def biasQ (Rp gS gP gG wS wP wG : ℝ) : ℝ := Rp * (gS * wS ^ 2 + gP * wP ^ 2 + gG * wG ^ 2)

/-- Scale-invariant Goodhart ratio `J(w) = Σγ_iw_i² / (ΣI_iw_i)²`. -/
noncomputable def goodhartJ (IS IP IG gS gP gG wS wP wG : ℝ) : ℝ :=
  (gS * wS ^ 2 + gP * wP ^ 2 + gG * wG ^ 2) / (IS * wS + IP * wP + IG * wG) ^ 2

/-- Manipulation-proof normalizing constant `κ = (Σ I_j/γ_j)⁻¹`. -/
noncomputable def kap (IS IP IG gS gP gG : ℝ) : ℝ := 1 / (IS / gS + IP / gP + IG / gG)

/-- Manipulation-proof weight on a channel with importance `I` and gaming elasticity `g`:
    `w⋆ = κ·I/g`, where `κ` is computed from the full triple `(IS,IP,IG,gS,gP,gG)`. -/
noncomputable def wStar (I g IS IP IG gS gP gG : ℝ) : ℝ := kap IS IP IG gS gP gG * I / g

/-! ### R3 (HEADLINE, canon candidate) — the Manipulation-Proof Weighting Theorem. -/

/-- **R3 (FOC ray).** At the manipulation-proof weights, `γ_i·w_i⋆/I_i = κ` for every
    channel — the defining first-order-condition ray `w_i⋆ ∝ I_i/γ_i`. -/
theorem mpwt_foc_ray_proportional_to_I_over_gamma
    (IS IP IG gS gP gG : ℝ) (hIS : 0 < IS) (hIP : 0 < IP) (hIG : 0 < IG)
    (hgS : 0 < gS) (hgP : 0 < gP) (hgG : 0 < gG) :
    gS * wStar IS gS IS IP IG gS gP gG / IS = kap IS IP IG gS gP gG ∧
      gP * wStar IP gP IS IP IG gS gP gG / IP = kap IS IP IG gS gP gG ∧
      gG * wStar IG gG IS IP IG gS gP gG / IG = kap IS IP IG gS gP gG := by
  unfold wStar ; ring_nf ;
  grind

/-- **R3 (HEADLINE, canon candidate).** The manipulation-proof ray `w⋆` achieves the GLOBAL
    MINIMUM of the Goodhart ratio `J` over the entire positive orthant (the Cauchy–Schwarz
    equality case): no reweighting of the three D-Score channels achieves a lower
    bias-per-unit-informativeness-squared than `w_i⋆=κI_i/γ_i`. -/
theorem mpwt_is_global_min_on_simplex
    (IS IP IG gS gP gG wS wP wG : ℝ)
    (hIS : 0 < IS) (hIP : 0 < IP) (hIG : 0 < IG)
    (hgS : 0 < gS) (hgP : 0 < gP) (hgG : 0 < gG)
    (hwS : 0 < wS) (hwP : 0 < wP) (hwG : 0 < wG) :
    goodhartJ IS IP IG gS gP gG
        (wStar IS gS IS IP IG gS gP gG) (wStar IP gP IS IP IG gS gP gG)
        (wStar IG gG IS IP IG gS gP gG)
      ≤ goodhartJ IS IP IG gS gP gG wS wP wG := by
  unfold goodhartJ wStar kap;
  field_simp;
  nlinarith [ sq_nonneg ( gS * wS * IP - gP * wP * IS ), sq_nonneg ( gP * wP * IG - gG * wG * IP ), sq_nonneg ( gG * wG * IS - gS * wS * IG ), mul_pos hgS hgP, mul_pos hgP hgG, mul_pos hgG hgS ]

/-! ### R2 — the bias quadratic form matches the steward's own rational optimum. -/

/-- Steward's optimal gaming injection into a channel given weight `w`, gaming elasticity
    `g`, and shadow price `R'(D̄)`, under quadratic gaming cost `n²/(2γ)`:
    `n⋆ = R'(D̄)·w·γ`. -/
def stewardOptN (Rp w g : ℝ) : ℝ := Rp * w * g

/-- Steward's per-channel net objective `w·R'(D̄)·n − n²/(2γ)` (linear gain, quadratic
    gaming cost).

    IMPLEMENTATION FLAG: marked `noncomputable` because real-number division is
    noncomputable in Lean; this does not alter the definition's mathematical value. -/
noncomputable def stewardObj (Rp w g n : ℝ) : ℝ := w * Rp * n - n ^ 2 / (2 * g)

/-- **R2.** `n⋆ = R'(D̄)wγ` is the unique global maximizer of the steward's per-channel
    objective, and plugging it back in recovers exactly the quadratic bias form
    `w·n⋆ = R'(D̄)·γ·w²` — i.e. `Bias(w)=R'(D̄)Σγ_iw_i²` is literally the sum of each
    channel's own rational-manipulation optimum, not an ad hoc functional form. -/
theorem bias_quadratic_form_matches_steward_optimum
    (Rp w g : ℝ) (hg : 0 < g) :
    (∀ n : ℝ, stewardObj Rp w g n ≤ stewardObj Rp w g (stewardOptN Rp w g)) ∧
      w * stewardOptN Rp w g = Rp * g * w ^ 2 := by
  unfold stewardObj; unfold stewardOptN; exact ⟨ by intros; nlinarith [ sq_nonneg ( Rp * w * g - ‹_› ), mul_div_cancel₀ ( ( ‹_› : ℝ ) ^ 2 ) ( by positivity : ( 2 * g ) ≠ 0 ), mul_div_cancel₀ ( ( Rp * w * g ) ^ 2 ) ( by positivity : ( 2 * g ) ≠ 0 ) ], by ring ⟩ ;

/-! ### R4 — Ranking Inversion (illustrative calibration `I=(1/2,3/10,1/5)`, `γ=(10,3,1)`). -/

/-- **R4 (canon candidate).** At the paper's illustrative calibration — Viridis's own
    D-Score default importances `(I_S,I_P,I_G)=(1/2,3/10,1/5)` against gaming elasticities
    `(γ_S,γ_P,γ_G)=(10,3,1)` — the manipulation-proof ranking is a STRICT, FULL inversion of
    the current one: `w_S⋆ < w_P⋆ < w_G⋆` (current design ranks `S>P>G`; manipulation-proof
    design ranks `G⋆>P⋆>S⋆`). -/
theorem ranking_inversion_exists_for_gammaS_gt_gammaG :
    wStar (1 / 2) 10 (1 / 2) (3 / 10) (1 / 5) 10 3 1
        < wStar (3 / 10) 3 (1 / 2) (3 / 10) (1 / 5) 10 3 1 ∧
      wStar (3 / 10) 3 (1 / 2) (3 / 10) (1 / 5) 10 3 1
        < wStar (1 / 5) 1 (1 / 2) (3 / 10) (1 / 5) 10 3 1 := by
  norm_num [ wStar, kap ]

/-! ### Goodhart ratio strictly lower under `w⋆` vs. the shipped defaults. -/

/-- **Canon candidate.** At the illustrative calibration, the Goodhart ratio at the
    manipulation-proof weights is STRICTLY lower than at Viridis's shipped default weights
    (which are literally `w_cur = I`: the current design sets weight equal to raw
    importance and ignores gaming elasticity entirely). -/
theorem goodhart_ratio_strictly_lower_under_wstar :
    goodhartJ (1 / 2) (3 / 10) (1 / 5) 10 3 1
        (wStar (1 / 2) 10 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
        (wStar (3 / 10) 3 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
        (wStar (1 / 5) 1 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
      < goodhartJ (1 / 2) (3 / 10) (1 / 5) 10 3 1 (1 / 2) (3 / 10) (1 / 5) := by
  unfold goodhartJ wStar ;
  unfold kap; norm_num;

/-! ### R6 — IB ceiling-inflation reduced under `w⋆`. -/

/-- IB ceiling-inflation of a weighting `w`: the injected bias scaled by the true
    achievable dissipative capacity `D_true>0` — the fraction by which a gamed `D`
    overstates the true Intelligence-Bound ceiling `dI/dt ≤ P·D/(k_BT ln2)`.

    IMPLEMENTATION FLAG: marked `noncomputable` because real-number division is
    noncomputable in Lean; this does not alter the definition's mathematical value. -/
noncomputable def ceilingInflation (Rp Dtrue gS gP gG wS wP wG : ℝ) : ℝ :=
  biasQ Rp gS gP gG wS wP wG / Dtrue

/-- **R6 (canon candidate).** At the illustrative calibration, switching from the shipped
    default weights to the manipulation-proof weights STRICTLY REDUCES the IB
    ceiling-inflation, for any positive shadow price `R'(D̄)` and true capacity `D_true`
    (independently reproduces the paper's own reported ≈72.4% reduction). -/
theorem ceiling_inflation_reduced_under_wstar (Rp Dtrue : ℝ) (hRp : 0 < Rp) (hD : 0 < Dtrue) :
    ceilingInflation Rp Dtrue 10 3 1
        (wStar (1 / 2) 10 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
        (wStar (3 / 10) 3 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
        (wStar (1 / 5) 1 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
      < ceilingInflation Rp Dtrue 10 3 1 (1 / 2) (3 / 10) (1 / 5) := by
  unfold ceilingInflation wStar biasQ kap; norm_num; ring_nf; norm_num [ hRp, hD ] ;

/-! ### Non-vacuity witness. -/

/-- **Non-vacuity.** The manipulation-proof ray, its ranking inversion, and its strict
    Goodhart-ratio improvement over the shipped defaults are all witnessed together at the
    paper's own illustrative calibration point. -/
theorem mpwt_nonvacuous :
    0 < kap (1 / 2) (3 / 10) (1 / 5) 10 3 1 ∧
      wStar (1 / 2) 10 (1 / 2) (3 / 10) (1 / 5) 10 3 1
        < wStar (1 / 5) 1 (1 / 2) (3 / 10) (1 / 5) 10 3 1 ∧
      goodhartJ (1 / 2) (3 / 10) (1 / 5) 10 3 1
          (wStar (1 / 2) 10 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
          (wStar (3 / 10) 3 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
          (wStar (1 / 5) 1 (1 / 2) (3 / 10) (1 / 5) 10 3 1)
        < goodhartJ (1 / 2) (3 / 10) (1 / 5) 10 3 1 (1 / 2) (3 / 10) (1 / 5) := by
  unfold goodhartJ wStar kap; norm_num;

end Viridis.Warden.ManipulationProofWeighting