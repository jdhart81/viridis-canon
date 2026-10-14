"""Exercise the active read paths on disposable inputs, never live science."""
import contextlib
import hashlib
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import packaging_runtime as runtime
import packaging_catalog as catalog
import test_packaging_v003_data_alias as aliases
import test_packaging_v004_platform_timezone as timezone_fixture


def same_mode_chmod(path, *, follow_symlinks=True):
    before = path.stat(follow_symlinks=follow_symlinks)
    time.sleep(0.002)
    if follow_symlinks:
        path.chmod(stat.S_IMODE(before.st_mode))
    else:
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns), follow_symlinks=False)
    return before, path.stat(follow_symlinks=follow_symlinks)


class ActiveStableInputTests(unittest.TestCase):
    def test_actual_adapter_identity_is_exact_sha_size_mtime_inode_device(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary).resolve() / "input.bin"; path.write_bytes(b"approved")
            value = runtime.read_stable_input(path); observed = path.stat()
            self.assertEqual(value.identity, (hashlib.sha256(value.data).hexdigest(),
                observed.st_size, observed.st_mtime_ns, observed.st_ino, observed.st_dev))

    def test_active_runtime_reader_accepts_real_ctime_only_change_during_read(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / "input.bin"; path.write_bytes(b"approved")
            old = Path.read_bytes; changed = []
            def read(current):
                raw = old(current)
                if current == path and not changed:
                    changed.append(same_mode_chmod(path))
                return raw
            with patch.object(Path, "read_bytes", read), runtime.json_data_scope(root):
                self.assertEqual(runtime.read_data_file(root, path)[1], b"approved")
            self.assertNotEqual(changed[0][0].st_ctime_ns, changed[0][1].st_ctime_ns)

    def test_active_scientific_record_accepts_ctime_only_then_rechecks_unchanged_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); owner = root / "evidence"; owner.mkdir()
            path = root / "input.bin"; path.write_bytes(b"approved")
            data = catalog.ScientificInputData(root, SimpleNamespace(owner_evidence_directory=owner))
            data.record(path); before = dict(data.inputs[str(path)])
            first, last = same_mode_chmod(path); data.record(path)
            self.assertNotEqual(first.st_ctime_ns, last.st_ctime_ns)
            self.assertEqual(runtime.input_row_identity(before), runtime.input_row_identity(data.inputs[str(path)]))
            self.assertEqual(list(owner.iterdir()), [])

    def test_same_size_content_change_with_restored_mtime_holds_in_actual_record(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / "input.bin"; path.write_bytes(b"approved")
            data = catalog.ScientificInputData(root, SimpleNamespace())
            data.record(path); before = path.stat(); path.write_bytes(b"rejected")
            os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
            with self.assertRaisesRegex(runtime.PackagingHold, "SCIENTIFIC_INPUT_CHANGED"):
                data.record(path)

    def test_content_change_during_read_with_restored_mtime_is_not_a_ctime_waiver(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / "input.bin"; path.write_bytes(b"approved")
            before = path.stat(); old = Path.read_bytes; changed = []
            def read(current):
                raw = old(current)
                if current == path and not changed:
                    changed.append(True); path.write_bytes(b"rejected")
                    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
                return raw
            with patch.object(Path, "read_bytes", read):
                with self.assertRaisesRegex(runtime.PackagingHold, "SOURCE_HASH_OR_RACE"):
                    runtime.read_data_file(root, path)

    def test_active_owned_reader_accepts_ctime_only_change(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); owner = root / "owner"; path = owner / "bytes/input.bin"
            path.parent.mkdir(parents=True); path.write_bytes(b"approved")
            data = catalog.ScientificInputData(root, SimpleNamespace(owner_evidence_directory=owner))
            science = catalog._SCIENCE.set(data); capture = catalog._READ_CAPTURE.set(data)
            try:
                self.assertEqual(data.read_owned(path), b"approved")
                same_mode_chmod(path)
                self.assertEqual(data.read_owned(path), b"approved")
            finally:
                catalog._READ_CAPTURE.reset(capture); catalog._SCIENCE.reset(science)

    def test_original_security_mode_guard_remains_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); path = root / "input.bin"; path.write_bytes(b"approved")
            data = catalog.ScientificInputData(root, SimpleNamespace()); data.record(path)
            before = runtime.read_stable_input(path).identity; path.chmod(0o400)
            self.assertEqual(runtime.read_stable_input(path).identity, before)
            with self.assertRaisesRegex(runtime.PackagingHold, "SCIENTIFIC_INPUT_CHANGED"):
                data.record(path)

    def test_directory_ctime_only_change_preserves_original_topology_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); directory = root / "inputs"; directory.mkdir()
            data = catalog.ScientificInputData(root, SimpleNamespace())
            original = data.data_path; calls = []
            def observe(path):
                calls.append(path)
                if len(calls) == 2:
                    before, after = same_mode_chmod(directory)
                    self.assertNotEqual(before.st_ctime_ns, after.st_ctime_ns)
                return original(path)
            with patch.object(data, "data_path", observe):
                data.record(directory)

    def test_directory_mtime_change_still_holds_during_original_topology_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve(); directory = root / "inputs"; directory.mkdir()
            data = catalog.ScientificInputData(root, SimpleNamespace())
            original = data.data_path; calls = []
            def observe(path):
                calls.append(path)
                if len(calls) == 2:
                    before = directory.stat()
                    os.utime(directory, ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000))
                return original(path)
            with patch.object(data, "data_path", observe):
                with self.assertRaisesRegex(runtime.PackagingHold, "SCIENTIFIC_INPUT_PATH_READ_RACE"):
                    data.record(directory)

    def test_historical_alias_link_ctime_is_diagnostic_only(self):
        with aliases.alias_fixture() as fixture:
            data = catalog.ScientificInputData(fixture.root, fixture.context, data_alias_observation=fixture.binding)
            first, last = same_mode_chmod(fixture.alias, follow_symlinks=False)
            self.assertNotEqual(first.st_ctime_ns, last.st_ctime_ns)
            data.alias_guard(complete=True); data.record(fixture.logical)
            self.assertEqual(data.inputs[str(fixture.logical)]["sha256"], runtime.sha(fixture.physical.read_bytes()))

    def test_native_timezone_leaf_and_resolution_link_ctime_are_diagnostic_only(self):
        with timezone_fixture.native_fixture() as fixture:
            observation = fixture.observation
            same_mode_chmod(fixture.physical)
            for link in fixture.links:
                same_mode_chmod(link, follow_symlinks=False)
            actual = runtime.platform_timezone_frame(observation)
            self.assertEqual(actual["sha256"], observation["after"]["sha256"])

    def test_native_timezone_content_change_still_holds_with_restored_mtime(self):
        with timezone_fixture.native_fixture() as fixture:
            before = fixture.physical.stat(); raw = fixture.physical.read_bytes()
            fixture.physical.write_bytes(raw[:10] + b"x" + raw[11:])
            os.utime(fixture.physical, ns=(before.st_atime_ns, before.st_mtime_ns))
            with self.assertRaisesRegex(runtime.PackagingHold, "NATIVE_TIMEZONE_CONTENT_IDENTITY"):
                runtime.platform_timezone_frame(fixture.observation)


if __name__ == "__main__":
    unittest.main()
