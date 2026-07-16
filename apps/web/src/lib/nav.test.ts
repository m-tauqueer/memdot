import { describe, expect, it } from "vitest";

import { isNavActive, PRIMARY_NAV } from "./nav.js";

describe("PRIMARY_NAV", () => {
  it("keeps FSD order", () => {
    expect(PRIMARY_NAV.map((item) => item.label)).toEqual([
      "Today",
      "Library",
      "Spaces",
      "Ask",
      "Test",
      "Review",
      "Memory",
      "Integrations",
      "Settings",
    ]);
  });

  it("matches nested library routes", () => {
    const library = PRIMARY_NAV.find((item) => item.label === "Library");
    expect(library).toBeTruthy();
    expect(isNavActive("/library/sources/abc", library!)).toBe(true);
    expect(isNavActive("/today", library!)).toBe(false);
  });
});
