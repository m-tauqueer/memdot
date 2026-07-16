/**
 * ADR-0013 / FSD-OFF: authenticated API responses are never generically cached.
 * Only public/static shell assets may use Cache Storage. Account content must
 * wait for a Core-authorized encrypted offline envelope.
 */

export type CacheClass = "shell" | "pinned" | "review_pack" | "network_only" | "forbidden";

const PUBLIC_SHELL = ["/manifest.webmanifest", "/icon.svg", "/sw.js"];

export function classifyRequest(pathname: string): CacheClass {
  if (pathname.startsWith("/api/")) {
    return "network_only";
  }
  if (pathname.startsWith("/_next/static/") || pathname.startsWith("/__next/static/")) {
    return "shell";
  }
  if (PUBLIC_SHELL.includes(pathname)) {
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
  return ["navigate_public_shell"].includes(action);
}
