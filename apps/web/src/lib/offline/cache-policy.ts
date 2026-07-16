/**
 * ADR-0013 / FSD-OFF: authenticated API responses are never generically cached.
 * Shell + explicit pin/review-pack allowlists only.
 */

export type CacheClass = "shell" | "pinned" | "review_pack" | "network_only" | "forbidden";

const SHELL_PREFIXES = ["/", "/today", "/auth", "/onboarding", "/manifest.webmanifest", "/icon.svg", "/sw.js"];

export function classifyRequest(pathname: string): CacheClass {
  if (pathname.startsWith("/api/")) {
    return "network_only";
  }
  if (pathname.startsWith("/_next/") || pathname.startsWith("/__next")) {
    return "shell";
  }
  if (SHELL_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}?`))) {
    return "shell";
  }
  // Authenticated product routes: shell HTML may cache; data is network-only.
  if (
    pathname.startsWith("/library") ||
    pathname.startsWith("/spaces") ||
    pathname.startsWith("/ask") ||
    pathname.startsWith("/test") ||
    pathname.startsWith("/review") ||
    pathname.startsWith("/memory") ||
    pathname.startsWith("/integrations") ||
    pathname.startsWith("/settings")
  ) {
    return "shell";
  }
  return "network_only";
}

export function mayServiceWorkerCache(pathname: string): boolean {
  const kind = classifyRequest(pathname);
  return kind === "shell" || kind === "pinned" || kind === "review_pack";
}

export function offlineActionAllowed(action: string, online: boolean): boolean {
  if (online) {
    return true;
  }
  return ["navigate_shell", "read_pin", "review_pack_respond"].includes(action);
}
