"""Build and verify the machine-readable Viridis research catalog."""

from __future__ import annotations

import hashlib
import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .canonical import canonical_digest
from .coverage_provenance import validate_provenance, equal as provenance_equal
from .model import ResearchRecord
from .publications import load_publication_joins
from .methods_digests import load_methods_digest_joins, validate_methods_digests, require_disjoint_publications


SCHEMA = "https://jdhart81.github.io/viridis-canon/schemas/research-catalog-v1.json"
DEFAULT_CAVEAT = (
    "Lean checks conditional mathematics. This record is not, by itself, "
    "empirical validation, regulatory approval, or proof of a real-world magnitude."
)
_DECL_RE = re.compile(
    r"^\s*(?:private\s+|protected\s+)?(theorem|lemma|def)\s+([A-Za-z0-9_'.]+)",
    re.MULTILINE,
)
_IMPORT_RE = re.compile(r"^\s*import\s+(.+?)\s*$", re.MULTILINE)
_NAMESPACE_RE = re.compile(r"^\s*namespace\s+([A-Za-z0-9_'.]+)\s*$", re.MULTILINE)
_COMMENT_RE = re.compile(r"/-!?\s*(.*?)\s*-/", re.DOTALL)
_MODULE_COMMENT_RE = re.compile(r"/-!\s*(.*?)\s*-/", re.DOTALL)
_ABSTRACT_LIMIT = 1_600
_QUARANTINE_STATUSES = frozenset({"UNSOUND", "UNSOUND_ENVIRONMENT"})
_UNCERTIFIED_NOTICE = (
    "UNCERTIFIED — no hash-bound Viridis Comparator certificate covers this deposit's claims. "
    "Lean sources may compile but have not been independently certified. "
    "Results are conditional on the stated model assumptions."
)


def _publication_index_consumers():
    """Reuse the repository's coverage consumers; never execute Lean or issue proof evidence."""
    gates = Path(__file__).resolve().parents[1] / "00_lab_infrastructure" / "gates"
    if str(gates) not in sys.path:
        sys.path.insert(0, str(gates))
    claims = importlib.import_module("claim_binding")
    publication = importlib.import_module("publication_gate")
    if any(Path(module.__file__).resolve().parent != gates for module in (claims, publication)):
        raise ValueError("coverage consumer came from a different checkout")
    return claims, publication


def _load_coverage_ledger(root: Path, config: dict[str, Any], ledger_path: Path | None):
    value = ledger_path or config.get("coverage_ledger")
    if not value:
        return None, "", "MISSING_CORPUS_LEDGER"
    try:
        path = Path(value)
        if not path.is_absolute():
            path = root / path
        content = path.read_bytes()
        ledger = json.loads(content)
        if not isinstance(ledger, dict):
            raise ValueError("ledger must be an object")
        return ledger, hashlib.sha256(content).hexdigest(), ""
    except (OSError, TypeError, ValueError):
        return None, "", "UNREADABLE_OR_MALFORMED_CORPUS_LEDGER"


