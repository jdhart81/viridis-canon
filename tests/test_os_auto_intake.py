"""Auto-intake: proven engine results enter the canon and go live (canon_core/auto_intake.py).

Invariants exercised here (docs/auto_intake/README.md):
  AI-1 only PROVEN, non-trivial, class A/B statements enter; TESTED and conjectures never do;
       the Intelligence Bound is never called proven; no kernel is called product-ready
  AI-2 idempotent: decided or already-backed statements are skipped; applying twice writes once
  AI-3 package shape: manifest, runner, Lean binding by hash, conformance replayed
  AI-4 verify reports every problem and the CLI exits non-zero, so nothing merges on red
  AI-6 go-live is one switch that core.json mirrors; rollback is one step and sticks
  AI-7 every decision is a ledger entry; the owner's note names the kernel and its rollback

The fixture is the real P3.CascadedRecovery result (viridis-research runs/2026-11-16_P3) with
a placeholder DOI, because the run's DOI arrives with the weekly release.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canon_core import auto_intake as AI  # noqa: E402
from canon_core.function_schema import RepoContext, discover_manifests, validate_admissions_ledger, validate_manifest  # noqa: E402
from canon_core.os_build import build_os  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "auto_intake" / "cascaded-recovery-virgin-share"
FID = "cascaded-recovery-virgin-share"
STATEMENT = "P3.CascadedRecovery"
NOW = "2026-11-17T22:00:00Z"


def _digest(root: Path, rels) -> str:
    h = hashlib.sha256()
    for rel in rels:
        h.update((root / rel).read_bytes())
    return h.hexdigest()


GOVERNANCE = (AI.CORE_PATH, AI.ADMISSIONS_PATH, AI.FAMILIES_PATH, AI.INTAKE_PATH, AI.LEDGER_PATH)


class Workspace:
    """A throwaway copy of the canon with the fixture package drafted into it."""

    def __init__(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "canon"
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".lake", "build", "os-bundle*", "__pycache__"))
        self.package = self.root / "research" / FID
        self._forget_fixture_kernel()
        (self.package / "lean").mkdir(parents=True)
        shutil.copy(FIXTURE / "function.fixture.json", self.package / "function.json")
        shutil.copy(FIXTURE / "runner.py", self.package / "runner.py")
        shutil.copy(FIXTURE / "intake.json", self.package / "intake.json")
        for name in ("Statement.lean.txt", "Proof.lean.txt"):
            shutil.copy(FIXTURE / "lean" / name, self.package / "lean" / name)
        shutil.copy(FIXTURE / "conformance_test.fixture.py", self.root / AI.conformance_test_path(FID))
        self.index = json.loads((FIXTURE / "certified_index.json").read_text(encoding="utf-8"))

    def _forget_fixture_kernel(self) -> None:
        """Start from a canon in which the fixture statement was never decided, even after it really enters."""
        shutil.rmtree(self.package, ignore_errors=True)
        (self.root / AI.conformance_test_path(FID)).unlink(missing_ok=True)
        edits = {
            AI.LEDGER_PATH: lambda d: d.update(entries=[e for e in d["entries"] if e["statement"] != STATEMENT]),
            AI.CORE_PATH: lambda d: d.update(function_order=[f for f in d["function_order"] if f != FID]),
            AI.ADMISSIONS_PATH: lambda d: d.update(admitted=[a for a in d["admitted"] if a["id"] != FID]),
            AI.INTAKE_PATH: lambda d: d.update(records=[r for r in d["records"] if r.get("abbreviation") != STATEMENT]),
            AI.FAMILIES_PATH: lambda d: [f.update(function_order=[x for x in f["function_order"] if x != FID]) for f in d["families"]],
        }
        for rel, edit in edits.items():
            doc = json.loads((self.root / rel).read_text(encoding="utf-8"))
            edit(doc)
            (self.root / rel).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def manifest(self) -> dict:
        return json.loads((self.package / "function.json").read_text(encoding="utf-8"))

    def write_manifest(self, manifest: dict) -> None:
        (self.package / "function.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def intake(self) -> dict:
        return json.loads((self.package / "intake.json").read_text(encoding="utf-8"))

    def write_intake(self, intake: dict) -> None:
        (self.package / "intake.json").write_text(json.dumps(intake, indent=2), encoding="utf-8")

    def json(self, rel: str):
        return json.loads((self.root / rel).read_text(encoding="utf-8"))

    def set_policy(self, **changes) -> None:
        policy = self.json(AI.POLICY_PATH)
        policy.update(changes)
        (self.root / AI.POLICY_PATH).write_text(json.dumps(policy, indent=2), encoding="utf-8")

    def validate_all(self) -> list[str]:
        context = RepoContext.load(self.root)
        errors, manifests = [], {}
        for path in discover_manifests(self.root):
            manifest = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(validate_manifest(manifest, path, context))
            manifests[manifest["id"]] = manifest
        return errors + validate_admissions_ledger(context, manifests)

    def close(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)


class _Base(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace()
        self.addCleanup(self.ws.close)

    def verify(self):
        return AI.verify(self.ws.root, self.ws.index, self.ws.package)


class EligibilityTests(_Base):  # AI-1
    def test_the_proven_package_passes(self):
        self.assertEqual(self.verify(), [])

    def test_plan_reports_every_statement_with_a_reason(self):
        plan = AI.plan(self.ws.root, self.ws.index)
        rows = {r["statement"]: r for r in plan["rows"]}
        self.assertEqual(rows[STATEMENT]["decision"], "CANDIDATE")
        self.assertEqual(rows["P3.CyclicSymbiosis"]["decision"], "SKIP")
        self.assertIn("SEALED_UNPROVEN", rows["P3.CyclicSymbiosis"]["reason"])
        tested = [r for r in plan["rows"] if "TESTED" in r["reason"]]
        self.assertTrue(tested and all(r["decision"] == "SKIP" for r in tested))
        self.assertTrue(all(r["reason"] for r in plan["rows"]))

    def test_tested_results_never_enter(self):
        claim = self.ws.index["tested_claims"][0]
        problems = AI.eligibility(self.ws.index, f"{claim['project']}.{claim['claim_id']}")
        self.assertTrue(any("TESTED" in p for p in problems))

    def test_unproven_or_trivial_statements_never_enter(self):
        for mutate, expect in (
            (lambda r: r.update(status="SEALED_UNPROVEN"), "not PROVEN"),
            (lambda r: r.update(proof=None), "not PROVEN"),
            (lambda r: r.update(closed_by_single_tactic=True), "trivial"),
        ):
            index = copy.deepcopy(self.ws.index)
            mutate(index["statements"][STATEMENT])
            problems = AI.verify(self.ws.root, index, self.ws.package)
            self.assertTrue(any(expect in p for p in problems), (expect, problems))

    def test_only_class_a_or_b_enters(self):
        for klass in ("C", "RECERT", None):
            intake = self.ws.intake()
            intake["class"] = klass
            self.ws.write_intake(intake)
            self.assertTrue(any("only A or B" in p for p in self.verify()), klass)

    def test_class_b_must_name_what_it_strengthens(self):
        intake = self.ws.intake()
        intake["strengthens"] = None
        self.ws.write_intake(intake)
        self.assertTrue(any("strengthens" in p for p in self.verify()))

    def test_entry_waits_for_the_run_doi(self):
        index = copy.deepcopy(self.ws.index)
        index["statements"][STATEMENT]["proof"]["doi"] = None
        rows = {r["statement"]: r for r in AI.plan(self.ws.root, index)["rows"]}
        self.assertEqual(rows[STATEMENT]["decision"], "WAIT")
        self.assertTrue(any("DOI" in p for p in AI.verify(self.ws.root, index, self.ws.package)))

    def test_the_intelligence_bound_is_never_called_proven(self):
        for text in ("This kernel applies the Intelligence Bound.",
                     "The Intelligence Bound is proven, so recovery is bounded (a conjecture elsewhere)."):
            manifest = self.ws.manifest()
            manifest["scope"] = text
            self.ws.write_manifest(manifest)
            self.assertTrue(any("conjecture" in p for p in self.verify()), text)
        manifest = self.ws.manifest()
        manifest["scope"] = "Unrelated to the Intelligence Bound conjecture; a single material stream in series."
        self.ws.write_manifest(manifest)
        self.assertEqual(self.verify(), [])

    def test_no_kernel_is_called_product_ready(self):
        manifest = self.ws.manifest()
        manifest["summary"] += " Product-ready for clients."
        self.ws.write_manifest(manifest)
        self.assertTrue(any("product-ready" in p for p in self.verify()))


class PackageShapeTests(_Base):  # AI-3
    def test_wrong_formula_breaks_conformance(self):
        runner = self.ws.package / "runner.py"
        runner.write_text(runner.read_text(encoding="utf-8").replace("share *= 1 - x", "share *= 1 - x / 2"), encoding="utf-8")
        problems = self.verify()
        self.assertTrue(any("statement part" in p or "example" in p for p in problems), problems)

    def test_hypothesis_violations_must_be_refused(self):
        runner = self.ws.package / "runner.py"
        runner.write_text(runner.read_text(encoding="utf-8").replace("if f > 1:", "if f > 10:"), encoding="utf-8")
        self.assertTrue(any("negative control 0 was not refused" in p for p in self.verify()))

    def test_lean_sources_must_be_the_sealed_files(self):
        proof = self.ws.package / "lean" / "Proof.lean.txt"
        proof.write_text(proof.read_text(encoding="utf-8") + "\n-- edited\n", encoding="utf-8")
        manifest = self.ws.manifest()
        for source in manifest["lean"]["sources"]:
            if source["path"].endswith("Proof.lean.txt"):
                source["sha256"] = hashlib.sha256(proof.read_bytes()).hexdigest()
        self.ws.write_manifest(manifest)
        self.assertTrue(any("checked proof" in p for p in self.verify()))

    def test_entry_shape_is_enforced(self):
        for key, value, expect in (
            ("tier", "admitted", "tier must be"),
            ("kind", "theorem_function", "kind must be"),
            ("empirical_validation", {"status": "VALIDATED", "record": "x"}, "empirical_validation"),
            ("boundary", "Exact arithmetic of the series-stage model only, nothing else is said here.", "does not establish"),
            ("doi", "10.5281/zenodo.1", "run DOI"),
        ):
            manifest = json.loads((FIXTURE / "function.fixture.json").read_text(encoding="utf-8"))
            manifest[key] = value
            self.ws.write_manifest(manifest)
            self.assertTrue(any(expect in p for p in self.verify()), (key, self.verify()))
        self.ws.write_manifest(json.loads((FIXTURE / "function.fixture.json").read_text(encoding="utf-8")))

    def test_conformance_needs_cases_controls_and_a_test_file(self):
        manifest = self.ws.manifest()
        manifest["provenance"]["conformance_cases"] = manifest["provenance"]["conformance_cases"][:1]
        manifest["provenance"]["negative_controls"] = []
        self.ws.write_manifest(manifest)
        (self.ws.root / AI.conformance_test_path(FID)).unlink()
        problems = self.verify()
        for expect in ("at least three", "negative_controls", "missing"):
            self.assertTrue(any(expect in p for p in problems), expect)

    def test_package_lives_under_research(self):
        moved = self.ws.root / "series" / FID
        shutil.copytree(self.ws.package, moved)
        problems = AI.verify(self.ws.root, self.ws.index, moved)
        self.assertTrue(any("research/<function id>/" in p for p in problems))

    def test_cli_exits_non_zero_on_any_problem(self):  # AI-4
        runner = self.ws.package / "runner.py"
        runner.write_text(runner.read_text(encoding="utf-8").replace("share *= 1 - x", "share *= 1 - x / 2"), encoding="utf-8")
        index = self.ws.tmp / "index.json"
        index.write_text(json.dumps(self.ws.index), encoding="utf-8")
        proc = subprocess.run([sys.executable, "-m", "canon_core", "auto-intake", "verify", "--root", str(self.ws.root),
                               "--index", str(index), "--package", str(self.ws.package)],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("ERROR:", proc.stdout)


class LifecycleTests(_Base):  # AI-2, AI-6, AI-7
    def test_apply_go_live_rollback(self):
        ws = self.ws
        before = ws.json(AI.CORE_PATH)["function_order"]
        entry = AI.apply(ws.root, ws.index, ws.package, now=NOW, regenerate=True)
        self.assertEqual((entry["status"], entry["function_id"], entry["class"]), ("ENTERED", FID, "B"))
        self.assertEqual(entry["run_dir"], "runs/2026-11-16_P3")
        family = next(f for f in ws.json(AI.FAMILIES_PATH)["families"] if f["id"] == "governance-coordination")
        self.assertIn(FID, family["function_order"])
        record = next(r for r in ws.json(AI.INTAKE_PATH)["records"] if r["abbreviation"] == STATEMENT)
        self.assertEqual(record["state"], "CERTIFICATION_READY")
        self.assertIn(FID, (ws.root / "formalization.yaml").read_text(encoding="utf-8"))
        self.assertEqual(ws.json(AI.CORE_PATH)["function_order"], before)  # entered is not live

        # AI-2: a second apply writes nothing; the statement is now skipped with its reason
        snapshot = _digest(ws.root, GOVERNANCE)
        again = AI.apply(ws.root, ws.index, ws.package, now="2026-11-18T22:00:00Z", regenerate=False)
        self.assertEqual(again, entry)
        self.assertEqual(_digest(ws.root, GOVERNANCE), snapshot)
        rows = {r["statement"]: r for r in AI.plan(ws.root, ws.index)["rows"]}
        self.assertEqual(rows[STATEMENT]["decision"], "SKIP")
        self.assertIn("already decided", rows[STATEMENT]["reason"])

        proc = subprocess.run([sys.executable, "-m", "unittest", "tests.test_os_auto_cascaded_recovery_virgin_share"],
                              cwd=ws.root, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])  # the kernel's own conformance tests

        live = AI.go_live(ws.root, FID, now=NOW, regenerate=True)
        self.assertEqual(live["status"], "LIVE")
        self.assertEqual(ws.json(AI.CORE_PATH)["function_order"], before + [FID])
        admission = next(a for a in ws.json(AI.ADMISSIONS_PATH)["admitted"] if a["id"] == FID)
        self.assertIn("2026-11-17", admission["human_gate"])
        self.assertIn(f"rollback --function {FID}", admission["human_gate"])
        self.assertEqual(ws.manifest()["tier"], "admitted")
        self.assertEqual(ws.validate_all(), [])
        out = ws.tmp / "bundle-live"
        result = build_os(ws.root, out, replay_parity=False)
        bundle = json.loads((out / "functions.json").read_text(encoding="utf-8"))
        self.assertIn(FID, {f["id"] for f in bundle["functions"]})
        self.assertNotIn(FID, result["rejected"])
        self.assertEqual(AI.go_live(ws.root, FID, now="2026-11-19T00:00:00Z", regenerate=False)["live_at"], NOW)

        note = AI.note(ws.root, "2026-11-17T00:00:00Z")
        self.assertIn(FID, note)
        self.assertIn("LIVE", note)
        self.assertIn(f"rollback --function {FID}", note)

        rolled = AI.rollback(ws.root, FID, now="2026-11-18T09:00:00Z", regenerate=True)
        self.assertEqual(rolled["status"], "ROLLED_BACK")
        self.assertEqual(ws.json(AI.CORE_PATH)["function_order"], before)
        self.assertNotIn(FID, {a["id"] for a in ws.json(AI.ADMISSIONS_PATH)["admitted"]})
        self.assertEqual(ws.manifest()["tier"], "callable")
        self.assertEqual(ws.validate_all(), [])
        out = ws.tmp / "bundle-rolled"
        result = build_os(ws.root, out, replay_parity=False)
        bundle = json.loads((out / "functions.json").read_text(encoding="utf-8"))
        self.assertNotIn(FID, {f["id"] for f in bundle["functions"]})
        self.assertIn(FID, result["rejected"])
        with self.assertRaises(AI.IntakeError):
            AI.go_live(ws.root, FID)  # a rolled-back kernel never comes back by itself
        self.assertEqual(AI.rollback(ws.root, FID, regenerate=False)["rolled_back_at"], "2026-11-18T09:00:00Z")

    def test_ci_audit_accepts_only_auto_intake_live_list_changes(self):  # AI-6 guard in os-bundle.yml
        ws = self.ws
        base_adm, base_core = ws.json(AI.ADMISSIONS_PATH), ws.json(AI.CORE_PATH)
        AI.apply(ws.root, ws.index, ws.package, now=NOW, regenerate=False)
        AI.go_live(ws.root, FID, now=NOW, regenerate=False)
        self.assertEqual(AI.audit_admissions(ws.root, base_adm, base_core), [])
        live_adm, live_core = ws.json(AI.ADMISSIONS_PATH), ws.json(AI.CORE_PATH)
        hand = ws.json(AI.ADMISSIONS_PATH)
        hand["admitted"].append({"id": "pcs", "tier": "admitted", "evidence": "x", "human_gate": "x"})
        hand["admitted"][0]["evidence"] = "edited"
        (ws.root / AI.ADMISSIONS_PATH).write_text(json.dumps(hand), encoding="utf-8")
        problems = AI.audit_admissions(ws.root, base_adm, base_core)
        self.assertTrue(any("pcs" in p for p in problems))
        self.assertTrue(any("existing admission entry changed" in p for p in problems))
        (ws.root / AI.ADMISSIONS_PATH).write_text(json.dumps(live_adm), encoding="utf-8")
        AI.rollback(ws.root, FID, now=NOW, regenerate=False)
        self.assertEqual(AI.audit_admissions(ws.root, live_adm, live_core), [])
        core = ws.json(AI.CORE_PATH)
        core["function_order"] = list(reversed(core["function_order"]))
        (ws.root / AI.CORE_PATH).write_text(json.dumps(core), encoding="utf-8")
        self.assertTrue(any("operating order changed" in p for p in AI.audit_admissions(ws.root, live_adm, live_core)))

    def test_go_live_switch_off_writes_nothing(self):
        ws = self.ws
        AI.apply(ws.root, ws.index, ws.package, now=NOW, regenerate=False)
        ws.set_policy(go_live=False)
        snapshot = _digest(ws.root, (AI.CORE_PATH, AI.ADMISSIONS_PATH))
        with self.assertRaises(AI.IntakeError):
            AI.go_live(ws.root, FID)
        self.assertEqual(_digest(ws.root, (AI.CORE_PATH, AI.ADMISSIONS_PATH)), snapshot)

    def test_go_live_needs_core_to_agree(self):
        ws = self.ws
        AI.apply(ws.root, ws.index, ws.package, now=NOW, regenerate=False)
        core = ws.json(AI.CORE_PATH)
        core["authority"]["automatic_kernel_activation"] = False
        (ws.root / AI.CORE_PATH).write_text(json.dumps(core, indent=2), encoding="utf-8")
        with self.assertRaises(AI.IntakeError):
            AI.go_live(ws.root, FID)

    def test_intake_switch_off_enters_nothing(self):
        self.ws.set_policy(enabled=False)
        snapshot = _digest(self.ws.root, GOVERNANCE)
        with self.assertRaises(AI.IntakeError):
            AI.apply(self.ws.root, self.ws.index, self.ws.package, regenerate=False)
        self.assertEqual(_digest(self.ws.root, GOVERNANCE), snapshot)

    def test_declined_statements_are_logged_once(self):
        ws = self.ws
        with self.assertRaises(AI.IntakeError):
            AI.decide(ws.root, ws.index, STATEMENT, "B", "class B enters through apply, never decide")
        first = AI.decide(ws.root, ws.index, STATEMENT, "C", "no buyer decision in this test", now=NOW)
        second = AI.decide(ws.root, ws.index, STATEMENT, "C", "a different reason later", now="2026-11-20T00:00:00Z")
        self.assertEqual(first, second)
        self.assertEqual(len([e for e in AI.load_ledger(ws.root)["entries"] if e["statement"] == STATEMENT]), 1)
        self.assertIn("not entered, class C", AI.note(ws.root, "2026-11-17T00:00:00Z"))
        self.assertTrue(any("already decided" in p for p in self.verify()))

    def test_a_statement_already_backing_a_function_is_skipped(self):
        ws = self.ws
        other = ws.root / "series" / "PCS" / "function.json"
        manifest = json.loads(other.read_text(encoding="utf-8"))
        manifest.setdefault("provenance", {})["research_statement"] = STATEMENT
        other.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        rows = {r["statement"]: r for r in AI.plan(ws.root, ws.index)["rows"]}
        self.assertEqual(rows[STATEMENT]["decision"], "SKIP")
        self.assertIn("already backs", rows[STATEMENT]["reason"])
        self.assertTrue(any("already backs" in p for p in self.verify()))


class RepositoryStateTests(unittest.TestCase):
    """The checked-in policy, ledger and live list agree, and every auto kernel still conforms."""

    def test_switch_and_core_agree(self):
        policy = json.loads((ROOT / AI.POLICY_PATH).read_text(encoding="utf-8"))
        core = json.loads((ROOT / AI.CORE_PATH).read_text(encoding="utf-8"))
        self.assertEqual(policy["standard"], "VOS-AUTO-INTAKE-1")
        self.assertEqual(bool(policy["go_live"]), core["authority"]["automatic_kernel_activation"])
        self.assertEqual(policy["max_new_kernels_per_run"], 1)

    def test_every_ledger_entry_is_consistent(self):
        core = json.loads((ROOT / AI.CORE_PATH).read_text(encoding="utf-8"))["function_order"]
        admitted = {a["id"] for a in json.loads((ROOT / AI.ADMISSIONS_PATH).read_text(encoding="utf-8"))["admitted"]}
        for entry in AI.load_ledger(ROOT)["entries"]:
            for key in ("statement", "class", "status", "run_dir", "reason", "decided_at"):
                self.assertIn(key, entry)
            fid = entry.get("function_id")
            if entry["status"] == "DECLINED":
                self.assertIn(entry["class"], AI.CLASSES_DECLINE)
                self.assertIsNone(fid)
                continue
            self.assertIn(entry["class"], AI.CLASSES_ENTER)
            package = ROOT / "research" / fid
            self.assertEqual(AI.conformance_problems(ROOT, package), [], fid)
            self.assertTrue((ROOT / AI.conformance_test_path(fid)).is_file(), fid)
            self.assertEqual(entry["status"] == "LIVE", fid in core, fid)
            self.assertEqual(entry["status"] == "LIVE", fid in admitted, fid)


if __name__ == "__main__":
    unittest.main()
