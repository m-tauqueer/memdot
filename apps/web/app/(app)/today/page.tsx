import { EmptyState } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";

export default function TodayPage() {
  return (
    <>
      <PageHeader
        eyebrow="Home"
        title="Today"
        description="Action-oriented home for due reviews, processing attention, and proposals."
      />
      <div className="grid gap-3 md:grid-cols-3">
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Due reviews</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">0</p>
          <p className="text-meta mt-1">Queue fills from eligible learning evidence.</p>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Processing</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">0</p>
          <p className="text-meta mt-1">Accepted jobs stay visible until terminal.</p>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <p className="text-label">Proposals</p>
          <p className="mt-2 text-2xl font-semibold tracking-tight">0</p>
          <p className="text-meta mt-1">AI writes wait for your approval.</p>
        </section>
      </div>
      <EmptyState
        title="Quiet day"
        description="When sources process, reviews come due, or proposals arrive, they land here first."
      />
    </>
  );
}
