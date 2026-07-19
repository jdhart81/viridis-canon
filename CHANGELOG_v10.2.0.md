# CHANGELOG — Canon v10.2.0 "The Equilibrium Wave"

**Date:** 2026-07-19
**Parent:** v10.1.0 (record `21223021`, the Keystone Wave)
**Authorization:** Spine version bump authorized by Justin D. Hart on 2026-07-19 ("push the updated spine version"), applied to the full ready backlog of six Aristotle-verified nightly results (ledger rows 55–58, 60–61), all previously routed **spine + branch** by standing curation authority (`CANON_SPINE_DOCTRINE.md` §6). This is a MINOR bump (v10.1 → v10.2): no MAJOR trigger is in play (axiom set unchanged, no package restructuring, no breaking change to a published theorem) — see `CANON_SPINE_DOCTRINE.md` §7.

## Added to the spine (6 modules, all zero `sorry`, axioms subset-of {propext, Classical.choice, Quot.sound})

### `EffortlessEquilibrium.lean` — Effortless Equilibrium Theorem (EET, "the Steersman")
Nightly Run-097 (2026-07-13). Aristotle project `65ae007a-5c0f-4605-9027-0402c42ca0c6`. 11 named results. 39th IB self-application. Wu-wei rest states exist on nonempty compact domains (EVT); rest iff grad(Phi)=0; a forced non-attractor admits no rest state; holding power P_hold = gamma^-1||grad(Phi)||^2 >= 0 with equality exactly at rest; harmonization toward an attractor is strictly cheaper than forcing a non-attractor; the IB floor on forcing time.

### `PerennialCorridor.lean` — Perennial Corridor Theorem (PCT, "the Gardener")
Nightly Run-098 (2026-07-14). 15 named results. Whittle-index corridor urgency is homogeneous of degree 1 and ranks by centrality; the unimodal superlevel set is an order-convex band; the stewardship dividend is nonnegative; the IB floor on maintenance holding power is monotone in information.

### `DecoherentSelection.lean` — Decoherent Selection Theorem (DST, "the Chooser")
Nightly Run-099 (2026-07-15). 12 named results. 41st IB self-application. Decision cost is nonnegative and vanishes iff the pointer-basis eigenstate is selected; ambiguity cost is bounded by ln N and maximal at the uniform distribution; the einselected basis is the unique zero-waste choice (basis efficiency = cos^2(Theta)); the IB throughput speed limit applies to collapse.

### `MutualisticAttestation.lean` — Mutualistic Attestation Theorem (MAT, "the Attester")
Nightly **Run-100** (2026-07-16 — 100th nightly-run milestone). 19 named results. 42nd IB self-application. Attestation cost = k_BT*ln2*(residual entropy), zero iff evidence is decisive, maximal at the equivocal read; certification feedback exhibits fold bistability (trap and mutualism are the two stable states, the separatrix is unstable); optimal confidence is interior; attestation efficiency = cos^2(Theta).

### `ThermodynamicAttention.lean` — Thermodynamic Attention Theorem (TAT, "the Attuner")
Nightly Run-101 (2026-07-17). 12 named results. 43rd IB self-application. The rational-inattention shadow price equals the Landauer quantum k_BT; the wu-wei optimum sets the marginal cost of nonpredictive information to zero; attention water-fills the einselected slow basis per the KKT conditions, filling slow modes first; an Inattention Trap opens below a resolvability threshold C_crit.

### `StewardshipSetpoint.lean` — Stewardship Setpoint Theorem (SST, "the Steward")
Nightly Run-102 (2026-07-18). 13 named results. 44th IB self-application. **First-ever [01] Intelligence Bound x Stewardship pairing** — the act-budget twin of TAT. A living renewable stock dD/dt = g(D) - phi*H obeys a golden-rule sustainable ceiling Omega*D*, with closed form D* = (K/2)(1 - r/rho); Tragedy-of-the-Commons collapse follows for phi*Omega > rho.

Four of the six (EET, PCT, DST, MAT) are R6 members of the eta = cos^2(Theta) basis-efficiency family alongside the already-published HEWT/ESOT/MCET (2026-07-12 working-corpus batch). Their meta-unifier, **UPEM** (Universal Projection-Efficiency Meta-Theorem, ledger row 59), is verified clean and gate-passed but is **held back from this wave** pending a journal-quality paper (INV-PAPER — every gate-passed Lean result needs a paper before submission; none yet exists for UPEM since it was orchestrator-queued rather than nightly-run-sourced). UPEM is expected to fold into a near-term v10.3.0 once its paper is written.

All six modules added to `SPINE_MANIFEST.txt`, `lakefile.toml` `defaultTargets` + `lean_lib` entries, and `AxiomAudit.lean`'s import list and `viridisSpineModules`. No changes to `viridisAllowedAxioms`.

## Not admitted to this wave
- **UPEM** (Universal Projection-Efficiency Meta-Theorem) — verified clean, spine-candidate, blocked on INV-PAPER (see above). Ledger row 59 remains AWAITING JUSTIN OK pending paper.
- **PVT** (Run-103, "the Metronome") — still in flight at Aristotle as of 2026-07-19, not yet landed.

Spine now stands at v10.2.0. Concept DOI `10.5281/zenodo.19317982` resolves here.
