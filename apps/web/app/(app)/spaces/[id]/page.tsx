"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo } from "react";

import { useSession } from "@/src/components/auth/SessionProvider";
import { PageHeader } from "@/src/components/shell/PageHeader";
import { listRegistry } from "@/src/lib/workspace/registry";

export default function SpaceDetailPage() {
  const params = useParams<{ id: string }>();
  const spaceId = params.id;
  const session = useSession();
  const accountId = session.session?.account_id;

  const related = useMemo(() => {
    if (!accountId) {
      return [];
    }
    return listRegistry(accountId).filter((item) => item.spaceId === spaceId);
  }, [accountId, spaceId]);

  return (
    <>
      <PageHeader
        eyebrow="Space"
        title="Space detail"
        description={`Space ${spaceId}. Breadcrumb context for Library/Ask/Test defaults.`}
      />
      <div className="flex flex-wrap gap-3 text-sm">
        <Link
          className="text-primary underline-offset-2 hover:underline"
          href={`/library?space=${spaceId}`}
        >
          Open Library
        </Link>
        <Link
          className="text-primary underline-offset-2 hover:underline"
          href={`/ask?space=${spaceId}`}
        >
          Ask in Space
        </Link>
        <Link
          className="text-primary underline-offset-2 hover:underline"
          href={`/test?space=${spaceId}`}
        >
          Test in Space
        </Link>
      </div>
      <section className="mt-6 rounded-2xl border border-border bg-card p-4">
        <h2 className="m-0 text-sm font-semibold">Local items in this Space</h2>
        {related.length === 0 ? (
          <p className="text-meta mt-3">No locally tracked sources/documents/courses yet.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {related.map((item) => (
              <li key={`${item.kind}-${item.id}`}>
                {item.kind}: {item.title} · {item.id}
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
