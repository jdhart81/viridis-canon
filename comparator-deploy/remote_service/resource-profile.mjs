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
  return contexts.run({profile: selectResourceProfile(request)}, action);
}
export function currentResourceProfile() {
  return contexts.getStore()?.profile ?? selectResourceProfile({});
}
export function comparatorWallMilliseconds(defaultMilliseconds) {
  return currentResourceProfile().name === 'foundational' ? 600_000 : defaultMilliseconds;
}
