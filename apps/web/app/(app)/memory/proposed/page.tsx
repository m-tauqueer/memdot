"use client";

import { useMemo, useState } from "react";

import { Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, approveProposal, createProposal, rejectProposal } from "@/src/lib/api/client";
import { listRegistry, upsertRegistry } from "@/src/lib/workspace/registry";

export default function MemoryProposedPage() {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [proposalId, setProposalId] = useState("");
  const [spaceId, setSpaceId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [targetType, setTargetType] = useState("memory_item");
  const [patchText, setPatchText] = useState('{"assertion":"proposed fact"}');
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);

  const local = useMemo(() => {
    void tick;
    return accountId ? listRegistry(accountId, "proposal") : [];
  }, [accountId, tick]);

  async function createLocalProposal() {
    if (!accountId) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const patch = JSON.parse(patchText) as Record<string, unknown>;
      const created = await createProposal({
        space_id: spaceId,
        target_id: targetId,
        target_type: targetType,
        patch_json: patch,
        base_revision_id: null,
      });
      const id = created.proposalId || proposalId;
      if (id) {
        setProposalId(id);
        upsertRegistry(accountId, {
          id,
          kind: "proposal",
          title: "AI proposal",
          spaceId,
          updatedAt: new Date().toISOString(),
        });
        setTick((value) => value + 1);
      }
      setMessage(`Created ${JSON.stringify(created).slice(0, 200)}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  async function decide(kind: "approve" | "reject") {
    setBusy(true);
    setMessage(null);
    try {
      const result =
        kind === "approve" ? await approveProposal(proposalId) : await rejectProposal(proposalId);
      setMessage(`${kind}: ${JSON.stringify(result).slice(0, 200)}`);
      setTick((value) => value + 1);
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
        description="AI and external writes wait for explicit approve or reject. No proposal list GET on Core — track IDs locally."
      />
      <SurfaceState
        kind="partial"
        title="Canonical approval only"
        description="Approving promotes memory; rejecting excludes it. Historical mode lives under approved items."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
        <Input label="Target ID" value={targetId} onChange={(e) => setTargetId(e.target.value)} />
        <Input label="Target type" value={targetType} onChange={(e) => setTargetType(e.target.value)} />
        <label className="md-field">
          <span className="md-label">Patch JSON</span>
          <textarea
            className="md-input h-28 py-2 font-mono text-xs"
            value={patchText}
            onChange={(e) => setPatchText(e.target.value)}
          />
        </label>
        <Button
          label="Create proposal"
          variant="secondary"
          disabled={busy || !spaceId || !targetId}
          onClick={() => void createLocalProposal()}
        />
        <Input label="Proposal ID" value={proposalId} onChange={(e) => setProposalId(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button label="Approve" disabled={busy || !proposalId} onClick={() => void decide("approve")} />
          <Button
            label="Reject"
            variant="danger"
            disabled={busy || !proposalId}
            onClick={() => void decide("reject")}
          />
        </div>
        {local.length > 0 ? (
          <ul className="text-meta space-y-1">
            {local.map((row) => (
              <li key={row.id}>
                <button type="button" className="text-primary underline-offset-2 hover:underline" onClick={() => setProposalId(row.id)}>
                  {row.id}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
        {message ? (
          <p className="text-meta" role="status">
            {message}
          </p>
        ) : null}
      </div>
    </>
  );
}
