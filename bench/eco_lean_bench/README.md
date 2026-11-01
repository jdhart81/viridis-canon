---
pretty_name: Eco-Lean Bench
license: apache-2.0
language:
  - en
task_categories:
  - text-generation
tags:
  - lean4
  - theorem-proving
  - formal-verification
  - mathlib
  - ecology
size_categories:
  - n<1K
configs:
  - config_name: default
    data_files: data/tasks.jsonl
---

# Eco-Lean Bench

**90 Lean 4 theorems from applied ecology, conservation and decision science, each with a frozen statement and a kernel-checked reference proof.** A prover gets the challenge file with `sorry` in place of every proof and must fill them in. Scoring uses the same check that certified the originals: the Lean kernel at a pinned toolchain and Mathlib revision, plus an audit of every theorem's axioms.

Most formal-math benchmarks come from competitions or textbooks. These come from working models: corridor reliability, seed-source routing, precautionary capacity under moment uncertainty, anytime change detection, capital allocation. Every task is a certified run from [`certificates/`](../../certificates/), so each statement was frozen before it was proved and each proof was accepted by two independent kernels.

| | Tasks | Theorems |
|---|---|---|
| Substantial (≥ 200 lines, median proof ≥ 6 lines) | 8 | 44 |
| Elementary | 7 | 46 |
| **Total** | **15** | **90** |

Depth is a size indicator from [`certificates/index.json`](../../certificates/index.json), not a judgement of difficulty or novelty.

## A task

Each line of [`data/tasks.jsonl`](data/tasks.jsonl) is one task:

| Field | Meaning |
|---|---|
| `task_id` | `ELB-NNN`, from the certified run `Run-NNN` |
| `challenge` | The full challenge file. Every target theorem's proof is `sorry`; nothing else is. |
| `targets` | Fully qualified names of the theorems to prove |
| `toolchain`, `mathlib_rev` | The exact Lean toolchain and Mathlib commit to check against |
| `permitted_axioms` | `propext`, `Quot.sound`, `Classical.choice` |
| `depth`, `reference_median_proof_lines` | Size of the certified proof |
| `reference_solution` | Path and SHA-256 of the certified proof. It is not inlined, so the file can go straight to a prover. |
| `public_since` | The date the reference proof became public, for contamination cuts |

Runs 120, 121 and 122 are left out: their statements were frozen together with their proofs, so there is no separate challenge. [`data/manifest.json`](data/manifest.json) lists them with the hashes of everything else.

## Score a submission

Put one complete Lean file per attempted task in a folder, named by task id (`ELB-139.lean`). Each file is the challenge with the target proofs filled in.

```bash
# Precheck: seconds, no Lean. Use it to iterate.
python3 bench/eco_lean_bench/score.py my-run/

# Authoritative: elaborates each file at the pinned toolchain and audits axioms.
# Needs elan; the first run fetches the Mathlib cache (several GB).
python3 bench/eco_lean_bench/score.py my-run/ --kernel --out result.json

# Also confirm statements in the kernel with leanprover/comparator.
COMPARATOR=/path/to/comparator python3 bench/eco_lean_bench/score.py my-run/ --kernel --out result.json
```

A target theorem counts when:

1. it is declared under the same qualified name with the same statement as the challenge (whitespace aside);
2. its proof, and everything it uses, has no `sorry` or `admit`;
3. the file declares no `axiom`, does not use `native_decide`, kernel-skipping options, `#exit` or custom syntax, and leaves every challenge definition unchanged;
4. in `--kernel` mode, the file elaborates without errors and the theorem depends only on the permitted axioms.

Partial credit is per theorem. The result JSON records the dataset hash and each file's SHA-256, so anyone can re-run it.

Sanity check: the certified reference proofs score 90/90 and the unmodified challenges score 0/90 (`score.py --reference`, and the tests in [`tests/test_eco_lean_bench.py`](../../tests/test_eco_lean_bench.py)).

## Leaderboard

Only `--kernel` results are listed. Open a pull request that adds your `result.json` under `results/` and a row here, and say which model or system produced the proofs, with its training cutoff.

| System | Training cutoff | Solved | Substantial | Elementary | Result |
|---|---|---|---|---|---|
| *(no entries yet)* | | | | | |

## Contamination

The reference proofs are public in this repository. A model trained on GitHub after a task's `public_since` date may have seen its proof. Report your model's training cutoff, and when it matters, score only the tasks whose `public_since` is later.

## What a score means, and what it does not

A solved theorem means a machine-checked proof of a fixed formal statement. It does not mean the statement captures the paper's prose claim, that the model describes any real ecosystem, or that the result is new. See [`certificates/README.md`](../../certificates/README.md) for what the underlying certificates establish.

## Rebuild

```bash
python3 bench/eco_lean_bench/build.py          # regenerate data/ from certificates/index.json
python3 bench/eco_lean_bench/build.py --check  # what CI runs (through the tests)
```

The build checks every challenge against the SHA-256 bound in `certificates/index.json` and refuses to export a task whose targets are not bare `sorry` or whose statements differ from the certified proof. A new certified run becomes a new task on the next build.

## Licence

The scripts and the task data (Lean source) are Apache-2.0, like the rest of this repository's code. This documentation is CC-BY-4.0, per the repository's contribution terms. Viridis LLC.
