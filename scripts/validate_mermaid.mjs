#!/usr/bin/env node
/**
 * Parse every ```mermaid fence with Mermaid's parser (not a first-line heuristic).
 * Invalid diagram syntax fails the process.
 *
 * Loads via --import ./scripts/register-dompurify.mjs so Mermaid receives a
 * JSDOM-backed DOMPurify in Node.
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import mermaid from "mermaid";

const root = fileURLToPath(new URL("..", import.meta.url));
const mermaidFence = /```mermaid\n([\s\S]*?)```/g;

mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });

function collectMarkdownFiles(dir, out = []) {
  for (const entry of readdirSync(dir)) {
    if (entry === "node_modules" || entry === ".venv" || entry === ".git" || entry === ".next") {
      continue;
    }
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      collectMarkdownFiles(full, out);
    } else if (entry.endsWith(".md")) {
      out.push(full);
    }
  }
  return out;
}

const roots = [
  join(root, "AGENTS.md"),
  join(root, "CONTEXT.md"),
  join(root, "CONTRIBUTING.md"),
  join(root, "OWNERS.md"),
  join(root, "README.md"),
  join(root, "IMPLEMENTATION_PLAN.md"),
  join(root, "IMPLEMENTATION_TRACKER.md"),
  ...collectMarkdownFiles(join(root, "docs")),
];

const files = [...new Set(roots)].filter((path) => {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
});

let diagrams = 0;
const errors = [];

for (const file of files) {
  const text = readFileSync(file, "utf8");
  let match;
  let index = 0;
  const rel = relative(root, file);
  while ((match = mermaidFence.exec(text)) !== null) {
    index += 1;
    const source = match[1].trim();
    diagrams += 1;
    try {
      await mermaid.parse(source);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      errors.push(`${rel} mermaid#${index}: ${message}`);
    }
  }
}

try {
  await mermaid.parse("flowchart LR\n  A-->");
  errors.push("negative-control: invalid diagram unexpectedly parsed");
} catch {
  // expected
}

if (errors.length > 0) {
  console.error("Mermaid parse validation failed:");
  for (const error of errors) {
    console.error(`  - ${error}`);
  }
  process.exit(1);
}

console.log(`Parsed ${diagrams} Mermaid diagrams across ${files.length} markdown files.`);
