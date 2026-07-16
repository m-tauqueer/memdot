"use client";

import { useState } from "react";

import { Banner, Button, Input } from "@memdot/ui";

import { useConnectivity } from "@/src/components/connectivity/ConnectivityProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  ApiError,
  notionConnect,
  notionListPages,
  notionResolveConflict,
  notionSelectPages,
  notionSyncBinding,
} from "@/src/lib/api/client";

export default function IntegrationsPage() {
  const connectivity = useConnectivity();
  const [connectionId, setConnectionId] = useState("");
  const [bindingId, setBindingId] = useState("");
  const [spaceId, setSpaceId] = useState("");
  const [pageIds, setPageIds] = useState("");
  const [fixture, setFixture] = useState("");
  const [payload, setPayload] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(label: string, action: () => Promise<unknown>) {
    setBusy(true);
    setPayload(null);
    try {
      const result = await action();
      setPayload(`${label}\n${JSON.stringify(result, null, 2)}`);
      if (result && typeof result === "object") {
        const record = result as Record<string, unknown>;
        if (typeof record.connectionId === "string") {
          setConnectionId(record.connectionId);
        }
        if (typeof record.bindingId === "string") {
          setBindingId(record.bindingId);
        }
      }
    } catch (err) {
      setPayload(err instanceof ApiError ? `${label} failed: ${err.message}` : `${label} failed`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Connections"
        title="Integrations"
        description="Notion sync with write-boundary honesty, MCP consent surfaces, and external capture completeness labels."
      />
      {!connectivity.online ? (
        <Banner
          tone="warning"
          title="Integrations require a connection"
          description="Sync and OAuth are online-only."
        />
      ) : null}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Notion</h2>
          <p className="text-meta mt-2">
            Live OAuth belongs to the Alpha integration gate. This UI exercises Core
            connect/select/sync/resolve, including the HTTP emulator path.
          </p>
          <div className="mt-3 grid gap-3">
            <Button
              label="Connect Notion"
              disabled={busy || !connectivity.online}
              onClick={() => void run("connect", () => notionConnect())}
            />
            <Input
              label="Connection ID"
              value={connectionId}
              onChange={(e) => setConnectionId(e.target.value)}
            />
            <Button
              label="List pages"
              variant="secondary"
              disabled={busy || !connectionId}
              onClick={() => void run("pages", () => notionListPages(connectionId))}
            />
            <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
            <Input
              label="Notion page IDs (comma-separated)"
              value={pageIds}
              onChange={(e) => setPageIds(e.target.value)}
            />
            <Button
              label="Select pages"
              variant="secondary"
              disabled={busy || !connectionId || !spaceId || !pageIds}
              onClick={() =>
                void run("select", () =>
                  notionSelectPages({
                    connection_id: connectionId,
                    space_id: spaceId,
                    notion_page_ids: pageIds
                      .split(",")
                      .map((part) => part.trim())
                      .filter(Boolean),
                  }),
                )
              }
            />
            <Input
              label="Binding ID"
              value={bindingId}
              onChange={(e) => setBindingId(e.target.value)}
            />
            <Input
              label="Fixture content (emulator)"
              value={fixture}
              onChange={(e) => setFixture(e.target.value)}
            />
            <div className="flex flex-wrap gap-2">
              <Button
                label="Sync binding"
                disabled={busy || !bindingId}
                onClick={() =>
                  void run("sync", () => notionSyncBinding(bindingId, fixture || null))
                }
              />
              <Button
                label="Resolve keep Memdot"
                variant="secondary"
                disabled={busy || !bindingId}
                onClick={() =>
                  void run("resolve", () =>
                    notionResolveConflict(bindingId, { resolution: "keep_memdot" }),
                  )
                }
              />
            </div>
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">MCP & external AI</h2>
          <SurfaceState
            kind="partial"
            title="Consent & revocation"
            description="MCP OAuth clients register at the edge. Grant resolve and durable nonces are Core-owned. Capture remains best-effort and labelled incomplete unless the host sends full turns."
          />
          <ul className="text-meta mt-3 space-y-2">
            <li>search / fetch signatures stay compatibility-safe.</li>
            <li>propose-memory creates proposals — never silent writes.</li>
            <li>Private Spaces are categorically excluded from external retrieval.</li>
            <li>Live ChatGPT/Claude/Gemini proof is Alpha-gate only.</li>
          </ul>
        </section>
      </div>
      {payload ? (
        <pre className="mt-4 overflow-auto rounded-2xl border border-border bg-card p-4 text-xs">
          {payload}
        </pre>
      ) : null}
    </>
  );
}
