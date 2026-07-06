# CHANGELOG — Canon v10.1.0 "The Keystone Wave"

**Date:** 2026-07-06
**Parent:** v10.0.0 (record `20801185`, the Core-Extension Wave)
**Authorization:** Spine freeze-break pre-authorized by Justin D. Hart on 2026-06-29 ("ok update to 10.1"), scoped to UWMT; confirmed and extended on 2026-07-06 after applying the five-gate Spine Admission Test (`CANON_SPINE_DOCTRINE.md`) to the full backlog of seven Aristotle-verified nightly results then in `ZENODO_SUBMISSION_LEDGER.md`. Two passed all five gates and are admitted here; the other five (MINT, SRT, IET, SCT, GNT) are published the same day as series/standalone records — they remain outside the spine.

## Added to the spine (2 modules, both zero `sorry`, axioms subset-of {propext, Classical.choice, Quot.sound})

### `UniversalWaterfilling.lean` — Universal Water-Filling Meta-Theorem (UWMT, "the Keystone")
Nightly Run-084 (2026-06-29). Aristotle project `da92404c-11ad-45c9-9778-2be6065adc4b`. 8 named results.
Unifies the nine-member shadow-price / water-filling family (the Pacer, the Appraiser, the Verifier, the Surveyor, the Sower, the Harmonizer, the capacity-Harmonizer, and others) into one variational object with two control knobs -- curvature of the per-channel value and temperature of an entropic regularizer -- with the multiplier lambda simultaneously the water level, the economic shadow price, and the thermodynamic free energy (`dV*/dB = lambda`). Passes the Spine Admission Test: it is the meta-theorem the prior family members are corollaries of, not a domain application.

### `GeodesicSaturation.lean` — Geodesic Saturation Theorem (GST, "the Sage")
Nightly Run-086 (2026-07-01). Aristotle project `f864600a-b328-4e7b-9473-476a3b0799c2`. 6 named results.
Characterizes the Intelligence Bound's own equality/saturation condition: `dI/dt = (P - F)*c`, the bound holds iff `0 <= F` (forcing), and it saturates -- is met with equality -- iff `F = 0` (a constant-speed Fisher-Rao geodesic; wu wei made literal). Names UWMT as its "multichannel shadow," forming a coherent milestone wave with it. Passes the Spine Admission Test: this is the IB's own saturation geometry, not an applied result.

Both modules added to `SPINE_MANIFEST.txt`, `lakefile.toml` `defaultTargets` + `lean_lib` entries, and `AxiomAudit.lean`'s import list and `viridisSpineModules`.

## Housekeeping fix (pre-existing drift, corrected in this release)
The local `01_MATHLIB/Aristotle-Pipeline` working tree had not been synced after the v10.0.0 Zenodo publish -- `SymbioticIntelligenceBound.lean`, `MRAB.lean`, the v10.0.0 `lakefile.toml`/`SPINE_MANIFEST.txt`/`AxiomAudit.lean` were present in the published record and the GitHub mirror but missing from the local pipeline directory. Synced from the published v10.0.0 package before layering in v10.1's two new modules, so the working tree now matches what's actually live.

## Not admitted to the spine (published same day as series/standalone -- see `ZENODO_SUBMISSION_LEDGER.md` rows 42-46)
- **MINT** (Mutualistic Inference Network Theorem) -- N-agent generalization of SIB; still a domain application (cognitive/multi-agent networks) with deferred gate-checked pieces. Standalone.
- **SRT** (Stewardship Revisit Theorem) -- extends the D-Score monitoring stack; routed to S2 (Monitoring), matching its sibling MWT.
- **IET** (Intelligence Exergy Theorem) -- second-law completion of the Intelligence Capacity Framework; reuses the established cos^2(Theta)/exergy template rather than introducing new core machinery. Standalone.
- **SCT** (Symbiotic Corridor Theorem) -- explicit generalization of CST; routed to S5 (Corridors), matching its parent.
- **GNT** (Grokking Nucleation Theorem) -- sibling of HDT in the learning-transition taxonomy; routed to S6 (Cognition & Learning), matching HDT.

Spine now FROZEN at v10.1.0 (this record). Concept DOI `10.5281/zenodo.19317982` resolves here.
