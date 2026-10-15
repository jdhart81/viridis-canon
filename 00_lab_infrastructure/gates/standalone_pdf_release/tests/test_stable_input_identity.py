"""Prepared I-9 checks; every mutation is confined to disposable temp inputs."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common"))
import stable_input_identity as identity


class StableInputIdentityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.path = self.root / "input.bin"
        self.path.write_bytes(b"approved bytes")

    def test_tuple_is_exact_sha_size_mtime_inode_device(self):
        snapshot = identity.read_stable(self.path); observed = self.path.stat()
        self.assertEqual(snapshot.identity, (hashlib.sha256(b"approved bytes").hexdigest(),
            observed.st_size, observed.st_mtime_ns, observed.st_ino, observed.st_dev))
        self.assertEqual(snapshot.data, b"approved bytes")
        self.assertNotIn("st_ctime", Path(identity.__file__).read_text())

    def test_chmod_metadata_change_preserves_identity(self):
        baseline = identity.read_stable(self.path)
        self.path.chmod(stat.S_IRUSR)
        self.assertEqual(identity.read_stable(self.path, expected=baseline.identity), baseline)

    def test_xattr_metadata_change_preserves_identity(self):
        baseline = identity.read_stable(self.path)
        name = "com.viridis.identity.test" if sys.platform == "darwin" else "user.viridis.identity.test"
        if hasattr(os, "setxattr"):
            try:
                os.setxattr(self.path, name, b"metadata only")
            except OSError as exc:
                self.skipTest("temporary filesystem xattrs unavailable: " + type(exc).__name__)
        elif sys.platform == "darwin" and shutil.which("xattr"):
            result = subprocess.run(["xattr", "-w", name, "metadata only", str(self.path)], capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, "temporary xattr mutation failed")
        else:
            self.skipTest("platform does not provide xattrs")
        self.assertEqual(identity.read_stable(self.path, expected=baseline.identity), baseline)

    def test_same_size_content_change_with_restored_mtime_fails(self):
        baseline = identity.read_stable(self.path); before = self.path.stat()
        changed = b"different data"; self.assertEqual(len(changed), len(baseline.data))
        self.path.write_bytes(changed)
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
        with self.assertRaisesRegex(identity.StableInputHold, "approved content identity"):
            identity.read_stable(self.path, expected=baseline.identity)

    def test_mutation_between_reads_fails_even_when_metadata_is_restored(self):
        before = self.path.stat(); original = identity._read_once; calls = 0
        def mutate(descriptor, limit):
            nonlocal calls
            raw = original(descriptor, limit); calls += 1
            if calls == 1:
                self.path.write_bytes(b"different data")
                os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns))
            return raw
        with mock.patch.object(identity, "_read_once", mutate):
            with self.assertRaisesRegex(identity.StableInputHold, "during read"):
                identity.read_stable(self.path)

    def test_inode_replacement_fails_even_with_identical_bytes_and_mtime(self):
        baseline = identity.read_stable(self.path); before = self.path.stat()
        replacement = self.root / "replacement.bin"; replacement.write_bytes(baseline.data)
        os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns)); replacement.replace(self.path)
        with self.assertRaisesRegex(identity.StableInputHold, "approved content identity"):
            identity.read_stable(self.path, expected=baseline.identity)

    def test_mtime_change_fails_with_identical_content(self):
        baseline = identity.read_stable(self.path); before = self.path.stat()
        os.utime(self.path, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
        with self.assertRaises(identity.StableInputHold):
            identity.read_stable(self.path, expected=baseline.identity)

    def test_symlink_and_parent_symlink_are_refused(self):
        link = self.root / "link.bin"; link.symlink_to(self.path)
        with self.assertRaises(identity.StableInputHold):
            identity.read_stable(link)
        folder = self.root / "parent"; folder.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(identity.StableInputHold):
            identity.read_stable(folder / "input.bin")

    def test_directory_and_overlimit_input_are_refused(self):
        with self.assertRaises(identity.StableInputHold):
            identity.read_stable(self.root)
        with self.assertRaisesRegex(identity.StableInputHold, "byte limit"):
            identity.read_stable(self.path, max_bytes=1)


if __name__ == "__main__":
    unittest.main()
