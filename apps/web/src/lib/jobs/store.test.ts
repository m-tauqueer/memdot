import { beforeEach, describe, expect, it } from "vitest";

import { activeJobCount, clearJobs, listJobs, upsertJob } from "./store.js";

describe("jobs store", () => {
  beforeEach(() => {
    clearJobs("acct-a");
    clearJobs("acct-b");
  });

  it("tracks active jobs per account", () => {
    upsertJob("acct-a", {
      jobId: "job-1",
      kind: "ingestion",
      title: "Upload",
      stage: "parsing",
      acceptedAt: "2026-07-17T00:00:00.000Z",
      updatedAt: "2026-07-17T00:00:00.000Z",
    });
    upsertJob("acct-a", {
      jobId: "job-2",
      kind: "export",
      title: "Export",
      stage: "ready",
      acceptedAt: "2026-07-17T00:00:00.000Z",
      updatedAt: "2026-07-17T00:00:00.000Z",
    });

    expect(listJobs("acct-a")).toHaveLength(2);
    expect(activeJobCount("acct-a")).toBe(1);
    expect(listJobs("acct-b")).toHaveLength(0);
  });
});
