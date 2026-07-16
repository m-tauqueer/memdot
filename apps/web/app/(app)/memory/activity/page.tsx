"use client";

import { useMemo } from "react";

import { Badge } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { useJobs } from "@/src/components/jobs/JobsProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { listRegistry } from "@/src/lib/workspace/registry";

export default function MemoryActivityPage() {
  const session = useSession();
  const jobs = useJobs();
  const accountId = session.session?.account_id;
  const rows = useMemo(() => {
    if (!accountId) {
      return [];
    }
    return listRegistry(accountId).filter((item) =>
      ["proposal", "document", "source", "conversation"].includes(item.kind),
    );
  }, [accountId]);

  return (
    <>
      <PageHeader
        eyebrow="Memory"
        title="Activity"
        description="Approval history, ingestion, and conversation activity visible from this device index plus session jobs."
      />
      <section className="rounded-2xl border border-border bg-card p-4">
        <h2 className="m-0 text-sm font-semibold">Local activity</h2>
        {rows.length === 0 ? (
          <p className="text-meta mt-3">No local activity yet.</p>
        ) : (
          <ul className="mt-3 divide-y divide-border">
            {rows.map((row) => (
              <li
                key={`${row.kind}-${row.id}`}
                className="flex items-center justify-between gap-3 py-3 text-sm"
              >
                <div>
                  <p className="m-0 font-semibold">{row.title}</p>
                  <p className="text-meta m-0">
                    {row.kind} · {row.id}
                  </p>
                </div>
                <Badge tone="neutral">{new Date(row.updatedAt).toLocaleString()}</Badge>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="mt-4 rounded-2xl border border-border bg-card p-4">
        <h2 className="m-0 text-sm font-semibold">Jobs</h2>
        {jobs.jobs.length === 0 ? (
          <p className="text-meta mt-3">No jobs in this session.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {jobs.jobs.map((job) => (
              <li key={job.jobId} className="flex justify-between gap-3">
                <span>{job.title}</span>
                <Badge tone={job.stage === "failed" ? "danger" : "neutral"}>{job.stage}</Badge>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
