"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Skeleton } from "@memdot/ui";

import { useSession } from "@/src/components/auth/SessionProvider";

export function RequireAuth({ children }: { children: ReactNode }) {
  const session = useSession();
  const router = useRouter();

  useEffect(() => {
    if (session.status === "anonymous") {
      router.replace("/auth");
    }
  }, [session.status, router]);

  if (session.status === "loading") {
    return (
      <div className="space-y-3 p-8" role="status" aria-label="Loading session">
        <Skeleton height={28} width="40%" />
        <Skeleton height={16} width="70%" />
        <Skeleton height={16} width="55%" />
      </div>
    );
  }

  if (session.status !== "authenticated") {
    return null;
  }

  return <>{children}</>;
}
