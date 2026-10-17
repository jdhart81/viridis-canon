"""One absolute budget for an approved descriptive release continuation.

Every blocking operation receives the same Budget. Active work has 540 seconds
by default, followed by a 30 second durable-cleanup reserve. Neither stage nor
retry creates a new budget. A caller must also retain its outer process/job cap.
"""
from __future__ import annotations

import math
import signal
import threading
import time


class DeadlineExceeded(TimeoutError):
    """The shared active or cleanup deadline has expired."""


class _DeadlineInterrupt(BaseException):
    """Escape inherited retry loops which catch ordinary Exception instances."""


def _seconds(value, *, zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Deadline durations must be finite numbers")
    if value < 0 or (not zero and value == 0):
        raise ValueError("Deadline duration is outside its allowed range")
    return float(value)


class Budget:
    def __init__(self, active_seconds=540, cleanup_seconds=30, *, clock=time.monotonic, sleeper=time.sleep):
        active = _seconds(active_seconds)
        cleanup = _seconds(cleanup_seconds, zero=True)
        if active + cleanup > 600:
            raise ValueError("The complete release budget must not exceed 600 seconds")
        self._clock, self._sleeper = clock, sleeper
        self._started = clock()
        self._active_deadline = self._started + active
        self._cleanup_deadline = self._active_deadline + cleanup
        self._call_depth = 0

    def require_remaining(self):
        remaining = self._active_deadline - self._clock()
        if remaining <= 0:
            raise DeadlineExceeded("APPROVED_RELEASE_ACTIVE_DEADLINE_EXHAUSTED")
        return remaining

    def remaining_cap(self, cap_seconds):
        return min(_seconds(cap_seconds), self.require_remaining())

    def cleanup_remaining_cap(self, cap_seconds):
        cap = _seconds(cap_seconds)
        remaining = self._cleanup_deadline - self._clock()
        if remaining <= 0:
            raise DeadlineExceeded("APPROVED_RELEASE_CLEANUP_DEADLINE_EXHAUSTED")
        return min(cap, remaining)

    def sleep(self, seconds):
        duration = _seconds(seconds, zero=True)
        if duration >= self.require_remaining():
            raise DeadlineExceeded("APPROVED_RELEASE_RETRY_WOULD_EXCEED_DEADLINE")
        self._sleeper(duration)
        self.require_remaining()

    def call(self, function, *args, **kwargs):
        """Bound an inherited blocking call without modifying its frozen source.

        POSIX/main-thread use is mandatory. An internal BaseException escapes
        ordinary inherited retry handlers, then becomes a normal TimeoutError
        at this outer boundary. Nested calls share the already-running timer.
        An earlier ambient alarm is an earlier wrapper boundary, reported as
        DeadlineExceeded here; its own handler is restored only after the call.
        Its elapsed-adjusted timer is restored, including already-due delivery.
        This alarm alone is not a process-tree supervisor: the owning entry must
        also cap/reap its process group and bound child transports explicitly.
        """
        remaining = self.require_remaining()
        if threading.current_thread() is not threading.main_thread() or not hasattr(signal, "setitimer"):
            raise RuntimeError("Bounded inherited calls require the POSIX main thread")
        if self._call_depth:
            return function(*args, **kwargs)
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_delay, previous_interval = signal.getitimer(signal.ITIMER_REAL)
        began = time.monotonic()
        delay = min(remaining, previous_delay) if previous_delay > 0 else remaining

        def interrupt(_signum, _frame):
            raise _DeadlineInterrupt()

        self._call_depth = 1
        signal.signal(signal.SIGALRM, interrupt)
        signal.setitimer(signal.ITIMER_REAL, delay)
        try:
            try:
                result = function(*args, **kwargs)
                self.require_remaining()
                return result
            except _DeadlineInterrupt:
                raise DeadlineExceeded("APPROVED_RELEASE_BLOCKING_CALL_DEADLINE_EXHAUSTED") from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_handler)
            elapsed = time.monotonic() - began
            self._call_depth = 0
            if previous_delay > 0:
                restored = previous_delay - elapsed
                if restored <= 0:
                    restored = previous_interval - ((elapsed - previous_delay) % previous_interval) if previous_interval > 0 else 0.000001
                signal.setitimer(signal.ITIMER_REAL, restored, previous_interval)
