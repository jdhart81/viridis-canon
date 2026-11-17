"""Auto-intake: proven engine results enter the canon as decision kernels, then go live.

The science engine (jdhart81/viridis-engine) writes runs to jdhart81/viridis-research,
whose ``index/certified.json`` is the certification authority. This module is the
deterministic gate between that index and the Viridis OS in this repository. The
engine drafts a kernel package for one candidate per night (see
docs/auto_intake/DRAFTING.md); everything here only checks, records and switches.

Invariants (tests: tests/test_os_auto_intake.py)

AI-1 Eligibility. Only a statement with status PROVEN in the certified index, a
     proof, ``closed_by_single_tactic`` false and (when the run record is available)
     ``trivial`` false can enter, and only when its class is A (new service) or B
     (strengthens one). TESTED claims never become kernels; SEALED_UNPROVEN and
     every other status never enter. The Intelligence Bound is a conjecture: any
     manifest text that names it must call it a conjecture.
AI-2 Idempotent. A statement already decided in os/research_statements.json, or
     already backing a function manifest, is skipped; applying twice writes once.
AI-3 Package shape. function.json (decision_kernel, inputs with units, the sealed
     statement and the proof copied in by hash, the run's DOI, boundary text),
     runner.py, a conformance test file, and machine-checked statement conformance
     on the example, the cases and the negative controls.
AI-4 Merge only on green. ``verify`` returns every problem; the engine step merges
     only when verify, validate-functions, the OS build and the canon tests pass.
AI-5 (viridisos) refreshes from the canon after merge: tools/refresh_from_canon.py there.
AI-6 Go-live is one switch. ``go_live`` in os/auto_intake.json (owner decision
     2026-11-17) mirrors os/core.json authority.automatic_kernel_activation. With it
     off nothing is written to os/core.json or os/admissions.json. ``rollback`` takes
     a kernel out of service in one step and keeps it out.
AI-7 Every decision is a ledger entry (statement, run, reason); ``plan`` reports
     every skip with its reason, reproducibly from the two repositories.
"""

from __future__ import annotations

import datetime as _dt
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

POLICY_PATH = "os/auto_intake.json"
LEDGER_PATH = "os/research_statements.json"
CORE_PATH = "os/core.json"
ADMISSIONS_PATH = "os/admissions.json"
FAMILIES_PATH = "os/families.json"
INTAKE_PATH = "os/research_intake.json"
LEDGER_STANDARD = "VOS-RESEARCH-STATEMENT-LEDGER-1"
CLASSES_ENTER = ("A", "B")
CLASSES_DECLINE = ("C", "RECERT")
FORBIDDEN = re.compile(r"product[- ]ready|production[- ]ready|ready for production|ready to sell", re.I)
IB_NAME = re.compile(r"intelligence[- ]bound", re.I)
IB_CLAIM = re.compile(r"intelligence[- ]bound[^.]{0,80}\b(is|was|has been)\s+(proven|proved|derived|verified)", re.I)


class IntakeError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


# --------------------------------------------------------------------------- io

def _read(root: Path, rel: str) -> Any:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _write(root: Path, rel: str, value: Any) -> None:
    (root / rel).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_policy(root: Path) -> dict:
    return _read(root, POLICY_PATH)


def load_ledger(root: Path) -> dict:
    path = root / LEDGER_PATH
    if not path.is_file():
        return {"schema_version": 1, "standard": LEDGER_STANDARD, "entries": []}
    return _read(root, LEDGER_PATH)


def ledger_by_statement(root: Path) -> dict[str, dict]:
    return {e["statement"]: e for e in load_ledger(root)["entries"]}


def load_index(path: Path) -> dict:
    index = json.loads(Path(path).read_text(encoding="utf-8"))
    if index.get("schema") != "viridis-certified-index-v1":
        raise IntakeError([f"{path}: not a viridis-certified-index-v1 file"])
    return index


