# CLAIMS MATRIX — Viridis Canon

**Purpose.** Lean type-checking guarantees exactly one thing: *the proof term
inhabits the stated type.* It does **not** guarantee that the stated type means
what the theorem's name suggests, that the hypotheses are physically realizable,
or that the assumptions describe nature. This file separates those layers for
every headline result so that no reader mistakes "Lean-checked" for "empirically
established."

For each result: the **informal claim** (what the name/paper suggests), the
**exact Lean conclusion** (what is actually proved), the **required
assumptions**, what is **NOT established**, and a **status label** from
[`THEOREM_STATUS_TAXONOMY.md`](./THEOREM_STATUS_TAXONOMY.md).

> Reading guide for the labels: **Derived** = substantive and self-contained ·
> **Conditional** = true given stated regime assumptions · **Definition-expansion**
> = follows by unfolding a definition · **Bridge-assumption** = the load-bearing
> step is an assumed hypothesis, not a derived fact · **Empirical-hypothesis** =
> requires data to validate · **Conjecture** = stated, not proved · **Exploratory**
> = quarantined, not part of the verified spine.

Last updated: 2026-06-21 (Integrity Release v9.1.0). Module/line references are to
`01_MATHLIB/Aristotle-Pipeline/`.

---

## P1 — D-Score (information-theoretic)

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `mutualInfo_le_entropy_left` | `I(X;Y) ≤ H(X)` for finite discrete `X,Y` on a probability space | `IsProbabilityMeasure μ`, measurability | nothing beyond the inequality | **Derived** |
| `dScore_mem_Icc` | `dScore μ X Y ∈ [0,1]` | probability measure, measurability | that the normalized ratio is a *validated biodiversity / landscape* metric | **Derived** (math) / **Empirical-hypothesis** (as an ecology metric) |

**Note.** P1 is the strongest module: it *constructs* entropy and mutual
information and proves a real bound, then derives a genuinely normalized score.
The only caveat is interpretive — turning this into a field biodiversity index is
an empirical-modeling problem, not a theorem.

---

## P0 — Intelligence Bound (erasure-side footing, post-Wolpert)

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `intelligence_bound` | `İ ≤ P / (k_B T ln 2)` | `SatisfiesLandauerLimit` (assumed predicate), erasure ≥ creation rate | that any *physical* system must satisfy the assumed Landauer predicate | **Conditional** |
| `thermodynamic_bound_lemma` | algebraic rearrangement of `SatisfiesLandauerLimit` | the predicate itself | a *derivation* of the predicate from microphysics | **Definition-expansion** |
| `landauer_dissipation_bound` (was `finite_memory_dissipation`) | `P ≥ İ · k_B T ln 2` | `h_landauer`, `h_erasure_needed` | nothing beyond Landauer + transitivity (dead `h_mem`/`C` removed v9.1.0) | **Definition-expansion** ✅ resolved |
| `BoundedMemoryDissipation.bounded_memory_dissipation_floor` | `ε>0 ∧ ε·E ≤ Q ∧ A−E ≤ M ⟹ ε·(A−M) ≤ Q` — bounded-memory dissipation floor, **`hmem` load-bearing** | per-erasure floor `ε>0`, budget `ε·E ≤ Q`, bounded memory `A−E ≤ M` | universal `ε = k_BT ln2` (regime param); the process↔ledger identification | **Derived/Conditional** ✅ Aristotle-verified (`6483ae65`, 2026-06-21; non-vacuity + load-bearing machine-checked) |
| `conditional_conservation` | long-horizon preservation dominates exploitation, NNReal, finite case | finite rates, horizon threshold | unconditional convergence | **Conditional** (non-vacuous) |

**✅ RESOLVED (v9.1.0, 2026-06-21).** Dead `h_mem`/`C` removed; theorem renamed
`landauer_dissipation_bound`. The honest, non-vacuous bounded-memory dissipation
floor — bounded memory **load-bearing**, with machine-checked non-vacuity and a
machine-checked proof that `hmem` cannot be dropped — is the new spine module
`BoundedMemoryDissipation` (Aristotle `6483ae65`; axioms ⊆ {propext, Classical.choice,
Quot.sound}). INV-4 closed.

