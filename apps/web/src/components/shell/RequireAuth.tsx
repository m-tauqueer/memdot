"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Banner, Skeleton } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";

export function RequireAuth({ children }: { children: ReactNode }) {
  const session = useSession();
  const router = useRouter();
  const pathname = usePathname() || "";

  useEffect(() => {
    if (session.status === "anonymous") {
      router.replace(`/auth?error=session_expired&next=${encodeURIComponent(pathname)}`);
    }
  }, [session.status, router, pathname]);

  useEffect(() => {
    if (
      session.status === "authenticated" &&
      session.session?.adult_attested === false &&
      !pathname.startsWith("/onboarding")
    ) {
      router.replace("/onboarding");
    }
  }, [pathname, router, session.session?.adult_attested, session.status]);

  if (session.status === "loading") {
    return (
      <div className="space-y-3 p-8" role="status" aria-label="Loading session">
        <Skeleton height={28} width="40%" />
        <Skeleton height={16} width="70%" />
        <Skeleton height={16} width="55%" />
      </div>
    );
  }

  if (session.status === "error") {
    return (
      <div className="mx-auto max-w-lg p-8">
        <Banner
          tone="danger"
          title="Session check failed"
          description={session.error?.message || "Could not verify your session."}
          action={
            <button
              type="button"
              className="md-btn md-btn-secondary md-btn-sm"
              onClick={() => session.refresh()}
            >
              Retry
            </button>
          }
        />
      </div>
    );
  }

  if (session.status !== "authenticated") {
    return null;
  }

  if (!pathname.startsWith("/onboarding") && session.session?.adult_attested === false) {
    return null;
  }

  return <>{children}</>;
}
