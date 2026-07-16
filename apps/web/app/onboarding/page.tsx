"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@memdot/ui";

import { RequireAuth } from "@/src/components/shell/RequireAuth";
import { ApiError, attestAdult } from "@/src/lib/api/client";

function OnboardingForm() {
  const router = useRouter();
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await attestAdult(confirmed);
      router.replace("/today");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `${err.message}${err.correlationId ? ` (${err.correlationId})` : ""}`
          : "Could not save attestation",
      );
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6">
      <p className="text-label mb-3">Onboarding</p>
      <h1 className="m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
        Confirm you are 18 or older
      </h1>
      <p className="text-meta mt-3 leading-relaxed">
        Hosted Memdot is for adults. This confirmation is required before account use. Minors are
        out of scope for v1.
      </p>
      <label className="mt-8 flex items-start gap-3 text-sm">
        <input
          type="checkbox"
          className="mt-1"
          checked={confirmed}
          onChange={(event) => setConfirmed(event.target.checked)}
        />
        <span>I confirm that I am at least 18 years old.</span>
      </label>
      <div className="mt-6 flex gap-3">
        <Button label={busy ? "Saving…" : "Continue"} disabled={!confirmed || busy} onClick={() => void submit()} />
      </div>
      {error ? (
        <p className="mt-4 text-sm text-[color:var(--destructive)]" role="alert">
          {error}
        </p>
      ) : null}
    </main>
  );
}

export default function OnboardingPage() {
  return (
    <RequireAuth>
      <OnboardingForm />
    </RequireAuth>
  );
}
