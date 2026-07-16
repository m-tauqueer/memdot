import { z } from "zod";

const modes = ["hosted", "self_host", "test", "development"] as const;

const settingsSchema = z
  .object({
    MCP_ENV: z
      .string({ required_error: "MCP_ENV is required" })
      .trim()
      .min(1, "MCP_ENV must not be blank")
      .transform((value) => value.toLowerCase().replace(/-/g, "_"))
      .refine(
        (value): value is (typeof modes)[number] => (modes as readonly string[]).includes(value),
        {
          message: "MCP_ENV must be hosted|self_host|test|development",
        },
      ),
    MCP_HOST: z.string().default("0.0.0.0"),
    MCP_PORT: z.coerce.number().int().positive().default(8100),
    MCP_OIDC_ISSUER: z.string().default(""),
    // Optional in-cluster discovery base for readiness (defaults to issuer).
    MCP_OIDC_DISCOVERY_URL: z.string().default(""),
    MCP_OIDC_AUDIENCE: z.string().default("memdot-mcp"),
    MCP_ALLOWED_ORIGINS: z.string().default("http://localhost:3000"),
    MCP_TELEMETRY_EXPORT: z.string().default("off"),
    MCP_OTEL_EXPORTER_OTLP_ENDPOINT: z.string().default(""),
    MCP_PROVIDER_API_KEY: z.string().default(""),
  })
  .superRefine((value, ctx) => {
    for (const origin of value.MCP_ALLOWED_ORIGINS.split(",")) {
      const cleaned = origin.trim();
      if (!cleaned) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "MCP_ALLOWED_ORIGINS must not be blank",
        });
        continue;
      }
      if (cleaned.includes("*")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "MCP_ALLOWED_ORIGINS rejects wildcard trust",
        });
      }
      if (!cleaned.startsWith("http://") && !cleaned.startsWith("https://")) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "MCP_ALLOWED_ORIGINS must be absolute http(s) origins",
        });
      }
    }

    const exportOff = ["", "off", "false", "0", "disabled"].includes(
      value.MCP_TELEMETRY_EXPORT.trim().toLowerCase(),
    );
    if (!exportOff && value.MCP_OTEL_EXPORTER_OTLP_ENDPOINT.trim() === "") {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "telemetry exporter enabled without explicit endpoint",
      });
    }

    if (value.MCP_ENV === "self_host" || value.MCP_ENV === "hosted") {
      if (
        !value.MCP_OIDC_ISSUER.startsWith("http://") &&
        !value.MCP_OIDC_ISSUER.startsWith("https://")
      ) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "MCP_OIDC_ISSUER must be an absolute URL",
        });
      }
      if (!value.MCP_OIDC_AUDIENCE.trim()) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "MCP_OIDC_AUDIENCE must not be blank",
        });
      }
    }

    if (
      value.MCP_PROVIDER_API_KEY &&
      (value.MCP_PROVIDER_API_KEY.startsWith("sk-") ||
        value.MCP_PROVIDER_API_KEY.includes("BEGIN PRIVATE KEY"))
    ) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "MCP_PROVIDER_API_KEY must not embed plaintext provider credentials",
      });
    }
  });

export type McpSettings = z.infer<typeof settingsSchema>;

export function loadSettings(env: NodeJS.ProcessEnv = process.env): McpSettings {
  const parsed = settingsSchema.safeParse(env);
  if (!parsed.success) {
    const message = parsed.error.issues.map((issue) => issue.message).join("; ");
    throw new Error(message);
  }

  return parsed.data;
}
