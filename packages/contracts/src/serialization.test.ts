import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const repoRoot = fileURLToPath(new URL("../../../", import.meta.url));

describe("serialization equivalence", () => {
  it("matches the Python problem+json fixture", () => {
    const fixture = JSON.parse(
      readFileSync(join(repoRoot, "tests/contracts/fixtures/problem.v1.example.json"), "utf8"),
    ) as Record<string, unknown>;
    expect(fixture).toEqual({
      type: "about:blank",
      title: "Internal Server Error",
      status: 500,
      code: "internal_error",
    });
  });
});
