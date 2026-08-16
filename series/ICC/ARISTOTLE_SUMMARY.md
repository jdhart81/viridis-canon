# Summary of changes for run 074fac38-39da-4b38-b9ff-53dd6a18281a
Re-ran the frozen `PaperFormalization` project unaltered and verified it end to end. No theorem, definition, proof body, namespace, witness, toolchain, or statement-contract text was modified, and no Git, commit, push, or publication action was performed.

**Environment actually used (matches `EXACT_STATEMENT_CONTRACT.md` §1)**
- `lean-toolchain`: `leanprover/lean4:v4.28.0`; Lake 5.0.0 (Lean 4.28.0).
- Vendored mathlib checkout HEAD: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`, its own `lean-toolchain` `leanprover/lean4:v4.28.0`.

**Build evidence** — `lake build PaperFormalization`:
```
✔ [8026/8032] Built PaperFormalization.Entropy (31s)
✔ [8027/8032] Built PaperFormalization.ChainRule (14s)
✔ [8028/8032] Built PaperFormalization.Claims (15s)
✔ [8029/8032] Built PaperFormalization.ZeroCovariance (19s)
✔ [8030/8032] Built PaperFormalization.ErasureFamily (21s)
✔ [8031/8032] Built PaperFormalization (13s)
Build completed successfully (8032 jobs).
```
Each of the five source files was additionally elaborated individually (`lake env lean PaperFormalization/<File>.lean`), producing no errors and no warnings.

**`#print axioms` evidence** — running `AxiomCheck.lean` unchanged reports, for all ten named declarations (`mutual_information_chain_balance`, `forbidden_proxy_capacity_ceiling`, `capacity_ceiling_slack_decomposition`, `perfect_invariance_target_proxy_collapse`, `erasure_family_tightness`, and the five corresponding `_nonvacuity` obligations, all in `Viridis.Run126.PaperFormalization`):
```
depends on axioms: [propext, Classical.choice, Quot.sound]
```
The same three-axiom result was also confirmed for `forbidden_proxy_capacity_ceiling_combined` (Eq. 4), `H_Y_given_S_eq_zero_of_diagonal`, and `zero_covariance_does_not_certify_invariance` (inventory claim C7, the bonus nonlinear negative control).

**Escape audit** — a full-text scan of all `.lean` sources found no `sorry`, `admit`, `sorryAx`, `axiom` declaration, `@[implemented_by]`, `native_decide`, `unsafe`, `extern`, `opaque`, or `partial def`. Allowed axioms only.

**Contract conformance** — I read every file and compared the statements against `EXACT_STATEMENT_CONTRACT.md`: the `JointLaw` structure, `Hs`, the six information quantities in divergence form (so C1/C3 are genuine theorems rather than definitional unfoldings), the chain-rule identities, the Gibbs inequality and the nonnegativity results, the five frozen targets C1–C5 with their exact signatures and namespace, the five non-vacuity witnesses (`diagLaw`, `indepRLaw`, `uniformLaw`, `erasureLaw` at `q = 1/2`), and the C5 tightness conjunct `I(R;Y) = H(Y|S) + q`. All match verbatim; nothing was weakened, renamed, or reinterpreted.

The Properties table lists the five frozen targets, their non-vacuity obligations, the Eq. 4 combined ceiling, the C7 control, and the definitions they are stated in terms of, each marked according to the verified outcome above.

Scope note: this is a machine-checked proof result only. It makes no claim of empirical validation, reconciliation, ledger or canon admission, publication readiness, or publication authority, and it does not affect the separate classification state `HOLD_SIGNIFICANCE_NONTRIVIALITY_UNCLEARED`.