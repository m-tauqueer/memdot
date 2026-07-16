import { describe, expect, it } from "vitest";

import { Banner } from "./Banner.js";

describe("Banner", () => {
  it("renders polite live region by default", () => {
    const element = Banner({ title: "Offline", description: "Limited mode" });
    expect(element?.props["aria-live"]).toBe("polite");
    expect(element?.props.role).toBe("status");
  });
});