---

## BoundedMemoryLearning / BiosphereErasureBound (the recovered footing)

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `bounded_memory_forces_erasure` | `A − E ≤ M ⟹` erasure `E ≥ A − M` | acquisition `A`, capacity `M` reals | a universal per-bit constant | **Conditional** |
| `erasure_dissipation_floor` | dissipation `≥ ε·(A−M)` | per-erasure cost `ε` as an *operating-regime* assumption | that `ε = k_B T ln 2` universally (reversible-computing loophole explicitly encoded) | **Conditional** |
| `sustained_learning_bound` | finite-horizon inequality on sustained acquisition | bounded memory + ε-regime | infinite-horizon / acquisition-side floor | **Conditional** |
| `reversible_regime_imposes_no_bound` | in the reversible regime, no bound | reversibility | — (this is the honest negative result) | **Derived** |
| `biosphere_erasure_floor`, `erasure_floor_positive`, `stewardship_power_floor` | positive erasure/power floors given `ε_L, D > 0` | `ε_L`, complexity `D`, rate `r` as positives | empirical values of `ε_L`, `D` | **Conditional** |

**Note.** This is the post-Wolpert reconstruction and it is conducted honestly:
acquisition vs. erasure are distinguished, `ε` is a regime assumption, and the
reversible loophole is a theorem, not a footnote.

---

## P2 — HDFM / dendritic corridors (graph theory)

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `tree_edge_removal_partition` | `¬ (T.deleteEdges {e}).Connected` — removing an edge **disconnects** the tree | `T` connected & acyclic | the strictly stronger "**exactly two** components" (true for trees, but not proved here) | **Derived** (for the stated `¬Connected` conclusion) |
| `tree_every_edge_is_bridge`, `tree_edge_count` | standard tree facts | finite tree | — | **Derived** |
| `dendritic_minimum_cost`, `dendritic_max_info_efficiency` | cost/efficiency results on the model graph | the model's cost & info definitions | that the model's cost function matches field economics | **Conditional** |

**Fixed in v9.1.0.** The docstring previously said "partitions into exactly two
connected components"; corrected to match the `¬Connected` conclusion.

---

## P3 — Goodhart impossibility / alignment-as-feasibility

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `proxy_misalignment_implies_dscore_loss` | `∃ a L, proxyAligned a K ∧ (a L).dscore < L.dscore` — there **exists** a landscape on which a proxy-aligned agent loses D-Score | `proxyAligned` defined to **zero every component outside the proxy K** | that **every** partial-objective optimizer Goodharts (the def is strong; the result is existential) | **Conditional** |
| `goodhart_inevitable` | existential form over proxy-aligned agents | same strong `proxyAligned` | universal failure of all bounded-rational optimizers | **Conditional** |

**Note.** The result is valid and useful, but its force comes from the
definition of `proxyAligned` (zero outside `K`). A weaker, more realistic agent
model (down-weights, not zeroes) is the natural next strengthening.

---

## P4 — Thermodynamic economics

| Result | Exact Lean conclusion | Required assumptions | NOT established | Status |
|---|---|---|---|---|
| `thermodynamic_production_bound` | `F ≤ η·P·D/(k_B T ln 2)` | IB structure | — | **Conditional** |
| `non_substitutability_D_essential` / `_P_essential` | `F(P,0)=0` and `F(0,D)=0` — **boundary essentiality** | η,kBT bounded | "perfect complements / Leontief / σ=0" — the isoquant `D=c·F₀/(η·P)` is a **rectangular hyperbola**, so substitution is **positive** for D>0 | **Definition-expansion** (boundary essentiality only) |
| `steady_state_necessity` | `P_max / kBT_min < ⊤` — the rate ceiling is **finite** | finite power, positive min temperature | that material-throughput growth **must** enter a steady state, or that efficiency is the **only** growth source | **Definition-expansion** |
| `infinite_foreclosure_cost` | `∫_{[0,∞)} v_min·rate = ⊤` — an **undiscounted** positive flow diverges | positive flow, **no discounting** | infinite cost under "**any** valuation framework" — discounting/declining valuation gives finite present value | **Conditional** |