def _coverage_for_record(
    root: Path, path: Path, curated: dict[str, Any], config: dict[str, Any],
    ledger: dict[str, Any] | None, ledger_sha256: str, ledger_error: str,
    *, enforce: bool, doi: str,
) -> dict[str, Any]:
    """Label exact source bytes from the SSOT and existing gates, never from a manifest."""
    result = {
        "mode": "ENFORCING" if enforce else "REPORT_ONLY", "status": "HOLD",
        "label": _UNCERTIFIED_NOTICE, "canon_eligible": False,
        "proposed_canon_eligible": False, "proposed_status": "working",
        "ledger_sha256": ledger_sha256, "reasons": [],
    }
    if ledger is None:
        result["reasons"].append(ledger_error)
        return result
    try:
        claims, publication = _publication_index_consumers()
        canonical_root = claims.tree_root(ledger)
        entities = claims.ledger_entities(ledger)
        entity_id = curated.get("coverage_entity_id")
        if entity_id:
            matches = [entry for entry in entities if entry.get("id") == entity_id]
        else:
            prefix = Path(config.get("coverage_source_prefix", ""))
            relative = prefix / path.relative_to(root)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("invalid canonical source prefix")
            matches = [entry for entry in entities if entry.get("path") == relative.as_posix()]
        if len(matches) != 1:
            result["reasons"].append("MISSING_OR_AMBIGUOUS_LEDGER_ENTITY")
            return result
        entity = matches[0]
        result["entity_id"] = entity["id"]
        vacuous = claims._static_vacuity({}, entity)
        if entity.get("status") in _QUARANTINE_STATUSES or vacuous:
            result.update(proposed_status="quarantined", quarantine=True)
            result["reasons"].append("QUARANTINED_OR_VACUOUS_LEDGER_ENTITY")
            return result
        if entity.get("status") != "CERTIFIED":
            result["reasons"].append("LEDGER_ENTITY_NOT_CERTIFIED")
            return result
        canonical = (canonical_root / entity["path"]).resolve(strict=True)
        if not canonical.is_relative_to(canonical_root):
            raise ValueError("ledger entity is outside the certification tree")
        current_sha = _sha256_bytes(path.read_bytes())
        if canonical.is_file() and (
            _sha256_bytes(canonical.read_bytes()) != current_sha
            or entity.get("sha256") != current_sha
        ):
            result["reasons"].append("INDEX_SOURCE_HASH_MISMATCH")
            return result
        inspection = claims.inspect_entity_certificate(entity, ledger)
        if inspection.get("valid") is not True or inspection.get("candidate_sha256") != current_sha:
            result["reasons"].append("CERTIFIED_CANDIDATE_HASH_MISMATCH")
            return result
        artifact = canonical.parent if canonical.is_file() else canonical
        gate = publication.evaluate_publication(artifact, ledger, entity_id=entity["id"], enforce=enforce)
        if gate.get("status") != "PASS" or gate.get("exact_publication_binding") is not True:
            result["reasons"].append("PUBLICATION_BINDING_OR_CLAIM_GATE_HOLD")
            return result
        claim_gate = gate.get("claim_gate", {})
        bound = claim_gate.get("claims")
        if claim_gate.get("status") != "PASS" or not isinstance(bound, list) or not bound or any(
            claim.get("status") != "PASS" or claim.get("evidence_class") == "CERTIFIED_TRIVIAL"
            for claim in bound
        ):
            result["reasons"].append("MISSING_OR_TRIVIAL_BOUND_CLAIMS")
            return result
        if doi and gate.get("doi") != doi:
            result["reasons"].append("PUBLIC_DOI_NOT_BOUND_TO_THIS_ARTIFACT")
            return result
        result.update(status="PASS", label="CERTIFIED", proposed_status="verified",
                      proposed_canon_eligible=True, canon_eligible=enforce,
                      certificate_sha256=inspection.get("sha256"),
                      candidate_sha256=current_sha, exact_publication_binding=True,
                      bound_claims=[{key: claim.get(key) for key in
                          ("english_claim", "lean_theorem", "nonvacuity_obligation")}
                          for claim in bound])
    except Exception:
        # A failed consumer, missing evidence, timeout or malformed entity can
        # never fall back to spine membership, clean text or a copied verdict.
        result["reasons"].append("COVERAGE_CONSUMER_HOLD")
    return result


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _manifest_paths(root: Path, manifest_name: str) -> set[str]:
    if not manifest_name:
        return set()
    manifest = root / manifest_name
    if not manifest.exists():
        return set()
    paths: set[str] = set()
    for raw in manifest.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            paths.add(Path(line).as_posix())
    return paths


