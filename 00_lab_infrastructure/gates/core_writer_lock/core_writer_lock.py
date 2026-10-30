"""Inactive Core writer-session flock primitive. Never unlink or TTL-unlock it.

Only a host or actual parent process owning the complete write session may
acquire this lock. Running this wrapper around a single checkpoint command
DOES NOT lock an LLM's intervening tool calls; see INTEGRATION_GAP.md.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import sys

CANONICAL_CORE = Path('/Users/justinhart/Desktop/Cowork /Viridis Core docs 2.0')
LOCK_NAME = '.viridis-core-writer.lock'
FD_ENV = 'VIRIDIS_CORE_WRITER_FD'


class WriterLockHold(RuntimeError):
    pass


class WriterBusy(WriterLockHold):
    pass


def _root(core_root):
    root = Path(core_root).absolute()
    if '..' in root.parts or any(p.is_symlink() for p in (root, *root.parents)) or not root.is_dir():
        raise WriterLockHold('HOLD_CANONICAL_CORE_DIRECTORY')
    return root


def _regular(descriptor):
    state = os.fstat(descriptor)
    if not stat.S_ISREG(state.st_mode) or state.st_nlink != 1 or state.st_mode & 0o022:
        raise WriterLockHold('HOLD_REGULAR_PRIVATE_LOCK_INODE')
    return state


def _identity(state):
    return state.st_dev, state.st_ino


class WriterSession:
    """One open file description, inherited by every participating writer child.

    close() closes only this process's descriptor. It deliberately never calls
    LOCK_UN: that would unlock surviving descendants sharing the description.
    """
    def __init__(self, core_root, descriptor):
        self.root = _root(core_root)
        self.path = self.root / LOCK_NAME
        self._descriptor = descriptor
        self._inode = _identity(_regular(descriptor))

    @classmethod
    def acquire(cls, core_root):
        root = _root(core_root); path = root / LOCK_NAME
        if path.is_symlink():
            raise WriterLockHold('HOLD_LOCK_SYMLINK')
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, 0o600)
        try:
            session = cls(root, fd)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise WriterBusy('HOLD_CORE_WRITER_ACTIVE') from None
            session.assert_owned()
            return session
        except BaseException:
            os.close(fd)
            raise

    @classmethod
    def inherited(cls, core_root, descriptor):
        # Duplication preserves the supplied open description. Its trusted
        # parent/host must authenticate the handoff: flock cannot establish the
        # descriptor's historical session lineage (see assert_owned's race note).
        fd = os.dup(descriptor)
        try:
            session = cls(core_root, fd); session.assert_owned(); return session
        except BaseException:
            os.close(fd); raise

    def fileno(self):
        if self._descriptor is None:
            raise WriterLockHold('HOLD_WRITER_SESSION_CLOSED')
        return self._descriptor

    def assert_owned(self):
        """Establish current exclusion; never authenticate prior session lineage."""
        fd = self.fileno(); state = _regular(fd)
        if self.path.is_symlink() or _identity(state) != self._inode or _identity(self.path.lstat()) != self._inode:
            raise WriterLockHold('HOLD_LOCK_PATH_REPLACED')
        _root(self.root)
        # Even an independent SHARED open must be excluded, proving an exclusive
        # owner exists. Testing the inherited fd alone could silently acquire or
        # upgrade an unlocked/shared file rather than prove an existing session.
        probe = os.open(self.path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            if _identity(_regular(probe)) != self._inode:
                raise WriterLockHold('HOLD_LOCK_PATH_REPLACED')
            try:
                fcntl.flock(probe, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                pass
            else:
                raise WriterLockHold('HOLD_SESSION_NOT_EXCLUSIVELY_LOCKED')
        finally:
            os.close(probe)
        try:
            # Establish current exclusive ownership of this fd. Usually this is
            # the trusted parent's inherited open description. If the prior
            # owner releases after the probe, an unrelated fd may acquire a NEW
            # lock here. This proves present exclusion, never historical session
            # identity or continuity; a genuine host must authenticate that.
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise WriterLockHold('HOLD_DESCRIPTOR_NOT_SESSION_OWNER') from None

    def child_options(self, *, env=None, pass_fds=()):
        self.assert_owned()
        environment = dict(os.environ if env is None else env)
        environment[FD_ENV] = str(self.fileno())
        return {'env': environment, 'pass_fds': tuple(dict.fromkeys((*pass_fds, self.fileno())))}

    def close(self):
        if self._descriptor is not None:
            fd, self._descriptor = self._descriptor, None
            os.close(fd)

    def __enter__(self):
        try:
            self.assert_owned()
        except BaseException:
            self.close(); raise
        return self

    def __exit__(self, *_):
        self.close()


@contextmanager
def writer_session(core_root=CANONICAL_CORE):
    """For one real Python session owner; never call just around --begin."""
    session = WriterSession.acquire(core_root)
    try:
        yield session
    finally:
        session.close()


def run_writer_command(command, *, core_root=CANONICAL_CORE):
    """A real complete child session, not a background lock-holder daemon.

    Descendants must propagate child_options. If this supervisor exits while a
    participating descendant survives, its inherited fd retains kernel exclusion.
    No timeout, PID metadata, heartbeat, force flag, unlock or lock-file deletion.
    """
    if not command:
        raise WriterLockHold('HOLD_COMPLETE_WRITER_COMMAND_REQUIRED')
    inherited = os.environ.get(FD_ENV)
    if inherited is None:
        session = WriterSession.acquire(core_root)
    else:
        try:
            session = WriterSession.inherited(core_root, int(inherited))
        except (ValueError, OSError):
            raise WriterLockHold('HOLD_INVALID_INHERITED_WRITER_DESCRIPTOR') from None
    with session:
        child = subprocess.Popen(command, **session.child_options())
        return child.wait()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    try:
        return run_writer_command(command)
    except (WriterLockHold, OSError):
        print('HOLD_CORE_WRITER_SESSION', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
