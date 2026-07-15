import { describe, expect, it } from "vitest";

import {
  createLiveHealthResponse,
  createMcpServer,
  createReadyHealthResponse,
  handleRequest,
} from "./server.js";
import { loadSettings } from "./settings.js";

describe("health handlers", () => {
  it("returns live health payload", () => {
    expect(createLiveHealthResponse()).toEqual({ status: "ok" });
  });

  it("returns ready health payload", () => {
    expect(createReadyHealthResponse()).toEqual({ status: "ok", service: "mcp" });
  });
});

describe("createMcpServer", () => {
  it("serves live and ready health endpoints", async () => {
    const settings = loadSettings({
      MCP_ENV: "test",
      MCP_HOST: "127.0.0.1",
      MCP_PORT: "38123",
    });

    const mcp = createMcpServer(settings);
    await mcp.listen();

    const address = mcp.server.address();
    if (!address || typeof address === "string") {
      throw new Error("Expected server to bind to a TCP port");
    }

    const baseUrl = `http://127.0.0.1:${address.port}`;

    const live = await fetch(`${baseUrl}/health/live`);
    expect(live.status).toBe(200);
    await expect(live.json()).resolves.toEqual({ status: "ok" });

    const ready = await fetch(`${baseUrl}/health/ready`);
    expect(ready.status).toBe(200);
    await expect(ready.json()).resolves.toEqual({ status: "ok", service: "mcp" });

    await mcp.close();
  });
});

describe("handleRequest", () => {
  it("returns 404 for unknown routes", async () => {
    const { createServer } = await import("node:http");
    const server = createServer(handleRequest);

    await new Promise<void>((resolve) => {
      server.listen(0, "127.0.0.1", () => resolve());
    });

    const address = server.address();
    if (!address || typeof address === "string") {
      throw new Error("Expected server to bind to a TCP port");
    }

    const response = await fetch(`http://127.0.0.1:${address.port}/unknown`);
    expect(response.status).toBe(404);

    await new Promise<void>((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  });
});
