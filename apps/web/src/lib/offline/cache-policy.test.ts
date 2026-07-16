import { describe, expect, it } from "vitest";

import { classifyRequest, mayServiceWorkerCache, offlineActionAllowed } from "./cache-policy.js";

describe("cache policy", () => {
  it("keeps API responses network-only", () => {
    expect(classifyRequest("/api/v1/auth/session")).toBe("network_only");
    expect(mayServiceWorkerCache("/api/v1/sources")).toBe(false);
  });

  it("allows only public/static shell assets", () => {
    expect(classifyRequest("/today")).toBe("network_only");
    expect(mayServiceWorkerCache("/manifest.webmanifest")).toBe(true);
    expect(mayServiceWorkerCache("/library")).toBe(false);
  });

  it("limits offline actions", () => {
    expect(offlineActionAllowed("ask", false)).toBe(false);
    expect(offlineActionAllowed("read_pin", false)).toBe(false);
    expect(offlineActionAllowed("ask", true)).toBe(true);
  });
});
