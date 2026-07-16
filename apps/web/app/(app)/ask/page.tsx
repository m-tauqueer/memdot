"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Badge, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  ApiError,
  appendConversationTurn,
  compileContext,
  createConversation,
  getConversation,
  listConversations,
} from "@/src/lib/api/client";
import { upsertRegistry } from "@/src/lib/workspace/registry";

export default function AskPage() {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [spaceId, setSpaceId] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [query, setQuery] = useState("");
  const [receipt, setReceipt] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const listQuery = useQuery({
    queryKey: ["conversations"],
    queryFn: () => listConversations(),
  });
  const detailQuery = useQuery({
    queryKey: ["conversation", conversationId],
    queryFn: () => getConversation(conversationId),
    enabled: Boolean(conversationId),
  });

  async function ensureConversation(): Promise<string> {
    if (conversationId) {
      return conversationId;
    }
    const created = await createConversation({
      space_id: spaceId,
      source_client: "native",
      completeness: "complete",
    });
    const id = created.conversationId || created.id;
    if (!id) {
      throw new Error("Conversation create returned no id");
    }
    setConversationId(id);
    if (accountId) {
      upsertRegistry(accountId, {
        id,
        kind: "conversation",
        title: "Ask conversation",
        spaceId,
        updatedAt: new Date().toISOString(),
      });
    }
    return id;
  }

  async function onAsk() {
    setBusy(true);
    setMessage(null);
    try {
      const compiled = await compileContext({ query, purpose: "ask" });
      setReceipt(JSON.stringify(compiled, null, 2));
      const id = await ensureConversation();
      await appendConversationTurn(id, {
        role: "user",
        content: query,
        auto_native: true,
        client_turn_id: crypto.randomUUID(),
        context_receipt_id:
          typeof compiled.receiptId === "string"
            ? compiled.receiptId
            : typeof compiled.contextReceiptId === "string"
              ? compiled.contextReceiptId
              : null,
      });
      setMessage("Turn appended with context receipt when available.");
      void detailQuery.refetch();
      void listQuery.refetch();
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Ask failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Retrieval"
        title="Ask"
        description="Source-first native conversation with context receipts. Online-only (ADR-0013)."
      />
      <SurfaceState
        kind="partial"
        title="Compile → turn → receipt"
        description="Answers from a model router are not streamed here yet; receipts and conversation capture are wired."
      />
      <div className="mt-4 grid max-w-3xl gap-3">
        <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
        <Input
          label="Conversation ID (optional)"
          value={conversationId}
          onChange={(e) => setConversationId(e.target.value)}
          hint="Leave blank to create a new native conversation"
        />
        <Input label="Question" value={query} onChange={(e) => setQuery(e.target.value)} />
        <Button
          label={busy ? "Working…" : "Compile & record turn"}
          disabled={busy || !query.trim() || !spaceId}
          onClick={() => void onAsk()}
        />
        {message ? (
          <p className="text-meta" role="status">
            {message}
          </p>
        ) : null}
        {receipt ? (
          <section className="rounded-2xl border border-border bg-card p-4">
            <div className="mb-2 flex items-center gap-2">
              <h2 className="m-0 text-sm font-semibold">Context receipt</h2>
              <Badge tone="accent">external knowledge labelled when present</Badge>
            </div>
            <pre className="overflow-auto text-xs leading-relaxed">{receipt}</pre>
          </section>
        ) : null}
        {detailQuery.isSuccess ? (
          <section className="rounded-2xl border border-border bg-card p-4">
            <h2 className="m-0 text-sm font-semibold">Conversation</h2>
            <pre className="mt-3 overflow-auto text-xs">
              {JSON.stringify(detailQuery.data, null, 2)}
            </pre>
          </section>
        ) : null}
        {listQuery.isSuccess ? (
          <section className="rounded-2xl border border-border bg-card p-4">
            <h2 className="m-0 text-sm font-semibold">Conversations</h2>
            <pre className="mt-3 overflow-auto text-xs">
              {JSON.stringify(listQuery.data, null, 2)}
            </pre>
          </section>
        ) : null}
      </div>
    </>
  );
}
