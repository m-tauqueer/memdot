"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Banner, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { useConnectivity } from "@/src/components/connectivity/ConnectivityProvider";
import { useJobs } from "@/src/components/jobs/JobsProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { ApiError, beginOidc, createTombstone, requestAccountExport, restoreReplay } from "@/src/lib/api/client";
import {
  estimateOfflineBytes,
  getReviewPack,
  listPins,
  type PinRecord,
  type ReviewPackMeta,
} from "@/src/lib/offline/store";

const SECTIONS = [
  { href: "/memory/proposed", label: "Pending proposals" },
  { href: "/memory/activity", label: "Activity" },
  { href: "/integrations", label: "Integrations" },
];

export default function SettingsPage() {
  const session = useSession();
  const connectivity = useConnectivity();
  const jobs = useJobs();
  const accountId = session.session?.account_id;
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [deleteMsg, setDeleteMsg] = useState<string | null>(null);
  const [entityId, setEntityId] = useState("");
  const [entityType, setEntityType] = useState("source");
  const [busy, setBusy] = useState(false);
  const [pins, setPins] = useState<PinRecord[]>([]);
  const [pack, setPack] = useState<ReviewPackMeta | null>(null);
  const [bytes, setBytes] = useState(0);
  const [swState, setSwState] = useState(() =>
    typeof navigator === "undefined" || !("serviceWorker" in navigator)
      ? "unsupported"
      : "checking",
  );

  useEffect(() => {
    if (!accountId) {
      return;
    }
    void Promise.all([listPins(accountId), getReviewPack(accountId), estimateOfflineBytes(accountId)]).then(
      ([nextPins, nextPack, nextBytes]) => {
        setPins(nextPins);
        setPack(nextPack);
        setBytes(nextBytes);
      },
    );
  }, [accountId]);

  useEffect(() => {
    if (!("serviceWorker" in navigator)) {
      return;
    }
    let cancelled = false;
    void navigator.serviceWorker.getRegistration().then((reg) => {
      if (!cancelled) {
        setSwState(reg ? "registered" : "not_installed");
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  async function startExport() {
    if (!session.session?.recent_auth) {
      setExportMsg("Recent authentication required. Re-authenticate, then retry export.");
      return;
    }
    setBusy(true);
    setExportMsg(null);
    try {
      const result = await requestAccountExport();
      const jobId =
        result && typeof result === "object" && "jobId" in result
          ? String((result as { jobId: string }).jobId)
          : `export-${Date.now()}`;
      if (accountId) {
        const job = {
          jobId,
          kind: "export" as const,
          title: "Account export",
          stage: "exporting" as const,
          acceptedAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        if (result && typeof result === "object" && "correlationId" in result) {
          jobs.trackJob({
            ...job,
            correlationId: String((result as { correlationId: string }).correlationId),
          });
        } else {
          jobs.trackJob(job);
        }
      }
      setExportMsg("Export accepted as a durable job. Track progress under Jobs.");
    } catch (err) {
      if (err instanceof ApiError && err.needsRecentAuth) {
        setExportMsg("Recent authentication required for export.");
      } else {
        setExportMsg(
          err instanceof ApiError
            ? `${err.message}${err.correlationId ? ` · ${err.correlationId}` : ""}`
            : "Export failed",
        );
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Profile, privacy, offline, export, and deletion. Destructive actions require recent auth."
      />
      {!connectivity.online ? (
        <Banner
          tone="warning"
          title="Offline settings are read-only for security changes"
          description="You can inspect pinned content and review-pack metadata. Export, deletion, and credential changes need a connection."
        />
      ) : null}
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Privacy & data</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>Export creates a durable job (HTTP 202).</li>
            <li>Deletion tombstones immediately; purge checkpoints are server-owned.</li>
            <li>Recent auth: {session.session?.recent_auth ? "satisfied" : "required for sensitive actions"}.</li>
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button
              label={busy ? "Starting…" : "Request account export"}
              variant="secondary"
              disabled={busy || !connectivity.online}
              onClick={() => void startExport()}
            />
            {!session.session?.recent_auth ? (
              <Button
                label="Re-authenticate"
                variant="ghost"
                disabled={!connectivity.online}
                onClick={() => {
                  void beginOidc().then((result) => {
                    const url = result.authorization_url || result.authorize_url || result.url;
                    if (url) {
                      window.location.href = url;
                    }
                  });
                }}
              />
            ) : null}
          </div>
          {exportMsg ? <p className="text-meta mt-3">{exportMsg}</p> : null}
          <div className="mt-6 border-t border-border pt-4">
            <h3 className="m-0 text-sm font-semibold">Deletion tombstone</h3>
            <p className="text-meta mt-2">Requires recent auth. Purge checkpoints remain server-owned.</p>
            <div className="mt-3 grid gap-3">
              <Input label="Entity ID" value={entityId} onChange={(e) => setEntityId(e.target.value)} />
              <Input label="Entity type" value={entityType} onChange={(e) => setEntityType(e.target.value)} />
              <div className="flex flex-wrap gap-2">
                <Button
                  label="Create tombstone"
                  variant="danger"
                  disabled={busy || !connectivity.online || !entityId || !session.session?.recent_auth}
                  onClick={() => {
                    setBusy(true);
                    setDeleteMsg(null);
                    void createTombstone({ entity_id: entityId, entity_type: entityType })
                      .then((result) => setDeleteMsg(`Tombstone: ${JSON.stringify(result).slice(0, 160)}`))
                      .catch((err: unknown) =>
                        setDeleteMsg(err instanceof ApiError ? err.message : "Tombstone failed"),
                      )
                      .finally(() => setBusy(false));
                  }}
                />
                <Button
                  label="Restore replay"
                  variant="secondary"
                  disabled={busy || !connectivity.online || !session.session?.recent_auth}
                  onClick={() => {
                    setBusy(true);
                    setDeleteMsg(null);
                    void restoreReplay({})
                      .then((result) => setDeleteMsg(`Replay: ${JSON.stringify(result).slice(0, 160)}`))
                      .catch((err: unknown) =>
                        setDeleteMsg(err instanceof ApiError ? err.message : "Replay failed"),
                      )
                      .finally(() => setBusy(false));
                  }}
                />
              </div>
              {deleteMsg ? <p className="text-meta">{deleteMsg}</p> : null}
            </div>
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Offline (ADR-0013)</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>PWA: {swState.replaceAll("_", " ")}</li>
            <li>Pinned items: {pins.length}</li>
            <li>
              Review pack:{" "}
              {pack
                ? `${pack.itemCount} items · expires ${new Date(pack.expiresAt).toLocaleDateString()}`
                : "none downloaded"}
            </li>
            <li>Local namespace ≈ {bytes} bytes</li>
          </ul>
          <p className="text-meta mt-3">
            Logout clears this account&apos;s offline namespace on this device. Ordinary API responses are
            never cached.
          </p>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4 md:col-span-2">
          <h2 className="m-0 text-sm font-semibold">Shortcuts</h2>
          <ul className="mt-3 flex flex-wrap gap-4 text-sm">
            {SECTIONS.map((item) => (
              <li key={item.href}>
                <Link className="text-primary underline-offset-2 hover:underline" href={item.href}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
