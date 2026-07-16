"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Badge, EmptyState } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { useJobs } from "@/src/components/jobs/JobsProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { listRegistry } from "@/src/lib/workspace/registry";

export default function TodayPage() {
  const session = useSession();
  const jobs = useJobs();
  const accountId = session.session?.account_id;
  const proposals = useMemo(
    () => (accountId ? listRegistry(accountId, "proposal") : []),
    [accountId],
  );
  const assessments = useMemo(
    () => (accountId ? listRegistry(accountId, "assessment") : []),
    [accountId],
  );

  return (
    <>
      <PageHeader
        eyebrow="Home"
        title="Today"
        description="Action-oriented home for processing attention, proposals, and due reviews tracked in this session."
      />
      <div className="grid gap-3 md:grid-cols-3">
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Due reviews</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{assessments.length}</p>
          <p className="text-meta mt-1">
            Local assessment handles — open <Link href="/review">Review</Link>.
          </p>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Processing</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{jobs.activeCount}</p>
          <p className="text-meta mt-1">
            <button
              type="button"
              className="text-primary underline-offset-2 hover:underline"
              onClick={() => jobs.setOpen(true)}
            >
              Open jobs
            </button>
          </p>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Proposals</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">{proposals.length}</p>
          <p className="text-meta mt-1">
            <Link href="/memory/proposed">Review proposed memory</Link>
          </p>
        </section>
      </div>
      {jobs.jobs.length > 0 ? (
        <section className="mt-4 rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Active & recent jobs</h2>
          <ul className="mt-3 space-y-2">
            {jobs.jobs.slice(0, 5).map((job) => (
              <li key={job.jobId} className="flex items-center justify-between gap-3 text-sm">
                <span>
                  {job.title}
                  {job.sourceId ? (
                    <>
                      {" · "}
                      <Link href={`/library/sources/${job.sourceId}`}>source</Link>
                    </>
                  ) : null}
                </span>
                <Badge tone={job.stage === "failed" ? "danger" : "neutral"}>{job.stage}</Badge>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <EmptyState
          title="Quiet day"
          description="When sources process, reviews come due, or proposals arrive, they land here first."
        />
      )}
    </>
  );
}
