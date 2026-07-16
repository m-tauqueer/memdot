const modes = ["hosted", "self_host", "test", "development"] as const;

export type WebSettings = {
  WEB_ENV: (typeof modes)[number];
  WEB_ALLOWED_ORIGINS: string;
  WEB_OIDC_ISSUER: string;
  WEB_OIDC_AUDIENCE: string;
  WEB_TELEMETRY_EXPORT: string;
  WEB_OTEL_EXPORTER_OTLP_ENDPOINT: string;
};

function normalizeMode(value: string): (typeof modes)[number] {
  const cleaned = value.trim();
  if (!cleaned) {
    throw new Error("WEB_ENV must be a non-empty string");
  }
  const normalized = cleaned.toLowerCase().replace(/-/g, "_");
  if (!(modes as readonly string[]).includes(normalized)) {
    throw new Error("WEB_ENV must be hosted|self_host|test|development");
  }
  return normalized as (typeof modes)[number];
}

export function loadWebSettings(
  env: Record<string, string | undefined> = process.env,
): WebSettings {
  const settings: WebSettings = {
    WEB_ENV: normalizeMode(env.WEB_ENV ?? "development"),
    WEB_ALLOWED_ORIGINS: env.WEB_ALLOWED_ORIGINS ?? "http://localhost:3000",
    WEB_OIDC_ISSUER: env.WEB_OIDC_ISSUER ?? "",
    WEB_OIDC_AUDIENCE: env.WEB_OIDC_AUDIENCE ?? "memdot-web",
    WEB_TELEMETRY_EXPORT: env.WEB_TELEMETRY_EXPORT ?? "off",
    WEB_OTEL_EXPORTER_OTLP_ENDPOINT: env.WEB_OTEL_EXPORTER_OTLP_ENDPOINT ?? "",
  };

  for (const origin of settings.WEB_ALLOWED_ORIGINS.split(",")) {
    const cleaned = origin.trim();
    if (!cleaned) {
      throw new Error("WEB_ALLOWED_ORIGINS must not contain blank entries");
    }
    if (cleaned.includes("*")) {
      throw new Error("WEB_ALLOWED_ORIGINS rejects wildcard trust");
    }
    if (!cleaned.startsWith("http://") && !cleaned.startsWith("https://")) {
      throw new Error("WEB_ALLOWED_ORIGINS must be absolute http(s) origins");
    }
  }

  const exportOff = ["", "off", "false", "0", "disabled"].includes(
    settings.WEB_TELEMETRY_EXPORT.trim().toLowerCase(),
  );
  if (!exportOff && !settings.WEB_OTEL_EXPORTER_OTLP_ENDPOINT.trim()) {
    throw new Error("telemetry exporter enabled without explicit endpoint");
  }

  if (settings.WEB_ENV === "self_host" || settings.WEB_ENV === "hosted") {
    if (
      !settings.WEB_OIDC_ISSUER.startsWith("http://") &&
      !settings.WEB_OIDC_ISSUER.startsWith("https://")
    ) {
      throw new Error("WEB_OIDC_ISSUER must be an absolute URL");
    }
    if (!settings.WEB_OIDC_AUDIENCE.trim()) {
      throw new Error("WEB_OIDC_AUDIENCE must not be blank");
    }
  }

  return settings;
}
