/**
 * Web server readiness choice (Phase 2):
 * OIDC discovery is NOT required for `/api/health` readiness.
 * The web process can serve static/shell routes without the IdP; OIDC is enforced
 * at authenticated navigation / session establishment (Phase 3+), not process ready.
 * Telemetry outage also must not fail readiness.
 */
export type WebHealthPayload = {
  status: "ok";
  service: "web";
  oidc_required_for_readiness: false;
};

export function createWebHealthPayload(): WebHealthPayload {
  return {
    status: "ok",
    service: "web",
    oidc_required_for_readiness: false,
  };
}
