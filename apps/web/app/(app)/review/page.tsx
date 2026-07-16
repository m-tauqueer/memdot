"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge, Button } from "@memdot/ui";

import { useConnectivity } from "@/src/components/connectivity/ConnectivityProvider";
import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  getReviewPack,
  setReviewPack,
  type ReviewPackMeta,
} from "@/src/lib/offline/store";
import { listRegistry } from "@/src/lib/workspace/registry";

export default function ReviewPage() {
  const session = useSession();
  const connectivity = useConnectivity();
  const accountId = session.session?.account_id;
  const assessments = useMemo(
    () => (accountId ? listRegistry(accountId, "assessment") : []),
    [accountId],
  );
  const [pack, setPackState] = useState<ReviewPackMeta | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function refreshPackMeta() {
    if (!accountId) {
      return;
    }
    setPackState(await getReviewPack(accountId));
  }

  async function downloadPack() {
    if (!accountId) {
      return;
    }
    const createdAt = new Date();
    const expiresAt = new Date(createdAt.getTime() + 7 * 24 * 60 * 60 * 1000);
    const next: ReviewPackMeta = {
      id: crypto.randomUUID(),
      createdAt: createdAt.toISOString(),
      expiresAt: expiresAt.toISOString(),
      courseIds: listRegistry(accountId, "course").map((row) => row.id),
      itemCount: assessments.length,
      bytes: 0,
    };
    await setReviewPack(accountId, next);
    setPackState(next);
    setMessage(
      "Seven-day review pack metadata stored locally. Sealed answers/rubrics are never written to this pack.",
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="Learning"
        title="Review"
        description="Due queue, Evidence Twin reasons, and offline provisional responses. Canonical grading happens only after online acknowledgement."
      />
      {!connectivity.online ? (
        <SurfaceState
          kind="offline"
          title="Offline review mode"
          description="Respond from a downloaded pack. Submissions stay provisional until sync."
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
            ADR-0013: prompts + source context only. No sealed keys. Expires after seven days.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button label="Download / refresh pack" disabled={!connectivity.online || !accountId} onClick={() => void downloadPack()} />
            <Button label="Reload meta" variant="secondary" onClick={() => void refreshPackMeta()} />
          </div>
          {pack ? (
            <ul className="text-meta mt-3 space-y-1">
              <li>Pack {pack.id}</li>
              <li>Items {pack.itemCount}</li>
              <li>Expires {new Date(pack.expiresAt).toLocaleString()}</li>
            </ul>
          ) : (
            <p className="text-meta mt-3">No pack downloaded on this device.</p>
          )}
          {message ? <p className="text-meta mt-3">{message}</p> : null}
        </section>
      </div>
    </>
  );
}
