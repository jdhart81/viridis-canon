from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import zipfile


SCRIPT = Path(__file__).with_name("assemble_saturday_candidate.py")
SPEC = importlib.util.spec_from_file_location("assemble_saturday_candidate", SCRIPT)
assembler = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = assembler
SPEC.loader.exec_module(assembler)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


def fixture(
    root: Path,
    *,
    ledger_status: str = "⏳ AWAITING JUSTIN OK",
    ledger_row: int | None = 78,
    license_id: str = "unassigned",
) -> dict[str, Path]:
    finalized_root = root / "RESEARCH_PIPELINE_v2/finalized"
    package_root = root / "packages"
    staging_root = root / "staging"
    deposits_root = root / "deposits"
    run = finalized_root / "Run-117"
    run.mkdir(parents=True)
    (run / "paper.pdf").write_bytes(b"%PDF-example")
    (run / "Example.lean").write_text("theorem example : True := by trivial\n", encoding="utf-8")
    (run / "Example_ARISTOTLE_SUMMARY.md").write_text("# Summary\n", encoding="utf-8")
    manifest = {
        "run_id": "Run-117",
        "title": "Example Result",
        "artifacts": {"paper_pdf": "paper.pdf"},
        "release_metadata": {
            "abbreviation": "EXR",
            "description": "<p>Example formally checked result.</p>",
            "keywords": ["example", "Lean 4", "formal verification"],
            "version": "1.0.0",
            "license": license_id,
            "series_route": "S6 Cognition & Learning",
            "spine_gate": "Gate 3",
            "spine_reason": "domain-applying, not domain-defining",
            "spine_admitted": False,
            "notes": "Working paper; not peer-reviewed. Lean certifies mathematics under assumptions.",
            "ledger_row": ledger_row,
        },
    }
    write_json(run / "PAPER_PACKAGE_MANIFEST.json", manifest)
    write_json(
        run / "FINALIZED_PACKAGE.json",
        {"status": "FINALIZED", "external_mutation": False},
    )
    write_json(
        package_root / "Run-117/QUALITY_GATE.json",
        {"quality_verdict": "PASS", "saturday_status": "CANDIDATE_FOR_LEDGER_G0_G9"},
    )
    write_json(
        finalized_root.parent / "viridisos_kernel_packages/Run-117/VIRIDISOS_KERNEL_PACKAGE.json",
        {
            "schema_version": 1,
            "standard": "VRS-VIRIDISOS-KERNEL-PACKAGE-1",
            "run_id": "Run-117",
            "status": "NO_RUNTIME_KERNEL",
            "eligible_for_runtime_module": False,
            "authority": {"production_deployment_authorized": False},
            "external_mutation": False,
        },
    )
    lockstep = assembler.load_lockstep()
    artifact_names = ("paper.pdf", "Example.lean", "Example_ARISTOTLE_SUMMARY.md")
    review = {
        "schema_version": 2,
        "reviewer_system": "Codex",
        "reviewer_model": "gpt-5.6-terra",
        "reviewed_at_utc": "2026-08-01T12:00:00Z",
        "verdict": "pass",
        "series_route": "S6 Cognition & Learning",
        "spine_admission": {
            "admitted": False,
            "gate": "Gate 3",
            "reason": "domain-applying, not domain-defining",
        },
        "artifacts": {name: lockstep.sha256(run / name) for name in artifact_names},
        "checks": {name: True for name in lockstep.REVIEW_CHECKS},
    }
    write_json(run / "POST_ARISTOTLE_REVIEW.json", review)
    ledger_path = root / "ZENODO_SUBMISSION_LEDGER.md"
    ledger_path.write_text(
        "| # | Date | Item / module | Source | Aristotle ID | Verified | Route | Status | DOI |\n"
        f"| 78 | 2026-08-01 | EXR — Example Result | Run 117 | p | yes | S6 standalone | {ledger_status} | — |\n",
        encoding="utf-8",
    )
    write_json(
        finalized_root.parent / "PUBLIC_IDENTITY_RECONCILIATION_SURFACE_2026-08-30.json",
        {"authoritative_ledger_max_row_observed": 78, "records": []},
    )
    return {
        "finalized_root": finalized_root,
        "package_root": package_root,
        "staging_root": staging_root,
        "deposits_root": deposits_root,
        "ledger_path": ledger_path,
    }


