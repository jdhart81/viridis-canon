"""WS-20: function manifests, the OS compiler and the runner runtime.

Invariants exercised here (see os/README.md):
  I1 every callable function has a bundle entry; the bundle is the only product input
  I2 the Python runners reproduce viridis-conservation-app@398b177 exactly
  I3 the compiler never promotes; admitted requires the human ledger; Mutualist BLOCKED
  I4 honest labels: Lean refs, DOI, tier, NOT_VALIDATED
  I5 same commit => same bundle digest
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from canon_core.function_schema import (  # noqa: E402
    OPTIONAL_KEYS,
    REQUIRED_KEYS,
    TIERS,
    RepoContext,
    discover_manifests,
    input_schema,
    load_runtime,
    service_state,
    validate_admissions_ledger,
    validate_manifest,
)
from canon_core.os_build import BuildError, build_os, bundle_digest  # noqa: E402

V = load_runtime(ROOT)


def _manifests():
    out = {}
    for path in discover_manifests(ROOT):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        out[manifest["id"]] = (manifest, path)
    return out


def _tree_digest(paths):
    h = hashlib.sha256()
    for path in sorted(paths):
        h.update(str(path).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


class SchemaDocumentTests(unittest.TestCase):
    def test_json_schema_matches_validator(self):
        schema = json.loads((ROOT / "docs/schemas/function-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), set(REQUIRED_KEYS))
        self.assertEqual(set(schema["properties"]), set(REQUIRED_KEYS) | set(OPTIONAL_KEYS))
        self.assertEqual(tuple(schema["properties"]["tier"]["enum"]), TIERS)
        self.assertFalse(schema["additionalProperties"])


class RepositoryManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = RepoContext.load(ROOT)
        cls.manifests = _manifests()

    def test_every_manifest_is_valid(self):
        errors = []
        for manifest, path in self.manifests.values():
            errors.extend(validate_manifest(manifest, path, self.context))
        errors.extend(validate_admissions_ledger(self.context, {k: v[0] for k, v in self.manifests.items()}))
        self.assertEqual(errors, [])

    def test_the_eighteen_decision_kernels_are_present(self):
        kernels = {k for k, (m, _) in self.manifests.items() if m["kind"] == "decision_kernel"}
        self.assertEqual(len(kernels), 18)
        core = json.loads((ROOT / "os/core.json").read_text(encoding="utf-8"))
        self.assertEqual(set(core["function_order"]), kernels)

    def test_mutualist_stays_blocked(self):  # I3
        manifest, _ = self.manifests["mutualist"]
        self.assertEqual(manifest["state"], "BLOCKED")
        self.assertEqual(manifest["tier"], "reference")
        self.assertIsNone(manifest["runner"])
        self.assertEqual(service_state(manifest), "BLOCKED_PRODUCT_WARRANT_REQUIRED")

    def test_honest_labels(self):  # I4
        for manifest, _ in self.manifests.values():
            self.assertEqual(manifest["empirical_validation"], "NOT_VALIDATED", manifest["id"])
            self.assertTrue(manifest["doi"].startswith("10."), manifest["id"])
            self.assertTrue(manifest["lean"]["theorems"], manifest["id"])
            self.assertIn(manifest["tier"], TIERS)

    def test_tempo_is_flagged_not_hidden(self):
        manifest, _ = self.manifests["tempo"]
        self.assertEqual(manifest["lean"]["sources"], [])
        self.assertEqual(manifest["reconciliation"]["code"], "CANON_RECORD")
        self.assertEqual(manifest["tier"], "callable")

    def test_generated_input_schema_is_closed(self):
        for manifest, _ in self.manifests.values():
            schema = input_schema(manifest)
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["type"], "object")


class NegativeValidationTests(unittest.TestCase):
    """Each rule must actually reject. Mutations are applied to a copy of a real manifest."""

    @classmethod
    def setUpClass(cls):
        cls.context = RepoContext.load(ROOT)
        cls.manifests = _manifests()

    def errors_for(self, fid, mutate, context=None):
        manifest, path = self.manifests[fid]
        m = copy.deepcopy(manifest)
        mutate(m)
        return validate_manifest(m, path, context or self.context)

    def assertRejects(self, fid, mutate, fragment, context=None):
        errors = self.errors_for(fid, mutate, context)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_admitted_requires_ledger(self):  # I3
        self.assertRejects("shared-channel-coverage", lambda m: (m.update(tier="admitted", reconciliation=None)), "os/admissions.json")

    def test_ledger_removal_demotes_nothing_silently(self):  # I3
        context = RepoContext.load(ROOT)
        context.admitted.pop("restoration")
        self.assertRejects("restoration", lambda m: None, "os/admissions.json", context)

    def test_admitted_cannot_carry_reconciliation(self):
        self.assertRejects("restoration", lambda m: m.update(reconciliation={"code": "CANON_CLASSIFICATION", "note": "open item here"}), "open reconciliation")

    def test_blocked_cannot_publish_runner(self):
        self.assertRejects("mutualist", lambda m: m.update(runner="runner.py"), "must not publish a runner")
        self.assertRejects("mutualist", lambda m: m.update(tier="callable"), "only be tier 'reference'")

    def test_lean_hash_is_enforced(self):
        def mutate(m):
            m["lean"]["sources"][0]["sha256"] = "0" * 64
        self.assertRejects("restoration", mutate, "does not match the manifest")

    def test_theorem_names_are_enforced(self):
        self.assertRejects("restoration", lambda m: m["lean"]["theorems"].append("no_such_theorem"), "no_such_theorem")

    def test_doi_cross_check(self):
        self.assertRejects("restoration", lambda m: m.update(doi="10.5281/zenodo.1"), "disagrees with the catalog DOI")

    def test_validation_claim_needs_a_record(self):  # I4
        self.assertRejects("restoration", lambda m: m.update(empirical_validation={"status": "VALIDATED", "record": "nope.md"}), "validation record")

    def test_missing_source_only_for_canon_record(self):
        self.assertRejects("restoration", lambda m: m["lean"].update(sources=[]), "only a CANON_RECORD")

    def test_hypothesis_names_and_grammar(self):
        self.assertRejects("tempo", lambda m: m["hypotheses"].append({"id": "x", "statement": "s", "check": "ghost > 0"}), "unknown inputs")
        self.assertRejects("tempo", lambda m: m["hypotheses"].append({"id": "y", "statement": "s", "check": "__import__('os')"}), "whitelist")
        self.assertRejects("tempo", lambda m: m["hypotheses"].append({"id": "z", "statement": "s", "check": "cadence.real > 0"}), "unsupported syntax")

    def test_example_must_satisfy_schema_and_hypotheses(self):
        self.assertRejects("tempo", lambda m: m["example"]["inputs"].update(cadence=-1), "input schema")

    def test_unknown_keys_rejected(self):
        self.assertRejects("tempo", lambda m: m.update(certificate=True), "unknown key 'certificate'")


class RuntimeSemanticsTests(unittest.TestCase):
    """viridis_fn reproduces the JavaScript numbers the product signs."""

    def test_to_fixed_matches_node(self):
        # [x, Number(x.toFixed(12)), Number(x.toFixed(0)), Number(x.toFixed(9))] from Node 22
        vectors = [
            [0.0001220703125, 0.000122070313, 0, 0.00012207],
            [2.5, 2.5, 3, 2.5],
            [0.5, 0.5, 1, 0.5],
            [1.0000000000005, 1.000000000001, 1, 1],
            [-0.0001220703125, -0.000122070313, 0, -0.00012207],
            [1e21, 1e21, 1e21, 1e21],
            [5e-324, 0, 0, 0],
            [0.30000000000000004, 0.3, 0, 0.3],
        ]
        for x, f12, f0, f9 in vectors:
            self.assertEqual(V.to_fixed(x, 12), f12, x)
            self.assertEqual(V.to_fixed(x, 0), f0, x)
            self.assertEqual(V.to_fixed(x, 9), f9, x)

    def test_locale_usd_matches_node(self):
        for x, text in [(870.785, "870.79"), (1.005, "1.01"), (100000.125, "100,000.13"), (0.125, "0.13"),
                        (2.675, "2.68"), (1e21, "1,000,000,000,000,000,000,000.00"), (1234567.895, "1,234,567.90")]:
            self.assertEqual(V.locale_usd(x), text, x)

    def test_fdlibm_ports_match_node_bit_for_bit(self):
        def bits(x):
            return struct.pack("<d", x)
        for a, b, expected in [(2, 0.5, 1.4142135623730951), (10, 1 / 3, 2.154434690031884), (0.3, 3, 0.026999999999999996),
                               (7.5, -2.25, 0.01074266807949073), (1.0000001, 1e9, 2.6881038582144647e43), (-2, 3, -8)]:
            self.assertEqual(bits(V.js_pow(a, b)), bits(expected), (a, b))
        self.assertTrue(math.isnan(V.js_pow(-8, 1 / 3)))
        self.assertEqual(V.js_pow(0, -1), math.inf)
        for x, log, cosh_log in [(0.1, -2.3025850929940455, 5.049999999999999), (2, 0.6931471805599453, 1.25),
                                 (10, 2.302585092994046, 5.050000000000001), (1e-300, -690.7755278982137, 4.999999999999881e299),
                                 (123.456, 4.815884817283264, 61.73205002592016)]:
            self.assertEqual(bits(V.js_log(x)), bits(log), x)
            self.assertEqual(bits(V.js_cosh(V.js_log(x))), bits(cosh_log), x)

    def test_js_division_never_raises(self):
        self.assertEqual(V.js_div(1, 0), math.inf)
        self.assertEqual(V.js_div(-1, 0), -math.inf)
        self.assertTrue(math.isnan(V.js_div(0, 0)))

    def test_validator_messages_match_product(self):
        schema = {"type": "object", "additionalProperties": False, "required": ["a"],
                  "properties": {"a": {"type": "number", "exclusiveMinimum": 0}, "b": {"type": "integer", "enum": [-1, 1]}}}
        cases = [({}, "inputs missing required field(s): a"), ({"a": 1, "z": 1}, "inputs contains unsupported field(s): z"),
                 ({"a": 0}, "inputs.a must be > 0"), ({"a": True}, "inputs.a must be a finite number"),
                 ({"a": 1, "b": 0}, "inputs.b must be one of -1, 1")]
        for value, message in cases:
            with self.assertRaises(V.InputError) as caught:
                V.validate_schema(value, schema)
            self.assertEqual(str(caught.exception), message)


class CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        watched = [p for p in (ROOT / "os").rglob("*") if p.is_file() and "__pycache__" not in p.parts]
        watched += discover_manifests(ROOT)
        cls.before = _tree_digest(watched)
        cls.watched = watched
        cls.result_a = build_os(ROOT, cls.tmp / "a", source_ref="test")
        cls.result_b = build_os(ROOT, cls.tmp / "b", source_ref="test")
        cls.bundle = json.loads((cls.tmp / "a" / "functions.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_deterministic_digest(self):  # I5
        self.assertEqual(self.result_a["digest"], self.result_b["digest"])
        self.assertEqual(bundle_digest(self.tmp / "a"), self.result_a["digest"])
        self.assertEqual((self.tmp / "a" / "DIGEST").read_text().strip(), self.result_a["digest"])

    def test_compiler_writes_nothing_in_the_repository(self):  # I3
        self.assertEqual(_tree_digest(self.watched), self.before)

    def test_every_callable_manifest_has_a_bundle_entry(self):  # I1
        ids = {f["id"] for f in self.bundle["functions"]}
        for fid, (manifest, _) in _manifests().items():
            self.assertIn(fid, ids)
            entry = next(f for f in self.bundle["functions"] if f["id"] == fid)
            self.assertEqual(entry["tier"], manifest["tier"])  # never promoted
            if entry["runnable"]:
                self.assertTrue((self.tmp / "a" / entry["runner_path"]).is_file())

    def test_bundle_authority(self):  # I3
        self.assertFalse(self.bundle["authority"]["compiler_can_promote"])
        mutualist = next(f for f in self.bundle["functions"] if f["id"] == "mutualist")
        self.assertFalse(mutualist["runnable"])
        self.assertEqual(mutualist["service_state"], "BLOCKED_PRODUCT_WARRANT_REQUIRED")
        for entry in self.bundle["functions"]:
            self.assertFalse(entry["production_certification"])
            self.assertEqual(entry["public_run_authority"], "UNSIGNED_NOT_VIRIDIS_REVIEWED")

    def test_parity_fixtures_were_replayed(self):  # I2
        cases = self.bundle["parity"]["cases_by_function"]
        self.assertEqual(len(cases), 17)
        self.assertTrue(all(n >= 100 for n in cases.values()))

    def test_reference_tier_covers_the_catalog(self):
        reference = json.loads((self.tmp / "a" / "reference.json").read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "docs/data/catalog.json").read_text(encoding="utf-8"))
        self.assertEqual(len(reference["records"]), len(catalog["records"]))

    def test_bundle_self_test_and_dispatch(self):
        run = self.tmp / "a" / "run.py"
        proc = subprocess.run([sys.executable, "-I", "-B", str(run), "--self-test"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        request = {"calls": [{"id": "mutualist", "inputs": {}}, {"id": "tempo", "inputs": {"haste_cost": -1, "neglect_cost": 1, "cadence": 1}}]}
        proc = subprocess.run([sys.executable, "-I", "-B", str(run)], input=json.dumps(request), capture_output=True, text=True)
        results = json.loads(proc.stdout)["results"]
        self.assertEqual(results[0]["error_class"], "blocked")
        self.assertEqual(results[1], {"ok": False, "error_class": "input", "error": "inputs.haste_cost must be > 0"})

    def test_build_refuses_unledgered_admission(self):  # I3
        work = self.tmp / "repo"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".lake", "build", "os-bundle*"))
        ledger = json.loads((work / "os/admissions.json").read_text(encoding="utf-8"))
        ledger["admitted"] = [e for e in ledger["admitted"] if e["id"] != "tempo" and e["id"] != "restoration"]
        (work / "os/admissions.json").write_text(json.dumps(ledger), encoding="utf-8")
        with self.assertRaises(BuildError) as caught:
            build_os(work, self.tmp / "c", replay_parity=False)
        self.assertTrue(any("restoration" in e and "admissions" in e for e in caught.exception.errors))


if __name__ == "__main__":
    unittest.main()


class EngineManifestResilienceTests(unittest.TestCase):
    """I6: a defective engine-authored manifest never blocks the weekly bundle and is never hidden."""

    def test_unprotected_defect_is_recorded_not_fatal(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            work = tmp / "repo"
            shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns(".git", ".lake", "build", "os-bundle*"))
            bad = json.loads((work / "os/functions/perennial-corridor-holding-power/function.json").read_text(encoding="utf-8"))
            bad["id"] = "engine-draft-function"
            bad["lean"]["theorems"] = ["not_in_the_source"]
            target = work / "series" / "SBB" / "engine_draft"
            target.mkdir(parents=True)
            (target / "function.json").write_text(json.dumps(bad), encoding="utf-8")
            result = build_os(work, tmp / "out", replay_parity=False)
            self.assertIn("engine-draft-function", result["rejected"])
            bundle = json.loads((tmp / "out" / "functions.json").read_text(encoding="utf-8"))
            self.assertNotIn("engine-draft-function", {f["id"] for f in bundle["functions"]})
            self.assertEqual(bundle["stats"]["rejected_functions"], 1)
            self.assertTrue(bundle["rejected_functions"][0]["errors"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TheoremFunctionPropertyTests(unittest.TestCase):
    """Whenever a theorem function's hypotheses hold, its conclusion check must hold too.

    A failure would mean the manifest mistranslates the Lean statement (the Lean
    theorem itself is machine-checked). A negative control proves the test can fail.
    """

    SAMPLES = 3000

    @staticmethod
    def _sample(manifest, rng):
        def value(inp):
            if inp["type"] == "array":
                return [rng.choice([0, 0.1, 0.25, 0.5, 1, 2, 3, rng.random(), rng.uniform(0, 5)]) for _ in range(rng.randint(1, 6))]
            if inp["type"] == "integer":
                return rng.randint(0, 8)
            v = rng.choice([0, 0.5, 1, 2, 3, 5, 10, rng.random(), rng.uniform(0, 20), rng.uniform(-5, 5), 10 ** rng.uniform(-6, 6)])
            if "minimum" in inp and v < inp["minimum"]:
                v = inp["minimum"] + abs(v)
            return v
        x = {i["name"]: value(i) for i in manifest["inputs"]}
        if "probabilities" in x:
            total = sum(x["probabilities"]) or 1
            x["probabilities"] = [v / total for v in x["probabilities"]]
        return x

    def _faults(self, manifest, seed=7):
        import random
        sys.path.insert(0, str(ROOT / "os" / "lib"))
        import theorem_runner  # noqa: WPS433
        rng = random.Random(seed)
        held = faults = 0
        for _ in range(self.SAMPLES):
            out = theorem_runner.run_theorem(manifest, self._sample(manifest, rng))
            held += out["hypotheses_hold"]
            faults += out["status"] == "TRANSLATION_FAULT"
        return held, faults

    def test_no_translation_faults(self):
        theorem_functions = [m for m, _ in _manifests().values() if m["kind"] == "theorem_function"]
        self.assertGreaterEqual(len(theorem_functions), 14)
        for manifest in theorem_functions:
            held, faults = self._faults(manifest)
            self.assertGreater(held, 50, f"{manifest['id']}: sampler rarely satisfies the hypotheses")
            self.assertEqual(faults, 0, manifest["id"])

    def test_negative_control_detects_a_flipped_conclusion(self):
        manifest = copy.deepcopy(_manifests()["perennial-corridor-holding-power"][0])
        manifest["conclusion"]["check"] = "approx_le(holding_power_high, holding_power_low)"
        _, faults = self._faults(manifest)
        self.assertGreater(faults, 0)
