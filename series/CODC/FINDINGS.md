# Run-133 outside findings

Outside readers found two places where a certified Run-133 theorem took as a
hypothesis a step that the paper, *The Corridor Overlap Duality Certificate*
([10.5281/zenodo.22665525](https://doi.org/10.5281/zenodo.22665525)), derives.
Both are confirmed and recorded in the [bounty ledger](../../BOUNTY.md#ledger).
The repairs go into the Run-133 re-certification tracked in
[#194](https://github.com/jdhart81/viridis-canon/issues/194); until that lands,
the certified files and `COMPARATOR_SUMMARY.md` in this folder are unchanged.

| Claim | Theorem | Finding | Credit |
|---|---|---|---|
| C1 | `synchrony_dividend_identity` | Misstated: takes the finite-path factorization as an input (`ProductFactorization`) that the paper derives. Repair: `finite_path_factorization` via `Finset.prod_union_inter`. | @BeakDo, reporter and repair ([#152](https://github.com/jdhart81/viridis-canon/issues/152)); @tim777z, integration ([#167](https://github.com/jdhart81/viridis-canon/pull/167)) |
| C5 | `additive_shared_cost_saving` | Trivial: the hypothesis `costA + costB = costUnion + costShared` is the conclusion rearranged, so the theorem holds for any four reals and says nothing about edges or paths. Paper Proposition 2's content is inclusion–exclusion for finite sums. Repair: state C5 over `Finset` sums of edge costs and derive it from `Finset.sum_union_inter`. | whhhh1500 ([#158](https://github.com/jdhart81/viridis-canon/issues/158)) |

## For the next version of the paper

The next Zenodo version of 10.5281/zenodo.22665525 acknowledges both findings by
name: BeakDo (C1, with integration by tim777z) and whhhh1500 (C5). It should
also restate C1 and C5 in the repaired form, or label them as assumed identities
if the re-certification has not landed by then.

This note records findings and credit. It does not change what the existing
certificate establishes; see [`certificates/README.md`](../../certificates/README.md).
