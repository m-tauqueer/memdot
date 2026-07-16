/**
 * Global job visibility foundation (FSD-OPS-001).
 * Core has no account-wide job list GET yet — this aggregates accepted job IDs
 * from mutations in this browser session, partitioned by account.
 */

export type JobStage =
  | "accepted"
  | "uploaded"
  | "validating"
  | "parsing"
  | "normalizing"
  | "mapping"
  | "indexing"
  | "ready"
  | "ready-with-warnings"
  | "failed"
  | "deleting"
  | "cancelled"
  | "exporting"
  | "unknown";

export type ClientJob = {
  jobId: string;
  kind: "ingestion" | "export" | "deletion" | "sync" | "rebuild" | "other";
  title: string;
  stage: JobStage;
  acceptedAt: string;
  updatedAt: string;
  sourceId?: string;
  correlationId?: string;
  retryable?: boolean;
  warning?: string;
};

const KEY = "memdot.jobs.v1";

type JobsFile = Record<string, ClientJob[]>;

const memoryFile: JobsFile = {};

function storageAvailable(): boolean {
  try {
    return typeof sessionStorage !== "undefined";
  } catch {
    return false;
  }
}

function readAll(): JobsFile {
  if (!storageAvailable()) {
    return memoryFile;
  }
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) {
      return {};
    }
    return JSON.parse(raw) as JobsFile;
  } catch {
    return {};
  }
}

function writeAll(file: JobsFile): void {
  if (!storageAvailable()) {
    for (const key of Object.keys(memoryFile)) {
      delete memoryFile[key];
    }
    Object.assign(memoryFile, file);
    return;
  }
  sessionStorage.setItem(KEY, JSON.stringify(file));
}

export function listJobs(accountId: string): ClientJob[] {
  const rows = readAll()[accountId] ?? [];
  return [...rows].sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));
}

export function upsertJob(accountId: string, job: ClientJob): ClientJob[] {
  const file = readAll();
  const rows = file[accountId] ?? [];
  const next = [...rows.filter((row) => row.jobId !== job.jobId), job];
  file[accountId] = next;
  writeAll(file);
  return listJobs(accountId);
}

export function patchJob(
  accountId: string,
  jobId: string,
  patch: Partial<ClientJob>,
): ClientJob[] {
  const existing = listJobs(accountId).find((row) => row.jobId === jobId);
  if (!existing) {
    return listJobs(accountId);
  }
  return upsertJob(accountId, {
    ...existing,
    ...patch,
    jobId,
    updatedAt: patch.updatedAt ?? new Date().toISOString(),
  });
}

export function clearJobs(accountId: string): void {
  const file = readAll();
  delete file[accountId];
  writeAll(file);
}

export function activeJobCount(accountId: string): number {
  return listJobs(accountId).filter(
    (job) => !["ready", "ready-with-warnings", "failed", "cancelled"].includes(job.stage),
  ).length;
}
