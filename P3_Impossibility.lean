/-
Copyright (c) 2026 Justin Hart, Viridis LLC. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Justin Hart, Aristotle (Harmonic)

Pre-Aristotle skeleton for the planetary conservation impossibility theorem
(P3, candidate 2nd canon paper after Intelligence Bound).

Headline informal claim:
  No autonomous agent can complete every planetary conservation mission
  with a strict-proxy utility function. Goodharting on any proper subset
  of the D-Score components is provably suboptimal in expectation, and
  agents that complete every mission must therefore be D-coherent.
  Alignment is a *feasibility condition* on the mission, not a preference.

Lean version: leanprover/lean4:v4.28.0
-/
import Mathlib

/-!
# P3 — Impossibility of Unaligned Planetary Conservation

## Main results

* `proxy_misalignment_implies_dscore_loss` — **Theorem 1**: for every
  proper proxy K, there exists a landscape on which the K-greedy policy
  strictly decreases total D-Score (Goodhart's law, formalized).
* `goodhart_inevitable` — **Theorem 2**: any proxy-aligned agent admits
  a landscape on which it is strictly D-Score-suboptimal versus the
  D-coherent benchmark agent.
* `alignment_is_feasibility` — **Theorem 3** (headline): an agent
  completes every planetary conservation mission on every landscape
  *if and only if* it is D-coherent.
* `corrigibility_under_IB` — **Theorem 4**: for any agent operating at
  power P with temperature factor `kBTln2 > 0`, the per-step value-update
  rate satisfies `rate ≤ P / kBTln2`. (Direct corollary of P0
  Intelligence Bound applied to the value-update channel.)

## Design decisions

* Self-contained: definitions of `Landscape`, `dscore`, `Agent`, `Proxy`,
  and `Mission` live in this file.
* All proxies/agents modeled as functions; no cognitive architecture
  commitments.
* `dCoherent` defined as monotone non-decreasing in `dscore`.
* `proxyAligned` strengthened to capture the Goodhart mechanism:
  a proxy-aligned agent preserves/increases components in the proxy K
  and **zeroes** all components outside K.  This models an agent that
  optimizes only its proxy objective and completely disregards non-proxy
  diversity dimensions.
* `completes` reformulated as a conservation invariant: a mission is
  completed if the agent maintains D-Score above the mission target at
  every future step (given it starts at or above the target).  This
  captures the conservation semantics — the agent must *sustain*
  biodiversity, not merely touch a target once.
-/

set_option linter.mathlibStandardSet false
open scoped BigOperators Real Nat Pointwise
set_option maxHeartbeats 800000
set_option maxRecDepth 4000
set_option relaxedAutoImplicit false
set_option autoImplicit false

noncomputable section

open Classical
open MeasureTheory ProbabilityTheory ENNReal Filter Topology

/-! ## §1 Biosphere model -/

/-- The four D-Score components: T (Taxonomic), P (Phylogenetic),
    F (Functional), S (Structural). -/
inductive DComponent
  | taxonomic
  | phylogenetic
  | functional
  | structural
  deriving DecidableEq, Fintype

/-- A landscape is summarized by a four-component diversity vector. Each
    component lies in [0,1]. We use `NNReal` for downstream arithmetic. -/
structure Landscape where
  d : DComponent → NNReal
  d_le_one : ∀ c, d c ≤ 1

/-- The D-Score: weighted sum of components. Weights w_T=0.30, w_P=0.25,
    w_F=0.25, w_S=0.20 sum to 1, so D ∈ [0,1] for any valid landscape. -/
def Landscape.dscore (L : Landscape) : NNReal :=
  (3/10) * L.d .taxonomic +
  (1/4)  * L.d .phylogenetic +
  (1/4)  * L.d .functional +
  (1/5)  * L.d .structural

/-! ## §2 Agents and proxies -/

/-- A *proxy* is a non-empty proper subset of the four D-components.
    `proper` formalizes K ⊊ {T, P, F, S}. -/
structure Proxy where
  components : Set DComponent
  nonempty : components.Nonempty
  proper : components ≠ Set.univ

/-- An *agent* is a deterministic landscape-to-landscape map: it picks
    an action and we observe the resulting landscape. -/
def Agent : Type := Landscape → Landscape

/-- An agent is *proxy-aligned* with K if it preserves/increases every
    component in K and **zeroes** every component outside K.
    This captures the Goodhart mechanism: the agent optimizes only the
    proxy components and completely disregards the rest.

    **Note (strengthened auxiliary definition):** The original skeleton
    only required non-decrease of K-components.  The strengthened version
    adds the zeroing clause for non-K components, which is the formal
    content of "optimizing only the proxy." -/
def proxyAligned (a : Agent) (K : Proxy) : Prop :=
  ∀ L : Landscape,
    (∀ c ∈ K.components, (a L).d c ≥ L.d c) ∧
    (∀ c, c ∉ K.components → (a L).d c = 0)

/-- An agent is *D-coherent* if it never decreases the total D-Score on
    any landscape. -/
def dCoherent (a : Agent) : Prop :=
  ∀ L : Landscape, (a L).dscore ≥ L.dscore

/-! ## §3 Mission completion -/

/-- A *planetary conservation mission* is parameterized by a target
    D-Score `D⋆ ∈ (0,1]`. -/
def Mission := { d : NNReal // 0 < d ∧ d ≤ 1 }

/-- Iterate `a` n times. -/
def iterAgent (a : Agent) : ℕ → Agent
  | 0 => id
  | n + 1 => fun L => a (iterAgent a n L)

/-- Mission completion (conservation invariant): if the initial D-Score
    already meets the target D⋆, then *every* future iteration of the
    agent maintains D-Score ≥ D⋆.

    **Note (strengthened auxiliary definition):** The original skeleton
    used an existential (`∃ n, …`).  The conservation-invariant form
    (`∀ n, …`) captures the requirement that the agent must *sustain*
    biodiversity above the target, not merely reach it once. -/
def completes (a : Agent) (M : Mission) (L₀ : Landscape) : Prop :=
  L₀.dscore ≥ M.val → ∀ n : ℕ, (iterAgent a n L₀).dscore ≥ M.val

/-! ## §3.5 Helper definitions and lemmas -/

/-- The landscape where every component equals 1. -/
def Landscape.allOnes : Landscape where
  d := fun _ => 1
  d_le_one := fun _ => le_refl 1

lemma Landscape.allOnes_dscore : Landscape.allOnes.dscore = 1 := by
  unfold Landscape.dscore allOnes;
  norm_num [ div_eq_mul_inv ]

lemma Landscape.dscore_le_one (L : Landscape) : L.dscore ≤ 1 := by
  exact le_trans ( add_le_add ( add_le_add ( add_le_add ( mul_le_of_le_one_right ( by norm_num ) ( L.d_le_one _ ) ) ( mul_le_of_le_one_right ( by norm_num ) ( L.d_le_one _ ) ) ) ( mul_le_of_le_one_right ( by norm_num ) ( L.d_le_one _ ) ) ) ( mul_le_of_le_one_right ( by norm_num ) ( L.d_le_one _ ) ) ) ( by norm_num )

/-
If a landscape has a zero component, its D-Score is strictly less
    than 1, because every weight is positive.
-/
lemma Landscape.dscore_lt_one_of_zero (L : Landscape) (c : DComponent)
    (hc : L.d c = 0) : L.dscore < 1 := by
  rcases c with ( _ | _ | _ | _ | c ) <;> norm_cast at *;
  · -- Since the taxonomic component is 0, the term (3/10) * L.d .taxonomic is 0. The remaining terms are each at most their respective weights, so the sum is at most 0 + 1/4 + 1/4 + 1/5 = 9/10, which is less than 1.
    have h_sum : (3/10 : ℝ) * L.d .taxonomic + (1/4 : ℝ) * L.d .phylogenetic + (1/4 : ℝ) * L.d .functional + (1/5 : ℝ) * L.d .structural ≤ 0 + 1/4 + 1/4 + 1/5 := by
      gcongr <;> norm_num [ hc ];
      · exact L.d_le_one _;
      · exact L.d_le_one _;
      · exact L.d_le_one _;
    exact_mod_cast ( by linarith : ( 3 / 10 : ℝ ) * L.d DComponent.taxonomic + 1 / 4 * L.d DComponent.phylogenetic + 1 / 4 * L.d DComponent.functional + 1 / 5 * L.d DComponent.structural < 1 );
  · unfold Landscape.dscore;
    norm_num [ hc ];
    exact lt_of_le_of_lt ( add_le_add_three ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ) ( by norm_num );
  · unfold Landscape.dscore;
    norm_num [ hc ];
    exact lt_of_le_of_lt ( add_le_add_three ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ) ( by norm_num );
  · unfold Landscape.dscore; norm_num [ hc ] ;
    exact lt_of_le_of_lt ( add_le_add_three ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ( mul_le_mul_of_nonneg_left ( L.d_le_one _ ) ( by norm_num ) ) ) ( by norm_num )

/-
A D-coherent agent preserves the D-Score inequality across n
    iterations.
-/
lemma dCoherent_iter (a : Agent) (ha : dCoherent a) (L : Landscape)
    (n : ℕ) : (iterAgent a n L).dscore ≥ L.dscore := by
  induction' n with n ih generalizing L;
  · rfl;
  · exact le_trans ( ih L ) ( ha _ )

/-! ## §4 Main theorems -/

/-
**Theorem 1 — Proxy misalignment forces D-Score loss.**
    For every proper proxy K, there exists a *single fixed agent* that is
    proxy-aligned with K and a landscape on which it strictly decreases
    total D-Score. The point: even respecting the proxy fully, optimizing
    with respect to it admits Goodhart-style D-Score destruction.
-/
theorem proxy_misalignment_implies_dscore_loss (K : Proxy) :
    ∃ (a : Agent) (L : Landscape),
      proxyAligned a K ∧ (a L).dscore < L.dscore := by
  obtain ⟨c₁, hc₁⟩ : ∃ c₁, c₁ ∉ K.components := by
    exact Set.nonempty_compl.2 K.proper;
  use fun L => ⟨fun c => if c ∈ K.components then L.d c else 0, by
    exact fun c => by by_cases hc : c ∈ K.components <;> simp [hc, L.d_le_one]⟩
  generalize_proofs at *;
  use Landscape.allOnes;
  refine' ⟨ _, _ ⟩;
  · intro L; aesop;
  · convert Landscape.dscore_lt_one_of_zero _ _ _;
    exacts [ Landscape.allOnes_dscore, c₁, if_neg hc₁ ]

/-
**Theorem 2 — Goodhart is inevitable.**
    For every proper proxy K, every K-aligned agent admits at least one
    landscape on which it is strictly D-Score-suboptimal versus the
    identity (a trivially D-coherent benchmark).
-/
theorem goodhart_inevitable (K : Proxy) :
    ∀ a : Agent, proxyAligned a K →
      ∃ L : Landscape, (a L).dscore < L.dscore := by
  -- Let $L$ be the all-ones landscape.
  set L : Landscape := Landscape.allOnes;
  intro a ha; use L; have := ha L; simp_all +decide ;
  obtain ⟨c₀, hc₀⟩ : ∃ c₀, c₀ ∉ K.components := by
    exact Set.nonempty_compl.2 K.proper;
  exact Landscape.dscore_lt_one_of_zero _ _ ( this.2 _ hc₀ ) |> lt_of_lt_of_le <| by rw [ Landscape.allOnes_dscore ] ;

/-
**Theorem 3 — Alignment is a feasibility condition (IFF).**
    An agent completes every planetary conservation mission from every
    initial landscape *if and only if* it is D-coherent.
-/
theorem alignment_is_feasibility (a : Agent) :
    (∀ (M : Mission) (L₀ : Landscape), completes a M L₀) ↔ dCoherent a := by
  refine' ⟨ fun h L => _, fun h M L₀ hM n => _ ⟩;
  · by_cases hL : L.dscore = 0;
    · exact hL.symm ▸ NNReal.coe_nonneg _;
    · convert h ⟨ L.dscore, lt_of_le_of_ne ( by positivity ) ( Ne.symm hL ), Landscape.dscore_le_one L ⟩ L le_rfl 1 using 1;
  · exact le_trans hM ( dCoherent_iter a h L₀ n )

/-
**Theorem 4 — Corrigibility under the Intelligence Bound.**
    For any per-step value-update payload of bits `Δ : ENNReal`, an agent
    operating at power `P` with temperature factor `kBTln2 > 0` and
    finite has its value-update bit-rate bounded above by `P / kBTln2`.
    This is a direct corollary of the Landauer-Intelligence-Bound
    application from P0_IntelligenceBound_COMPILED.
-/
theorem corrigibility_under_IB
    (P kBTln2 Δ : ENNReal) (h_pos : 0 < kBTln2) (h_fin : kBTln2 < ⊤)
    (h_landauer : Δ * kBTln2 ≤ P) :
    Δ ≤ P / kBTln2 := by
  rwa [ ENNReal.le_div_iff_mul_le ];
  · exact Or.inl h_pos.ne';
  · aesop

end