"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@memdot/ui";

import { PageHeader } from "@/src/components/shell/PageHeader";
import { ApiError, requestAccountExport } from "@/src/lib/api/client";

const SECTIONS = [
  { href: "/memory/proposed", label: "Pending proposals" },
  { href: "/memory/activity", label: "Activity" },
  { href: "/integrations", label: "Integrations" },
];

export default function SettingsPage() {
  const [exportMsg, setExportMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function startExport() {
    setBusy(true);
    setExportMsg(null);
    try {
      const result = await requestAccountExport();
      setExportMsg(
        typeof result === "object" && result !== null
          ? `Export accepted (202). ${JSON.stringify(result).slice(0, 160)}`
          : "Export accepted.",
      );
    } catch (err) {
      setExportMsg(
        err instanceof ApiError
          ? `${err.message}${err.correlationId ? ` · ${err.correlationId}` : ""}`
          : "Export failed",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="Account"
        title="Settings"
        description="Profile, privacy, offline, export, and deletion. Destructive actions require recent auth."
      />
      <div className="grid gap-3 md:grid-cols-2">
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Privacy & data</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
            <li>Export creates a durable job (HTTP 202) — package contents still mature on Core.</li>
            <li>Deletion tombstones immediately; purge checkpoints are server-owned.</li>
            <li>Offline: pin + 7-day review pack only (ADR-0013).</li>
          </ul>
          <div className="mt-4">
            <Button
              label={busy ? "Starting…" : "Request account export"}
              variant="secondary"
              disabled={busy}
              onClick={() => void startExport()}
            />
            {exportMsg ? <p className="text-meta mt-3">{exportMsg}</p> : null}
          </div>
        </section>
        <section className="rounded-2xl border border-border bg-card p-4">
          <h2 className="m-0 text-sm font-semibold">Shortcuts</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {SECTIONS.map((item) => (
              <li key={item.href}>
                <Link className="text-primary underline-offset-2 hover:underline" href={item.href}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </>
  );
}
