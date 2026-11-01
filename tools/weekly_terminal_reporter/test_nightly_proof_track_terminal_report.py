import json
import hashlib
from pathlib import Path

from nightly_proof_track_terminal_report import (
    assert_report_output_is_mutable,
    canonical_run_id,
    evaluate,
    saturday_report,
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def bind(path: Path) -> dict:
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fixture(tmp_path: Path) -> tuple[Path, Path]:
    control = tmp_path / "control"
    live = tmp_path / "live"
    run = "Run-130_seed-source"
    (live / "07_nightly_engine/compound research papers" / run).mkdir(parents=True)
    (live / "07_nightly_engine/compound research papers" / run / "RUN_MANIFEST.json").write_text("{}", encoding="utf-8")
    write_json(live / "07_nightly_engine/viridis-science-agent/nightly/NIGHTLY_STATE.json", {"current_run": 130})
    (control / "science-engine/07_nightly_engine/compound research papers" / run).mkdir(parents=True)
    write_json(control / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts/Run-130.json", {"status": "MIRRORED"})
    write_json(control / "RESEARCH_PIPELINE_v2/nightly_packages/Run-130/QUALITY_GATE.json", {"quality_verdict": "HOLD", "saturday_status": "EXCLUDE_HOLD"})
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {"active": None, "history": []})
    return control, live


def test_canonical_run_id():
    assert canonical_run_id("Run-130_seed-source") == "Run-130"


def test_sealed_saturday_report_cannot_be_overwritten(tmp_path):
    packet = tmp_path / "saturday_packets" / "2026-08-15"
    packet.mkdir(parents=True)
    output = packet / "PROOF_TRACK_STATUS.json"
    write_json(packet / "SATURDAY_PACKAGE_MANIFEST.json", {"state": "SEALED"})
    try:
        assert_report_output_is_mutable(output)
    except RuntimeError as exc:
        assert "sealed Saturday packet is immutable" in str(exc)
    else:
        raise AssertionError("sealed packet overwrite was not rejected")


def test_unsealed_saturday_report_remains_writable(tmp_path):
    output = tmp_path / "saturday_packets" / "2026-08-22" / "PROOF_TRACK_STATUS.json"
    assert_report_output_is_mutable(output)


def test_missing_request_is_visible_even_when_paper_is_held(tmp_path):
    control, live = fixture(tmp_path)
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_MISSING_FROZEN_PROOF_REQUEST"
    assert status["paper_quality_verdict"] == "HOLD"


def test_bound_significance_hold_does_not_cancel_proof_obligation(tmp_path):
    control, live = fixture(tmp_path)
    correction = control / "RESEARCH_PIPELINE_v2/pre_aristotle_corrections/Run-130_example-r1"
    receipt = correction / "CORRECTION_RECEIPT.json"
    manifest = control / "RESEARCH_PIPELINE_v2/nightly_packages/Run-130/PAPER_PACKAGE_MANIFEST.json"
    write_json(receipt, {"run_id": "Run-130"})
    write_json(correction / "SIGNIFICANCE_SCREEN_HOLD.json", {
        "verdict": "HOLD_SIGNIFICANCE_NONTRIVIALITY_NOT_INDEPENDENTLY_CLEARED"
    })
    write_json(manifest, {"pre_aristotle_correction": {"path": str(receipt)}})
    write_json(control / "RESEARCH_PIPELINE_v2/nightly_packages/Run-130/QUALITY_GATE.json", {
        "quality_verdict": "PASS",
        "saturday_status": "HOLD_ARISTOTLE",
        "manifest_path": str(manifest),
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_MISSING_FROZEN_PROOF_REQUEST"
    assert status["significance_gate_status"] == "HOLD_SIGNIFICANCE_NONTRIVIALITY_NOT_INDEPENDENTLY_CLEARED"
    assert "hash-bound Engine-3 Lean statement" in status["next_action"]
    report = saturday_report(["130"], "2026-08-15", control_root=control, live_root=live)
    assert report["all_runs_have_frozen_request"] is False


def test_direct_request_surfaces_audited_significance_hold(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    audit = request.parent / "FORGE_AUDIT.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-target",
        "significance_status": "HOLD_SIGNIFICANCE_NONTRIVIALITY_NOT_INDEPENDENTLY_CLEARED",
    })
    write_json(audit, {
        "evidence": {
            "significance": {
                "verdict": "HOLD_SIGNIFICANCE_NONTRIVIALITY_NOT_INDEPENDENTLY_CLEARED"
            }
        }
    })
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{
            "request_path": str(request),
            "audit_path": str(audit),
            "status": "AUDIT_FAILED_TERMINAL",
            "failed_checks": ["statement_freeze_pass"],
        }],
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "AUDIT_FAILED_TERMINAL"
    assert status["significance_gate_status"] == (
        "HOLD_SIGNIFICANCE_NONTRIVIALITY_NOT_INDEPENDENTLY_CLEARED"
    )
    assert "deliberately reformulate" in status["next_action"]


def test_ready_request_is_not_hidden_by_paper_hold(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {"source_run": "Run-130", "candidate_id": "Run-130-target"})
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_ENGINE3_MIGRATION_REQUIRED"


def test_engine3_request_routes_directly_to_comparator(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "science-engine/07_nightly_engine/compound research papers/Run-130_seed-source/formalization/ENGINE3_VERIFICATION_REQUEST.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-Comparator-attempt-1",
        "request_kind": "LEAN_PROOF",
        "primary_verifier": "COMPARATOR_CLOUD",
        "aristotle_required": False,
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "READY_FOR_COMPARATOR_CERTIFICATION"
    assert status["request_paths"] == [str(request)]


def test_engine3_certificate_outranks_terminal_legacy_formalization(tmp_path):
    control, live = fixture(tmp_path)
    legacy = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130-legacy/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(legacy, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-PaperFormalization-attempt-1",
        "request_kind": "PAPER_TO_LEAN_FORMALIZATION",
    })
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{"request_path": str(legacy), "status": "AUDIT_FAILED_TERMINAL"}],
    })
    cert_root = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-130"
    request = cert_root / "ENGINE3_VERIFICATION_REQUEST.json"
    receipt = cert_root / "COMPARATOR_CLOUD_RECEIPT.json"
    statement = cert_root / "VERIFICATION_STATEMENT.lean"
    candidate = cert_root / "VERIFICATION_CANDIDATE.lean"
    sealed = cert_root / "SEALED_paper.pdf"
    write_json(request, {"source_run": "Run-130", "request_kind": "LEAN_PROOF"})
    write_json(receipt, {"status": "VERIFIED"})
    statement.parent.mkdir(parents=True, exist_ok=True)
    statement.write_text("theorem frozen : True := by trivial\n", encoding="utf-8")
    candidate.write_text("theorem frozen : True := by trivial\n", encoding="utf-8")
    sealed.write_bytes(b"paper")
    write_json(cert_root / "LEAN_ZERO_SORRY_CERTIFICATE.json", {
        "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
        "status": "LEAN_ZERO_SORRY_CERTIFIED",
        "run_id": "Run-130",
        "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
        "bindings": {
            "request": bind(request),
            "independent_cloud_receipt": bind(receipt),
            "formal_statement": bind(statement),
            "candidate_proof": bind(candidate),
            "sealed_paper_inputs": {"SEALED_paper.pdf": bind(sealed)},
        },
    })

    status = evaluate(130, control_root=control, live_root=live)

    assert status["proof_status"] == "LEAN_ZERO_SORRY_CERTIFIED"
    assert status["lean_certificate"]["status"] == "LEAN_ZERO_SORRY_CERTIFIED"
    assert status["paper_saturday_status"] == "EXCLUDE_HOLD"
    write_json(control / "RESEARCH_PIPELINE_v2/nightly_packages/Run-130/QUALITY_GATE.json", {
        "quality_verdict": "PASS", "saturday_status": "HOLD_ARISTOTLE"})
    status = evaluate(130, control_root=control, live_root=live)
    assert status["paper_saturday_status"] == "HOLD_RECONCILIATION"
    assert "later independent review" in status["next_action"]


