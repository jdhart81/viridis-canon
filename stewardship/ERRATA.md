# Narrow stewardship and attention errata

Baseline Git: `20b684f42a242d17a642fdcd16eda50cc9b650f8`.
Starting HEAD: `85505cfe7f2f8d3977a96e18ea6d27a6ae8dd692`.
The two relevant modules were identical between those commits. Zenodo record
21444226's ZIP was downloaded read-only; its published MD5 matched, and its
SST and TAT Lean bytes matched the comparison commit. The ZIP SHA-256 and
per-file comparisons are in `evidence/zenodo-comparison.json`. This does not
assert equivalence of all deposit files to a Git tree. Published artifacts
and existing proof environments were not rewritten.

| Historical statement/name | Actual content and correction |
|---|---|
| `setpoint_J_beats_forcing_J` | Proves 0<g(Dstar)/r. It never defined or compared two lifetime objectives. Eventual zero throughput does not erase early output. Canonical name is now `raw_setpoint_regeneration_discount_positive`; old name is a deprecated alias. New `raw_lifetime_regret` is an actual integral comparison including φ. |
| `sustCeiling` / sustainable ceiling | Value is ΩDstar, an instantaneous capacity at that stock. Sustainable held rate is g(Dstar)/φ, requiring Ω≥(α+r)/(2φ) for the raw setpoint. Definition retained for compatibility; its meaning is explicitly corrected. |
| `uStar` | Legacy formula (α+r)/(2Ω) assumes φ=1. General raw duty is (α+r)/(2φΩ), information-weighted duty (α+r)/(3φΩ). Corrected family uses explicit φ. Existing legacy proofs are retained as normalized algebra only. |
| `forcing_collapses_capacity_when_phiOmega_gt_rho` | Concludes strictly negative drift at a positive stock, not D(t)→0. Renamed `forcing_drift_negative_when_phiOmega_gt_rho`, with a deprecated alias. The new benchmark's explicit forcing solution has a separately derived analytical limit and exponential bound. |
| `orar_extremum_seeking_converges_to_Dstar` | Derivative signs, not convergence of a specified algorithm. Renamed `potential_derivative_points_toward_Dstar`; deprecated alias retained. |
| sustainable ratio ≤1/2 | Dstar/K is a stock fraction. It is not a theorem that actual sustained output is half capacity. Canonical theorem renamed `raw_stock_ratio_le_one_half`. |
| `attention_shadow_price_eq_landauer_quantum` | Differentiates the defined attnCost=kBT·I and evaluates it at ln 2. Canonical name is `assumed_linear_attention_cost_derivative`; old name deprecated. Formal: Definition-expansion. Physical price: Empirical-hypothesis / bridge requiring independent justification. |

The information-weighted certificate does not repair or validate a universal
thermodynamic attention-price claim. Original authorship, source provenance,
licenses and proof terms remain; corrected names and documentation avoid
attributing the new local proof to historical Aristotle runs.

The existing hygiene script used Bash `mapfile`, unavailable in macOS Bash 3.
Its array-loading lines now use equivalent read loops. All manifest inputs,
comment stripping, no-hole checks, axiom checks and vacuity checks are unchanged.
The initial failure is preserved in `evidence/baseline/hygiene.log`.


Integration review: changing Lean source bytes correctly invalidated the two
existing theorem-function source bindings. `evidence/source-binding-review.json`
records exact declaration/proof equality modulo the stewardship rename. Only
these directly affected manifests were repinned, with their numerical expressions,
hypotheses and admission tiers unchanged. The stewardship function's returned
theorem-name string now names `potential_derivative_points_toward_Dstar` and its
manifest version is 1.1.0; the attention metadata correction is 1.0.1. This is a
reviewable metadata/API-label change, not a deployed runtime change. No admission
ledger or business application was modified. All 42 manifests validate afterward.
The three initial integration failures remain in final-verification-1 logs.

The historical P0 build generated its previously absent Lake lockfile, recording
the already-declared f897 Mathlib revision and resolved transitive dependencies.
The lockfile is included for reproducibility; no toolchain or Mathlib upgrade
was made. Baseline initial-status.txt was captured after creating the evidence
folder, so its sole untracked entry is that folder; the clone was clean before it.
