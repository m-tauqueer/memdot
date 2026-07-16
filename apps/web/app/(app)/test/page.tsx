"use client";

import { useState } from "react";

import { Badge, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  ApiError,
  addCourseNode,
  createAssessment,
  createCourse,
  getAttemptView,
  revealAttempt,
  startAttempt,
  submitAttempt,
} from "@/src/lib/api/client";
import { rememberSpace, upsertRegistry } from "@/src/lib/workspace/registry";

export default function TestPage() {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [spaceId, setSpaceId] = useState("");
  const [courseTitle, setCourseTitle] = useState("Course");
  const [courseId, setCourseId] = useState("");
  const [itemId, setItemId] = useState("");
  const [revisionId, setRevisionId] = useState("");
  const [clientAttemptId, setClientAttemptId] = useState(() => `web-${Date.now()}`);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [selected, setSelected] = useState("a");
  const [confidence, setConfidence] = useState("sure");
  const [promptView, setPromptView] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hintRevealed, setHintRevealed] = useState(false);
  const [answerRevealed, setAnswerRevealed] = useState(false);

  async function bootstrapCourse() {
    if (!accountId) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      rememberSpace(accountId, spaceId);
      const course = await createCourse({ space_id: spaceId, title: courseTitle });
      const id = course.courseId || course.id;
      if (!id) {
        throw new Error("No course id");
      }
      setCourseId(id);
      await addCourseNode(id, {
        kind: "concept",
        title: "Concept 1",
        confirmation: "confirmed",
      });
      const assessment = await createAssessment({
        course_id: id,
        title: "Sample MCQ",
        item_type: "mcq",
        prompt: "Sample question — sealed answer stays server-side.",
        sealed_answer: { correctOption: "a" },
        sealed_rubric: { notes: "server sealed" },
      });
      if (assessment.assessmentItemId) {
        setItemId(assessment.assessmentItemId);
      }
      if (assessment.revisionId) {
        setRevisionId(assessment.revisionId);
      }
      upsertRegistry(accountId, {
        id,
        kind: "course",
        title: courseTitle,
        spaceId,
        updatedAt: new Date().toISOString(),
      });
      if (assessment.assessmentItemId) {
        upsertRegistry(accountId, {
          id: assessment.assessmentItemId,
          kind: "assessment",
          title: "Sample MCQ",
          spaceId,
          updatedAt: new Date().toISOString(),
          ...(assessment.revisionId ? { meta: assessment.revisionId } : {}),
        });
      }
      setMessage(`Course ${id} ready`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Bootstrap failed");
    } finally {
      setBusy(false);
    }
  }

  async function loadPrompt() {
    setBusy(true);
    try {
      const view = await getAttemptView(itemId, revisionId);
      setPromptView(JSON.stringify(view, null, 2));
      setMessage("Loaded attempt view (sealed fields omitted by Core)");
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Load failed");
    } finally {
      setBusy(false);
    }
  }

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
      setMessage(`Started · ${result.status ?? "in_progress"}`);
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
      if (answer) {
        setAnswerRevealed(true);
      } else {
        setHintRevealed(true);
      }
      setMessage(answer ? "Answer reveal recorded server-side" : "Hint reveal recorded server-side");
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
        confidence,
        client_attempt_id: clientAttemptId,
        hint_revealed: hintRevealed,
        answer_revealed: answerRevealed,
      });
      setMessage(`Submitted · ${JSON.stringify(result).slice(0, 240)}`);
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
        description="Server-owned lifecycle: setup → attempt view → start → optional reveal → submit with confidence. Client reveal booleans do not unlock sealed answers."
      />
      <div className="mb-3 flex flex-wrap gap-2">
        {hintRevealed ? <Badge tone="warning">Hint revealed</Badge> : null}
        {answerRevealed ? <Badge tone="danger">Answer revealed</Badge> : null}
      </div>
      <SurfaceState
        kind="partial"
        title="Bootstrap a course or paste IDs"
        description="Create course + concept + assessment against Core, or paste existing UUIDs."
      />
      <div className="mt-4 grid max-w-xl gap-3">
        <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
        <Input label="Course title" value={courseTitle} onChange={(e) => setCourseTitle(e.target.value)} />
        <Button
          label={busy ? "Working…" : "Create course + sample item"}
          disabled={busy || !spaceId}
          onClick={() => void bootstrapCourse()}
        />
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
        <Input label="Confidence" value={confidence} onChange={(e) => setConfidence(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button label="Load prompt" variant="secondary" disabled={busy || !itemId || !revisionId} onClick={() => void loadPrompt()} />
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
        {promptView ? (
          <pre className="overflow-auto rounded-2xl border border-border bg-card p-4 text-xs">{promptView}</pre>
        ) : null}
      </div>
    </>
  );
}
