"use client";

import Link from "next/link";
import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, createMemoryItem, getMemoryItem } from "@/src/lib/api/client";
import { rememberSpace } from "@/src/lib/workspace/registry";

export default function MemoryItemsPage() {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [spaceId, setSpaceId] = useState("");
  const [title, setTitle] = useState("");
  const [assertion, setAssertion] = useState("");
  const [itemId, setItemId] = useState("");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [historical, setHistorical] = useState(false);

  async function createItem() {
    if (!accountId) {
      return;
    }
    setBusy(true);
    setError(null);
    try {
      rememberSpace(accountId, spaceId);
      const created = await createMemoryItem({
        space_id: spaceId,
        title,
        assertion_text: assertion,
      });
      setPayload(created as Record<string, unknown>);
      if (created && typeof created === "object" && "memoryItemId" in created) {
        setItemId(String((created as { memoryItemId: string }).memoryItemId));
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function load() {
    setBusy(true);
    setError(null);
    setPayload(null);
    try {
      setPayload(await getMemoryItem(itemId));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Lookup failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Memory"
        title="Approved memory"
        description="Approved memories and retained interactions. Historical mode is a presentation filter — Core still owns eligibility."
        actions={
          <Link
            className="text-sm text-primary underline-offset-2 hover:underline"
            href="/memory/proposed"
          >
            Review proposals
          </Link>
        }
      />
      <label className="mb-4 flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={historical}
          onChange={(e) => setHistorical(e.target.checked)}
        />
        Historical mode (show superseded / retained context labels when present)
      </label>
      <SurfaceState
        kind="partial"
        title={historical ? "Historical presentation on" : "Open or create a memory item"}
        description="List GET is not available; create or paste an ID."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
        <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
        <Input label="Assertion" value={assertion} onChange={(e) => setAssertion(e.target.value)} />
        <Button
          label="Create approved item"
          variant="secondary"
          disabled={busy || !spaceId || !title || !assertion}
          onClick={() => void createItem()}
        />
        <Input label="Memory item ID" value={itemId} onChange={(e) => setItemId(e.target.value)} />
        <Button
          label={busy ? "Loading…" : "Load"}
          disabled={busy || !itemId}
          onClick={() => void load()}
        />
        {error ? (
          <p className="text-sm text-[color:var(--destructive)]" role="alert">
            {error}
          </p>
        ) : null}
        {payload ? (
          <pre className="overflow-auto rounded-2xl border border-border bg-card p-4 text-xs leading-relaxed">
            {JSON.stringify(payload, null, 2)}
          </pre>
        ) : null}
      </div>
    </>
  );
}
