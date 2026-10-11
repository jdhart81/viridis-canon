Phase 8 advisory quality metrics and authoring helpers

`phase8_quality.py` uses Python's standard library plus the sibling additive `novelty_stage.py`. It makes no network call, executes no Lean code, issues no certificate, and calls no verification or publication module. Its input failures yield `ADVISORY_UNAVAILABLE` with exit 0; they never change the pipeline verdict. Unknown classification is preserved. A claimed novelty status is credited only after the sibling classifier rechecks the exact target/search hashes, exact comparison-review hash and the same allowed status. Retrospective checks use the original classification timestamp so later report age does not erase a valid historical assessment. A search stale at the actual run, foreign-run target, changed evidence, missing review/hash or explicit stale-at-selection flag yields UNASSESSED. Raw status strings cannot establish KNOWN, KNOWN_VARIANT or LIKELY_NEW.

The weekly cohort is unique nightly run IDs with timezone-aware `RUN_MANIFEST.generated_at_utc` in the requested ISO week in America/New_York. File modification times, certification retries, supplemental witness/probe jobs, digest versions and DOI dates do not create additional run attempts. Certification count reports the current SSOT `run_entities` status `CERTIFIED` for that generation cohort; it is not a new certificate validation. A just-generated run absent from SSOT reports `UNKNOWN_LEDGER_STATUS`.

Depth uses deduplicated `(run_id, lean_theorem)` tables from registered Methods Notes, exported theorem names in the current SSOT, and `MAIN_NOTES` plus `headline_eligible=true`. Additive future `QUALITY_LABELS.json` may supply actual reviewed labels for those same exported main claims. A run is SUBSTANTIVE if at least one actual exported relevant main claim is explicitly SUBSTANTIVE. If no substantive claim is known and any main label is unknown, the run remains UNASSESSED; it is ROUTINE or DEFINITIONAL only when its assessed main labels warrant that conclusion. Conflicting labels become UNASSESSED. Proof length or syntactic tactics alone do not establish SUBSTANTIVE; this consumer records the existing classification without inventing an evidence verdict.

The headline target uses SUBSTANTIVE / **all certified runs**, including unassessed runs in the denominator. The LIKELY_NEW target uses LIKELY_NEW / **all attempted runs**. Thus a tiny assessed sample cannot meet either target. Assessed-only shares and assessment coverage are separately printed. A zero evidenced lower bound is no demonstrated success; it never labels unknown results known or routine. Portfolio hit rate likewise prints recorded-selection coverage and an all-attempts lower bound. Targets never block certification or publication.

The 28-day trend starts at the exact Phase 8 activation timestamp passed by `--phase8-start`. All prior runs, including already-sealed runs on the activation date, are excluded from the Phase 8 trend. Omitting activation excludes all historical runs; the baseline does exactly that. The first W41 baseline observes 7 actual dated runs, 4 currently CERTIFIED, 2 HAS_SORRY, and Run-193 absent from SSOT at snapshot time. All seven novelty and depth classifications are UNASSESSED; this is not a zero-newness/zero-substance result.

Weekly command (paths must retain their spaces):

```sh
python3 '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/phase-8/phase8_quality.py' \
  --tree-root '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0' \
  --phase8-root '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/phase-8' \
  --week 2026-W42 \
  --phase8-start '<exact timezone-aware timestamp from Phase 8 activation receipt>' \
  --output-dir '/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0/reports/verification-coverage/phase-8/weekly/2026-W42-v001'
```

The weekly JSON records SHA-256 for every read input and input coverage gaps. Previous weekly JSON files under `phase-8/weekly/*/WEEKLY_QUALITY_METRICS.json` provide the trend history; duplicate run IDs do not double-count.

Per-run advisory inputs may be in the newly authored run directory or `phase-8/runs/Run-NNN/`:

- `NOVELTY_ASSESSMENT.json`: `run_id`, `status`, `target_sha256`, `search_evidence_sha256`, `one_line_reasoning` (from the novelty stage).
- `TARGET_SELECTION.json`: `run_id`, `portfolio_item_id` (`P8-01`–`P8-20` or null), `value_rationale`. Missing selection remains unrecorded, not an off-portfolio choice.
- `QUALITY_LABELS.json`: `run_id`, `claims` with `lean_theorem`, literal `semantic_tier`, `headline_eligible:true` for main results only. Labels remain advisory and are not evidence-class changes.
- `PORTFOLIO_OUTCOMES.json`: `run_id`, `outcomes` with `portfolio_item_id`, `disposition` (`STRENGTHENED` or `DISCHARGED`), `reviewed:true`, `review_reason`, `evidence_path`, `evidence_sha256`. Outcomes count only when the evidence bytes still match. No result is deemed to solve an open problem from its title or certificate alone.

Future note authoring (before the initial claim-map/manuscript binding freeze):

```sh
python3 phase8_quality.py render-note \
  --input '/new-note-authoring-draft/SCOPED_CLAIM_MAP.json' \
  --run-id Run-194 \
  --assessment '/phase-8/runs/Run-194/NOVELTY_ASSESSMENT.json' \
  --output '/new-note-authoring-draft/NOVELTY_CLAIM_TABLE.md' \
  --tex-output '/new-note-authoring-draft/NOVELTY_CLAIM_TABLE.tex'
```

Include the TeX fragment in the newly authored note before first freeze. Its column is **Run-target novelty**: the run's target assessment does not imply that auxiliary identity or routine theorems are novel. The paragraph states this distinction and prints the target/search-evidence hashes. Missing, malformed or other-run assessment displays UNASSESSED. It preserves the source input and evidence class, basis, scope and certificate fields. Existing different fragments are not overwritten; use a new pre-binding draft path. Do not rewrite frozen historical notes or alter a publication gate's closed schema.

At weekly digest assembly, each newly authored note carries that printed table in the existing Methods Notes archive. This helper does **not** alter the original digest wrapper/metadata/payload schema. It creates an additional advisory `DIGEST_NOVELTY.md` under Phase 8 reports:

```sh
python3 phase8_quality.py render-digest \
  --input '/prepared-digest/DIGEST_MANIFEST.json' \
  --phase8-root '/phase-8' \
  --output '/phase-8/weekly/2026-W42-v001/DIGEST_NOVELTY.md'
```

Use the existing original nightly/weekly scheduler to run these helpers. There is no new timer, enforcement flag, daily notification or publication route. Include the weekly quality ledger in the already-authorized weekly report.

Validation:

```sh
python3 -m unittest -v test_phase8_quality.py
```

The tests cover empty/malformed input, actual-date timezone boundaries, duplicate attempts/digests, current-SSOT-only counts, excluded unexported claims, unknown classifications, exact activation exclusion, the full target denominators, reviewed outcome evidence, four-week deduplication, input preservation, future table wording, safe TeX rendering, refusal to replace an existing different authoring fragment, spoofed LIKELY_NEW, changed evidence/review, foreign-run target and stale-at-run assessment. Install both additive modules in the same directory before running the full bound-assessment suite.
