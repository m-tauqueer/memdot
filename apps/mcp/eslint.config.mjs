import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

const restrictedImports = {
  paths: [
    { name: "pg", message: "MCP must not import database clients." },
    { name: "postgres", message: "MCP must not import database clients." },
    { name: "openai", message: "MCP must not import model SDKs." },
    { name: "minio", message: "MCP must not import object storage clients." },
    { name: "@memdot/ui", message: "MCP must not import UI package." },
  ],
  patterns: [
    {
      group: ["@aws-sdk/*"],
      message: "MCP must not import cloud provider SDKs.",
    },
    {
      group: [
        "**/services/core/**",
        "**/services/workers/**",
        "**/packages/domain-python/**",
        "**/packages/ui/**",
      ],
      message: "MCP must not import backend, domain, or UI internals.",
    },
  ],
};

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores: ["dist/**", "node_modules/**", "coverage/**"],
  },
  {
    rules: {
      "no-restricted-imports": ["error", restrictedImports],
    },
  },
);
