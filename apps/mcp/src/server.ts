import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

import type { McpSettings } from "./settings.js";

export type HealthResponse = {
  status: "ok";
  service?: "mcp";
};

export function createLiveHealthResponse(): HealthResponse {
  return { status: "ok" };
}

export function createReadyHealthResponse(): HealthResponse {
  return { status: "ok", service: "mcp" };
}

export function handleRequest(req: IncomingMessage, res: ServerResponse): void {
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
  const server = createServer(handleRequest);

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
