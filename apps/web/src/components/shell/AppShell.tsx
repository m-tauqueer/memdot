"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { Badge, Banner, Button } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { useConnectivity } from "@/src/components/connectivity/ConnectivityProvider";
import { JobsPanel } from "@/src/components/jobs/JobsPanel";
import { useJobs } from "@/src/components/jobs/JobsProvider";
import { logout } from "@/src/lib/api/client";
import { clearAccountOffline } from "@/src/lib/offline/store";
import { isNavActive, MOBILE_TAB_NAV, PRIMARY_NAV } from "@/src/lib/nav";
import { clearRegistry } from "@/src/lib/workspace/registry";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "/today";
  const session = useSession();
  const connectivity = useConnectivity();
  const jobs = useJobs();
  const router = useRouter();
  const [signingOut, setSigningOut] = useState(false);
  const accountId = session.session?.account_id;

  async function onSignOut() {
    setSigningOut(true);
    try {
      if (accountId) {
        await clearAccountOffline(accountId);
        clearRegistry(accountId);
        jobs.clearAccountJobs();
      }
      await logout();
    } finally {
      window.location.href = "/auth";
    }
  }

  return (
    <div className="flex min-h-dvh bg-background text-foreground">
      <a href="#main-content" className="md-skip-link">
        Skip to main content
      </a>
      <aside
        className="hidden w-[260px] shrink-0 border-r border-border bg-sidebar p-4 md:flex md:flex-col"
        aria-label="Primary"
      >
        <div className="mb-6 px-2">
          <div className="font-[family-name:var(--font-display)] text-2xl font-semibold tracking-tight">
            Memdot
          </div>
          <p className="text-meta mt-1">Memory that cites itself</p>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5" aria-label="Main">
          {PRIMARY_NAV.map((item) => {
            const active = isNavActive(pathname, item);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  active ? "bg-accent text-accent-foreground" : "text-foreground hover:bg-muted"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-4 space-y-2 border-t border-border pt-4 text-meta">
          <div className="flex flex-wrap items-center gap-2 px-2">
            <Badge tone={connectivity.online ? "success" : "warning"}>
              {connectivity.online ? "Online" : "Offline"}
            </Badge>
            <Badge tone="accent">Beta</Badge>
            {!connectivity.online ? <Badge tone="warning">Stale offline OK</Badge> : null}
          </div>
          {accountId ? (
            <p className="truncate px-2 text-xs" title={accountId}>
              Account {accountId.slice(0, 8)}…
            </p>
          ) : null}
          {session.session?.recent_auth === false ? (
            <p className="px-2 text-xs text-[color:var(--warning)]">Recent auth expired</p>
          ) : null}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header
          className="sticky top-0 z-10 flex h-12 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur md:px-6"
          role="banner"
        >
          <div className="font-[family-name:var(--font-display)] text-lg font-semibold md:hidden">
            Memdot
          </div>
          <button
            type="button"
            className="hidden h-8 flex-1 rounded-lg border border-border bg-card px-3 text-left text-sm text-muted-foreground md:block"
            aria-label="Open search"
            onClick={() => router.push("/ask")}
          >
            Search or jump…
          </button>
          <div className="ml-auto flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              aria-label={`Jobs${jobs.activeCount ? `, ${jobs.activeCount} active` : ""}`}
              onClick={() => jobs.setOpen(true)}
            >
              Jobs
              {jobs.activeCount > 0 ? (
                <Badge tone="accent">{String(jobs.activeCount)}</Badge>
              ) : (
                <Badge tone="neutral">0</Badge>
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              label={signingOut ? "Signing out…" : "Sign out"}
              disabled={signingOut}
              onClick={() => void onSignOut()}
            />
          </div>
        </header>

        {!connectivity.online ? (
          <div className="px-4 pt-3 md:px-8">
            <Banner
              tone="warning"
              title="You are offline"
              description="Shell, pinned reading, and a downloaded review pack remain available. Ask, import, sync, MCP, and settings security changes need a connection."
            />
          </div>
        ) : null}
        {connectivity.swUpdateReady ? (
          <div className="px-4 pt-3 md:px-8">
            <Banner
              tone="info"
              title="Update ready"
              description="A new app version is waiting. It will not interrupt an active test or dirty editor — apply when safe."
              action={
                <Button label="Reload" size="sm" onClick={() => connectivity.applySwUpdate()} />
              }
            />
          </div>
        ) : null}

        <main id="main-content" className="flex-1 overflow-auto px-4 pb-24 pt-5 md:px-8 md:pb-8" tabIndex={-1}>
          {children}
        </main>

        <nav
          className="fixed inset-x-0 bottom-0 z-10 flex border-t border-border bg-card/95 px-2 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"
          aria-label="Mobile"
        >
          {MOBILE_TAB_NAV.map((item) => {
            const active = isNavActive(pathname, item);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-1 flex-col items-center py-2 text-xs font-semibold ${
                  active ? "text-primary" : "text-muted-foreground"
                }`}
                aria-current={active ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
          <Link
            href="/settings"
            className="flex flex-1 flex-col items-center py-2 text-xs font-semibold text-muted-foreground"
          >
            More
          </Link>
        </nav>
      </div>
      <JobsPanel />
    </div>
  );
}
