import { describe, expect, it } from "vitest";

import { loadSettings } from "../src/settings.js";

describe("mcp settings", () => {
  it("accepts development defaults", () => {
    const settings = loadSettings({
      MCP_ENV: "development",
    });
    expect(settings.MCP_ENV).toBe("development");
  });

  it("rejects wildcard origins", () => {
    expect(() =>
      loadSettings({
        MCP_ENV: "development",
        MCP_ALLOWED_ORIGINS: "https://*",
      }),
    ).toThrow(/wildcard/);
  });

  it("rejects exporter without endpoint", () => {
    expect(() =>
      loadSettings({
        MCP_ENV: "development",
        MCP_TELEMETRY_EXPORT: "otlp",
        MCP_OTEL_EXPORTER_OTLP_ENDPOINT: "",
      }),
    ).toThrow(/exporter/);
  });

  it("requires issuer in self_host mode", () => {
    expect(() =>
      loadSettings({
        MCP_ENV: "self_host",
        MCP_OIDC_ISSUER: "",
      }),
    ).toThrow(/OIDC_ISSUER/);
  });
});
