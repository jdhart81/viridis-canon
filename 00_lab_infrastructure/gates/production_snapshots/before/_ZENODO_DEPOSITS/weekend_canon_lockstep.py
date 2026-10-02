#!/usr/bin/env python3
"""Run a dated Zenodo publication wave and its GitHub mirror as one transaction.

Default is a local-only dry run:

  python3 weekend_canon_lockstep.py --date 2026-08-02

Normal publication (Justin must explicitly authorize the irreversible publisher):

  python3 weekend_canon_lockstep.py --date 2026-08-02 --go -- \
    python3 publish_dated_bundles.py --date 2026-08-02 --publish --go

Recovery when DOI files already exist (never republishes to Zenodo):

  python3 weekend_canon_lockstep.py --date 2026-08-02 --go

Invariants:
  * GitHub write access is probed before the publisher can mint a DOI.
  * New multi-file projects enter git under an abbreviation-scoped directory
    with their pinned build files; legacy flat bundles retain their old path.
  * Every available PUBLISHED_DOI.txt is mirrored even if the publisher exits nonzero.
  * Success requires a fresh public clone whose files match the bundles byte-for-byte.
  * A JSON receipt records the DOI/file/commit correspondence.

The script is stdlib-only. It never publishes to Zenodo itself; it runs the exact
publisher argv supplied after ``--``. Publisher scripts must write PUBLISHED_DOI.txt
immediately after each successful Zenodo publish and skip bundles that already have it.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Iterable, Sequence
import urllib.error
import urllib.request


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import release_coherence

REPOSITORY = "jdhart81/viridis-canon"
PUBLIC_REPO_URL = f"https://github.com/{REPOSITORY}.git"
PUBLIC_CATALOG_URL = "https://jdhart81.github.io/viridis-canon/data/catalog.json"
TOKEN_REPO_URL = "https://jdhart81:{token}@github.com/" + REPOSITORY + ".git"
TOKEN_FILE = ROOT / "secrets" / "Github token Viridis LLC.md"
RECEIPT_DIR = HERE / "LOCKSTEP_RECEIPTS"
TOKEN_PATTERN = re.compile(
    r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
)
DOI_PATTERN = re.compile(r"10\.\d{4,9}/zenodo\.\d+")
POST_ARISTOTLE_REVIEW_REQUIRED_AFTER = "2026-07-26"
POST_ARISTOTLE_REVIEW_NAME = "POST_ARISTOTLE_REVIEW.json"
LEGACY_CLAUDE_REVIEW_NAME = "CLAUDE_REVIEW.json"
REVIEW_CHECKS = (
    "claim_separation",
    "stale_language_removed",
    "theorem_scope_matches",
    "references_checked",
    "ai_disclosure_ready",
)
FORMAL_SUMMARY_TARGET_NAMES = frozenset({
    "ARISTOTLE_SUMMARY.MD",
    "COMPARATOR_SUMMARY.MD",
})
# Backward-compatible aliases for historical tooling and bundles. New reviews
# must use the provider-neutral v2 file and schema below.
CLAUDE_REVIEW_REQUIRED_AFTER = POST_ARISTOTLE_REVIEW_REQUIRED_AFTER
CLAUDE_REVIEW_NAME = LEGACY_CLAUDE_REVIEW_NAME
CLAUDE_CHECKS = REVIEW_CHECKS
COAUTHOR_TRAILER = (
    "Co-authored-by: Aristotle (Harmonic) "
    "<aristotle-harmonic@harmonic.fun>"
)


class LockstepError(RuntimeError):
    """A fail-closed lockstep error safe to show to the operator."""


@dataclasses.dataclass(frozen=True)
class Bundle:
    abbreviation: str
    path: Path
    title: str
    payload: tuple[Path, ...]
    payload_targets: tuple[str, ...]
    git_build_root: str | None
    doi: str | None
    paper: Path
    review_path: Path | None
    review_sha256: str | None
    reviewed_at_utc: str | None
    reviewer_system: str | None
    reviewer_model: str | None
    series_route: str | None
    spine_gate: str | None


def payload_pairs(bundle: Bundle) -> tuple[tuple[Path, str], ...]:
    if len(bundle.payload) != len(bundle.payload_targets):
        raise LockstepError(f"{bundle.path}: source/target payload length mismatch")
    return tuple(zip(bundle.payload, bundle.payload_targets, strict=True))


def safe_bundle_file(bundle_path: Path, value: object) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise LockstepError(f"{bundle_path}: git payload source_path is required")
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise LockstepError(f"{bundle_path}: unsafe git payload source_path {value!r}")
    source = (bundle_path / relative).resolve()
    try:
        source.relative_to(bundle_path.resolve())
    except ValueError as exc:
        raise LockstepError(f"{bundle_path}: git payload source escapes bundle") from exc
    if not source.is_file():
        raise LockstepError(f"{bundle_path}: missing git payload source {value!r}")
    return source


def safe_git_target(bundle_path: Path, abbreviation: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LockstepError(f"{bundle_path}: git payload target_path is required")
    relative = Path(value)
    required_root = Path("series") / abbreviation
    if relative.is_absolute() or ".." in relative.parts:
        raise LockstepError(f"{bundle_path}: unsafe git target {value!r}")
    try:
        relative.relative_to(required_root)
    except ValueError as exc:
        raise LockstepError(
            f"{bundle_path}: new git target must be namespaced below {required_root}"
        ) from exc
    return relative.as_posix()


def load_git_payload_manifest(
    bundle_path: Path,
    abbreviation: str,
) -> tuple[tuple[Path, ...], tuple[str, ...], str | None] | None:
    manifest_path = bundle_path / "GIT_PAYLOAD_MANIFEST.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LockstepError(f"{manifest_path}: invalid JSON") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise LockstepError(f"{manifest_path}: schema_version must be 1")
    if manifest.get("standard") != "VRS-GIT-PAYLOAD-1":
        raise LockstepError(f"{manifest_path}: invalid standard")
    if manifest.get("abbreviation") != abbreviation:
        raise LockstepError(f"{manifest_path}: abbreviation mismatch")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise LockstepError(f"{manifest_path}: entries must be non-empty")
    sources: list[Path] = []
    targets: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise LockstepError(f"{manifest_path}: entry must be an object")
        source = safe_bundle_file(bundle_path, entry.get("source_path"))
        target = safe_git_target(bundle_path, abbreviation, entry.get("target_path"))
        if entry.get("sha256") != sha256(source):
            raise LockstepError(f"{manifest_path}: SHA-256 mismatch for {source.name}")
        sources.append(source)
        targets.append(target)
    if len(targets) != len(set(targets)):
        raise LockstepError(f"{manifest_path}: duplicate target paths")
    if not any(source.suffix == ".lean" for source in sources):
        raise LockstepError(f"{manifest_path}: no Lean source")
    if not any(Path(target).name.upper() in FORMAL_SUMMARY_TARGET_NAMES for target in targets):
        raise LockstepError(f"{manifest_path}: no formal verification summary")
    build_root = manifest.get("build_root")
    if not isinstance(build_root, str) or not build_root.strip():
        raise LockstepError(f"{manifest_path}: build_root is required")
    normalized_build_root = safe_git_target(bundle_path, abbreviation, build_root)
    return tuple(sources), tuple(targets), normalized_build_root


def extract_github_token(raw: str) -> str:
    """Parse escaped or plain GitHub tokens without ever printing the token."""
    normalized = raw.replace("\\", "").replace(" ", "").replace("\n", "")
    matches = TOKEN_PATTERN.findall(normalized)
    if not matches:
        raise LockstepError(f"no GitHub credential found in {TOKEN_FILE}")
    token = max(matches, key=len)
    prefixes = ("ghp_", "github_pat_")
    if not token.startswith(prefixes):
        raise LockstepError(
            "GitHub credential must be a persistent classic or fine-grained PAT"
        )
    return token


def read_github_token() -> str:
    try:
        return extract_github_token(TOKEN_FILE.read_text(encoding="utf-8"))
    except OSError as exc:
        raise LockstepError(f"cannot read GitHub credential: {exc}") from exc


def read_doi(path: Path) -> str | None:
    if not path.is_file():
        return None
    doi = path.read_text(encoding="utf-8").strip()
    if DOI_PATTERN.fullmatch(doi) is None:
        raise LockstepError(f"{path}: invalid DOI {doi!r}")
    return doi


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_post_aristotle_review(
    bundle_path: Path,
    paper: Path,
    lean_files: Sequence[Path],
    summaries: Sequence[Path],
) -> tuple[Path, str, str, str, str | None, str, str]:
    """Validate the post-Aristotle review against the exact release artifacts."""
    neutral_path = bundle_path / POST_ARISTOTLE_REVIEW_NAME
    legacy_path = bundle_path / LEGACY_CLAUDE_REVIEW_NAME
    present = [path for path in (neutral_path, legacy_path) if path.is_file()]
    if len(present) != 1:
        detail = "missing" if not present else "ambiguous; both review files are present"
        raise LockstepError(
            f"{bundle_path}: {detail} post-Aristotle review; expected exactly one of "
            f"{POST_ARISTOTLE_REVIEW_NAME} or {LEGACY_CLAUDE_REVIEW_NAME}"
        )
    review_path = present[0]
    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LockstepError(f"{review_path}: invalid post-Aristotle review: {exc}") from exc

    if review_path == legacy_path:
        if review.get("schema_version") != 1:
            raise LockstepError(f"{review_path}: legacy schema_version must be 1")
        if review.get("reviewer") != "Claude":
            raise LockstepError(f"{review_path}: legacy reviewer must be Claude")
        reviewer_system = "Claude"
        reviewer_model = None
    else:
        if review.get("schema_version") != 2:
            raise LockstepError(f"{review_path}: schema_version must be 2")
        reviewer_system = review.get("reviewer_system")
        reviewer_model = review.get("reviewer_model")
        if not isinstance(reviewer_system, str) or not reviewer_system.strip():
            raise LockstepError(f"{review_path}: reviewer_system is required")
        if not isinstance(reviewer_model, str) or not reviewer_model.strip():
            raise LockstepError(f"{review_path}: reviewer_model is required")
        reviewer_system = reviewer_system.strip()
        reviewer_model = reviewer_model.strip()
    if review.get("verdict") != "pass":
        raise LockstepError(f"{review_path}: verdict must be pass")

    reviewed_at = review.get("reviewed_at_utc")
    try:
        parsed = dt.datetime.fromisoformat(str(reviewed_at).replace("Z", "+00:00"))
    except ValueError as exc:
        raise LockstepError(f"{review_path}: invalid reviewed_at_utc") from exc
    if parsed.tzinfo is None:
        raise LockstepError(f"{review_path}: reviewed_at_utc must include a timezone")

    route = review.get("series_route")
    if not isinstance(route, str) or not route.strip():
        raise LockstepError(f"{review_path}: series_route is required")

    spine = review.get("spine_admission")
    if not isinstance(spine, dict) or spine.get("admitted") is not False:
        raise LockstepError(
            f"{review_path}: series/standalone releases must record spine_admission.admitted=false"
        )
    gate = spine.get("gate")
    reason = spine.get("reason")
    if not isinstance(gate, str) or not gate.strip() or not isinstance(reason, str) or not reason.strip():
        raise LockstepError(f"{review_path}: spine gate and reason are required")

    checks = review.get("checks")
    if not isinstance(checks, dict):
        raise LockstepError(f"{review_path}: checks object is required")
    missing_checks = [name for name in REVIEW_CHECKS if checks.get(name) is not True]
    if missing_checks:
        raise LockstepError(
            f"{review_path}: review checks are not green: {', '.join(missing_checks)}"
        )

    expected = {item.name: sha256(item) for item in (paper, *lean_files, *summaries)}
    artifacts = review.get("artifacts")
    if not isinstance(artifacts, dict) or artifacts != expected:
        raise LockstepError(
            f"{review_path}: artifact names or SHA-256 hashes do not match the bundle"
        )

    return (
        review_path,
        sha256(review_path),
        str(reviewed_at),
        reviewer_system,
        reviewer_model,
        route.strip(),
        f"{gate.strip()}: {reason.strip()}",
    )


def discover_bundles(
    date: str,
    base: Path = HERE,
    *,
    allow_unassigned_license: bool = False,
    include_abbreviations: frozenset[str] | None = None,
) -> list[Bundle]:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) is None:
        raise LockstepError("--date must use YYYY-MM-DD")

    bundles: list[Bundle] = []
    seen_targets: dict[str, Path] = {}
    for path in sorted(base.glob(f"{date}_*_standalone")):
        if not path.is_dir():
            continue
        parts = path.name.split("_", 2)
        if len(parts) < 3 or not parts[1]:
            raise LockstepError(f"{path}: cannot derive abbreviation")
        abbreviation = parts[1].upper()
        if include_abbreviations is not None and abbreviation not in include_abbreviations:
            continue
        metadata_path = path / "zenodo_metadata.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            title = metadata["metadata"]["title"]
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            raise LockstepError(f"{metadata_path}: invalid metadata: {exc}") from exc
        if date > POST_ARISTOTLE_REVIEW_REQUIRED_AFTER:
            license_id = metadata["metadata"].get("license")
            if not allow_unassigned_license and (
                not isinstance(license_id, str)
                or not license_id.strip()
                or license_id.strip().lower() in {"unassigned", "none", "pending"}
            ):
                raise LockstepError(
                    f"{metadata_path}: exact rights/license value is required"
                )
            creators = metadata["metadata"].get("creators", [])
            creator_names = [
                str(creator.get("name", ""))
                for creator in creators
                if isinstance(creator, dict)
            ]
            if not any("Justin" in name and "Hart" in name for name in creator_names):
                raise LockstepError(
                    f"{metadata_path}: Justin D. Hart must be the accountable creator"
                )
            ai_names = ("aristotle", "claude", "chatgpt", "openai", "harmonic")
            unsafe = [
                name for name in creator_names if any(term in name.lower() for term in ai_names)
            ]
            if unsafe:
                raise LockstepError(
                    f"{metadata_path}: AI systems belong in disclosure/provenance, "
                    f"not creators: {', '.join(unsafe)}"
                )
        reviewed_payload = tuple(
            sorted(
                candidate
                for candidate in path.iterdir()
                if candidate.is_file()
                and (
                    candidate.name.endswith(".lean")
                    or (
                        candidate.suffix.lower() == ".md"
                        and "summary" in candidate.name.lower()
                    )
                )
            )
        )
        lean_files = [item for item in reviewed_payload if item.name.endswith(".lean")]
        summaries = [
            item
            for item in reviewed_payload
            if item.suffix.lower() == ".md" and "summary" in item.name.lower()
        ]
        if not lean_files:
            raise LockstepError(f"{path}: no .lean file")
        if not summaries:
            raise LockstepError(f"{path}: no Aristotle summary companion")
        papers = sorted(
            item for item in path.iterdir() if item.is_file() and item.suffix.lower() == ".pdf"
        )
        if not papers:
            raise LockstepError(f"{path}: no paper PDF (INV-PAPER)")
        if date > POST_ARISTOTLE_REVIEW_REQUIRED_AFTER and len(papers) != 1:
            raise LockstepError(
                f"{path}: future release bundles require exactly one final paper PDF"
            )
        paper = papers[0]

        review_path: Path | None = None
        review_hash: str | None = None
        reviewed_at: str | None = None
        reviewer_system: str | None = None
        reviewer_model: str | None = None
        series_route: str | None = None
        spine_gate: str | None = None
        if date > POST_ARISTOTLE_REVIEW_REQUIRED_AFTER:
            (
                review_path,
                review_hash,
                reviewed_at,
                reviewer_system,
                reviewer_model,
                series_route,
                spine_gate,
            ) = load_post_aristotle_review(path, paper, lean_files, summaries)

        declared_git_payload = load_git_payload_manifest(path, abbreviation)
        if declared_git_payload is None:
            payload = reviewed_payload
            payload_targets = tuple(f"series/{item.name}" for item in payload)
            git_build_root = None
        else:
            payload, payload_targets, git_build_root = declared_git_payload

        for item, target in zip(payload, payload_targets, strict=True):
            prior = seen_targets.get(target)
            if prior is not None:
                raise LockstepError(
                    f"duplicate git target {target}: {prior} and {item}"
                )
            seen_targets[target] = item

        if date > POST_ARISTOTLE_REVIEW_REQUIRED_AFTER and not allow_unassigned_license:
            try:
                release_coherence.validate_bundle(path)
            except release_coherence.CoherenceError as exc:
                raise LockstepError(str(exc)) from exc

        bundles.append(
            Bundle(
                abbreviation=abbreviation,
                path=path,
                title=str(title),
                payload=payload,
                payload_targets=payload_targets,
                git_build_root=git_build_root,
                doi=read_doi(path / "PUBLISHED_DOI.txt"),
                paper=paper,
                review_path=review_path,
                review_sha256=review_hash,
                reviewed_at_utc=reviewed_at,
                reviewer_system=reviewer_system,
                reviewer_model=reviewer_model,
                series_route=series_route,
                spine_gate=spine_gate,
            )
        )

    if not bundles:
        raise LockstepError(f"no {date}_*_standalone bundles found in {base}")
    return bundles


def redact(text: str, secrets: Iterable[str]) -> str:
    result = text
    for secret in secrets:
        if secret:
            result = result.replace(secret, "[REDACTED]")
    return result


def run(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
    capture: bool = True,
    secrets: Iterable[str] = (),
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        list(argv),
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        capture_output=capture,
        check=False,
    )
    if check and completed.returncode:
        stdout = redact(completed.stdout or "", secrets)[-1200:]
        stderr = redact(completed.stderr or "", secrets)[-1200:]
        detail = "\n".join(part for part in (stdout, stderr) if part.strip())
        raise LockstepError(
            f"{argv[0]} failed with exit {completed.returncode}"
            + (f":\n{detail}" if detail else "")
        )
    return completed


def git(
    repo: Path,
    *args: str,
    check: bool = True,
    token: str = "",
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    return run(
        ["git", "-C", str(repo), *args],
        env=env,
        check=check,
        secrets=(token,),
    )


def gh(
    *args: str,
    token: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, GH_TOKEN=token, GIT_TERMINAL_PROMPT="0")
    return run(
        ["gh", *args],
        env=env,
        check=check,
        secrets=(token,),
    )


def commit_message(date: str, bundles: Sequence[Bundle]) -> str:
    lines = [
        f"canon: {date} Zenodo-GitHub lockstep ({len(bundles)} deposits)",
        "",
        "Zenodo DOI <-> GitHub source lockstep:",
    ]
    lines.extend(f"  {bundle.abbreviation:<6}{bundle.doi}" for bundle in bundles)
    lines.extend(
        [
            "",
            "Git mirror only: exact pinned Lean projects and formal-verification "
            "summaries from the published series/standalone bundles, plus DOI "
            "catalog and series-index updates.",
            "",
        ]
    )
    if all(bundle.review_path is not None for bundle in bundles):
        lines.append(
            "None of these deposits is admitted to the spine. The bundle reviews "
            "record the failed admission gate and reason. No spine files or spine "
            "version are changed."
        )
    else:
        lines.append(
            "Legacy 2026-07-26 recovery: none of these deposits is admitted to the "
            "spine; all fail Gate 3 as domain-applying, not domain-defining. The "
            "spine remains v10.2.0."
        )
    # Keep the existing trailer for legacy Aristotle payloads only. Comparator
    # bundles must not acquire an unsupported Aristotle authorship attribution.
    if any(source.name.upper().endswith("ARISTOTLE_SUMMARY.MD")
           for bundle in bundles for source in bundle.payload):
        lines.extend(["", COAUTHOR_TRAILER])
    lines.append("")
    return "\n".join(lines)


def copy_payload(repo: Path, bundles: Sequence[Bundle]) -> list[str]:
    series = repo / "series"
    series.mkdir(exist_ok=True)
    targets: list[str] = []
    for bundle in bundles:
        for source, relative in payload_pairs(bundle):
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            targets.append(relative)
    return sorted(targets)


def markdown_cell(value: str) -> str:
    return " ".join(value.replace("|", r"\|").split())


def update_public_surfaces(
    repo: Path, bundles: Sequence[Bundle]
) -> tuple[list[str], str, str]:
    """Add DOI mappings/index rows and regenerate the deterministic Pages catalog."""
    if any(bundle.doi is None for bundle in bundles):
        raise LockstepError("public surfaces cannot be built before every included DOI exists")

    config_path = repo / "catalog" / "config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
        doi_by_path = config["doi_by_path"]
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise LockstepError(f"{config_path}: invalid public catalog configuration") from exc
    if not isinstance(doi_by_path, dict):
        raise LockstepError(f"{config_path}: doi_by_path must be an object")

    for bundle in bundles:
        assert bundle.doi is not None
        for source, target in payload_pairs(bundle):
            if source.suffix != ".lean":
                continue
            key = target
            existing = doi_by_path.get(key)
            if existing is not None and existing != bundle.doi:
                raise LockstepError(
                    f"{config_path}: {key} already maps to a different DOI ({existing})"
                )
            doi_by_path[key] = bundle.doi
    config["doi_by_path"] = dict(sorted(doi_by_path.items()))
    config_path.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    index_path = repo / "series" / "README.md"
    try:
        index_text = index_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LockstepError(f"{index_path}: cannot read series index") from exc
    marker = "\nSeries concept DOIs:"
    if marker not in index_text:
        raise LockstepError(f"{index_path}: missing Series concept DOIs marker")

    new_rows: list[str] = []
    for bundle in bundles:
        assert bundle.doi is not None
        for source, target in payload_pairs(bundle):
            if source.suffix != ".lean":
                continue
            display_target = target.removeprefix("series/")
            file_cell = f"`{display_target}`"
            existing_row = next(
                (
                    line
                    for line in index_text.splitlines()
                    if line.startswith("|") and file_cell in line
                ),
                None,
            )
            if existing_row is not None:
                if bundle.doi not in existing_row:
                    raise LockstepError(
                        f"{index_path}: {display_target} exists with a different DOI"
                    )
                continue
            if not bundle.series_route:
                raise LockstepError(
                    f"{bundle.path}: post-Aristotle review must supply series_route for new index rows"
                )
            new_rows.append(
                f"| {file_cell} | {markdown_cell(bundle.title)} | "
                f"{markdown_cell(bundle.series_route)} | "
                f"[{bundle.doi}](https://doi.org/{bundle.doi}) |"
            )
    if new_rows:
        index_text = index_text.replace(
            marker, "\n" + "\n".join(new_rows) + marker, 1
        )
        index_path.write_text(index_text, encoding="utf-8")

    build = run(
        [sys.executable, "tools/build_research_portal.py"],
        cwd=repo,
        secrets=(),
    )
    if build.stdout:
        print(build.stdout.strip())
    run(
        [sys.executable, "tools/build_research_portal.py", "--check"],
        cwd=repo,
        secrets=(),
    )
    catalog_path = repo / "docs" / "data" / "catalog.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        digest = str(catalog["catalog_digest"])
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        raise LockstepError(f"{catalog_path}: invalid generated catalog") from exc
    return (
        ["catalog/config.json", "docs/data/catalog.json", "series/README.md"],
        digest,
        str(config.get("release", "unknown")),
    )


def preflight_release(repo: Path) -> None:
    """Prove the checked-in catalog and deterministic tests are green."""
    run(
        [sys.executable, "tools/build_research_portal.py", "--check"],
        cwd=repo,
    )
    run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_*.py",
            "-v",
        ],
        cwd=repo,
    )


def probe_git_write(repo: Path, token: str) -> None:
    probe = git(
        repo,
        "push",
        "--dry-run",
        "origin",
        "HEAD:refs/heads/probe-write-access",
        check=False,
        token=token,
    )
    if probe.returncode:
        detail = redact((probe.stderr or probe.stdout or "").strip(), (token,))
        raise LockstepError(
            "GitHub write preflight failed before Zenodo publication"
            + (f":\n{detail[-800:]}" if detail else "")
        )


def refresh_dois(bundles: Sequence[Bundle]) -> list[Bundle]:
    return [
        dataclasses.replace(
            bundle, doi=read_doi(bundle.path / "PUBLISHED_DOI.txt")
        )
        for bundle in bundles
    ]


def create_commit(
    repo: Path, date: str, bundles: Sequence[Bundle], targets: Sequence[str], token: str
) -> tuple[str, bool]:
    git(repo, "add", "--", *targets, token=token)
    staged = git(repo, "diff", "--cached", "--name-only", token=token).stdout.strip()
    if not staged:
        return git(repo, "rev-parse", "HEAD", token=token).stdout.strip(), False

    git(
        repo,
        "-c",
        "user.name=Justin D. Hart",
        "-c",
        "user.email=viridisnorthLLC@gmail.com",
        "commit",
        "-m",
        commit_message(date, bundles),
        token=token,
    )
    return git(repo, "rev-parse", "HEAD", token=token).stdout.strip(), True


def push_commit(
    repo: Path, date: str, commit_sha: str, changed: bool, token: str
) -> tuple[str, str | None, str]:
    if not changed:
        return "main", None, commit_sha

    direct = git(repo, "push", "origin", "HEAD:main", check=False, token=token)
    if direct.returncode == 0:
        return "main", None, commit_sha

    branch = f"canon/lockstep-{date}-{commit_sha[:8]}"
    fallback = git(
        repo,
        "push",
        "origin",
        f"HEAD:refs/heads/{branch}",
        check=False,
        token=token,
    )
    if fallback.returncode:
        detail = redact(
            "\n".join((direct.stderr or "", fallback.stderr or "")), (token,)
        )
        raise LockstepError(f"main and fallback branch pushes failed:\n{detail[-1200:]}")

    title = f"canon: {date} Zenodo-GitHub lockstep"
    body = (
        "Mirrors the exact Lean modules and formal-verification provenance for the "
        f"{date} published Zenodo wave, updates the DOI catalog and series "
        "index, and regenerates the public research portal.\n\n"
        "No spine files or spine version are changed. See the commit body "
        "for all DOIs and the bundle reviews for the admission decisions."
    )
    pr = gh(
        "pr",
        "create",
        "--repo",
        REPOSITORY,
        "--base",
        "main",
        "--head",
        branch,
        "--title",
        title,
        "--body",
        body,
        token=token,
        check=False,
    )
    if pr.returncode:
        compare_url = f"https://github.com/{REPOSITORY}/compare/{branch}?expand=1"
        detail = redact((pr.stderr or pr.stdout or "").strip(), (token,))
        raise LockstepError(
            f"branch {branch} was pushed, but PR creation failed:\n{detail[-800:]}\n"
            f"Open: {compare_url}"
        )
    pr_url = pr.stdout.strip()
    checks = gh(
        "pr",
        "checks",
        pr_url,
        "--repo",
        REPOSITORY,
        "--watch",
        "--interval",
        "15",
        token=token,
        check=False,
    )
    if checks.returncode:
        detail = redact((checks.stderr or checks.stdout or "").strip(), (token,))
        if "no checks reported" not in detail.lower():
            raise LockstepError(
                f"PR checks failed; the DOI-bearing source remains on {branch}:\n"
                f"{detail[-1200:]}\nPR: {pr_url}"
            )
    merge = gh(
        "pr",
        "merge",
        pr_url,
        "--repo",
        REPOSITORY,
        "--merge",
        "--delete-branch",
        token=token,
        check=False,
    )
    if merge.returncode:
        detail = redact((merge.stderr or merge.stdout or "").strip(), (token,))
        if "--auto" not in detail and "policy prohibits" not in detail.lower():
            raise LockstepError(
                f"PR checks passed but merge failed:\n{detail[-800:]}\nPR: {pr_url}"
            )
        auto = gh(
            "pr",
            "merge",
            pr_url,
            "--repo",
            REPOSITORY,
            "--merge",
            "--auto",
            "--delete-branch",
            token=token,
            check=False,
        )
        if auto.returncode:
            auto_detail = redact((auto.stderr or auto.stdout or "").strip(), (token,))
            if "auto merge is not allowed" not in auto_detail.lower():
                raise LockstepError(
                    f"PR auto-merge could not be enabled:\n{auto_detail[-800:]}\nPR: {pr_url}"
                )
            # GitHub can report the initially visible checks as complete while
            # matrix jobs are still being registered. If repository auto-merge
            # is disabled, wait once more for the full check set, then retry
            # the ordinary authorized merge instead of leaving a green PR open.
            registration_deadline = time.monotonic() + 300
            while True:
                retry_checks = gh(
                    "pr",
                    "checks",
                    pr_url,
                    "--repo",
                    REPOSITORY,
                    "--watch",
                    "--interval",
                    "15",
                    token=token,
                    check=False,
                )
                if retry_checks.returncode == 0:
                    break
                retry_detail = redact(
                    (retry_checks.stderr or retry_checks.stdout or "").strip(),
                    (token,),
                )
                if (
                    "no checks reported" not in retry_detail.lower()
                    or time.monotonic() >= registration_deadline
                ):
                    raise LockstepError(
                        f"PR checks failed after auto-merge fallback:\n"
                        f"{retry_detail[-1200:]}\nPR: {pr_url}"
                    )
                time.sleep(15)
            retry_merge = gh(
                "pr",
                "merge",
                pr_url,
                "--repo",
                REPOSITORY,
                "--merge",
                "--delete-branch",
                token=token,
                check=False,
            )
            if retry_merge.returncode:
                retry_detail = redact(
                    (retry_merge.stderr or retry_merge.stdout or "").strip(),
                    (token,),
                )
                raise LockstepError(
                    f"PR checks passed but fallback merge failed:\n"
                    f"{retry_detail[-800:]}\nPR: {pr_url}"
                )
    merged_commit = wait_for_pr_merge(pr_url, token)
    return "main", pr_url, merged_commit


def wait_for_pr_merge(
    pr_url: str,
    token: str,
    *,
    timeout_seconds: int = 5400,
) -> str:
    """Wait for branch policy and auto-merge to land the authorized PR."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        viewed = gh(
            "pr",
            "view",
            pr_url,
            "--repo",
            REPOSITORY,
            "--json",
            "state,mergeCommit",
            token=token,
            check=False,
        )
        if viewed.returncode:
            detail = redact((viewed.stderr or viewed.stdout or "").strip(), (token,))
            raise LockstepError(f"cannot inspect auto-merge state:\n{detail[-800:]}")
        try:
            state = json.loads(viewed.stdout)
        except json.JSONDecodeError as exc:
            raise LockstepError("PR auto-merge state was not valid JSON") from exc
        if state.get("state") == "MERGED":
            merge_commit = state.get("mergeCommit")
            oid = merge_commit.get("oid") if isinstance(merge_commit, dict) else None
            if isinstance(oid, str) and re.fullmatch(r"[0-9a-f]{40}", oid):
                return oid
            raise LockstepError(f"cannot resolve merged main commit for {pr_url}")
        if state.get("state") == "CLOSED":
            raise LockstepError(f"authorized PR closed without merging: {pr_url}")
        time.sleep(15)
    raise LockstepError(f"timed out waiting for PR auto-merge: {pr_url}")


