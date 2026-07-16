"use client";

import Link from "next/link";
import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, getMemoryItem } from "@/src/lib/api/client";

export default function MemoryItemsPage() {
  const [itemId, setItemId] = useState("");
  const [payload, setPayload] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
        description="Lookup by ID for now — Core exposes GET /memory/items/{id}, not a list."
        actions={
          <Link className="text-sm text-primary underline-offset-2 hover:underline" href="/memory/proposed">
            Review proposals
          </Link>
        }
      />
      <SurfaceState
        kind="partial"
        title="Open a memory item"
        description="Paste a memory item UUID after approving a proposal or creating an item via Core."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Memory item ID" value={itemId} onChange={(e) => setItemId(e.target.value)} />
        <Button label={busy ? "Loading…" : "Load"} disabled={busy || !itemId} onClick={() => void load()} />
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
