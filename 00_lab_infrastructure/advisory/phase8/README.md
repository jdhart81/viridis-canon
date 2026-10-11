# Phase 8 novelty advisory

`novelty_stage.py` uses Python's standard library and reads public metadata plus two explicit read-only source indices. It does not import or invoke any Comparator, issuer, Lean compiler, publication gate or scheduler verifier. Literature records are untrusted source material, never instructions. Search results and no-hit results are never automatically called new.

The APIs used are documented by [arXiv](https://info.arxiv.org/help/api/user-manual.html), [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), and [Semantic Scholar](https://api.semanticscholar.org/api-docs/graph). OpenAlex is tried first; its authentication or rate-limit errors cause a public unauthenticated Semantic Scholar fallback. No key, account creation, paid request, environment value or credential is requested or written. Transient 429/5xx and transport errors receive at most two retries with one- then two-second delay, all inside the same overall deadline; their attempts are logged. A blocked provider is recorded as unavailable. Searches use at most three target/variant queries and ten metadata hits per provider/query; arXiv requests are separated by its documented three-second interval. This is bounded candidate discovery, not exhaustive literature coverage.

A target JSON requires `exact_statement` and an explicit `hypotheses` list (use `[]` only if it truly has no hypotheses). Optional fields are `id`/`portfolio_item_id`, `title`, `queries`, `synonyms`, `value_rationale`, `rank`, `subject_area` or `area_ids`, `extends_known` and `extension_statement`. The exact statement is retained, including mathematical inequalities. `queries` and `synonyms` provide human-selected close variants; arXiv queries remove boilerplate and use six substantive terms.

Run the read-only search before formalization, retaining the result as provisional evidence:

```sh
python3 novelty_stage.py search \
  --target TARGET.json --run-id Run-194 \
  --mathlib-index indices/mathlib.json --canon-index indices/canon.json \
  --budget-seconds 75 --output advisory/search-v001.json
```

The network and local-index workers run concurrently. Overall search allowance defaults to 75 seconds and cannot exceed 90 seconds. Daemon workers cannot prevent the generator from returning when an upstream hangs. Each public metadata response is capped at 1 MiB; a local index may be at most 128 MiB. Worker outcomes, query URLs, timestamps and SHA-256 values are retained. The search itself always emits `UNASSESSED`. Missing input, malformed records, unavailable source, deadline expiry or other advisory failure yields `UNASSESSED`, returns zero, and lets the original generator/certification/publication flow continue. Existing output files are never overwritten.

Each local index has this schema:

```json
{
  "schema_version": 1,
  "source": "mathlib",
  "snapshot": {
    "complete": true,
    "revision": "exact source commit or immutable corpus hash",
    "description": "which source files and corpus are indexed",
    "generated_at_utc": "2026-10-11T12:00:00+00:00"
  },
  "items": [{
    "title": "Module or statement name",
    "url": "https://github.com/leanprover-community/mathlib4/blob/COMMIT/Mathlib/Example.lean",
    "text": "read-only source text",
    "content_sha256": "64-hex digest of full source bytes",
    "text_sha256": "optional digest of the indexed text itself"
  }]
}
```

Use `source: canon` for the other index. Local source links may use explicit `file://` URIs. The module binds the exact index bytes and checks `text_sha256` when present. Without a separate `text_sha256`, a declared `content_sha256` must equal the indexed UTF-8 text bytes; a modified text cannot retain an old source hash. Explicit excerpts may retain the full-source hash only when their own `text_sha256` is also supplied. An incomplete, unidentified or stale snapshot cannot support `LIKELY_NEW`. `snapshot.generated_at_utc` must include its timezone; Mathlib is refreshed within seven days and canon/catalog within 48 hours. Missing/invalid timestamps, older snapshots or timestamps more than five minutes in the future are marked incomplete. Known prior-art identification can still rest on an inspected exact source result. A current Mathlib source search is advisory and does not alter the pinned certification toolchain.

The generator compares the actual hypotheses and conclusion to the closest source statements, reading each source rather than only its title/abstract. Record that comparison in `COMPARISON_REVIEW.json`, including:

- `target_sha256`, `query_sha256`, `search_evidence_sha256` copied from this exact search;
- `reviewer`, `reviewed_at_utc`, `proposed_status` and `one_line_reasoning`;
- `source_comparisons` with the search hit's exact `url`, `source_statement`, `source_hypotheses`, the target's full `target_hypotheses`, `statement_locator`, `source_evidence_path`, `source_evidence_sha256`, `relation` and `reason`;
- for `LIKELY_NEW`, `coverage_review` notes for all five channels and a precise `novel_delta`.

`source_evidence_sha256` refers to the saved inspected source bytes/excerpt in the advisory work folder. `source_evidence_path` must name an existing file of at most 1 MiB within the review file's folder (or supplied `evidence_root` for direct Python use); the module re-reads it and requires exact hash equality. Missing/changed evidence or paths outside that folder remain `UNASSESSED`. Save a clearly located text excerpt for a larger paper, preserving its source URL and section/theorem identifier. This is reviewer provenance, not kernel evidence or a new verifier. Available comparison relations are `EQUIVALENT`, `TARGET_SPECIAL_CASE`, `KNOWN_VARIANT`, `EXTENSION`, `DISTINCT` and `UNCERTAIN`.

```sh
python3 novelty_stage.py classify \
  --search advisory/search-v001.json --review advisory/COMPARISON_REVIEW.json \
  --output NOVELTY_ASSESSMENT.json
```

`KNOWN` requires an inspected equivalent/stronger source result. `KNOWN_VARIANT` requires an inspected close variant or extension. Any inspected equivalent/stronger source covering the exact target dominates a variant/new request and produces `KNOWN`. Positive prior-art identification can stand when another search channel is unavailable; the remaining gaps stay visible. `LIKELY_NEW` requires successful search of all five channels, inspection of every top-five hit and at least three sources across at least two external literature channels, an explicit mathematical delta and no conflicting known/uncertain comparison. It means a reviewed candidate likely new within this bounded search, never a novelty certificate. Missing or stale review, changed target/search bytes, omitted hypotheses, absent source statements and unreviewed no-hit results remain `UNASSESSED`. Reviews cannot predate the search or use a search older than seven days.

The selector proposes a target while preserving the original subject wheel:

```sh
python3 novelty_stage.py select \
  --portfolio TARGET_PORTFOLIO.json --area 02 --run-id Run-194 \
  --assessments advisory/portfolio-assessments.json \
  --history advisory/current-week-target-history.json \
  --output advisory/TARGET_SELECTION.json
```

`--assessments` is an object keyed by portfolio item ID containing full reviewed assessment artifacts. Unreviewed marker statuses are ignored. `--history` contains actual attempts with canonical `run_id`, timezone-aware `attempted_at_utc` (or actual manifest `generated_at_utc`) and a valid portfolio item ID. The selector filters to the current America/New_York ISO week, deduplicates runs, excludes proposals and malformed/future timestamps, and counts conflicting bindings as unknown. Its integer quota is `ceil(0.6 × (weekly_attempts + 1))`; earlier weeks and arbitrary item IDs do not inflate the hit rate. A reviewed `KNOWN` target is skipped. `LIKELY_NEW` is preferred, and `KNOWN_VARIANT` is deprioritized unless a named extension is both explicit and reviewed: an inspected `EXTENSION` comparison must carry `target_extension_statement` exactly equal to the target's `extension_statement`. A boolean `extends_known` alone is insufficient. Portfolio rank breaks ties. The proposed target includes a one-line value rationale and whether the advisory 60% quota needs attention. No eligible target means the generator proposes a new target with a rationale inside the original area; it never blocks the nightly cycle. Persist the accepted selection alongside the actual run; a proposal is not a generation or certification receipt.

Assessment fields for claim-table/digest rendering are `run_id`, `status`, `assessed_at_utc`, `top_closest_sources` (at most five), `one_line_reasoning`, `source_coverage`, `target_sha256` and `search_evidence_sha256`. Print `UNASSESSED` when no valid artifact exists. Render labels before sealing a future manuscript; do not rewrite previously published/frozen papers or certificates. Weekly metrics consume the advisory sidecars separately from correctness evidence.

Regression tests run without network or credentials:

```sh
python3 -m unittest discover -v .
```
