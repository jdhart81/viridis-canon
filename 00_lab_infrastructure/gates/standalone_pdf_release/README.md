# Standalone manuscript PDFs

Effective user directive: 2026-10-12. Standard: `VRS-STANDALONE-MANUSCRIPT-PDF-1`.

Every Viridis research deposit must expose the actual manuscript as a separate,
top-level PDF that opens directly from the record. A digest, summary, abstract,
source file or reproduction ZIP does not satisfy this requirement for its
constituent papers. Each Methods Digest note uses a descriptive Run name such
as `Run-167-Paper.pdf`; an existing descriptive name may remain.

The PDF must be byte-identical to the admitted manuscript and, when archived,
to its public archive member. Every note listed in `DIGEST_MANIFEST.json` must
have its own top-level PDF, declared in the approved upload inventory with
SHA-256, MD5 and size. Separate access copies change accessibility and no
scientific claim, verification status, author, license or proof scope.

`_ZENODO_DEPOSITS/manuscript_pdf_gate.py` validates actual upload paths rather
than merely finding a PDF on disk. It rejects a digest-only PDF, a missing
constituent manuscript, an omitted upload declaration and changed bytes.
It checks PDF manuscripts in public reproduction ZIP and TAR-family archives
against standalone copies. Papers in `papers/` or `manuscripts/` are recognized
even when they have descriptive titles. Unknown archived PDF roles must also
have an identical standalone copy; an unrelated summary cannot hide them.
Individual figure paths and names are excluded unless they explicitly identify
a paper. A figure alone does not establish a manuscript. Standard
`paper`/`manuscript` filenames are recognized; a descriptive standalone name
uses an exact SHA-256/MD5/size role declaration in `MANUSCRIPT_PDFS.json`.

Resource type does not exempt a manuscript: software deposits containing an
actual paper must expose it as well. For newly assembled archives containing
`paper`/`manuscript` MD, DOCX or TEX sources, the corresponding rendered PDF
with the same stem must be present in the approved archive and separately
accessible. This convention is a packaging gate; existing scientific PDF
correspondence review remains authoritative. Historical access repairs may
add a reviewed faithful rendering without altering the published archive.
A truly manuscript-free dataset, code archive or index needs a truthful scoped
exception through separate reviewed routing; this publisher has no automatic
resource-type or figure-only exemption.
The current dated and successor publishers enforce this gate during planning
and immediately before publication. After preserving the minted DOI they
download standalone PDFs from the public record and require exact checksums
and bytes. A readback failure retains the DOI and blocks completion; recovery
checks that same DOI and does not republish it.

Future Methods Digest releases use this mandatory default entry point:

```text
python3 _ZENODO_DEPOSITS/guard_methods_digest_release.py \
  --config <exact CONFIG.json> --expected-config-sha256 <exact SHA-256>
```

This is a read-only preflight. After the existing exact release authorization,
the same invocation adds `--go --output <canonical private reports directory>`.
The guard invokes only the config's own hash-bound controller, which must still
verify the genuine reviewed source closure, scientific admission, own-account
authority, original mutation journal and strict publication readback. The guard
then independently verifies direct public PDFs and writes
`STANDALONE_MANUSCRIPT_PDF_READBACK.json` before reporting success.

An archive-only legacy digest cannot pass this entry point. Its immutable
controller and source pins remain historical evidence and cannot be used for
a new release under this directive.

## Digest runtime compatibility

The existing Phase-7 digest helper accepts only four main upload names and its
controller accepts only six files. These bytes and their merged-source
identities must stay unchanged for historical receipts. The compatible v2
helper and exact source-review plan are prepared in
`_ZENODO_DEPOSITS/digest_pdf_v2_review/`. The helper adds exact admitted
`Run-N-Paper.pdf` copies during fresh assembly, declares them in the immutable
manifest, rejects missing or changed copies during every prewrite, and includes
them in the existing complete strict public readback.

This proposed helper is **not installed in the pinned digest runtime**. Before
the next digest can publish, the source review must cover the compatible
controller upload inventory, v2 registration dispatch, current runtime source
closure, genuine merged source readback and fresh config/authorization hashes.
Passing the outer gate alone grants no scientific or source authority.

Existing published deposits may gain an exact already-public PDF access copy
without rewriting their historical manifest, archived files or scope. Their
access-correction receipt binds original files, archive member and added PDF;
newly assembled releases must declare those PDFs before publication.

Public announcements link directly to the manuscript PDF and also retain the
record DOI for proofs and reproduction material. Release receipts include
each direct PDF URL and exact hash. Folder presence or successful upload alone
does not establish this standard's public completion.
