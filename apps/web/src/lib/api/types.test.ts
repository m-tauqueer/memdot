import { describe, expect, it } from "vitest";

import { BROWSER_API_PATHS } from "./types.js";

describe("generated API path contract", () => {
  it("covers auth and core browser seams", () => {
    expect(BROWSER_API_PATHS).toContain("/api/v1/auth/session");
    expect(BROWSER_API_PATHS).toContain("/api/v1/auth/oidc/begin");
    expect(BROWSER_API_PATHS).toContain("/api/v1/export/account");
  });
});
