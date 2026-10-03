export interface ResourceProfile {
  name: string; client_wait_seconds: number; wrapper_seconds: number; comparator_wall_ms: number;
  compile_wall_ms: number; collection_wall_ms: number;
  comparator_cpu_seconds: number; memory_max_bytes: number; toolchain: string;
}
export interface ExecutionContext {
  requestId: string; profile: ResourceProfile; records: any[];
  startedMono: number; clock: () => number; diagnosticCaptureFailed?: boolean;
}
export const DEFAULT_PROFILE: ResourceProfile;
export const FOUNDATION_PROFILE: ResourceProfile;
export const PROJECT_POLICY: Readonly<Record<string, any>>;
export function selectResourceProfile(request: any, observedProjectPolicy?: any): ResourceProfile;
export function resolveObservedPolicy(project: string, observation: any): ResourceProfile;
export function makeExecutionContext(requestId: string, request: any, clock?: () => number, projectRoot?: string): ExecutionContext;
export function phaseLimits(context: ExecutionContext, phase: string): any;
export function successfulTermination(record: any): boolean;
export function withTerminationDiagnostics<T>(result: T, context: ExecutionContext): T;

export function observeProjectPolicy(projectRoot: string, project: string): any;
