"""Real flock/process tests in disposable directories; never touch actual Core."""
from contextlib import contextmanager
import json
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

GATE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GATE))
from core_writer_lock import WriterSession, WriterBusy, WriterLockHold, LOCK_NAME, FD_ENV

PRELUDE = '''import os,sys,time,subprocess
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from core_writer_lock import WriterSession,writer_session,FD_ENV
root=Path(sys.argv[1])
'''


class ProcessLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.processes = []
        self.addCleanup(self.clean_processes)

    def clean_processes(self):
        (self.root / 'RELEASE_CHILD').touch()
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=3)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:stream.close()

    def spawn(self, script):
        process = subprocess.Popen([sys.executable,'-I','-B','-u','-c',PRELUDE+script,str(self.root),str(GATE)],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.processes.append(process);return process

    def line(self, process):
        import selectors
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(selector.select(timeout=5), 'Fixture child did not reach the expected lifecycle barrier')
        line = process.stdout.readline().strip()
        if not line:
            self.fail('Fixture child ended before barrier: '+process.stderr.read())
        return line

    def advance(self, process):
        process.stdin.write('continue\n');process.stdin.flush()

    def assert_busy(self):
        with self.assertRaises(WriterBusy):
            WriterSession.acquire(self.root)

    def await_available(self):
        end = time.monotonic()+5
        while True:
            try:
                session=WriterSession.acquire(self.root);session.close();return
            except WriterBusy:
                if time.monotonic()>=end:self.fail('Writer descriptor survived fixture completion')
                time.sleep(0.01)

    def test_parent_holds_across_begin_return_model_gap_finish_coverage_and_closeout(self):
        # This is a synthetic real parent/child lifecycle, NOT evidence that the
        # current host LLM scheduler has such a parent hook.
        process=self.spawn('''
with writer_session(root) as session:
    for phase in ('BEGIN_RETURNED','MODEL_TOOL_GAP','FINISH_COVERAGE_RETURNED','CLOSEOUT_RETURNED'):
        child_code="import os,sys;sys.path.insert(0,sys.argv[1]);from core_writer_lock import WriterSession,FD_ENV;from pathlib import Path;session=WriterSession.inherited(Path(sys.argv[2]),int(os.environ[FD_ENV]));session.assert_owned();session.close()"
        child=subprocess.run([sys.executable,'-I','-B','-c',child_code,sys.argv[2],str(root)],**session.child_options())
        if child.returncode:raise RuntimeError('writer child failed')
        print(phase,flush=True)
        if not sys.stdin.readline():raise RuntimeError('fixture cancelled')
print('RELEASED',flush=True)
''')
        for phase in ('BEGIN_RETURNED','MODEL_TOOL_GAP','FINISH_COVERAGE_RETURNED','CLOSEOUT_RETURNED'):
            self.assertEqual(self.line(process),phase)
            self.assert_busy()
            self.advance(process)
        self.assertEqual(self.line(process),'RELEASED')
        self.assertEqual(process.wait(timeout=3),0)
        self.await_available()

    def surviving_child_fixture(self, *, kill_parent=False):
        child_code = """import os,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[2])
from core_writer_lock import WriterSession,FD_ENV
root=Path(sys.argv[1])
with WriterSession.inherited(root,int(os.environ[FD_ENV])) as session:
    session.assert_owned()
    print('CHILD_READY',flush=True)
    while not (root/'RELEASE_CHILD').exists():time.sleep(0.01)
"""
        script = '''
with writer_session(root) as session:
    child=subprocess.Popen([sys.executable,'-I','-B','-u','-c',CHILD_CODE,str(root),sys.argv[2]],
        stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,**session.child_options())
    if child.stdout.readline().strip()!='CHILD_READY':raise RuntimeError('child not ready')
    print('DESCENDANT_READY',flush=True)
    if KILL_PARENT:sys.stdin.readline()
print('PARENT_EXIT',flush=True)
'''.replace('CHILD_CODE',repr(child_code)).replace('KILL_PARENT',repr(kill_parent))
        process=self.spawn(script)
        self.assertEqual(self.line(process),'DESCENDANT_READY')
        if kill_parent:
            process.terminate();process.wait(timeout=3)
        else:
            self.assertEqual(self.line(process),'PARENT_EXIT');self.assertEqual(process.wait(timeout=3),0)
        try:
            self.assert_busy()
        finally:
            (self.root/'RELEASE_CHILD').touch()
        self.await_available()

    def test_parent_close_cannot_unlock_surviving_writer_child(self):
        self.surviving_child_fixture()

    def test_abrupt_parent_exit_keeps_child_writer_excluded_until_child_exit(self):
        self.surviving_child_fixture(kill_parent=True)

    def test_stale_metadata_never_steals_a_live_os_lock(self):
        path=self.root/LOCK_NAME
        path.write_text('{"pid":0,"heartbeat":"1970-01-01","status":"RELEASED"}')
        process=self.spawn('''
with writer_session(root):
    print('HELD',flush=True)
    sys.stdin.readline()
''')
        self.assertEqual(self.line(process),'HELD')
        before=path.read_bytes();self.assert_busy();self.assertEqual(path.read_bytes(),before)
        self.advance(process);process.wait(timeout=3);self.await_available()

    def test_existing_file_without_kernel_owner_is_available(self):
        (self.root/LOCK_NAME).write_text('{"status":"HELD","pid":999999999}')
        with WriterSession.acquire(self.root) as session:session.assert_owned()
        self.await_available()

    def test_unlocked_descriptor_is_not_a_session_capability(self):
        path=self.root/LOCK_NAME;path.touch(mode=0o600)
        fd=os.open(path,os.O_RDWR)
        try:
            with self.assertRaisesRegex(WriterLockHold,'NOT_EXCLUSIVELY_LOCKED'):
                WriterSession.inherited(self.root,fd)
        finally:os.close(fd)
        self.await_available()

    def test_shared_lock_descriptor_cannot_be_upgraded_and_claimed_as_exclusive_session(self):
        path=self.root/LOCK_NAME;path.touch(mode=0o600);fd=os.open(path,os.O_RDWR)
        try:
            fcntl.flock(fd,fcntl.LOCK_SH|fcntl.LOCK_NB)
            with self.assertRaisesRegex(WriterLockHold,'NOT_EXCLUSIVELY_LOCKED'):
                WriterSession.inherited(self.root,fd)
        finally:os.close(fd)
        self.await_available()

    def test_unrelated_open_of_owned_inode_is_not_owner(self):
        with WriterSession.acquire(self.root) as owner:
            fd=os.open(self.root/LOCK_NAME,os.O_RDWR)
            try:
                with self.assertRaisesRegex(WriterLockHold,'NOT_SESSION_OWNER'):
                    WriterSession.inherited(self.root,fd)
            finally:os.close(fd)
            owner.assert_owned()

    def test_owner_release_interleaving_establishes_only_current_exclusion_not_session_lineage(self):
        owner=WriterSession.acquire(self.root)
        unrelated=os.open(self.root/LOCK_NAME,os.O_RDWR)
        real_flock=fcntl.flock;released=[]
        def release_after_blocked_probe(fd,operation):
            try:return real_flock(fd,operation)
            except BlockingIOError:
                if operation==(fcntl.LOCK_SH|fcntl.LOCK_NB) and not released:
                    owner.close();released.append(True)
                raise
        joined=None
        try:
            with patch('core_writer_lock.fcntl.flock',side_effect=release_after_blocked_probe):
                joined=WriterSession.inherited(self.root,unrelated)
            self.assertEqual(released,[True])
            # This unrelated fd acquired a NEW exclusive lock after the old
            # owner's real close. It is safe current exclusion, not proof of
            # authenticated historical session continuity.
            joined.assert_owned();self.assert_busy()
        finally:
            if joined is not None:joined.close()
            os.close(unrelated);owner.close()
        self.await_available()

    def test_symlink_fifo_and_hardlink_are_refused(self):
        path=self.root/LOCK_NAME;target=self.root/'protected';target.write_bytes(b'unchanged')
        path.symlink_to(target)
        with self.assertRaises(WriterLockHold):WriterSession.acquire(self.root)
        self.assertEqual(target.read_bytes(),b'unchanged');path.unlink()
        os.mkfifo(path)
        with self.assertRaises(WriterLockHold):WriterSession.acquire(self.root)
        path.unlink();os.link(target,path)
        with self.assertRaises(WriterLockHold):WriterSession.acquire(self.root)
        self.assertEqual(target.read_bytes(),b'unchanged')

    def test_replaced_canonical_inode_invalidates_existing_writer_guard(self):
        with WriterSession.acquire(self.root) as session:
            path=self.root/LOCK_NAME;path.rename(self.root/'old-inode')
            path.touch(mode=0o600)
            with self.assertRaisesRegex(WriterLockHold,'PATH_REPLACED'):session.assert_owned()
        self.assertTrue((self.root/'old-inode').exists())


if __name__=='__main__':unittest.main()
