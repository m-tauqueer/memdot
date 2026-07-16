import { EmptyState, Skeleton } from "@memdot/ui";
import type { ReactNode } from "react";

export type SurfaceKind =
  | "loading"
  | "empty"
  | "partial"
  | "degraded"
  | "failed"
  | "unauthorized"
  | "offline"
  | "rate_limited"
  | "ready";

export function SurfaceState({
  kind,
  title,
  description,
  action,
  children,
}: {
  kind: SurfaceKind;
  title?: string;
  description?: string;
  action?: ReactNode;
  children?: ReactNode;
}) {
  if (kind === "loading") {
    return (
      <div className="space-y-3" role="status" aria-label="Loading">
        <Skeleton height={20} width="35%" />
        <Skeleton height={52} />
        <Skeleton height={52} />
        <Skeleton height={52} />
      </div>
    );
  }

  if (kind === "ready") {
    return <>{children}</>;
  }

  const defaults: Record<Exclude<SurfaceKind, "loading" | "ready">, { title: string; description: string }> =
    {
      empty: {
        title: title ?? "Nothing here yet",
        description: description ?? "When there is something to show, it will appear in this space.",
      },
      partial: {
        title: title ?? "Some content is unavailable",
        description: description ?? "What is present is shown below. Missing pieces will fill in when ready.",
      },
      degraded: {
        title: title ?? "Running in a limited mode",
        description: description ?? "A provider or lane is unavailable. Safe fallbacks remain.",
      },
      failed: {
        title: title ?? "Something went wrong",
        description: description ?? "Try again. If it persists, share the correlation ID with support.",
      },
      unauthorized: {
        title: title ?? "Sign in required",
        description: description ?? "Reconnect to continue. Resource details are not disclosed.",
      },
      offline: {
        title: title ?? "You are offline",
        description:
          description ?? "Pinned reading and the review pack remain available when cached. Other actions need a connection.",
      },
      rate_limited: {
        title: title ?? "Slow down",
        description:
          description ?? "Too many requests. Wait a moment, then retry. Correlation IDs stay visible for support.",
      },
    };

  const copy = defaults[kind];
  return <EmptyState title={copy.title} description={copy.description} action={action} />;
}
