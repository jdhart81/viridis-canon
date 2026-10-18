# Theorem bounty

We pay **$50** for each confirmed **vacuous, trivial or misstated theorem** among
the 18 certified runs in [`certificates/`](./certificates/). The program pays at
most **$500** in total and runs until **2027-01-31** or until the cap is reached,
whichever comes first.

Machine checking proves that a Lean statement follows from its hypotheses. It
cannot tell you whether the statement says what the paper claims, or whether it
says anything at all. That is where outside eyes help most, so we pay for them.

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

## What does not count

- Disagreement with a modelling assumption that the paper or the result page
  states explicitly. Those are welcome in [Discussions](https://github.com/jdhart81/viridis-canon/discussions),
  but they are not bounty findings.
- Style, naming, proof length or performance.
- Material outside the 18 certified runs.
- Issues already recorded in the ledger below, or already disclosed in
  `certificates/README.md` (for example, the three runs whose challenge file is
  identical to the solution).
- Reports from Viridis staff or contractors.

## How to report

Open an issue with the **Theorem bounty report** template. Give the run, the
theorem name, the category, and your argument. A short Lean snippet (a
counterexample, or a proof that the hypotheses are contradictory) makes
confirmation fast but is not required.

Do not post payment details in the issue. If a report is confirmed, we contact
you privately.

## How findings are decided and paid

- Justin D. Hart, the accountable author, decides each report and explains the
  decision in the issue.
- The first eligible report of a given defect is paid. Duplicates are credited
  in the ledger but not paid.
- Payment is made within 30 days of confirmation by a method agreed with you.
  Void where prohibited.
- Every confirmed finding is fixed or relabelled, and the affected result page,
  manifest and Zenodo record are corrected.

## Ledger

| Date | Run | Theorem | Category | Reporter | Outcome |
|---|---|---|---|---|---|
| — | — | — | — | — | No findings yet. |
