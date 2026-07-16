"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { Banner, Button } from "@memdot/ui";

import { DocumentEditor } from "@/src/components/editor/DocumentEditor";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import {
  ApiError,
  getDocument,
  listDocumentRevisions,
  saveDocumentRevision,
} from "@/src/lib/api/client";
import { emptyMemdotDocument, type MemdotDocument } from "@/src/lib/document/memdot";

function asMemdot(
  documentId: string,
  payload: Record<string, unknown> | undefined,
): MemdotDocument {
  const body = payload?.document;
  if (body && typeof body === "object" && "root" in (body as object)) {
    const doc = body as MemdotDocument;
    return { ...doc, documentId, schema: "memdot-document", schemaVersion: 1 };
  }
  return emptyMemdotDocument(documentId);
}

function revisionFromDoc(payload: Record<string, unknown> | undefined): string | null {
  if (!payload) {
    return null;
  }
  if (typeof payload.revisionId === "string") {
    return payload.revisionId;
  }
  if (typeof payload.currentRevisionId === "string") {
    return payload.currentRevisionId;
  }
  return null;
}

export default function DocumentDetailPage() {
  const params = useParams<{ id: string }>();
  const documentId = params.id;
  const [savedRevisionId, setSavedRevisionId] = useState<string | null>(null);
  const [editorEpoch, setEditorEpoch] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [conflict, setConflict] = useState(false);
  const [busy, setBusy] = useState(false);

  const docQuery = useQuery({
    queryKey: ["document", documentId],
    queryFn: () => getDocument(documentId),
    enabled: Boolean(documentId),
  });
  const revisionsQuery = useQuery({
    queryKey: ["document", documentId, "revisions"],
    queryFn: () => listDocumentRevisions(documentId),
    enabled: Boolean(documentId),
  });

  const baseRevisionId = savedRevisionId ?? revisionFromDoc(docQuery.data);
  const initial = useMemo(() => asMemdot(documentId, docQuery.data), [documentId, docQuery.data]);

  async function onSave(doc: MemdotDocument) {
    setBusy(true);
    setMessage(null);
    setConflict(false);
    try {
      const saved = await saveDocumentRevision(documentId, {
        base_revision_id: baseRevisionId,
        document: { ...doc, documentId, schema: "memdot-document", schemaVersion: 1 },
      });
      if (saved.revisionId) {
        setSavedRevisionId(saved.revisionId);
      }
      setMessage(`Saved revision ${saved.revisionId ?? ""}`);
      void revisionsQuery.refetch();
      void docQuery.refetch();
    } catch (err) {
      if (err instanceof ApiError && err.isConflict) {
        setConflict(true);
        if (err.currentRevisionId) {
          setSavedRevisionId(err.currentRevisionId);
        }
        setMessage(
          err.currentRevisionId
            ? `Stale base — rebased to ${err.currentRevisionId}. Review content, then save again.`
            : "Stale base revision — reload and resolve before saving again.",
        );
      } else {
        setMessage(err instanceof ApiError ? err.message : "Save failed");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Document"
        title="Editor"
        description={`Document ${documentId}. Explicit Save with base-revision conflict checks (no silent offline edits).`}
      />
      {conflict ? (
        <Banner
          tone="warning"
          title="Revision conflict"
          description="Another revision landed first. Base pointer was updated when Core returned currentRevisionId."
          action={
            <Button
              size="sm"
              variant="secondary"
              label="Reload editor"
              onClick={() => {
                setConflict(false);
                setEditorEpoch((value) => value + 1);
                void docQuery.refetch();
                void revisionsQuery.refetch();
              }}
            />
          }
        />
      ) : null}
      {docQuery.isLoading ? <SurfaceState kind="loading" /> : null}
      {docQuery.isError ? (
        <SurfaceState
          kind="failed"
          description={docQuery.error instanceof ApiError ? docQuery.error.message : "Load failed"}
        />
      ) : null}
      {docQuery.isSuccess ? (
        <DocumentEditor
          documentId={documentId}
          initial={initial}
          contentKey={`${documentId}:${baseRevisionId ?? "new"}:${editorEpoch}`}
          busy={busy}
          onSave={(doc) => void onSave(doc)}
        />
      ) : null}
      {message ? (
        <p className="text-meta mt-3" role="status">
          {message}
        </p>
      ) : null}
      {revisionsQuery.isSuccess ? (
        <section className="mt-6 rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Revision history</h2>
          <pre className="mt-3 overflow-auto text-xs">
            {JSON.stringify(revisionsQuery.data.items ?? revisionsQuery.data, null, 2)}
          </pre>
        </section>
      ) : null}
    </>
  );
}