def test_stages_candidate_but_does_not_promote_unapproved_ledger_row():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp))
        result = assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        assert result["status"] == "STAGED_CANDIDATE"
        assert result["ledger"]["state"] == "HOLD_LEDGER"
        bundle = Path(result["bundle"])
        assert (bundle / "VIRIDISOS_KERNEL_PACKAGE.json").is_file()
        manifest = assembler.read_json(bundle / "BUNDLE_MANIFEST.json")
        assert manifest["viridisos_kernel_package"]["status"] == "NO_RUNTIME_KERNEL"
        promoted = assembler.promote_ledger_cleared(
            "2026-08-02",
            staging_root=paths["staging_root"],
            deposits_root=paths["deposits_root"],
            ledger_path=paths["ledger_path"],
        )
        assert promoted["status"] == "HOLD_NO_LEDGER_CLEARED_BUNDLES"
        assert not paths["deposits_root"].exists()


def test_ready_kernel_bundle_includes_spec_engine_tests_and_fixtures():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp))
        run = paths["finalized_root"] / "Run-117"
        engine = run / "kernel.py"
        test = run / "test_kernel.py"
        input_path = run / "fixture_input.json"
        expected_path = run / "fixture_expected.json"
        engine.write_text("def compute(inputs):\n    return inputs\n", encoding="utf-8")
        test.write_text("def test_kernel():\n    assert True\n", encoding="utf-8")
        write_json(input_path, {"value": 1})
        write_json(expected_path, {"value": 1})
        spec_path = run / "VIRIDISOS_KERNEL_SPEC.json"
        write_json(spec_path, {"standard": "VRS-VIRIDISOS-KERNEL-SPEC-1", "run_id": "Run-117"})
        receipt_path = run.parent.parent / "viridisos_kernel_packages/Run-117/VIRIDISOS_KERNEL_PACKAGE.json"
        write_json(
            receipt_path,
            {
                "schema_version": 1,
                "standard": "VRS-VIRIDISOS-KERNEL-PACKAGE-1",
                "run_id": "Run-117",
                "status": "KERNEL_IMPLEMENTATION_READY",
                "eligible_for_runtime_module": True,
                "source_sha256": {"kernel_spec": assembler.sha256(spec_path)},
                "implementation": {
                    "engine": {
                        "path": "kernel.py",
                        "sha256": assembler.sha256(engine),
                        "entrypoint": "compute",
                    },
                    "tests": [{"path": "test_kernel.py", "sha256": assembler.sha256(test)}],
                    "fixtures": [
                        {
                            "input": "fixture_input.json",
                            "input_sha256": assembler.sha256(input_path),
                            "expected": "fixture_expected.json",
                            "expected_sha256": assembler.sha256(expected_path),
                        }
                    ],
                },
                "authority": {"production_deployment_authorized": False},
                "external_mutation": False,
            },
        )
        result = assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        bundle = Path(result["bundle"])
        for name in (
            "VIRIDISOS_KERNEL_SPEC.json",
            "kernel.py",
            "test_kernel.py",
            "fixture_input.json",
            "fixture_expected.json",
        ):
            assert (bundle / "viridisos_kernel" / name).is_file()
        manifest = assembler.read_json(bundle / "BUNDLE_MANIFEST.json")
        assert len(manifest["viridisos_kernel_package"]["implementation_files"]) == 5


def test_missing_authoritative_row_still_stages_but_never_promotes():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp), ledger_row=None)
        result = assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        assert result["status"] == "STAGED_CANDIDATE"
        assert result["ledger"]["state"] == "HOLD_LEDGER"
        assert "not been assigned" in result["ledger"]["reason"]
        promoted = assembler.promote_ledger_cleared(
            "2026-08-02",
            staging_root=paths["staging_root"],
            deposits_root=paths["deposits_root"],
            ledger_path=paths["ledger_path"],
        )
        assert promoted["status"] == "HOLD_NO_LEDGER_CLEARED_BUNDLES"
        assert promoted["holds"][0]["reason"] == "ledger row missing"


