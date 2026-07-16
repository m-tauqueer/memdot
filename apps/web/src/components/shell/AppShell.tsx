"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { Badge, Button } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { logout } from "@/src/lib/api/client";
import { isNavActive, MOBILE_TAB_NAV, PRIMARY_NAV } from "@/src/lib/nav";

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname() || "/today";
  const session = useSession();
  const online = typeof navigator === "undefined" ? true : navigator.onLine;

  return (
    <div className="flex min-h-dvh bg-background text-foreground">
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
          <div className="flex items-center gap-2 px-2">
            <Badge tone={online ? "success" : "warning"}>{online ? "Online" : "Offline"}</Badge>
            <Badge tone="accent">Beta</Badge>
          </div>
          {session.session?.account_id ? (
            <p className="truncate px-2 text-xs" title={session.session.account_id}>
              Account {session.session.account_id.slice(0, 8)}…
            </p>
          ) : null}
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-12 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur md:px-6">
          <div className="font-[family-name:var(--font-display)] text-lg font-semibold md:hidden">
            Memdot
          </div>
          <button
            type="button"
            className="hidden h-8 flex-1 rounded-lg border border-border bg-card px-3 text-left text-sm text-muted-foreground md:block"
            aria-label="Open search"
          >
            Search or jump…
          </button>
          <div className="ml-auto flex items-center gap-2">
            <Badge tone="neutral">Jobs</Badge>
            <Button
              variant="ghost"
              size="sm"
              label="Sign out"
              onClick={() => {
                void logout().finally(() => {
                  window.location.href = "/auth";
                });
              }}
            />
          </div>
        </header>

        <main className="flex-1 overflow-auto px-4 pb-24 pt-5 md:px-8 md:pb-8">{children}</main>

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
    </div>
  );
}
