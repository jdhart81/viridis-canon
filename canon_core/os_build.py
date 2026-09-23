"""``python -m canon_core build-os`` — compile the canon into the Viridis OS bundle.

The repository is the research, the bundle is the OS, the site is its interface.

Build steps (any failure aborts; nothing is written on failure):

1. discover every ``function.json``; validate each manifest and the admissions
   ledger (``canon_core.function_schema``);
2. check the OS governance files agree with the manifests (families, order);
3. run every published example through its runner and require an exact match;
4. replay the recorded parity fixtures (``os/parity/*.json``) — WS-20 I2;
5. emit the bundle: ``functions.json``, ``reference.json`` (every catalog record),
   ``runners/``, ``run.py``, ``SHA256SUMS`` and ``DIGEST``;
6. execute the written bundle's own ``run.py --self-test`` in a clean process.

Determinism (I5): no clocks, no randomness, sorted keys and paths, and the
digest is the SHA-256 of ``SHA256SUMS`` (one ``<sha256>  <path>`` line per file,
path-sorted), so the same commit always yields the same ``DIGEST``.

Authority (I3): the compiler reads tiers and the admissions ledger and never
writes either; it cannot promote a function.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from .function_schema import (
    RepoContext,
    discover_manifests,
    input_schema,
    is_runnable,
    load_runtime,
    service_state,
    units_map,
    validate_admissions_ledger,
    validate_manifest,
)

BUNDLE_SCHEMA = "https://jdhart81.github.io/viridis-canon/schemas/os-bundle-v1.json"
BUNDLE_VERSION = 1
TIER_RANK = {"reference": 0, "callable": 1, "admitted": 2}


class BuildError(RuntimeError):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def _read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(value: Any) -> str:
    return json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"


def _sanitize(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(v) for v in value]
    return value


def same_json(a: Any, b: Any, path: str = "$") -> str | None:
    """Strict JSON-number equality; returns a description of the first difference."""

    if isinstance(a, bool) or isinstance(b, bool):
        return None if (type(a) is bool and type(b) is bool and a == b) else f"{path}: {a!r} != {b!r}"
    if a is None or b is None:
        return None if (a is None and b is None) else f"{path}: {a!r} != {b!r}"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return None if float(a) == float(b) else f"{path}: {a!r} != {b!r}"
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return f"{path}: length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            diff = same_json(x, y, f"{path}[{i}]")
            if diff:
                return diff
        return None
    if isinstance(a, dict) and isinstance(b, dict):
        if list(a) != list(b):
            return f"{path}: keys {list(a)} != {list(b)}"
        for key in a:
            diff = same_json(a[key], b[key], f"{path}.{key}")
            if diff:
                return diff
        return None
    return None if a == b else f"{path}: {a!r} != {b!r}"


class Runners:
    """Loads manifest runners in-process with the repository runtime on the path."""

    def __init__(self, root: Path):
        self.root = root
        self.runtime = load_runtime(root)
        lib = str(root / "os" / "lib")
        if lib not in sys.path:
            sys.path.insert(0, lib)
        spec = importlib.util.spec_from_file_location("theorem_runner", root / "os" / "lib" / "theorem_runner.py")
        self.theorem = importlib.util.module_from_spec(spec)
        sys.modules["theorem_runner"] = self.theorem
        spec.loader.exec_module(self.theorem)
        self._modules: dict[str, Any] = {}

    def call(self, manifest: dict[str, Any], manifest_path: Path, inputs: dict[str, Any]) -> dict[str, Any]:
        runtime = self.runtime
        try:
            runtime.validate_schema(inputs, input_schema(manifest))
            if manifest["runner"] == "theorem":
                output = self.theorem.run_theorem(manifest, inputs)
            else:
                key = manifest["id"]
                if key not in self._modules:
                    spec = importlib.util.spec_from_file_location(
                        f"canon_runner_{key.replace('-', '_')}", manifest_path.parent / "runner.py"
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._modules[key] = module
                output = self._modules[key].run(json.loads(json.dumps(inputs)))
            return {"ok": True, "output": _sanitize(output)}
        except runtime.InputError as error:
            return {"ok": False, "error": str(error), "cls": "DecisionKernelInputError"}
        except Exception as error:  # noqa: BLE001 - a fault is reported, never swallowed
            return {"ok": False, "error": f"FAULT {type(error).__name__}: {error}", "cls": "fault"}


def _function_entry(manifest: dict[str, Any], path: Path, root: Path, catalog_by_path: dict[str, Any]) -> dict[str, Any]:
    entry = {k: v for k, v in manifest.items() if k != "$schema"}
    rel = path.relative_to(root).as_posix()
    runnable = is_runnable(manifest)
    canon_records = []
    for source in manifest["lean"]["sources"]:
        record = catalog_by_path.get(source["path"])
        if record is not None:
            canon_records.append({
                "record_id": record["record_id"],
                "path": record["path"],
                "status": record["status"],
                "integrity": record["integrity"],
                "title": record["title"],
            })
    runner_path = None
    if runnable:
        runner_path = "runners/theorem_runner.py" if manifest["runner"] == "theorem" else f"runners/{manifest['id']}.py"
    entry.update({
        "manifest_path": rel,
        "manifest_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "input_schema": input_schema(manifest),
        "units": units_map(manifest),
        "runnable": runnable,
        "service_state": service_state(manifest),
        "runner_path": runner_path,
        "canon_records": canon_records,
        "public_run_authority": "UNSIGNED_NOT_VIRIDIS_REVIEWED",
        "production_certification": False,
    })
    return entry


def build_os(
    root: Path,
    out_dir: Path,
    *,
    source_ref: str = "",
    release: str = "",
    replay_parity: bool = True,
    self_test: bool = True,
) -> dict[str, Any]:
    root = root.resolve()
    context = RepoContext.load(root)
    errors: list[str] = []

    # 1. manifests ------------------------------------------------------
    # A manifest is *protected* when a human has pinned it: listed in
    # os/core.json function_order (the product's decision kernels) or in the
    # admissions ledger. Any defect in a protected manifest fails the build.
    # Any other manifest (e.g. one written by the nightly engine's package
    # template) that fails validation is *rejected*: it is left out of the
    # callable set, recorded with its errors in the bundle, and its catalog
    # record stays visible in the reference tier. Nothing is filtered silently.
    core = _read(root / "os" / "core.json")
    families_doc = _read(root / "os" / "families.json")
    intake = _read(root / "os" / "research_intake.json")
    protected = set(core.get("function_order", [])) | set(context.admitted)
    manifests: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    rejected: dict[str, dict[str, Any]] = {}

    def reject(key: str, path: Path, problems: list[str]) -> None:
        if key in protected:
            errors.extend(problems)
        else:
            entry = rejected.setdefault(key, {"manifest_path": path.relative_to(root).as_posix(), "errors": []})
            entry["errors"].extend(problems)

    for path in discover_manifests(root):
        rel = path.relative_to(root).as_posix()
        try:
            manifest = _read(path)
        except json.JSONDecodeError as error:
            reject(rel, path, [f"{rel}: invalid JSON: {error}"])
            continue
        mid = manifest.get("id") if isinstance(manifest, dict) else None
        if not isinstance(mid, str) or not mid:
            reject(rel, path, [f"{rel}: manifest has no id"])
            continue
        if mid in manifests or mid in rejected:
            errors.append(f"{rel}: duplicate function id '{mid}'")
            continue
        problems = validate_manifest(manifest, path, context)
        if problems:
            reject(mid, path, problems)
            continue
        manifests[mid] = manifest
        paths[mid] = path
    errors.extend(validate_admissions_ledger(context, {**manifests, **{k: {} for k in rejected}}))
    for mid in protected:
        if mid not in manifests and mid not in rejected and not any(mid in e for e in errors):
            errors.append(f"os/core.json or os/admissions.json names '{mid}' but no function.json declares it")

    # 2. governance files agree with manifests --------------------------
    for mid, manifest in list(manifests.items()):
        family = manifest.get("decision_family")
        if family is None:
            continue
        declared = next((f for f in families_doc["families"] if f["id"] == family), None)
        if declared is None or mid not in declared.get("function_order", []):
            reject(mid, paths[mid], [f"{mid}: decision_family '{family}' does not list it in os/families.json function_order (a human curates family membership)"])
            manifests.pop(mid)
            paths.pop(mid)
    for family in families_doc["families"]:
        order = family.get("function_order", [])
        if len(order) != len(set(order)):
            errors.append(f"os/families.json: family '{family['id']}' lists a function twice")
        for mid in order:
            if mid not in manifests and mid not in rejected:
                errors.append(f"os/families.json: family '{family['id']}' lists unknown function '{mid}'")
            elif mid in manifests and manifests[mid].get("decision_family") != family["id"]:
                errors.append(f"os/families.json: '{mid}' is listed under '{family['id']}' but declares '{manifests[mid].get('decision_family')}'")
    kernels = {m for m, man in manifests.items() if man.get("kind") == "decision_kernel"}
    order = core.get("function_order", [])
    if len(order) != len(set(order)):
        errors.append("os/core.json: function_order lists a function twice")
    for mid in kernels - set(order):
        reject(mid, paths[mid], [f"{mid}: a new decision_kernel must be added to os/core.json function_order by a human"])
        manifests.pop(mid)
        paths.pop(mid)
    if errors:
        raise BuildError(errors)

    # 3. examples --------------------------------------------------------
    runners = Runners(root)
    for mid, manifest in list(manifests.items()):
        if not is_runnable(manifest):
            continue
        example = manifest["example"]
        result = runners.call(manifest, paths[mid], example["inputs"])
        problems = []
        if not result["ok"]:
            problems.append(f"{mid}: example failed: {result['error']}")
        else:
            diff = same_json(result["output"], _sanitize(example["expected_outputs"]))
            if diff:
                problems.append(f"{mid}: example output differs from expected_outputs at {diff}")
            if manifest["kind"] == "theorem_function" and result["output"]["status"] != "CONCLUSION_FOLLOWS":
                problems.append(f"{mid}: the published example must satisfy the hypotheses and the conclusion")
        if problems:
            reject(mid, paths[mid], problems)
            if mid not in protected:
                manifests.pop(mid)
                paths.pop(mid)
    if errors:
        raise BuildError(errors)

    # 4. parity fixtures (I2) ----------------------------------------------
    parity_stats: dict[str, int] = {}
    if replay_parity:
        for fixture in sorted((root / "os" / "parity").glob("*.json")):
            document = _read(fixture)
            cases = document.get("cases")
            if cases is None and "published" in document:
                cases = [
                    {"id": k, "inputs": v["inputs"], "result": {"ok": True, "output": v["outputs"]}}
                    for k, v in document["published"].items()
                ]
            for case in cases or []:
                mid = case["id"]
                if mid not in manifests:
                    errors.append(f"{fixture.name}: parity case for unknown function '{mid}'")
                    continue
                expected = case["result"]
                got = runners.call(manifests[mid], paths[mid], case["inputs"])
                if expected["ok"] != got["ok"]:
                    errors.append(f"{fixture.name}: {mid}: ok={got['ok']} but the product returned ok={expected['ok']} for {json.dumps(case['inputs'])[:200]}")
                elif expected["ok"]:
                    diff = same_json(got["output"], expected["output"])
                    if diff:
                        errors.append(f"{fixture.name}: {mid}: {diff}")
                elif expected.get("error") != got.get("error"):
                    errors.append(f"{fixture.name}: {mid}: error {got.get('error')!r} != product {expected.get('error')!r}")
                parity_stats[mid] = parity_stats.get(mid, 0) + 1
    if errors:
        raise BuildError(errors)

    # 5. bundle ------------------------------------------------------------
    catalog = _read(root / "docs" / "data" / "catalog.json")
    catalog_by_path = {r["path"]: r for r in catalog["records"]}
    theorem_ids = sorted(m for m, man in manifests.items() if man["kind"] == "theorem_function")
    ordered_ids = list(core["function_order"]) + theorem_ids
    functions = [_function_entry(manifests[m], paths[m], root, catalog_by_path) for m in ordered_ids]

    bound: dict[str, list[str]] = {}
    for entry in functions:
        for source in entry["lean"]["sources"]:
            bound.setdefault(source["path"], []).append(entry["id"])
    tier_of = {e["id"]: e["tier"] for e in functions}
    reference_records = []
    for record in catalog["records"]:
        fids = bound.get(record["path"], [])
        os_tier = "reference"
        for fid in fids:
            if TIER_RANK[tier_of[fid]] > TIER_RANK[os_tier]:
                os_tier = tier_of[fid]
        if record["status"] == "quarantined":
            kernel_state = "QUARANTINED"
        elif record["status"] == "verified" and record["integrity"] == "gate-passed":
            kernel_state = "KERNEL_CANDIDATE"
        else:
            kernel_state = "NOT_ELIGIBLE"
        reference_records.append({
            "record_id": record["record_id"],
            "title": record["title"],
            "summary": record["summary"],
            "abstract": record["abstract"],
            "path": record["path"],
            "doi": record["doi"],
            "paper_url": record["paper_url"],
            "source_url": record["source_url"],
            "status": record["status"],
            "integrity": record["integrity"],
            "catalog_tier": record["tier"],
            "lean_module": record["lean_module"],
            "theorem_count": record["theorem_count"],
            "lemma_count": record["lemma_count"],
            "external_validation": record["external_validation"],
            "caveat": record["caveat"],
            "source_sha256": record["source_sha256"],
            "record_digest": record["digest"],
            "tags": record["tags"],
            "kernel_state": kernel_state,
            "os_tier": os_tier,
            "function_ids": fids,
        })

    families = []
    for family in families_doc["families"]:
        families.append({**family, "function_ids": list(family["function_order"])})
    runnable = [e for e in functions if e["runnable"]]
    stats = {
        "functions": len(functions),
        "decision_kernels": sum(e["kind"] == "decision_kernel" for e in functions),
        "theorem_functions": sum(e["kind"] == "theorem_function" for e in functions),
        "runnable": len(runnable),
        "runnable_decision_kernels": sum(e["kind"] == "decision_kernel" for e in runnable),
        "admitted": sum(e["tier"] == "admitted" for e in functions),
        "callable": sum(e["tier"] == "callable" for e in functions),
        "reference_functions": sum(e["tier"] == "reference" for e in functions),
        "blocked": sum(e["state"] == "BLOCKED" for e in functions),
        "reconciliation_open": sum(e["reconciliation"] is not None for e in functions),
        "decision_families": len(families),
        "catalog_records": len(reference_records),
        "catalog_verified": sum(r["status"] == "verified" for r in reference_records),
        "catalog_quarantined": sum(r["status"] == "quarantined" for r in reference_records),
        "kernel_candidates": sum(r["kernel_state"] == "KERNEL_CANDIDATE" for r in reference_records),
        "doi_identities": len({r["doi"] for r in reference_records if r["doi"]}),
        "research_intake": len(intake["records"]),
        "rejected_functions": len(rejected),
    }
    source = {
        "repository": catalog["repository"],
        "release": release or catalog["release"],
        "catalog_release": catalog["release"],
        "concept_doi": catalog["concept_doi"],
        "catalog_digest": catalog["catalog_digest"],
        "commit": source_ref or "unrecorded",
    }
    functions_doc = {
        "schema": BUNDLE_SCHEMA,
        "bundle_version": BUNDLE_VERSION,
        "source": source,
        "authority": {
            "compiler_can_promote": False,
            "admission": "human-authored entry in os/admissions.json only",
            "automatic_certification": False,
            "automatic_ledger_mutation": False,
            "credit_issuance": False,
            "empirical_validation_default": "NOT_VALIDATED",
            "production_certification": False,
        },
        "service": core["service"],
        "core": {k: v for k, v in core.items() if k not in ("service", "function_order", "schema_version")},
        "stats": stats,
        "families": families,
        "functions": functions,
        "research_intake": intake,
        "parity": {"fixtures_replayed": replay_parity, "cases_by_function": dict(sorted(parity_stats.items()))},
        "rejected_functions": [
            {"key": key, **value} for key, value in sorted(rejected.items())
        ],
    }
    reference_doc = {
        "schema": BUNDLE_SCHEMA,
        "bundle_version": BUNDLE_VERSION,
        "source": source,
        "honesty_notice": catalog.get("honesty_notice", ""),
        "records": reference_records,
    }

    staging = out_dir.with_name(out_dir.name + ".tmp")
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "runners").mkdir(parents=True)
    (staging / "functions.json").write_text(_dump(functions_doc), encoding="utf-8")
    (staging / "reference.json").write_text(_dump(reference_doc), encoding="utf-8")
    lib = root / "os" / "lib"
    shutil.copyfile(lib / "run.py", staging / "run.py")
    shutil.copyfile(lib / "viridis_fn.py", staging / "runners" / "viridis_fn.py")
    shutil.copyfile(lib / "theorem_runner.py", staging / "runners" / "theorem_runner.py")
    for entry in functions:
        if entry["runner_path"] and entry["runner"] == "runner.py":
            shutil.copyfile(paths[entry["id"]].parent / "runner.py", staging / entry["runner_path"])
    files = sorted(p for p in staging.rglob("*") if p.is_file())
    sums = "".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(staging).as_posix()}\n" for p in files
    )
    (staging / "SHA256SUMS").write_text(sums, encoding="utf-8")
    digest = hashlib.sha256(sums.encode("utf-8")).hexdigest()
    (staging / "DIGEST").write_text(digest + "\n", encoding="utf-8")

    # 6. the written bundle must pass its own self-test in a clean process
    if self_test:
        proc = subprocess.run(
            [sys.executable, "-I", "-B", str(staging / "run.py"), "--self-test"],
            capture_output=True, text=True, timeout=300, cwd=str(staging),
        )
        if proc.returncode != 0:
            shutil.rmtree(staging)
            raise BuildError([f"bundle self-test failed: {proc.stdout.strip()} {proc.stderr.strip()[:2000]}"])

    if out_dir.exists():
        shutil.rmtree(out_dir)
    staging.rename(out_dir)
    return {"digest": digest, "stats": stats, "out_dir": str(out_dir), "parity": parity_stats, "rejected": rejected}


def bundle_digest(bundle_dir: Path) -> str:
    """Recompute a bundle's digest from its files (used by verifiers)."""

    files = sorted(
        p for p in bundle_dir.rglob("*")
        if p.is_file() and p.name not in ("SHA256SUMS", "DIGEST")
    )
    sums = "".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(bundle_dir).as_posix()}\n" for p in files
    )
    return hashlib.sha256(sums.encode("utf-8")).hexdigest()
