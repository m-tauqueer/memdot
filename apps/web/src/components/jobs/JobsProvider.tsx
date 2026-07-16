"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { useSession } from "@/src/components/auth/SessionProvider";
import {
  activeJobCount,
  clearJobs,
  listJobs,
  type ClientJob,
  upsertJob,
} from "@/src/lib/jobs/store";

type JobsValue = {
  jobs: ClientJob[];
  activeCount: number;
  open: boolean;
  setOpen: (open: boolean) => void;
  trackJob: (job: ClientJob) => void;
  refresh: () => void;
  clearAccountJobs: () => void;
};

const JobsContext = createContext<JobsValue | null>(null);

export function JobsProvider({ children }: { children: ReactNode }) {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [version, setVersion] = useState(0);
  const [open, setOpen] = useState(false);

  const jobs = useMemo(() => {
    void version;
    if (!accountId) {
      return [] as ClientJob[];
    }
    return listJobs(accountId);
  }, [accountId, version]);

  const refresh = useCallback(() => {
    setVersion((value) => value + 1);
  }, []);

  const value = useMemo<JobsValue>(
    () => ({
      jobs,
      activeCount: accountId ? activeJobCount(accountId) : 0,
      open,
      setOpen,
      trackJob: (job) => {
        if (!accountId) {
          return;
        }
        upsertJob(accountId, job);
        setVersion((value) => value + 1);
      },
      refresh,
      clearAccountJobs: () => {
        if (!accountId) {
          return;
        }
        clearJobs(accountId);
        setVersion((value) => value + 1);
      },
    }),
    [jobs, accountId, open, refresh],
  );

  return <JobsContext.Provider value={value}>{children}</JobsContext.Provider>;
}

export function useJobs(): JobsValue {
  const ctx = useContext(JobsContext);
  if (!ctx) {
    throw new Error("useJobs must be used within JobsProvider");
  }
  return ctx;
}
