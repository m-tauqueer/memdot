"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { Badge, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  ApiError,
  cancelSource,
  getSourceStatus,
  listSourceVersions,
  reprocessSource,
  retrySource,
} from "@/src/lib/api/client";
import { pinItem, unpinItem } from "@/src/lib/offline/store";

export default function SourceDetailPage() {
  const params = useParams<{ id: string }>();
  const sourceId = params.id;
  const session = useSession();
  const accountId = session.session?.account_id;
  const [revisionId, setRevisionId] = useState("");
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const statusQuery = useQuery({
    queryKey: ["source", sourceId, "status"],
    queryFn: () => getSourceStatus(sourceId),
    enabled: Boolean(sourceId),
  });
  const versionsQuery = useQuery({
    queryKey: ["source", sourceId, "versions"],
    queryFn: () => listSourceVersions(sourceId),
    enabled: Boolean(sourceId),
  });

  async function run(action: () => Promise<unknown>, label: string) {
    setBusy(true);
    setActionMsg(null);
    try {
      const result = await action();
      setActionMsg(`${label}: ${JSON.stringify(result).slice(0, 220)}`);
      void statusQuery.refetch();
      void versionsQuery.refetch();
    } catch (err) {
      setActionMsg(err instanceof ApiError ? err.message : `${label} failed`);
    } finally {
      setBusy(false);
    }
  }

  const statusTone =
    typeof statusQuery.data?.processingStatus === "string" &&
    String(statusQuery.data.processingStatus).includes("fail")
      ? "danger"
      : "neutral";

  return (
    <>
      <PageHeader
        eyebrow="Source"
        title="Source detail"
        description={sourceId}
        actions={
          statusQuery.data?.processingStatus ? (
            <Badge tone={statusTone}>{String(statusQuery.data.processingStatus)}</Badge>
          ) : null
        }
      />
      {statusQuery.isLoading || versionsQuery.isLoading ? <SurfaceState kind="loading" /> : null}
      {statusQuery.isError ? (
        <SurfaceState
          kind={
            statusQuery.error instanceof ApiError && statusQuery.error.status === 401
              ? "unauthorized"
              : "failed"
          }
          description={
            statusQuery.error instanceof ApiError
              ? statusQuery.error.message
              : "Could not load status"
          }
        />
      ) : null}
      {statusQuery.isSuccess ? (
        <pre className="overflow-auto rounded-2xl border border-border bg-card p-4 text-xs leading-relaxed">
          {JSON.stringify(statusQuery.data, null, 2)}
        </pre>
      ) : null}
      {versionsQuery.isSuccess ? (
        <section className="mt-4 rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Versions</h2>
          <pre className="mt-3 overflow-auto text-xs leading-relaxed">
            {JSON.stringify(versionsQuery.data.items ?? versionsQuery.data, null, 2)}
          </pre>
        </section>
      ) : null}
      <section className="mt-4 grid max-w-xl gap-3 rounded-2xl border border-border bg-card p-4">
        <h2 className="m-0 text-sm font-semibold">Lifecycle actions</h2>
        <Input
          label="Revision ID (for retry / reprocess)"
          value={revisionId}
          onChange={(e) => setRevisionId(e.target.value)}
        />
        <div className="flex flex-wrap gap-2">
          <Button
            label="Cancel"
            variant="secondary"
            disabled={busy}
            onClick={() => void run(() => cancelSource(sourceId), "Cancel")}
          />
          <Button
            label="Retry"
            variant="secondary"
            disabled={busy || !revisionId}
            onClick={() => void run(() => retrySource(sourceId, revisionId), "Retry")}
          />
          <Button
            label="Reprocess"
            disabled={busy || !revisionId}
            onClick={() => void run(() => reprocessSource(sourceId, revisionId), "Reprocess")}
          />
          <Button
            label="Pin for offline"
            variant="ghost"
            disabled={!accountId}
            onClick={() => {
              if (!accountId) {
                return;
              }
              void pinItem(accountId, {
                id: sourceId,
                kind: "source",
                title: `Source ${sourceId.slice(0, 8)}`,
                revisionId: revisionId || "unknown",
                revisionAt: new Date().toISOString(),
                payload: JSON.stringify(statusQuery.data ?? {}),
                pinnedAt: new Date().toISOString(),
              }).then(() => setActionMsg("Pinned for offline reading (ADR-0013)"));
            }}
          />
          <Button
            label="Unpin"
            variant="ghost"
            disabled={!accountId}
            onClick={() => {
              if (!accountId) {
                return;
              }
              void unpinItem(accountId, sourceId).then(() => setActionMsg("Unpinned"));
            }}
          />
        </div>
        {actionMsg ? (
          <p className="text-meta" role="status">
            {actionMsg}
          </p>
        ) : null}
      </section>
    </>
  );
}
