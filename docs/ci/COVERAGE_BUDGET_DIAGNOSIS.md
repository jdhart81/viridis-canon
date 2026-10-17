# Coverage job budget repair

The serial Python 3.11 job exceeds the unchanged 600-second cap. Six closed historical fixture calls consume approximately 84% of primary time. Their source is unchanged; the environmental slowdown remains unproven.

| Execution | Whole job | Primary step / unittest | Result |
| --- | ---: | ---: | --- |
| PR114 546a911, [first](https://github.com/jdhart81/viridis-canon/actions/runs/39053064484/job/117455407476) | 602s | 595s / 594.404s | Cap failure |
| Same head, [one unchanged retry](https://github.com/jdhart81/viridis-canon/actions/runs/39053064484/job/117459416771) | 555s | 544s / 542.558s | Passed |
| PR114 B5 dad80dd, [fresh required CI](https://github.com/jdhart81/viridis-canon/actions/runs/39060503103/job/117477319350) | 625s | 614s / 612.690s | Cap failure; cancelled |
| Main 2daa389, [coverage](https://github.com/jdhart81/viridis-canon/actions/runs/39059515904/job/117474406133) | 604s | 595s / 593.469s | Cap failure |
| Main 562d72b, [coverage](https://github.com/jdhart81/viridis-canon/actions/runs/39061798280/job/117481104852) | 603s | 595s / 594.097s | Cap failure |

The 562 observation followed another actor's unrelated main merge, not a repair retry. Each primary command completed 2,196 tests. The separate 188-test suite succeeded except on dad80dd, where cancellation skipped it. Successful tests alone do not satisfy the cap.

Diagnosis SHA-256: e21ffc3cf7442ccdcf7b33ff4239155341b8893ab198ceaf3335cea5166357f8.
Initial source-only scope SHA-256: 91d20ed6fd6bf6e7b658b2a53568e845ec18586c14c52805cec853ce10897426.

The repair uses three whole discovery-owner shards. Every shard performs the original full discovery/import sequence, preserves load_tests, inheritance and generated methods, then selects complete owner suites. The manifest preserves 2,196 primary executions, including 32 repeated IDs, plus 188 separate secondary executions: 2,384 executions / 2,352 distinct IDs. All five original skips and all six historical nested calls remain required. Production, frozen fixture and caching code stays unchanged.

The retained report-only-consumers aggregate requires every shard, exact actual execution multiplicity, raw skip events and matching outcome counters. Missing, extra, failed, cancelled or over-budget work fails. It authenticates completed shard-job and step timings from the current GitHub run/attempt. This new read-only job API path uses actions:read and the built-in GitHub token, so the PR requires full Tier 1 independent Claude review under B3.

Jobs use a nine-minute timeout. Child processes share one cumulative 510-second active deadline, five-second TERM grace and one-second post-KILL reap/independent group-absence deadline. Permission errors never mean absence; leader reap alone is insufficient. Actual whole jobs, including setup/cleanup, and every executed step must still finish within 600 seconds. Root independently qualifies terminal whole-job timings, including the aggregate itself.

Shard estimates 188s/191s/235s are not measured successful results.

Local history: launch 1 exited71 before Python/tests because sandbox_apply was refused. Root-authorized recovery launch 2 ran 14 inert tests in 0.454s: 12 passed, two deadline controls failed on signal0 PermissionError; eight causal mutation controls passed. R2's 19 revised controls remained unexecuted. R3 added 22 controls and 10 mutation families: the prior eight plus explicit post-KILL query-bypass and raw-skip append-removal mutants. Real process-group/PID absence probes are separate from the synthetic negative-only persistent-group oracle.

PR127 head 31bc20d then exhausted that original budget: each Ubuntu shard ran 22 controls with 21 passes and one failure. Python 3.11 left a skipped subTest's parent outcome as skipped, while the oracle wrongly expected ok. All 10 mutant families and real process-group/PID absence controls passed, but the 2,384-execution coverage workload never ran and no reports existed. The aggregate failed on output redirection before its API read because the parent directory was absent. Other retained checks passed within the caps; longest whole job was 558s. Failure receipt SHA-256: 8f251ad446794ebf600005aa8bbf2ec600cdb4fd998dcee93c5b202fac86044b.

Direct human authority subsequently reopened the CI retry budget without erasing failures or changing gates/caps (authority SHA-256: 208365dba3fb13b8c09b26ed93f5d4f45cd6c8dcfa8e9a4d3950b73bb6c22f6e). The narrow correction checks genuine raw skip events without assuming a parent success callback; a separate inert parent-ok report must still fail for its raw skip event. The workflow creates only the output parent before redirection, and empty reports still fail. Focused Python 3.11.5 validation passed 19 inert controls and all 10 mutation families in 0.084s, plus an isolated output-parent/empty-report control. The three real-process cleanup controls were not rerun locally because of the recorded Mac permission failures. The corrected shard runner has not executed the original 2,384 workload or full Ubuntu cohort. Focused receipt SHA-256: c17b3a1f710cdf558605db05e7866d53db6d873b1c25d31e5d67ceb0ee473ec2.

Head changes do not reset counters. No automatic retry, extra timezone preflight, PR108 retry, cap waiver or new cache optimization follows from this correction. This repair still requires its own exact-head review, retained CI, scans, normal merge and actual postmerge main CI. A later PR114 main-only integration must separately reprove the unchanged 13-path effective diff and B5 conditions; attaching this workflow change directly to PR114 would invalidate that identity.
