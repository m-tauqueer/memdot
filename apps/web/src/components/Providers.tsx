"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { SessionProvider } from "@/src/components/auth/SessionProvider";
import { ConnectivityProvider } from "@/src/components/connectivity/ConnectivityProvider";
import { JobsProvider } from "@/src/components/jobs/JobsProvider";

export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: (failureCount, error) => {
              if (
                error &&
                typeof error === "object" &&
                "status" in error &&
                (error as { status: number }).status === 401
              ) {
                return false;
              }
              return failureCount < 1;
            },
            refetchOnWindowFocus: false,
            gcTime: 5 * 60_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <ConnectivityProvider>
        <SessionProvider>
          <JobsProvider>{children}</JobsProvider>
        </SessionProvider>
      </ConnectivityProvider>
    </QueryClientProvider>
  );
}