def test_single_saturday_authorization_binds_unchanged_staged_candidate():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(
            Path(temp),
            ledger_status="✅ OK — S6 standalone (Justin)",
            ledger_row=None,
        )
        assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        bound = assembler.bind_ledger(
            "117",
            "2026-08-02",
            78,
            justin_authorized=True,
            license_id="cc-by-4.0",
            staging_root=paths["staging_root"],
            ledger_path=paths["ledger_path"],
        )
        promoted = assembler.promote_ledger_cleared(
            "2026-08-02",
            staging_root=paths["staging_root"],
            deposits_root=paths["deposits_root"],
            ledger_path=paths["ledger_path"],
        )
        assert bound["status"] == "LEDGER_BOUND"
        assert promoted["status"] == "READY_FOR_DRY_RUN"
        deposit = paths["deposits_root"] / "2026-08-02_EXR_standalone"
        assert (deposit / "LEDGER_BINDING.json").is_file()


def test_single_authorization_binds_license_and_ledger_without_changing_science():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(
            Path(temp),
            ledger_status="✅ OK — S6 standalone (Justin)",
            ledger_row=None,
            license_id="unassigned",
        )
        assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        bundle = paths["staging_root"] / "2026-08-02/2026-08-02_EXR_standalone"
        paper_hash = assembler.sha256(bundle / "paper.pdf")
        bound = assembler.bind_ledger(
            "117",
            "2026-08-02",
            78,
            justin_authorized=True,
            license_id="cc-by-4.0",
            staging_root=paths["staging_root"],
            ledger_path=paths["ledger_path"],
        )
        metadata = assembler.read_json(bundle / "zenodo_metadata.json")
        release = assembler.read_json(bundle / "RELEASE_BINDING.json")
        assert bound["status"] == "LEDGER_BOUND"
        assert metadata["metadata"]["license"] == "cc-by-4.0"
        assert "ASSIGNED_CC_BY_4_0" in (bundle / "RIGHTS_AND_LICENSE.md").read_text()
        assert "not published" not in metadata["metadata"]["description"].lower()
        assert release["license"] == "cc-by-4.0"
        assert release["ledger_row"] == 78
        assert assembler.sha256(bundle / "paper.pdf") == paper_hash
        assert assembler.tree_hashes(bundle) == assembler.read_json(
            bundle / "BUNDLE_MANIFEST.json"
        )["artifact_sha256"]


def test_authorization_reconciles_embedded_rights_and_checksums():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(
            Path(temp),
            ledger_status="✅ OK — S6 standalone (Justin)",
            ledger_row=None,
        )
        assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        bundle = paths["staging_root"] / "2026-08-02/2026-08-02_EXR_standalone"
        with zipfile.ZipFile(bundle / "REPRODUCTION_BUNDLE.zip", "w") as archive:
            archive.writestr(
                "RIGHTS_AND_LICENSE.md",
                (bundle / "RIGHTS_AND_LICENSE.md").read_text(encoding="utf-8"),
            )
        (bundle / "SHA256SUMS.txt").write_text("pre-authorization\n", encoding="utf-8")
        manifest = assembler.read_json(bundle / "BUNDLE_MANIFEST.json")
        manifest["artifact_sha256"] = assembler.tree_hashes(bundle)
        assembler.write_json_atomic(bundle / "BUNDLE_MANIFEST.json", manifest)

        assembler.bind_ledger(
            "117",
            "2026-08-02",
            78,
            justin_authorized=True,
            license_id="cc-by-4.0",
            staging_root=paths["staging_root"],
            ledger_path=paths["ledger_path"],
        )
        with zipfile.ZipFile(bundle / "REPRODUCTION_BUNDLE.zip") as archive:
            embedded = archive.read("RIGHTS_AND_LICENSE.md").decode("utf-8")
        assert "ASSIGNED_CC_BY_4_0" in embedded
        assert "HOLD_UNASSIGNED" not in embedded
        checksums = (bundle / "SHA256SUMS.txt").read_text(encoding="utf-8")
        assert "REPRODUCTION_BUNDLE.zip" in checksums


