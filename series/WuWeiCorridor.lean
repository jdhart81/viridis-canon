/-
===============================================================================
  The Wu-Wei Corridor Design Theorem (WCDT) — clean core
  Lean 4 / Mathlib formalization.  Viridis LLC.  For submission to Aristotle.
===============================================================================

CONTEXT (nightly Run 036, wu-wei-corridor-design).
  A conservation corridor must simultaneously satisfy three *pillar* feasibility
  constraints — geometric (C_geom), measurement (C_meas), and decoherence
  (C_decoh) — on the Symbiotic Stewardship Manifold M_symb.  The "wu-wei"
  (minimum-force) design is, by definition (finding Invariant I3), the unique
  fixed point of the simultaneous Bregman / Censor–Elfving multiprojection
  iteration whose fixed-point set is the common feasible region.  Pierra's
  product-space reformulation makes the combined multiprojection operator a
  firmly-nonexpansive averaged map; under the standard Bregman–Legendre
  contraction hypothesis (finding Invariant I5) it is a strict contraction, so
  Banach's theorem delivers existence, uniqueness, and Picard convergence of the
  wu-wei corridor.

WHAT IS PROVEN HERE (the clean core — no `sorry`, axioms ⊆ Mathlib):

  Abstracting the multiprojection operator as a contraction `T` (Lipschitz
  constant `K < 1`) on a complete nonempty metric space `E` (the model for
  M_symb with the Fisher–Rao metric):

  1. WCDT_unique_fixed_point  — the wu-wei corridor EXISTS and is UNIQUE:
        `∃! c, T c = c`.                                  (Censor–Elfving limit)
  2. WCDT_iteration_converges — the multiprojection Picard iteration converges
        to that corridor from any starting design `x₀`.   (constructive design)
  3. WCDT_corridor_feasible   — the wu-wei corridor lies in EVERY pillar
        feasibility set simultaneously (the wu-wei = no-forcing property):
        if the operator maps into `⋂ i, C i`, the fixed point is in all `C i`.
  4. WCDT_nonvacuous          — the hypothesis class is genuinely inhabited by a
        non-degenerate contraction with a real unique fixed point, so 1–3 are
        NOT vacuous.

THE HONEST BOUNDARY (the input, NOT formalized here):
  WHICH Bregman–Legendre generator and metric (Fisher–Rao vs. Euclidean) make
  the concrete simultaneous-multiprojection operator a strict contraction with a
  given factor `K` is the analytic content supplied as the hypothesis
  `ContractingWith K T` (finding Invariants I4–I5).  Mathlib lacks Bregman
  projection / Fisher–Rao geometry, so that analysis is the input; this file
  proves everything downstream of it — the Censor–Elfving existence /
  uniqueness / convergence core that the corridor-design product depends on.
  The throughput-scaling corollary (`SqrtScaling_from_WCDT`, Onsager–Machlup)
  is deliberately out of scope for this clean core.
===============================================================================
-/
import Mathlib

open Filter Topology

namespace Viridis.HDFM.WuWeiCorridor

/--
**WCDT — existence and uniqueness of the wu-wei corridor.**
The simultaneous multiprojection operator `T`, being a strict contraction
(`ContractingWith K T`) on the complete nonempty manifold model `E`, has a
unique fixed point: the wu-wei corridor design exists and is unique.
-/
theorem WCDT_unique_fixed_point
    {E : Type*} [MetricSpace E] [CompleteSpace E] [Nonempty E]
    {K : NNReal} {T : E → E} (hT : ContractingWith K T) :
    ∃! c : E, T c = c := by
  convert hT.exists_fixedPoint;
  constructor <;> intro h;
  · convert hT.exists_fixedPoint;
  · obtain ⟨ c, hc ⟩ := h ( Classical.arbitrary E ) ( by simp +decide [ edist_dist ] );
    refine' ⟨ c, hc.1, _ ⟩;
    intro y hy; have := hT.dist_le_mul y c; simp_all +decide [ Function.IsFixedPt ] ;
    exact dist_le_zero.mp ( by nlinarith [ show ( K : ℝ ) < 1 from hT.1, show ( 0 : ℝ ) ≤ dist y c from dist_nonneg ] )

/--
**WCDT — convergence of the design iteration.**
From any initial corridor `x₀`, the Picard / Censor–Elfving iterates `T^[n] x₀`
converge to the (unique) wu-wei corridor `c`.  This is the constructive content:
the design is computable as the limit of the multiprojection sweep.
-/
theorem WCDT_iteration_converges
    {E : Type*} [MetricSpace E] [CompleteSpace E] [Nonempty E]
    {K : NNReal} {T : E → E} (hT : ContractingWith K T) (x₀ : E) :
    ∃ c : E, T c = c ∧ Tendsto (fun n => T^[n] x₀) atTop (𝓝 c) := by
  have := @WCDT_unique_fixed_point E;
  have := @this _ _ _ K T hT; rcases this with ⟨ c, hc ⟩ ; use c; refine ⟨ hc.1, ?_ ⟩;
  convert hT.tendsto_iterate_fixedPoint x₀ using 1;
  rw [ hc.2 _ ( hT.fixedPoint_isFixedPt ) ]

/--
**WCDT — the wu-wei corridor is simultaneously feasible (no-forcing).**
If the multiprojection operator `T` maps every design into the common feasible
region `⋂ i, C i` (the three pillar sets), then the wu-wei corridor — its fixed
point — lies in every pillar set `C i` at once.  This is the formal "wu-wei =
all constraints met without forcing any single axis" property.
-/
theorem WCDT_corridor_feasible
    {E : Type*} [MetricSpace E] [CompleteSpace E] [Nonempty E] {ι : Type*}
    {K : NNReal} {T : E → E} (hT : ContractingWith K T)
    {C : ι → Set E} (hmap : ∀ x, T x ∈ ⋂ i, C i) :
    ∃ c : E, T c = c ∧ ∀ i, c ∈ C i := by
  obtain ⟨ c, hc ⟩ := WCDT_unique_fixed_point hT;
  exact ⟨ c, hc.1, fun i => by simpa [ hc.1 ] using Set.mem_iInter.mp ( hmap c ) i ⟩

/--
**Non-vacuity witness.**
The contraction hypothesis of `WCDT_unique_fixed_point` is inhabited by a
genuine, non-degenerate contraction (`x ↦ x/2` on `ℝ`, factor `1/2 < 1`) whose
unique fixed point is a real point.  Hence the WCDT theorems above are not
vacuously true.
-/
theorem WCDT_nonvacuous :
    ∃ (T : ℝ → ℝ) (K : NNReal), ContractingWith K T ∧ ∃! c : ℝ, T c = c := by
  refine' ⟨ fun x => x / 2, 1 / 2, _, _ ⟩;
  · refine' ⟨ by norm_num, _ ⟩;
    norm_num [ lipschitzWith_iff_norm_sub_le ];
    grind;
  · exact ⟨ 0, by norm_num, by intro x hx; linear_combination hx.symm * 2 ⟩

end Viridis.HDFM.WuWeiCorridor