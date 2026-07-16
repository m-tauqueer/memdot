"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { Badge, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { useJobs } from "@/src/components/jobs/JobsProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, createDocument, uploadSourceFile } from "@/src/lib/api/client";
import { emptyMemdotDocument } from "@/src/lib/document/memdot";
import { listRegistry, rememberSpace, upsertRegistry } from "@/src/lib/workspace/registry";

export default function LibraryPage() {
  const router = useRouter();
  const session = useSession();
  const jobs = useJobs();
  const accountId = session.session?.account_id;
  const [spaceId, setSpaceId] = useState("");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tick, setTick] = useState(0);

  const sources = useMemo(() => {
    void tick;
    return accountId ? listRegistry(accountId, "source") : [];
  }, [accountId, tick]);
  const documents = useMemo(() => {
    void tick;
    return accountId ? listRegistry(accountId, "document") : [];
  }, [accountId, tick]);

  async function onUpload() {
    if (!file || !accountId) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      rememberSpace(accountId, spaceId);
      const result = await uploadSourceFile({
        spaceId,
        title: title || file.name,
        file,
      });
      upsertRegistry(accountId, {
        id: result.sourceId,
        kind: "source",
        title: title || file.name,
        spaceId,
        meta: result.jobId ? `job ${result.jobId}` : "uploaded",
        updatedAt: new Date().toISOString(),
      });
      if (result.jobId) {
        jobs.trackJob({
          jobId: result.jobId,
          kind: "ingestion",
          title: title || file.name,
          stage: "uploaded",
          acceptedAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          sourceId: result.sourceId,
        });
      }
      setTick((value) => value + 1);
      setMessage(`Upload accepted · source ${result.sourceId}`);
      router.push(`/library/sources/${result.sourceId}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onCreateDocument() {
    if (!accountId) {
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      rememberSpace(accountId, spaceId);
      const provisionalId = crypto.randomUUID();
      const created = await createDocument({
        space_id: spaceId,
        title: title || "Untitled document",
        document: emptyMemdotDocument(provisionalId),
      });
      upsertRegistry(accountId, {
        id: created.documentId,
        kind: "document",
        title: title || "Untitled document",
        spaceId,
        meta: created.revisionId,
        updatedAt: new Date().toISOString(),
      });
      setTick((value) => value + 1);
      router.push(`/library/documents/${created.documentId}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Create document failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Evidence"
        title="Library"
        description="Upload sources and author documents. Account-wide lists are not on Core yet — recent items are tracked in this browser."
      />
      <div className="grid gap-4 lg:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Upload source</h2>
          <div className="mt-3 grid gap-3">
            <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
            <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <label className="md-field">
              <span className="md-label">File</span>
              <input
                type="file"
                className="md-input h-auto py-2"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <Button
                label={busy ? "Uploading…" : "Upload & process"}
                disabled={busy || !spaceId || !file}
                onClick={() => void onUpload()}
              />
              <Button
                label="New document"
                variant="secondary"
                disabled={busy || !spaceId}
                onClick={() => void onCreateDocument()}
              />
            </div>
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Recent in this browser</h2>
          {sources.length === 0 && documents.length === 0 ? (
            <SurfaceState kind="empty" title="No local items yet" description="Upload or create to populate this list." />
          ) : (
            <ul className="mt-3 divide-y divide-border">
              {sources.map((item) => (
                <li key={`s-${item.id}`}>
                  <Link
                    href={`/library/sources/${item.id}`}
                    className="flex items-center justify-between gap-3 py-3 hover:opacity-90"
                  >
                    <div>
                      <p className="m-0 text-sm font-semibold">{item.title}</p>
                      <p className="text-meta m-0">{item.id}</p>
                    </div>
                    <Badge tone="neutral">source</Badge>
                  </Link>
                </li>
              ))}
              {documents.map((item) => (
                <li key={`d-${item.id}`}>
                  <Link
                    href={`/library/documents/${item.id}`}
                    className="flex items-center justify-between gap-3 py-3 hover:opacity-90"
                  >
                    <div>
                      <p className="m-0 text-sm font-semibold">{item.title}</p>
                      <p className="text-meta m-0">{item.id}</p>
                    </div>
                    <Badge tone="accent">document</Badge>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
      {message ? (
        <p className="text-meta mt-4" role="status">
          {message}
        </p>
      ) : null}
    </>
  );
}