def wait_for_main_workflows(
    commit_sha: str,
    token: str,
    *,
    timeout_seconds: int = 5400,
) -> list[dict[str, object]]:
    """Wait until blocking CI and Pages workflows succeed on the main commit."""
    required = {"viridis-canon-ci", "research-catalog-and-pages"}
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        listed = gh(
            "run",
            "list",
            "--repo",
            REPOSITORY,
            "--commit",
            commit_sha,
            "--event",
            "push",
            "--limit",
            "20",
            "--json",
            "databaseId,name,status,conclusion,url",
            token=token,
            check=False,
        )
        if listed.returncode:
            detail = redact((listed.stderr or listed.stdout or "").strip(), (token,))
            raise LockstepError(f"cannot inspect GitHub workflows:\n{detail[-800:]}")
        try:
            rows = json.loads(listed.stdout)
        except json.JSONDecodeError as exc:
            raise LockstepError("GitHub workflow response was not valid JSON") from exc
        if not isinstance(rows, list) or not all(
            isinstance(row, dict) for row in rows
        ):
            raise LockstepError(
                "GitHub workflow response must be an array of workflow objects"
            )
        latest: dict[str, dict[str, object]] = {}
        for row in rows:
            name = row.get("name")
            if name in required and name not in latest:
                latest[str(name)] = row
        failed = [
            f"{name}: {row.get('conclusion')}"
            for name, row in latest.items()
            if row.get("status") == "completed" and row.get("conclusion") != "success"
        ]
        if failed:
            raise LockstepError(
                "blocking GitHub workflow failed on main: " + ", ".join(failed)
            )
        if required.issubset(latest) and all(
            latest[name].get("status") == "completed"
            and latest[name].get("conclusion") == "success"
            for name in required
        ):
            return [latest[name] for name in sorted(required)]
        time.sleep(15)
    raise LockstepError(
        f"timed out waiting for blocking workflows on main commit {commit_sha}"
    )



