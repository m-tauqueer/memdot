"use client";

import { useSearchParams } from "next/navigation";

/** Read `?space=` / `?spaceId=` for Space-preserving deep links (FSD-NAV-003). */
export function useSpaceParam(fallback = ""): string {
  const params = useSearchParams();
  return params.get("space") || params.get("spaceId") || fallback;
}
