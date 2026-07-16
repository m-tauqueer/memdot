/**
 * Protocol-level tests through the official MCP SDK client (not raw HTTP fixtures only).
 */
import { createHmac } from "node:crypto";
import { createServer } from "node:http";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { afterEach, describe, expect, it } from "vitest";

import { handleSdkMcpRequest } from "./mcp-sdk-server.js";
import { loadSettings } from "./settings.js";

const HS_KEY = "test-mcp-jwt-hs256-key-32bytes!!!!";

function b64url(input: string | Buffer): string {
  return Buffer.from(input).toString("base64url").replace(/=+$/g, "");
}

function mintToken(claims: Record<string, unknown> = {}): string {
  const now = Math.floor(Date.now() / 1000);
  const header = b64url(JSON.stringify({ alg: "HS256", typ: "JWT", kid: "test" }));
  const payload = b64url(
    JSON.stringify({
      iss: "https://issuer.example",
      aud: "memdot-mcp",
      resource: "memdot-mcp",
      sub: "mcp-sub",
      iat: now,
      exp: now + 300,
      account_id: "01900000-0000-7000-8000-000000000001",
      actor_id: "01900000-0000-7000-8000-000000000002",
      client_id: "mcp-client",
      scope: "memdot.memory.read",
      ...claims,
    }),
  );
  const sig = createHmac("sha256", HS_KEY).update(`${header}.${payload}`).digest("base64url");
  return `${header}.${payload}.${sig}`;
}

describe("MCP SDK Streamable HTTP protocol", () => {
  const servers: Array<ReturnType<typeof createServer>> = [];

  afterEach(async () => {
    await Promise.all(
      servers.splice(0).map(
        (server) =>
          new Promise<void>((resolve, reject) => {
            server.close((error) => (error ? reject(error) : resolve()));
          }),
      ),
    );
  });

  it("negotiates initialize and lists the five frozen tools via SDK client", async () => {
    const settings = loadSettings({
      MCP_ENV: "test",
      MCP_HOST: "127.0.0.1",
      MCP_PORT: "38140",
      MCP_OIDC_ISSUER: "https://issuer.example",
      MCP_OIDC_AUDIENCE: "memdot-mcp",
      MCP_JWT_HS256_KEY: HS_KEY,
      MCP_CORE_SERVICE_SECRET: "test-mcp-service-secret-32bytes-xx",
      MCP_CORE_BASE_URL: "http://127.0.0.1:9",
    });

    const server = createServer((req, res) => {
      void handleSdkMcpRequest(req, res, settings);
    });
    servers.push(server);
    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", () => resolve());
    });
    const address = server.address();
    if (!address || typeof address === "string") {
      throw new Error("expected tcp bind");
    }

    const token = mintToken();
    const transport = new StreamableHTTPClientTransport(
      new URL(`http://127.0.0.1:${address.port}/mcp`),
      {
        requestInit: {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      },
    );
    const client = new Client({ name: "memdot-protocol-test", version: "0.0.0" });
    await client.connect(transport);
    const listed = await client.listTools();
    const names = listed.tools.map((tool) => tool.name).sort();
    expect(names).toEqual(
      ["fetch", "prepare_context", "propose_memory", "record_interaction", "search"].sort(),
    );
    await client.close();
  });

  it("returns 401 with WWW-Authenticate when Authorization is missing", async () => {
    const settings = loadSettings({
      MCP_ENV: "test",
      MCP_HOST: "127.0.0.1",
      MCP_PORT: "38141",
      MCP_OIDC_ISSUER: "https://issuer.example",
      MCP_OIDC_AUDIENCE: "memdot-mcp",
      MCP_JWT_HS256_KEY: HS_KEY,
      MCP_CORE_SERVICE_SECRET: "test-mcp-service-secret-32bytes-xx",
    });

    const server = createServer((req, res) => {
      void handleSdkMcpRequest(req, res, settings);
    });
    servers.push(server);
    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", () => resolve());
    });
    const address = server.address();
    if (!address || typeof address === "string") {
      throw new Error("expected tcp bind");
    }

    const response = await fetch(`http://127.0.0.1:${address.port}/mcp`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        jsonrpc: "2.0",
        id: 1,
        method: "initialize",
        params: {
          protocolVersion: "2024-11-05",
          capabilities: {},
          clientInfo: { name: "t", version: "0" },
        },
      }),
    });
    expect(response.status).toBe(401);
    expect(response.headers.get("www-authenticate") || "").toContain("Bearer");
  });
});
