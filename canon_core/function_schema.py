"""Validator for Viridis OS function manifests (``function.json``, schema v1).

The JSON Schema in ``docs/schemas/function-v1.json`` documents the shape; this
module enforces it with the standard library only and adds the semantic checks
a schema cannot express:

* tier rules (``admitted`` requires an entry in ``os/admissions.json``; the
  validator never changes a tier),
* Lean source hashes and theorem names against the repository,
* DOI cross-checks against the catalog configuration,
* examples validated against the generated input schema and the hypotheses,
* honest labels (``empirical_validation`` stays ``NOT_VALIDATED`` unless the
  repository records a validation file).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_URL = "https://jdhart81.github.io/viridis-canon/schemas/function-v1.json"
MANIFEST_NAME = "function.json"
TIERS = ("reference", "callable", "admitted")
KINDS = ("decision_kernel", "theorem_function")
STATES = ("READY", "BLOCKED")
RECONCILIATION_CODES = ("CANON_CLASSIFICATION", "CANON_RECORD")
INPUT_TYPES = ("number", "integer", "boolean", "string", "array", "object")
REQUIRED_KEYS = (
    "schema_version", "id", "kind", "name", "version", "summary", "decision_family",
    "tier", "state", "reconciliation", "blocked", "doi", "lean", "inputs", "outputs",
    "hypotheses", "example", "scope", "boundary", "empirical_validation", "runner",
)
OPTIONAL_KEYS = ("$schema", "line", "derived", "conclusion", "provenance")
INPUT_KEYWORDS = (
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "enum", "items",
    "minItems", "maxItems", "properties", "additionalProperties",
)
_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_DOI_RE = re.compile(r"^10\.[0-9]{4,9}/\S+$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_DECL_TEMPLATE = r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*(?:theorem|lemma|def|abbrev|instance)\s+(?:[A-Za-z0-9_'.]+\.)?{name}(?=[\s:({{\[]|$)"
_SKIP_DIRS = {".git", ".lake", "build", "node_modules", "os-bundle", "__pycache__"}


def load_runtime(root: Path):
    """Import ``os/lib/viridis_fn.py`` (the runner runtime shipped in bundles)."""

    path = root / "os" / "lib" / "viridis_fn.py"
    name = "viridis_fn"
    if name in sys.modules and getattr(sys.modules[name], "__file__", None) == str(path):
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_manifests(root: Path) -> list[Path]:
    """Every ``function.json`` in the repository, in path order."""

    found: list[Path] = []
    for path in root.rglob(MANIFEST_NAME):
        rel = path.relative_to(root)
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        found.append(path)
    return sorted(found, key=lambda p: p.relative_to(root).as_posix())


def input_schema(manifest: dict[str, Any]) -> dict[str, Any]:
    """The closed JSON schema the product validates inputs against."""

    properties: dict[str, Any] = {}
    required: list[str] = []
    for item in manifest.get("inputs", []):
        prop = {"type": item["type"]}
        for keyword in INPUT_KEYWORDS:
            if keyword in item:
                prop[keyword] = item[keyword]
        properties[item["name"]] = dict(sorted(prop.items()))
        if item.get("required"):
            required.append(item["name"])
    return {
        "additionalProperties": False,
        "properties": dict(sorted(properties.items())),
        "required": required,
        "type": "object",
    }


def units_map(manifest: dict[str, Any]) -> dict[str, str]:
    return {o["name"]: o["unit"] for o in manifest.get("outputs", []) if o.get("unit")}


def service_state(manifest: dict[str, Any]) -> str:
    """Public service state, derived only from repository-recorded fields."""

    if manifest.get("state") == "BLOCKED":
        return "BLOCKED_PRODUCT_WARRANT_REQUIRED"
    reconciliation = manifest.get("reconciliation") or {}
    if reconciliation.get("code") == "CANON_RECORD":
        return "PREVIEW_ONLY_CANON_RECORD_RECONCILIATION_REQUIRED"
    if reconciliation.get("code") == "CANON_CLASSIFICATION":
        return "PREVIEW_ONLY_CANON_CLASSIFICATION_RECONCILIATION_REQUIRED"
    if manifest.get("tier") == "admitted":
        return "READY_UNSIGNED_PREVIEW"
    if manifest.get("tier") == "callable":
        return "CALLABLE_UNSIGNED_PREVIEW_NOT_ADMITTED"
    return "REFERENCE_ONLY_NOT_CALLABLE"


def is_runnable(manifest: dict[str, Any]) -> bool:
    return (
        manifest.get("state") == "READY"
        and manifest.get("tier") in ("callable", "admitted")
        and bool(manifest.get("runner"))
        and manifest.get("example") is not None
    )


@dataclass
class RepoContext:
    """Everything a manifest is cross-checked against."""

    root: Path
    families: set[str] = field(default_factory=set)
    admitted: dict[str, dict[str, Any]] = field(default_factory=dict)
    doi_by_path: dict[str, str] = field(default_factory=dict)
    catalog_by_path: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, root: Path) -> "RepoContext":
        root = root.resolve()
        families_doc = _read_json(root / "os" / "families.json", {"families": []})
        ledger = _read_json(root / "os" / "admissions.json", {"admitted": []})
        config = _read_json(root / "catalog" / "config.json", {})
        catalog = _read_json(root / "docs" / "data" / "catalog.json", {"records": []})
        doi_by_path = dict(config.get("doi_by_path", {}))
        for path, curated in config.get("curation", {}).items():
            if curated.get("doi"):
                doi_by_path[path] = curated["doi"]
        return cls(
            root=root,
            families={f["id"] for f in families_doc.get("families", [])},
            admitted={entry["id"]: entry for entry in ledger.get("admitted", [])},
            doi_by_path=doi_by_path,
            catalog_by_path={r["path"]: r for r in catalog.get("records", [])},
        )


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _declares(text: str, name: str) -> bool:
    pattern = _DECL_TEMPLATE.format(name=re.escape(name))
    return re.search(pattern, text, re.MULTILINE) is not None


def _type_ok(value: Any, kind: str) -> bool:
    return {
        "str": isinstance(value, str),
        "bool": isinstance(value, bool),
        "list": isinstance(value, list),
        "dict": isinstance(value, dict),
    }[kind]


def validate_manifest(
    manifest: Any,
    manifest_path: Path,
    context: RepoContext,
) -> list[str]:
    """Return every problem with ``manifest``; an empty list means valid."""

    errors: list[str] = []
    rel = manifest_path.relative_to(context.root).as_posix() if manifest_path.is_absolute() else str(manifest_path)

    def err(message: str) -> None:
        errors.append(f"{rel}: {message}")

    if not isinstance(manifest, dict):
        return [f"{rel}: manifest must be a JSON object"]

    # --- shape -----------------------------------------------------------
    for key in REQUIRED_KEYS:
        if key not in manifest:
            err(f"missing required key '{key}'")
    for key in manifest:
        if key not in REQUIRED_KEYS and key not in OPTIONAL_KEYS:
            err(f"unknown key '{key}'")
    if errors:
        return errors
    if manifest.get("$schema", SCHEMA_URL) != SCHEMA_URL:
        err("$schema must be the function-v1 schema URL")
    if manifest["schema_version"] != 1:
        err("schema_version must be 1")
    mid = manifest["id"]
    if not isinstance(mid, str) or not _ID_RE.match(mid):
        err("id must be kebab-case")
    if manifest["kind"] not in KINDS:
        err(f"kind must be one of {KINDS}")
    for key in ("name", "summary", "scope", "boundary"):
        if not isinstance(manifest[key], str) or len(manifest[key].strip()) < 3:
            err(f"{key} must be a non-empty string")
    if isinstance(manifest["summary"], str) and len(manifest["summary"]) < 20:
        err("summary must be a plain-language sentence")
    if isinstance(manifest["boundary"], str) and len(manifest["boundary"]) < 20:
        err("boundary must state what the result does not establish")
    if not isinstance(manifest["version"], str) or not _VERSION_RE.match(manifest["version"]):
        err("version must be semantic (x.y.z)")
    tier = manifest["tier"]
    if tier not in TIERS:
        err(f"tier must be one of {TIERS}")
    if manifest["state"] not in STATES:
        err(f"state must be one of {STATES}")
    if not isinstance(manifest["doi"], str) or not _DOI_RE.match(manifest["doi"]):
        err("doi must be a DOI (10.xxxx/...)")
    family = manifest["decision_family"]
    if family is not None and family not in context.families:
        err(f"decision_family '{family}' is not declared in os/families.json")

    reconciliation = manifest["reconciliation"]
    if reconciliation is not None:
        if not isinstance(reconciliation, dict) or reconciliation.get("code") not in RECONCILIATION_CODES:
            err(f"reconciliation.code must be one of {RECONCILIATION_CODES}")
        elif not isinstance(reconciliation.get("note"), str) or len(reconciliation["note"]) < 10:
            err("reconciliation.note must explain what is unreconciled")
    blocked = manifest["blocked"]
    if blocked is not None and (not isinstance(blocked, dict) or blocked.get("verdict") != "BLOCKED"):
        err("blocked.verdict must be 'BLOCKED'")

    # --- honest labels (I4) ----------------------------------------------
    validation = manifest["empirical_validation"]
    if validation != "NOT_VALIDATED":
        if not isinstance(validation, dict) or not isinstance(validation.get("record"), str):
            err("empirical_validation must be 'NOT_VALIDATED' or {status, record}")
        elif not (context.root / validation["record"]).is_file():
            err("empirical_validation.record must point at a validation record in the repository")

    # --- Lean binding ----------------------------------------------------
    lean = manifest["lean"]
    if not isinstance(lean, dict):
        err("lean must be an object")
        lean = {}
    sources = lean.get("sources", [])
    theorems = lean.get("theorems", [])
    if not isinstance(lean.get("module"), str) or not lean.get("module"):
        err("lean.module is required")
    if not isinstance(theorems, list) or not theorems or not all(isinstance(t, str) and t for t in theorems):
        err("lean.theorems must list at least one theorem name")
        theorems = []
    if not isinstance(sources, list):
        err("lean.sources must be a list")
        sources = []
    missing_source_allowed = (reconciliation or {}).get("code") == "CANON_RECORD"
    if not sources and not missing_source_allowed:
        err("lean.sources is empty; only a CANON_RECORD reconciliation may omit the Lean source")
    source_text = ""
    for source in sources:
        path = source.get("path") if isinstance(source, dict) else None
        digest = source.get("sha256") if isinstance(source, dict) else None
        if not isinstance(path, str) or not isinstance(digest, str) or not _SHA_RE.match(digest):
            err("each lean.sources entry needs path and sha256")
            continue
        file = context.root / path
        if not file.is_file():
            err(f"Lean source {path} does not exist")
            continue
        actual = sha256_file(file)
        if actual != digest:
            err(f"Lean source {path} sha256 {actual[:12]} does not match the manifest {digest[:12]} — re-review the function")
        source_text += file.read_text(encoding="utf-8", errors="replace") + "\n"
        record = context.catalog_by_path.get(path)
        if record is not None and record.get("source_sha256") != actual:
            err(f"catalog record for {path} is stale (rebuild docs/data/catalog.json)")
        expected_doi = context.doi_by_path.get(path) or (record or {}).get("doi")
        if expected_doi and expected_doi != manifest["doi"]:
            err(f"doi {manifest['doi']} disagrees with the catalog DOI {expected_doi} for {path}")
    if sources:
        for name in theorems:
            if not _declares(source_text, name):
                err(f"theorem '{name}' is not declared in the listed Lean sources")

    # --- inputs / outputs ------------------------------------------------
    inputs = manifest["inputs"]
    names: list[str] = []
    if not isinstance(inputs, list):
        err("inputs must be a list")
        inputs = []
    for item in inputs:
        if not isinstance(item, dict):
            err("each input must be an object")
            continue
        name = item.get("name")
        if not isinstance(name, str) or not _NAME_RE.match(name):
            err(f"input name {name!r} must be snake_case")
            continue
        names.append(name)
        if item.get("type") not in INPUT_TYPES:
            err(f"input '{name}' type must be one of {INPUT_TYPES}")
        for key in ("unit", "help"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                err(f"input '{name}' needs a {key}")
        if not isinstance(item.get("required"), bool):
            err(f"input '{name}' needs required: true|false")
        for key in item:
            if key not in ("name", "type", "unit", "help", "required", *INPUT_KEYWORDS):
                err(f"input '{name}' has unknown key '{key}'")
    if len(set(names)) != len(names):
        err("input names must be unique")
    outputs = manifest["outputs"]
    out_names = [o.get("name") for o in outputs if isinstance(o, dict)] if isinstance(outputs, list) else []
    if not isinstance(outputs, list) or len(out_names) != len(outputs):
        err("outputs must be a list of {name, unit?}")
    if len(set(out_names)) != len(out_names):
        err("output names must be unique")

    derived = manifest.get("derived", [])
    conclusion = manifest.get("conclusion")
    if manifest["kind"] == "theorem_function" and manifest["tier"] != "reference":
        if not isinstance(conclusion, dict) or not all(k in conclusion for k in ("statement", "check", "lean_theorem")):
            err("a callable theorem_function needs conclusion {statement, check, lean_theorem}")
        elif conclusion["lean_theorem"] not in theorems:
            err("conclusion.lean_theorem must be one of lean.theorems")
        if manifest["runner"] != "theorem":
            err("a callable theorem_function uses the generic runner ('theorem')")
    elif manifest["kind"] == "theorem_function" and isinstance(conclusion, dict) and conclusion.get("lean_theorem") not in theorems:
        err("conclusion.lean_theorem must be one of lean.theorems")
    elif derived or conclusion:
        err("derived/conclusion are only for theorem_function manifests")

    # --- hypotheses ------------------------------------------------------
    runtime = load_runtime(context.root)
    hypotheses = manifest["hypotheses"]
    if not isinstance(hypotheses, list):
        err("hypotheses must be a list")
        hypotheses = []
    known = set(names)
    for d in derived or []:
        try:
            runtime.parse_check(d["expression"])
            unknown = runtime.condition_names(d["expression"]) - known
            if unknown:
                err(f"derived '{d['name']}' references unknown names {sorted(unknown)}")
        except (KeyError, TypeError, runtime.CheckSyntaxError) as error:
            err(f"derived value is invalid: {error}")
        if isinstance(d, dict) and "name" in d:
            known.add(d["name"])
    hyp_ids = []
    for hyp in hypotheses:
        if not isinstance(hyp, dict) or not all(isinstance(hyp.get(k), str) for k in ("id", "statement", "check")):
            err("each hypothesis needs id, statement and check")
            continue
        hyp_ids.append(hyp["id"])
        try:
            unknown = runtime.condition_names(hyp["check"]) - set(names)
            if unknown:
                err(f"hypothesis '{hyp['id']}' references unknown inputs {sorted(unknown)}")
        except runtime.CheckSyntaxError as error:
            err(f"hypothesis '{hyp['id']}': {error}")
    if len(set(hyp_ids)) != len(hyp_ids):
        err("hypothesis ids must be unique")
    if isinstance(conclusion, dict) and isinstance(conclusion.get("check"), str):
        try:
            unknown = runtime.condition_names(conclusion["check"]) - known
            if unknown:
                err(f"conclusion references unknown names {sorted(unknown)}")
        except runtime.CheckSyntaxError as error:
            err(f"conclusion: {error}")

    # --- tiers and authority (I3) ---------------------------------------
    runner = manifest["runner"]
    example = manifest["example"]
    if manifest["state"] == "BLOCKED":
        if blocked is None:
            err("a BLOCKED function must say why in 'blocked'")
        if tier != "reference":
            err("a BLOCKED function can only be tier 'reference'")
        if runner is not None:
            err("a BLOCKED function must not publish a runner")
    elif blocked is not None:
        err("'blocked' is only allowed when state is BLOCKED")
    if tier in ("callable", "admitted"):
        if runner is None:
            err(f"tier '{tier}' requires a runner")
        if example is None:
            err(f"tier '{tier}' requires an example")
    if tier == "admitted":
        entry = context.admitted.get(mid)
        if entry is None or entry.get("tier") != "admitted":
            err("tier 'admitted' requires a human-authored entry in os/admissions.json")
        if reconciliation is not None:
            err("an admitted function cannot carry an open reconciliation")
        if not sources:
            err("an admitted function must bind a Lean source")
    if runner is not None:
        if runner == "theorem":
            if manifest["kind"] != "theorem_function":
                err("runner 'theorem' is only for theorem_function manifests")
        elif runner != "runner.py":
            err("runner must be 'runner.py', 'theorem' or null")
        elif not (manifest_path.parent / "runner.py").is_file():
            err("runner.py is missing beside the manifest")

    # --- example (validated, and satisfies the hypotheses) --------------
    if example is not None:
        if not isinstance(example, dict) or not isinstance(example.get("inputs"), dict) or not isinstance(example.get("expected_outputs"), dict):
            err("example must be {inputs, expected_outputs}")
        else:
            try:
                runtime.validate_schema(example["inputs"], input_schema(manifest))
            except runtime.InputError as error:
                err(f"example inputs fail the input schema: {error}")
            for hyp in hypotheses:
                if isinstance(hyp, dict) and isinstance(hyp.get("check"), str):
                    try:
                        if not runtime.check(hyp["check"], example["inputs"]):
                            if manifest["kind"] == "decision_kernel":
                                err(f"example does not satisfy hypothesis '{hyp['id']}'")
                    except runtime.CheckSyntaxError:
                        pass
            declared = [o["name"] for o in outputs if isinstance(o, dict) and not o.get("input_echo")]
            if manifest["kind"] == "decision_kernel" and list(example["expected_outputs"].keys()) != declared:
                err("example.expected_outputs keys must equal the declared outputs, in order")
    return errors


def validate_admissions_ledger(context: RepoContext, manifests: dict[str, dict[str, Any]]) -> list[str]:
    errors = []
    for mid, entry in context.admitted.items():
        for key in ("id", "tier", "evidence", "human_gate"):
            if not entry.get(key):
                errors.append(f"os/admissions.json: entry '{mid}' is missing '{key}'")
        if mid not in manifests:
            errors.append(f"os/admissions.json: '{mid}' has no function.json")
        elif manifests[mid].get("state") == "BLOCKED":
            errors.append(f"os/admissions.json: '{mid}' is BLOCKED and cannot be admitted")
    return errors