**Fixed in v9.1.0.** Leontief / perfect-complements / σ=0 language withdrawn from
P4 docstrings; claims reduced to boundary essentiality and finiteness. A genuine
zero-substitution claim would require switching to a CES/Leontief production form
(deferred; see §Open).

---

## P9 — AI Safety  ⚠ EXPLORATORY (quarantined v9.1.0)

**Removed from the verified spine and from `defaultTargets`.** Retained for
research. Listed here for full transparency.

| Result | Exact Lean conclusion | What's wrong | Status |
|---|---|---|---|
| `ai_conservation_alignment` | `∃ T₀, ∀ T > T₀, …`, **proved with `T₀ = ⊤`** so `T > ⊤` is unsatisfiable | **VACUOUS** — establishes nothing | **Exploratory** (broken) |
| `deception_power_cost` | `0 < ΔI · kBT_ln2` | no term for deceptive-system power; proves no lower bound on it | **Exploratory** (mislabeled) |
| `complete_alignment_framework` | `a < b ∨ a = b` (i.e. `a ≤ b`) | does not show a rational agent must preserve the biosphere | **Exploratory** (trivial) |
| `misalignment_self_defeat` | `min(ρ₂·B, P/c) ≤ min(ρ₁·B, P/c)` given `ρ₂ ≤ ρ₁` | **assumes** lower ρ; the biological D→ρ link is unformalized (`AISystem.D` unused by `ibCeiling`) | **Exploratory** (assumption-loaded) |
| `data_wall_containment`, `containment_*`, `*_limited_ceiling` | genuine monotonicity/min facts | fine as stated, but they are facts about `min`, not safety guarantees | **Definition-expansion** |

A non-vacuous reconstruction (real `T₀`, a power term for deception, a formal
D→ρ bridge) is queued for a fresh Aristotle pass before P9 can re-enter the spine.

---

## Bridges

| Result | Exact Lean conclusion | Issue | Status |
|---|---|---|---|
| `Bridge_MissionFeasibility.mission_feasibility` | `Feasible e m ↔ r ≤ P/(k_B T ln2)` over **local** definitions | imports only `Mathlib`; rebuilds analogues of P0/P3/P4 rather than importing them | **Bridge-assumption** — ⚠ should import the pillars (INV-5) |
| `Bridge_BiosphereProductivity.*` | IB ⇄ NPP duality, 6 thm | self-contained; genuine | **Conditional** |
| `Bridge_EcoChainInstrument.*` | operator ↔ instrument layer | self-contained | **Conditional** |

**Open.** `Bridge_MissionFeasibility` should `import ViridisCanon.P0 / P1 / P3 /
P4` and bridge the *existing* definitions, so the dependency graph is real rather
than re-declared. Deferred to a forge pass (changes proof content).

---

## Open items deferred to a fresh Aristotle pass (not claimed verified in v9.1.0)

1. ~~**P0** — make `h_mem` load-bearing~~ ✅ **DONE v9.1.0** (module `BoundedMemoryDissipation`, Aristotle `6483ae65`).
2. **P4** — optional: replace `F=η·P·D/c` with a CES/Leontief form if a genuine
   zero-substitution claim is wanted (otherwise the boundary-essentiality framing
   here stands).
3. **Bridges** — `Bridge_MissionFeasibility` to import the real pillars.
4. **P9** — full non-vacuous reconstruction before any spine re-entry.

These are proof-content changes; per the Aristotle-first gate they require a fresh
machine-checked pass and are **not** asserted as verified in this release.
