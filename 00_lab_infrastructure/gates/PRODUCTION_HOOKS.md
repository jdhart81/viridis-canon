# Production coverage observers

Justin's v4 decision retains `/Users/justinhart/Desktop/science ` as the untrusted generation lab and `/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0` as the mirror/certification authority. The saved scheduler and intake source root remain unchanged. Gates discover and assess certificates only in Cowork. The only source-root access is an inventory/hash comparison for INV-8; source bytes never feed the certificate consumer.

The three unversioned production files are captured under `production_snapshots/before/`, with SHA-256 receipts in `MANIFEST.json`. `installed/` contains the exact deployed successors. The intermediate report-only checkpoint adapter is also preserved under `report_only_v1/`. Neither verifier nor issuer is patched.

`install_report_only_hooks.py --root <Cowork> --report-only` checks the before and prepared hashes, refuses unexpected production-script changes, and installs the adapters plus a dedicated `RESEARCH_PIPELINE_v2/verification_coverage_gates/` runtime. Production never imports a dirty or unmerged Git checkout. The installation receipt lists every runtime/script hash. Future runtime changes require a reviewed installation; they do not follow repository updates automatically.

- Publisher: call the publication gate after successful release-coherence validation; return the original metadata payload unchanged.
- Canon mirror: call the same gate before including each bundle in the mirror plan; preserve the payload and transaction guard.
- Nightly: after a FINISH checkpoint is sealed, invoke `run_flow.py --report-only`; on replay, reuse that checkpoint-bound report. Timeout, missing runtime/input, malformed ledger or drift is reported as HOLD with a conjecture label. Existing checkpoint incidents and exit status remain intact.

The hooks have no enforcing argument and do not publish or change release eligibility. Proposed labels go to stderr and dated reports outside immutable bundles. Default publisher/mirror plans exercise them without `--publish`, `--go`, credentials, network writes, or Lean execution.

INV-8 compares complete inventories, including hidden files and extra mirror files, rejects symlinks/read errors/concurrent changes, and gives a mismatched run the single status `MIRROR_DRIFT`. The underlying classification and exact differences remain recorded. Drifted runs are excluded from eligible-run coverage; certificate counts never include them. All previous classification priorities remain in force after the parity override. The publication consumer repeats the parity check, so a later one-byte change cannot inherit an old ledger pass.

`run_flow.py` runs one complete REPORT_ONLY coverage/publication observation cycle tied to the existing nightly START/FINISH contract. It reads generation, FIFO debt, package/review state and certification receipts, rebuilds the whole-tree ledger, evaluates publication labels, records parity differences, and produces DOI triage. It generates no second paper in an already-satisfied nightly window, submits no proofs, repairs no held receipt and promotes no package. A cycle may finish HOLD; report creation is not scientific progress.

DOI triage uses the 98 locally evidenced version DOIs. Of the 52 missing artifact-proof certificates, a Run join is only a search key: CURABLE_BY_JOIN requires both deposited proof and statement bytes to bind an existing valid Comparator certificate and a matching source/mirror run. Missing joins or different Lean bytes remain TRUE_CONJECTURE/HOLD. This label describes evidence, not mathematical falsity.

For the 46 proof-certified artifacts, each deposited TeX manuscript is diffed against its own certified sealed paper. COSMETIC requires unchanged manuscript-body assertions (only comments, whitespace or preamble metadata may differ). Body statements that certification now exists, or changed scope, hypotheses or numbers, count as SUBSTANTIVE. This conservative definition includes many provenance-only body edits; SUBSTANTIVE does not mean the underlying proof is invalid. Every diff carries both SHA-256 values. Anonymous public GET readback independently confirms all 46 deposited PDF/TeX pairs against the published file checksums; that readback has no certificate authority.

Enforcement remains OFF. Existing DOI relabeling remains a human decision after reviewing the cycle report.
