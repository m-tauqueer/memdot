"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Badge, Button, Input } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { SurfaceState } from "@/src/components/states/SurfaceState";
import { listRegistry, rememberSpace } from "@/src/lib/workspace/registry";

export default function SpacesPage() {
  const session = useSession();
  const accountId = session.session?.account_id;
  const [spaceId, setSpaceId] = useState("");
  const [title, setTitle] = useState("General");
  const [privateHint, setPrivateHint] = useState(false);
  const [tick, setTick] = useState(0);

  const spaces = useMemo(() => {
    void tick;
    return accountId ? listRegistry(accountId, "space") : [];
  }, [accountId, tick]);

  return (
    <>
      <PageHeader
        eyebrow="Organization"
        title="Spaces"
        description="Spaces are server-owned. Core has no Space create/list API in OpenAPI yet — register known Space IDs locally for navigation defaults."
      />
      <SurfaceState
        kind="partial"
        title="Private Spaces are never externally retrievable"
        description="Mark a Space as private in your notes; enforcement remains on Core. External AI cannot see Private Spaces."
      />
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Remember a Space</h2>
          <div className="mt-3 grid gap-3">
            <Input label="Space ID" value={spaceId} onChange={(e) => setSpaceId(e.target.value)} />
            <Input label="Label" value={title} onChange={(e) => setTitle(e.target.value)} />
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={privateHint}
                onChange={(e) => setPrivateHint(e.target.checked)}
              />
              Private (local label only)
            </label>
            <Button
              label="Save locally"
              disabled={!accountId || !spaceId}
              onClick={() => {
                if (!accountId) {
                  return;
                }
                rememberSpace(accountId, spaceId, privateHint ? `${title} (private)` : title);
                setTick((value) => value + 1);
              }}
            />
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Known Spaces</h2>
          {spaces.length === 0 ? (
            <p className="text-meta mt-3">None yet.</p>
          ) : (
            <ul className="mt-3 divide-y divide-border">
              {spaces.map((space) => (
                <li key={space.id} className="flex items-center justify-between gap-3 py-3">
                  <div>
                    <Link
                      className="text-sm font-semibold hover:underline"
                      href={`/spaces/${space.id}`}
                    >
                      {space.title}
                    </Link>
                    <p className="text-meta m-0">{space.id}</p>
                  </div>
                  {space.title.includes("private") ? (
                    <Badge tone="warning">Private</Badge>
                  ) : (
                    <Badge tone="neutral">Space</Badge>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </>
  );
}
