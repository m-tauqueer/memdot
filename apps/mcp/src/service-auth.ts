import { createHmac, randomBytes, createHash } from "node:crypto";

export type ServiceAuthIdentity = {
  accountId: string;
  actorId: string;
  purpose: "external_read" | "external_propose" | "external_interaction";
  scopes: string[];
  clientId: string;
  subject: string;
  exp?: number;
  authorization?: string;
};

function b64url(raw: Buffer | string): string {
  return Buffer.from(raw)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/g, "");
}

export function buildServiceAuthHeaders(
  secret: string,
  identity: ServiceAuthIdentity,
): Record<string, string> {
  if (secret.trim().length < 32) {
    throw new Error("MCP_CORE_SERVICE_SECRET must contain at least 32 characters");
  }
  const ts = Math.floor(Date.now() / 1000).toString();
  const nonce = randomBytes(16).toString("hex");
  const payload: Record<string, unknown> = {
    v: 1,
    account_id: identity.accountId,
    actor_id: identity.actorId,
    purpose: identity.purpose,
    scopes: [...identity.scopes].sort(),
    client_id: identity.clientId,
    sub: identity.subject,
    exp: identity.exp ?? Math.floor(Date.now() / 1000) + 300,
  };
  if (identity.authorization) {
    payload.authorization_sha256 = createHash("sha256")
      .update(identity.authorization)
      .digest("hex");
  }
  const bodyB64 = b64url(JSON.stringify(payload));
  const signature = createHmac("sha256", secret).update(`${ts}.${nonce}.${bodyB64}`).digest("hex");
  return {
    "X-Memdot-Service-Auth": "v1",
    "X-Memdot-Service-Ts": ts,
    "X-Memdot-Service-Nonce": nonce,
    "X-Memdot-Service-Body": bodyB64,
    "X-Memdot-Service-Sig": signature,
  };
}
