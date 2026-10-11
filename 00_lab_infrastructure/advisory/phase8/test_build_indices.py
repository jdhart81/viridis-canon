import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from build_indices import canon_index, mathlib_index, write_new


class IndexTests(unittest.TestCase):
    def test_mathlib_reads_exact_source_without_extracting_or_compiling(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.tar.gz"
            source = b"theorem identity (p : Prop) : p = p := rfl\n"
            with tarfile.open(path, "w:gz") as tar:
                item = tarfile.TarInfo("mathlib4-" + "a" * 40 + "/Mathlib/Test.lean")
                item.size = len(source)
                tar.addfile(item, io.BytesIO(source))
            result = mathlib_index(path, "a" * 40)
            self.assertTrue(result["snapshot"]["complete"])
            self.assertEqual(result["items"][0]["text"].encode(), source)
            self.assertEqual(result["items"][0]["content_sha256"], hashlib.sha256(source).hexdigest())
            self.assertEqual(list(Path(folder).iterdir()), [path])

    def test_source_symlink_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.tar.gz"
            with tarfile.open(path, "w:gz") as tar:
                item = tarfile.TarInfo("mathlib4-" + "a" * 40 + "/Mathlib/Test.lean")
                item.type = tarfile.SYMTYPE
                item.linkname = "/etc/passwd"
                tar.addfile(item)
            with self.assertRaises(ValueError):
                mathlib_index(path, "a" * 40)

    def test_wrong_revision_archive_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.tar.gz"
            with tarfile.open(path, "w:gz") as tar:
                item = tarfile.TarInfo("mathlib4-" + "b" * 40 + "/Mathlib/Test.lean")
                item.size = 1
                tar.addfile(item, io.BytesIO(b"x"))
            with self.assertRaises(ValueError):
                mathlib_index(path, "a" * 40)

    def test_canon_local_links_are_explicit_uris(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            mirror = root / "science-engine/07_nightly_engine/compound research papers/Run-194_test"
            mirror.mkdir(parents=True)
            (mirror / "paper.tex").write_text("A source claim, not verification evidence.")
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"records": [{"title": "Old claim", "doi": "10.5281/zenodo.1"},
                                                       {"title": "One", "source_url": "https://example.org/source1"},
                                                       {"title": "Two", "paper_url": "https://example.org/source2"}],
                                           "methods_digests": [{"doi": "10.5281/zenodo.2", "notes": [{"run_id": "Run-193"}, {"run_id": "Run-192"}]}]}))
            result = canon_index(root, catalog)
            self.assertEqual(result["snapshot"]["mirror_papers"], 1)
            local = result["items"][-1]
            self.assertTrue(local["url"].startswith("file://"))
            self.assertEqual(local["content_sha256"], hashlib.sha256((mirror / "paper.tex").read_bytes()).hexdigest())
            self.assertNotIn("CERTIFIED", local["text"])
            self.assertEqual(result["items"][1]["url"], "https://example.org/source1")
            self.assertEqual(result["items"][2]["url"], "https://example.org/source2")
            self.assertEqual(local["text_sha256"], local["content_sha256"])
            self.assertIn("Run-193", result["items"][3]["text"])
            self.assertIn("Run-192", result["items"][3]["text"])
            self.assertEqual(len(result["items"]), 5)

    def test_missing_mirror_cannot_be_marked_complete(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"records": [{"title": "Old claim"}], "methods_digests": [{"doi": "10.5281/zenodo.2"}]}))
            with self.assertRaises(ValueError):
                canon_index(root, catalog)

    def test_index_outputs_immutable(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "index.json"
            write_new(p, {"items": []})
            with self.assertRaises(FileExistsError):
                write_new(p, {"items": ["different"]})


if __name__ == "__main__":
    unittest.main()