def test_paper_to_lean_request_is_not_mislabeled_as_verified_proof(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-PaperFormalization-attempt-1",
        "request_kind": "PAPER_TO_LEAN_FORMALIZATION",
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_ENGINE3_MIGRATION_REQUIRED"
    assert status["request_kinds"] == ["PAPER_TO_LEAN_FORMALIZATION"]


def test_audited_formalization_return_still_is_not_verified_proof(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130-formalization/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-PaperFormalization-attempt-1",
        "request_kind": "PAPER_TO_LEAN_FORMALIZATION",
    })
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{"request_path": str(request), "status": "AUDITED_VERIFIED"}],
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_PROOF_REQUEST_NOT_STAGED"


def test_separate_proof_request_advances_after_formalization_contract_audit(tmp_path):
    control, live = fixture(tmp_path)
    formalization = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130-formalization/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    proof = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130-proof/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    audit = formalization.parent / "FORGE_AUDIT.json"
    write_json(formalization, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-PaperFormalization-attempt-1",
        "request_kind": "PAPER_TO_LEAN_FORMALIZATION",
    })
    write_json(proof, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-Proof-attempt-1",
        "request_kind": "LEAN_PROOF",
    })
    write_json(audit, {"formalization_contract_pass": True, "proof_certificate": False})
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{
            "request_path": str(formalization),
            "audit_path": str(audit),
            "status": "AUDIT_FAILED_TERMINAL",
        }],
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_ENGINE3_MIGRATION_REQUIRED"
    assert status["request_kinds"] == ["LEAN_PROOF", "PAPER_TO_LEAN_FORMALIZATION"]


