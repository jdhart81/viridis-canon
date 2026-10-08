#!/usr/bin/env python3
"""Prepare opt-in foundational Methods Notes for the unchanged Comparator.

Default: read-only plan. --enforce freezes a new envelope and still leaves it
DEBT. This coordinator never executes Lean, transmits a candidate, issues a
certificate, or changes publication state.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable

CANONICAL_ROOT = Path("/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0")
TOOLCHAIN = "leanprover/lean4:v4.28.0"
MATHLIB_REV = "8f9d9cff6bd728b17a24e163c9402775d9e6a365"
PERMITTED_AXIOMS = ["propext", "Quot.sound", "Classical.choice"]
DISCLAIMER = ("Machine-checked: logical validity given the stated model. "
              "NOT an empirical validation of the model's assumptions.")
CONJECTURE = "CONJECTURE — not machine-verified"
ALIGNMENT_STANDARD = "VRS-ENGINE3-ALIGNED-COMPARATOR-PAIR-1"
SEALED_NAMES = {"SEALED_paper.pdf", "SEALED_paper.tex", "SEALED_CLAIM_INVENTORY.json", "SEALED_RUN_MANIFEST.json"}
LEAN_NAME = re.compile(r"[A-Za-z_][\w']*(?:\.[A-Za-z_][\w']*)*")


class PreparationError(ValueError):
    """Missing or conflicting preparation evidence; status remains HOLD/DEBT."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def regular_path(path: Path, *, must_exist: bool = True) -> Path:
    path = path.absolute()
    if ".." in path.parts:
        raise PreparationError("parent traversal is forbidden")
    for part in (path, *path.parents):
        if part.is_symlink():
            raise PreparationError(f"symlink path refused: {part}")
    if must_exist and not path.is_file():
        raise PreparationError(f"required regular file is missing: {path}")
    return path


def read_object(raw: bytes, label: str) -> dict[str, Any]:
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise PreparationError(f"{label} must be a JSON object")
    return value


def explicit_claims(binding: dict[str, Any], declarations: list[str]) -> tuple[list[dict], list[str], list[str]]:
    claims = binding.get("claims")
    if not isinstance(claims, list) or not claims:
        raise PreparationError("claim_binding must explicitly enumerate public claims")
    normalized: list[dict] = []
    theorems: list[str] = []
    witnesses: list[str] = []
    english_seen: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict):
            raise PreparationError("each claim must be an object")
        english = claim.get("english_claim", claim.get("english"))
        if not isinstance(english, str) or not english.strip() or english in english_seen:
            raise PreparationError("each public claim needs unique nonempty English text")
        english_seen.add(english)
        names = []
        for field in ("lean_theorem", "nonvacuity_obligation"):
            name = claim.get(field)
            if not isinstance(name, str) or LEAN_NAME.fullmatch(name) is None:
                raise PreparationError(f"{field} must name exactly one Lean declaration")
            # No namespace guessing: supplied name must be present exactly once.
            if declarations.count(name) != 1:
                raise PreparationError(f"{field} must name one source declaration: {name}")
            names.append(name)
        fidelity = claim.get("model_fidelity")
        if not isinstance(fidelity, dict):
            raise PreparationError("explicit model_fidelity is required")
        for field in ("defined", "empirically_identified"):
            symbols = fidelity.get(field)
            if not isinstance(symbols, list) or any(not isinstance(s, str) or not s.strip() for s in symbols):
                raise PreparationError(f"model_fidelity.{field} must explicitly list its symbols")
            if len(set(symbols)) != len(symbols):
                raise PreparationError(f"model_fidelity.{field} contains duplicate symbols")
        if not fidelity["defined"] and not fidelity["empirically_identified"]:
            raise PreparationError("model_fidelity must name at least one symbol")
        if set(fidelity["defined"]) & set(fidelity["empirically_identified"]):
            raise PreparationError("model symbols cannot occupy both fidelity classes")
        if claim.get("disclaimer") != DISCLAIMER:
            raise PreparationError("the exact INV-4 disclaimer is required")
        normalized.append({"english_claim": english, "lean_theorem": names[0],
                           "nonvacuity_obligation": names[1], "model_fidelity": fidelity,
                           "disclaimer": DISCLAIMER})
        if names[0] not in theorems:
            theorems.append(names[0])
        if names[1] not in witnesses:
            witnesses.append(names[1])
    return normalized, theorems, witnesses


