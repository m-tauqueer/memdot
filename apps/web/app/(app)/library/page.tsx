"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button, Input } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { ApiError, createSource } from "@/src/lib/api/client";

export default function LibraryPage() {
  const router = useRouter();
  const [spaceId, setSpaceId] = useState("");
  const [title, setTitle] = useState("");
  const [openId, setOpenId] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onCreate() {
    setBusy(true);
    setMessage(null);
    try {
      const created = await createSource({ space_id: spaceId, title });
      setMessage(`Created ${created.sourceId}`);
      router.push(`/library/sources/${created.sourceId}`);
    } catch (err) {
      setMessage(err instanceof ApiError ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Evidence"
        title="Library"
        description="Core has create + per-source status/versions today — no account-wide source list yet."
      />
      <SurfaceState
        kind="partial"
        title="Open or create a source"
        description="Paste a space UUID to create, or open an existing source by ID."
      />
      <div className="mt-4 grid gap-6 md:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Create source</h2>
          <div className="mt-3 grid gap-3">
            <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
            <Input label="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
            <Button
              label={busy ? "Creating…" : "Create"}
              disabled={busy || !spaceId || !title}
              onClick={() => void onCreate()}
            />
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Open by ID</h2>
          <div className="mt-3 grid gap-3">
            <Input label="Source ID" value={openId} onChange={(e) => setOpenId(e.target.value)} />
            <Button
              label="Open"
              variant="secondary"
              disabled={!openId}
              onClick={() => router.push(`/library/sources/${openId}`)}
            />
            {openId ? (
              <Link className="text-sm text-primary underline-offset-2 hover:underline" href={`/library/sources/${openId}`}>
                Go to detail
              </Link>
            ) : null}
          </div>
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
