# Forward generation premise guard

`generation_premise_guard.py` adds an authoring check for future, unsealed papers.
Every allowed actual basis (`THEOREM`, `CONDITIONAL_PL_PD`, `INDEPENDENT`) must
appear as an affirmative declaration at the start of the first visible abstract
paragraph. Foundation/Formal wording and bounded nested emphasis are accepted.
Quoted examples, definitions, hidden text and conditional TeX cannot supply the
declaration. The guard preserves the existing statement, candidate and manuscript
text for the unchanged INV-9 predicates.

For independent work, the draft sentence is:

> The foundation basis is INDEPENDENT; no framework-level bound or PL/PD premise is used.

The guard calls the exact hash-bound `premise_declaration.evaluate` with
`required=True`. PASS is required for the same basis, without a historical
exemption. Its exact title dependency is also bound before compilation. A static
PASS is neither a proof nor a certificate, and no local Lean executes. Source
and input reads are bounded and rechecked; optional import bytecode writes are
suppressed. `require_staged_manifest` additionally binds and rechecks the actual
draft manifest bytes.

The current authoritative Codex per-run builder and Core package preseal module
are outside this repository. This module alone does not install a generation
fix. Private, exact-target review patches add checks before package/request/final
manifest writes and before the first live-directory rename/state advance. The
Core proposal requires an explicit future-generation opt-in, preserving historical
preseal consumers. Adoption of the reviewed helper and those call sites remains
a separate source-deployment step. Existing sealed runs and INV-9 files remain
unchanged.

Run the focused source regressions from this directory:

```sh
python3 -B -m unittest test_generation_premise_guard test_premise_declaration test_inv9_title_basis
```

The regressions use synthetic public fixtures. Private integration evidence
applies both patches to disposable single-file copies, then executes the patched
write, seal, finalize, commit and opt-in preseal functions against synthetic
stages. It demonstrates that a premise HOLD precedes any boundary mutation; it
does not generate a paper, advance state or install Core code.

Staging paths must have no symlinked ancestor. On macOS, use the physical
`/private/tmp` or `/private/var` form; the `/tmp` and `/var` aliases are refused.
Malformed UTF-8, JSON, or object shapes produce labeled premise HOLDs before
any sealing, request, rename, or state write.
