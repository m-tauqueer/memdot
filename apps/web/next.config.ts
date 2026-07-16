import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadWebSettings } from "./src/lib/settings";

// Fail closed at build/startup for invalid web configuration.
loadWebSettings(process.env);

const rootDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(rootDir, "../.."),
  poweredByHeader: false,
};

export default nextConfig;
