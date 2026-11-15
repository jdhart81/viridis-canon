# Canon Deposit Invariants

Binding rules for every hub release of the Viridis Canon on Zenodo (concept DOI
[10.5281/zenodo.19317982](https://doi.org/10.5281/zenodo.19317982)). The concept DOI
resolves to the latest version, so each version is the public front door to the whole
canon and must read like one.

Revised 2026-11-14. The earlier rule (a fixed description template plus one trailing
note) was retired: the hub description has been generated from the repository since
the October 2026 release, and the old template named an AI tool as co-author, which
[`AI_USE_AND_AUTHORSHIP.md`](./AI_USE_AND_AUTHORSHIP.md) and Zenodo both rule out.

## INV-DESC: one source for the description

The Zenodo `description` of a hub version is the output of

    python3 tools/build_overview.py --zenodo-description

built from the commit being released. Nothing is typed into the record by hand. The
counts, results, corrections and authorship statement in it come from the same
repository records as the overview page, and `tests/test_overview.py` checks them.

## INV-FILES: what a hub version holds

- The overview PDF from `tools/build_overview.py --pdf`, checked with `--check-pdf`.
- The certificates bundle from `tools/build_overview.py --bundle`. Before upload,
  `certificates/verify_bundle.py` must pass on the unpacked bundle.
- Files from the previous version are not carried over.
- After publishing, every file is read back without signing in and its SHA-256 is
  compared with the built file.

## INV-AI: authorship and AI use

- Justin D. Hart is the only creator. No AI tool is listed as creator or contributor.
- The description names the AI tools used and their roles.

## INV-LOCKSTEP: Zenodo and Git agree

- The release commit is on `main` before anything is published.
- `README.md`, `CITATION.cff` and the overview carry the same version, and that version
  exists on Zenodo.
- The release commit is tagged `canon-vYYYY.MM.DD` and has a GitHub Release that links
  the version DOI.

## Standing rules

- Publishing is gated on Justin's explicit go-ahead for that release.
- Credentials are never printed, committed or put in a URL.
- Spine freeze: no new spine version without Justin's explicit OK (v9 frozen).
- A published version is never edited to hide a defect. A defect gets a notice on the
  old version and a corrected new version.
