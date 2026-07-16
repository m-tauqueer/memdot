"use client";

import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, approveProposal, rejectProposal } from "@/src/lib/api/client";

export default function MemoryProposedPage() {
  const [proposalId, setProposalId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function decide(kind: "approve" | "reject") {
    setBusy(true);
    setMessage(null);
    try {
      const result =
        kind === "approve" ? await approveProposal(proposalId) : await rejectProposal(proposalId);
      setMessage(`${kind}: ${JSON.stringify(result).slice(0, 200)}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : `${kind} failed`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Memory"
        title="Proposed"
        description="AI and external writes wait for explicit approve or reject. Core has no proposal list GET yet."
      />
      <SurfaceState
        kind="partial"
        title="Decide by proposal ID"
        description="Paste a proposal UUID from MCP propose-memory or Core tooling."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Proposal ID" value={proposalId} onChange={(e) => setProposalId(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button
            label="Approve"
            disabled={busy || !proposalId}
            onClick={() => void decide("approve")}
          />
          <Button
            label="Reject"
            variant="danger"
            disabled={busy || !proposalId}
            onClick={() => void decide("reject")}
          />
        </div>
        {message ? (
          <p className="text-meta" role="status">
            {message}
          </p>
        ) : null}
      </div>
    </>
  );
}