def verify_doi_resolution(doi: str, *, attempts: int = 3) -> None:
    """Retry transient public resolver failures; success still requires resolution."""
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                f"https://doi.org/{doi}",
                headers={"User-Agent": "Viridis-Canon-Lockstep/1.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status >= 400:
                    raise LockstepError(f"DOI did not resolve: {doi} ({response.status})")
            return
        except (OSError, urllib.error.URLError) as exc:
            permanent_http_error = (
                isinstance(exc, urllib.error.HTTPError)
                and exc.code not in {408, 429, 500, 502, 503, 504}
            )
            if permanent_http_error or attempt + 1 == attempts:
                raise LockstepError(f"DOI did not resolve: {doi}: {exc}") from exc
            print(f"Transient DOI readback failure; retry {attempt + 2}/{attempts}: {doi}")
            time.sleep(2 ** (attempt + 1))


def verify_pages(
    catalog_digest: str,
    bundles: Sequence[Bundle],
    *,
    timeout_seconds: int = 900,
) -> str:
    """Wait for Pages to expose the exact catalog and verify every DOI resolves."""
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    published_catalog: dict[str, object] | None = None
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                PUBLIC_CATALOG_URL,
                headers={"User-Agent": "Viridis-Canon-Lockstep/1.0"},
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                candidate = json.loads(response.read().decode("utf-8"))
            if not isinstance(candidate, dict):
                raise LockstepError("Pages catalog root must be a JSON object")
            if candidate.get("catalog_digest") == catalog_digest:
                published_catalog = candidate
                break
            last_error = (
                f"catalog digest is {candidate.get('catalog_digest')}, "
                f"expected {catalog_digest}"
            )
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = str(exc)
        time.sleep(15)
    if published_catalog is None:
        raise LockstepError(f"Pages catalog did not converge: {last_error}")

    published_records = published_catalog.get("records")
    if not isinstance(published_records, list):
        raise LockstepError("Pages catalog records must be an array")
    records = {
        record.get("path"): record
        for record in published_records
        if isinstance(record, dict)
    }
    for bundle in bundles:
        assert bundle.doi is not None
        for source, target in payload_pairs(bundle):
            if source.suffix != ".lean":
                continue
            path = target
            record = records.get(path)
            if record is None or record.get("doi") != bundle.doi:
                raise LockstepError(
                    f"Pages catalog DOI mismatch for {path}: expected {bundle.doi}"
                )
        verify_doi_resolution(bundle.doi)
    return PUBLIC_CATALOG_URL


def verify_public(
    branch: str, expected_commit: str, expected_hashes: dict[str, str]
) -> dict[str, str]:
    temp_root = Path(tempfile.mkdtemp(prefix="viridis-canon-verify-", dir="/var/tmp"))
    repo = temp_root / "viridis-canon"
    try:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        run(
            [
                "git",
                "clone",
                "--quiet",
                "--depth",
                "1",
                "--branch",
                branch,
                PUBLIC_REPO_URL,
                str(repo),
            ],
            env=env,
        )
        actual_commit = git(repo, "rev-parse", "HEAD").stdout.strip()
        if actual_commit != expected_commit:
            raise LockstepError(
                f"public {branch} is {actual_commit}, expected {expected_commit}"
            )

        hashes: dict[str, str] = {}
        for relative, expected_hash in expected_hashes.items():
            target = repo / relative
            if not target.is_file():
                raise LockstepError(f"fresh public clone is missing {relative}")
            target_hash = sha256(target)
            if expected_hash != target_hash:
                raise LockstepError(f"fresh public clone mismatch: {relative}")
            hashes[relative] = target_hash
        return hashes
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def write_receipt(
    date: str,
    bundles: Sequence[Bundle],
    commit_sha: str,
    source_commit_sha: str,
    branch: str,
    pr_url: str | None,
    hashes: dict[str, str],
    catalog_digest: str,
    spine_version: str,
    workflows: Sequence[dict[str, object]],
    public_catalog_url: str,
) -> Path:
    RECEIPT_DIR.mkdir(exist_ok=True)
    path = RECEIPT_DIR / f"{date}.json"
    payload = {
        "schema_version": 2,
        "verified_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository": REPOSITORY,
        "branch": branch,
        "commit_sha": commit_sha,
        "source_commit_sha": source_commit_sha,
        "pull_request_url": pr_url,
        "catalog_digest": catalog_digest,
        "public_catalog_url": public_catalog_url,
        "workflows": list(workflows),
        "spine_version": spine_version,
        "spine_changed": False,
        "bundles": [
            {
                "abbreviation": bundle.abbreviation,
                "doi": bundle.doi,
                "title": bundle.title,
                "files": [target for _, target in payload_pairs(bundle)],
                "paper": {
                    "path": bundle.paper.name,
                    "sha256": sha256(bundle.paper),
                },
                "post_aristotle_review": (
                    {
                        "path": bundle.review_path.name,
                        "sha256": bundle.review_sha256,
                        "reviewed_at_utc": bundle.reviewed_at_utc,
                        "reviewer_system": bundle.reviewer_system,
                        "reviewer_model": bundle.reviewer_model,
                    }
                    if bundle.review_path is not None
                    else None
                ),
                "series_route": bundle.series_route,
                "spine_gate": bundle.spine_gate,
            }
            for bundle in bundles
        ],
        "sha256": hashes,
        "status": "verified",
    }
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)
    return path


