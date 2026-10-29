"""Eco-Lean Bench: the task set stays current and the scorer is honest.

Runs in the research-portal workflow (python3 -m unittest discover -s tests).
Standard library only; no Lean required. The invariant letters refer to
bench/eco_lean_bench/{lean_text,build,score}.py.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = ROOT / "bench" / "eco_lean_bench"
sys.path.insert(0, str(BENCH))



def _load(name: str):
    spec = importlib.util.spec_from_file_location("eco_lean_bench_" + name, BENCH / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


lean_text = _load("lean_text")
score = _load("score")
build = sys.modules["eco_lean_bench_build"]

NS = "Viridis.ThermodynamicEconomics.RetrofitWaterFilling."
REF_139 = (ROOT / "certificates" / "Run-139" / "VERIFICATION_CANDIDATE.lean").read_text(encoding="utf-8")


def task(task_id: str) -> dict:
    return next(t for t in score.load_tasks() if t["task_id"] == task_id)


def precheck_139(text: str) -> dict:
    return score.precheck(task("ELB-139"), text)


class DatasetTests(unittest.TestCase):
    def test_checked_in_data_is_current_and_deterministic(self):  # B5
        lines, manifest = build.build()
        self.assertEqual(build.build(), (lines, manifest))
        self.assertEqual((build.DATA / "tasks.jsonl").read_text(encoding="utf-8"), lines,
                         "run bench/eco_lean_bench/build.py")
        self.assertEqual((build.DATA / "manifest.json").read_text(encoding="utf-8"), manifest)

    def test_counts_and_exclusions(self):  # B1
        m = json.loads((build.DATA / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["counts"]["tasks"], 15)
        self.assertEqual(m["counts"]["theorems"], 90)
        self.assertEqual([e["run"] for e in m["excluded"]], ["Run-120", "Run-121", "Run-122"])
        self.assertEqual(m["tasks_sha256"], build.sha256((build.DATA / "tasks.jsonl").read_bytes()))

    def test_tasks_carry_the_bound_challenge_and_no_solution(self):  # B2, B3
        for t in score.load_tasks():
            raw = (ROOT / t["challenge_file"]).read_bytes()
            self.assertEqual(t["challenge"].encode("utf-8"), raw, t["task_id"])
            self.assertEqual(build.sha256(raw), t["challenge_sha256"])
            self.assertEqual(set(t["reference_solution"]), {"file", "sha256"})
            thms = lean_text.theorem_map(t["challenge"])
            for q in t["targets"]:
                self.assertIn(thms[q].proof(), build.SORRY_PROOFS, q)
            self.assertEqual(len(t["targets"]), t["target_count"])

    def test_a_tampered_challenge_hash_aborts_the_build(self):  # B2
        index = json.loads((ROOT / "certificates" / "index.json").read_text(encoding="utf-8"))
        run = copy.deepcopy(next(r for r in index["runs"] if r["run"] == "Run-139"))
        run["files"]["challenge"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(build.BuildError, "challenge hash"):
            build.build_task(run)


class PrecheckTests(unittest.TestCase):
    def test_reference_solutions_solve_everything(self):
        r = score.score(score.reference_files())
        self.assertEqual((r["solved"], r["total"]), (90, 90))
        self.assertFalse(r["authoritative"])

    def test_the_challenge_itself_solves_nothing(self):  # S2
        files = {t["task_id"]: t["challenge"] for t in score.load_tasks()}
        r = score.score(files)
        self.assertEqual(r["solved"], 0)
        reasons = {v for row in r["tasks"] for v in row["failures"].values()}
        self.assertEqual(reasons, {"proof uses sorry or admit"})

    def test_partial_credit_for_one_open_target(self):  # S2
        text = REF_139.replace("  linarith\n", "  sorry\n")
        res = precheck_139(text)
        self.assertTrue(res["file_ok"])
        failed = [q for q, r in res["targets"].items() if r]
        self.assertEqual(failed, [NS + "embodied_burden_lowers_benefit"])

    def test_a_gap_reached_through_a_helper_lemma_counts(self):  # S2
        helper = "theorem helper_gap (x : Real) : x <= x := by\n  sorry\n\n"
        text = REF_139.replace("theorem embodied_burden_lowers_benefit", helper +
                               "theorem embodied_burden_lowers_benefit")
        text = text.replace("  linarith\n", "  have := helper_gap gross\n  linarith\n")
        res = precheck_139(text)
        self.assertEqual(res["targets"][NS + "embodied_burden_lowers_benefit"], "proof uses sorry or admit")
        self.assertIsNone(res["targets"][NS + "coordinate_improvement_identity"])

    def test_sorry_in_comments_and_strings_is_ignored(self):  # T2
        text = REF_139.replace("  ring\n\ntheorem embodied",
                               "  ring -- no sorry here\n/- nor /- nested sorry -/ here -/\n\n"
                               "def note : String := \"sorry, admit\"\n\ntheorem embodied")
        self.assertEqual(sum(r is None for r in precheck_139(text)["targets"].values()), 6)

    def test_a_weakened_statement_fails(self):  # S1
        text = REF_139.replace("    0 <= clippedAllocation b c q lambda := by",
                               "    0 <= clippedAllocation b c q lambda \\/ True := by")
        res = precheck_139(text)
        self.assertEqual(res["targets"][NS + "clippedAllocation_nonnegative"],
                         "statement differs from the challenge")

    def test_reformatting_a_statement_is_fine(self):  # T4
        text = REF_139.replace("theorem clippedAllocation_le_one (b c q lambda : Real) :\n    clippedAllocation",
                               "theorem clippedAllocation_le_one\n  (b c q lambda : Real) :   clippedAllocation")
        self.assertIsNone(precheck_139(text)["targets"][NS + "clippedAllocation_le_one"])

    def test_missing_or_renamespaced_targets_fail(self):  # S1
        text = REF_139.replace("theorem interior_stationarity", "theorem interior_stationarity'")
        self.assertEqual(precheck_139(text)["targets"][NS + "interior_stationarity"], "missing")
        moved = REF_139.replace("namespace Viridis.ThermodynamicEconomics.RetrofitWaterFilling",
                                "namespace Elsewhere").replace(
            "end Viridis.ThermodynamicEconomics.RetrofitWaterFilling", "end Elsewhere")
        res = precheck_139(moved)
        self.assertTrue(all(r for r in res["targets"].values()))

    def test_a_changed_definition_zeroes_the_file(self):  # S4
        text = REF_139.replace("min 1 (max 0 ((b - lambda * c) / q))", "min 1 (max 0 1)")
        res = precheck_139(text)
        self.assertFalse(res["file_ok"])
        self.assertIn("changes or drops def " + NS + "clippedAllocation", res["file_reasons"])
        r = score.score({"ELB-139": text}, only={"ELB-139"})
        self.assertEqual(r["solved"], 0)

    def test_escape_hatches_zero_the_file(self):  # S3
        cases = {
            "axiom cheat : False\n\n": "declares an axiom",
            "set_option debug.skipKernelTC true\n\n": "uses skipKernelTC",
            "macro \"trivially\" : tactic => `(tactic| sorry)\n\n": "uses macro",
        }
        for inject, reason in cases.items():
            text = REF_139.replace("noncomputable def clippedAllocation", inject + "noncomputable def clippedAllocation")
            res = precheck_139(text)
            self.assertFalse(res["file_ok"], inject)
            self.assertIn(reason, res["file_reasons"])
        native = REF_139.replace("  ring\n\ntheorem embodied", "  native_decide\n\ntheorem embodied")
        self.assertIn("uses native_decide", precheck_139(native)["file_reasons"])

    def test_unknown_submission_file_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "ELB-999.lean").write_text("", encoding="utf-8")
            with self.assertRaises(SystemExit):
                score.read_submission(Path(d))

    def test_not_attempted_scores_zero_and_hashes_are_recorded(self):  # S6
        r = score.score({"ELB-139": REF_139})
        rows = {row["task_id"]: row for row in r["tasks"]}
        self.assertEqual(rows["ELB-123"]["status"], "not attempted")
        self.assertEqual(rows["ELB-139"]["file_sha256"], build.sha256(REF_139.encode("utf-8")))
        self.assertEqual((r["solved"], r["total"]), (6, 90))
        self.assertEqual(r["tasks_sha256"], build.sha256((build.DATA / "tasks.jsonl").read_bytes()))


class KernelModeTests(unittest.TestCase):
    def test_dry_run_lays_out_a_pinned_project_outside_the_repo(self):  # S5, S6
        with tempfile.TemporaryDirectory() as d:
            r = score.score({"ELB-139": REF_139}, mode="kernel", dry_run=True, keep=Path(d), only={"ELB-139"})
            row = r["tasks"][0]
            work = Path(row["work_dir"])
            self.assertTrue(work.is_relative_to(Path(d)))
            t = task("ELB-139")
            self.assertEqual((work / "lean-toolchain").read_text().strip(), t["toolchain"])
            self.assertIn(f'rev = "{t["mathlib_rev"]}"', (work / "lakefile.toml").read_text())
            self.assertEqual((work / "Solution.lean").read_text(), REF_139)
            self.assertEqual((work / "Challenge.lean").read_text(), t["challenge"])
            cfg = json.loads((work / "config.json").read_text())
            self.assertEqual(cfg["theorem_names"], t["targets"])
            check = (work / "Check.lean").read_text()
            for q in t["targets"]:
                self.assertIn(f"#print axioms {q}\n", check)
            self.assertIn(["lake", "env", "lean", "Check.lean"], row["commands"])
            self.assertFalse(r["authoritative"])
            self.assertEqual(r["solved"], 0)

    def test_axiom_log_parsing(self):  # S5
        t = task("ELB-139")
        a, b, c, *rest = t["targets"]
        log = (f"'{a}' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
               f"'{b}' depends on axioms: [propext, sorryAx]\n"
               f"'{c}' does not depend on any axioms\n")
        out = score.parse_axiom_log(t, log)
        self.assertIsNone(out[a])
        self.assertEqual(out[b], "uses axioms sorryAx")
        self.assertIsNone(out[c])
        self.assertTrue(all(out[q] == "not found by Lean" for q in rest))
        err = score.parse_axiom_log(t, log + "Check.lean:3:2: error: unknown identifier\n")
        self.assertTrue(all(v == "elaboration error" for v in err.values()))


class LeanTextTests(unittest.TestCase):
    def test_strip_keeps_layout(self):  # T1
        src = 'a -- c\n/- x /- y -/ z -/ b "s -- t" \'"\' x\'\n'
        out = lean_text.strip(src)
        self.assertEqual(len(out), len(src))
        self.assertEqual(out.count("\n"), src.count("\n"))
        self.assertNotIn("c", out.split("\n")[0][1:])
        self.assertTrue(out.rstrip().endswith("x'"))
        self.assertNotIn("--", out)

    def test_statement_boundaries(self):  # T4
        src = ("namespace N\n"
               "theorem t1 (x : Nat) : let y := x\n    y = x := by\n  rfl\n"
               "theorem t2 (a : Int) :\n    |a| = |a| := by rfl\n"
               "theorem t3 : Nat → Nat\n  | 0 => 0\n  | n + 1 => n\n"
               "end N\n"
               "theorem _root_.top : True := trivial\n")
        m = lean_text.theorem_map(src)
        self.assertEqual(set(m), {"N.t1", "N.t2", "N.t3", "top"})
        self.assertEqual(m["N.t1"].statement(), "(x : Nat) : let y := x y = x")
        self.assertEqual(m["N.t2"].statement(), "(a : Int) : |a| = |a|")
        self.assertEqual(m["N.t3"].statement(), ": Nat → Nat")
        self.assertEqual(m["top"].proof(), ":= trivial")


if __name__ == "__main__":
    unittest.main()
