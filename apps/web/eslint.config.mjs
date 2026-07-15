import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const restrictedImports = {
  paths: [
    { name: "pg", message: "Web must not import database clients." },
    { name: "postgres", message: "Web must not import database clients." },
    { name: "openai", message: "Web must not import model SDKs." },
    { name: "minio", message: "Web must not import object storage clients." },
  ],
  patterns: [
    {
      group: ["@aws-sdk/*"],
      message: "Web must not import cloud provider SDKs.",
    },
    {
      group: ["**/services/core/**", "**/services/workers/**", "**/packages/domain-python/**"],
      message: "Web must not import backend service or Python domain internals.",
    },
  ],
};

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...nextVitals,
  ...nextTs,
  {
    ignores: [".next/**", "node_modules/**", "coverage/**"],
  },
  {
    rules: {
      "no-restricted-imports": ["error", restrictedImports],
    },
  },
];

export default config;
