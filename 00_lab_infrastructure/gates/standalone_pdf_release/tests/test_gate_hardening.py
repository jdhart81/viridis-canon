"""Security regressions for exact manuscript coverage and complete readback."""
from __future__ import annotations

import bz2
import gzip
import hashlib
from io import BytesIO
import json
import lzma
from pathlib import Path
import stat
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import manuscript_pdf_gate as gate

PAPER = b"%PDF-1.4\nactual manuscript\n%%EOF\n"
SUMMARY = b"%PDF-1.4\nunrelated summary\n%%EOF\n"


def zipped(rows):
    target = BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in rows:
                archive.writestr(name, data)
    return target.getvalue()


def tarred(rows):
    target = BytesIO()
    with tarfile.open(fileobj=target, mode="w") as archive:
        for name, data in rows:
            info = tarfile.TarInfo(name); info.size = len(data)
            archive.addfile(info, BytesIO(data))
    return target.getvalue()


class HardeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, data):
        path = self.root / name; path.write_bytes(data)
        return path

    def paper(self):
        self.put("paper.pdf", SUMMARY)

    def test_prefixed_zip_with_disguised_filename_cannot_hide_manuscript(self):
        self.paper()
        prefixed = b"MZ self-extracting preamble\n" + zipped([("papers/Hidden-Paper.pdf", PAPER)])
        self.assertTrue(zipfile.is_zipfile(BytesIO(prefixed)))
        self.put("opaque.bin", prefixed)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "byte-identical separate PDF"):
            gate.require_local(self.root)
        self.put("Hidden-Paper.pdf", PAPER)
        self.assertEqual(len(gate.require_local(self.root)["manuscripts"]), 1)

    def digest(self, run="Run-167", *, filename=None, archive_hash=None):
        filename = filename or run + "-Paper.pdf"
        self.put("paper.pdf", SUMMARY)
        self.put(filename, PAPER)
        self.put("METHODS_NOTES.zip", zipped([("notes/" + run + "/paper.pdf", PAPER)]))
        manifest = {"notes": [{"run_id": run, "uploads": [{"filename": "paper.pdf", "sha256": archive_hash or hashlib.sha256(PAPER).hexdigest()}]}],
                    "uploads": [{"filename": filename, **gate._hashes(PAPER)}]}
        self.put("DIGEST_MANIFEST.json", json.dumps(manifest).encode())
        return manifest

    def record(self, plan):
        return {"id": 123, "files": [{"key": row["filename"], "size": row["bytes"], "checksum": "md5:" + row["md5"]}
                                      for row in plan["upload_files"]]}

    def test_archived_manuscript_source_requires_rendered_counterpart(self):
        self.paper(); path = self.put("source.zip", zipped([("papers/Hidden-Paper.tex", b"source manuscript")]))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "corresponding rendered PDF"):
            gate.require_local(self.root, [self.root / "paper.pdf", path])

    def test_v7_tar_magic_without_ustar_or_extension_is_inspected(self):
        self.paper(); raw = bytearray(tarred([("paper.pdf", PAPER)]))
        raw[257:265] = b"\0" * 8
        raw[148:156] = b"        "
        raw[148:156] = (f"{sum(raw[:512]):06o}\0 ").encode("ascii")
        path = self.put("v7-container.bin", bytes(raw))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "separate PDF"):
            gate.require_local(self.root, [self.root / "paper.pdf", path])

    def test_decoded_codec_layers_are_charged_to_shared_budget(self):
        self.put("paper.pdf", PAPER)
        raw = gzip.compress(tarred([("paper.pdf", PAPER)]))
        one = self.put("one.tar.gz", raw); two = self.put("two.tar.gz", raw)
        with mock.patch.object(gate, "MAX_ARCHIVE_BYTES", 15000):
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "total expanded"):
                gate.require_local(self.root, [self.root / "paper.pdf", one, two])

    def test_pdf_magic_is_required(self):
        self.put("paper.pdf", b"this is not PDF")
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "actual PDF"):
            gate.require_local(self.root)

    def test_run_specific_name_is_required(self):
        self.digest(filename="Other-Paper.pdf")
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "Run-named"):
            gate.require_local(self.root)

    def test_digest_upload_binding_is_required(self):
        manifest = self.digest(); manifest["uploads"] = []
        self.put("DIGEST_MANIFEST.json", json.dumps(manifest).encode())
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "approved digest upload"):
            gate.require_local(self.root)

    def test_safe_archive_paths_are_required(self):
        self.paper(); self.put("source.zip", zipped([("../paper.pdf", SUMMARY)]))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "unsafe"):
            gate.require_local(self.root)

    def test_unknown_pdf_role_is_not_an_exemption(self):
        self.paper(); self.put("source.zip", zipped([("unknown/Descriptive.pdf", PAPER)]))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "byte-identical"):
            gate.require_local(self.root)

    def test_public_download_hashes_are_checked_for_nonpdf_files(self):
        self.paper(); self.put("data.csv", b"a,b\n1,2\n")
        plan = gate.require_local(self.root)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "downloaded upload differs"):
            gate.require_public(self.record(plan), plan,
                download=lambda rid, name: b"a,b\n9,9\n" if name == "data.csv" else (self.root / name).read_bytes())

    def test_public_size_and_md5_must_both_match(self):
        self.paper(); plan = gate.require_local(self.root)
        for field, value in (("size", 999), ("checksum", "md5:" + "0" * 32)):
            with self.subTest(field=field):
                record = self.record(plan); record["files"][0][field] = value
                with self.assertRaisesRegex(gate.ManuscriptPDFHold, "missing or changed"):
                    gate.require_public(record, plan, download=lambda rid, name: (self.root / name).read_bytes())

    def test_duplicate_members_are_rejected_even_when_identical(self):
        self.paper(); self.put("source.zip", zipped([("paper.pdf", SUMMARY), ("paper.pdf", SUMMARY)]))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "duplicate"):
            gate.require_local(self.root)

    def test_artifact_symlinks_are_rejected(self):
        real = self.put("real.bin", SUMMARY); (self.root / "paper.pdf").symlink_to(real)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "regular"):
            gate.require_local(self.root, [self.root / "paper.pdf"])

    def test_note_hash_must_match_exact_archive_member(self):
        self.digest(archive_hash="0" * 64)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "hash differs"):
            gate.require_local(self.root)

    def test_word_sources_require_rendering(self):
        self.paper(); self.put("Descriptive.docx", b"a real manuscript source")
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "source requires"):
            gate.require_local(self.root)

    def test_no_pdf_deposit_is_rejected(self):
        self.put("README.txt", b"no paper")
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "at least one"):
            gate.require_local(self.root)

    def test_tar_nonregular_manuscript_is_rejected(self):
        self.paper(); target = BytesIO()
        with tarfile.open(fileobj=target, mode="w") as archive:
            info = tarfile.TarInfo("paper.pdf"); info.type = tarfile.SYMTYPE; info.linkname = "other.pdf"
            archive.addfile(info)
        self.put("source.tar", target.getvalue())
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "archived manuscript must be a regular"):
            gate.require_local(self.root)

    def test_outside_upload_is_rejected(self):
        self.paper()
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other) / "paper.pdf"; outside.write_bytes(PAPER)
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "top-level"):
                gate.require_local(self.root, [outside])

    def test_figure_only_deposit_is_rejected(self):
        self.put("figure.pdf", PAPER)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "figure PDF"):
            gate.require_local(self.root)

    def test_read_race_changes_cause_hold_but_ctime_does_not(self):
        path = self.put("paper.pdf", PAPER); original = Path.stat; original_read = Path.read_bytes
        for changed in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns"):
            with self.subTest(changed=changed):
                read_finished = False
                def read(target):
                    nonlocal read_finished
                    data = original_read(target)
                    read_finished = True
                    return data
                def altered(target, *args, **kwargs):
                    value = original(target, *args, **kwargs)
                    if target == path and read_finished:
                        fields = {name: getattr(value, name) for name in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode")}
                        fields[changed] += 1
                        return SimpleNamespace(**fields)
                    return value
                with mock.patch.object(Path, "stat", altered), mock.patch.object(Path, "read_bytes", read):
                    if changed == "st_ctime_ns":
                        self.assertEqual(gate._read(path), PAPER)
                    else:
                        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "changed during read"):
                            gate._read(path)

    def test_manuscript_role_hash_binding_is_required(self):
        self.put("Descriptive.pdf", PAPER)
        roles = {"standard": gate.STANDARD, "manuscripts": [{"filename": "Descriptive.pdf", **gate._hashes(SUMMARY)}]}
        self.put("MANUSCRIPT_PDFS.json", json.dumps(roles).encode())
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "bytes differ"):
            gate.require_local(self.root)

    def test_run_ids_need_three_or_more_decimal_digits(self):
        for run in ("Run-16", "Run-ABC", "Other-167"):
            with self.subTest(run=run):
                for path in self.root.iterdir():
                    path.unlink()
                self.digest(run)
                with self.assertRaisesRegex(gate.ManuscriptPDFHold, "Run identities"):
                    gate.require_local(self.root)
        for path in self.root.iterdir():
            path.unlink()
        self.digest("Run-1000")
        self.assertEqual(gate.require_local(self.root)["manuscripts"][0]["run_id"], "Run-1000")

    def test_disguised_archives_and_compression_aliases_cannot_hide_papers(self):
        raw_tar = tarred([("papers/Descriptive.pdf", PAPER)])
        codecs = [("opaque.bin", zipped([("paper.pdf", PAPER)])), ("opaque.data", raw_tar),
                  ("source.tgz", gzip.compress(raw_tar)), ("source.tbz2", bz2.compress(raw_tar)),
                  ("source.tbz", bz2.compress(raw_tar)), ("source.txz", lzma.compress(raw_tar)),
                  ("paper.pdf.gz", gzip.compress(PAPER)), ("opaque.gz", gzip.compress(PAPER)),
                  ("opaque.bin", gzip.compress(raw_tar))]
        for filename, raw in codecs:
            with self.subTest(filename=filename, magic=raw[:6]):
                self.paper(); path = self.put(filename, raw)
                with self.assertRaisesRegex(gate.ManuscriptPDFHold, "byte-identical"):
                    gate.require_local(self.root, [self.root / "paper.pdf", path])
                standalone = self.put("Actual-Paper.pdf", PAPER)
                self.assertTrue(gate.require_local(self.root, [self.root / "paper.pdf", path, standalone])["manuscripts"])

    def test_zstd_magic_is_inspected_or_fails_closed_without_codec(self):
        self.paper()
        try:
            from compression import zstd
        except ImportError:
            path = self.put("opaque.bin", b"\x28\xb5\x2f\xfdunavailable")
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "zstd.*unavailable"):
                gate.require_local(self.root, [self.root / "paper.pdf", path])
            return
        path = self.put("opaque.bin", zstd.compress(tarred([("paper.pdf", PAPER)])))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "byte-identical"):
            gate.require_local(self.root, [self.root / "paper.pdf", path])
        standalone = self.put("Actual-Paper.pdf", PAPER)
        self.assertEqual(len(gate.require_local(self.root, [self.root / "paper.pdf", path, standalone])["manuscripts"]), 1)

    def test_nested_archives_have_a_three_level_limit(self):
        self.paper(); standalone = self.put("Actual-Paper.pdf", PAPER)
        raw = zipped([("paper.pdf", PAPER)])
        raw = zipped([("second.zip", raw)])
        raw = zipped([("first.zip", raw)])
        path = self.put("source.zip", raw)
        plan = gate.require_local(self.root, [self.root / "paper.pdf", standalone, path])
        self.assertEqual(plan["manuscripts"][0]["member"], "first.zip!second.zip!paper.pdf")
        path.write_bytes(zipped([("too-deep.zip", raw)]))
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "nesting depth"):
            gate.require_local(self.root, [self.root / "paper.pdf", standalone, path])

    def test_member_and_total_limits_are_enforced_across_archives(self):
        self.paper(); one = self.put("one.zip", zipped([("data.bin", b"x" * 20)]))
        two = self.put("two.zip", zipped([("data.bin", b"y" * 20)]))
        with mock.patch.object(gate, "MAX_MEMBER_BYTES", 19):
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "member exceeds"):
                gate.require_local(self.root, [self.root / "paper.pdf", one])
        with mock.patch.object(gate, "MAX_ARCHIVE_BYTES", 39):
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "total expanded"):
                gate.require_local(self.root, [self.root / "paper.pdf", one, two])

    def test_compressed_expansion_is_bounded_before_archive_parse(self):
        self.paper(); path = self.put("source.gz", gzip.compress(b"x" * 101))
        with mock.patch.object(gate, "MAX_ARCHIVE_BYTES", 100):
            with self.assertRaisesRegex(gate.ManuscriptPDFHold, "expansion exceeds"):
                gate.require_local(self.root, [self.root / "paper.pdf", path])

    def test_invalid_and_unsupported_archives_hold_cleanly(self):
        self.paper()
        for filename, raw in (("bad.zip", b"bad"), ("bad.tar", b"bad"), ("bad.zst", b"\x28\xb5\x2f\xfdbad"),
                              ("opaque.bin", b"7z\xbc\xaf\x27\x1c"), ("bad.rar", b"bad"), ("bad.gz", b"\x1f\x8bbad")):
            with self.subTest(filename=filename):
                path = self.put(filename, raw)
                with self.assertRaises(gate.ManuscriptPDFHold):
                    gate.require_local(self.root, [self.root / "paper.pdf", path])

    def test_zip_symlinks_cannot_be_mistaken_for_regular_pdf_bytes(self):
        self.paper(); target = BytesIO()
        with zipfile.ZipFile(target, "w") as archive:
            info = zipfile.ZipInfo("paper.pdf"); info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, SUMMARY)
        self.put("source.zip", target.getvalue())
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "regular file"):
            gate.require_local(self.root)

    def test_malformed_manifests_are_clean_holds(self):
        self.paper()
        for filename in ("MANUSCRIPT_PDFS.json", "DIGEST_MANIFEST.json"):
            for content in (b"[]", b"null", b'"string"', b"{", b"\xff"):
                with self.subTest(filename=filename, content=content):
                    path = self.put(filename, content)
                    with self.assertRaises(gate.ManuscriptPDFHold):
                        gate.require_local(self.root)
                    path.unlink()
        for field in (None, {}, 7, "string"):
            for key in ("uploads",):
                manifest = self.digest(); manifest[key] = field
                self.put("DIGEST_MANIFEST.json", json.dumps(manifest).encode())
                with self.assertRaises(gate.ManuscriptPDFHold):
                    gate.require_local(self.root)

    def test_complete_readback_includes_archives_and_rejects_extras_or_omissions(self):
        self.digest(); plan = gate.require_local(self.root); record = self.record(plan)
        seen = []
        def download(rid, name):
            self.assertEqual(rid, "123"); seen.append(name)
            return (self.root / name).read_bytes()
        receipt = gate.require_public(record, plan, download=download)
        self.assertEqual(set(seen), {p.name for p in self.root.iterdir()})
        self.assertEqual(len(receipt["upload_files"]), 4)
        self.assertEqual(len(receipt["pdfs"]), 2)
        for mode in ("extra", "missing", "duplicate"):
            with self.subTest(mode=mode):
                altered = json.loads(json.dumps(record))
                if mode == "extra": altered["files"].append({"key": "unexpected.txt", "size": 0, "checksum": "md5:" + hashlib.md5(b"").hexdigest()})
                elif mode == "missing": altered["files"] = [row for row in altered["files"] if row["key"] != "METHODS_NOTES.zip"]
                else: altered["files"].append(altered["files"][0])
                with self.assertRaises(gate.ManuscriptPDFHold):
                    gate.require_public(altered, plan, download=download)

    def test_public_archive_download_is_hash_bound(self):
        self.digest(); plan = gate.require_local(self.root)
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "downloaded upload differs"):
            gate.require_public(self.record(plan), plan,
                download=lambda rid, name: b"changed archive" if name == "METHODS_NOTES.zip" else (self.root / name).read_bytes())

    def test_public_preflight_without_complete_upload_binding_is_rejected(self):
        self.paper(); plan = gate.require_local(self.root); record = self.record(plan)
        del plan["upload_files"]
        with self.assertRaisesRegex(gate.ManuscriptPDFHold, "complete approved upload"):
            gate.require_public(record, plan)

    def test_public_download_is_anonymous_and_encodes_filename(self):
        opener = mock.Mock(); response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"file bytes"
        opener.open.return_value = response
        with mock.patch.object(gate.urllib.request, "build_opener", return_value=opener):
            self.assertEqual(gate.public_pdf_bytes("123", "A file.zip"), b"file bytes")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://zenodo.org/api/records/123/files/A%20file.zip/content")
        self.assertNotIn("Authorization", dict(request.header_items()))
        self.assertNotIn("access_token", request.full_url)


if __name__ == "__main__":
    unittest.main()