def _today() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _manifests(root: Path) -> dict[str, tuple[dict, Path]]:
    from .function_schema import discover_manifests

    out = {}
    for path in discover_manifests(root):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        out[manifest.get("id")] = (manifest, path)
    return out


def backed_statements(root: Path, include_drafts: bool = True) -> dict[str, str]:
    """research statement id -> function id, for every manifest that names one.

    With ``include_drafts`` false, an auto-intake package that is drafted but not yet in the
    ledger does not count: the statement is still a candidate until ``apply`` records it.
    """
    ledger = ledger_by_statement(root)
    out = {}
    for fid, (manifest, _) in _manifests(root).items():
        prov = manifest.get("provenance") or {}
        stmt = prov.get("research_statement")
        if not stmt:
            continue
        if not include_drafts and prov.get("authored_by") == "auto-intake" and stmt not in ledger:
            continue
        out[stmt] = fid
    return out


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


# -------------------------------------------------------------------------- plan

def eligibility(index: dict, statement: str, research_root: Path | None = None) -> list[str]:
    """AI-1: why ``statement`` may not enter (empty = eligible)."""
    rec = (index.get("statements") or {}).get(statement)
    if rec is None:
        tested = {f"{c.get('project')}.{c.get('claim_id')}" for c in index.get("tested_claims", [])}
        if statement in tested:
            return ["TESTED result: a re-executed observational computation never becomes a predictive kernel"]
        return [f"{statement} is not in the certified index"]
    problems = []
    if rec.get("status") != "PROVEN" or not rec.get("proof"):
        problems.append(f"status is {rec.get('status')}, not PROVEN")
    if rec.get("closed_by_single_tactic"):
        problems.append("trivial: closed by a single tactic")
    if research_root is not None and rec.get("proof"):
        cert_path = Path(research_root) / rec["proof"]["run_dir"] / "certification.json"
        if not cert_path.is_file():
            problems.append(f"{cert_path} is missing")
        else:
            labels = json.loads(cert_path.read_text(encoding="utf-8")).get("labels", {})
            mine = [v for v in labels.values() if v.get("statement_id") == statement]
            if not mine or mine[0].get("label") != "PROVEN":
                problems.append("the run's certification.json does not label it PROVEN")
            elif mine[0].get("trivial") is not False:
                problems.append("the run's certification.json marks it trivial")
            elif mine[0].get("statement_sha256") != rec.get("sha256"):
                problems.append("certification.json and the index disagree on the statement hash")
    return problems


def plan(root: Path, index: dict, research_root: Path | None = None) -> dict:
    """Every PROVEN statement and TESTED claim with a decision and a reason (AI-1, AI-2, AI-7)."""
    policy = load_policy(root)
    ledger = ledger_by_statement(root)
    backed = backed_statements(root, include_drafts=False)
    rows = []
    for statement in sorted(index.get("statements", {})):
        rec = index["statements"][statement]
        proof = rec.get("proof") or {}
        row = {"statement": statement, "run_dir": proof.get("run_dir"), "doi": proof.get("doi")}
        problems = eligibility(index, statement, research_root)
        if statement in ledger:
            e = ledger[statement]
            row.update(decision="SKIP", reason=f"already decided: class {e['class']}, {e['status']}"
                       + (f" ({e['function_id']})" if e.get("function_id") else ""))
        elif statement in backed:
            row.update(decision="SKIP", reason=f"already backs canon function {backed[statement]}")
        elif problems:
            row.update(decision="SKIP", reason="; ".join(problems))
        elif policy.get("require_run_doi", True) and not proof.get("doi"):
            row.update(decision="WAIT", reason="proven; waiting for the run's Zenodo DOI from the weekly release")
        else:
            row.update(decision="CANDIDATE", reason="proven, non-trivial, undecided: draft and classify")
        rows.append(row)
    for claim in index.get("tested_claims", []):
        rows.append({"statement": f"{claim.get('project')}.{claim.get('claim_id')}@{claim.get('run_dir')}",
                     "run_dir": claim.get("run_dir"), "doi": claim.get("doi"), "decision": "SKIP",
                     "reason": "TESTED result: evidence only, never a predictive kernel"})
    return {
        "enabled": bool(policy.get("enabled")),
        "go_live": bool(policy.get("go_live")),
        "max_new_kernels_per_run": policy.get("max_new_kernels_per_run", 1),
        "candidates": [r["statement"] for r in rows if r["decision"] == "CANDIDATE"],
        "rows": rows,
    }