def load_alignment_helper(root: Path) -> tuple[Callable, dict]:
    path = regular_path(root / "RESEARCH_PIPELINE_v2/engine3_align_challenge.py")
    helper_bytes = path.read_bytes()
    spec = importlib.util.spec_from_file_location("viridis_existing_engine3_alignment", path)
    if spec is None or spec.loader is None:
        raise PreparationError("existing alignment helper is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.align_challenge, {"path": str(path), "sha256": digest(helper_bytes)}


def note_lines(run_id: str, source: Path, source_hash: str, claims: list[dict], targets: list[str]) -> list[str]:
    lines = [f"Methods Note — {run_id}", CONJECTURE,
             "Preparation only. Private Comparator verification is pending.",
             f"Source: {source}", f"Source SHA-256: {source_hash}",
             "Declared targets: " + ", ".join(targets)]
    for index, claim in enumerate(claims, 1):
        lines.extend([f"Claim {index}: {claim['english_claim']}",
                      f"Lean declaration: {claim['lean_theorem']}",
                      f"Inhabitation/non-vacuity obligation: {claim['nonvacuity_obligation']}",
                      "Defined symbols: " + (", ".join(claim['model_fidelity']['defined']) or "none declared"),
                      "Empirically identified symbols: " + (", ".join(claim['model_fidelity']['empirically_identified']) or "none declared")])
    return lines + [DISCLAIMER, "No empirical validation, certificate, DOI, or Canon admission is conferred by this note."]


def tex_bytes(lines: list[str]) -> bytes:
    escape = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
              "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    def escaped(value: str) -> str:
        return "".join(escape.get(char, char) for char in value)
    body = "\n\n".join(escaped(line) + r"\par" for line in lines)
    return (r"\documentclass[10pt]{article}" + "\n" + r"\usepackage[utf8]{inputenc}" + "\n"
            + r"\usepackage[margin=0.6in]{geometry}" + "\n" + r"\pagestyle{empty}" + "\n"
            + r"\begin{document}" + "\n" + body + "\n" + r"\end{document}" + "\n").encode("utf-8")


def methods_pdf(lines: list[str]) -> bytes:
    """One-page deterministic PDF; dependency failure is a HOLD, never installation."""
    try:
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as exc:
        raise PreparationError("reportlab is unavailable; Methods Note envelope remains HOLD") from exc
    fonts = [Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
             Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]
    font_path = next((p for p in fonts if p.is_file()), None)
    if font_path is None:
        raise PreparationError("Unicode PDF font unavailable; cannot print model symbols faithfully")
    font_name = "ViridisTrackBMethodsNote"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=letter, invariant=1, pageCompression=1)
    canvas.setTitle(lines[0])
    canvas.setAuthor("Viridis Methods Note preparer (untrusted)")
    canvas.setFont(font_name, 9)
    width, height = letter
    x, y = 36, height - 36
    def wrap(text: str) -> list[str]:
        output, pending = [], ""
        for char in text:
            if pending and pdfmetrics.stringWidth(pending + char, font_name, 9) > width - 72:
                output.append(pending)
                pending = char
            else:
                pending += char
        return output + [pending]
    for line in lines:
        for part in wrap(line):
            if y < 36:
                raise PreparationError("Methods Note exceeds one page; explicit shorter claim metadata required")
            canvas.drawString(x, y, part)
            y -= 12
        y -= 4
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def command_plan(root: Path, destination: Path) -> list[list[str]]:
    scripts = root / "RESEARCH_PIPELINE_v2"
    return [[sys.executable, str(scripts / "comparator_cloud_lean_verifier.py"),
             "--request", str(destination / "ENGINE3_VERIFICATION_REQUEST.json"),
             "--formal-statement", str(destination / "VERIFICATION_CHALLENGE_ALIGNED.lean"),
             "--candidate", str(destination / "VERIFICATION_CANDIDATE.lean"),
             "--output", str(destination / "COMPARATOR_CLOUD_RECEIPT.json")],
            [sys.executable, str(scripts / "issue_lean_zero_sorry_certificate.py"),
             "--request", str(destination / "ENGINE3_VERIFICATION_REQUEST.json"),
             "--cloud-receipt", str(destination / "COMPARATOR_CLOUD_RECEIPT.json"),
             "--output", str(destination / "LEAN_ZERO_SORRY_CERTIFICATE.json")]]


