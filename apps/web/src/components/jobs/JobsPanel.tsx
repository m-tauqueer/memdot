"use client";

import { Badge, Button, Dialog } from "@memdot/ui";

import { useJobs } from "@/src/components/jobs/JobsProvider";

export function JobsPanel() {
  const jobs = useJobs();

  return (
    <Dialog
      open={jobs.open}
      onClose={() => jobs.setOpen(false)}
      title="Jobs"
      description="Accepted work stays visible here. Core has no account-wide job list GET yet — this panel tracks jobs recorded from this browser session."
      footer={<Button label="Close" variant="secondary" onClick={() => jobs.setOpen(false)} />}
    >
      {jobs.jobs.length === 0 ? (
        <p className="text-meta m-0">No jobs recorded in this session.</p>
      ) : (
        <ul className="m-0 flex list-none flex-col gap-3 p-0">
          {jobs.jobs.map((job) => (
            <li key={job.jobId} className="rounded-xl border border-border p-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="m-0 text-sm font-semibold">{job.title}</p>
                  <p className="text-meta m-0 mt-1">
                    {job.kind} · {job.jobId}
                  </p>
                </div>
                <Badge tone={job.stage === "failed" ? "danger" : "neutral"}>{job.stage}</Badge>
              </div>
              <p className="text-meta m-0 mt-2">
                Updated {new Date(job.updatedAt).toLocaleString()}
                {job.correlationId ? ` · ${job.correlationId}` : ""}
              </p>
              {job.warning ? <p className="text-meta m-0 mt-1">{job.warning}</p> : null}
            </li>
          ))}
        </ul>
      )}
    </Dialog>
  );
}
