"use client";

import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, compileContext, listConversations } from "@/src/lib/api/client";

export default function AskPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onCompile() {
    setBusy(true);
    setResult(null);
    try {
      const compiled = await compileContext({ query, purpose: "ask" });
      setResult(JSON.stringify(compiled, null, 2));
    } catch (err) {
      setResult(err instanceof ApiError ? err.message : "Compile failed");
    } finally {
      setBusy(false);
    }
  }

  async function onListConversations() {
    setBusy(true);
    setResult(null);
    try {
      const rows = await listConversations();
      setResult(JSON.stringify(rows, null, 2));
    } catch (err) {
      setResult(err instanceof ApiError ? err.message : "List failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Retrieval"
        title="Ask"
        description="Native source-first conversation with context receipts and citations. Online-only (ADR-0013)."
      />
      <SurfaceState
        kind="partial"
        title="Context compile first"
        description="Full chat UI comes later; this wires compile + conversation list against Core."
      />
      <div className="mt-4 grid max-w-2xl gap-3">
        <Input label="Query" value={query} onChange={(e) => setQuery(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button
            label={busy ? "Working…" : "Compile context"}
            disabled={busy || !query.trim()}
            onClick={() => void onCompile()}
          />
          <Button
            label="List conversations"
            variant="secondary"
            disabled={busy}
            onClick={() => void onListConversations()}
          />
        </div>
        {result ? (
          <pre className="overflow-auto rounded-2xl border border-border bg-card p-4 text-xs leading-relaxed">
            {result}
          </pre>
        ) : null}
      </div>
    </>
  );
}
