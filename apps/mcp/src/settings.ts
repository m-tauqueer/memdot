import { z } from "zod";

const settingsSchema = z.object({
  MCP_ENV: z
    .string({ required_error: "MCP_ENV is required" })
    .trim()
    .min(1, "MCP_ENV must not be blank"),
  MCP_HOST: z.string().default("0.0.0.0"),
  MCP_PORT: z.coerce.number().int().positive().default(8100),
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
