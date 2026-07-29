# DualCorridor — Aristotle verification summary

**Module:** `DualCorridor` (`DualCorridor_Verified.lean`)
**Paper:** Hart, J. (2026). *Trees Cannot Cut: Circuit Rank as the Design Variable Reconciling
Habitat Connectivity and Fuel Discontinuity in Managed Forest Landscapes.*
**DOI (version):** 10.5281/zenodo.21686447 · **Concept DOI:** 10.5281/zenodo.21686446
**Published:** 2026-07-29, `viridis-canon` community
**Route:** Journal branch (standalone DOI) · indexed in Series **S5 — Corridors & Spatial**
(`10.5281/zenodo.20777068`) · `isDerivedFrom` spine `10.5281/zenodo.19317982`
**Toolchain:** `leanprover/lean4:v4.28.0` · Mathlib rev `8f9d9cff`
**Correspondence:** Justin@viridisconservation.com

---

## Gate results

| Gate | Result |
|---|---|
| G-ARISTOTLE-FIRST — fresh pass, zero `sorry` | **PASS** — run 3, project `f07e765b-02f1-4cfc-9f40-6bae222150fe`, completed 2026-07-29 |
| Clean axiom audit, per theorem | **PASS** — 21/21 within `{propext, Classical.choice, Quot.sound}` |
| Non-vacuity | **PASS** — `FaceCount.ofCircuitRank` exhibits the hypothesis as inhabited, itself axiom-clean |
| Paper-first | **PASS** — 26 pp PDF leads the deposit |
| Honest scope | **PASS** — see *Scope* below; stated in the paper banner, Appendix B, the README and the Zenodo notes |
| Identity hygiene | **PASS** — Viridis LLC, Columbia Falls MT; ORCID 0009-0008-3082-2482; Aristotle (Harmonic) credited as co-author |
| Hold check | **PASS** — no active hold |

---

## The twenty-one verified results

| Result | Paper |
|---|---|
| `zeroCut` | **Proposition 1** — an acyclic corridor leaves one compartment |
| `faces_eq_circuitRank_add_one` | Proposition 2 — compartments = μ + 1 |
| `bridge_no_merge` | Proposition 4(i) — bridges have zero cut capacity |
| `nonBridge_merges_exactly_one` | Proposition 4(ii) |
| `disjoint_support` | Proposition 4(iii) — the two supports are disjoint |
| `boundaryAnchor_faces` | **Proposition 5** — b anchors give exactly b compartments |
| `first_anchor_buys_nothing` | §2.6 off-by-one |
| `numComponents_delete_bridge` | Prop 4(i) keystone |
| `circuitRank_delete_bridge` | Prop 4(i) lemma |
| `circuitRank_delete_nonBridge` | Prop 4(ii) core |
| `numComponents_delete_nonBridge` | — |
| `circuitRank_eq_zero_iff_isAcyclic` | Prop 1 lemma |
| `circuitRank_eq_zero_of_isAcyclic` | Prop 1 lemma, forward direction |
| `circuitRank_nonneg` | non-vacuity support |
| `circuitRank_anchor_of_isAcyclic` | Prop 5 core |
| `anchor_connected`, `anchor_edge_card`, `numComponents_eq_one_of_connected` | Prop 5 support |
| `sum_component_vertex_cards`, `edgeFinset_card_delete_of_mem` | counting helpers |
| `FaceCount.ofCircuitRank` | **non-vacuity witness** |

Full `#print axioms` output: `lean/axiom_audit.log`.

---

## Scope — what is *not* proved

1. **The topological step.** That the geometric compartment count of Ω \ C equals circuit
   rank plus one — Alexander duality — is carried as an **explicit hypothesis**, the
   `FaceCount` structure. Mathlib has neither Alexander duality nor a usable planar Euler
   formula. `FaceCount.ofCircuitRank` shows the interface is inhabited, so nothing
   downstream is vacuous — but it is the **tautological model**
   (`faces G := (circuitRank G + 1).toNat`). It does **not** establish that the geometric
   count satisfies the relation.
2. **Proposition 3** (length scaling) is asymptotic analysis and is not formalised.
3. **The numerical results** (§4 of the paper) are lattice simulation and are independent
   of the Lean development.

Lean certifies the reasoning, not empirical magnitudes.

---

## Provenance — three runs, two failures

| Run | Project | Outcome |
|---|---|---|
| 1 | `1eec0165-14bd-4785-bf3a-26e293c78d79` | ~17 h, cancelled at 78%. 16 `sorry` → 4. Audit: Props 2, 4(ii), 5 clean; Props 1, 4(i), 4(iii) on `sorryAx`. **FAILED the keystone.** |
| 2 | `2d959850-c127-45ae-9ec1-46f2cdc618d6` | Out of budget at 100%. Closed one helper lemma; moved nothing at paper level. **FAILED the keystone.** |
| 3 | `f07e765b-02f1-4cfc-9f40-6bae222150fe` | **COMPLETE.** Keystone closed; Props 1, 4(i), 4(iii) unlocked; `FaceCount` instance created on request. One `sorry` left. |

**Diagnosis that unlocked run 3.** The run-2 skeleton derived the keystone
`numComponents_delete_bridge` *from* `circuitRank_delete_bridge` — which is the keystone's
own arithmetic consequence. A primitive derived from its consequence has no way in. Run 3
inverted the dependency: component count posed as primitive, circuit-rank identity as
consequence, with the fibre-counting route named explicitly
(`SimpleGraph.ConnectedComponent.surjective_map_ofLE`). It closed.

**Deviation to note.** Run 3 left one `sorry`, at `circuitRank_eq_zero_iff_isAcyclic`. It
was closed **by hand**, not by the prover, from run-3 lemmas that are themselves axiom-clean
(forward: strong induction on edge count, every edge of an acyclic graph being a bridge;
reverse: a cycle yields a non-bridge edge, and `circuitRank_delete_nonBridge` with
`circuitRank_nonneg` force μ ≥ 1). The artifact as shipped was rebuilt from scratch and
re-audited after that edit.

---

## Method note

After run 1, "sixteen sorries reduced to four, build succeeded" would have read as progress
on the paper's headline claim. The axiom audit showed the headline claim was among the four.
After run 3, "one sorry remaining" understated the problem in the other direction — that
single `sorry` was Proposition 1, and it poisoned `zeroCut` transitively.

Neither error is detectable from the build log. **Run `#print axioms` on every named result,
every time.**