def print_plan(date: str, bundles: Sequence[Bundle], publisher: Sequence[str]) -> None:
    published = [bundle for bundle in bundles if bundle.doi]
    print(f"{date}: {len(bundles)} bundles, {sum(len(b.payload) for b in bundles)} git files")
    for bundle in bundles:
        state = bundle.doi or "awaiting DOI"
        review = (
            f"reviewed by {bundle.reviewer_system}"
            if bundle.review_path
            else "legacy review exemption"
        )
        print(
            f"  {bundle.abbreviation:<6}{state}  "
            f"({len(bundle.payload)} git files; {review})"
        )
    if publisher:
        print("\nPublisher argv:")
        print("  " + " ".join(publisher))
    elif len(published) == len(bundles):
        print("\nRecovery/verification mode: all DOI files already exist; Zenodo will not run.")
    else:
        print("\nNo publisher supplied; --go will mirror only bundles that already have DOI files.")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True, help="wave date, YYYY-MM-DD")
    parser.add_argument(
        "--go",
        action="store_true",
        help="probe GitHub, optionally run the supplied publisher, mirror, and verify",
    )
    parser.add_argument(
        "--rebuild-lean",
        action="store_true",
        help="optional diagnostic replay; sealed Aristotle/post-Lean receipts are the default gate",
    )
    parser.add_argument(
        "publisher",
        nargs=argparse.REMAINDER,
        help="exact publisher argv after --; must include --publish",
    )
    args = parser.parse_args(argv)
    if args.publisher and args.publisher[0] == "--":
        args.publisher = args.publisher[1:]
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    bundles = discover_bundles(args.date)
    print_plan(args.date, bundles, args.publisher)
    if not args.go:
        print("\nDRY RUN — no network calls or writes.")
        return 0
    if args.publisher and "--publish" not in args.publisher:
        raise LockstepError(
            "publisher argv must contain --publish; use the publisher directly for drafts"
        )

    token = read_github_token()
    temp_root = Path(tempfile.mkdtemp(prefix="viridis-canon-lockstep-", dir="/var/tmp"))
    repo = temp_root / "viridis-canon"
    publisher_rc = 0
    try:
        env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
        run(
            ["git", "clone", "--quiet", TOKEN_REPO_URL.format(token=token), str(repo)],
            env=env,
            secrets=(token,),
        )
        probe_git_write(repo, token)
        print("\nGitHub write preflight: OK (before Zenodo).")
        print("\nRunning pre-publication catalog and unit gates...")
        preflight_release(repo)
        copy_payload(repo, bundles)
        if args.rebuild_lean:
            declared_builds = [bundle for bundle in bundles if bundle.git_build_root]
            if declared_builds:
                print("Running optional exact pinned-project diagnostics...")
                for bundle in declared_builds:
                    assert bundle.git_build_root is not None
                    run(["lake", "build"], cwd=repo / bundle.git_build_root)
            print("Running optional Canon compatibility diagnostics...")
            run(["lake", "build"], cwd=repo)
            run(["lake", "build"], cwd=repo / "compat" / "v4_24")
        else:
            print(
                "Sealed Aristotle and exact post-Lean receipts: OK; "
                "redundant local Lean rebuild skipped."
            )
        print("Pre-publication release gates: OK.")

        if args.publisher:
            print("\nRunning the explicitly authorized publisher...")
            completed = run(
                args.publisher,
                cwd=HERE,
                check=False,
                capture=False,
                secrets=(token,),
            )
            publisher_rc = completed.returncode

        refreshed = refresh_dois(bundles)
        published = [bundle for bundle in refreshed if bundle.doi]
        missing = [bundle.abbreviation for bundle in refreshed if not bundle.doi]
        if not published:
            raise LockstepError(
                "no valid PUBLISHED_DOI.txt files exist; nothing may be pushed to git"
            )

        published_targets = [
            target
            for bundle in published
            for _, target in payload_pairs(bundle)
        ]
        surface_targets, catalog_digest, spine_version = update_public_surfaces(
            repo, published
        )
        commit_targets = sorted(set(published_targets + surface_targets))
        expected_hashes = {
            target: sha256(repo / target) for target in commit_targets
        }
        commit_sha, changed = create_commit(
            repo, args.date, published, commit_targets, token
        )
        branch, pr_url, public_commit = push_commit(
            repo, args.date, commit_sha, changed, token
        )
        # Recovery/no-change runs still bind the exact public main commit to its
        # required CI and Pages receipts. Reusing DOIs must not weaken evidence.
        workflows = wait_for_main_workflows(public_commit, token)
        hashes = verify_public(branch, public_commit, expected_hashes)
        public_catalog_url = verify_pages(catalog_digest, published)
        receipt = write_receipt(
            args.date,
            published,
            public_commit,
            commit_sha,
            branch,
            pr_url,
            hashes,
            catalog_digest,
            spine_version,
            workflows,
            public_catalog_url,
        )

        print(f"\nGit mirror verified on main: {public_commit}")
        if public_commit != commit_sha:
            print(f"  source commit: {commit_sha}")
        print(f"  branch: {branch}")
        print(f"  files:  {len(hashes)} byte-for-byte matches")
        if pr_url:
            print(f"  PR:     {pr_url}")
        print(f"  catalog: {public_catalog_url}")
        print(f"  receipt: {receipt.relative_to(ROOT)}")

        print("\nPreparing the receipt-bound OS research update (no runtime adoption)...")
        run([sys.executable, str(ROOT / "RESEARCH_PIPELINE_v2/os_kernel_update_queue.py"),
             "--receipt", str(receipt)], cwd=ROOT, capture=False)

        if publisher_rc:
            raise LockstepError(
                f"publisher exited {publisher_rc}; all {len(published)} DOI-bearing "
                "bundles were still mirrored and verified"
            )
        if missing:
            raise LockstepError(
                "Git lockstep is satisfied for published bundles, but these bundles "
                f"still have no DOI: {', '.join(missing)}"
            )
        return 0
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LockstepError as exc:
        print(f"\n[ABORT] {exc}", file=sys.stderr)
        raise SystemExit(1)
