"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Badge, Button } from "@memdot/ui";

import { useConnectivity } from "@/src/components/connectivity/ConnectivityProvider";
import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { listRegistry } from "@/src/lib/workspace/registry";

export default function ReviewPage() {
  const session = useSession();
  const connectivity = useConnectivity();
  const accountId = session.session?.account_id;
  const assessments = useMemo(
    () => (accountId ? listRegistry(accountId, "assessment") : []),
    [accountId],
  );

  return (
    <>
      <PageHeader
        eyebrow="Learning"
        title="Review"
        description="Due queue and Evidence Twin reasons. Review-pack download is unavailable until Core provides an authorized encrypted pack contract."
      />
      {!connectivity.online ? (
        <SurfaceState
          kind="offline"
          title="Review requires a connection"
          description="Offline review is not enabled yet because no server-authorized encrypted pack is available."
        />
      ) : null}
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Due / known items</h2>
          {assessments.length === 0 ? (
            <p className="text-meta mt-3">
              No local assessments. Create one under <Link href="/test">Test</Link>.
            </p>
          ) : (
            <ul className="mt-3 space-y-2 text-sm">
              {assessments.map((item) => (
                <li key={item.id} className="flex items-center justify-between gap-2">
                  <span>
                    {item.title}
                    <span className="text-meta block">{item.id}</span>
                  </span>
                  <Badge tone="neutral">due reason: practice</Badge>
                </li>
              ))}
            </ul>
          )}
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Seven-day review pack</h2>
          <p className="text-meta mt-2">
            ADR-0013 requires a server-authorized encrypted pack with no sealed keys. That Core
            contract is not available yet, so no pack is fabricated locally.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button label="Review-pack download unavailable" disabled />
          </div>
          <p className="text-meta mt-3">No review pack is stored on this device.</p>
        </section>
      </div>
    </>
  );
}
