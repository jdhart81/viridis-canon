import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location("leak_scan_under_test", Path(__file__).resolve().parents[1] / "token_leak_scan.py")
SCAN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCAN)
TOKEN = "DUMMY_SCAN_CREDENTIAL_" + "x" * 40


class LeakScanTests(unittest.TestCase):
    def test_stream_finds_matches_split_across_chunks(self):
        for size in (1, 7, 30, 64, 1024):
            with self.subTest(size=size):
                self.assertEqual(SCAN.count_stream(io.BytesIO(b"prefix" + TOKEN.encode() + b"gap" + TOKEN.encode()), TOKEN.encode(), size), 2)

    def test_scan_output_contains_only_counts_and_sanitized_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            token_file = root / "secret.md"
            token_file.write_text("# API token\n" + TOKEN + "\n")
            leak = root / ("receipt-" + TOKEN + ".json")
            leak.write_text(json.dumps({"unexpected": TOKEN}))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = SCAN.main(["--token-file", str(token_file), str(root)])
            self.assertEqual(result, 1)
            self.assertNotIn(TOKEN, out.getvalue())
            report = json.loads(out.getvalue())
            self.assertEqual(report["hit_count"], 2)
            self.assertEqual(report["scanned_files"], 1)
            self.assertIn("***", report["paths"][0]["path"])

    def test_missing_input_is_scan_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            token_file = root / "secret.md"
            token_file.write_text(TOKEN)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                result = SCAN.main(["--token-file", str(token_file), str(root / "missing")])
            self.assertEqual(result, 2)
            self.assertEqual(json.loads(out.getvalue())["hit_count"], 0)

    def test_symlinks_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            token_file = root / "secret.md"
            token_file.write_text(TOKEN)
            (root / "alias").symlink_to(token_file)
            result = SCAN.scan_paths([root], TOKEN.encode(), token_file)
            self.assertTrue(result["unreadable_paths"])

    def test_git_scan_includes_commit_message_and_tracked_blobs(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            def git(*args):
                return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
            git("init", "--quiet")
            git("config", "user.email", "dummy@example.invalid")
            git("config", "user.name", "Dummy Test")
            (repo / "receipt.txt").write_text(TOKEN)
            git("add", "receipt.txt")
            git("commit", "--quiet", "-m", "Dummy " + TOKEN)
            report = SCAN.scan_commit(repo, "HEAD", TOKEN.encode())
            self.assertEqual(report["hit_count"], 2)
            self.assertEqual(report["scanned_files"], 1)


if __name__ == "__main__":
    unittest.main()
