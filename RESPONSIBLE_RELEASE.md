# How Viridis releases AI-assisted science

AI systems help produce most of the results in this repository. Some propose the
models and arguments; some draft the Lean proofs. So the questions now being asked
of AI-generated mathematics apply to us too.

In September 2026 the
[Advisory Group on Mathematics and Artificial Intelligence](https://agmai.org/)
published recommendations for the
[responsible release of AI-generated mathematics](https://agmai.org/general-sep29/),
based on responses from more than 600 mathematicians. A week later a large batch
of AI-generated manuscripts was released as a Git repository. Critics noted that
most of its results were not machine-checked, that no named person answered for
each paper, and that nothing had a persistent identifier.

Viridis is not an AI lab, and our results are applied: ecology, conservation and
land-use decisions, not open problems in pure mathematics. We hold ourselves to
the same standard anyway. This page sets out what we do against each
recommendation, including where we fall short.

## The recommendations, one by one

| Recommendation (paraphrased) | What Viridis does | Where to check | Gap we know about |
|---|---|---|---|
| **Readable write-ups that cite prior work.** | Every result ships with a paper (PDF and TeX source) and a bibliography. | The `paper` DOI for each result in [`formalization.yaml`](./formalization.yaml). | How thoroughly papers cover prior work varies. If we missed something, tell us through an [external-validation report](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml). |
| **Deposit in an independent repository with persistent identifiers that record changes.** | Every release has a Zenodo DOI. Zenodo is run by CERN, not by us. It keeps prior versions and logs metadata changes through DataCite. This Git repository holds the working source; the DOIs are the record. | The concept DOI [10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982). The [`viridis-canon` Zenodo community](https://zenodo.org/communities/viridis-canon) holds the 11-record publication tier; every other record is in the [`viridis-canon-archive` community](https://zenodo.org/communities/viridis-canon-archive), still public with the same DOI. | None. |
| **Disclose the model, prompts, a reasoning summary, time and compute.** | [`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md) names each tool and its role. Certified runs carry provenance receipts, such as `CODEX_AUTHORSHIP_AND_PROVENANCE_RECEIPT.json`. | [`certificates/`](./certificates/) | **Gap:** there is no per-result table yet of model versions, prompts, wall-clock time and compute. We will publish one. |
| **Formalize to community standards: a challenge file for comparator, `formalization.yaml`, and machine-readable links between paper and proof.** | Each certified result has a comparator challenge/solution pair, checked by both the Lean kernel and the nanoda kernel. We publish the byte-exact files and the certificate that binds them, a re-run script, and a `formalization.yaml` linking each result's paper, Lean module, theorems, verifier and empirical status. | [`certificates/`](./certificates/) and [`formalization.yaml`](./formalization.yaml) | **Gap:** this release covers 18 certified runs. Another 60 runs are certified internally and still have to be exported in the same form. Six older kernel receipts are also still to come. |
| **Document AI use for each problem. Publish every result, the attempts that failed, and how problems were chosen.** | See the denominator below. | This page and [`certificates/index.json`](./certificates/index.json) | **Gap:** the reason each uncertified run failed is not published yet. |
| **A human who answers for each result.** | Justin D. Hart ([ORCID 0009-0008-3082-2482](https://orcid.org/0009-0008-3082-2482)) is the accountable author. AI tools are not authors. | [`CITATION.cff`](./CITATION.cff) and [`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md) | Corrected on 2026-10-18: no latest Zenodo record lists the Aristotle theorem prover as a creator; where it was credited, it is now a contributor. **Gap:** one early version of the canon concept (record [19317983](https://zenodo.org/records/19317983)) still lists it as a creator under an older spelling. |
| **Label clearly what is not verified.** | Every decision function carries `empirical_validation: NOT_VALIDATED` until field evidence exists. A published paper counts as certified only if an issuer certificate binds its exact bytes; every other public paper carries the UNCERTIFIED label. A certificate covers only its sealed artifacts and stated theorem scope. Certificates carry a depth label. | [`CLAIMS_MATRIX.md`](./CLAIMS_MATRIX.md), [`THEOREM_STATUS_TAXONOMY.md`](./THEOREM_STATUS_TAXONOMY.md) and [`certificates/README.md`](./certificates/README.md) | **Gap:** labels on Zenodo are incomplete. An audit on 2026-10-18 found two problems. First, 49 legacy records had their UNCERTIFIED label replaced in a WS-30 metadata edit. Second, 42 latest records carry no status label at all: 7 certified runs (Run-120, 121, 124, 132, 133, 137 and 139) and 35 records not yet mapped to a certificate. Some of those 35 state verification claims, for example [23329771](https://zenodo.org/records/23329771). Also, none of the PDFs published for the 18 certified runs is byte-identical to the sealed paper its certificate binds. We are correcting the labels. Until then, treat any Viridis paper without a certificate that binds its exact bytes as UNCERTIFIED. |

## The denominator

| Stage | Count |
|---|---|
| Nightly research-engine runs to date | 199 |
| Runs submitted to the Comparator certification pipeline (Run-116 onward, plus the Run-900 foundational series) | 84 |
| Runs issued a `LEAN_ZERO_SORRY_CERTIFIED` certificate | 78 |
| Certified runs published here in full, with the challenge, solution, certificate and receipt | 18 |
| Of those, labelled *substantial* by our size rule | 11 |

Runs 001–115 came before the current certification pipeline. Their historical
proof records do not count as certificates. They remain public on Zenodo and
carry an UNCERTIFIED label until they are re-certified.

**How results are chosen for this release.** The 18 published runs are the
certified results that back a callable decision function in [`os/`](./os/).
These are the results someone can actually use, so we checked them first.

## What a Lean check does not tell you

A comparator certificate shows that a stated theorem is proved, using only
standard axioms, and accepted by two independent kernels. It does not show
any of the following:

- **That the Lean statement says what the paper says.** Each run includes a
  `SEALED_CLAIM_INVENTORY.json` mapping the paper's claims to theorems, along
  with a statement-alignment receipt. Read them critically.
- **That the model's assumptions hold in a real landscape.**
- **That the result is new.**

Several certified results are elementary identities. They are labelled as
such, and we do not lead with them.

## How to hold us to this

- Re-run any certificate: `certificates/rerun.sh Run-129 --axioms-only` (see
  [`certificates/README.md`](./certificates/README.md)).
- Report a failed reproduction, a wrong statement, a missing citation, or a
  result you believe is trivial or known: open an
  [external-validation report](https://github.com/jdhart81/viridis-canon/issues/new?template=external-validation.yml).
  Failed and inconclusive reports are kept as evidence.
- Ask questions in [Discussions](https://github.com/jdhart81/viridis-canon/discussions).
