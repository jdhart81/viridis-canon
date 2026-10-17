# Native published-record edit projection

`zenodo_metadata_repair.py` preserves the complete native edit body for PUT.
Its comparison projection admits only a same-record edit of an already
published DOI: public `is_draft=false,is_published=true,status=published`, edit
`is_draft=true,is_published=true,status=published`, identical record/parent/PID
identity, and exact Zenodo record and upload navigation URLs. A new unpublished
version does not satisfy this contract.

The closed edit projection normalizes:

- A new, timezone-aware edit creation time ordered between the public update
  and edit update; this edit creation identity must remain exact across PUT.
- A well-formed edit expiry absent from the public record, and omission of the
  exact nondeleted public deletion marker.
- Known public-only navigation omissions, known draft-only action links, and
  the same record's public/draft file collection URL. Every normalized URL is
  derived from the protected record or parent identity.
- Omission of an entire file-link object only when every original link belongs
  to the closed, identity-derived self/content/container set. If links are
  present, only exact corresponding draft URLs and the derived commit action
  normalize. Unknown links, empty link objects and changed content URLs remain
  differences.
- The previously supported latest-draft boolean transition.

All metadata, custom fields, access, file identity/size/checksums, parent
content, unknown fields and unknown links remain protected. Both the opening
and checked edit are projected against the same current public baseline. The
opening projection must have no protected differences; after PUT both the
opening-to-checked and public-to-checked projections must contain exactly the
approved metadata field. Public readback and post-discard public comparison
continue to use the unchanged protected public comparator.

The `rdm-edit-21855705-20261016.json` fixture contains exact public and POST edit
subobjects from the safely deleted October 16 rehearsal. It has no receipt
paths or credentials. That live attempt held before PUT. Tests that materialize
file links after PUT, exercise cleanup, or reject later drift use an offline
simulated transport. No live PUT/post-PUT behavior is established by this test
suite. A different actual representation must HOLD, retain evidence and obtain
review before retrying; this source change is not installed by its tests.
