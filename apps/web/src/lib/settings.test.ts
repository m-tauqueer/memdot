import { describe, expect, it } from "vitest";

import { loadWebSettings } from "./settings.js";

describe("web settings", () => {
  it("accepts development mode", () => {
    expect(loadWebSettings({ WEB_ENV: "development" }).WEB_ENV).toBe("development");
  });

  it("rejects exporter without endpoint", () => {
    expect(() =>
      loadWebSettings({
        WEB_ENV: "development",
        WEB_TELEMETRY_EXPORT: "otlp",
        WEB_OTEL_EXPORTER_OTLP_ENDPOINT: "",
      }),
    ).toThrow(/exporter/);
  });

  it("rejects unknown mode", () => {
    expect(() => loadWebSettings({ WEB_ENV: "staging" })).toThrow(/WEB_ENV/);
  });

  it("rejects wildcard origins", () => {
    expect(() =>
      loadWebSettings({ WEB_ENV: "development", WEB_ALLOWED_ORIGINS: "https://*" }),
    ).toThrow(/wildcard/);
  });

  it("requires issuer in self_host mode", () => {
    expect(() =>
      loadWebSettings({
        WEB_ENV: "self_host",
        WEB_OIDC_ISSUER: "",
        WEB_ALLOWED_ORIGINS: "https://localhost:8443",
      }),
    ).toThrow(/WEB_OIDC_ISSUER/);
  });
});