def test_active_request_is_matched_by_resolved_path(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {"source_run": "Run-130", "candidate_id": "Run-130-target"})
    alternate = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/../attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": {"request_path": str(alternate), "status": "RUNNING"}, "history": []
    })
    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "HOLD_ENGINE3_MIGRATION_REQUIRED"
    assert "Engine-3" in status["next_action"]


def test_provider_warning_is_certificate_debt_not_a_pass(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-warning",
        "request_kind": "LEAN_PROOF",
    })
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{
            "request_path": str(request),
            "status": "PROOF_GATE_ACCEPTED_ZERO_SORRY_PROVIDER_WARNING",
        }],
    })

    status = evaluate(130, control_root=control, live_root=live)

    assert status["proof_status"] == "HOLD_CLEAN_CERTIFICATE_REQUIRED"
    assert "fresh exact-source Engine-3 candidate" in status["next_action"]
    assert "Comparator" in status["next_action"]


def test_aristotle_audit_without_independent_certificate_remains_debt(tmp_path):
    control, live = fixture(tmp_path)
    request = control / "RESEARCH_PIPELINE_v2/aristotle_submissions/Run-130/attempt-1/ARISTOTLE_FORGE_REQUEST.json"
    write_json(request, {
        "source_run": "Run-130",
        "candidate_id": "Run-130-clean",
        "request_kind": "LEAN_PROOF",
    })
    write_json(control / "RESEARCH_PIPELINE_v2/aristotle_forge_state.json", {
        "active": None,
        "history": [{"request_path": str(request), "status": "AUDITED_VERIFIED"}],
    })

    status = evaluate(130, control_root=control, live_root=live)

    assert status["proof_status"] == "HOLD_INDEPENDENT_CLOUD_CERTIFICATE_REQUIRED"
    assert "independent cloud Lean verification" in status["next_action"]


