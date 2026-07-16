import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

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
    // Fallback when server was created without settings injection.
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
