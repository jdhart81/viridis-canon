#!/usr/bin/env python3
"""Read-only DOI coverage audit. Consumes certificate assessments; verifies no Lean.

Publication evidence is the local publication registry or PUBLISHED_DOI.txt.
Reserved DOIs, concept identifiers, citations, metadata drafts and title similarity
are not treated as publication receipts. No network access or external mutation.
"""
from __future__ import annotations

import methods_digest_registration

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)
RUN = re.compile(r"\bRun-(\d+)(?:\b|[_-])")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, errors: list[dict]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append({"path": str(path), "error": type(exc).__name__, "detail": str(exc)})
        return None


def _run_id(value: Any) -> str | None:
    match = RUN.search(str(value))
    return f"Run-{int(match.group(1)):03d}" if match else None


def _title_key(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"\\[A-Za-z]+", " ", text).replace("\\\\", " ")
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", text).lower())


def _primary_title_key(value: Any) -> str:
    """Exact primary-title candidate when publication edited a subtitle."""
    return _title_key(re.split(r":|\\\\", str(value or ""), maxsplit=1)[0])


def _tex_title(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    match = re.search(r"\\(?:paper)?title(?:\[[^\]]*\])?\s*\{", text)
    if not match:
        return None
    start, level, pos = match.end(), 1, match.end()
    while pos < len(text) and level:
        if text[pos] == "{" and (pos == 0 or text[pos - 1] != "\\"):
            level += 1
        elif text[pos] == "}" and (pos == 0 or text[pos - 1] != "\\"):
            level -= 1
        pos += 1
    return " ".join(text[start:pos - 1].split()) if level == 0 else None


def published_dois(text: str) -> tuple[list[str], list[str]]:
    """Parse actual versions in receipt files; keep concept/citation IDs separate."""
    versions, excluded = set(), set()
    for line in text.splitlines():
        found = {match.group(0).rstrip(".,;)") for match in DOI.finditer(line)}
        if not found:
            continue
        stripped = line.strip()
        if re.search(r"concept\s*doi|isDerivedFrom|isSupplementTo|references", line, re.I):
            excluded.update(found)
        elif re.match(r"^10\.\d{4,9}/", stripped, re.I) or re.search(
            r"\b(?:Version\s+DOI|DOI|v\d+\s*:|PUBLISHED)\b", line, re.I
        ) or re.match(r"^\s*v\d+\s*:", line, re.I):
            versions.update(found)
        elif re.match(r"^\s*(?:Record(?:\s*\([^)]*\))?\s*:|https?://(?:www\.)?zenodo\.org/records?/)", line, re.I):
            # URLs duplicate version receipts, but are not themselves DOI strings.
            versions.update(found)
        else:
            excluded.update(found)
    return sorted(versions), sorted(excluded - versions)


def _certificates(ledger: dict, root: Path) -> list[dict]:
    raw = ledger.get("certificates", [])
    rows = list(raw.values()) if isinstance(raw, dict) else raw
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = row.get("cert_path") or row.get("certificate") or row.get("path")
        if not isinstance(path, str):
            continue
        p = Path(path)
        if not p.is_absolute():
            p = root / p
        validity = row.get("certificate_valid", row.get("cert_valid", row.get("valid", False)))
        result.append({**row, "path": str(p), "valid": validity is True})
    return result


def _artifact_certificate(deposit: Path, certificates: list[dict], errors: list[dict], root: Path, certificate_assessor=None) -> dict:
    path = deposit / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    assessment = {"certificate": str(path), "certificate_valid": False, "reasons": [],
                  "proof_certificate_present_valid": False, "publication_artifact_bound": False,
                  "formal_evidence_hash_bound": False, "sealed_manuscript_hash_bound": False}
    if not path.is_file():
        assessment["reasons"].append("No certificate in the publication artifact directory")
        return assessment
    cert = _json(path, errors)
    if not isinstance(cert, dict):
        assessment["reasons"].append("Certificate unreadable")
        return assessment
    assessment["run_id"] = _run_id(cert.get("run_id"))
    assessment["certificate_sha256"] = sha256(path)
    matches, invalid_matches = [], []
    for row in certificates:
        try:
            if Path(row["path"]).is_file() and sha256(Path(row["path"])) == assessment["certificate_sha256"]:
                if row["valid"]:
                    matches.append(row["path"])
                else:
                    invalid_matches.append(row)
        except OSError:
            continue
    assessment["cert_store_matches"] = sorted(set(matches))
    if not matches and certificate_assessor is not None:
        # Some released artifacts preserve a later alignment-upgrade envelope,
        # while the primary Run-NNN store retains its earlier certified attempt.
        # Reuse the same receipt-consuming inspection; never infer trust from a
        # matching run number or title, and never execute another verifier.
        try:
            inspected = certificate_assessor(path, root)
            assessment["artifact_certificate_inspection"] = {key: inspected.get(key) for key in ["path", "sha256", "valid", "reasons", "legacy_summary_missing"] if key in inspected}
            if inspected.get("valid") is True:
                matches.append(str(path))
                assessment["validated_via"] = "existing_certificate_inspection_of_preserved_publication_envelope"
            else:
                invalid_matches.append(inspected)
        except Exception as exc:
            assessment["reasons"].append(f"Existing certificate inspection failed closed: {type(exc).__name__}: {exc}")
    if not matches:
        if invalid_matches:
            assessment["reasons"].append("Copied certificate exists but canonical assessment is HOLD: " + "; ".join(sorted({reason for row in invalid_matches for reason in row.get("reasons", [])})))
        else:
            assessment["reasons"].append("No byte-identical certificate assessed valid in the canonical cert store")
        return assessment
    bindings = cert.get("bindings")
    if not isinstance(bindings, dict):
        assessment["reasons"].append("Certificate bindings missing")
        return assessment
    formal_checks = []
    for key, filename in [("candidate_proof", "VERIFICATION_CANDIDATE.lean"), ("formal_statement", "VERIFICATION_STATEMENT.lean")]:
        binding = bindings.get(key, {})
        p = deposit / filename
        ok = isinstance(binding, dict) and isinstance(binding.get("sha256"), str) and p.is_file() and sha256(p) == binding["sha256"]
        formal_checks.append(ok)
        if not ok:
            assessment["reasons"].append(f"Publication artifact {filename} missing or differs from certificate hash")
    assessment["formal_evidence_hash_bound"] = all(formal_checks)
    sealed_checks = []
    sealed_inputs = bindings.get("sealed_paper_inputs", {})
    sealed_inputs = sealed_inputs if isinstance(sealed_inputs, dict) else {}
    for filename in ["paper.pdf", "paper.tex"]:
        binding = sealed_inputs.get("SEALED_" + filename, {})
        binding = binding if isinstance(binding, dict) else {}
        p = deposit / filename
        sealed_checks.append(p.is_file() and bool(binding.get("sha256")) and sha256(p) == binding.get("sha256"))
    assessment["sealed_manuscript_hash_bound"] = all(sealed_checks)
    assessment["proof_certificate_present_valid"] = assessment["formal_evidence_hash_bound"]
    assessment["publication_artifact_bound"] = assessment["formal_evidence_hash_bound"] and assessment["sealed_manuscript_hash_bound"]
    assessment["certificate_valid"] = assessment["publication_artifact_bound"]
    if not assessment["sealed_manuscript_hash_bound"]:
        assessment["manuscript_note"] = "Published manuscript differs from the certificate's sealed inputs or is absent; certificate coverage here is formal evidence only."
        assessment["reasons"].append("Publication manuscript binding unresolved: paper.pdf/paper.tex absent or differ from certified sealed bytes")
    return assessment


def _build_audit_legacy(root: str | Path, ledger: dict, certificate_assessor=None) -> dict:
    if certificate_assessor is None:
        try:
            from certificate_inspection import inspect_certificate
            certificate_assessor = inspect_certificate
        except ImportError:
            pass
    root = Path(root).expanduser().resolve()
    errors: list[dict] = []
    registry_path = root / "science-engine/09_zenodo/ZENODO_RECORDS.json"
    registry = _json(registry_path, errors)
    registry = registry if isinstance(registry, dict) else {}
    registry_rows = registry.get("records", [])
    if not isinstance(registry_rows, list):
        errors.append({"path": str(registry_path), "error": "InvalidSchema", "detail": "records must be a list"})
        registry_rows = []
    certs = _certificates(ledger, root)
    deposits_root = root / "_ZENODO_DEPOSITS"
    try:
        dirs = sorted(p for p in deposits_root.iterdir() if p.is_dir() and not p.is_symlink() and p.name != "__pycache__")
    except OSError as exc:
        errors.append({"path": str(deposits_root), "error": type(exc).__name__, "detail": str(exc)})
        dirs = []
    # Reconciliation staging can contain durable receipts for later public
    # versions. Include receipt-bearing nested artifacts, without counting
    # staging containers as additional top-level deposit directories.
    nested_receipt_dirs = sorted({p.parent for p in deposits_root.rglob("PUBLISHED_DOI.txt")
                                 if p.parent not in dirs and not p.is_symlink()}) if deposits_root.exists() else []
    artifact_dirs = dirs + nested_receipt_dirs
    publications: dict[str, dict] = {}
    deposits = []
    digest_cache = {}

    def digest(path: Path) -> str:
        if path not in digest_cache:
            digest_cache[path] = sha256(path)
        return digest_cache[path]

    def add(doi: str, title: str, source: dict, deposit: dict | None = None) -> None:
        item = publications.setdefault(doi, {"doi": doi, "title": title, "provenance": [],
                                            "deposit_paths": [], "run_ids": [], "certificate_valid": False,
                                            "proof_certificate_present_valid": False, "publication_artifact_bound": False,
                                            "certificate_assessments": []})
        item["provenance"].append(source)
        if deposit:
            item["deposit_paths"].append(deposit["path"])
            item["certificate_assessments"].append(deposit["certificate_assessment"])
            item["certificate_valid"] |= deposit["certificate_assessment"]["certificate_valid"]
            item["proof_certificate_present_valid"] |= deposit["certificate_assessment"]["proof_certificate_present_valid"]
            item["publication_artifact_bound"] |= deposit["certificate_assessment"]["publication_artifact_bound"]
            item["run_ids"].extend(deposit["run_ids"])

    for directory in artifact_dirs:
        metadata_path = directory / "zenodo_metadata.json"
        metadata = _json(metadata_path, errors) if metadata_path.is_file() else {}
        metadata = metadata if isinstance(metadata, dict) else {}
        metadata = metadata.get("metadata", metadata)
        title = str(metadata.get("title") or directory.name) if isinstance(metadata, dict) else directory.name
        if title == directory.name:
            title = next((value for p in sorted(directory.glob("*.tex")) if (value := _tex_title(p))), title)
        receipt = directory / "PUBLISHED_DOI.txt"
        doi_values, excluded = [], []
        if receipt.is_file():
            try:
                doi_values, excluded = published_dois(receipt.read_text(encoding="utf-8"))
            except (OSError, UnicodeError) as exc:
                errors.append({"path": str(receipt), "error": type(exc).__name__, "detail": str(exc)})
        assessment = _artifact_certificate(directory, certs, errors, root, certificate_assessor)
        run_ids = set(filter(None, [assessment.get("run_id")]))
        for filename in ["LEDGER_BINDING.json", "RELEASE_BINDING.json", "ENGINE3_VERIFICATION_REQUEST.json"]:
            path = directory / filename
            if path.is_file():
                data = _json(path, errors)
                if isinstance(data, dict):
                    run_ids.update(filter(None, [_run_id(data.get("run_id")), _run_id(data.get("source_run"))]))
        deposit = {"path": str(directory), "title": title, "published_dois": doi_values,
                   "excluded_concept_or_citation_dois": excluded, "run_ids": sorted(run_ids),
                   "certificate_present": (directory / "LEAN_ZERO_SORRY_CERTIFICATE.json").is_file(),
                   "certificate_assessment": assessment, "registry_title_matches": []}
        deposits.append(deposit)
        for doi in doi_values:
            add(doi, title, {"kind": "local_publication_receipt", "path": str(receipt), "sha256": sha256(receipt)}, deposit)

    for index, row in enumerate(registry_rows):
        if not isinstance(row, dict):
            continue
        doi = row.get("doi")
        status = str(row.get("status", "")).lower()
        if not isinstance(doi, str) or not DOI.fullmatch(doi) or status in {"draft", "staged", "staging", "reserved", "unpublished"}:
            continue
        title = str(row.get("title") or doi)
        source = {"kind": "local_publication_registry", "path": str(registry_path),
                  "sha256": sha256(registry_path), "record_index": index,
                  "record_status": row.get("status"), "publication_date": row.get("publication_date")}
        add(doi, title, source)
        for deposit in deposits:
            if _title_key(deposit["title"]) == _title_key(title):
                deposit["registry_title_matches"].append(doi)
                # A shared title can describe different versions. It is a provenance
                # candidate, never authority to transfer a certificate to a DOI.
                item = publications[doi]
                item.setdefault("publication_candidate_joins", []).append(
                    {"basis": "exact_normalized_registry_title", "deposit": deposit["path"],
                     "certificate_transfer_authorized": False})
                item["run_ids"].extend(deposit["run_ids"])

    runs_root = root / "science-engine/07_nightly_engine/compound research papers"
    prereceipt_runs = []
    try:
        run_dirs = sorted(p for p in runs_root.iterdir() if p.is_dir() and not p.is_symlink() and _run_id(p.name))
    except OSError as exc:
        errors.append({"path": str(runs_root), "error": type(exc).__name__, "detail": str(exc)})
        run_dirs = []
    for directory in run_dirs:
        run_id = _run_id(directory.name)
        if not run_id or int(run_id[4:]) > 115:
            continue
        title = _tex_title(directory / "paper.tex")
        joins, candidate_joins = [], []
        for doi, publication in publications.items():
            for deposit_path in publication["deposit_paths"]:
                deposit_path = Path(deposit_path)
                hashes_match = []
                for name in ["paper.tex", "paper.pdf"]:
                    original, published = directory / name, deposit_path / name
                    if original.is_file() and published.is_file() and digest(original) == digest(published):
                        hashes_match.append(name)
                if hashes_match:
                    joins.append({"doi": doi, "basis": "exact_manuscript_hash", "files": hashes_match, "deposit": str(deposit_path)})
            if title and _title_key(title) == _title_key(publication["title"]):
                joins.append({"doi": doi, "basis": "exact_normalized_title"})
            elif title and _primary_title_key(title) and _primary_title_key(title) == _primary_title_key(publication["title"]):
                candidate_joins.append({"doi": doi, "basis": "exact_primary_title_candidate",
                                        "note": "Full subtitles differ; candidate provenance only, no certificate inheritance"})
        doi_values = sorted({join["doi"] for join in joins})
        prereceipt_runs.append({"run_id": run_id, "path": str(directory), "title": title,
                                "published_dois": doi_values, "publication_joins": joins,
                                "publication_join_candidates": candidate_joins,
                                "certificate_valid": False,
                                "status": "PRE_RECEIPT_UNCERTIFIED",
                                "note": "No publication evidence found" if not doi_values else "Published DOI found by exact local evidence join"})
        for doi in doi_values:
            publications[doi]["run_ids"].append(run_id)

    all_publications = []
    for item in publications.values():
        item["deposit_paths"] = sorted(set(item["deposit_paths"]))
        item["run_ids"] = sorted(set(item["run_ids"]))
        item["status"] = ("PUBLICATION_ARTIFACT_CERTIFIED" if item["publication_artifact_bound"] else
                          "PROOF_CERTIFIED_PUBLICATION_BINDING_UNRESOLVED" if item["proof_certificate_present_valid"] else
                          "PUBLISHED_WITHOUT_VALID_PROOF_CERTIFICATE")
        if not item["certificate_valid"]:
            item["recommended_label"] = "CONJECTURE — not machine-verified"
            item["reasons"] = sorted({reason for assessment in item["certificate_assessments"] for reason in assessment["reasons"]}) or ["No certificate-bound publication artifact identified in the scanned tree"]
        all_publications.append(item)
    all_publications.sort(key=lambda item: item["doi"])
    gaps = [item for item in all_publications if not item["certificate_valid"]]
    unresolved = [{"path": row["path"], "title": row["title"],
                   "reason": "No publication receipt or exact registry title join; draft/staging/publication state unresolved"}
                  for row in deposits if not row["published_dois"] and not row["registry_title_matches"]]
    return {"schema_version": "1.0", "mode": "report-only", "scan_root": str(root),
            "publication_evidence_scope": "Local registry and publication receipt files only; no live Zenodo readback",
            "certificate_scope": "Existing Comparator certificate assessment of each artifact's own envelope, plus exact artifact hashes; no new verifier",
            "registry": {"path": str(registry_path), "sha256": sha256(registry_path) if registry_path.is_file() else None,
                         "last_reviewed": registry.get("last_reviewed"), "records_count": len(registry_rows)},
            "counts": {"deposit_directories": len(dirs), "deposit_directories_without_certificate_file": sum(not (p / "LEAN_ZERO_SORRY_CERTIFICATE.json").is_file() for p in dirs),
                       "nested_publication_receipt_directories": len(nested_receipt_dirs),
                       "deposit_publication_receipts": sum(bool(row["published_dois"]) for row in deposits),
                       "published_dois": len(all_publications), "published_artifact_hash_bound": len(all_publications) - len(gaps),
                       "published_with_valid_formal_certificate": sum(row["proof_certificate_present_valid"] for row in all_publications),
                       "published_without_valid_proof_certificate": sum(not row["proof_certificate_present_valid"] for row in all_publications),
                       "published_proof_certified_artifact_binding_unresolved": sum(row["proof_certificate_present_valid"] and not row["publication_artifact_bound"] for row in all_publications),
                       "published_without_certificate": len(gaps), "prereceipt_runs": len(prereceipt_runs),
                       "prereceipt_runs_joined_to_published_dois": sum(bool(row["published_dois"]) for row in prereceipt_runs),
                       "prereceipt_runs_with_publication_join_candidates": sum(bool(row["publication_join_candidates"]) for row in prereceipt_runs),
                       "unresolved_publication_directories": len(unresolved), "errors": len(errors)},
            "published_records": all_publications, "published_without_certificate": gaps,
            "deposit_entities": deposits, "prereceipt_run_entities": prereceipt_runs,
            "unresolved_publication_candidates": unresolved, "errors": errors,
            "human_decision": "Existing DOI labels require explicit human approval before any Zenodo metadata amendment or new version."}


def build_audit(root: str | Path, ledger: dict, certificate_assessor=None) -> dict:
    return methods_digest_registration.augment_audit(root, ledger, _build_audit_legacy(root, ledger, certificate_assessor=certificate_assessor))


def _cell(value: Any) -> str:
    return str(value or "—").replace("|", "\\|").replace("\n", " ")


def render_markdown(audit: dict) -> str:
    counts = audit["counts"]
    lines = ["# Published DOI certificate coverage", "", "Report-only. No Zenodo writes or public labels were changed.", "",
             f"Canonical tree scanned: `{audit['scan_root']}`.", "",
             f"Local evidence identifies **{counts['published_dois']} published version DOIs**: **{counts['published_without_valid_proof_certificate']} without valid proof certificates**, **{counts['published_proof_certified_artifact_binding_unresolved']} with valid proof certificates but unresolved publication manuscript binding**, **{counts['published_artifact_hash_bound']} with exact publication artifact binding.", "",
             f"Deposit census: {counts['deposit_directories']} direct directories; {counts['deposit_directories_without_certificate_file']} have no certificate file. There are {counts['deposit_publication_receipts']} publication receipt files. The registry contains {audit['registry']['records_count']} records and was last reviewed {audit['registry']['last_reviewed']}; it is not a current complete publication census.", "",
             "A DOI is included only from the local publication registry or an explicit PUBLISHED_DOI.txt receipt. Concept DOIs, cited identifiers and reserved draft IDs are excluded. This report has no live Zenodo readback. Unresolved directories are listed separately.", "",
             "Proof coverage means an unchanged Comparator certificate accepted by the existing evidence consumer, plus matching candidate/statement hashes in the local publication artifact. Preserved upgraded publication envelopes are assessed against their own bound receipts and inputs. Publication coverage also requires manuscript bytes to match certified sealed inputs. Edited manuscript binding is unresolved even when its underlying proof certificate is valid. This report creates no new verification authority.", "",
             "## Published DOIs without valid proof certificates", "", "| Published DOI | Title | Run join | Cause | Evidence |", "|---|---|---|---|---|"]
    for item in audit["published_without_certificate"]:
        if item["proof_certificate_present_valid"]:
            continue
        doi = item["doi"]
        evidence = "; ".join(sorted({row["path"] for row in item["provenance"] if row["kind"] != "exact_normalized_registry_title_join"}))
        lines.append(f"| [{doi}](https://doi.org/{doi}) | {_cell(item['title'])} | {_cell(', '.join(item['run_ids']))} | {_cell('; '.join(item['reasons']))} | {_cell(evidence)} |")
    lines += ["", "## Valid proof certificates; publication manuscript binding unresolved", "",
              "These artifacts retain valid proof certificates. They remain publication HOLD because the edited or missing manuscript bytes are not the sealed bytes bound by those certificates. This is a binding gap, not a claim that the underlying formal proof is uncertified.", "",
              "| Published DOI | Title | Run join | Cause |", "|---|---|---|---|"]
    for item in audit["published_without_certificate"]:
        if item["proof_certificate_present_valid"]:
            doi = item["doi"]
            lines.append(f"| [{doi}](https://doi.org/{doi}) | {_cell(item['title'])} | {_cell(', '.join(item['run_ids']))} | {_cell('; '.join(item['reasons']))} |")
    lines += ["", "All publication gaps above require `CONJECTURE — not machine-verified` under the gate policy until resolved. Existing records remain unchanged pending explicit human approval.", "",
              "## Pre-receipt runs 001–115", "",
              f"Found {counts['prereceipt_runs']} runs; {counts['prereceipt_runs_joined_to_published_dois']} join to published version DOIs by exact manuscript hashes or exact normalized titles. A missing join means publication evidence is unavailable, not that the run was never published.", "",
              "| Run | Published DOI(s) | Join evidence |", "|---|---|---|"]
    for row in audit["prereceipt_run_entities"]:
        if row["published_dois"]:
            lines.append(f"| {row['run_id']} | {_cell(', '.join(row['published_dois']))} | {_cell(', '.join(sorted({join['basis'] for join in row['publication_joins']})))} |")
    lines += ["", "Primary titles can also identify candidates when published subtitles changed. These are provenance leads; they do not establish exact artifact identity or transfer certification.", "",
              "| Run | Candidate published DOI(s) | Basis |", "|---|---|---|"]
    for row in audit["prereceipt_run_entities"]:
        if row["publication_join_candidates"]:
            lines.append(f"| {row['run_id']} | {_cell(', '.join(sorted({join['doi'] for join in row['publication_join_candidates']})))} | Exact primary title; subtitle differs |")
    lines += ["", "## Unresolved publication state", "", "These directories have neither an explicit publication DOI receipt nor an exact title match in the registry. Their staged metadata is not proof of publication.", "", "| Directory | Title |", "|---|---|"]
    for row in audit["unresolved_publication_candidates"]:
        lines.append(f"| {_cell(row['path'])} | {_cell(row['title'])} |")
    if audit["errors"]:
        lines += ["", "## Read errors", "", "Read failures are retained as evidence gaps; no affected artifact is certified.", ""]
        for row in audit["errors"]:
            lines.append(f"- `{row['path']}`: {_cell(row['error'])}: {_cell(row['detail'])}")
    lines += ["", "Human decision: " + audit["human_decision"], ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown", required=True)
    args = parser.parse_args()
    ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    try:
        from certificate_inspection import inspect_certificate
    except ImportError:
        inspect_certificate = None
    audit = build_audit(args.root, ledger, certificate_assessor=inspect_certificate)
    Path(args.out).write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    Path(args.markdown).write_text(render_markdown(audit), encoding="utf-8")
    print(json.dumps(audit["counts"], sort_keys=True))
    return 1 if audit["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
