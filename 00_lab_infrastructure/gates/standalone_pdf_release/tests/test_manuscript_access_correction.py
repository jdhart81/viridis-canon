from __future__ import annotations
from copy import deepcopy
import hashlib
from io import BytesIO
import importlib.util
import json
from pathlib import Path
import sys
import unittest
import zipfile

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "digest_pdf_v2_review"))
import manuscript_access_correction as access
prior_source = HERE.parent / "RESEARCH_PIPELINE_v2/verification_coverage_gates/own_record_comparison.py"
if not prior_source.is_file():
    prior_source = HERE.parent / "own_record_comparison.py"
spec = importlib.util.spec_from_file_location("_exact_prior_projection", prior_source)
own = importlib.util.module_from_spec(spec); spec.loader.exec_module(own)


class ManuscriptAccessCorrectionTests(unittest.TestCase):
    def fixture(self):
        paper = b"%PDF-1.4\nactual original admitted manuscript\n%%EOF"
        stream = BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("notes/Run-167/paper.pdf", paper)
        archived = stream.getvalue()
        blobs = {"paper.pdf": b"%PDF-digest summary", "paper.tex": b"digest source", "metadata.json": b"{}", "METHODS_NOTES.zip": archived}
        manifest = {"notes": [{"run_id": "Run-167", "uploads": [{"filename": "paper.pdf", "sha256": hashlib.sha256(paper).hexdigest()}]}],
                    "archive_members": [{"path": "notes/Run-167/paper.pdf", **access._hashes(paper)}],
                    "uploads": [{"filename": name, **access._hashes(data)} for name, data in blobs.items()]}
        manifest_bytes = json.dumps(manifest).encode()
        blobs.update({"DIGEST_MANIFEST.json": manifest_bytes, "PUBLICATION_BINDING.json": b"original exact publication binding"})
        original = [{"filename": name, **access._hashes(data)} for name, data in blobs.items()]
        files = [{"key": row["filename"], "size": row["bytes"], "checksum": "md5:" + row["md5"]} for row in original]
        metadata = {"title": "Viridis Methods Digest", "description": "Exact old science scope", "license": "cc-by-4.0"}
        legacy = {"id": 23290748, "doi": "10.5281/zenodo.23290748", "metadata": metadata, "files": files}
        native = {"id": "23290748", "pids": {"doi": {"identifier": legacy["doi"]}}, "metadata": deepcopy(metadata), "versions": {"is_latest": False},
                  "files": {"entries": {f["key"]: deepcopy(f) for f in files}, "count": len(files), "total_bytes": sum(f["size"] for f in files), "enabled": True, "order": []}}
        copy = {"run_id": "Run-167", "member": "notes/Run-167/paper.pdf", "filename": "Run-167-Paper.pdf", **access._hashes(paper)}
        receipt = {"standard": access.STANDARD, "status": "EXACT_EXISTING_ARCHIVE_ACCESS_COPIES", "record_id": "23290748", "doi": legacy["doi"],
                   "source_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(), "source_archive_sha256": hashlib.sha256(archived).hexdigest(),
                   "original_files": original, "copies": [copy], "authority": {"path": "exact-user-directive.json", "sha256": "1" * 64}}
        after_l = deepcopy(legacy); after_n = deepcopy(native)
        added = {"key": copy["filename"], "size": copy["bytes"], "checksum": "md5:" + copy["md5"]}
        after_l["files"].append(added); after_n["files"]["entries"][added["key"]] = deepcopy(added)
        after_n["files"]["count"] += 1; after_n["files"]["total_bytes"] += copy["bytes"]
        blobs[copy["filename"]] = paper
        return {"actual_legacy": after_l, "actual_native": after_n, "saved_legacy": legacy, "saved_native": native,
                "receipt": receipt, "manifest_bytes": manifest_bytes, "archive_bytes": archived,
                "download": lambda rid, name: blobs[name], "authority_consumer": lambda binding: {"status": "EXACT_USER_ACCESS_COPY_AUTHORITY_PASS"},
                "protected_projection": own.prior_protected_projection}

    def test_exact_access_copy_preserves_original_full_observations(self):
        f = self.fixture(); result = access.require_pair(**f)
        self.assertEqual(result["observed_after"]["legacy"], f["actual_legacy"])
        self.assertEqual(result["observed_before"]["native"], f["saved_native"])
        self.assertEqual(result["status"], "EXACT_ARCHIVE_ACCESS_COPIES_PROTECTED_READBACK_PASS")
        self.assertFalse(result["certifies"])

    def test_arbitrary_extra_public_file_is_rejected(self):
        f = self.fixture(); f["actual_legacy"]["files"].append({"key": "unknown.txt", "size": 1, "checksum": "md5:" + "0" * 32})
        with self.assertRaisesRegex(access.AccessCorrectionHold, "EXACT_ONLY_ADDITIONS"):
            access.require_pair(**f)

    def test_changed_public_pdf_download_is_rejected(self):
        f = self.fixture(); download = f["download"]
        f["download"] = lambda rid, name: b"%PDF-changed" if name == "Run-167-Paper.pdf" else download(rid, name)
        with self.assertRaisesRegex(access.AccessCorrectionHold, "PUBLIC_PDF_BYTES"):
            access.require_pair(**f)

    def test_changed_original_bytes_are_rejected(self):
        f = self.fixture(); download = f["download"]
        f["download"] = lambda rid, name: b"modified paper source" if name == "paper.tex" else download(rid, name)
        with self.assertRaisesRegex(access.AccessCorrectionHold, "ALL_ORIGINAL_PUBLIC_BYTES"):
            access.require_pair(**f)

    def test_metadata_and_rights_are_not_access_exceptions(self):
        f = self.fixture(); f["actual_legacy"]["metadata"]["license"] = "all-rights-reserved"
        with self.assertRaisesRegex(access.AccessCorrectionHold, "UNCHANGED_ALL_OTHER_PROTECTED_CONTENT"):
            access.require_pair(**f)

    def test_version_flags_still_require_original_chain_authority(self):
        f = self.fixture(); f["actual_native"]["versions"]["is_latest"] = True
        with self.assertRaisesRegex(access.AccessCorrectionHold, "UNCHANGED_ALL_OTHER_PROTECTED_CONTENT"):
            access.require_pair(**f)

    def test_unknown_native_housekeeping_field_is_not_silently_accepted(self):
        f = self.fixture(); f["actual_native"]["files"]["unknown_field"] = "unexpected"
        with self.assertRaisesRegex(access.AccessCorrectionHold, "UNCHANGED_ALL_OTHER_PROTECTED_CONTENT"):
            access.require_pair(**f)

    def test_native_derived_totals_must_match_exact_added_pdfs(self):
        f = self.fixture(); f["actual_native"]["files"]["total_bytes"] += 1
        with self.assertRaisesRegex(access.AccessCorrectionHold, "NATIVE_DERIVED_TOTALS"):
            access.require_pair(**f)

    def test_caller_cached_pass_is_not_authority(self):
        f = self.fixture(); f["authority_consumer"] = lambda binding: {"status": "PASS"}
        with self.assertRaisesRegex(access.AccessCorrectionHold, "EXACT_USER_AUTHORITY"):
            access.require_pair(**f)


if __name__ == "__main__":
    unittest.main()
