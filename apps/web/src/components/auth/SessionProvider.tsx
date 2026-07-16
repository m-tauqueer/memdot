"use client";

import { useQuery } from "@tanstack/react-query";
import { createContext, useContext, useMemo, type ReactNode } from "react";

import { ApiError, fetchSession, type SessionStatus } from "@/src/lib/api/client";

type SessionContextValue = {
  status: "loading" | "authenticated" | "anonymous" | "error";
  session: SessionStatus | null;
  error: Error | null;
  refresh: () => Promise<void>;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const query = useQuery({
    queryKey: ["auth", "session"],
    queryFn: ({ signal }) => fetchSession(signal),
    retry: false,
  });

  const value = useMemo<SessionContextValue>(() => {
    if (query.isLoading) {
      return {
        status: "loading",
        session: null,
        error: null,
        refresh: async () => {
          await query.refetch();
        },
      };
    }
    if (query.isError) {
      const err = query.error;
      if (err instanceof ApiError && err.status === 401) {
        return {
          status: "anonymous",
          session: { authenticated: false },
          error: null,
          refresh: async () => {
            await query.refetch();
          },
        };
      }
      return {
        status: "error",
        session: null,
        error: err instanceof Error ? err : new Error("session_error"),
        refresh: async () => {
          await query.refetch();
        },
      };
    }
    if (query.data?.authenticated) {
      return {
        status: "authenticated",
        session: query.data,
        error: null,
        refresh: async () => {
          await query.refetch();
        },
      };
    }
    return {
      status: "anonymous",
      session: query.data ?? { authenticated: false },
      error: null,
      refresh: async () => {
        await query.refetch();
      },
    };
  }, [query]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext);
  if (!ctx) {
    throw new Error("useSession must be used within SessionProvider");
  }
  return ctx;
}
