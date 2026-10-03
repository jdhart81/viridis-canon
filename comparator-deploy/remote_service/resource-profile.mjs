/** Operational budgets only; never used as mathematical acceptance evidence. */
import { AsyncLocalStorage } from 'node:async_hooks';
const contexts = new AsyncLocalStorage();
export function selectResourceProfile(request) {
  const name = request.resourceProfile ?? 'nightly';
  if (!['nightly', 'foundational'].includes(name)) throw new Error('Unknown resource profile');
  if (name === 'foundational' && !/^Run-9\d{2}$/.test(request.runId ?? '')) {
    throw new Error('Foundational profile requires reserved Run-900–999');
  }
  return Object.freeze({name, runId: request.runId ?? null,
    comparatorWallSeconds: name === 'foundational' ? 600 : 285,
    acceptanceEvidence: false});
}
export function withResourceProfile(request, action) {
  return contexts.run({profile: selectResourceProfile(request), began: performance.now(), phaseReached: 'not-started', processes: []}, action);
}
export function currentResourceProfile() {
  return contexts.getStore()?.profile ?? selectResourceProfile({});
}
export function comparatorWallMilliseconds(defaultMilliseconds) {
  return currentResourceProfile().name === 'foundational' ? 600_000 : defaultMilliseconds;
}

export function beginProcess(description, wallMilliseconds) {
  try {
    const context = contexts.getStore();
    if (!context) return null;
    const phase = description === 'Comparator' ? 'compare-kernels'
      : description === 'Challenge theorem collection' ? 'collect-theorems'
      : description.startsWith('Compilation of olean for ') ? 'compile-' + description.slice(25) : description;
    const record = {phase, exitCode: null, signal: null, elapsedSeconds: null,
      wallSeconds: wallMilliseconds / 1000, deadlineFired: false, complete: false};
    context.phaseReached = phase;
    context.processes.push(record);
    return {record, began: performance.now()};
  } catch { return null; }
}
export function markDeadline(handle) {
  try { if (handle) handle.record.deadlineFired = true; } catch { /* diagnostics never change verdict */ }
}
export function closeProcess(handle, code, signal) {
  try {
    if (!handle) return;
    Object.assign(handle.record, {exitCode: code ?? null, signal: signal ?? null,
      elapsedSeconds: (performance.now() - handle.began) / 1000, complete: true});
  } catch { /* diagnostics never change verdict */ }
}
export function processDiagnostics() {
  const context = contexts.getStore();
  return {acceptanceEvidence: false, phaseReached: context?.phaseReached ?? 'unavailable',
    elapsedSeconds: context ? (performance.now() - context.began) / 1000 : null,
    comparator: context?.processes.findLast(p => p.phase === 'compare-kernels') ?? {
      phase: 'compare-kernels', exitCode: null, signal: null, elapsedSeconds: null,
      complete: false, unavailableReason: 'Comparator not reached or no current-request subprocess'},
    processes: (context?.processes ?? []).map(p => ({...p}))};
}
