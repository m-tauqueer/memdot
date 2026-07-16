/**
 * Official MCP SDK Streamable HTTP transport (stateless JSON responses).
 * Identity is validated before connect; tools call Core via service-auth.
 */
import { AsyncLocalStorage } from "node:async_hooks";
import type { IncomingMessage, ServerResponse } from "node:http";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { Transport } from "@modelcontextprotocol/sdk/shared/transport.js";
import { z } from "zod";

import { validateBearerToken, type ValidatedBearer } from "./bearer.js";
import { invokeTool } from "./tools.js";
import type { McpSettings } from "./settings.js";

const MAX_BODY_BYTES = 256 * 1024;
const identityStore = new AsyncLocalStorage<ValidatedBearer>();

async function readLimitedBody(req: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];
  let total = 0;
  for await (const chunk of req) {
    const buf = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    total += buf.length;
    if (total > MAX_BODY_BYTES) {
      throw new Error("payload_too_large");
    }
    chunks.push(buf);
  }
  const raw = Buffer.concat(chunks).toString("utf8").trim();
  if (!raw) {
    return {};
  }
  return JSON.parse(raw) as unknown;
}

function writeUnauthorized(res: ServerResponse, settings: McpSettings): void {
  const resource = settings.MCP_OIDC_AUDIENCE || "memdot-mcp";
  res.writeHead(401, {
    "Content-Type": "application/json",
    "WWW-Authenticate": `Bearer realm="memdot-mcp", resource_metadata="/.well-known/oauth-protected-resource", resource="${resource}"`,
  });
  res.end(
    JSON.stringify({ jsonrpc: "2.0", error: { code: -32001, message: "Unauthorized" }, id: null }),
  );
}

async function requireIdentity(
  req: IncomingMessage,
  settings: McpSettings,
): Promise<ValidatedBearer> {
  const issuer = settings.MCP_OIDC_ISSUER || "https://issuer.example";
  const options: {
    issuer: string;
    audience: string;
    resource?: string;
    hs256Key?: string;
    jwksUri?: string;
  } = {
    issuer,
    audience: settings.MCP_OIDC_AUDIENCE || "memdot-mcp",
    resource: settings.MCP_OIDC_AUDIENCE || "memdot-mcp",
  };
  if (settings.MCP_JWT_HS256_KEY) {
    options.hs256Key = settings.MCP_JWT_HS256_KEY;
  } else if (issuer.startsWith("http")) {
    options.jwksUri = `${issuer.replace(/\/$/, "")}/protocol/openid-connect/certs`;
  }
  return validateBearerToken(req.headers.authorization, options);
}

function identityHeaders(settings: McpSettings, identity: ValidatedBearer) {
  return {
    accountId: identity.accountId,
    actorId: identity.actorId,
    scopes: identity.scopes,
    clientId: identity.clientId,
    subject: identity.subject,
    authorization: `Bearer ${identity.token}`,
    serviceSecret: settings.MCP_CORE_SERVICE_SECRET,
    exp: identity.exp,
  };
}

function textResult(payload: unknown) {
  const structuredContent =
    typeof payload === "object" && payload !== null && !Array.isArray(payload)
      ? (payload as Record<string, unknown>)
      : { value: payload };
  return {
    structuredContent,
    content: [{ type: "text" as const, text: JSON.stringify(structuredContent) }],
  };
}

export function buildSdkMcpServer(settings: McpSettings): McpServer {
  const server = new McpServer({ name: "memdot-mcp", version: "0.1.0" });

  const run = async (name: string, args: Record<string, unknown>) => {
    const identity = identityStore.getStore();
    if (!identity) {
      throw new Error("unauthorized");
    }
    const payload = await invokeTool({
      name,
      arguments: args,
      coreBaseUrl: settings.MCP_CORE_BASE_URL,
      identity: identityHeaders(settings, identity),
    });
    return textResult(payload);
  };

  server.tool("search", { query: z.string().min(1).max(2048) }, async (args) =>
    run("search", args as Record<string, unknown>),
  );
  server.tool("fetch", { id: z.string().min(1) }, async (args) =>
    run("fetch", args as Record<string, unknown>),
  );
  server.tool(
    "prepare_context",
    {
      query: z.string(),
      purpose: z.string().optional(),
      max_tokens: z.number().int().optional(),
      max_items: z.number().int().optional(),
    },
    async (args) => run("prepare_context", args as Record<string, unknown>),
  );
  server.tool(
    "propose_memory",
    {
      space_id: z.string().uuid(),
      assertion_text: z.string().min(1),
      title: z.string().optional(),
    },
    async (args) => run("propose_memory", args as Record<string, unknown>),
  );
  server.tool(
    "record_interaction",
    {
      space_id: z.string().uuid(),
      client_conversation_id: z.string().min(1),
      role: z.string().min(1),
      content: z.string().min(1),
      completeness: z.string().min(1),
      idempotency_key: z.string().optional(),
      occurred_at: z.string().optional(),
      parent_turn_id: z.string().uuid().optional(),
      context_receipt_id: z.string().uuid().optional(),
      client_turn_id: z.string().optional(),
    },
    async (args) => run("record_interaction", args as Record<string, unknown>),
  );

  return server;
}

export async function handleSdkMcpRequest(
  req: IncomingMessage,
  res: ServerResponse,
  settings: McpSettings,
): Promise<void> {
  let identity: ValidatedBearer;
  try {
    identity = await requireIdentity(req, settings);
  } catch {
    writeUnauthorized(res, settings);
    return;
  }

  let body: unknown;
  try {
    body = await readLimitedBody(req);
  } catch (error) {
    const oversized = error instanceof Error && error.message === "payload_too_large";
    res.writeHead(oversized ? 413 : 400, { "Content-Type": "application/json" });
    res.end(JSON.stringify({ error: oversized ? "payload_too_large" : "invalid_json" }));
    return;
  }

  await identityStore.run(identity, async () => {
    const transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: undefined,
      enableJsonResponse: true,
    });
    const server = buildSdkMcpServer(settings);
    let closed = false;
    const closeResources = () => {
      if (closed) return;
      closed = true;
      void server.close().finally(() => transport.close());
    };
    res.once("finish", closeResources);
    res.once("close", closeResources);
    // SDK Transport.sessionId is optional at runtime in stateless mode.
    try {
      await server.connect(transport as unknown as Transport);
      await transport.handleRequest(req, res, body);
    } catch {
      if (!res.headersSent) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "mcp_request_failed" }));
      }
    }
  });
}
