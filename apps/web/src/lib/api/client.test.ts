import { describe, expect, it } from "vitest";

import { ApiError } from "./client.js";

describe("ApiError", () => {
  it("reads camelCase correlation and conflict revision ids", () => {
    const err = new ApiError(
      {
        status: 409,
        code: "conflict",
        detail: "Base revision is stale.",
        correlationId: "corr-1",
        currentRevisionId: "rev-2",
      },
      409,
    );
    expect(err.correlationId).toBe("corr-1");
    expect(err.currentRevisionId).toBe("rev-2");
    expect(err.isConflict).toBe(true);
  });
});
