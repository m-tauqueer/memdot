import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

import {
  MCP_TOOLS,
  buildProtectedResourceMetadata,
  invokeTool,
  mcpToolResponse,
} from "./tools.js";
import type { McpSettings } from "./settings.js";

export type HealthResponse = {
  status: "ok" | "degraded";
  service?: "mcp";
  dependency?: "oidc";
};

export function createLiveHealthResponse(): HealthResponse {
  return { status: "ok" };
}

export function createReadyHealthResponse(options?: {
  oidcOk?: boolean;
  oidcConfigured?: boolean;
}): HealthResponse {
  const oidcConfigured = options?.oidcConfigured ?? false;
  const oidcOk = options?.oidcOk ?? true;
  if (oidcConfigured && !oidcOk) {
    return { status: "degraded", service: "mcp", dependency: "oidc" };
  }
  return { status: "ok", service: "mcp" };
}

async function probeOidcDiscovery(issuer: string, timeoutMs = 2000): Promise<boolean> {
  if (!issuer.trim()) {
    return true;
  }
  const url = `${issuer.replace(/\/$/, "")}/.well-known/openid-configuration`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      return false;
    }
    const body = (await response.json()) as { issuer?: string; jwks_uri?: string };
    return Boolean(body.issuer && body.jwks_uri);
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

function readJsonBody(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => {
      const raw = Buffer.concat(chunks).toString("utf8").trim();
      if (!raw) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(raw) as Record<string, unknown>);
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

function writeJson(res: ServerResponse, status: number, payload: unknown): void {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(payload));
}

async function handleMcpRoutes(
  req: IncomingMessage,
  res: ServerResponse,
  settings: McpSettings,
  url: string,
): Promise<boolean> {
  if (req.method === "GET" && url === "/.well-known/oauth-protected-resource") {
    writeJson(res, 200, buildProtectedResourceMetadata(settings));
    return true;
  }

  if (req.method === "GET" && url === "/mcp/tools") {
    writeJson(res, 200, { tools: MCP_TOOLS });
    return true;
  }

  if (req.method === "POST" && url === "/mcp/tools/call") {
    const accountId = req.headers["x-memdot-account-id"];
    const actorId = req.headers["x-memdot-actor-id"];
    if (typeof accountId !== "string" || typeof actorId !== "string") {
      writeJson(res, 404, { code: "not_found" });
      return true;
    }
    try {
      const body = await readJsonBody(req);
      const name = String(body.name ?? "");
      const args = (body.arguments ?? {}) as Record<string, unknown>;
      const payload = await invokeTool({
        name,
        arguments: args,
        accountId,
        actorId,
        coreBaseUrl: settings.MCP_CORE_BASE_URL,
      });
      writeJson(res, 200, mcpToolResponse(payload));
    } catch {
      writeJson(res, 404, { code: "not_found" });
    }
    return true;
  }

  return false;
}

export function handleRequest(req: IncomingMessage, res: ServerResponse): void {
  void handleRequestAsync(req, res);
}

async function handleRequestAsync(req: IncomingMessage, res: ServerResponse): Promise<void> {
  const url = req.url?.split("?")[0] ?? "/";

  if (req.method === "GET" && url === "/health/live") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(createLiveHealthResponse()));
    return;
  }

  if (req.method === "GET" && url === "/health/ready") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(createReadyHealthResponse()));
    return;
  }

  res.writeHead(404, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ status: "not_found" }));
}

export type McpHttpServer = {
  server: Server;
  listen: () => Promise<void>;
  close: () => Promise<void>;
};

export function createMcpServer(settings: McpSettings): McpHttpServer {
  const server = createServer((req, res) => {
    void (async () => {
      const url = req.url?.split("?")[0] ?? "/";
      if (req.method === "GET" && url === "/health/live") {
        res.writeHead(200, { "Content-Type": "application/json" });
        res.end(JSON.stringify(createLiveHealthResponse()));
        return;
      }
      if (req.method === "GET" && url === "/health/ready") {
        const oidcConfigured = Boolean(settings.MCP_OIDC_ISSUER.trim());
        const discoveryBase =
          settings.MCP_OIDC_DISCOVERY_URL.trim() || settings.MCP_OIDC_ISSUER.trim();
        const oidcOk = oidcConfigured ? await probeOidcDiscovery(discoveryBase) : true;
        const payload = createReadyHealthResponse({ oidcConfigured, oidcOk });
        const code = payload.status === "ok" ? 200 : 503;
        res.writeHead(code, { "Content-Type": "application/json" });
        res.end(JSON.stringify(payload));
        return;
      }
      if (await handleMcpRoutes(req, res, settings, url)) {
        return;
      }
      res.writeHead(404, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "not_found" }));
    })();
  });

  return {
    server,
    listen: () =>
      new Promise((resolve, reject) => {
        server.once("error", reject);
        server.listen(settings.MCP_PORT, settings.MCP_HOST, () => resolve());
      }),
    close: () =>
      new Promise((resolve, reject) => {
        server.close((error) => {
          if (error) {
            reject(error);
            return;
          }
          resolve();
        });
      }),
  };
}