# ------------------------------------------------------------------------ verify

def _text_problems(value: Any, where: str) -> list[str]:
    problems = []
    if isinstance(value, str):
        if FORBIDDEN.search(value):
            problems.append(f"{where}: never call a kernel product-ready ({value[:60]!r})")
        if IB_NAME.search(value) and (IB_CLAIM.search(value) or "conjecture" not in value.lower()):
            problems.append(f"{where}: the Intelligence Bound must be called a conjecture, never proven")
    elif isinstance(value, dict):
        for k, v in value.items():
            problems += _text_problems(v, f"{where}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            problems += _text_problems(v, f"{where}[{i}]")
    return problems


def _load_runner(package: Path, root: Path):
    from .function_schema import load_runtime

    sys.modules.setdefault("viridis_fn", load_runtime(root))
    spec = importlib.util.spec_from_file_location(f"auto_runner_{package.name}", package / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run


def conformance_test_path(function_id: str) -> str:
    return f"tests/test_os_auto_{function_id.replace('-', '_')}.py"


def verify(root: Path, index: dict, package: Path, research_root: Path | None = None) -> list[str]:
    """AI-1 and AI-3 for one drafted package. An empty list means it may enter."""
    from .function_schema import RepoContext, validate_manifest

    root = Path(root).resolve()
    package = Path(package).resolve()
    errors: list[str] = []
    for name in ("function.json", "runner.py", "intake.json"):
        if not (package / name).is_file():
            errors.append(f"{package.name}/{name} is missing")
    if errors:
        return errors
    manifest = json.loads((package / "function.json").read_text(encoding="utf-8"))
    intake = json.loads((package / "intake.json").read_text(encoding="utf-8"))
    policy = load_policy(root)
    package_root = (root / policy.get("package_root", "research")).resolve()
    if package.parent != package_root or package.name != manifest.get("id"):
        errors.append(f"the package must be {policy.get('package_root', 'research')}/<function id>/")
    statement = intake.get("statement")
    fid = manifest.get("id")

    # classification (AI-1)
    if intake.get("class") not in CLASSES_ENTER:
        errors.append(f"class {intake.get('class')!r}: only A or B enter the canon")
    for key in ("buyer_decision", "proven", "assumed", "family", "service"):
        if not isinstance(intake.get(key), str) or len(intake[key].strip()) < 3:
            errors.append(f"intake.{key} is required")
    if intake.get("class") == "B" and not intake.get("strengthens"):
        errors.append("a class B kernel must name the service it strengthens")
    errors += eligibility(index, statement, research_root)
    rec = (index.get("statements") or {}).get(statement) or {}
    proof = rec.get("proof") or {}

    # idempotency (AI-2)
    prior = ledger_by_statement(root).get(statement)
    if prior is not None:
        errors.append(f"{statement} is already decided ({prior['status']})")
    backed = backed_statements(root)
    if backed.get(statement) not in (None, fid):
        errors.append(f"{statement} already backs {backed[statement]}")

    # manifest shape (AI-3)
    context = RepoContext.load(root)
    errors += validate_manifest(manifest, package / "function.json", context)
    expect = {"kind": "decision_kernel", "runner": "runner.py", "tier": "callable", "state": "READY",
              "reconciliation": None, "blocked": None, "empirical_validation": "NOT_VALIDATED"}
    for key, value in expect.items():
        if manifest.get(key) != value:
            errors.append(f"function.json {key} must be {value!r} on entry")
    if manifest.get("decision_family") != intake.get("family"):
        errors.append("function.json decision_family must equal intake.family")
    if intake.get("function_id") != fid:
        errors.append("intake.function_id must equal function.json id")
    for item in manifest.get("inputs", []):
        if not str(item.get("unit", "")).strip():
            errors.append(f"input {item.get('name')} has no unit")
    if not re.search(r"\b(not|never)\b", str(manifest.get("boundary", "")), re.I):
        errors.append("boundary must say what the kernel does not establish")
    if proof.get("doi"):
        if manifest.get("doi") != proof["doi"]:
            errors.append(f"doi {manifest.get('doi')} is not the run DOI {proof['doi']}")
    elif policy.get("require_run_doi", True):
        errors.append("the run has no Zenodo DOI yet: entry waits for the weekly release")

    # Lean binding to the sealed statement and the checked proof
    lean = manifest.get("lean") or {}
    constant = rec.get("constant", "")
    if constant and lean.get("module") != constant.rsplit(".", 1)[0]:
        errors.append(f"lean.module must be {constant.rsplit('.', 1)[0]}")
    digests = {s.get("sha256") for s in lean.get("sources", []) if isinstance(s, dict)}
    if rec.get("sha256") not in digests:
        errors.append("lean.sources must include the sealed statement file with its index sha256")
    if proof.get("candidate_sha256") not in digests:
        errors.append("lean.sources must include the checked proof file with its candidate sha256")

    # provenance and statement conformance
    prov = manifest.get("provenance") or {}
    want = {"authored_by": "auto-intake", "research_statement": statement,
            "research_run": proof.get("run_dir"), "statement_sha256": rec.get("sha256"),
            "candidate_sha256": proof.get("candidate_sha256"),
            "research_repository": policy.get("research_repository")}
    for key, value in want.items():
        if prov.get(key) != value:
            errors.append(f"provenance.{key} must be {value!r}")
    if not str(prov.get("statement_text", "")).strip():
        errors.append("provenance.statement_text must restate the sealed statement")
    parts = prov.get("statement_conformance") or []
    cases = prov.get("conformance_cases") or []
    negatives = prov.get("negative_controls") or []
    if not parts or not all(isinstance(p, dict) and p.get("part") and p.get("statement") and p.get("check") for p in parts):
        errors.append("provenance.statement_conformance must give part, statement and check for every part")
    if len(cases) < 3:
        errors.append("provenance.conformance_cases needs at least three input sets")
    if not negatives:
        errors.append("provenance.negative_controls needs at least one hypothesis-violating input")
    if not (root / conformance_test_path(fid or "")).is_file():
        errors.append(f"{conformance_test_path(fid or '')} is missing")
    errors += _text_problems({k: manifest.get(k) for k in ("name", "summary", "scope", "boundary", "provenance")}, "function.json")
    errors += _text_problems(intake, "intake.json")
    if errors:
        return errors

    return conformance_problems(root, package, manifest)


def conformance_problems(root: Path, package: Path, manifest: dict | None = None) -> list[str]:
    """Run the example, every conformance case and every negative control (AI-3).

    On every input that satisfies the hypotheses, every statement part's check must hold on
    the inputs plus the runner's outputs; every negative control must be refused with InputError.
    """
    from .function_schema import load_runtime

    root = Path(root).resolve()
    package = Path(package).resolve()
    if manifest is None:
        manifest = json.loads((package / "function.json").read_text(encoding="utf-8"))
    runtime = load_runtime(root)
    prov = manifest.get("provenance") or {}
    parts = prov.get("statement_conformance") or []
    errors: list[str] = []
    run = _load_runner(package, root)
    example = manifest["example"]
    try:
        got = run(dict(example["inputs"]))
        if got != example["expected_outputs"]:
            errors.append("the runner does not reproduce example.expected_outputs")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"the example raises {type(exc).__name__}: {exc}")
    for i, case in enumerate([example["inputs"], *(prov.get("conformance_cases") or [])]):
        if not all(runtime.check(h["check"], case) for h in manifest["hypotheses"]):
            errors.append(f"case {i} does not satisfy the hypotheses")
            continue
        try:
            out = run(dict(case))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"case {i} raises {type(exc).__name__}: {exc}")
            continue
        env = {**case, **out}
        for part in parts:
            if not runtime.check(part["check"], env):
                errors.append(f"case {i} breaks statement part {part['part']}: {part['check']}")
    for i, case in enumerate(prov.get("negative_controls") or []):
        try:
            run(dict(case))
            errors.append(f"negative control {i} was not refused")
        except runtime.InputError:
            pass
        except Exception as exc:  # noqa: BLE001
            errors.append(f"negative control {i} raised {type(exc).__name__}, not InputError")
    return errors


