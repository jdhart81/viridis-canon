# Comparator certificates

This folder publishes the evidence behind the Viridis results whose main
theorems were checked by [comparator](https://github.com/leanprover/comparator),
the Lean FRO's challenge/solution checker. For each certified run you get the
exact files the certificate binds by SHA-256, so you can confirm the chain
yourself and re-run the check on your own machine.

| Run | Result | DOI | Depth | Theorems | OS function |
|---|---|---|---|---|---|
| Run-129 | Anytime monitoring change certificate (Ville's inequality, mixture martingale, Wald-type delay bound) | [10.5281/zenodo.21971041](https://doi.org/10.5281/zenodo.21971041) | substantial | 4 | `anytime-change` |
| Run-130 | Seed-source bottleneck certificate (capacitated Hall / min-cut) | [10.5281/zenodo.21971057](https://doi.org/10.5281/zenodo.21971057) | substantial | 4 | `seed-source-bottleneck` |
| Run-127 | Moment-robust precautionary capacity (Cantelli bound, sharp two-point counterexample) | [10.5281/zenodo.21971046](https://doi.org/10.5281/zenodo.21971046) | substantial | 5 | `precautionary-capacity` |
| Run-128 | Bilateral-benefit reciprocity corridor (Nash bargaining midpoint) | [10.5281/zenodo.21971047](https://doi.org/10.5281/zenodo.21971047) | substantial | 5 | `reciprocity-corridor` |
| Run-126 | Forbidden-proxy information capacity audit | [10.5281/zenodo.21971043](https://doi.org/10.5281/zenodo.21971043) | substantial | 5 | `invariance-capacity` |
| Run-125 | Shared-channel coverage audit | [10.5281/zenodo.21971052](https://doi.org/10.5281/zenodo.21971052) | substantial | 6 | `shared-channel-coverage` |
| Run-132 | D-Score weight-charter certificate (sharp rank-stability bound) | [10.5281/zenodo.22236741](https://doi.org/10.5281/zenodo.22236741) | substantial | 6 | `dswc-tv-range-certificate` |
| Run-124 | Pivotal corridor stewardship (exact reliability gradients) | [10.5281/zenodo.22665554](https://doi.org/10.5281/zenodo.22665554) | substantial | 9 | `pcs-reliability-derivative-eq-pivotal-probability` |
| Run-122 | Zeno alignment budget | [10.5281/zenodo.22236789](https://doi.org/10.5281/zenodo.22236789) | substantial ¹ | 6 | `zab-uniform-zeno-schedule-maximizes-success` |
| Run-121 | Information symbiosis balance | [10.5281/zenodo.22236761](https://doi.org/10.5281/zenodo.22236761) | substantial ¹ | 4 | `isb-information-symbiosis-chain-rule` |
| Run-120 | Conjunctive audit stewardship | [10.5281/zenodo.22236735](https://doi.org/10.5281/zenodo.22236735) | substantial ¹ | 14 | `cast-conjunctive-chain-weakest-first` |
| Run-137 | Symbiotic accounting certificate | [10.5281/zenodo.22236768](https://doi.org/10.5281/zenodo.22236768) | elementary | 9 | `sac-conjunctive-rate-upper-bound` |
| Run-138 | Gaian alignment cone certificate | [10.5281/zenodo.22236748](https://doi.org/10.5281/zenodo.22236748) | elementary | 8 | `gacc-aggregate-residual-bound` |
| Run-123 | Free-energy floor for habitable-state concentration | [10.5281/zenodo.22236755](https://doi.org/10.5281/zenodo.22236755) | elementary | 7 | `hcf-kl-chain-rule-habitable-partition` |
| Run-131 | Directional switching hysteresis | [10.5281/zenodo.21971042](https://doi.org/10.5281/zenodo.21971042) | elementary | 5 | `switching-hysteresis` |
| Run-133 | Corridor overlap duality | [10.5281/zenodo.22665525](https://doi.org/10.5281/zenodo.22665525) | elementary | 6 | `codc-synchrony-dividend-identity` |
| Run-135 | Sufficient sanitization certificate | [10.5281/zenodo.22236775](https://doi.org/10.5281/zenodo.22236775) | elementary | 5 | `ssc-relevance-chain-identity` |
| Run-139 | Ecological-thermodynamic capital allocation | [10.5281/zenodo.22236785](https://doi.org/10.5281/zenodo.22236785) | elementary | 6 | `thermodynamic-economic-allocation` |

[`index.json`](./index.json) is the authoritative, machine-readable list. It
records, per run, the certificate gates, toolchain (`leanprover/lean4:v4.28.0`),
Mathlib revision (`8f9d9cff6bd728b17a24e163c9402775d9e6a365`, the same pin as
this repository's `lake-manifest.json`), the theorem names, the permitted
axioms, the OS function that uses the result, and the depth metrics.

**Depth** is a size indicator, not a verdict on novelty or importance:
*substantial* means the certified file has at least 200 non-blank lines and the
median proof of its listed theorems runs at least 6 lines; everything else is
*elementary*. Several elementary results are exact identities or one-step
consequences of a definition. They are correct and useful inside a decision
kernel, but we do not present them as deep mathematics.

¹ For Runs 120–122 the challenge file is byte-identical to the solution: the
statements were frozen together with their proofs rather than separately.
Comparator still kernel-checks every theorem and audits its axioms, but the
"statement matches the challenge" step is trivially satisfied for these three.

## What a certificate establishes, and what it does not

A certificate here records that, on the Viridis Comparator service:

- the listed theorems are proved in the solution file, with zero `sorry`;
- their statements match the challenge file;
- they use only `propext`, `Quot.sound` and `Classical.choice`;
- both the Lean kernel and the independent [nanoda](https://github.com/ammkrn/nanoda_lib) kernel accept them;
- non-vacuity witnesses for the hypotheses also check.

It does **not** establish:

- that a formal statement captures the paper's prose claim (see each run's `SEALED_CLAIM_INVENTORY.json` and statement-alignment receipt, and judge for yourself);
- that the model's assumptions hold in any ecosystem;
- that a result is new;
- that a decision built on it is correct.

Every OS function that uses these results carries `empirical_validation: NOT_VALIDATED`.

## Check it yourself

1. **The hash chain, in a second, no Lean needed:**

   ```bash
   python3 certificates/verify_bundle.py
   ```

2. **The axioms, in a few minutes, Lean only.** The script builds a throwaway project at the pinned toolchain and Mathlib revision, fetches the Mathlib cache, elaborates the certified solution and audits every theorem's axioms:

   ```bash
   certificates/rerun.sh Run-129 --axioms-only
   ```

3. **The full comparator check.** Install [comparator](https://github.com/leanprover/comparator) and its prerequisites, then:

   ```bash
   COMPARATOR=/path/to/comparator certificates/rerun.sh Run-129
   ```

Each run directory also holds `comparator.config.json`, generated from the
certificate's request and receipt by `tools/build_certificates_index.py`.

If your result differs from ours in any way — a failure, a different axiom, a
statement you think does not mean what the paper says — please open an
[external-validation report](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml).
Failed and inconclusive reproductions are kept as evidence, not deleted.

## Not yet in this folder

Five more admitted or callable kernels cite Comparator receipts issued under
older identifiers:

- restoration
- afforestation
- harmonization
- tempo
- carbon continuity

Mutualist also cites one, and stays blocked. Their receipt bundles will be added here as they are exported in the same byte-exact form.
