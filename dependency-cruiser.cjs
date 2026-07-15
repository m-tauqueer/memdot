/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "web-no-provider-or-db",
      comment: "Web must not import DB, object storage, Tex, or model SDKs",
      severity: "error",
      from: { path: "^apps/web" },
      to: {
        path: [
          "node_modules/pg($|/)",
          "node_modules/postgres",
          "node_modules/@aws-sdk",
          "node_modules/minio",
          "node_modules/openai",
          "node_modules/@anthropic",
          "services/core",
          "services/workers",
          "services/model-router",
          "packages/domain-python",
        ],
      },
    },
    {
      name: "mcp-no-provider-or-db",
      comment: "MCP must not import DB, object storage, Tex, model SDKs, or Core internals",
      severity: "error",
      from: { path: "^apps/mcp" },
      to: {
        path: [
          "node_modules/pg($|/)",
          "node_modules/postgres",
          "node_modules/@aws-sdk",
          "node_modules/minio",
          "node_modules/openai",
          "node_modules/@anthropic",
          "services/core",
          "services/workers",
          "services/model-router",
          "packages/domain-python",
          "packages/ui",
        ],
      },
    },
    {
      name: "ui-no-backend",
      comment: "UI package must stay frontend-only",
      severity: "error",
      from: { path: "^packages/ui" },
      to: {
        path: ["services/", "packages/domain-python", "apps/mcp"],
      },
    },
  ],
  options: {
    doNotFollow: {
      path: ["node_modules", "dist", ".next", "coverage"],
    },
    tsConfig: {
      fileName: "tsconfig.base.json",
    },
  },
};
