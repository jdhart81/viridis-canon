from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import tarfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import manuscript_pdf_gate as gate
import guard_methods_digest_release as guard


class ManuscriptPDFGateTests(unittest.TestCase):
    def bundle(self, root, *, separate=True, declared=True):
        root = Path(root); paper = b"%PDF-1.4\nactual note manuscript\n%%EOF"
        (root / "paper.pdf").write_bytes(b"%PDF-1.4\ndigest scope summary\n%%EOF")
        with zipfile.ZipFile(root / "METHODS_NOTES.zip", "w") as archive:
            archive.writestr("notes/Run-167/paper.pdf", paper)
        if separate:
            (root / "Run-167-Paper.pdf").write_bytes(paper)
        uploads = [{"filename": "paper.pdf"}, {"filename": "METHODS_NOTES.zip"}]
        if declared:
            uploads.append({"filename": "Run-167-Paper.pdf", **gate._hashes(paper)})
        manifest = {"notes": [{"run_id": "Run-167", "uploads": [{"filename": "paper.pdf", "sha256": hashlib.sha256(paper).hexdigest()}]}], "uploads": uploads}
        (root / "DIGEST_MANIFEST.json").write_text(json.dumps(manifest))
        return root, paper

    def test_digest_summary_is_not_a_manuscript_substitute(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp, separate=False, declared=False)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "lacks a byte-identical separate PDF"):
                gate.require_local(root)

    def test_exact_standalone_archive_copy_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            result = gate.require_local(root)
            self.assertEqual(result["manuscripts"][0]["run_id"], "Run-167")
            self.assertEqual(result["manuscripts"][0]["filename"], "Run-167-Paper.pdf")

    def test_pdf_present_but_not_approved_for_upload_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp, declared=False)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "absent from approved"):
                gate.require_local(root)

    def test_pdf_on_disk_but_excluded_from_actual_upload_set_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "lacks a byte-identical separate PDF"):
                gate.require_local(root, [root / "paper.pdf", root / "METHODS_NOTES.zip"])

    def test_changed_note_pdf_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            (root / "Run-167-Paper.pdf").write_bytes(b"%PDF-different")
            with self.assertRaises(gate.ManuscriptPDFHold):
                gate.require_local(root)

    def test_note_claimed_manuscript_hash_must_match_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            path = root / "DIGEST_MANIFEST.json"; m = json.loads(path.read_text())
            m["notes"][0]["uploads"][0]["sha256"] = "0" * 64
            path.write_text(json.dumps(m))
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "hash differs"):
                gate.require_local(root)

    def test_filename_extension_does_not_establish_pdf_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "paper.pdf").write_text("not a paper")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "actual PDF bytes"):
                gate.require_local(Path(tmp))

    def test_archive_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, paper = self.bundle(tmp)
            with zipfile.ZipFile(root / "METHODS_NOTES.zip", "a") as z:
                z.writestr("../paper.pdf", paper)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "unsafe"):
                gate.require_local(root)

    def test_archived_figure_does_not_require_a_separate_manuscript_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            with zipfile.ZipFile(root / "METHODS_NOTES.zip", "a") as archive:
                archive.writestr("figures/fig2_mu.pdf", b"%PDF-individual graph")
            self.assertEqual(len(gate.require_local(root)["manuscripts"]), 1)

    def test_figure_alone_is_not_an_actual_standalone_paper(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "figure.pdf").write_bytes(b"%PDF-figure")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "figure PDF"):
                gate.require_local(Path(tmp))

    def test_descriptive_papers_directory_cannot_remain_hidden_by_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paper = b"%PDF-actual restoration speed limit"
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated digest summary")
            with zipfile.ZipFile(root / "CANON.zip", "w") as archive:
                archive.writestr("papers/Restoration_Speed_Limit_v1.pdf", paper)
                archive.writestr("figures/fig2_mu.pdf", b"%PDF-figure")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "lacks a byte-identical separate PDF"):
                gate.require_local(root)
            (root / "Restoration-Speed-Limit-Paper.pdf").write_bytes(paper)
            self.assertEqual(len(gate.require_local(root)["manuscripts"]), 1)

    def test_ambiguous_archive_pdf_requires_copy_and_paper_role_precedes_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paper = b"%PDF-actual scientific manuscript"
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated summary")
            with zipfile.ZipFile(root / "source.zip", "w") as archive:
                archive.writestr("source/Descriptive_Title.pdf", paper)
                archive.writestr("figures/paper.pdf", paper)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "lacks a byte-identical separate PDF"):
                gate.require_local(root)
            (root / "Descriptive-Paper.pdf").write_bytes(paper)
            self.assertEqual(len(gate.require_local(root)["manuscripts"]), 2)

    def test_actual_tar_manuscript_cannot_remain_hidden_with_a_figure_upload(self):
        from io import BytesIO
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paper = b"%PDF-actual restored manuscript"
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated summary")
            with tarfile.open(root / "restoration.tar.gz", "w:gz") as archive:
                info = tarfile.TarInfo("restoration/paper.pdf"); info.size = len(paper)
                archive.addfile(info, BytesIO(paper))
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "lacks a byte-identical separate PDF"):
                gate.require_local(root)
            (root / "Restoration-Paper.pdf").write_bytes(paper)
            self.assertEqual(gate.require_local(root)["manuscripts"][0]["filename"], "Restoration-Paper.pdf")

    def test_descriptive_manuscript_name_requires_exact_role_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); data = b"%PDF-real science manuscript"
            (root / "Trees-Cannot-Cut.pdf").write_bytes(data)
            with self.assertRaises(gate.ManuscriptPDFHold):
                gate.require_local(root)
            roles = {"standard": gate.STANDARD, "manuscripts": [{"filename": "Trees-Cannot-Cut.pdf", **gate._hashes(data)}]}
            (root / "MANUSCRIPT_PDFS.json").write_text(json.dumps(roles))
            self.assertEqual(gate.require_local(root)["top_level_pdfs"][0]["filename"], "Trees-Cannot-Cut.pdf")

    def test_source_only_software_paper_is_not_exempted_by_unrelated_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); paper = b"%PDF-faithful historical manuscript rendering"
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated software overview")
            with zipfile.ZipFile(root / "software.zip", "w") as archive:
                archive.writestr("papers/UNIFYING_PAPER.md", "# Actual manuscript\n")
                archive.writestr("papers/UNIFYING_PAPER.docx", b"source document")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "source requires its corresponding rendered PDF"):
                gate.require_local(root)
            with zipfile.ZipFile(root / "software.zip", "a") as archive:
                archive.writestr("papers/UNIFYING_PAPER.pdf", paper)
            (root / "Unifying-Paper.pdf").write_bytes(paper)
            self.assertEqual(len(gate.require_local(root)["manuscripts"]), 1)

    def test_top_level_source_paper_requires_corresponding_uploaded_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source = root / "UNIFYING_PAPER_DRAFT.md"
            source.write_text("# Actual unifying paper\n")
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated summary")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "top-level manuscript source requires"):
                gate.require_local(root)
            rendered = root / "UNIFYING_PAPER_DRAFT.pdf"
            rendered.write_bytes(b"%PDF-faithful rendered manuscript")
            self.assertEqual(len(gate.require_local(root)["top_level_pdfs"]), 2)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "top-level manuscript source requires"):
                gate.require_local(root, [source, root / "paper.pdf"])

    def test_descriptive_word_manuscript_name_cannot_bypass_source_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); word = root / "HDFM_FINAL_With_Figures.docx"
            word.write_bytes(b"actual article source, descriptive filename")
            (root / "paper.pdf").write_bytes(b"%PDF-unrelated software summary")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "top-level manuscript source requires"):
                gate.require_local(root)
            with zipfile.ZipFile(root / "HDFM.zip", "w") as archive:
                archive.writestr(word.name, word.read_bytes())
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "source requires its corresponding rendered PDF"):
                gate.require_local(root, [root / "paper.pdf", root / "HDFM.zip"])

    def test_public_metadata_is_not_enough_without_exact_pdf_download(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp); plan = gate.require_local(root)
            record = {"id": 23290748, "files": [{"key": f["filename"], "size": f["bytes"], "checksum": "md5:" + f["md5"]} for f in plan["upload_files"]]}
            target = "Run-167-Paper.pdf"
            download = mock.Mock(side_effect=lambda rid, name:
                b"%PDF-changed" if name == target else (root / name).read_bytes())
            with self.assertRaisesRegex(gate.ManuscriptPDFHold,
                    r"downloaded upload differs from approved bytes: Run-167-Paper[.]pdf"):
                gate.require_public(record, plan, download=download)
            self.assertIn(mock.call("23290748", target), download.call_args_list)
            receipt = gate.require_public(record, plan, download=lambda rid, name: (root / name).read_bytes())
            self.assertEqual(len(receipt["pdfs"]), 2)

    def test_public_missing_separate_pdf_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp); plan = gate.require_local(root)
            missing_name = "Run-167-Paper.pdf"
            record = {"id": 23290748, "files": [
                {"key": f["filename"], "size": f["bytes"], "checksum": "md5:" + f["md5"]}
                for f in plan["upload_files"] if f["filename"] != missing_name]}
            download = mock.Mock()
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "exact approved uploads"):
                gate.require_public(record, plan, download=download)
            download.assert_not_called()

    def test_outer_guard_blocks_legacy_config_before_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp, separate=False, declared=False)
            config = root / "CONFIG.json"; config.write_text(json.dumps({"package": str(root)}))
            with mock.patch.object(guard, "dispatch") as run:
                rc = guard.main(["--config", str(config), "--expected-config-sha256", hashlib.sha256(config.read_bytes()).hexdigest(), "--go", "--output", str(root / "private-output")])
            self.assertEqual(rc, 1); run.assert_not_called()

    def test_outer_guard_dispatches_only_after_matching_config_and_pdfs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root, _ = self.bundle(tmp)
            config = root / "CONFIG.json"; config.write_text(json.dumps({"package": str(root)}))
            with mock.patch.object(guard, "dispatch", return_value={"status": "TEST_ONLY"}) as run:
                rc = guard.main(["--config", str(config), "--expected-config-sha256", hashlib.sha256(config.read_bytes()).hexdigest(), "--go", "--output", str(root / "private-output")])
            self.assertEqual(rc, 0); run.assert_called_once()

    def test_v2_assembly_and_current_guard_bind_standalone_paper_bytes(self):
        candidate = HERE / "digest_pdf_v2_review" / "methods_digest.py"
        spec = importlib.util.spec_from_file_location("_pdf_review_methods_digest_v2", candidate)
        v2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(v2)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); paper = b"%PDF-1.4\nactual scientific paper\n%%EOF"
            source = root / "source-metadata.json"
            source.write_text(json.dumps({"creators": [{"name": "Example"}], "license": "cc-by-4.0"}))
            note = {"run_id": "Run-167", "path": str(root / "fixture-note"), "section": "MAIN_NOTES", "foundation_basis": "INDEPENDENT", "prior_dois": [],
                "publication_binding": {"path": "unused-science-fixture", "sha256": "0" * 64},
                "uploads": [{"filename": "paper.pdf", "sha256": hashlib.sha256(paper).hexdigest()}],
                "claim_table": [{"lean_theorem": "example", "semantic_tier": "SUBSTANTIVE", "nonvacuity_label": "NO_HYPOTHESES", "headline_eligible": True}]}
            consumed = {"notes": [note], "members": [("notes/Run-167/paper.pdf", paper)], "input_bindings": {}, "authority": {"path": "unused", "sha256": "0" * 64}}
            output = root / "RESEARCH_PIPELINE_v2/science_release_queue/digests/example-v2"
            with mock.patch.object(v2, "consume_notes", return_value=consumed):
                manifest = v2.prepare(root, output, "2026-W42", [], consumed["authority"],
                    {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}, "2026-10-12",
                    render=lambda path: b"%PDF-1.4\ndigest summary\n%%EOF")
                self.assertEqual((output / "Run-167-Paper.pdf").read_bytes(), paper)
                self.assertIn("Run-167-Paper.pdf", {u["filename"] for u in manifest["uploads"]})
                self.assertEqual(v2.require_current(output, root), manifest)
                v2.publication_binding(output, root, assembled_at_utc="2026-10-12T10:00:00+00:00")
                files = [{"key": p.name, "size": p.stat().st_size, "checksum": "md5:" + hashlib.md5(p.read_bytes()).hexdigest()} for p in output.iterdir() if p.is_file()]
                record = {"id": 123, "doi": "10.5281/zenodo.123", "metadata": manifest["public_metadata"], "files": files}
                own = {"record_id": "123", "doi": record["doi"], "method": "POST", "url": "https://zenodo.org/api/deposit/depositions/123/actions/publish", "status": "HTTP_SUCCESS_ONLY_NOT_PUBLICATION_CLEARANCE"}
                receipt = v2.strict_readback(output, root, record, own, lambda f, rid: (output / f["key"]).read_bytes(), expected_record=record, metadata_consumer=lambda *args: None)
                self.assertEqual(receipt["files"], 7)
                (output / "Run-167-Paper.pdf").write_bytes(b"%PDF-changed")
                with self.assertRaisesRegex(v2.DigestHold, "separate note manuscript differs"):
                    v2.require_current(output, root)


if __name__ == "__main__":
    unittest.main()
