# ARISTOTLE_SUMMARY — CognitiveThroughput (CTT)

- **Status:** ✅ VERIFIED CLEAN
- **Aristotle project_id:** `b04c2897-6470-4a34-b9a7-1a15e6b373a7`
- **Agent task_id:** `733d7e0b-7dee-4aa3-9a9a-36b292c40b35`
- **Task status:** COMPLETE (100%)
- **Submitted:** 2026-06-17T12:07:48Z · **Completed:** 2026-06-17T12:13:15Z (~6 min)
- **Source:** nightly Run 039 — Cognitive Throughput Theorem (CTT)
- **Module:** `CognitiveThroughput` · namespace `Viridis.Cognition.CTT`
- **Target:** `SquareRootScaling` + 4 load-bearing corollaries (5 named theorems total)
- **Toolchain:** leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff

## Theorems discharged (statements preserved VERBATIM, 0 weakening)
1. `SquareRootScaling` — `R K (c*N) = R K N / √c` (inverse-√ homogeneity; consumes 0<c, 0<N) via `Real.sqrt_mul` + `field_simp`.
2. `throughput_invariant` — `R K N * √N = K` (conserved attention budget; consumes 0<N) via `field_simp`.
3. `envelope_strictAntitone` — `N₁<N₂ ⇒ R K N₂ < R K N₁` (the "attentional iris"; consumes 0<K) via `div_lt_div_of_pos_left`.
4. `decoupled_AI_zero_throughput` — `Kcog Wattn 0 kT = 0` (Φ_eco=0 ⇒ zero throughput) via `simp`.
5. `coupled_AI_positive_throughput` — `0<Wattn → 0<kT → 0<Φ_eco ⇒ 0 < Kcog` (symbiotic-AI bound) via `Real.sqrt_pos` + `positivity`.

## Verification
- `lean_build` succeeds (clean; no renames forced under the pin).
- `grep sorry`: zero outside comments (single occurrence is in the header doc-comment's ACCEPTANCE line).
- **Axiom audit:** exactly `{propext, Classical.choice, Quot.sound}` for all 5 named theorems.
- **Non-vacuity:** confirmed — each theorem genuinely consumes its positivity hypotheses; no conclusion collapses to a trivially-true goal.

## Meaning
First first-principles cognitive-throughput envelope: the maximum certified information
rate per observation obeys an inverse square-root law dI_cog/dt|max(N) = K_cog·N^(−1/2),
with K_cog = √(2·W_attn·Φ_eco/(k_B T ln 2)). The decoupled/coupled pair is the cognitive
face of the Intelligence Bound: throughput is gated by physical/ecological coupling Φ_eco.

## Provenance / gate
- No publication hold applies (G-TURYSHEV-PUBLICATION concerns the IB↔NPP biosphere-
  productivity duality, not this cognitive envelope).
- DEFERRED (NOT submitted): `Viridis.Cognition.CTT.OMPathEquivalence` (Onsager–Machlup ↔
  Koopman path-equivalence) — staged as a gate-check; no closed-form Lean-ready proposition.
- Forge stops here: landed in `new leans/`, backlog + ledger updated, ⏳ AWAITING JUSTIN OK.
  NOT promoted to canon, NOT deposited to Zenodo.
