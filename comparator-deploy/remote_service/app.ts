import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, writeFile } from "node:fs/promises";
import { join } from "node:path";

import {
  type CheckVerifyResponse,
  type StartVerifyRequest,
  type StartVerifyResponse,
  zStartVerifyRequest,
} from "@comparator/shared";
import express, { type Response } from "express";
import { z, type ZodSafeParseResult } from "zod";

import { getProjects } from "./projects.ts";
import { addWorkToQueue, health, metrics } from "./workqueue.ts";

export const app = express();
const TERMINAL_RESULT_ROOT = process.env.COMPARATOR_TERMINAL_RESULT_PATH
  ?? "/var/lib/viridis-lean/terminal-results";
// The dedicated SSH wrapper caps each Lean source at 4 MiB.  Allow both frozen
// sources plus JSON framing while keeping a fail-closed server-side ceiling.
app.use(express.json({ limit: "9mb" }));

/** Return false, asserting that parsing succeeded, or send a 400 response */
function poorlyFormed<T>(
  data: ZodSafeParseResult<T>,
  res: Response,
): data is Extract<ZodSafeParseResult<T>, { success: false }> {
  if (!data.success) {
    res.status(400).send({ error: "Poorly-formed request" });
    return true;
  }
  return false;
}

async function persistTerminalResult(requestId: string, result: CheckVerifyResponse): Promise<void> {
  await mkdir(TERMINAL_RESULT_ROOT, { recursive: true, mode: 0o700 });
  const destination = join(TERMINAL_RESULT_ROOT, `${requestId}.json`);
  const temporary = join(TERMINAL_RESULT_ROOT, `.${requestId}.tmp`);
  await writeFile(temporary, JSON.stringify(result), { encoding: "utf8", mode: 0o600 });
  await rename(temporary, destination);
}

async function sendTerminal(
  requestId: string,
  result: CheckVerifyResponse,
  sendMsg: (msg: CheckVerifyResponse) => void,
  res: Response,
): Promise<void> {
  try {
    await persistTerminalResult(requestId, result);
  } finally {
    sendMsg(result);
    res.end();
  }
}

app.get("/comparator/api/health", (_req, res) => {
  res.send(health());
});

app.get("/comparator/api/metrics.prom", (_req, res) => {
  res.set("Content-Type", "text/plain; charset=ascii");
  res.send(
    Object.entries(metrics())
      .map(([key, value]) => `${key} ${value}\n`)
      .toSorted()
      .join(""),
  );
});

app.get("/comparator/api/result/:requestId", async (req, res) => {
  const requestId = z.uuidv4().safeParse(req.params.requestId);
  if (poorlyFormed(requestId, res)) return;
  try {
    const value = JSON.parse(
      await readFile(join(TERMINAL_RESULT_ROOT, `${requestId.data}.json`), "utf8"),
    );
    res.send(value);
  } catch {
    res.sendStatus(404);
  }
});

/**
 * Jobs are stored with a post request and enqueued when their status is first requested.
 * In between, they're temporarily stored in `readyJobs`.
 */
const readyJobs = new Map<
  string,
  { timeoutCancel: NodeJS.Timeout; job: StartVerifyRequest }
>();
const READY_JOB_TIMEOUT_MS = 5000;

app.post("/comparator/api/start", async (req, res) => {
  const body = zStartVerifyRequest.safeParse(req.body);
  if (poorlyFormed(body, res)) return;

  let result: StartVerifyResponse;
  if (!(await getProjects()).some(({ project }) => project === body.data.project)) {
    result = { type: "project-not-supported" };
  } else {
    const uuid = randomUUID();
    readyJobs.set(uuid, {
      timeoutCancel: setTimeout(() => readyJobs.delete(uuid), READY_JOB_TIMEOUT_MS),
      job: body.data,
    });
    result = { type: "ready", requestId: uuid };
  }
  res.send(result);
});

app.get("/comparator/api/track/:requestId", (req, res) => {
  const requestId = z.uuidv4().safeParse(req.params.requestId);
  if (poorlyFormed(requestId, res)) return;

  const readyJob = readyJobs.get(requestId.data);
  if (!readyJob) {
    res.sendStatus(404);
    return;
  }

  // Server-sent events always need these
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Connection", "keep-alive");
  // For nginx
  res.setHeader("X-Accel-Buffering", "no");
  res.flushHeaders();

  const keepAlive: NodeJS.Timeout | undefined = setInterval(() => {
    res.write(":\n");
  }, 5000);

  const sendMsg = (msg: CheckVerifyResponse) => {
    res.write(`data: ${JSON.stringify(msg)}\n\n`);
  };

  clearTimeout(readyJob.timeoutCancel);
  readyJobs.delete(requestId.data);

  const { emitter, position } = addWorkToQueue(requestId.data, readyJob.job);
  sendMsg({ type: "in-queue", position });
  emitter.on("queueUpdate", (position) => {
    sendMsg({ type: "in-queue", position });
  });
  emitter.on("running", () => {
    sendMsg({ type: "in-progress" });
  });
  emitter.on("complete", (response) => {
    void sendTerminal(requestId.data, response, sendMsg, res);
  });
  emitter.on("failed", (error) => {
    void sendTerminal(
      requestId.data,
      { type: "verification-failed", description: "Unexpected failure", output: error,
        resourceProfile: { name: readyJob.job.resourceProfile ?? "nightly", runId: readyJob.job.runId ?? null, acceptanceEvidence: false },
        processDiagnostics: { acceptanceEvidence: false, phaseReached: "unavailable", elapsedSeconds: null,
          comparator: { exitCode: null, signal: null, elapsedSeconds: null, unavailableReason: "Queue failed outside subprocess result path" } } },
      sendMsg,
      res,
    );
  });

  // A submitted verification is durable work.  A dropped SSH/SSE connection
  // must not cancel it or remove its completion listeners: doing so discards a
  // valid kernel result and leaves the work queue's running count occupied
  // until the detached promise happens to settle.  The terminal callback above
  // persists the result independently; reconnecting clients recover it through
  // /result/:requestId.  Closing the stream therefore only stops keepalives.
  res.on("close", () => {
    clearInterval(keepAlive);
  });
});

app.get("/comparator/api/projects", async (_req, res) => {
  try {
    res.send(await getProjects());
  } catch (err) {
    res.status(400).send({ error: err instanceof Error ? err.message : String(err) });
  }
});
