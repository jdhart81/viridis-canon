# Aristotle Forge — Landing Summary: FNT (Forest Nucleation Theorem, clean core)

- **Landed:** 2026-06-25 (forge MODE P)
- **Aristotle project_id:** `8f6c9b99-ac4a-4069-bf64-ebe04a370963`
- **Agent task_id:** `03881254-463d-442d-9181-607e02fdd0f1`
- **Source:** nightly Run 061 `forest-nucleation-theorem` ([11] Afforestation x fire), CANON_BACKLOG Rank 15
- **Module:** `ForestNucleation.lean`, namespace `Viridis.Afforestation.ForestNucleation`
- **Status:** VERIFIED CLEAN — 0 `sorry`; axiom audit per theorem = exactly {propext, Classical.choice, Quot.sound}; all four theorems non-vacuous.
- **Toolchain:** leanprover/lean4 v4.28.0; Mathlib pin per landed `lake-manifest.json`.

## Theorems (statements preserved verbatim, all discharged)

1. **critical_nucleus** — for 0 < Δμ, a, σ, the critical radius rStar = 2aσ/(3Δμ) is strictly positive and is the UNIQUE global maximizer of the CNT free energy G(r) = -Δμ r^3 + aσ r^2 over r >= 0. Proof key: factorization G(rStar) - G(r) = Δμ (r - rStar)^2 (r + rStar/2) >= 0.
2. **barrier_half_identity** — the clean CNT half-barrier identity ΔG* = G(rStar) = (1/2) Δμ (rStar)^3 = (1/2) Δμ n*.
3. **broadcast_suboptimal** — the spatial Dispersal-Establishment Paradox: under fixed seed budget S and sharp establishment threshold at n*, colonized area A_col(n) = (S/n)*1[n >= n*]*C is UNIQUELY maximized at n = n* with value S*C/n*; every sub-critical (broadcast) cluster colonizes zero area.
4. **FNT_nonvacuous** — hypothesis class inhabited by a concrete positive triple with strictly positive barrier (ΔG* > 0), so 1-2 are not vacuously true.

## Aristotle output_summary (verbatim)

> All four `sorry`s in `ForestNucleation.lean` have been discharged, with the named theorem statements and conclusions preserved verbatim:
> - critical_nucleus — proved via the factorization G(rStar) - G(r) = Δμ*(r - rStar)^2*(r + rStar/2), giving positivity of rStar, the global-max inequality, and uniqueness.
> - barrier_half_identity — proved by substituting rStar (a*σ = (3/2)*Δμ*rStar) and simplifying to G(rStar) = (1/2)*Δμ*rStar^3.
> - broadcast_suboptimal — proved by case-splitting on the establishment indicator 1[nStar <= n] and using division monotonicity; establishes the unique maximizer at n = nStar, its positive value S*C/nStar, and zero colonized area for sub-critical clusters.
> - FNT_nonvacuous — proved with a concrete positive witness, confirming the non-vacuity of the hypothesis class.
>
> Acceptance verification:
> - 0 sorry remain (the only occurrence of the word is inside a documentation comment).
> - The project builds successfully.
> - Axiom audit for every named theorem returns exactly {propext, Classical.choice, Quot.sound}.
>
> Note: the hΔμ hypothesis of barrier_half_identity turns out to be unused by the proof (the identity also holds when Δμ = 0 via Lean's div-by-zero convention), producing a benign unused-variable linter warning. The binder was kept to preserve the statement verbatim; no statement was weakened or collapsed to a trivial conclusion.

## Honest boundary (modeling inputs, not formalized here)
The CNT free-energy form itself, the Arrhenius nucleation rate J = J0 exp(-ΔG*/T_eco), the ecological temperature T_eco, the general monotone-sigmoid committor p(n), and the tempo-coupled deadline t_dead are the ecological/thermodynamic modeling inputs. This file proves everything downstream of the clean polynomial reduction r := n^(1/3): the critical-point geometry, the half-barrier identity, and the sharp-threshold concentration-beats-broadcast optimum on which the drone-deposition design law depends.

## Routing
- **Tier:** spine candidate (extends P0 / [11] Afforestation; source finding tagged spine). Spine is FROZEN at v10.0.0 under G-SPINE-FREEZE — landing as a verified module; NO spine version cut without explicit Justin OK.
- **Next stage (Justin-gated):** ledger row 32 set to AWAITING JUSTIN OK. No promotion to 01_MATHLIB/Aristotle-Pipeline/, no canon lakefile edit, no Zenodo deposit by the forge.
