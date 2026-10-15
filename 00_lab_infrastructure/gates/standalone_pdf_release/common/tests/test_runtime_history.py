from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import runtime_history as history


class RuntimeHistoryTests(unittest.TestCase):
    def test_git_reader_disables_lazy_network_fetch_and_object_replacements(self):
        with mock.patch.object(history.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=b"bytes")) as run:
            self.assertEqual(history._git(history.REPO, "cat-file", "blob", "a" * 40), b"bytes")
        self.assertEqual(run.call_args.kwargs["env"]["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual(run.call_args.kwargs["env"]["GIT_NO_REPLACE_OBJECTS"], "1")

    def test_original_505_rows_and_unselected_v013_are_preserved(self):
        manifest = json.loads(history.HISTORY.read_bytes())
        prior = [row for row in manifest["versions"] if row["version"] != "v013"]
        self.assertEqual(len(prior), 12)
        self.assertEqual(sum(len(row["files"]) for row in prior), 505)
        self.assertEqual(manifest["active_runtime_selected"], "v012")
        self.assertEqual(manifest["active_runtime_path"],
                         "00_lab_infrastructure/gates/standalone_pdf_release/runtime")
        self.assertIs(manifest["tags_created"], True)
        self.assertEqual(len(manifest["historical_tag_objects"]), 12)
        self.assertIn("no runtime admission", manifest["active_semantic_label"])
        self.assertEqual(sum(row["version"] == "v013" for row in manifest["versions"]), 1)

    def test_existing_v005_functional_fixture_bytes_keep_their_exact_hashes(self):
        expected = {"packaging_runtime.py": "409cd52b97474d28d2dbcf70a9005ea73ab6d9228e30aca757931d9c2fea6910",
                    "packaging_catalog.py": "f4c292657703180eb1b34d80fd6080216744db96a872e76e83b4761479410ff7"}
        for filename, digest in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(hashlib.sha256(history.historical_bytes("v005", filename)).hexdigest(), digest)

    def test_all_historical_rows_resolve_to_exact_local_blob_bytes(self):
        manifest = json.loads(history.HISTORY.read_bytes())
        for version in manifest["versions"]:
            prefix = history.PREFIX + version["version"] + "/"
            for row in version["files"]:
                raw = history.historical_bytes(version["version"], row["path"].removeprefix(prefix))
                self.assertEqual(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest(), row["blob_sha"])

    def test_no_historical_runtime_directories_are_required_on_disk(self):
        self.assertTrue((history.RELEASE / "runtime").is_dir())
        for number in range(1, 14):
            self.assertFalse((history.RELEASE / ("future_runtime_v" + str(number).zfill(3))).exists())
        self.assertIn(b"def predecessor_installation", history.historical_bytes("v011", "packaging_runtime.py"))

    def test_unknown_or_unsafe_requests_are_refused(self):
        for version, filename in (("v999", "packaging_runtime.py"), ("v005", "../outside.py"),
                                  ("v005", "/absolute.py"), ("v005", "missing.py"), ("v5", "packaging_runtime.py")):
            with self.subTest(version=version, filename=filename), self.assertRaises(history.RuntimeHistoryError):
                history.historical_bytes(version, filename)

    def test_rebound_blob_or_tree_does_not_bypass_reviewed_path(self):
        original = json.loads(history.HISTORY.read_bytes())
        for field in ("tree_sha", "blob_sha"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                changed = json.loads(json.dumps(original))
                entry = next(row for row in changed["versions"] if row["version"] == "v005")
                if field == "tree_sha": entry[field] = "0" * 40
                else: next(row for row in entry["files"] if row["path"].endswith("/packaging_runtime.py"))[field] = "0" * 40
                path = Path(temp) / "history.json"; path.write_text(json.dumps(changed))
                with self.assertRaises(history.RuntimeHistoryError):
                    history.historical_bytes("v005", "packaging_runtime.py", manifest=path)


if __name__ == "__main__":
    unittest.main()