def _humanize(stem: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", stem)
    return spaced.replace("_", " ").replace("-", " ").strip()


def _record_id(path: str) -> str:
    raw = re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-")
    return raw.removesuffix("-lean")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _clean_comment_paragraph(value: str) -> str:
    lines = []
    for raw in value.splitlines():
        line = raw.strip()
        lowered = line.casefold()
        if lowered.startswith(
            (
                "copyright (c)",
                "released under ",
                "authors:",
                "co-authored-by:",
                "toolchain:",
                "lean:",
                "lean version:",
                "mathlib:",
                "mathlib version:",
            )
        ):
            continue
        line = re.sub(r"^[=*#─━\-\s]+", "", line)
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")
    cleaned = re.sub(r"\s+", " ", " ".join(lines)).strip()
    return cleaned.replace("**", "").replace("`", "")


def _extract_abstract(text: str, fallback: str) -> str:
    scope = text[:80_000]
    leading = _COMMENT_RE.search(scope)
    leading_text = _clean_comment_paragraph(leading.group(1)) if leading else ""
    if leading and leading.start() < 500 and len(leading_text) >= 300:
        abstract = leading_text
    else:
        candidates: list[tuple[int, int, str]] = []
        module_blocks = _MODULE_COMMENT_RE.findall(scope)
        blocks = module_blocks or _COMMENT_RE.findall(scope)
        for index, block in enumerate(blocks[:18]):
            cleaned = _clean_comment_paragraph(block)
            lowered = cleaned.casefold()
            if len(cleaned) < 90:
                continue
            if (
                "copyright (c)" in lowered
                and len(cleaned) < 500
                and "theorem" not in lowered
            ):
                continue
            score = min(len(cleaned), 900)
            if "this module" in lowered:
                score += 600
            if "formaliz" in lowered:
                score += 400
            if "context" in lowered or "main result" in lowered or "headline" in lowered:
                score += 180
            if "theorem" in lowered:
                score += 100
            candidates.append((score, -index, cleaned))
        if not candidates:
            return fallback
        abstract = max(candidates, key=lambda item: (item[0], item[1], item[2]))[2]
    if len(abstract) <= _ABSTRACT_LIMIT:
        return abstract
    shortened = abstract[:_ABSTRACT_LIMIT].rsplit(" ", 1)[0].rstrip(" ,;:")
    return shortened + "…"


def _repository_file_url(repository: str, path: str) -> str:
    if not repository.startswith("https://"):
        return ""
    encoded = quote(Path(path).as_posix(), safe="/")
    return f"{repository.rstrip('/')}/blob/main/{encoded}"


def _expand_globs(root: Path, patterns: Iterable[str], excluded: set[str]) -> list[Path]:
    seen: set[str] = set()
    found: list[Path] = []
    for pattern in patterns:
        for path in root.glob(pattern):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel in excluded or rel in seen:
                continue
            seen.add(rel)
            found.append(path)
    return sorted(found, key=lambda value: value.relative_to(root).as_posix())


def _discover_record(
    root: Path,
    path: Path,
    spine_paths: set[str],
    config: dict[str, Any],
    coverage_ledger: dict[str, Any] | None,
    ledger_sha256: str,
    ledger_error: str,
    enforce_coverage: bool,
) -> ResearchRecord:
    rel = path.relative_to(root).as_posix()
    content = path.read_bytes()
    text = content.decode("utf-8", errors="replace")
    decode_replacements = text.count("\ufffd")
    curated = config.get("curation", {}).get(rel, {})
    doi = str(curated.get("doi") or config.get("doi_by_path", {}).get(rel, ""))
    is_lean = path.suffix.casefold() == ".lean"
    declarations = _DECL_RE.findall(text)
    theorem_count = sum(kind == "theorem" for kind, _ in declarations)
    lemma_count = sum(kind == "lemma" for kind, _ in declarations)
    definition_count = sum(kind == "def" for kind, _ in declarations)
    namespaces = _NAMESPACE_RE.findall(text)

    quarantined = rel in set(config.get("quarantined", []))
    coverage = _coverage_for_record(
        root, path, curated, config, coverage_ledger, ledger_sha256, ledger_error,
        enforce=enforce_coverage, doi=doi,
    )
    quarantined = quarantined or coverage.get("quarantine") is True
    if quarantined:
        status = "quarantined"
        integrity = "quarantined"
        coverage.update(canon_eligible=False, proposed_canon_eligible=False,
                        proposed_status="quarantined", status="HOLD", label=_UNCERTIFIED_NOTICE)
    elif coverage["canon_eligible"] is True:
        status = "verified"
        integrity = "gate-passed"
    else:
        status = "working"
        integrity = "not-canon-admitted"

    default_tier = config.get(
        "default_tier",
        "spine" if is_lean and rel in spine_paths else "working-corpus",
    )
    historical_tier = curated.get("tier", default_tier)
    tier = historical_tier
    if tier == "spine" and coverage["canon_eligible"] is not True:
        tier = "working-corpus"
    title = curated.get("title") or _humanize(path.stem)
    if curated.get("summary"):
        summary = curated["summary"]
    elif is_lean:
        summary = (
            f"Lean research module with "
            f"{theorem_count + lemma_count} theorem and lemma declarations."
        )
    else:
        summary = "Research artifact indexed with a deterministic source fingerprint."
    abstract = (
        curated.get("abstract")
        or curated.get("summary")
        or _extract_abstract(text, summary)
    )
    repository = str(config.get("repository") or "")
    source_url = _repository_file_url(repository, rel)
    paper_target = str(curated.get("paper_target") or "")
    if doi:
        paper_url = f"https://doi.org/{quote(doi, safe='./')}"
    elif paper_target:
        paper_url = _repository_file_url(repository, paper_target)
    else:
        paper_url = source_url
    type_tag = "lean4" if is_lean else path.suffix.casefold().lstrip(".") or "artifact"
    tags = tuple(
        sorted(
            {
                *curated.get("tags", []),
                status,
                tier,
                type_tag,
            }
        )
    )

    return ResearchRecord(
        record_id=curated.get("id") or _record_id(rel),
        title=title,
        summary=summary,
        path=rel,
        status=status,
        tier=tier,
        visibility=curated.get("visibility", config.get("default_visibility", "public")),
        source_sha256=_sha256_bytes(content),
        abstract=abstract,
        source_url=source_url,
        paper_url=paper_url,
        theorem_count=theorem_count,
        lemma_count=lemma_count,
        definition_count=definition_count,
        line_count=len(text.splitlines()),
        imports=tuple(sorted(_IMPORT_RE.findall(text))),
        tags=tags,
        doi=doi,
        lean_module=(
            curated.get("lean_module")
            or (namespaces[0] if namespaces else path.stem)
            if is_lean
            else ""
        ),
        integrity=integrity,
        external_validation=curated.get("external_validation", "not-recorded"),
        caveat=(
            _UNCERTIFIED_NOTICE + "\n\nHistorical scope note: " + curated.get("caveat", DEFAULT_CAVEAT)
            if coverage["status"] != "PASS" else curated.get("caveat", DEFAULT_CAVEAT)
        ),
        metadata={
            "paper_target": curated.get("paper_target", ""),
            "aristotle_id": curated.get("aristotle_id", ""),
            "source_decode_replacements": decode_replacements,
            "artifact_type": type_tag,
            "verification_coverage": coverage,
            "historical_tier": historical_tier,
            "historical_spine_manifest_member": rel in spine_paths,
        },
    )


def build_catalog(
    root: Path,
    config_path: Path | None = None,
    *,
    include_private: bool = False,
    ledger_path: Path | None = None,
    enforce_coverage: bool = False,
    source_prefix: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic catalog document from a Viridis canon checkout."""

    root = root.resolve()
    config_path = config_path or root / "catalog" / "config.json"
    config = _load_json(config_path)
    if source_prefix is not None:
        config["coverage_source_prefix"] = source_prefix
    spine_paths = _manifest_paths(root, config.get("manifest", "SPINE_MANIFEST.txt"))
    excluded = set(config.get("exclude", []))
    ledger, ledger_sha256, ledger_error = _load_coverage_ledger(root, config, ledger_path)
    paths = _expand_globs(root, config.get("include", ["*.lean"]), excluded)
    records = [
        _discover_record(root, path, spine_paths, config, ledger, ledger_sha256, ledger_error, enforce_coverage)
        for path in paths
    ]
    selected_records = [
        record
        for record in records
        if include_private or record.visibility == "public"
    ]
    selected_records.sort(key=lambda record: (record.tier, record.title.casefold(), record.path))

    stats = {
        "records": len(selected_records),
        "verified": sum(record.status == "verified" for record in selected_records),
        "working": sum(record.status == "working" for record in selected_records),
        "spine": sum(record.tier == "spine" for record in selected_records),
        "flagships": sum(record.tier == "flagship" for record in selected_records),
        "working_corpus": sum(record.tier == "working-corpus" for record in selected_records),
        "quarantined": sum(record.status == "quarantined" for record in selected_records),
        "theorems_and_lemmas": sum(
            record.theorem_count + record.lemma_count for record in selected_records
        ),
    }
    publications = load_publication_joins(root, config)
    methods_digests = load_methods_digest_joins(root, config)
    require_disjoint_publications(publications, methods_digests)
    payload = {
        "schema": SCHEMA,
        "publication_scope": "workspace" if include_private else "public",
        "release": config["release"],
        "concept_doi": config["concept_doi"],
        "repository": config["repository"],
        "honesty_notice": config.get("honesty_notice", DEFAULT_CAVEAT),
        "human_publish_gate": True,
        "stats": stats,
        "records": [record.to_dict() for record in selected_records],
        "publications": publications,
        "methods_digests": methods_digests,
    }
    # Historical assessment headers require an actual supplied ledger build.
    # A missing-ledger source-only build remains HOLD and never invents provenance.
    if "coverage_provenance" in config and ledger is not None:
        payload["coverage_provenance"] = validate_provenance(payload, config["coverage_provenance"])
    return {**payload, "catalog_digest": canonical_digest(payload)}


def validate_catalog(
    document: dict[str, Any], *, root: Path | None = None,
    config_path: Path | None = None, ledger_path: Path | None = None,
    source_prefix: str | None = None,
) -> list[str]:
    """Validate fingerprints and reconsume evidence for every protected label.

    Digest-consistent JSON is not proof evidence. A verified/admitted record
    requires an explicit current source root and live coverage ledger; copied
    consumer results, historical spine membership and clean text do not suffice.
    """

    errors: list[str] = []
    digest = document.get("catalog_digest")
    payload = {key: value for key, value in document.items() if key != "catalog_digest"}
    if digest != canonical_digest(payload):
        errors.append("catalog_digest does not match the canonical payload")
    try:
        validate_methods_digests(document.get("methods_digests", []))
        require_disjoint_publications(document.get("publications", []), document.get("methods_digests", []))
    except (ValueError, TypeError, KeyError) as exc:
        errors.append("Methods Digest pointer projection rejected: " + str(exc))

    records = document.get("records")
    if not isinstance(records, list):
        return [*errors, "records must be a list"]
    ids: set[str] = set()
    paths: set[str] = set()
    config: dict[str, Any] = {}
    ledger = None
    ledger_sha, ledger_error = "", "MISSING_CORPUS_LEDGER"
    if root is not None:
        root = root.resolve()
        try:
            config = _load_json(config_path or root / "catalog" / "config.json")
            if source_prefix is not None:
                config["coverage_source_prefix"] = source_prefix
            ledger, ledger_sha, ledger_error = _load_coverage_ledger(root, config, ledger_path)
        except (OSError, TypeError, ValueError):
            ledger_error = "UNREADABLE_OR_MALFORMED_CATALOG_CONFIG"
    if "coverage_provenance" in document:
        try:
            validate_provenance(document, document["coverage_provenance"])
            if root is not None and not provenance_equal(document["coverage_provenance"], config.get("coverage_provenance")):
                raise ValueError("checked coverage provenance differs from closed configuration")
        except (ValueError, TypeError, KeyError) as exc:
            errors.append("coverage provenance rejected: " + str(exc))
    for index, record in enumerate(records):
        prefix = f"records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        record_id = record.get("record_id")
        path = record.get("path")
        if record_id in ids:
            errors.append(f"{prefix} duplicates record_id {record_id!r}")
        if path in paths:
            errors.append(f"{prefix} duplicates path {path!r}")
        ids.add(record_id)
        paths.add(path)
        record_digest = record.get("digest")
        record_payload = {key: value for key, value in record.items() if key != "digest"}
        if record_digest != canonical_digest(record_payload):
            errors.append(f"{prefix} digest mismatch")
        if (
            document.get("publication_scope") == "public"
            and record.get("visibility") != "public"
        ):
            errors.append(f"{prefix} leaks a non-public record")
        metadata = record.get("metadata")
        coverage = metadata.get("verification_coverage", {}) if isinstance(metadata, dict) else {}
        tags = record.get("tags", [])
        protected = (record.get("status") == "verified" or record.get("tier") == "spine"
                     or record.get("integrity") == "gate-passed"
                     or isinstance(tags, list) and any(tag in {"verified", "spine"} for tag in tags)
                     or isinstance(coverage, dict) and coverage.get("canon_eligible") is True)
        if protected:
            if root is None or ledger is None:
                errors.append(f"{prefix} protected eligibility lacks current source root and corpus ledger")
                continue
            try:
                source = (root / str(path)).resolve(strict=True)
                if not source.is_relative_to(root) or not source.is_file():
                    raise ValueError("source is outside the catalog root or not a file")
                if _sha256_bytes(source.read_bytes()) != record.get("source_sha256"):
                    raise ValueError("catalog source hash differs from current bytes")
                current = _coverage_for_record(
                    root, source, config.get("curation", {}).get(path, {}), config,
                    ledger, ledger_sha, ledger_error, enforce=True, doi=record.get("doi", ""),
                )
                if current.get("canon_eligible") is not True:
                    raise ValueError("current publication coverage HOLD: " + "; ".join(current["reasons"]))
                if (record.get("status") != "verified" or record.get("integrity") != "gate-passed"
                        or not isinstance(coverage, dict) or coverage.get("mode") != "ENFORCING"
                        or coverage.get("ledger_sha256") != ledger_sha
                        or coverage.get("entity_id") != current.get("entity_id")
                        or coverage.get("certificate_sha256") != current.get("certificate_sha256")
                        or coverage.get("candidate_sha256") != current.get("candidate_sha256")
                        or coverage.get("exact_publication_binding") is not True):
                    raise ValueError("recorded eligibility is inconsistent with current evidence")
            except Exception as exc:
                errors.append(f"{prefix} protected eligibility rejected: {type(exc).__name__}: {exc}")
    stats = document.get("stats")
    if isinstance(stats, dict):
        for key, field, value in (("verified", "status", "verified"), ("spine", "tier", "spine"),
                                  ("working", "status", "working"), ("quarantined", "status", "quarantined")):
            if stats.get(key) != sum(isinstance(record, dict) and record.get(field) == value for record in records):
                errors.append(f"stats.{key} disagrees with current record labels")
    return errors


def write_catalog(
    root: Path,
    output: Path,
    config_path: Path | None = None,
    *,
    include_private: bool = False,
    ledger_path: Path | None = None,
    enforce_coverage: bool = False,
    source_prefix: str | None = None,
) -> dict[str, Any]:
    """Build, validate, and write a catalog document."""

    document = build_catalog(
        root,
        config_path=config_path,
        include_private=include_private,
        ledger_path=ledger_path,
        enforce_coverage=enforce_coverage,
        source_prefix=source_prefix,
    )
    errors = validate_catalog(document, root=root, config_path=config_path,
                              ledger_path=ledger_path, source_prefix=source_prefix)
    if errors:
        raise ValueError("; ".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8")
    return document


def validate_catalog_sources(
    document: dict[str, Any], root: Path, config_path: Path | None = None,
) -> list[str]:
    """Check the complete current source/curation projection without private evidence.

    CI may lack the canonical certificate store. That cannot admit protected
    labels: validate_catalog separately reinspects those or holds. Restrictive
    SSOT quarantine labels and their diagnostic hashes need not be reconstructed
    from an absent private ledger to check the public source inventory.
    """
    expected = build_catalog(root, config_path=config_path,
                             include_private=document.get("publication_scope") == "workspace")
    actual = document.get("records", [])
    if not isinstance(actual, list) or any(not isinstance(record, dict) for record in actual):
        return ["records must be a list of objects"]
    by_path = {record.get("path"): record for record in actual}
    current = {record["path"]: record for record in expected["records"]}
    if set(by_path) != set(current) or len(by_path) != len(actual):
        return ["catalog source inventory differs from current configured sources"]
    errors = []
    try:
        config = _load_json(config_path or root / "catalog" / "config.json")
        if "coverage_provenance" in config or "coverage_provenance" in document:
            if not provenance_equal(document.get("coverage_provenance"), config.get("coverage_provenance")):
                raise ValueError("checked coverage provenance differs from closed configuration")
            validate_provenance(document, document.get("coverage_provenance"))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append("coverage provenance rejected: " + str(exc))
    if document.get("publications", []) != expected["publications"]:
        errors.append("explicit publication pointers differ from current configured source")
    if document.get("methods_digests", []) != expected["methods_digests"]:
        errors.append("Methods Digest pointers differ from current configured source")
    for key in ("schema", "release", "concept_doi", "repository", "honesty_notice", "human_publish_gate", "publications", "methods_digests"):
        if key in document and document[key] != expected[key]:
            errors.append(f"current catalog configuration field differs: {key}")
    evidence_fields = {"digest", "status", "tier", "integrity", "tags", "caveat", "metadata"}
    for path, source in current.items():
        record = by_path[path]
        for key in set(source) - evidence_fields:
            if record.get(key) != source[key]:
                errors.append(f"{path}: current source/curation field differs: {key}")
        source_metadata = source.get("metadata", {})
        metadata = record.get("metadata", {})
        if not isinstance(metadata, dict) or {k: v for k, v in metadata.items() if k != "verification_coverage"} != {
            k: v for k, v in source_metadata.items() if k != "verification_coverage"
        }:
            errors.append(f"{path}: current source/curation metadata differs")
        if record.get("status") not in {"working", "quarantined", "verified"}:
            errors.append(f"{path}: unsupported public status")
    return errors
