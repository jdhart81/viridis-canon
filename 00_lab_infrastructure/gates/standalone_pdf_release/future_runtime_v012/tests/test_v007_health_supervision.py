"""Harmless process/signal fixtures; no scientific or network calls."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import packaging_runtime as runtime


class HealthSupervisionTests(unittest.TestCase):
    def test_signal_unwinds_child_waiter_and_cannot_be_swallowed_by_scientific_fold(self):
        prior={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGALRM)}
        child=None;waited=[];outer_finally=[]
        with self.assertRaises(runtime.HealthSupervisionHold):
            try:
                with runtime.health_supervision_scope():
                    child=subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(30)'],
                                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    self.assertEqual(os.getpgid(child.pid),os.getpgid(os.getpid()))
                    try:
                        try:os.kill(os.getpid(),signal.SIGTERM)
                        except Exception:self.fail('original Exception fold swallowed supervisor abort')
                    finally:
                        child.terminate();waited.append(child.wait(timeout=3))
            finally:outer_finally.append(True)
        self.assertEqual(len(waited),1);self.assertNotEqual(waited[0],0)
        self.assertEqual(outer_finally,[True]);self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))
        self.assertEqual(prior,{sig:signal.getsignal(sig) for sig in prior})

    def test_scoped_alarm_is_fixed_cleanup_reserve_and_restored_on_success(self):
        calls=[];actual=signal.setitimer
        def observed(which,seconds,interval=0):
            calls.append((which,seconds,interval));return actual(which,seconds,interval)
        with patch.object(signal,'setitimer',side_effect=observed):
            with runtime.health_supervision_scope():pass
        self.assertEqual([value[1] for value in calls],[2940,0])
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))

    def test_existing_caller_timer_is_not_clobbered_or_accepted_as_authority(self):
        prior=signal.getsignal(signal.SIGALRM)
        try:
            signal.setitimer(signal.ITIMER_REAL,100)
            with self.assertRaisesRegex(runtime.PackagingHold,'NO_INHERITED_ACTIVE_TIMER'):
                with runtime.health_supervision_scope():self.fail('unexpected scope body')
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0],90)
            self.assertEqual(signal.getsignal(signal.SIGALRM),prior)
        finally:signal.setitimer(signal.ITIMER_REAL,0)

    def test_expired_cleanup_reserve_cannot_report_normal_success(self):
        with patch.object(runtime.time,'monotonic',side_effect=[100,3040]),\
             self.assertRaisesRegex(runtime.PackagingHold,'CLEANUP_RESERVE_EXPIRED'):
            with runtime.health_supervision_scope():pass
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.0,0.0))


if __name__=='__main__':unittest.main()
