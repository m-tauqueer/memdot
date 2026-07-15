import { describe, expect, it } from "vitest";

import { loadSettings } from "./settings.js";

describe("loadSettings", () => {
  it("parses MCP settings from the environment", () => {
    expect(
      loadSettings({
        MCP_ENV: "development",
        MCP_HOST: "127.0.0.1",
        MCP_PORT: "8100",
      }),
    ).toEqual({
      MCP_ENV: "development",
      MCP_HOST: "127.0.0.1",
      MCP_PORT: 8100,
    });
  });

  it("fails when MCP_ENV is blank", () => {
    expect(() =>
      loadSettings({
        MCP_ENV: "   ",
      }),
    ).toThrow(/MCP_ENV must not be blank/);
  });

  it("fails when MCP_ENV is missing", () => {
    expect(() => loadSettings({})).toThrow(/MCP_ENV/);
  });
});
