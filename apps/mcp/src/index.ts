import { createMcpServer } from "./server.js";
import { loadSettings } from "./settings.js";

function main(): void {
  const settings = loadSettings();
  const mcp = createMcpServer(settings);

  mcp.listen().then(() => {
    console.log(`MCP health service listening on http://${settings.MCP_HOST}:${settings.MCP_PORT}`);
  });

  const shutdown = () => {
    void mcp.close().finally(() => process.exit(0));
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main();