# ------------------------------------------------------------------- write paths

def _entry(statement: str, rec: dict, intake: dict, status: str, now: str, function_id=None) -> dict:
    proof = rec.get("proof") or {}
    return {
        "statement": statement,
        "class": intake["class"],
        "status": status,
        "function_id": function_id,
        "strengthens": intake.get("strengthens"),
        "service": intake.get("service"),
        "buyer_decision": intake.get("buyer_decision"),
        "proven": intake.get("proven"),
        "assumed": intake.get("assumed"),
        "reason": intake.get("reason", ""),
        "run_dir": proof.get("run_dir"),
        "doi": proof.get("doi"),
        "statement_sha256": rec.get("sha256"),
        "decided_at": now,
        "decided_by": "auto-intake",
        "live_at": None,
        "rolled_back_at": None,
        "rollback": (f"python3 -m canon_core auto-intake rollback --function {function_id}" if function_id else None),
    }


def _save_entry(root: Path, entry: dict) -> None:
    ledger = load_ledger(root)
    ledger["entries"] = [e for e in ledger["entries"] if e["statement"] != entry["statement"]] + [entry]
    ledger["entries"].sort(key=lambda e: e["statement"])
    _write(root, LEDGER_PATH, ledger)


def decide(root: Path, index: dict, statement: str, klass: str, reason: str, now: str | None = None) -> dict:
    """Record a statement that does not enter (class C or RECERT) so it is never re-screened (AI-2, AI-7)."""
    if klass not in CLASSES_DECLINE:
        raise IntakeError([f"decide records C or RECERT only, not {klass!r}"])
    if not reason or len(reason.strip()) < 10:
        raise IntakeError(["a declined statement needs a reason"])
    if statement in ledger_by_statement(root):
        return ledger_by_statement(root)[statement]
    rec = (index.get("statements") or {}).get(statement)
    if rec is None:
        raise IntakeError([f"{statement} is not in the certified index"])
    entry = _entry(statement, rec, {"class": klass, "reason": reason}, "DECLINED", now or _today())
    _save_entry(root, entry)
    return entry


