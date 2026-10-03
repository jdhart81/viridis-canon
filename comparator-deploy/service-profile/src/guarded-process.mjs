import { spawn as nodeSpawn } from 'node:child_process';
import { phaseLimits, successfulTermination } from './resource-profile.mjs';

export class TerminatedProcessError extends Error {
  constructor(description, output, diagnostic) {
    super(description); this.output = output; this.diagnostic = diagnostic;
  }
}
const unavailable = scope => ({ available: false, scope, user_cpu_seconds: null,
  system_cpu_seconds: null, max_rss_bytes: null,
  reason: 'Node ChildProcess does not expose per-child wait4/rusage; no accounting probe enabled' });
export function runGuarded(command, args, options, dependencies = {}) {
  const spawn = dependencies.spawn ?? nodeSpawn;
  const clock = dependencies.clock ?? (() => performance.now());
  const utc = dependencies.utc ?? (() => new Date().toISOString());
  const schedule = dependencies.setTimeout ?? setTimeout;
  const cancel = dependencies.clearTimeout ?? clearTimeout;
  const killGroup = dependencies.killGroup ?? ((pid, signal) => process.kill(-pid, signal));
  const { context, phase } = options;
  const limits = phaseLimits(context, phase);
  const start = clock(), startUtc = utc();
  let proc, timer, fired = false, spawnFailed = false, finished = false, killTarget = 'not_sent';
  let size = 0, overflow = false;
  const output = [];
  function append(str) {
    if (overflow) return;
    if (str.length + size > 1000000) {
      output.push(str.slice(0, 1000000-size) + '\n...clipped...'); overflow = true; size = 1000000;
    } else { output.push(str); size += str.length; }
  }
  function diagnostic(code, signal, reason) {
    return { phase, requestId: context.requestId, start: startUtc, end: utc(),
      elapsed_ms: Math.max(0,clock()-start), exitCode: signal ? null : code,
      signal: signal ?? null, guard_fired: fired, reason,
      guard_reason: fired ? limits.guard_reason : null, process_group_target: killTarget,
      profile: context.profile.name, limits,
      accounting: unavailable('spawned phase process; no parent/service aggregates substituted'),
      kernel_process_accounting: phase === 'compare-kernels' ?
        ['lean4export','nanoda','Lean-default-kernel-replay'].map(name => ({name,...unavailable(name === 'Lean-default-kernel-replay' ? 'comparator process; Lean kernel replay is in-process, not separately accounted' : 'internal exporter/nanoda subprocess; not individually observed')})) : [],
    };
  }
  // Only diagnostics get persisted; never command arguments, payloads or env.
  return new Promise((resolve,reject) => {
    function finish(code,signal) {
      if (finished) return;
      finished = true;
      if (timer !== undefined) cancel(timer);
      const d = diagnostic(code,signal,spawnFailed ? 'spawn_failed' : fired ? limits.guard_reason : signal ? 'signaled' : 'exited');
      try { context.records.push(d); } catch { context.diagnosticCaptureFailed = true; }
      if (!successfulTermination(d) || context.diagnosticCaptureFailed) {
        reject(new TerminatedProcessError(`${options.description ?? 'Process'} failed or terminated`,output.join(''),d));
      } else resolve(output.join(''));
    }
    if (limits.wall_ms <= 0) {
      fired = true; finish(null,null); return; // Never spawn after foundation budget expires.
    }
    try {
      proc = spawn(command,args,{cwd:options.cwd,env:options.env ?? process.env,detached:true});
    } catch {
      spawnFailed = true; finish(null,null); return;
    }
    proc.stdout.on('data',data => { const s=data.toString('utf8'); options.stdout?.(s); append(s); });
    proc.stderr.on('data',data => { const s=data.toString('utf8'); options.stderr?.(s); append(s); });
    proc.on('error',() => { spawnFailed = true; }); // Close follows error; retain one record only.
    proc.on('close',(code,signal) => finish(code,signal));
    timer = schedule(() => {
      fired = true;
      if (proc.pid !== undefined) {
        try { killGroup(proc.pid,'SIGKILL'); killTarget = 'detached_process_group'; return; } catch { /* fallback below */ }
      }
      killTarget = 'child_fallback'; proc.kill('SIGKILL');
    },limits.wall_ms);
  });
}
