import type { ExecutionContext } from './resource-profile.mjs';
export class TerminatedProcessError extends Error { output: string; diagnostic: any; }
export function runGuarded(command: string, args: readonly string[], options: {
  context: ExecutionContext; phase: string; description?: string;
  stdout?: (data: string) => void; stderr?: (data: string) => void;
  cwd?: string; env?: NodeJS.ProcessEnv;
}, dependencies?: any): Promise<string>;
