# Core writer session lock — inactive Tier 1 candidate

This is an OS-lock primitive and an explicit integration-gap proposal. It is
**not installed or activated**, and it does not cover the current scheduled LLM
session. Justin's current written sole-Core-writer authority continues to govern.
A green fixture or merged foundation PR cannot change that status.

`WriterSession.acquire(core_root)` takes nonblocking exclusive `flock` on exactly
`core_root/.viridis-core-writer.lock`. The production CLI fixes the canonical
Core root; only isolated tests pass disposable roots to the Python API. Busy
means HOLD. The file's PID, text, age, heartbeat and mere existence never decide
ownership. There is no force, TTL unlock, unlink, replacement, detached holder,
new scheduler or automation. Never remove/replace the canonical lock inode.

A genuine parent must retain the session object for the entire write session.
Each participating subprocess receives `session.child_options()` so its actual
open file description survives exec. `WriterSession.inherited(root, fd)` checks
the fixed inode, independent shared-descriptor exclusion and the actual inherited
exclusion. A stable unlocked/shared fd or unrelated fd while another exclusive
owner remains is rejected. However, an owner-release race between probe and fd
check can allow an unrelated fd to acquire a NEW exclusive lock. Current mutual
exclusion remains sound; historical session identity is not established by this
check. Neither the fd environment variable nor successful `assert_owned()` is
an authentication capability. The actual parent/host must authenticate the fd
handoff and invocation/thread lineage. Recheck `assert_owned()` before a write and
propagate the descriptor to all writer descendants. Metadata is not a substitute.

Closing a parent only closes its own descriptor. It never issues `LOCK_UN`,
which would also unlock descendants sharing that open description. A surviving
writer child retains the kernel lock after normal parent exit or cancellation.
Only the last participating descriptor's close releases it. This guarantee
requires every writer child to preserve its descriptor; this module cannot prove
that an arbitrary program has no untracked writer descendants.

A reviewed monolithic installer can eventually run under the complete-child
wrapper (`python core_writer_lock.py -- <whole installer argv>`), but this is
not an installation instruction. A wrapper around `nightly_checkpoint --begin`,
`--finish`, a health command, or one LLM tool call protects only that process,
not the generator's intervening session. See INTEGRATION_GAP.md before proposing
any production adoption. The primitive changes no science, FIFO, generation,
publication, model, cadence, schedule, gate or budget.

Tests use actual independent OS processes and flock in temporary directories.
They cover a synthetic complete parent lifecycle, inherited child ownership,
parent close/cancellation with a live child, stale metadata, same-inode unrelated
fds, owner-release interleaving and its current-exclusion-only contract,
shared/unlocked fds, replaced path and symlink/FIFO/hardlink refusal. The
synthetic lifecycle is not a genuine scheduler execution or adoption receipt.
Run `python -I -B -m unittest discover -s 00_lab_infrastructure/gates/core_writer_lock/tests -v`.