README_COUNT = re.compile(r"(\| Decision functions tied to Lean theorems \| \*\*)(\d+)(\*\* \|)")


def _regenerate(root: Path) -> None:
    """Rebuild every file generated from the manifests, as a human PR would (CI checks each)."""
    for tool in ("tools/build_certificates_index.py", "tools/build_formalization_yaml.py"):
        subprocess.run([sys.executable, tool], cwd=root, check=True, capture_output=True, text=True)
    count = len(re.findall(r"^  - id:", (root / "formalization.yaml").read_text(encoding="utf-8"), re.M))
    readme = root / "README.md"
    if readme.is_file():
        readme.write_text(README_COUNT.sub(lambda m: f"{m.group(1)}{count}{m.group(3)}",
                                           readme.read_text(encoding="utf-8")), encoding="utf-8")
    if (root / "tools" / "build_overview.py").is_file():
        subprocess.run([sys.executable, "tools/build_overview.py"], cwd=root, check=True, capture_output=True, text=True)


def apply(root: Path, index: dict, package: Path, research_root: Path | None = None,
          now: str | None = None, regenerate: bool = True) -> dict:
    """Enter one verified package: family, research intake, ledger, generated indexes."""
    root = Path(root).resolve()
    package = Path(package).resolve()
    intake = json.loads((package / "intake.json").read_text(encoding="utf-8"))
    statement = intake.get("statement")
    prior = ledger_by_statement(root).get(statement)
    if prior is not None and prior.get("function_id") == intake.get("function_id"):
        return prior  # AI-2: already entered, nothing to write
    errors = verify(root, index, package, research_root)
    if errors:
        raise IntakeError(errors)
    if not load_policy(root).get("enabled"):
        raise IntakeError(["auto-intake is switched off in os/auto_intake.json"])
    manifest = json.loads((package / "function.json").read_text(encoding="utf-8"))
    fid = manifest["id"]
    rec = index["statements"][statement]
    families = _read(root, FAMILIES_PATH)
    for family in families["families"]:
        if family["id"] == intake["family"] and fid not in family["function_order"]:
            family["function_order"].append(fid)
    _write(root, FAMILIES_PATH, families)
    research = _read(root, INTAKE_PATH)
    if not any(r.get("abbreviation") == statement for r in research["records"]):
        research["records"].append({
            "abbreviation": statement,
            "doi": manifest["doi"],
            "product_line": intake["service"],
            "run_id": rec["proof"]["run_dir"],
            "spine_admitted": False,
            "state": "CERTIFICATION_READY",
            "successor_version_candidate": "unassigned",
        })
    _write(root, INTAKE_PATH, research)
    entry = _entry(statement, rec, intake, "ENTERED", now or _today(), fid)
    _save_entry(root, entry)
    if regenerate:
        _regenerate(root)
    return entry