def test_engine3_certificate_accepts_control_relative_bindings(tmp_path):
    control, live = fixture(tmp_path)
    cert_root = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-130"
    request = cert_root / "ENGINE3_VERIFICATION_REQUEST.json"
    receipt = cert_root / "COMPARATOR_CLOUD_RECEIPT.json"
    statement = cert_root / "VERIFICATION_STATEMENT.lean"
    candidate = cert_root / "VERIFICATION_CANDIDATE.lean"
    sealed = cert_root / "SEALED_paper.pdf"
    write_json(request, {"source_run": "Run-130", "request_kind": "LEAN_PROOF"})
    write_json(receipt, {"status": "VERIFIED"})
    statement.write_text("theorem frozen : True := by trivial\n", encoding="utf-8")
    candidate.write_text("theorem frozen : True := by trivial\n", encoding="utf-8")
    sealed.write_bytes(b"paper")

    def relative_binding(path):
        return {
            "path": str(path.relative_to(control / "RESEARCH_PIPELINE_v2")),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    write_json(cert_root / "LEAN_ZERO_SORRY_CERTIFICATE.json", {
        "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1",
        "status": "LEAN_ZERO_SORRY_CERTIFIED",
        "run_id": "Run-130",
        "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
        "bindings": {
            "request": relative_binding(request),
            "independent_cloud_receipt": relative_binding(receipt),
            "formal_statement": relative_binding(statement),
            "candidate_proof": relative_binding(candidate),
            "sealed_paper_inputs": {"SEALED_paper.pdf": relative_binding(sealed)},
        },
    })

    status = evaluate(130, control_root=control, live_root=live)
    assert status["proof_status"] == "LEAN_ZERO_SORRY_CERTIFIED"


# Added successor tests. Synthetic positive cases exercise reporter joins and
# precedence ONLY. They do not authenticate c131's fixed private 0c03 receipt.
import shutil

import pytest
import nightly_proof_track_terminal_report as terminal_report


def _generated_mirrored_run(control, live, run_id):
    name = f"{run_id}_synthetic-reporter-only"
    write_json(live / terminal_report.RUNS_REL / name / "RUN_MANIFEST.json", {"synthetic": True})
    mirror = control / "science-engine" / terminal_report.RUNS_REL / name
    mirror.mkdir(parents=True, exist_ok=True)
    write_json(control / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts" / f"{run_id}.json",
               {"status": "MIRRORED"})
    return mirror


def _synthetic_reporter_context(tmp_path, monkeypatch):
    """No private science bytes, fixed receipt forgery, or trust-map substitution."""
    control, live = fixture(tmp_path)
    run_id = "Run-194"
    mirror = _generated_mirrored_run(control, live, run_id)
    package = control / "RESEARCH_PIPELINE_v2/nightly_packages" / run_id
    manifest = package / "PAPER_PACKAGE_MANIFEST.json"
    write_json(manifest, {"synthetic_reporter_logic_only": True})
    write_json(package / "QUALITY_GATE.json", {"quality_verdict": "HOLD", "saturday_status": "EXCLUDE_HOLD"})
    folder = control / "RESEARCH_PIPELINE_v2/lean_certificates" / run_id
    folder.mkdir(parents=True)
    documents = {
        "SEALED_RUN_MANIFEST.json": manifest.read_bytes(),
        "SEALED_CLAIM_INVENTORY.json": b'{"synthetic_reporter_logic_only":true}',
        "SEALED_paper.tex": b"synthetic reporter fixture; no scientific claim\n",
        "VERIFICATION_STATEMENT.lean": b"synthetic reporter bytes; not a Lean proof\n",
        "VERIFICATION_CANDIDATE.lean": b"synthetic reporter candidate; never executed\n",
    }
    for name, data in documents.items():
        (folder / name).write_bytes(data)
    source = {
        "source_run": run_id, "candidate_id": "synthetic-report-object",
        "request_kind": "LEAN_PROOF", "primary_verifier": "COMPARATOR_CLOUD",
        "aristotle_required": False,
        "significance_status": "HOLD_SIGNIFICANCE_SYNTHETIC_REPORTER_ONLY",
        "input_sha256": {"PAPER_PACKAGE_MANIFEST.json": bind(manifest)["sha256"]},
    }
    source_path = folder / "SOURCE_ENGINE3_REQUEST.json"
    write_json(source_path, source)
    mirror_path = mirror / "formalization/ENGINE3_VERIFICATION_REQUEST.json"
    mirror_path.parent.mkdir()
    mirror_path.write_bytes(source_path.read_bytes())
    stage_path = folder / "ENGINE3_VERIFICATION_REQUEST.json"
    write_json(stage_path, {
        "source_run": run_id, "candidate_id": source["candidate_id"],
        "synthetic_staged_wrapper": True, "local_lean_execution": False,
        "input_sha256": {
            "SOURCE_ENGINE3_REQUEST.json": bind(source_path)["sha256"],
            **{name: bind(folder / name)["sha256"] for name in documents},
        },
    })
    context = {
        "evidence": {
            "run_id": run_id, "status": "TERMINAL_PREMISE_HOLD",
            "request_sha256": bind(stage_path)["sha256"],
            "receipt_sha256": "SYNTHETIC_REPORTER_LOGIC_ONLY_NOT_0c03_AUTHENTICATION",
            "certifies": False, "clears_certification_debt": False,
            "publication_admitted": False,
            "test_evidence_scope": "SYNTHETIC_REPORTER_LOGIC_ONLY",
        },
        "snapshots": {path: path.read_bytes() for path in [
            stage_path, manifest, *(folder / name for name in documents)]},
        "stage": stage_path, "folder": folder, "manifest": manifest,
    }
    monkeypatch.setattr(terminal_report, "_authenticated_terminal_context", lambda *_: context)
    return control, live, context, source_path, mirror_path


def _synthetic_current_certificate(control, context, *, other_request=False):
    folder = context["folder"]
    request = context["stage"]
    if other_request:
        request = folder / "OTHER_SYNTHETIC_REQUEST.json"
        write_json(request, {"source_run": "Run-194", "different_object": True})
    receipt = folder / "SYNTHETIC_CLOUD_RECEIPT.json"
    write_json(receipt, {"test_evidence_scope": "SYNTHETIC_REPORTER_LOGIC_ONLY"})
    path = folder / "LEAN_ZERO_SORRY_CERTIFICATE.json"
    write_json(path, {
        "standard": "VRS-LEAN-ZERO-SORRY-CERTIFICATE-1", "status": "LEAN_ZERO_SORRY_CERTIFIED",
        "run_id": "Run-194", "verification_standard": "VRS-COMPARATOR-DUAL-KERNEL-1",
        "test_evidence_scope": "SYNTHETIC_REPORTER_LOGIC_ONLY_NO_AUTHORITY",
        "bindings": {
            "request": bind(request), "independent_cloud_receipt": bind(receipt),
            "formal_statement": bind(folder / "VERIFICATION_STATEMENT.lean"),
            "candidate_proof": bind(folder / "VERIFICATION_CANDIDATE.lean"),
            "sealed_paper_inputs": {name: bind(folder / name) for name in (
                "SEALED_RUN_MANIFEST.json", "SEALED_CLAIM_INVENTORY.json", "SEALED_paper.tex")},
        },
    })
    return path


def test_synthetic_join_bridges_distinct_staged_and_source_hashes_without_scope_promotion(tmp_path, monkeypatch):
    control, live, context, source, mirror = _synthetic_reporter_context(tmp_path, monkeypatch)
    status = evaluate(194, control_root=control, live_root=live)
    evidence = status["terminal_evidence"]
    assert bind(context["stage"])["sha256"] != bind(source)["sha256"]
    assert evidence["lineage"]["source_and_reported_mirror_sha256"] == bind(mirror)["sha256"]
    assert status["proof_status"] == "TERMINAL_PREMISE_HOLD"
    assert evidence["original_proof_status"] == "READY_FOR_COMPARATOR_CERTIFICATION"
    assert status["paper_quality_verdict"] == "HOLD"
    assert status["paper_saturday_status"] == "EXCLUDE_HOLD"
    assert status["significance_gate_status"] == "HOLD_SIGNIFICANCE_SYNTHETIC_REPORTER_ONLY"
    assert status["request_paths"] == [str(mirror)]
    assert status["proof_required"] is True and status["external_mutation"] is False
    assert evidence["authenticated_terminal_evidence"]["test_evidence_scope"] == "SYNTHETIC_REPORTER_LOGIC_ONLY"
    assert evidence["certifies"] is False and evidence["clears_certification_debt"] is False
    assert evidence["publication_admitted"] is False and evidence["authorizes_retry_or_transport"] is False
    assert "authorizes no retry or transport" in status["next_action"]


@pytest.mark.parametrize("change", ["source", "mirror", "stage_snapshot", "source_manifest_key", "missing_package"])
def test_synthetic_unjoined_same_run_is_unresolved_not_inherited_hold_or_successor_ready(tmp_path, monkeypatch, change):
    control, live, context, source, mirror = _synthetic_reporter_context(tmp_path, monkeypatch)
    if change == "source":
        source.write_bytes(source.read_bytes() + b"\n")
    elif change == "mirror":
        mirror.write_bytes(mirror.read_bytes() + b"\n")
    elif change == "stage_snapshot":
        context["snapshots"][context["stage"]] += b"\n"
    elif change == "source_manifest_key":
        document = json.loads(source.read_bytes())
        document["input_sha256"] = {"SEALED_RUN_MANIFEST.json": bind(context["manifest"])["sha256"]}
        write_json(source, document)
        mirror.write_bytes(source.read_bytes())
        stage = json.loads(context["stage"].read_bytes())
        stage["input_sha256"]["SOURCE_ENGINE3_REQUEST.json"] = bind(source)["sha256"]
        write_json(context["stage"], stage)
        context["snapshots"][context["stage"]] = context["stage"].read_bytes()
        context["evidence"]["request_sha256"] = bind(context["stage"])["sha256"]
    else:
        context["manifest"].unlink()
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert status["terminal_evidence"]["diagnostic"]
    assert "lineage" not in status["terminal_evidence"]
    assert "authorizes no retry, transport, successor generation" in status["next_action"]


def test_synthetic_same_exact_object_certificate_retains_both_records_as_conflict(tmp_path, monkeypatch):
    control, live, context, _, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    certificate = _synthetic_current_certificate(control, context)
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_CONFLICT
    assert status["lean_certificate"]["path"] == str(certificate)
    assert status["terminal_evidence"]["authenticated_terminal_evidence"]["status"] == "TERMINAL_PREMISE_HOLD"
    assert status["terminal_evidence"]["current_certificate"]["sha256"] == bind(certificate)["sha256"]
    assert status["terminal_evidence"]["original_proof_status"] == "LEAN_ZERO_SORRY_CERTIFIED"
    assert "retain both" in status["next_action"]


def test_synthetic_same_run_unknown_certificate_linkage_is_unresolved_and_preserved(tmp_path, monkeypatch):
    control, live, context, _, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    certificate = _synthetic_current_certificate(control, context, other_request=True)
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert status["lean_certificate"]["path"] == str(certificate)
    assert status["terminal_evidence"]["selected_current_certificate"]["path"] == str(certificate)
    assert status["terminal_evidence"]["authenticated_terminal_evidence"]["status"] == "TERMINAL_PREMISE_HOLD"
    assert "same-run certificate object linkage unresolved" in status["terminal_evidence"]["diagnostic"]


def test_synthetic_source_reread_drift_cannot_be_promoted_to_terminal_currentness(tmp_path, monkeypatch):
    control, live, _, source, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    reader = terminal_report._terminal_bytes
    reads = 0

    def drift_on_reread(path):
        nonlocal reads
        if path == source:
            reads += 1
            if reads == 2:
                source.write_bytes(source.read_bytes() + b"\n")
        return reader(path)

    monkeypatch.setattr(terminal_report, "_terminal_bytes", drift_on_reread)
    status = evaluate(194, control_root=control, live_root=live)
    assert reads == 2
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert "read window" in status["terminal_evidence"]["diagnostic"] or "join window" in status["terminal_evidence"]["diagnostic"]
    assert "readbacks" not in status["terminal_evidence"]


@pytest.mark.parametrize("name", [
    "ENGINE3_VERIFICATION_REQUEST.json", "VERIFICATION_STATEMENT.lean",
    "VERIFICATION_CANDIDATE.lean", "SEALED_RUN_MANIFEST.json",
    "SEALED_CLAIM_INVENTORY.json", "SEALED_paper.tex", "selected_package",
])
def test_synthetic_each_staged_input_and_selected_package_must_survive_join_reread(tmp_path, monkeypatch, name):
    control, live, context, _, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    target = context["manifest"] if name == "selected_package" else context["folder"] / name
    target.write_bytes(target.read_bytes() + b"\n")
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert "join window" in status["terminal_evidence"]["diagnostic"]


def test_synthetic_source_read_uncertainty_is_preserved_as_unresolved(tmp_path, monkeypatch):
    control, live, _, source, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    reader = terminal_report._terminal_bytes

    def unreadable(path):
        if path == source:
            raise PermissionError("synthetic SOURCE read uncertainty")
        return reader(path)

    monkeypatch.setattr(terminal_report, "_terminal_bytes", unreadable)
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert "PermissionError: synthetic SOURCE read uncertainty" == status["terminal_evidence"]["diagnostic"]


@pytest.mark.parametrize("missing", ["generated", "mirrored"])
def test_synthetic_terminal_detail_does_not_hide_generation_or_mirror_debt(tmp_path, monkeypatch, missing):
    control, live, _, _, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    if missing == "generated":
        run = terminal_report.find_run(live / terminal_report.RUNS_REL, "Run-194")
        (run / "RUN_MANIFEST.json").unlink()
        expected = "NOT_GENERATED"
    else:
        write_json(control / "RESEARCH_PIPELINE_v2/nightly_mirror_receipts/Run-194.json", {"status": "WAITING"})
        expected = "WAITING_FOR_MIRROR"
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == expected
    assert status["terminal_evidence"]["status"] == "TERMINAL_PREMISE_HOLD"
    assert status["terminal_evidence"]["original_proof_status"] == expected


def _install_fixed_public_helper(control):
    """Future admitted CI must materialize this finite, public-only data closure.

    Missing sources fail this test; there is no ambient Core fallback. The
    source/action packet binds all four files. No private receipt is copied.
    """
    source_root = Path(__file__).with_name("terminal_report_public_sources")
    sources = {
        "RESEARCH_PIPELINE_v2/verification_coverage_gates/terminal_certification/terminal_hold.py": terminal_report.TERMINAL_HELPER_SHA256,
        "RESEARCH_PIPELINE_v2/verification_coverage_gates/premise_declaration.py": "e00404ad578efa7dcd9299a5d947be594f36c15e53fd44479d22d578caab5137",
        "RESEARCH_PIPELINE_v2/verification_coverage_gates/inv9_title_basis.py": "5c9981fe2536a6cde3c8a1d2e7cdc9684c1369aeb145be4fda635c8af8dfec81",
        "RESEARCH_PIPELINE_v2/engine3_align_challenge.py": "d8d06e582d80bddae73dbb68a23a866ed8cac241f5c9780c3bc779a50fcd4870",
    }
    for relative, expected in sources.items():
        source = source_root / relative
        assert source.is_file(), f"required public fixture closure is absent: {relative}"
        assert bind(source)["sha256"] == expected, f"public fixture source pin mismatch: {relative}"
        destination = control / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return control / "RESEARCH_PIPELINE_v2/verification_coverage_gates/terminal_certification/terminal_hold.py"


@pytest.mark.parametrize("receipt", ["missing", "malformed", "different_bytes"])
def test_real_fixed_c131_missing_or_corrupt_receipt_returns_none_and_reporter_holds(tmp_path, receipt):
    control, live = fixture(tmp_path)
    _generated_mirrored_run(control, live, "Run-194")
    _install_fixed_public_helper(control)
    package = control / "RESEARCH_PIPELINE_v2/nightly_packages/Run-194"
    package.mkdir(parents=True)
    folder = control / "RESEARCH_PIPELINE_v2/lean_certificates/Run-194"
    folder.mkdir(parents=True)
    if receipt != "missing":
        (folder / terminal_report.TERMINAL_RECEIPTS["Run-194"][0]).write_bytes(
            b"{" if receipt == "malformed" else b'{"not_the_trusted_receipt":true}')
    helper, _, _ = terminal_report._load_terminal_helper(control)
    assert helper.terminal_hold(package, folder.parent) is None
    with pytest.raises(ValueError, match="unchanged terminal helper did not authenticate"):
        terminal_report._authenticated_terminal_context(control, package)
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert "unchanged terminal helper did not authenticate" in status["terminal_evidence"]["diagnostic"]
    assert "authenticated_terminal_evidence" not in status["terminal_evidence"]


def test_real_helper_own_source_drift_is_unresolved_without_importing_drifted_bytes(tmp_path):
    control, live = fixture(tmp_path)
    _generated_mirrored_run(control, live, "Run-194")
    helper_path = _install_fixed_public_helper(control)
    helper_path.write_bytes(helper_path.read_bytes() + b"\n# disposable drift control\n")
    status = evaluate(194, control_root=control, live_root=live)
    assert status["proof_status"] == terminal_report.TERMINAL_UNRESOLVED
    assert "terminal helper source pin mismatch" in status["terminal_evidence"]["diagnostic"]


@pytest.mark.parametrize("name", ["premise_declaration.py", "inv9_title_basis.py", "engine3_align_challenge.py"])
def test_real_c131_checker_source_pin_negative_without_private_positive_authentication(tmp_path, name):
    control, _ = fixture(tmp_path)
    _install_fixed_public_helper(control)
    helper, _, _ = terminal_report._load_terminal_helper(control)
    sources = helper._checker_sources()
    target = next(path for path in sources if path.name == name)
    target.write_bytes(target.read_bytes() + b"\n# disposable source pin negative\n")
    with pytest.raises(ValueError, match="terminal checker source pin mismatch"):
        helper._checker_sources()


def test_untrusted_other_run_remains_not_applicable_and_ordinary_ready(tmp_path, monkeypatch):
    control, live = fixture(tmp_path)
    mirror = _generated_mirrored_run(control, live, "Run-197")
    request = mirror / "formalization/ENGINE3_VERIFICATION_REQUEST.json"
    write_json(request, {"source_run": "Run-197", "request_kind": "LEAN_PROOF",
                         "primary_verifier": "COMPARATOR_CLOUD", "aristotle_required": False})

    def forbidden(*_):
        raise AssertionError("untrusted run must not enter terminal helper adapter")

    monkeypatch.setattr(terminal_report, "_authenticated_terminal_context", forbidden)
    status = evaluate(197, control_root=control, live_root=live)
    assert status["proof_status"] == "READY_FOR_COMPARATOR_CERTIFICATION"
    assert status["terminal_evidence"]["status"] == "NOT_APPLICABLE"


def test_synthetic_seven_run_report_retains_ids_and_held_row_without_readiness_upgrade(tmp_path, monkeypatch):
    control, live, _, _, _ = _synthetic_reporter_context(tmp_path, monkeypatch)
    for number in range(193, 200):
        if number == 194:
            continue
        run_id = f"Run-{number}"
        mirror = _generated_mirrored_run(control, live, run_id)
        write_json(mirror / "formalization/ENGINE3_VERIFICATION_REQUEST.json", {
            "source_run": run_id, "request_kind": "LEAN_PROOF",
            "primary_verifier": "COMPARATOR_CLOUD", "aristotle_required": False})
    report = saturday_report([str(number) for number in range(193, 200)], "2026-10-17",
                             control_root=control, live_root=live)
    assert [row["run_id"] for row in report["runs"]] == [f"Run-{number}" for number in range(193, 200)]
    assert report["runs"][1]["proof_status"] == "TERMINAL_PREMISE_HOLD"
    assert all(row["proof_status"] == "READY_FOR_COMPARATOR_CERTIFICATION"
               for row in report["runs"] if row["run_id"] != "Run-194")
    assert report["all_runs_have_frozen_request"] is True
    assert report["external_mutation"] is False
