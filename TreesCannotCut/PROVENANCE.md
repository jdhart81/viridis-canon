# Trees Cannot Cut, rung L2: provenance

Both Lean files in this module are byte-identical copies of the engine-certified pair
from the public record `jdhart81/viridis-research`, folder `runs/2026-11-09_P1`
(engine task P1-T003, certified 2026-11-09, engine commit `8c1757ff`).

| Canon path | Engine path | sha256 |
|---|---|---|
| `ViridisStatements/P1/Insertion.lean` | `lean/P1.Insertion/Statement.lean` | `800bd9b9fec5033192b40a9d02dae8abf5c15195b3e2b6f2a1c438a7ab08c734` |
| `TreesCannotCut/Insertion.lean` | `proofs/P1.Insertion.lean` | `e31434107d76a387f2bd47d3752511581084d3195b2563373ad279fbc907d670` |

The statement file sits at `ViridisStatements/P1/Insertion.lean` so that the proof's own
`import ViridisStatements.P1.Insertion` resolves without editing either file.

Engine certification (`certification.json`): PROVEN by kernel replay on Lean 4.28.0 /
Mathlib `8f9d9cff`, axioms `propext`, `Classical.choice`, `Quot.sound` only. The canon
spine build and `AxiomAudit` check the same files again on the same toolchain.

Check the copies with:

    sha256sum ViridisStatements/P1/Insertion.lean TreesCannotCut/Insertion.lean