def _set_tier(path: Path, tier: str) -> None:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["tier"] = tier
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def go_live(root: Path, function_id: str, now: str | None = None, regenerate: bool = True) -> dict:
    """AI-6: an ENTERED kernel joins the operating order and the admission ledger."""
    root = Path(root).resolve()
    policy = load_policy(root)
    if not policy.get("go_live"):
        raise IntakeError(["go_live is off in os/auto_intake.json: nothing written"])
    core = _read(root, CORE_PATH)
    if core["authority"].get("automatic_kernel_activation") is not True:
        raise IntakeError(["os/core.json authority.automatic_kernel_activation does not match the go_live switch"])
    entries = [e for e in load_ledger(root)["entries"] if e.get("function_id") == function_id]
    if not entries:
        raise IntakeError([f"{function_id} was not entered by auto-intake"])
    entry = entries[0]
    if entry["status"] == "LIVE":
        return entry
    if entry["status"] != "ENTERED":
        raise IntakeError([f"{function_id} is {entry['status']}; only ENTERED kernels go live"])
    manifests = _manifests(root)
    manifest, path = manifests[function_id]
    if function_id not in core["function_order"]:
        core["function_order"].append(function_id)
    _write(root, CORE_PATH, core)
    admissions = _read(root, ADMISSIONS_PATH)
    if not any(a["id"] == function_id for a in admissions["admitted"]):
        admissions["admitted"].append({
            "id": function_id,
            "tier": "admitted",
            "warrant_verdict": "ADMITTED",
            "evidence": (f"Research statement {entry['statement']} PROVEN in jdhart81/viridis-research "
                         f"{entry['run_dir']} (statement sha256 {entry['statement_sha256'][:12]}, DOI {entry['doi']}); "
                         "auto-intake gates, conformance tests, canon tests and the OS build passed."),
            "human_gate": ("Standing owner decision 2026-11-17 (os/auto_intake.json go_live): new kernels go live "
                           "automatically after their checks pass. Roll back: python3 -m canon_core auto-intake "
                           f"rollback --function {function_id}"),
        })
    _write(root, ADMISSIONS_PATH, admissions)
    _set_tier(path, "admitted")
    entry["status"] = "LIVE"
    entry["live_at"] = now or _today()
    _save_entry(root, entry)
    if regenerate:
        _regenerate(root)
    return entry


