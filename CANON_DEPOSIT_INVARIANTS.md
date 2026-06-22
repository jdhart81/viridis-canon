# Canon Deposit Invariants

Binding rules for every Viridis Canon Zenodo deposit (manual `push_canon_v*.py` or the
`viridis-canon-submission` task). The concept DOI resolves to the latest version, so each
record is a public front door to the whole canon — it must read like one.

## INV-DESC (description invariant) — REQUIRED on every version
The Zenodo `description` of every canon-snapshot version MUST equal:

    [stable canon description]  +  one trailing paragraph:
    "<p><strong>This version (vX.Y.Z).</strong> {one concise note}. {lineage note}.</p>"

- The **stable canon description** is `CANON_DESCRIPTION_TEMPLATE.html` (single source of
  truth) — it describes what the canon IS and never changes between releases.
- Only the **trailing "This version" note** changes per release (1–2 sentences: what this
  version added/changed). It is a side note, never the body.
- Do NOT make the description version-specific/technical (no CI/lakefile/patch-note prose
  in the body — that belongs in `CHANGELOG_vX.Y.Z.md` and the trailing note only).

## How to apply
- New version: `push_canon_vX.Y.Z.py` must build `description = open(CANON_DESCRIPTION_TEMPLATE.html).read() + this_version_note`.
- Edit an existing published record in place (same DOI): `canon_desc_backfill.py` pattern
  — POST actions/edit → GET metadata → set description → PUT → POST publish.

## Other standing invariants (recap)
- Spine freeze: no new spine version without Justin's explicit OK (v9 frozen).
- Token: read from `secrets/Zenodo_API/Zenodo_token.md`; never print; never use
  `raise_for_status` with the token in query params (it leaks into error URLs). Sanitize
  all output with `.replace(TOKEN,'***')`.
- Files: keep the featured paper PDF; replace the prior canon archive with the new snapshot zip.
- Zenodo↔Git lockstep: every deposit also pushes to github.com/jdhart81/viridis-canon (+ tag/Release).
- Publish keystroke is Justin-gated by default.
