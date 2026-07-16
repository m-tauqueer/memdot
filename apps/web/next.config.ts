import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { loadWebSettings } from "./src/lib/settings";

const settings = loadWebSettings(process.env);
const rootDir = path.dirname(fileURLToPath(import.meta.url));
const coreBase = settings.WEB_CORE_BASE_URL.replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(rootDir, "../.."),
  poweredByHeader: false,
  transpilePackages: ["@memdot/ui", "@memdot/contracts"],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${coreBase}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
