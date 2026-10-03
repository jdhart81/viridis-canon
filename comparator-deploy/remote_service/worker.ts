import type { StartVerifyRequest, VerifyResult } from "@comparator/shared";

import { createHash } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { KEEP_COMPARATOR_TEMP_FILES, USE_MOCK_VERIFICATION } from "./env.ts";
import { CheckingError, cleanup, collectThms, comparator, compile, createTaskDir, executionEvidenceForTask } from "./exec.ts";
import { isEvidenceCacheEligible, observeFile } from "./job-attestation.mjs";
import { withResourceProfile, currentResourceProfile } from "./resource-profile.mjs";
import { doMockWork } from "./mockworker.ts";

const workerSourceAtLoad = await observeFile(fileURLToPath(import.meta.url));
const CACHE_NAMESPACE = "vrs-comparator-cache-v2-targeted-lean4.28-mathlib-8f9d9cff6bd728b17a24e163c9402775d9e6a365";
const CACHE_ROOT = process.env.COMPARATOR_RESULT_CACHE_PATH ?? "/var/lib/viridis-lean/result-cache";
const inFlightByHash = new Map<string, Promise<VerifyResult>>();

function verificationHash(
  project: string,
  challenge: string,
  solution: string,
  theoremNames?: string[],
): string {
  return createHash("sha256")
    .update(CACHE_NAMESPACE)
    .update("\0")
    .update(project)
    .update("\0")
    .update(challenge)
    .update("\0")
    .update(solution)
    .update("\0")
    .update(JSON.stringify(theoremNames ?? []))
    .digest("hex");
}

async function readSuccessfulCache(key: string): Promise<VerifyResult | undefined> {
  try {
    const value = JSON.parse(await readFile(join(CACHE_ROOT, `${key}.json`), "utf8"));
    if (
      value?.cacheNamespace === CACHE_NAMESPACE &&
      value?.result?.type === "verification-ok" &&
      Array.isArray(value.result.theoremNames) &&
      typeof value.result.output === "string" &&
      isEvidenceCacheEligible(value.result.executionEvidence)
    ) {
      return value.result as VerifyResult;
    }
  } catch {
    // A cache miss or corrupt cache entry never changes verification semantics.
  }
  return undefined;
}

async function writeSuccessfulCache(key: string, taskId: string, result: VerifyResult): Promise<void> {
  if (result.type !== "verification-ok" || !isEvidenceCacheEligible(result.executionEvidence)) return;
  await mkdir(CACHE_ROOT, { recursive: true, mode: 0o700 });
  const destination = join(CACHE_ROOT, `${key}.json`);
  const temporary = join(CACHE_ROOT, `.${key}.${taskId}.tmp`);
  await writeFile(
    temporary,
    JSON.stringify({ cacheNamespace: CACHE_NAMESPACE, key, result }),
    { encoding: "utf8", mode: 0o600 },
  );
  await rename(temporary, destination);
}

/**
 * `challenge-thms` can surface compiler-generated proof fields created while
 * elaborating definitions with proof-valued fields (for example
 * `SomeDefinition._proof_2`). Those names are not stable public declarations
 * and lean4export may correctly omit them, causing a panic before either
 * kernel can check the actual frozen theorem set. Module-local declarations
 * (for example `_private.Challenge.0.SomeHelper`) also receive different names
 * when the same source is compiled as Solution. Keep every explicit public
 * theorem declaration and exclude only unstable generated/private names.
 */
export function filterComparatorTheoremNames(theoremNames: string[]): string[] {
  return theoremNames.filter(
    (name) => !name.includes("._proof_") && !name.startsWith("_private."),
  );
}

