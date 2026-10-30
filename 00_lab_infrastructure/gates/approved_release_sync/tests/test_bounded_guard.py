"""Inert OS supervision cases; no Core source, credential or network use."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
import trusted_canon_adapter as adapter
from deadline import Budget, DeadlineExceeded


class PrimitiveGuard:
    def value(self): return {"status": "INERT_OK"}
    def process(self): return subprocess.CompletedProcess(["not-returned"], 2, "fixture", "redacted")
    def fail(self): raise RuntimeError("fixture-secret-never-forwarded")
    def oversized(self): return "x" * (2 * 1024 * 1024)
    def leave_descendant(self, marker, pidfile, *, block=False):
        code = "import pathlib,time;time.sleep(.5);pathlib.Path(" + repr(str(marker)) + ").write_text('late')"
        child = subprocess.Popen([sys.executable, "-c", code], close_fds=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Path(pidfile).write_text(str(child.pid))
        if block: time.sleep(60)
        return {"returned": True}


class BoundedGuardTests(unittest.TestCase):
    def test_real_owned_group_value_and_process_return(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(3, 1))
        self.assertEqual(guard.value(), {"status": "INERT_OK"})
        value = guard.process()
        self.assertEqual((value.returncode, value.stdout, value.stderr), (2, "fixture", "redacted"))
        self.assertEqual(value.args, [])

    def test_error_and_oversized_results_are_fixed_holds(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(3, 1))
        for operation in (guard.fail, guard.oversized):
            with self.subTest(operation=operation), self.assertRaises(adapter.sync.SyncHold) as caught:
                operation()
            self.assertNotIn("fixture-secret", str(caught.exception))

    def test_returning_with_a_live_descendant_holds_and_prevents_late_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); marker, pidfile = root / "late", root / "pid"
            guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(3, 1))
            with self.assertRaisesRegex(adapter.sync.SyncHold, "GROUP_NOT_QUIESCENT"):
                guard.leave_descendant(marker, pidfile)
            self.assertTrue(pidfile.is_file(), "The descendant must actually have been started")
            time.sleep(.6)
            self.assertFalse(marker.exists())

    def test_timeout_kills_owned_group_before_late_descendant_write(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve(); marker, pidfile = root / "late", root / "pid"
            guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(.2, 1))
            began = time.monotonic()
            with self.assertRaises(DeadlineExceeded): guard.leave_descendant(marker, pidfile, block=True)
            self.assertLess(time.monotonic() - began, 1.5)
            self.assertTrue(pidfile.is_file(), "The timed descendant must actually have started")
            time.sleep(.6)
            self.assertFalse(marker.exists())

    def test_group_observer_rejects_empty_malformed_missing_or_non_zombie_leader(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(3, 1))
        for text in ("", "bad\n", "1 1 Z\n", "123 123 S\n", "123 123 Z\n123 123 Z\n", "123 x Z\n"):
            with self.subTest(text=text), patch.object(adapter.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout=text)):
                with self.assertRaises(adapter.sync.SyncHold): guard._live_descendants(123)
        with patch.object(adapter.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="123 123 Z\n124 123 Z\n")):
            self.assertFalse(guard._live_descendants(123))
        with patch.object(adapter.subprocess, "run", return_value=SimpleNamespace(returncode=0, stdout="123 123 Z\n124 123 S\n")):
            self.assertTrue(guard._live_descendants(123))

    def test_cleanup_permission_error_is_uncatchable_by_ordinary_retry(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(1, 1))
        with patch.object(guard, "_signal", side_effect=PermissionError()), patch.object(guard, "_exited", return_value=None):
            with self.assertRaises(adapter.GuardQuiescenceHold): guard._cleanup(123, True)
        self.assertFalse(issubclass(adapter.GuardQuiescenceHold, Exception))

    def test_no_group_signal_before_acknowledged_isolation(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(1, 1))
        with patch.object(adapter.os, "kill") as direct, patch.object(adapter.os, "killpg") as group:
            guard._signal(123, False, 15)
            direct.assert_called_once_with(123, 15); group.assert_not_called()

    def test_parent_reaper_override_refuses_before_fork(self):
        guard = adapter.BoundedGuard(PrimitiveGuard(), Budget(1, 1))
        with patch.object(adapter.signal, "getsignal", return_value=adapter.signal.SIG_IGN), patch.object(adapter.os, "fork") as fork:
            with self.assertRaisesRegex(adapter.sync.SyncHold, "POSIX_SINGLE_THREAD"): guard.value()
            fork.assert_not_called()
