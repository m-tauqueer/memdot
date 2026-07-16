"use client";

import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, revealAttempt, startAttempt, submitAttempt } from "@/src/lib/api/client";

export default function TestPage() {
  const [courseId, setCourseId] = useState("");
  const [itemId, setItemId] = useState("");
  const [revisionId, setRevisionId] = useState("");
  const [clientAttemptId, setClientAttemptId] = useState("web-attempt-1");
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [selected, setSelected] = useState("a");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function runStart() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await startAttempt({
        course_id: courseId,
        assessment_item_id: itemId,
        assessment_revision_id: revisionId,
        client_attempt_id: clientAttemptId,
      });
      setAttemptId(result.attemptId ?? null);
      setMessage(`Started · ${result.status ?? "in_progress"} · ${result.attemptId ?? ""}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Start failed");
    } finally {
      setBusy(false);
    }
  }

  async function runReveal(answer: boolean) {
    if (!attemptId) {
      setMessage("Start an attempt first");
      return;
    }
    setBusy(true);
    try {
      await revealAttempt({ attempt_id: attemptId, answer, hint: !answer });
      setMessage(answer ? "Server recorded answer reveal" : "Server recorded hint reveal");
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Reveal failed");
    } finally {
      setBusy(false);
    }
  }

  async function runSubmit() {
    setBusy(true);
    try {
      const result = await submitAttempt({
        course_id: courseId,
        assessment_item_id: itemId,
        assessment_revision_id: revisionId,
        response: { selectedOption: selected },
        confidence: "sure",
        client_attempt_id: clientAttemptId,
      });
      setMessage(`Submitted · ${JSON.stringify(result).slice(0, 200)}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Submit failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Learning"
        title="Test"
        description="Server-owned lifecycle: start → optional reveal → submit with confidence. Client reveal booleans are ignored."
      />
      <SurfaceState
        kind="partial"
        title="Wire IDs from a course you created via Core"
        description="List endpoints for courses are still create-only in OpenAPI; paste UUIDs from Core/API tooling for now."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Course ID" value={courseId} onChange={(e) => setCourseId(e.target.value)} />
        <Input label="Assessment item ID" value={itemId} onChange={(e) => setItemId(e.target.value)} />
        <Input
          label="Assessment revision ID"
          value={revisionId}
          onChange={(e) => setRevisionId(e.target.value)}
        />
        <Input
          label="Client attempt ID"
          value={clientAttemptId}
          onChange={(e) => setClientAttemptId(e.target.value)}
        />
        <Input label="Selected option" value={selected} onChange={(e) => setSelected(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button label="Start" disabled={busy} onClick={() => void runStart()} />
          <Button label="Reveal hint" variant="secondary" disabled={busy} onClick={() => void runReveal(false)} />
          <Button label="Reveal answer" variant="secondary" disabled={busy} onClick={() => void runReveal(true)} />
          <Button label="Submit" disabled={busy} onClick={() => void runSubmit()} />
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
