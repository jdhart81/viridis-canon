# ARISTOTLE_SUMMARY — Wu Wei Dominance (clean core)

- **Target:** `WuWeiDominance.lean` (capstone `wu_wei_dominance_of_rates`; assembled `wu_wei_dominance`)
- **Aristotle project_id:** `53861622-f85c-4cc7-926f-eaf610cb5a53` (description `forge_wuwei`)
- **Agent task_id:** `0f12a777-9346-4e02-814d-718c854232fc`
- **Submitted:** 2026-06-24T12:04:20Z · **Completed:** 2026-06-24T12:09:31Z (~5 min)
- **Status:** `TaskStatus.COMPLETE` @ 100% (clean COMPLETE — not COMPLETE_WITH_ERRORS)
- **Source:** JUSTIN-DIRECTED (2026-06-23 session); CANON_BACKLOG top-of-queue
- **Toolchain:** leanprover/lean4:v4.28.0 · Mathlib pin 8f9d9cff
- **Landed:** `new leans/2026-06-24_aristotle_WuWeiDominance_forge/`

## Verification (VERIFIED CLEAN)
- `lake build` of the `WuWeiDominance` target completes with **0 errors**.
- **0 `sorry`** in source (the only token match is the prose "no `sorry`" in the doc header).
- **Axiom audit limited to `{propext, Classical.choice, Quot.sound}`** on the main
  results (`wu_wei_dominance`, `wu_wei_dominance_of_rates`) and supporting lemmas
  (`fast_collapse`, `support_evolve_eq_of_safe`).
- **All named theorem statements and conclusions preserved verbatim;** no auxiliary
  definition strengthened.
- **Non-vacuous:** capstone concludes a strict inequality
  `richness (evolve Dfast thr T c0) < richness (evolve Dslow thr T c0)`
  from explicit sub-/super-critical hypotheses (`hsub`/`hsuper`).

## Aristotle's fix (from output_summary)
The file contained no `sorry`s; the only build failure was a renamed Mathlib
lemma. `le_or_lt` no longer exists under that name, so in `Drift.support_subset`
the proof now uses `rcases le_or_gt (c i) 0` (its current Mathlib name). No
statement was weakened. Other flagged candidates (`Finset.card_le_card`,
`Finset.ssubset_iff_of_subset`, `Nat.le_induction` base/succ labels) are all still
valid under this pin and needed no change.

## What is proven
Multiplicative-drift + extinction-cull ecosystem model: (1) absorbing boundary
`support (Step c) subset support c`; (2) permanence — richness antitone along any
trajectory; (3) sub-critical safety preserves support; (4) super-critical collapse
strictly+permanently drops richness; (5) **dominance** — a sub-critical (slow /
wu wei) policy attains strictly greater long-run species richness (Hill-0
diversity) than a super-critical (aggressive) policy.

## The honest boundary (cited input, deliberately NOT formalized)
Which rate regime a policy falls in (`hsub` vs `hsuper`) is governed by the
Kramers / Freidlin-Wentzell escape law `MFPT ~ exp(dU(r_eco - r_int) / sigma^2)`,
critical rate `r* = Theta(r_eco)` (empirically ~ 0.85*r_eco). Mathlib lacks
Freidlin-Wentzell, so that law is supplied as the hypotheses `hsub`/`hsuper`.
Everything downstream of it is proven here. Next forge target on this thread:
**Lemma C — the Freidlin-Wentzell barrier**.

## Disposition
SERIES candidate (S4/S5 bridge). Spine FROZEN at v10 — route to Series /
standalone pending Justin's OK. Ledger row 30 -> AWAITING JUSTIN OK.