def prepare(*, source: Path, claim_binding: Path, run_id: str, root: Path,
            out: Path, enforce: bool = False, pdf_writer: Callable[[list[str]], bytes] | None = None,
            scanner: Callable[[Path], dict] | None = None) -> dict[str, Any]:
    if re.fullmatch(r"Run-9[0-9]{2}", run_id) is None:
        raise PreparationError("Track B requires an explicit reserved ID Run-900 through Run-999")
    root = root.absolute()
    source = regular_path(source)
    claim_binding = regular_path(claim_binding)
    if source.suffix != ".lean" or not source.is_relative_to(root):
        raise PreparationError("source must be a Lean file inside the explicitly selected canonical root")
    destination = regular_path(out / run_id, must_exist=False)
    if destination.exists():
        raise PreparationError("immutable destination already exists; preserve it")
    if (root / "RESEARCH_PIPELINE_v2/lean_certificates" / run_id).exists():
        raise PreparationError("reserved run ID already exists in the canonical certificate store")
    for name in ("comparator_cloud_lean_verifier.py", "issue_lean_zero_sorry_certificate.py"):
        regular_path(root / "RESEARCH_PIPELINE_v2" / name)
    raw = source.read_bytes()
    binding_raw = claim_binding.read_bytes()
    # Avoid a second promotion of bytes already represented by an issued
    # certificate. A matching recorded binding is enough to hold preparation;
    # it is not accepted here as proof or a valid certificate.
    store = root / "RESEARCH_PIPELINE_v2/lean_certificates"
    for path in sorted(store.glob("Run-*/LEAN_ZERO_SORRY_CERTIFICATE.json")):
        recorded = read_object(regular_path(path).read_bytes(), "recorded certificate")
        proof = recorded.get("bindings", {}).get("candidate_proof", {})
        if isinstance(proof, dict) and proof.get("sha256") == digest(raw):
            raise PreparationError("source bytes already have a recorded certificate; consult the corpus ledger")
    if scanner is None:
        from static_pregate import scan
        scanner = scan
    triage = scanner(source)
    if not isinstance(triage, dict) or triage.get("static_pass") is not True:
        raise PreparationError("source is not CLEAN_UNCERTIFIED; static failure is quarantined from Track B")
    if triage.get("sha256") != digest(raw):
        raise PreparationError("source changed during static triage")
    if triage.get("has_sorry") or triage.get("has_sorryAx") or triage.get("unexpected_axioms"):
        raise PreparationError("incomplete or unsound sources cannot enter Track B")
    if triage.get("status") in {"CERTIFIED", "UNSOUND", "HAS_SORRY", "DEBT"}:
        raise PreparationError("source is not eligible CLEAN_UNCERTIFIED input")
    declarations = triage.get("decls")
    if not isinstance(declarations, list) or not declarations:
        raise PreparationError("source has no declared theorem/lemma targets")
    claims, claimed_theorems, witnesses = explicit_claims(read_object(binding_raw, "claim_binding"), declarations)
    targets = list(dict.fromkeys(claimed_theorems + witnesses))
    align, helper_binding = load_alignment_helper(root)
    # Reuse the existing freezer: no source edits, invented signatures or helper proofs.
    challenge, signatures = align(raw.decode("utf-8"), raw.decode("utf-8"), targets)
    challenge_raw = challenge.encode("utf-8")
    result = {"standard": "VRS-TRACK-B-METHODS-NOTE-PREPARATION-1",
              "mode": "ENFORCING" if enforce else "REPORT_ONLY", "status": "DEBT",
              "preparation_status": "PLAN_READY", "source_classification": "CLEAN_UNCERTIFIED",
              "run_id": run_id, "canonical_tree": str(root), "destination": str(destination),
              "source": {"path": str(source), "sha256": digest(raw)},
              "claim_binding": {"path": str(claim_binding), "sha256": digest(binding_raw)},
              "alignment_helper": helper_binding, "expected_theorem_names": targets,
              "nonvacuity_obligations": witnesses, "signature_sha256": signatures,
              "certified": False, "local_lean_execution": False, "transport_performed": False,
              "transport_authorization_required": True, "external_mutation": False,
              "command_plan": command_plan(root, destination)}
    if not enforce:
        return result
    lines = note_lines(run_id, source, digest(raw), claims, targets)
    pdf = (pdf_writer or methods_pdf)(lines)
    if not isinstance(pdf, bytes) or not pdf.startswith(b"%PDF-") or b"%%EOF" not in pdf[-1024:]:
        raise PreparationError("Methods Note PDF writer returned invalid bytes")
    payloads = {"VERIFICATION_CANDIDATE.lean": raw, "VERIFICATION_STATEMENT.lean": challenge_raw,
                "VERIFICATION_CHALLENGE_ALIGNED.lean": challenge_raw, "claim_binding.json": json_bytes({"claims": claims}),
                "SEALED_paper.tex": tex_bytes(lines), "SEALED_paper.pdf": pdf}
    payloads["SEALED_CLAIM_INVENTORY.json"] = json_bytes({
        "schema_version": "VRS-TRACK-B-CLAIM-INVENTORY-1", "artifact_kind": "METHODS_NOTE",
        "verification_status": "PENDING_COMPARATOR", "claims": [
            {**claim, "claim": claim["english_claim"], "evidence_class": "FORMAL_TARGET", "verification_status": "PENDING_COMPARATOR",
             "empirical_content": {"evidence_class": "DEFERRED", "symbols": claim["model_fidelity"]["empirically_identified"]}}
            for claim in claims]})
    def bound(name: str) -> dict:
        return {"path": str(destination / name), "sha256": digest(payloads[name])}
    payloads["STATEMENT_ALIGNMENT.json"] = json_bytes({
        "schema_version": 1, "standard": ALIGNMENT_STANDARD, "status": "FROZEN",
        "operation": "unchanged helper replaces supplied target proof bodies with sorry",
        "sealed_statement": bound("VERIFICATION_STATEMENT.lean"), "candidate": bound("VERIFICATION_CANDIDATE.lean"),
        "aligned_challenge": bound("VERIFICATION_CHALLENGE_ALIGNED.lean"), "expected_theorem_names": targets,
        "signature_sha256": signatures, "target_signatures_match_sealed_statement": True,
        "candidate_forbidden_constructs_empty": True, "introduced_sorry_count": len(targets),
        "local_lean_execution": False, "external_mutation": False})
    payloads["CANDIDATE_AUTHORSHIP.json"] = json_bytes({
        "schema_version": "VRS-CODEX-CANDIDATE-AUTHORSHIP-1", "author": "CODEX",
        "author_role": "UNTRUSTED_ENVELOPE_PREPARER", "original_source_authorship": "PRESERVED_NOT_REATTRIBUTED",
        "run": run_id, "scientific_target_signatures_changed": False,
        "source": result["source"], "claim_binding": result["claim_binding"],
        "verification_status": "PENDING_ALIGNED_PRIVATE_COMPARATOR", "local_lean_execution": False})
    payloads["SEALED_RUN_MANIFEST.json"] = json_bytes({
        "schema_version": "VRS-TRACK-B-METHODS-NOTE-MANIFEST-1", "run_id": run_id,
        "artifact_kind": "METHODS_NOTE", "canonical_tree": str(root), "source": result["source"],
        "claim_binding": result["claim_binding"], "alignment_helper": helper_binding,
        "verification_status": "PENDING_COMPARATOR", "artifact_sha256": {n: digest(b) for n, b in payloads.items()},
        "expected_theorem_names": targets, "nonvacuity_obligations": witnesses,
        "toolchain": TOOLCHAIN, "mathlib_rev": MATHLIB_REV,
        "local_lean_execution": False, "certificate_issued": False})
    request = {"schema_version": "3.0", "source_run": run_id, "request_kind": "LEAN_PROOF",
               "candidate_id": f"{run_id}-MethodsNote-{digest(raw)[:12]}", "module": run_id.replace("-", ""),
               "primary_verifier": "COMPARATOR_CLOUD", "toolchain": TOOLCHAIN, "mathlib_rev": MATHLIB_REV,
               "permitted_axioms": PERMITTED_AXIOMS, "permitted_sorries": [], "aristotle_required": False,
               "local_lean_execution": False, "local_lean_fallback_authorized": False,
               "expected_theorem_names": targets, "nonvacuity_obligations": witnesses,
               "input_sha256": {name: digest(data) for name, data in payloads.items()},
               "statement_contract_sha256": digest(challenge_raw),
               "statement_alignment": {"standard": ALIGNMENT_STANDARD,
                   "sealed_statement": {"filename": "VERIFICATION_STATEMENT.lean", "sha256": digest(challenge_raw)},
                   "receipt": {"filename": "STATEMENT_ALIGNMENT.json", "sha256": digest(payloads["STATEMENT_ALIGNMENT.json"])}},
               "candidate_authorship_binding": {"author": "CODEX", "receipt": "CANDIDATE_AUTHORSHIP.json"},
               "canonical_output_bindings": {"certificate_directory": str(destination),
                   "cloud_receipt": str(destination / "COMPARATOR_CLOUD_RECEIPT.json"),
                   "certificate": str(destination / "LEAN_ZERO_SORRY_CERTIFICATE.json")},
               "status": "FROZEN_PENDING_TRANSPORT_AUTHORIZATION"}
    if not SEALED_NAMES.issubset(request["input_sha256"]):
        raise PreparationError("complete sealed-input set is missing")
    payloads["ENGINE3_VERIFICATION_REQUEST.json"] = json_bytes(request)
    # Recheck immediately before any output mutation. Preserve an incomplete
    # destination if an I/O error occurs; it is a HOLD, never a resumable pass.
    if source.read_bytes() != raw or claim_binding.read_bytes() != binding_raw:
        raise PreparationError("source or claim binding changed before freezing")
    regular_path(destination, must_exist=False)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    for name, data in payloads.items():  # Request was added last.
        descriptor = os.open(destination / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    result.update(preparation_status="FROZEN_PENDING_COMPARATOR", envelope_written=True,
                  request=str(destination / "ENGINE3_VERIFICATION_REQUEST.json"),
                  envelope_sha256={name: digest(data) for name, data in payloads.items()})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--claim-binding", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=CANONICAL_ROOT)
    parser.add_argument("--out", required=True, type=Path, help="Parent directory for immutable Run-NNN envelope")
    parser.add_argument("--enforce", action="store_true", help="Freeze envelope only; never transmit or certify")
    args = parser.parse_args(argv)
    try:
        result = prepare(source=args.source, claim_binding=args.claim_binding, run_id=args.run_id,
                         root=args.root, out=args.out, enforce=args.enforce)
        code = 0
    except Exception as exc:
        result = {"status": "HOLD", "certified": False, "mode": "ENFORCING" if args.enforce else "REPORT_ONLY",
                  "reasons": [f"{type(exc).__name__}: {exc}"], "local_lean_execution": False,
                  "transport_performed": False, "external_mutation": False}
        code = 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
