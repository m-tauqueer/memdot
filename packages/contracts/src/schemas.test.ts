import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const packageRoot = fileURLToPath(new URL("../", import.meta.url));

function readJson(relativePath: string): Record<string, unknown> {
  const raw = readFileSync(join(packageRoot, relativePath), "utf8");
  return JSON.parse(raw) as Record<string, unknown>;
}

function listSchemaFiles(directory: string): string[] {
  return readdirSync(join(packageRoot, directory))
    .filter((name) => name.endsWith(".json"))
    .sort();
}

describe("JSON schemas", () => {
  it("loads all versioned JSON schema fixtures", () => {
    const files = listSchemaFiles("schemas/json");
    expect(files).toEqual([
      "export-manifest.v1.json",
      "memdot-document.v1.json",
      "problem.v1.json",
      "provider-port-health.v1.json",
      "resource-envelope.v1.json",
    ]);

    for (const file of files) {
      const schema = readJson(join("schemas/json", file));
      expect(schema.$schema).toBeTruthy();
      expect(schema.$id).toMatch(/^https:\/\/schemas\.memdot\.app\//);
    }
  });

  it("loads scaffold event fixtures", () => {
    const schema = readJson("schemas/events/scaffold.event.v1.json");
    expect(schema.$id).toBe("https://schemas.memdot.app/events/scaffold/v1.json");
    expect(schema.properties).toHaveProperty("eventName");
    expect(schema.properties).toHaveProperty("eventVersion");
  });
});

describe("generated OpenAPI types", () => {
  it("re-exports generated OpenAPI types", async () => {
    const contracts = await import("./index.js");
    expect(contracts).toBeDefined();
  });
});
