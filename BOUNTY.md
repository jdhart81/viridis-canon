# Theorem bounty

> **Update: the cash bounty is closed to new reports.**
> Reports opened before this notice was published (the merge time of the pull
> request that added it) are still reviewed under the original terms below,
> including the $500 total cap. Reports opened after that are credit only: a
> confirmed finding goes in the ledger with your name and is acknowledged on the
> affected result page and in the paper's next version. How findings are judged
> has not changed.

I started this bounty to bring careful outside readers to the canon, and more of
you showed up than I planned for. I can't fund an open-ended cash program, so I'm
closing it to new cash claims rather than let the promise outrun what I can pay.
Every report already filed gets a real review under the terms it was filed under.
— Justin

## What counts

A finding is eligible when it concerns a theorem or witness listed for a run in
[`certificates/index.json`](./certificates/index.json) and shows one of:

1. **Vacuous.** The hypotheses cannot all hold at once, or the conclusion holds
   for a degenerate reason that empties the paper's claim. Our non-vacuity
   witnesses are meant to rule this out; a witness that does not actually
   instantiate the hypotheses it claims to is a finding.
2. **Trivial.** The paper presents a theorem as a substantive result, but it is a
   restatement of a hypothesis or follows in one step from the definitions. Seven
   runs are already labelled *elementary* in the index; an elementary theorem is
   only a finding if the paper claims more than it proves.
3. **Misstated.** The Lean statement does not match the paper's prose claim: a
   missing or extra hypothesis, a wrong quantifier or inequality direction, a
   weaker claim than the paper states, or a challenge file that states something
   other than what the certificate describes.

Machine checking proves that a Lean statement follows from its hypotheses. It
cannot tell you whether the statement says what the paper claims, or whether it
says anything at all. That is where outside eyes help most.

## What does not count

- Disagreement with a modelling assumption that the paper or the result page
  states explicitly. Those are welcome in [Discussions](https://github.com/jdhart81/viridis-canon/discussions),
  but they are not bounty findings.
- Style, naming, proof length or performance.
- Material outside the 18 certified runs in [`certificates/`](./certificates/).
- Issues already recorded in the ledger below, or already disclosed in
  `certificates/README.md` (for example, the three runs whose challenge file is
  identical to the solution).
- Reports from Viridis staff or contractors.

## How to report

Open an issue with the **Theorem bounty report** template. Give the run, the
theorem name, the category, and your argument. A short Lean snippet (a
counterexample, or a proof that the hypotheses are contradictory) makes
confirmation fast but is not required.

## What a confirmed finding earns

**Reports opened after this notice was published: credit.** Your name and the
finding go in the ledger below, and the affected result page and the paper's next
version acknowledge you. There is no cash award.

**Reports opened before this notice was published: the original terms.**
We pay **$50** for each confirmed vacuous, trivial or misstated theorem, up to
**$500** in total across all reports. Do not post payment details in the issue;
if a report is confirmed, we contact you privately. Payment is made within 30
days of confirmation by a method agreed with you. Void where prohibited.

## How findings are decided

- Justin D. Hart, the accountable author, decides each report and explains the
  decision in the issue.
- The first eligible report of a given defect receives the award (cash under the
  original terms, credit after). Duplicates are credited in the ledger.
- Every confirmed finding is fixed or relabelled, and the affected result page,
  manifest and Zenodo record are corrected.

## Ledger

| Date | Run | Theorem | Category | Reporter | Outcome |
|---|---|---|---|---|---|
| 2026-10-29 | Run-133 | `Viridis.HDFM.CorridorOverlapDuality.synchrony_dividend_identity` (C1) | Misstated | @BeakDo ([#152](https://github.com/jdhart81/viridis-canon/issues/152)) | Confirmed, $50 under the original terms. The paper derives C1's finite-path factorization; the mapped theorem took it as an input. Repair: `finite_path_factorization`, supplied by @BeakDo, integration by @tim777z in [#167](https://github.com/jdhart81/viridis-canon/pull/167). |
| 2026-10-29 | Run-129 | `bounded_overshoot_expected_delay` (C4) | Misstated | @mak777uh ([#121](https://github.com/jdhart81/viridis-canon/issues/121)) | Confirmed, $50 under the original terms. The Lean statement adds a uniform two-sided bound on the increments; the paper assumes only an upper bound plus the usual Wald integrability, so the certified theorem covers a bounded-increment special case. Documentation correction to follow. |
