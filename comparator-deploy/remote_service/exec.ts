import { execFile, spawn } from "node:child_process";
import { chmod, cp, mkdir, mkdtemp, readdir, rm, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import { z } from "zod";

import { IS_DEVELOPMENT, PROJ_ROOT } from "./env.ts";
import { currentExecutionContext } from "./resource-profile.mjs";
import { runGuarded } from "./guarded-process.mjs";
import { buildJobEvidence } from "./job-attestation.mjs";

export interface VerifyTask {
  taskId: string;
  project: string;
  challenge: string;
  solution: string;
}

/**
 * A fresh working directory created each time the module stais loaded. These
 * will hang around indefinitely on the filesystem unless there's a cleanup
 * process or unless the target for tmpdir() is a tempfs.
 */
export const WORKING_TMP_ROOT_DIR = await mkdtemp(join(tmpdir(), "comparator-"));
console.log("Comparator project root: " + PROJ_ROOT);
console.log("Comparator working tmp root: " + WORKING_TMP_ROOT_DIR);

function workingDir(taskId: string) {
  return join(WORKING_TMP_ROOT_DIR, taskId);
}

export class CheckingError extends Error {
  output: string;
  constructor(description: string, output: string) {
    super(description);
    this.output = output;
  }
}

/** Keep stage guards unchanged except for the exact server-approved comparator profile. */
function spawnPromise(command: string, args: readonly string[], options: {
  description?: string; stdout?: (data: string) => void; stderr?: (data: string) => void;
  cwd?: string; env?: NodeJS.ProcessEnv;
}): Promise<string> {
  const description = options.description ?? "Process";
  const phase = description === "Comparator" ? "compare-kernels" :
    description === "Challenge theorem collection" ? "collect-theorems" :
    description.startsWith("Compilation of olean for ") ? "compile-" + description.slice(25) : description;
  return runGuarded(command, args, { ...options, phase, context: currentExecutionContext() })
    .catch((err: { message: string; output: string }) => { throw new CheckingError(err.message, err.output); });
}

const staging = (module: string) => `${module}-staging`;

export async function createTaskDir(taskId: string) {
  await mkdir(join(workingDir(taskId), "Challenge", ".lake"), { recursive: true });
  await mkdir(join(workingDir(taskId), staging("Challenge")));
  await mkdir(join(workingDir(taskId), "Solution", ".lake"), { recursive: true });
  await mkdir(join(workingDir(taskId), staging("Solution")));
  // Production Bubblewrap intentionally drops to uid/gid 65534. Grant that
  // sandbox access only to this disposable PrivateTmp-scoped task tree while
  // leaving the service-wide umask restrictive.
  await Promise.all([
    chmod(workingDir(taskId), 0o711),
    chmod(join(workingDir(taskId), "Challenge"), 0o711),
    chmod(join(workingDir(taskId), "Challenge", ".lake"), 0o777),
    chmod(join(workingDir(taskId), staging("Challenge")), 0o777),
    chmod(join(workingDir(taskId), "Solution"), 0o711),
    chmod(join(workingDir(taskId), "Solution", ".lake"), 0o777),
    chmod(join(workingDir(taskId), staging("Solution")), 0o777),
  ]);
}

function projectDir(project: string) {
  return join(PROJ_ROOT, project);
}

const script = (scriptName: string) => join(import.meta.dirname, "..", "scripts", scriptName);

/**
 * Write <module> into the task directory at `$DIR/<module>/<module>.lean`,
 * and put the artifacts from building the module into
 * `$DIR/<module>/.lake/build`
 */
export async function compile(
  taskId: string,
  project: string,
  module: string,
  leanContents: string,
) {
  const projDir = projectDir(project);
  const workDir = workingDir(taskId);
  const leanPath = join(workDir, module, module + ".lean");
  await writeFile(leanPath, leanContents);
  await chmod(leanPath, 0o644);

  let cmd: string;
  let args: string[];
  if (IS_DEVELOPMENT) {
    console.error("Running insecure compile without a sandbox", { taskId, project, module });

    await Promise.all([
      cp(join(projDir, "lake-manifest.json"), join(workDir, module, "lake-manifest.json")),
      cp(join(projDir, "lakefile.toml"), join(workDir, module, "lakefile.toml")),
      cp(join(projDir, "lean-toolchain"), join(workDir, module, "lean-toolchain")),
      symlink(join(projDir, ".lake", "packages"), join(workDir, module, ".lake", "packages")),
    ]);

    cmd = "lake";
    args = ["build", module];
  } else {
    cmd = script("compile.sh");
    args = [projDir, workDir, module];
  }

  return spawnPromise(cmd, args, {
    cwd: join(workDir, module),
    description: `Compilation of olean for ${module}`,
  });
}

export async function collectThms(taskId: string, project: string) {
  const module = "Challenge";
  const projDir = projectDir(project);
  const workDir = workingDir(taskId);

  let cmd: string;
  let args: string[];
  if (IS_DEVELOPMENT) {
    console.error("Running insecure collectThms without a sandbox", { taskId, project });

    await cp(join(projDir, "ChallengeThms.lean"), join(workDir, module, "ChallengeThms.lean"));

    cmd = "lake";
    args = ["exe", "challenge-thms"];
  } else {
    cmd = script("collectThms.sh");
    args = [projDir, workDir];
  }

  const stdout: string[] = [];
  await spawnPromise(cmd, args, {
    cwd: join(workDir, module),
    description: "Challenge theorem collection",
    stdout: (str) => stdout.push(str),
  });

  return z.array(z.string()).parse(JSON.parse(stdout.join("")));
}

export async function comparator(taskId: string, project: string, theoremNames: string[]) {
  const projDir = projectDir(project);
  const workDir = workingDir(taskId);

  const configPath = join(workDir, "Challenge", "config.json");
  await writeFile(
    configPath,
    JSON.stringify(
      {
        challenge_module: "Challenge",
        solution_module: "Solution",
        theorem_names: theoremNames,
        permitted_axioms: ["propext", "Quot.sound", "Classical.choice"],
        enable_nanoda: true,
      },
      undefined,
      2,
    ),
  );
  await chmod(configPath, 0o644);

  let cmd: string;
  let args: string[];
  let env: { [key: string]: string };
  if (IS_DEVELOPMENT) {
    console.error("Running Comparator insecurely without a sandbox", {
      taskId,
      project,
      theoremNames,
    });

    // Move files into place
    const mvSrc = join(workDir, "Solution", ".lake", "build", "lib", "lean");
    const mvDst = join(workDir, "Challenge", ".lake", "build", "lib", "lean");
    await Promise.all(
      (await readdir(mvSrc)).map((name) => cp(join(mvSrc, name), join(mvDst, name))),
    );
    await cp(
      join(workDir, "Solution", "Solution.lean"),
      join(workDir, "Challenge", "Solution.lean"),
    );

    cmd = "lake";
    args = ["exe", "comparator", "config.json"];
    env = {
      COMPARATOR_NANODA: join(PROJ_ROOT, "./nanoda_lib/target/release/nanoda_bin"),
      COMPARATOR_LANDRUN: ".lake/packages/comparator/scripts/fake-landrun.sh",
      COMPARATOR_LEAN4EXPORT: ".lake/packages/lean4export/.lake/build/bin/lean4export",
    };
  } else {
    cmd = script("comparator.sh");
    args = [projDir, workDir, join(projectDir("nanoda_lib"), "target/release")];
    env = {};
  }

  return spawnPromise(cmd, args, {
    cwd: join(workDir, "Challenge"),
    description: "Comparator",
    env: { ...process.env, ...env },
  });
}

const execFileAsync = promisify(execFile);
export async function cleanup(taskId: string) {
  const dir = workingDir(taskId);
  try {
    // Necessary to allow the overlayfs-created working directories to be deleted
    await execFileAsync("chmod", ["-R", "u+rwX", dir]);
  } catch (err) {
    console.error("chmod during cleanup failed", { taskId, err });
  }
  await rm(workingDir(taskId), { recursive: true, force: true });
}

/** Read actual launcher observations before cleanup; never infer pins from the project name. */
export function executionEvidenceForTask(taskId: string, challenge: string, solution: string, workerSourceAtLoad: Record<string, unknown>) {
  return buildJobEvidence({ taskId, workRoot: workingDir(taskId), challenge, solution, workerSourceAtLoad });
}
