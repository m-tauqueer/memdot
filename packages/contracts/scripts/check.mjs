#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const output = path.join(packageRoot, "generated/openapi/openapi.ts");
const before = readFileSync(output, "utf8");

execFileSync("node", ["scripts/generate.mjs"], {
  cwd: packageRoot,
  stdio: "inherit",
});

const after = readFileSync(output, "utf8");
if (before !== after) {
  console.error("Generated OpenAPI types are stale. Run `pnpm generate` in @memdot/contracts.");
  process.exit(1);
}

console.log("Generated OpenAPI types are fresh.");