export function selectComparatorTheoremNames(
  availableNames: string[],
  requestedNames?: string[],
): string[] {
  const available = filterComparatorTheoremNames(availableNames);
  if (requestedNames === undefined) return available;

  const selected: string[] = [];
  for (const requested of requestedNames) {
    const matches = available.filter(
      (name) => name === requested || name.endsWith(`.${requested}`),
    );
    const matched = matches[0];
    if (matches.length !== 1 || matched === undefined) {
      throw new CheckingError(
        `Required theorem export target ${requested} resolved ${matches.length} times`,
        matches.join("\n"),
      );
    }
    if (!selected.includes(matched)) selected.push(matched);
  }
  return selected;
}

async function doUncachedWork(
  taskId: string,
  { project, challenge, solution, theoremNames: requestedTheoremNames }: StartVerifyRequest,
): Promise<VerifyResult> {
  if (USE_MOCK_VERIFICATION) {
    return { ...(await doMockWork(challenge, solution)), executionEvidence: {
      status: "MOCK_NOT_ATTESTED", cacheEligible: false,
      scope: "Development mock output; no runtime or kernel execution is attested.",
    } };
  }

  try {
    const key = verificationHash(project, challenge, solution, requestedTheoremNames);
    const cached = await readSuccessfulCache(key);
    if (cached) return cached;

    await createTaskDir(taskId);
    // The dedicated certifier is now 4-vCPU/8-GiB. Challenge and Solution are
    // independent exact-byte builds, so run them concurrently to keep the
    // complete dual-kernel path inside the five-minute wall SLO.
    await Promise.all([
      compile(taskId, project, "Challenge", challenge),
      compile(taskId, project, "Solution", solution),
    ]);

    const theoremNames = selectComparatorTheoremNames(
      await collectThms(taskId, project),
      requestedTheoremNames,
    );

    const output = await comparator(taskId, project, theoremNames);
    const executionEvidence = await executionEvidenceForTask(taskId, challenge, solution, workerSourceAtLoad);
    if (executionEvidence.status === "INTEGRITY_HOLD") {
      return { type: "verification-failed", description: "Per-job runtime/source observation failed integrity checks", output, executionEvidence };
    }
    const result: VerifyResult = { type: "verification-ok", theoremNames, output, executionEvidence };
    await writeSuccessfulCache(key, taskId, result);
    return result;
  } catch (err) {
    if (err instanceof CheckingError) {
      return {
        type: "verification-failed",
        description: err.message,
        output: err.output,
      };
    }
    return {
      type: "verification-failed",
      description: "Unexpected error",
      output: err instanceof Error ? err.message : String(err),
    };
  } finally {
    if (!KEEP_COMPARATOR_TEMP_FILES) {
      await cleanup(taskId);
    }
  }
}

async function doWorkInternal(
  taskId: string,
  request: StartVerifyRequest,
): Promise<VerifyResult> {
  const key = verificationHash(
    request.project,
    request.challenge,
    request.solution,
    request.theoremNames,
  );
  // Keep operational profiles/run bindings isolated; scientific cache hash is unchanged.
  const flightKey = key + "\0" + currentResourceProfile().name + "\0" + (request.runId ?? "");
  const existing = inFlightByHash.get(flightKey);
  if (existing) {
    const result = await existing;
    return { ...result, executionEvidence: {
      ...(result.executionEvidence ?? {}),
      delivery: { mode: "IN_FLIGHT_REUSE", servedForRequestId: taskId },
    } };
  }

  const work = doUncachedWork(taskId, request);
  inFlightByHash.set(flightKey, work);
  try {
    const result = await work;
    return { ...result, executionEvidence: {
      ...(result.executionEvidence ?? {}),
      delivery: { mode: "FRESH_EXECUTION", servedForRequestId: taskId },
    } };
  } finally {
    if (inFlightByHash.get(flightKey) === work) inFlightByHash.delete(flightKey);
  }
}

export async function doWork(taskId: string, request: StartVerifyRequest): Promise<VerifyResult> {
  return withResourceProfile(request, async () => {
    const result = await doWorkInternal(taskId, request);
    return { ...result, resourceProfile: currentResourceProfile() };
  });
}
