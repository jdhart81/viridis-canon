"""Compile census: completeness (C1), bytes (C2), no silent pass (C4). The Lean-running parts are exercised in CI."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import compile_census as cc  # noqa: E402


def make_repo(tmp: Path) -> Path:
    (tmp / "lakefile.toml").write_text('name = "Root"\n[leanOptions]\nautoImplicit = false\n[[lean_lib]]\nname = "A"\n')
    (tmp / "lean-toolchain").write_text("leanprover/lean4:v4.28.0\n")
    (tmp / "A.lean").write_text("/- header\nimport Fake.InComment\n-/\nimport Mathlib\n-- import Not.This\nimport B\n\ntheorem t : True := trivial\nimport Late\n")
    (tmp / "B.lean").write_text("import Mathlib.Tactic\ndef b := 1\n")
    (tmp / "Old.lean").write_text("import Mathlib\n")
    proj = tmp / "series" / "X"
    proj.mkdir(parents=True)
    (proj / "lakefile.toml").write_text('name = "x"\n[[lean_lib]]\nname = "Main"\n')
    (proj / "lean-toolchain").write_text("leanprover/lean4:v4.28.0\n")
    (proj / "Main.lean").write_text("import Sub.Part\nimport B\n")
    (proj / "Sub").mkdir()
    (proj / "Sub" / "Part.lean").write_text("import Mathlib\n")
    compat = tmp / "compat" / "old"
    compat.mkdir(parents=True)
    (compat / "lakefile.toml").write_text('name = "c"\n[[lean_lib]]\nname = "Old"\nsrcDir = "../.."\nglobs = ["Old"]\n')
    (compat / "lean-toolchain").write_text("leanprover/lean4:v4.24.0\n")
    (tmp / "certificates" / "Run-1").mkdir(parents=True)
    (tmp / "certificates" / "Run-1" / "C.lean").write_text("import Mathlib\n")
    (tmp / ".lake" / "packages").mkdir(parents=True)
    (tmp / ".lake" / "packages" / "Skip.lean").write_text("x")
    return tmp


class Planning(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.repo = make_repo(self.tmp)
        self.plan = cc.build_plan(self.repo)
        self.files = self.plan["files"]

    def test_every_lean_file_once_and_lake_dir_skipped(self):
        self.assertEqual(sorted(self.files), ["A.lean", "B.lean", "Old.lean", "certificates/Run-1/C.lean",
                                              "series/X/Main.lean", "series/X/Sub/Part.lean"])

    def test_header_imports_only(self):
        self.assertEqual(cc.parse_imports((self.repo / "A.lean").read_text()), ["Mathlib", "B"])

    def test_units_modules_and_dependencies(self):
        self.assertEqual(self.files["A.lean"]["deps"], ["B.lean"])
        main = self.files["series/X/Main.lean"]
        self.assertEqual((main["unit"], main["module"]), ("series/X", "Main"))
        self.assertEqual(main["deps"], ["B.lean", "series/X/Sub/Part.lean"])       # own project first, then the root
        self.assertEqual(self.files["certificates/Run-1/C.lean"]["module"], "certificates.«Run-1».C")

    def test_a_file_claimed_through_srcdir_gets_that_projects_toolchain(self):
        self.assertEqual(self.files["Old.lean"]["toolchain"], "leanprover/lean4:v4.24.0")
        self.assertEqual(self.files["A.lean"]["toolchain"], "leanprover/lean4:v4.28.0")
        self.assertEqual(self.files["A.lean"]["options"], {"autoImplicit": False})

    def test_order_puts_dependencies_first(self):
        order = self.plan["order"]
        self.assertLess(order.index("B.lean"), order.index("A.lean"))
        self.assertLess(order.index("series/X/Sub/Part.lean"), order.index("series/X/Main.lean"))

    def test_shards_partition_the_files_and_closures_carry_dependencies(self):
        owned = [[p for p in self.files if cc.shard_of(p, 3) == i] for i in range(3)]
        self.assertEqual(sorted(sum(owned, [])), sorted(self.files))
        self.assertIn("B.lean", cc.closure(["series/X/Main.lean"], self.files))


class Merging(unittest.TestCase):
    def entry(self, path, status="CLEAN", **kw):
        return {"path": path, "status": status, "sha256": "0" * 64, **kw}

    def test_complete_ledger_counts(self):
        reps = [{"commit": "c", "entries": [self.entry("a.lean", declarations=3, theorems=2)]},
                {"commit": "c", "entries": [self.entry("b.lean", "COMPILE_FAILED", detail="error: x")]}]
        ledger = cc.merge_reports(reps, ["a.lean", "b.lean"])
        self.assertEqual((ledger["files"], ledger["counts"]["CLEAN"], ledger["counts"]["COMPILE_FAILED"]), (2, 1, 1))
        self.assertEqual((ledger["declarations"], ledger["theorems"]), (3, 2))

    def test_missing_duplicate_unknown_and_mixed_commits_are_refused(self):
        one = {"commit": "c", "entries": [self.entry("a.lean")]}
        with self.assertRaisesRegex(ValueError, "missing"):
            cc.merge_reports([one], ["a.lean", "b.lean"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            cc.merge_reports([one, one], ["a.lean"])
        with self.assertRaisesRegex(ValueError, "unknown"):
            cc.merge_reports([one], [])
        with self.assertRaisesRegex(ValueError, "unknown status"):
            cc.merge_reports([{"commit": "c", "entries": [self.entry("a.lean", "PASSED")]}], ["a.lean"])
        with self.assertRaisesRegex(ValueError, "different commits"):
            cc.merge_reports([one, {"commit": "d", "entries": [self.entry("b.lean")]}], ["a.lean", "b.lean"])

    def test_regressions_need_the_same_recorded_status(self):
        ledger = cc.merge_reports([{"commit": "c", "entries": [
            self.entry("a.lean"), self.entry("b.lean", "COMPILE_FAILED"), self.entry("c.lean", "NONSTANDARD_AXIOM"),
            self.entry("d.lean", "NO_DECLARATIONS")]}], ["a.lean", "b.lean", "c.lean", "d.lean"])
        gaps = {"gaps": [{"path": "b.lean", "status": "COMPILE_FAILED"}, {"path": "c.lean", "status": "COMPILE_FAILED"}]}
        reg = cc.regressions(ledger, gaps)
        self.assertEqual(len(reg), 1)
        self.assertTrue(reg[0].startswith("c.lean: NONSTANDARD_AXIOM"))

    def test_audit_output_is_parsed_strictly(self):
        m = cc.RESULT_RE.search("noise\nCENSUS_RESULT checked=4 theorems=2 axioms=[propext, sorryAx] violations=[Foo.bar:sorryAx]\n")
        self.assertEqual(m.groups(), ("4", "2", "propext, sorryAx", "Foo.bar:sorryAx"))
        self.assertIsNone(cc.RESULT_RE.search("CENSUS_RESULT checked=4"))


class RealRepository(unittest.TestCase):
    def test_plan_covers_every_lean_file_in_the_canon(self):
        plan = cc.build_plan(REPO)
        self.assertEqual(sorted(plan["files"]), cc.lean_files(REPO))
        self.assertEqual(sorted(plan["order"]), cc.lean_files(REPO))
        self.assertEqual(plan["files"]["P0_IntelligenceBound_COMPILED.lean"]["toolchain"], "leanprover/lean4:v4.24.0")
        for e in plan["files"].values():
            self.assertTrue(e["toolchain"], e["path"])

    def test_committed_snapshots_are_well_formed(self):
        """A snapshot is a dated record of one census at one commit; CI regenerates the live ledger."""
        for path in sorted((REPO / "reports" / "compile_census").glob("ledger-*.json")):
            ledger = json.loads(path.read_text())
            self.assertEqual(ledger["schema"], "viridis-canon/compile-census/v1")
            self.assertEqual(ledger["files"], len(ledger["entries"]))
            self.assertEqual(sum(ledger["counts"].values()), ledger["files"])
            for e in ledger["entries"]:
                self.assertIn(e["status"], cc.STATUSES)
                self.assertRegex(e["sha256"], r"^[0-9a-f]{64}$")                         # C2
        gaps_path = REPO / "reports" / "compile_census" / "known_gaps.json"
        if gaps_path.is_file():
            for g in json.loads(gaps_path.read_text())["gaps"]:
                self.assertIn(g["status"], cc.STATUSES)
                self.assertTrue((REPO / g["path"]).is_file(), g["path"])
                self.assertTrue(g.get("reason"), g["path"])


if __name__ == "__main__":
    unittest.main()
