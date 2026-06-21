# Theorem Status Taxonomy — Viridis Canon

Every headline result in the canon carries exactly one of these labels in
[`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md). The label states **how much epistemic
weight a Lean-checked theorem actually carries** — which is never automatic from
the fact that it compiles.

The ladder, strongest to weakest:

| Label | Meaning | A reader may rely on it for… | They may NOT infer… |
|---|---|---|---|
| **Derived** | Substantive, self-contained mathematics. The conclusion is non-trivial and the hypotheses are mild/standard. | The mathematical statement, full stop. | A physical/empirical interpretation beyond the math. |
| **Conditional** | True **given explicitly stated regime assumptions** (a Landauer predicate, a cost constant `ε`, finiteness, a horizon threshold). | The implication "assumptions ⟹ conclusion." | That the assumptions hold of nature. |
| **Definition-expansion** | Follows by unfolding a definition; little independent content. Often a boundary/edge fact. | The stated identity/inequality. | That it captures the richer informal claim its name suggests. |
| **Bridge-assumption** | The load-bearing step is an **assumed hypothesis**, not a derived fact (e.g. a predicate is assumed rather than mechanistically established; a hypothesis is present but unused). | The conditional structure. | That the bridge/mechanism has been *established*. |
| **Empirical-hypothesis** | A mathematically well-formed claim whose truth depends on **data** (a metric's ecological validity, a parameter's real value). | The claim as a *testable hypothesis*. | That it has been empirically validated. |
| **Conjecture** | Stated and motivated, **not proved** (or proved only in a degenerate special case). | Direction of research. | That it is a theorem. |
| **Exploratory** | **Quarantined.** Not part of the verified spine. May be conditional, mislabeled, trivial, or — in the worst case — vacuous. | Nothing, until reconstructed. | Any verified guarantee. |

## How a label is assigned

1. **Read the Lean conclusion, not the name.** Strip the docstring; look only at
   the type after the final `:`.
2. **Check hypothesis realizability.** Is any hypothesis unsatisfiable (a `⊤`
   witness, a contradictory bound)? → it cannot be **Derived/Conditional**;
   it is at best **Exploratory** until fixed. (Enforced by `vacuity_lint.py`.)
3. **Check for unused load-bearing hypotheses.** If the named mechanism's
   hypothesis is present but the proof never uses it → **Bridge-assumption**.
4. **Check name ≤ conclusion.** If the name claims strictly more than the type
   (e.g. "exactly two components" vs. `¬Connected`; "perfect complements" vs.
   `F(P,0)=0`) → down-label and add a NOT-established note.
5. **Separate math from world.** A clean theorem about a *model* is **Derived**
   for the model and **Empirical-hypothesis / Conditional** for the world.

## Why this exists (the "verification halo")

The single largest credibility risk to a machine-verified research program is
that readers collapse three different statements into one:

> (a) Lean accepts the proof. (b) The proof follows from physically meaningful
> assumptions. (c) Those assumptions describe reality.

Only (a) is automatic. This taxonomy forces every result to declare where it sits
on (a)→(b)→(c). Grading our own claims by formal strength is not a weakness of the
canon — it is the differentiator: it is what lets a sophisticated critic trust the
**Derived** results precisely because we have not oversold the **Conditional** and
**Exploratory** ones.
