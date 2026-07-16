"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { ApiError, apiRequest } from "@/src/lib/api/client";

export default function AuthPage() {
  const session = useSession();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (session.status === "authenticated") {
      router.replace("/today");
    }
  }, [session.status, router]);

  async function startSignIn() {
    setBusy(true);
    setError(null);
    try {
      const result = await apiRequest<{
        authorization_url?: string;
        authorize_url?: string;
        url?: string;
      }>("/api/v1/auth/oidc/begin", { method: "POST", body: {} });
      const url = result.authorization_url || result.authorize_url || result.url;
      if (!url) {
        throw new Error("OIDC begin did not return an authorization URL");
      }
      window.location.href = url;
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `${err.message}${err.correlationId ? ` (${err.correlationId})` : ""}`
          : err instanceof Error
            ? err.message
            : "Sign-in failed";
      setError(message);
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-6">
      <p className="text-label mb-3">Memdot</p>
      <h1 className="m-0 font-[family-name:var(--font-display)] text-4xl font-semibold tracking-tight">
        Sign in
      </h1>
      <p className="text-meta mt-3 leading-relaxed">
        Hosted Memdot uses Google through Memdot Core. Your browser session and CSRF protection are
        issued by Core after a successful OIDC callback.
      </p>
      <div className="mt-8 flex flex-col gap-3">
        <Button
          label={busy ? "Redirecting…" : "Continue with Google"}
          disabled={busy || session.status === "loading"}
          onClick={() => void startSignIn()}
        />
        {error ? (
          <p className="text-sm text-[color:var(--destructive)]" role="alert">
            {error}
          </p>
        ) : null}
      </div>
    </main>
  );
}
