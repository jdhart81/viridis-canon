import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

// Server-owned policy. No request timeout/profile field is consulted.
export const DEFAULT_PROFILE = Object.freeze({
  name: 'nightly-default', client_wait_seconds: 300, wrapper_seconds: 1200, comparator_wall_ms: 285000,
  compile_wall_ms: 285000, collection_wall_ms: 285000,
  comparator_cpu_seconds: 600, memory_max_bytes: 7864320000,
  toolchain: 'leanprover/lean4:v4.28.0',
});
export const FOUNDATION_PROFILE = Object.freeze({
  ...DEFAULT_PROFILE, name: 'foundation-run900-approved-v1',
  client_wait_seconds: 1200, comparator_wall_ms: 600000,
});
export const PROJECT_POLICY = Object.freeze({
  project: 'viridis-lean-4.28', toolchain: DEFAULT_PROFILE.toolchain,
  project_manifest_sha256: '5124c8ab00b060f01073494d149b13b9a24d4781c1de43ff3d53b84a7a3ecf52',
  toolchain_file_sha256: 'db7bb24b756d745bbde83fe92718b51bd3625dae3701ba0f598d0eedcd3f3028',
  mathlib_revision: '8f9d9cff6bd728b17a24e163c9402775d9e6a365',
  challenge_sha256: 'c9c95d12784f13d9a3912fceef254c9a004e52b8a4ef3e54195f1adcd2eb19f0',
  solution_sha256: '04169bd8217aaadbef4e3369a0b11dad918b1bda46231832f8e2bdd89e90b965',
  // Exact ordered wire exports, including the client's repeated witness names.
  theorem_names: Object.freeze(["thermodynamic_bound_lemma", "finite_memory_dissipation", "learning_dissipation_link", "indep_self_implies_indep_any", "mutualInformation_eq_zero_iff_indep", "entropy_eq_zero_iff_indep_self", "entropy_eq_zero_implies_mutualInformation_eq_zero", "mutualInformation_eq_zero_of_entropy_eq_zero", "eventually_finite_entropy", "ennreal_div_eq_div_mul_div", "decomposition_lemma_pointwise", "intelligence_rate_eq_product_eventually", "limsup_decomposition", "data_bound_lemma_conditional", "intelligence_bound", "thermodynamic_factor_pos_finite", "phase_transition_algebra", "phase_transition_regimes", "prediction1_rho_dependence", "data_wall", "conditional_conservation_core", "conditional_conservation", "intelligence_bound_joint_witness", "phase_joint_witness", "conservation_joint_witness", "intelligence_bound_joint_witness", "phase_joint_witness", "conservation_joint_witness"]),
});
const sha256 = value => createHash('sha256').update(value).digest('hex');
// This digest resolver is for trusted server observations, never API input.
export function resolveObservedPolicy(project, observation) {
  const p = PROJECT_POLICY;
  return project === p.project && observation?.project_manifest_sha256 === p.project_manifest_sha256 &&
    observation.toolchain_file_sha256 === p.toolchain_file_sha256 && observation.challenge_sha256 === p.challenge_sha256 &&
    observation.solution_sha256 === p.solution_sha256 &&
    JSON.stringify(observation.theorem_names) === JSON.stringify(p.theorem_names)
    ? FOUNDATION_PROFILE : DEFAULT_PROFILE;
}
export function selectResourceProfile(request, observedProjectPolicy = null) {
  if (typeof request?.challenge !== 'string' || typeof request?.solution !== 'string') return DEFAULT_PROFILE;
  return resolveObservedPolicy(request.project, {
    project_manifest_sha256: observedProjectPolicy?.project_manifest_sha256,
    toolchain_file_sha256: observedProjectPolicy?.toolchain_file_sha256,
    challenge_sha256: sha256(request.challenge), solution_sha256: sha256(request.solution),
    theorem_names: request.theoremNames,
  });
}
export function observeProjectPolicy(projectRoot, project) {
  if (!projectRoot || project !== PROJECT_POLICY.project) return null;
  try {
    return { project_manifest_sha256: sha256(readFileSync(join(projectRoot, project, 'lake-manifest.json'))),
      toolchain_file_sha256: sha256(readFileSync(join(projectRoot, project, 'lean-toolchain'))) };
  } catch { return null; } // Missing/drifted policy gets no elevated allowance.
}
export function makeExecutionContext(requestId, request, clock = () => performance.now(), projectRoot) {
  const startedMono = clock();
  const profile = selectResourceProfile(request, observeProjectPolicy(projectRoot, request.project));
  return { requestId, profile, records: [], startedMono, clock };
}
export function phaseLimits(context, phase) {
  const p = context.profile;
  const configured = phase === 'compare-kernels' ? p.comparator_wall_ms :
    phase === 'collect-theorems' ? p.collection_wall_ms : p.compile_wall_ms;
  // Only foundation has the new operation clamp. Reserve 15 s for delivery/cleanup.
  const remaining = p === FOUNDATION_PROFILE ?
    Math.max(0, p.wrapper_seconds * 1000 - 15000 - (context.clock() - context.startedMono)) : Infinity;
  return {
    wall_ms: Math.min(configured, remaining), configured_phase_wall_ms: configured,
    operation_wrapper_seconds: p.wrapper_seconds, policy_client_wait_seconds: p.client_wait_seconds,
    operation_reserve_ms: p === FOUNDATION_PROFILE ? 15000 : null,
    comparator_cpu_seconds: p.comparator_cpu_seconds, memory_max_bytes: p.memory_max_bytes,
    toolchain: p.toolchain, source: 'server-allowlist',
    guard_reason: remaining < configured ? 'foundation_operation_budget' : 'phase_wall_limit',
  };
}
export function successfulTermination(d) {
  return d.exitCode === 0 && d.signal === null && !d.guard_fired && d.reason === 'exited';
}
export function withTerminationDiagnostics(result, context) {
  const records = [...context.records].sort((a,b) => a.phase.localeCompare(b.phase));
  const diagnostics = { standard: 'VRS-COMPARATOR-TERMINATION-1', requestId: context.requestId,
    profile: context.profile.name, capture_status: context.diagnosticCaptureFailed ? 'FAILED' : 'RECORDED', records };
  if (result.type === 'verification-ok' && (context.diagnosticCaptureFailed || records.some(d => !successfulTermination(d)))) {
    return { type: 'verification-failed', description: 'Incomplete or terminated verifier phase',
      output: result.output, terminationDiagnostics: diagnostics };
  }
  return { ...result, terminationDiagnostics: diagnostics };
}
