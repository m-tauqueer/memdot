import { NextResponse } from "next/server";

import { loadWebSettings } from "@/src/lib/settings";

/** Non-secret runtime flags for the browser shell. */
export function GET() {
  const settings = loadWebSettings(process.env);
  return NextResponse.json({
    env: settings.WEB_ENV,
    oidcAudience: settings.WEB_OIDC_AUDIENCE,
    coreBaseConfigured: Boolean(settings.WEB_CORE_BASE_URL),
  });
}