def rollback(root: Path, function_id: str, now: str | None = None, regenerate: bool = True) -> dict:
    """AI-6: take a kernel out of service in one step; it stays callable and is never re-admitted."""
    root = Path(root).resolve()
    entries = [e for e in load_ledger(root)["entries"] if e.get("function_id") == function_id]
    if not entries:
        raise IntakeError([f"{function_id} was not entered by auto-intake"])
    entry = entries[0]
    if entry["status"] == "ROLLED_BACK":
        return entry
    core = _read(root, CORE_PATH)
    core["function_order"] = [f for f in core["function_order"] if f != function_id]
    _write(root, CORE_PATH, core)
    admissions = _read(root, ADMISSIONS_PATH)
    admissions["admitted"] = [a for a in admissions["admitted"] if a["id"] != function_id]
    _write(root, ADMISSIONS_PATH, admissions)
    manifests = _manifests(root)
    if function_id in manifests:
        _set_tier(manifests[function_id][1], "callable")
    entry["status"] = "ROLLED_BACK"
    entry["rolled_back_at"] = now or _today()
    _save_entry(root, entry)
    if regenerate:
        _regenerate(root)
    return entry


def audit_admissions(root: Path, base_admissions: dict, base_core: dict) -> list[str]:
    """CI guard for auto-intake branches: every admission or live-list change is one auto-intake made.

    An id added to os/admissions.json or os/core.json must be a LIVE ledger entry of an
    auto-intake manifest while go_live is on; an id removed must be ROLLED_BACK. Any other
    change to either file is a human act and belongs in a separate PR.
    """
    root = Path(root).resolve()
    policy = load_policy(root)
    ledger = {e["function_id"]: e for e in load_ledger(root)["entries"] if e.get("function_id")}
    manifests = _manifests(root)
    now_adm = {a["id"]: a for a in _read(root, ADMISSIONS_PATH)["admitted"]}
    was_adm = {a["id"]: a for a in base_admissions["admitted"]}
    now_core = list(_read(root, CORE_PATH)["function_order"])
    was_core = list(base_core["function_order"])
    errors = []
    for fid in sorted(set(now_adm) - set(was_adm)) + [f for f in now_core if f not in was_core]:
        entry = ledger.get(fid)
        prov = (manifests.get(fid, ({}, None))[0].get("provenance") or {})
        if not policy.get("go_live"):
            errors.append(f"{fid}: go_live is off, so auto-intake may not make it live")
        if entry is None or entry["status"] != "LIVE" or prov.get("authored_by") != "auto-intake":
            errors.append(f"{fid}: added to the live list but not a LIVE auto-intake kernel")
    for fid in sorted(set(was_adm) - set(now_adm)) + [f for f in was_core if f not in now_core]:
        entry = ledger.get(fid)
        if entry is None or entry["status"] != "ROLLED_BACK":
            errors.append(f"{fid}: removed from the live list but not an auto-intake rollback")
    for fid in set(now_adm) & set(was_adm):
        if now_adm[fid] != was_adm[fid]:
            errors.append(f"{fid}: an existing admission entry changed; that is a human act")
    if [f for f in was_core if f in now_core] != [f for f in now_core if f in was_core]:
        errors.append("os/core.json: the existing operating order changed; that is a human act")
    return sorted(set(errors))


