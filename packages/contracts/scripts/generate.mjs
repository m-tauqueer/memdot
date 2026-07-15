#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));
const input = path.join(packageRoot, "generated/openapi/openapi.json");
const output = path.join(packageRoot, "generated/openapi/openapi.ts");
const openapiCli = path.join(packageRoot, "node_modules", ".bin", "openapi-typescript");

execFileSync(openapiCli, [input, "-o", output], {
  cwd: packageRoot,
  stdio: "inherit",
});

console.log(`Generated OpenAPI types at ${path.relative(packageRoot, output)}`);
