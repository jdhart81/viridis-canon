"""Build and verify the machine-readable Viridis research catalog."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

from .canonical import canonical_digest
from .model import ResearchRecord


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
_BANNED_RE = re.compile(r"\b(?:sorry|admit|sorryAx)\b")
_COMMENT_RE = re.compile(r"/-!?\s*(.*?)\s*-/", re.DOTALL)
_MODULE_COMMENT_RE = re.compile(r"/-!\s*(.*?)\s*-/", re.DOTALL)
_ABSTRACT_LIMIT = 1_600


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
    if quarantined:
        status = "quarantined"
        integrity = "quarantined"
    elif is_lean and rel in spine_paths and not _BANNED_RE.search(text):
        status = "verified"
        integrity = "gate-passed"
    else:
        status = "working"
        integrity = "not-canon-admitted"

    default_tier = config.get(
        "default_tier",
        "spine" if is_lean and rel in spine_paths else "working-corpus",
    )
    tier = curated.get("tier", default_tier)
    title = curated.get("title") or _humanize(path.stem)
    if curated.get("summary"):
        summary = curated["summary"]
    elif is_lean:
        summary = (
            f"Machine-checked Lean research module with "
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
        caveat=curated.get("caveat", DEFAULT_CAVEAT),
        metadata={
            "paper_target": curated.get("paper_target", ""),
            "aristotle_id": curated.get("aristotle_id", ""),
            "source_decode_replacements": decode_replacements,
            "artifact_type": type_tag,
        },
    )


def build_catalog(
    root: Path,
    config_path: Path | None = None,
    *,
    include_private: bool = False,
) -> dict[str, Any]:
    """Build a deterministic catalog document from a Viridis canon checkout."""

    root = root.resolve()
    config_path = config_path or root / "catalog" / "config.json"
    config = _load_json(config_path)
    spine_paths = _manifest_paths(root, config.get("manifest", "SPINE_MANIFEST.txt"))
    excluded = set(config.get("exclude", []))
    paths = _expand_globs(root, config.get("include", ["*.lean"]), excluded)
    records = [
        _discover_record(root, path, spine_paths, config)
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
    }
    return {**payload, "catalog_digest": canonical_digest(payload)}


def validate_catalog(document: dict[str, Any]) -> list[str]:
    """Return validation errors for a generated catalog document."""

    errors: list[str] = []
    digest = document.get("catalog_digest")
    payload = {key: value for key, value in document.items() if key != "catalog_digest"}
    if digest != canonical_digest(payload):
        errors.append("catalog_digest does not match the canonical payload")

    records = document.get("records")
    if not isinstance(records, list):
        return [*errors, "records must be a list"]
    ids: set[str] = set()
    paths: set[str] = set()
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
    return errors


def write_catalog(
    root: Path,
    output: Path,
    config_path: Path | None = None,
    *,
    include_private: bool = False,
) -> dict[str, Any]:
    """Build, validate, and write a catalog document."""

    document = build_catalog(
        root,
        config_path=config_path,
        include_private=include_private,
    )
    errors = validate_catalog(document)
    if errors:
        raise ValueError("; ".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    output.write_text(rendered, encoding="utf-8")
    return document
