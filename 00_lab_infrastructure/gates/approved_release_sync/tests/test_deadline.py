"""Only synthetic clocks and tiny inert sleeps; no runtime/Core imports."""
import importlib.util
from pathlib import Path
import signal
import threading
import time
import unittest

PATH = Path(__file__).resolve().parents[1] / "runtime/deadline.py"
spec = importlib.util.spec_from_file_location("approved_release_deadline_tests", PATH)
deadline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deadline)


class BudgetTests(unittest.TestCase):
    def test_one_absolute_budget_caps_later_stages_and_cleanup(self):
        now = [10.0]
        budget = deadline.Budget(clock=lambda: now[0])
        self.assertEqual(budget.remaining_cap(999), 540)
        now[0] += 535
        self.assertEqual(budget.remaining_cap(60), 5)
        now[0] += 5
        with self.assertRaises(deadline.DeadlineExceeded): budget.require_remaining()
        self.assertEqual(budget.cleanup_remaining_cap(999), 30)
        now[0] += 30
        with self.assertRaises(deadline.DeadlineExceeded): budget.cleanup_remaining_cap(1)

    def test_invalid_or_extended_budget_rejected(self):
        for args in [(601, 0), (540, 61), (True, 30), (float("inf"), 0), (float("nan"), 0), (0, 30), (1, -1)]:
            with self.subTest(args=args), self.assertRaises(ValueError): deadline.Budget(*args)

    def test_retry_sleep_cannot_restart_or_extend_budget(self):
        now = [0.0]
        def sleep(seconds): now[0] += seconds
        budget = deadline.Budget(10, 2, clock=lambda: now[0], sleeper=sleep)
        budget.sleep(6)
        self.assertEqual(budget.require_remaining(), 4)
        with self.assertRaises(deadline.DeadlineExceeded): budget.sleep(4)
        self.assertEqual(now[0], 6)

    def test_blocking_inherited_exception_retry_loop_is_interrupted(self):
        budget = deadline.Budget(0.03, 0.03)
        def catches_ordinary_errors():
            while True:
                try: time.sleep(10)
                except Exception: pass
        began = time.monotonic()
        with self.assertRaises(deadline.DeadlineExceeded): budget.call(catches_ordinary_errors)
        self.assertLess(time.monotonic() - began, 0.5)
        self.assertGreater(budget.cleanup_remaining_cap(1), 0)

    def test_nested_call_does_not_reset_outer_alarm(self):
        budget = deadline.Budget(0.03, 0.03)
        began = time.monotonic()
        with self.assertRaises(deadline.DeadlineExceeded): budget.call(lambda: budget.call(time.sleep, 2))
        self.assertLess(time.monotonic() - began, 0.5)

    def test_previous_handler_and_remaining_alarm_are_restored(self):
        old_handler = signal.getsignal(signal.SIGALRM)
        old_timer = signal.getitimer(signal.ITIMER_REAL)
        handler = lambda *_args: None
        try:
            signal.signal(signal.SIGALRM, handler)
            signal.setitimer(signal.ITIMER_REAL, 2, 0.7)
            budget = deadline.Budget(0.5, 0.1)
            self.assertEqual(budget.call(lambda: (time.sleep(0.01), "ok")[1]), "ok")
            remaining, interval = signal.getitimer(signal.ITIMER_REAL)
            self.assertIs(signal.getsignal(signal.SIGALRM), handler)
            self.assertGreater(remaining, 1.5)
            self.assertLess(remaining, 2)
            self.assertAlmostEqual(interval, 0.7)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)
            if old_timer[0] > 0: signal.setitimer(signal.ITIMER_REAL, *old_timer)

    def test_non_main_thread_fails_closed_before_function(self):
        called, errors = [], []
        budget = deadline.Budget()
        def worker():
            try: budget.call(lambda: called.append(True))
            except RuntimeError as error: errors.append(str(error))
        thread = threading.Thread(target=worker)
        thread.start(); thread.join(0.5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(called, [])
        self.assertEqual(errors, ["Bounded inherited calls require the POSIX main thread"])


if __name__ == "__main__": unittest.main()