def test_ledger_binding_requires_both_justin_authorization_and_cleared_row():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp), ledger_row=None)
        assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        try:
            assembler.bind_ledger(
                "117",
                "2026-08-02",
                78,
                justin_authorized=False,
                staging_root=paths["staging_root"],
                ledger_path=paths["ledger_path"],
            )
        except assembler.AssemblyError as exc:
            assert "Justin" in str(exc)
        else:
            raise AssertionError("binding without Justin authorization must fail")
        try:
            assembler.bind_ledger(
                "117",
                "2026-08-02",
                78,
                justin_authorized=True,
                staging_root=paths["staging_root"],
                ledger_path=paths["ledger_path"],
            )
        except assembler.AssemblyError as exc:
            assert "not Justin-cleared" in str(exc)
        else:
            raise AssertionError("binding an awaiting ledger row must fail")


def test_justin_ok_row_promotes_local_bundle_idempotently():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp), ledger_status="✅ OK — S6 standalone (Justin)")
        assembler.stage_candidate(
            "Run-117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        assembler.bind_ledger(
            "Run-117",
            "2026-08-02",
            78,
            justin_authorized=True,
            license_id="cc-by-4.0",
            staging_root=paths["staging_root"],
            ledger_path=paths["ledger_path"],
        )
        first = assembler.promote_ledger_cleared(
            "2026-08-02",
            staging_root=paths["staging_root"],
            deposits_root=paths["deposits_root"],
            ledger_path=paths["ledger_path"],
        )
        second = assembler.promote_ledger_cleared(
            "2026-08-02",
            staging_root=paths["staging_root"],
            deposits_root=paths["deposits_root"],
            ledger_path=paths["ledger_path"],
        )
        assert first["status"] == "READY_FOR_DRY_RUN"
        assert second["status"] == "READY_FOR_DRY_RUN"
        assert len(first["promoted"]) == 1
        assert (paths["deposits_root"] / "2026-08-02_EXR_standalone/BUNDLE_MANIFEST.json").is_file()


def test_duplicate_ledger_row_never_promotes():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(Path(temp), ledger_status="✅ OK — S6 standalone (Justin)")
        with paths["ledger_path"].open("a", encoding="utf-8") as handle:
            handle.write("| 78 | 2026-08-01 | EXR duplicate | Run 117 | p | yes | S6 | ✅ OK | — |\n")
        result = assembler.stage_candidate(
            "117",
            "2026-08-02",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        assert result["ledger"]["state"] == "HOLD_LEDGER"
        assert "occurs 2 times" in result["ledger"]["reason"]


def test_ai_systems_are_not_zenodo_creators():
    payload = assembler.zenodo_payload(
        "Title",
        {
            "license": "cc-by-4.0",
            "keywords": ["a", "b", "c"],
            "version": "1.0.0",
            "notes": "not peer-reviewed",
            "description": "<p>description</p>",
        },
    )
    assert payload["metadata"]["creators"] == [
        {
            "name": "Hart, Justin D.",
            "affiliation": "Viridis LLC, Columbia Falls, Montana, USA",
            "orcid": "0009-0008-3082-2482",
        }
    ]


def test_published_run_is_not_restaged_or_promoted_again():
    with tempfile.TemporaryDirectory() as temp:
        paths = fixture(
            Path(temp),
            ledger_status="🌐 PUBLISHED — release reconciled",
        )
        result = assembler.stage_candidate(
            "117",
            "2026-08-22",
            **{key: paths[key] for key in ("finalized_root", "package_root", "staging_root", "ledger_path")},
        )
        assert result["status"] == "ALREADY_PUBLISHED"
        assert not (paths["staging_root"] / "2026-08-22").exists()
