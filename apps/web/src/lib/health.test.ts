import { describe, expect, it } from "vitest";

import { createWebHealthPayload } from "./health";

describe("createWebHealthPayload", () => {
  it("returns the web health contract", () => {
    expect(createWebHealthPayload()).toEqual({
      status: "ok",
      service: "web",
    });
  });
});
