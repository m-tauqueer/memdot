"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { Banner, Button } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";
import { ApiError, beginOidc } from "@/src/lib/api/client";

type RuntimeConfig = {
  env: string;
  oidcAudience: string;
};

function authErrorCopy(code: string | null): { title: string; description: string } | null {
  switch (code) {
    case "access_denied":
    case "provider_denied":
      return {
        title: "Sign-in was denied",
        description: "The identity provider denied access. You can try again or use another account.",
      };
    case "cancelled":
      return {
        title: "Sign-in cancelled",
        description: "Nothing was changed. Start again when you are ready.",
      };
    case "session_expired":
      return {
        title: "Session expired",
        description: "Sign in again to continue. Resource details from the previous session are not shown.",
      };
    case "popup_blocked":
      return {
        title: "Popup blocked",
        description: "Allow popups for Memdot or use the full-page redirect below.",
      };
    case "internal":
      return {
        title: "Sign-in failed",
        description: "An internal error interrupted authentication. Retry, or contact an operator with the correlation ID if shown.",
      };
    default:
      return null;
  }
}

function AuthForm() {
  const session = useSession();
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [config, setConfig] = useState<RuntimeConfig | null>(null);

  const recovery = authErrorCopy(params.get("error"));
  const isSelfHost = config?.env === "self_host";

  useEffect(() => {
    void fetch("/api/runtime-config")
      .then((res) => res.json())
      .then((body: RuntimeConfig) => setConfig(body))
      .catch(() => setConfig({ env: "development", oidcAudience: "memdot-web" }));
  }, []);

  useEffect(() => {
    if (session.status === "authenticated") {
      router.replace("/today");
    }
  }, [session.status, router]);

  async function startSignIn() {
    setBusy(true);
    setError(null);
    try {
      const result = await beginOidc();
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
        {isSelfHost
          ? "Self-host Memdot uses your configured OIDC issuer through Memdot Core. Session and CSRF cookies are issued after a successful callback."
          : "Hosted Memdot uses Google through Memdot Core. Email/password and invite codes are not offered in v1."}
      </p>
      <p className="text-meta mt-2">
        Public beta · adults only · no payment required
      </p>
      {recovery ? (
        <div className="mt-6">
          <Banner tone="warning" title={recovery.title} description={recovery.description} />
        </div>
      ) : null}
      <div className="mt-8 flex flex-col gap-3">
        <Button
          label={
            busy
              ? "Redirecting…"
              : isSelfHost
                ? "Continue with OIDC"
                : "Continue with Google"
          }
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

export default function AuthPage() {
  return (
    <Suspense
      fallback={
        <main className="mx-auto flex min-h-dvh max-w-md items-center px-6">
          <p className="text-meta">Loading sign-in…</p>
        </main>
      }
    >
      <AuthForm />
    </Suspense>
  );
}
