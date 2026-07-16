import { describe, expect, it } from "vitest";

import { PRIMARY_NAV } from "./nav.js";

/** Route smoke inventory for Wave 9 foundation (build also enumerates App Router pages). */
const FOUNDATION_ROUTES = [
  "/",
  "/auth",
  "/onboarding",
  "/today",
  "/library",
  "/spaces",
  "/ask",
  "/test",
  "/review",
  "/memory/items",
  "/memory/proposed",
  "/memory/activity",
  "/integrations",
  "/settings",
  "/api/health",
  "/api/runtime-config",
];

describe("route smoke inventory", () => {
  it("keeps primary nav destinations in the foundation set", () => {
    for (const item of PRIMARY_NAV) {
      expect(FOUNDATION_ROUTES).toContain(item.href);
    }
  });

  it("lists auth and onboarding outside the app shell", () => {
    expect(FOUNDATION_ROUTES).toEqual(expect.arrayContaining(["/auth", "/onboarding"]));
  });
});
