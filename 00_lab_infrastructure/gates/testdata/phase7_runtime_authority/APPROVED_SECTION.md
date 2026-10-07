## Phase 7 — Claude audit of release packet v002 — 2026-10-07

Packet: `2026-10-06/phase-7-science-catchup-v001/release-packet-v002/RELEASE_PACKET.md`. The packet is accurate and appropriately conservative: no overclaiming was found, and the disclaimer ("logical validity given the model, not empirical validation") is present. The 48 HOLDs are an evidence gap, not a science failure. Resolutions below; after these, publication proceeds without another Claude stop unless a hard-stop condition occurs.

### 1. Per-claim nonvacuity witnesses (blocks 47 packages; 297 null witnesses)
Claude's count: 132 of the 297 claims have **no hypotheses beyond type binders** over nonempty types (ℝ, ℕ, ℤ, ℚ, function types into ℝ).
- **Tier 0, no hypotheses:** nonvacuity is discharged by rule. A universally quantified statement over a nonempty domain with no premises cannot be vacuous. Record `witness = NO_HYPOTHESES (domain nonempty: <type>)`. Custom types need a recorded `Inhabited`/`Nonempty` instance or an explicit term.
- **Tier 1, hypotheses present (about 165):**
  1. Pre-screen candidate substitutions (start with the run's existing `*_nonvacuous` values) using **exact rational arithmetic** (sympy `Rational`, no floats). Use rigorous interval arithmetic for `sqrt`, `exp` or `log`.
  2. For each claim with a passing substitution, emit a Lean witness lemma `example : <every hypothesis at the substituted values> := by norm_num [defs]` (or `positivity`/`nlinarith`).
  3. **Bundle all witness lemmas for a run into one Comparator job on the droplet**, under the standard dual-kernel and axiom rules. A certified bundle sets `selected_reviewed_witness` for those claims.
  4. Claims with no certified witness stay in the paper only under the label **"certified; nonvacuity not demonstrated"**, and do not count toward the note's certified-result headline.
- The exact-arithmetic pre-screen is a selection aid only; the Comparator remains the sole verifier of record.

### 2. Semantic triviality tiers (replaces open "semantic review required")
In the same Comparator bundle, add downgrade-only probes per claim: try closing each theorem with `rfl`, then `simp only [<defs>]`, then `ring`/`ring_nf`/`norm_num`/`linarith`/`nlinarith`/`field_simp; ring` after unfolding definitions. Label each claim:
- `DEFINITIONAL` (closes by `rfl`/defs-only `simp`);
- `ROUTINE` (closes by one standard tactic after unfolding; e.g. Run-140 `option_value_identity` is a `ring` identity under `optionValue`'s definition);
- `SUBSTANTIVE` (no probe closes it).

Labels print in the claim table. A note whose claims are all DEFINITIONAL is published only inside the Methods Digest appendix, never as a headline note. Probes can only downgrade a label; they never certify.

### 3. Run-127: product-form underdeclaration
Narrow the paper. Every product-form statement moves to a labeled "Conjectural context" section that cites foundation 10.5281/zenodo.23141592 and the Run-902 conditional. The certified scope keeps only theorems whose statements and definitions do not encode the product form. If a certified theorem itself encodes the product form without PL/PD hypotheses, that theorem leaves the certified scope and Run-127 goes on the re-proof candidate list. Rerun INV-9 on the narrowed paper.

### 4. Run-147: INV-9 title false positive
Keep the historical title. Add one sentence to the abstract: "This note does not depend on the product-form Intelligence Bound conjecture; its results are independent of premises PL and PD." Amend the INV-9 checker so a phrase-only title match **with zero product-form formula matches and an explicit basis sentence in the abstract** passes. Add must-fail tests: a formula match still fails; the title match without the sentence still fails.

### 5. Run-187 discovery debt
Install the merged corrected selector through the standard PR/protected-hash path. Then confirm via SSOT that Run-187 reads CERTIFIED.

### 6. Release flow after 1–5
Packages that pass all gates go to publication in the weekly Methods Digest: exact bindings at publish time, ≤10 Zenodo writes per day, strict readback. Wave C draft passes (125, 126, 128–131, 134, 141) may go first once their witnesses are complete (each has 0 null witnesses already). No further Claude stop is required. Claude audits the first published digest by readback.
