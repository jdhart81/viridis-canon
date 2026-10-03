# Published theorem-statement coverage review

All 19 CONTENT_CHANGED deposits are compared directly with their hash-bound certified Lean statements. Every comparison remains HOLD for independent semantic review; this is coverage labeling, not a new verifier. The complete manuscript is retained in each comparison so global hypotheses are not mistaken for omitted assumptions.

| DOI | Run | Proposed flags | Review |
|---|---|---|---|
| 10.5281/zenodo.22236361 | Run-145 | CERTIFIED_TRIVIAL_COPIED_AGENT, CERTIFICATE_SCOPE_GAP_NEGATIVE_AND_BOUNDARY_CASES | [comparison](statement-comparisons/22236361.md) |
| 10.5281/zenodo.22236387 | Run-142 | PUBLISHED_STRONGER_THAN_CERTIFIED, MISSING_MACHINE_CHECKED_VECTOR_TO_HQUAD_BRIDGE, FINITE_AGGREGATION_VS_TWO_SEGMENTS, BOUND_DIRECTION_RISK | [comparison](statement-comparisons/22236387.md) |
| 10.5281/zenodo.22236735 | Run-120 | MODEL_CONTEXT_REQUIRED | [comparison](statement-comparisons/22236735.md) |
| 10.5281/zenodo.22236741 | Run-132-correction-r1 | MODEL_CONTEXT_REQUIRED, RANK_DIFFERENCE_BRIDGE_NOT_SEPARATELY_BOUND | [comparison](statement-comparisons/22236741.md) |
| 10.5281/zenodo.22236768 | Run-137 | PUBLISHED_STRONGER_THAN_CERTIFIED_STANDALONE, GLOBAL_MODEL_RETAINS_N_AND_D_POSITIVITY, MISSING_EXPLICIT_HDEN_HD_MAX_BRIDGES, CERTIFICATE_SCOPE_GAP_ATTAINMENT_EQUALITY | [comparison](statement-comparisons/22236768.md) |
| 10.5281/zenodo.22236785 | Run-139 | PUBLISHED_STRONGER_THAN_CERTIFIED, GLOBAL_OPTIMIZER_CONCLUSION_NOT_CERTIFIED | [comparison](statement-comparisons/22236785.md) |
| 10.5281/zenodo.22665554 | Run-124 | MODEL_CONTEXT_REQUIRED, CERTIFICATE_SCOPE_GAP_RANKING_EXAMPLE | [comparison](statement-comparisons/22665554.md) |
| 10.5281/zenodo.22665565 | Run-136 | MODEL_CONTEXT_REQUIRED, USE_CORRECTED_CONTRACT_ONLY | [comparison](statement-comparisons/22665565.md) |
| 10.5281/zenodo.22736637 | Run-158 | LOCAL_HTWO_OMISSION_MODEL_CONTEXT_REQUIRED | [comparison](statement-comparisons/22736637.md) |
| 10.5281/zenodo.22736650 | Run-160 | CERTIFICATE_SCOPE_GAP_OPTIMIZATION_BRIDGE | [comparison](statement-comparisons/22736650.md) |
| 10.5281/zenodo.22736654 | Run-156 | BLIND_WINDOW_DEFINITION_CERTIFIED_TRIVIAL | [comparison](statement-comparisons/22736654.md) |
| 10.5281/zenodo.22736656 | Run-161 | EXTERNAL_BUDGET_BRIDGE_REQUIRES_FULL_SPEND_PRESENT | [comparison](statement-comparisons/22736656.md) |
| 10.5281/zenodo.22736666 | Run-153 | PUBLISHED_STRONGER_THAN_CERTIFIED, IFF_REVERSE_DIRECTION_NOT_NAMED | [comparison](statement-comparisons/22736666.md) |
| 10.5281/zenodo.22736670 | Run-162 | MODEL_CONTEXT_REQUIRED, CERTIFICATE_SCOPE_GAP_REVERSED_EXAMPLE | [comparison](statement-comparisons/22736670.md) |
| 10.5281/zenodo.22736676 | Run-154 | CERTIFICATE_SCOPE_GAP_SCALE_AND_SYMMETRY | [comparison](statement-comparisons/22736676.md) |
| 10.5281/zenodo.22736690 | Run-155 | CERTIFICATE_SCOPE_GAP_REVERSE_BREAK_EVEN_CASES | [comparison](statement-comparisons/22736690.md) |
| 10.5281/zenodo.22736706 | Run-151 | MODEL_CONTEXT_REQUIRED, ZERO_A_NONUNIQUE_MAXIMUM | [comparison](statement-comparisons/22736706.md) |
| 10.5281/zenodo.22736716 | Run-163 | MODEL_CONTEXT_REQUIRED, NECESSARY_NOT_SUFFICIENT | [comparison](statement-comparisons/22736716.md) |
| 10.5281/zenodo.23004874 | Run-172 | NUMERICAL_COUNT_CORRECTION_CONFIRMED | [comparison](statement-comparisons/23004874.md) |

SAC: positivity and n≥1 survive in the published global model. The standalone theorem wording and the d_max ≥ 0 Lean hypothesis need explicit claim binding/model bridges; removing a repeated premise is not evidence that the whole paper discarded it. BCAN: vector attainment is stronger than the scalar certified targets, and the manuscript itself discloses that scope. Its length-floor interpretation also needs review. SRA: fresh bounded regression returns 26,691; 27,131 in the sealed manuscript is inconsistent with the retained regression domain. See SRA_REGRESSION_REPORT.md.