def entered_not_live(root: Path) -> set[str]:
    return {e["function_id"] for e in load_ledger(root)["entries"]
            if e.get("function_id") and e["status"] in ("ENTERED", "ROLLED_BACK")}


# --------------------------------------------------------------------------- cli

def add_parser(sub) -> None:
    p = sub.add_parser("auto-intake", help="enter proven engine results as kernels (docs/auto_intake/README.md)")
    p.add_argument("action", choices=("plan", "verify", "apply", "decide", "go-live", "rollback", "note", "audit"))
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--index", type=Path, help="viridis-research index/certified.json")
    p.add_argument("--research-root", type=Path, help="viridis-research checkout (cross-checks certification.json)")
    p.add_argument("--package", type=Path, help="series/<ID> directory drafted for one statement")
    p.add_argument("--statement")
    p.add_argument("--class", dest="klass")
    p.add_argument("--reason", default="")
    p.add_argument("--function")
    p.add_argument("--since", default="", help="note: ledger changes at or after this UTC timestamp")
    p.add_argument("--base-ref", default="origin/main", help="audit: the git ref the PR merges into")


def note(root: Path, since: str) -> str:
    """AI-7: the plain-text lines for Justin's kernel-flag email."""
    lines = []
    for e in load_ledger(root)["entries"]:
        stamps = [e.get("decided_at") or "", e.get("live_at") or "", e.get("rolled_back_at") or ""]
        if not any(s and s >= since for s in stamps):
            continue
        if e["status"] == "DECLINED":
            lines.append(f"- {e['statement']} ({e['run_dir']}): not entered, class {e['class']}: {e['reason']}")
            continue
        state = {"ENTERED": "entered the canon (callable)", "LIVE": "entered and LIVE on the decision-service list",
                 "ROLLED_BACK": "rolled back (out of service, still callable)"}[e["status"]]
        lines.append(f"- {e['function_id']} from {e['statement']} ({e['run_dir']}, DOI {e['doi']}): {state}. "
                     f"Class {e['class']}" + (f", strengthens {e['strengthens']}" if e.get("strengthens") else "")
                     + f". Proven: {e['proven']} Assumed: {e['assumed']} Roll back: {e['rollback']}")
    return "\n".join(lines)


def run_cli(args) -> int:
    root = args.root.resolve()
    try:
        if args.action == "note":
            print(note(root, args.since))
            return 0
        if args.action == "audit":
            def at_base(rel):
                out = subprocess.run(["git", "-C", str(root), "show", f"{args.base_ref}:{rel}"],
                                     capture_output=True, text=True, check=True)
                return json.loads(out.stdout)
            errors = audit_admissions(root, at_base(ADMISSIONS_PATH), at_base(CORE_PATH))
            for e in errors:
                print(f"ERROR: {e}")
            if not errors:
                print("auto-intake audit: every live-list change is an auto-intake go-live or rollback")
            return 1 if errors else 0
        if args.action == "rollback":
            print(json.dumps(rollback(root, args.function), indent=2))
            return 0
        if args.action == "go-live":
            print(json.dumps(go_live(root, args.function), indent=2))
            return 0
        index = load_index(args.index)
        if args.action == "plan":
            print(json.dumps(plan(root, index, args.research_root), indent=2))
            return 0
        if args.action == "verify":
            errors = verify(root, index, args.package, args.research_root)
            for e in errors:
                print(f"ERROR: {e}")
            if not errors:
                print(f"auto-intake verify: {args.package} may enter")
            return 1 if errors else 0
        if args.action == "apply":
            print(json.dumps(apply(root, index, args.package, args.research_root), indent=2))
            return 0
        if args.action == "decide":
            print(json.dumps(decide(root, index, args.statement, args.klass, args.reason), indent=2))
            return 0
    except IntakeError as error:
        for e in error.errors:
            print(f"ERROR: {e}")
        return 1
    return 2
