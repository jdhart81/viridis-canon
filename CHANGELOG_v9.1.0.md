# CHANGELOG — Integrity Release v9.1.0 (2026-06-21)

**Type:** integrity / calibration release. No new theorems are claimed. This
release tightens the correspondence between every headline, hypothesis, theorem
statement, proof, and empirical claim, and makes the canon's guarantees
machine-enforced rather than asserted in prose.

It follows an external technical audit (2026-06-21). We adopt its substantive
findings in full. Publishing the corrections openly is deliberate: a research
program that grades its own claims by formal strength is more trustworthy than
one that advertises uniform "machine-verified" status.

## Positioning change

The canon is now described as **Lean-checked conditional mathematics** for the
Viridis research program, with explicit physical and empirical assumptions —
not "machine-verified physics/economics/ecology." A Lean-checked theorem
guarantees that the proof inhabits the stated type; it does **not** guarantee
that the type captures the informal claim, that the hypotheses are realizable, or
that the assumptions describe nature. Those layers are now separated explicitly.

New governing documents (verified-spine root):
- `CLAIMS_MATRIX.md` — every headline result: informal claim · exact Lean
  conclusion · required assumptions · what is NOT established · status label.
- `THEOREM_STATUS_TAXONOMY.md` — the 7 labels (Derived / Conditional /
  Definition-expansion / Bridge-assumption / Empirical-hypothesis / Conjecture /
  Exploratory).

## Corrections

### P9 (AI Safety) — QUARANTINED as Exploratory
Removed from `defaultTargets` and from the verified-spine guarantee; retained for
research with an EXPLORATORY banner.
- `ai_conservation_alignment` was **vacuous**: proved with existential witness
  T₀ = ⊤, making the hypothesis `T > T₀` unsatisfiable and the ∀ empty. The prior
  README framed this as an "ENNReal edge case"; that framing was wrong and is
  withdrawn.
- `deception_power_cost` concludes only `0 < ΔI·kBT_ln2` — no term for a
  deceptive system's power, no lower bound on it. Name de-escalated to a
  conjecture in the matrix.
- `complete_alignment_framework` concludes `a ≤ b` (written `a < b ∨ a = b`),
  not that a rational agent must preserve the biosphere.
- `misalignment_self_defeat` **assumes** ρ₂ ≤ ρ₁; the biological D→ρ link is
  unformalized (`AISystem.D` is unused by `ibCeiling`).
A non-vacuous reconstruction is queued for a fresh Aristotle pass before any
spine re-entry.

### P4 (Thermodynamic Economics) — labels de-escalated (comment-only; no proof change)
- The "perfect complements / Leontief / σ(P,D)=0" language is **withdrawn**. With
  F = η·P·D/c the isoquant D = c·F₀/(η·P) is a rectangular hyperbola, so the
  elasticity of substitution is **positive** for D>0. The theorems establish
  **boundary essentiality** (F=0 when D=0 or P=0), not zero substitutability.
- `steady_state_necessity` restated as what it proves: the rate ceiling
  P_max/(k_B T_min ln2) is **finite**. It does not by itself prove growth must
  halt.
- `infinite_foreclosure_cost` restated as **conditional on no discounting**: an
  undiscounted positive flow over [0,∞) diverges; present value is finite under
  discounting.

### P2 (HDFM) — docstring corrected (comment-only; no proof change)
- `tree_edge_removal_partition` proves `¬ Connected` (the tree is disconnected),
  not "exactly two connected components." Docstring corrected.

### P0 (Intelligence Bound) — ✅ FIXED (Aristotle-verified)
- Unused `h_mem`/`C` removed from `finite_memory_dissipation`, renamed
  `landauer_dissipation_bound` (Landauer + transitivity — **Definition-expansion**,
  no false bounded-memory claim).
- New spine module **`BoundedMemoryDissipation`**: the honest, non-vacuous
  bounded-memory dissipation floor with bounded memory **load-bearing**
  (`bounded_memory_dissipation_floor`, `…_nonvacuous`, `bounded_memory_is_load_bearing`).
  Aristotle run `6483ae65` (2026-06-21): `lake build` clean, 0 sorry, axioms ⊆
  {propext, Classical.choice, Quot.sound} on all five, returned byte-identical (no
  weakening). INV-4 closed. Co-authored-by: Aristotle (Harmonic).

### Bridges — dependency graph to be made real (queued)
- `Bridge_MissionFeasibility` imports only Mathlib and re-declares analogues of
  P0/P3/P4 rather than importing them. To be repointed at the real pillar
  modules. Proof-content change → queued.

## Enforcement (the audit is now machine-checked, INV-1/3)

- `AxiomAudit.lean` — build target; walks the environment and **throws on**
  `lake build` if any spine declaration depends on an axiom outside
  `{propext, Classical.choice, Quot.sound}` or on `sorryAx`. Replaces the prior
  informational "axiom audit" step that only printed a message.
- `tools/vacuity_lint.py` — flags ⊤-witness / `absurd … not_top_lt` / `nomatch`
  vacuity fingerprints. Verified to flag P9 (3 hits) and to pass clean on the
  14-module post-quarantine spine.
- `tools/check_spine_hygiene.sh` — no `sorry`/`admit` in code, no homemade
  axioms, runs the vacuity linter. Passes clean on the current spine.
- `.github/workflows/ci.yml` — textual gates **blocking**; Lean build + axiom audit **provisional** (continue-on-error) pending GitHub Actions validation (clarified in v9.1.1). No-`sorry` log
  scan + axiom-audit confirmation. Branch-protect `main` to require it.

## Not changed
- No theorem proof was rewritten in v9.1.0 (proof-content fixes are queued for a
  fresh Aristotle pass per the Aristotle-first gate). All edits to `.lean` spine
  files in this release are comments/docstrings, banners, or build-target config.
- Concept DOI `10.5281/zenodo.19317982` continues to resolve to the latest spine.

## Known follow-ups (tracked in CLAIMS_MATRIX → Open items)
1. ~~P0 `h_mem` rewrite~~ ✅ DONE (module `BoundedMemoryDissipation`).  2. P9 non-vacuous reconstruction.
3. Bridge_MissionFeasibility real imports.  4. Optional CES/Leontief form for P4.
5. Reconcile per-file toolchain header comments (P4 header still cites Lean
   4.24.0 / Mathlib f897ebcf) with the repo-pinned 4.28.0.
