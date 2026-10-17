# Whole scheduled-session hook: unresolved, activation blocked

Read-only inspection on 2026-10-17 found the current automation to be a local
cron LLM prompt with model, project and cwds. It has no child-command argv or
pre-turn/post-turn host callback in its stored configuration. Its exact prompt
SHA-256 is `5b46a83d8d27bb70f8241da01b5351e7f21a8057b78903dc23f8366e54a3ea18`.
No automation configuration was changed.

The actual installed `RESEARCH_PIPELINE_v2/nightly_checkpoint.py` writes START
and returns from `--begin`. The LLM then performs generation, independent tool
calls, proof transport and reversible work. Later `--finish` is a separate
process; it writes FINISH and waits for its coverage subprocess. The prompt
also requires streak/weekly receipt closeout and storage cleanup after those
commands. `autonomous_transition_executor.py` returns `AGENT_JUDGMENT_REQUIRED`
for model-owned work. `pipeline_orchestrator.py` computes routes, not the agent
session. No inspected repository or installed component owns that whole lifetime.

A correct reviewed host integration must:

1. Acquire the canonical exclusive flock before the earliest Core-writing
   health/preflight action, not merely before START.
2. Bind the actual scheduled invocation and its authenticated tool dispatch to
   that session. Retain ownership during model reasoning, waits and every tool
   call, START, generation, FIFO work, FINISH, coverage, closeout and cleanup.
3. Keep every writer child tracked and excluded until its real terminal exit.
   Cancellation/error must stop new writes and preserve exclusion while any
   child can still write. Never infer quiescence from an old FINISH, stale PID,
   receipt flag, heartbeat expiry, absent UI or one command's exit.
4. Release after genuine session completion and all writer source exits. Root
   installers and every other Core writer must adopt that same protocol.

The current source candidate supplies the descriptor primitive and process
properties, not this host integration. Until a real host hook is implemented,
reviewed and tested against the actual generator invocation, there is no sound
claim of whole-scheduler-session coverage. Do not create the actual Core lock,
install this library, amend the automation prompt, or replace current authority
on the strength of this candidate alone.

## Persistent session-holder option, explicitly unimplemented

An authenticated persistent holder could keep `flock` across separate LLM tool
commands without a TTL. A future reviewed `acquire/assert/release` protocol would
need a unique invocation/thread/nonce, independent descriptor exclusion, all
writer operations routed through the authenticated session, and release only
after actual final writer/child exits. Cancellation must retain ownership for
explicit reconciliation. A detached holder plus prompt text alone cannot prove
that every tool call is covered or that a requested release is quiescent. A
nonexpired nonce, process alive check or metadata assertion is insufficient.

No such host dispatch/lifecycle hook is available in the inspected source. This
candidate therefore does not implement or advertise an `--acquire` daemon,
`--release` shortcut, stale-holder stealing, or completion claim. A later holder
implementation remains a separate Tier 1 source/audit/CI/merge/install step.


## Descriptor proof boundary

Independent-probe and fd flock checks establish present mutual exclusion only.
Between those syscalls, another owner can release and a caller's unrelated fd
can acquire a new lock. No overlap follows, but this is not authenticated
continuity of the original invocation. Even a successful assertion or fd number
cannot prove that historical lineage. A real host must authenticate the actual
parent-issued inherited descriptor and session identity before admitting tools;
that additional host capability remains unimplemented here. The causal race
fixture preserves this limit rather than treating new acquisition as proof of
an earlier session. Do not use this low-level primitive as authorization.
