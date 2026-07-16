"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Banner, Button } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { RequireAuth } from "@/src/components/shell/RequireAuth";
import { ApiError, attestAdult } from "@/src/lib/api/client";

function OnboardingForm() {
  const router = useRouter();
  const session = useSession();
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submitAge() {
    setBusy(true);
    setError(null);
    try {
      await attestAdult(confirmed);
      await session.refresh();
      router.replace("/today");
    } catch (err) {
      // Declined stays blocked. Duplicate attestation / already-active often returns
      // 404 via Core safe_not_found after unique constraint — still allow prefs.
      if (err instanceof ApiError && err.status === 403 && err.code === "attestation_declined") {
        setError("You must confirm you are 18 or older to use hosted Memdot.");
      } else if (err instanceof ApiError && err.status === 403) {
        setError(`${err.message}${err.correlationId ? ` (${err.correlationId})` : ""}`);
      } else {
        setError(err instanceof ApiError ? err.message : "Could not confirm account eligibility.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-lg flex-col justify-center px-6 py-10">
      <p className="text-label mb-3">Onboarding</p>
      <Banner
        tone="info"
        title="Public beta"
        description="Experimental features may change. Capacity is not guaranteed forever."
        live="off"
      />

      <h1 className="mt-6 m-0 font-[family-name:var(--font-display)] text-3xl font-semibold tracking-tight">
        Confirm you are 18 or older
      </h1>
      <p className="text-meta mt-3 leading-relaxed">
        V1 is adults-only. Memdot does not ask for a birth date or identity document.
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
      {!confirmed ? (
        <p className="text-meta mt-3">
          If you cannot confirm, you cannot use hosted Memdot. No product content will be stored.
        </p>
      ) : null}
      <div className="mt-6 flex flex-wrap gap-3">
        <Button
          label={busy ? "Saving…" : "Continue"}
          disabled={!confirmed || busy}
          onClick={() => void submitAge()}
        />
      </div>
      <p className="text-meta mt-5">
        Profile defaults and starting-space setup remain unavailable until Core exposes canonical
        account-preference and Space creation contracts.
      </p>

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
