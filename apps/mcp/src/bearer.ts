import { createHmac, createPublicKey, verify as verifySignature } from "node:crypto";

export type ValidatedBearer = {
  accountId: string;
  actorId: string;
  clientId: string;
  subject: string;
  scopes: string[];
  exp: number;
  token: string;
};

function b64urlJson(segment: string): Record<string, unknown> {
  const padded = segment + "=".repeat((4 - (segment.length % 4)) % 4);
  const json = Buffer.from(padded.replace(/-/g, "+").replace(/_/g, "/"), "base64").toString("utf8");
  return JSON.parse(json) as Record<string, unknown>;
}

function parseScopes(raw: unknown): string[] {
  if (typeof raw === "string") {
    return raw
      .replace(/,/g, " ")
      .split(/\s+/)
      .map((part) => part.trim())
      .filter(Boolean);
  }
  if (Array.isArray(raw)) {
    return raw.map((item) => String(item));
  }
  return [];
}

function verifyHs256(headerB64: string, payloadB64: string, sigB64: string, key: string): boolean {
  const expected = createHmac("sha256", key)
    .update(`${headerB64}.${payloadB64}`)
    .digest("base64url");
  return expected === sigB64;
}

type Jwk = {
  kty?: string;
  kid?: string;
  alg?: string;
  use?: string;
  n?: string;
  e?: string;
  crv?: string;
  x?: string;
  y?: string;
};

async function fetchJwks(jwksUri: string): Promise<Jwk[]> {
  const response = await fetch(jwksUri, { signal: AbortSignal.timeout(5000) });
  if (!response.ok) {
    throw new Error("jwks_fetch_failed");
  }
  const body = (await response.json()) as { keys?: Jwk[] };
  if (!Array.isArray(body.keys)) {
    throw new Error("jwks_invalid");
  }
  return body.keys;
}

function verifyAsymmetric(
  alg: string,
  headerB64: string,
  payloadB64: string,
  sigB64: string,
  jwk: Jwk,
): boolean {
  const keyObject = createPublicKey({ key: jwk, format: "jwk" });
  const signature = Buffer.from(sigB64.replace(/-/g, "+").replace(/_/g, "/"), "base64");
  const data = Buffer.from(`${headerB64}.${payloadB64}`);
  if (alg === "RS256") {
    return verifySignature("RSA-SHA256", data, keyObject, signature);
  }
  if (alg === "ES256") {
    return verifySignature("SHA256", data, keyObject, signature);
  }
  return false;
}

async function verifyWithJwks(
  alg: string,
  kid: string | undefined,
  headerB64: string,
  payloadB64: string,
  sigB64: string,
  jwksUri: string,
): Promise<boolean> {
  const keys = await fetchJwks(jwksUri);
  const candidates = keys.filter((key) => {
    if (kid && key.kid && key.kid !== kid) {
      return false;
    }
    if (key.alg && key.alg !== alg) {
      return false;
    }
    return true;
  });
  for (const key of candidates) {
    try {
      if (verifyAsymmetric(alg, headerB64, payloadB64, sigB64, key)) {
        return true;
      }
    } catch {
      // try next key
    }
  }
  return false;
}

/**
 * Validate bearer JWT with mandatory cryptographic verification.
 * Requires either hs256Key or jwksUri — unsigned structural acceptance is forbidden.
 */
export async function validateBearerToken(
  authorizationHeader: string | undefined,
  options: {
    issuer: string;
    audience: string;
    resource?: string;
    hs256Key?: string;
    jwksUri?: string;
  },
): Promise<ValidatedBearer> {
  if (!authorizationHeader?.toLowerCase().startsWith("bearer ")) {
    throw new Error("missing_bearer");
  }
  const token = authorizationHeader.slice(7).trim();
  if (!token) {
    throw new Error("missing_bearer");
  }
  if (!options.hs256Key && !options.jwksUri) {
    throw new Error("bearer_verification_unconfigured");
  }
  const parts = token.split(".");
  if (parts.length !== 3) {
    throw new Error("invalid_token");
  }
  const headerB64 = parts[0] ?? "";
  const payloadB64 = parts[1] ?? "";
  const sigB64 = parts[2] ?? "";
  if (!headerB64 || !payloadB64 || !sigB64) {
    throw new Error("invalid_token");
  }
  const header = b64urlJson(headerB64);
  const claims = b64urlJson(payloadB64);
  const alg = String(header.alg ?? "");
  const kid = typeof header.kid === "string" ? header.kid : undefined;

  let signatureOk = false;
  if (alg === "HS256") {
    if (!options.hs256Key) {
      throw new Error("invalid_alg");
    }
    signatureOk = verifyHs256(headerB64, payloadB64, sigB64, options.hs256Key);
  } else if (alg === "RS256" || alg === "ES256") {
    if (!options.jwksUri) {
      throw new Error("invalid_alg");
    }
    signatureOk = await verifyWithJwks(alg, kid, headerB64, payloadB64, sigB64, options.jwksUri);
  } else {
    throw new Error("invalid_alg");
  }
  if (!signatureOk) {
    throw new Error("invalid_signature");
  }

  const now = Math.floor(Date.now() / 1000);
  const exp = Number(claims.exp);
  const nbf = claims.nbf !== undefined ? Number(claims.nbf) : undefined;
  if (!Number.isFinite(exp) || exp < now) {
    throw new Error("token_expired");
  }
  if (nbf !== undefined && nbf > now) {
    throw new Error("token_not_yet_valid");
  }
  if (String(claims.iss ?? "") !== options.issuer.replace(/\/$/, "")) {
    throw new Error("issuer_mismatch");
  }
  const aud = claims.aud;
  const audOk =
    aud === options.audience || (Array.isArray(aud) && aud.map(String).includes(options.audience));
  if (!audOk) {
    throw new Error("audience_mismatch");
  }
  if (options.resource) {
    if (typeof claims.resource !== "string" || claims.resource !== options.resource) {
      throw new Error("resource_mismatch");
    }
  }
  const subject = String(claims.sub ?? "");
  const clientId = String(claims.client_id ?? claims.azp ?? "");
  const accountId = String(claims.account_id ?? claims.memdot_account_id ?? "");
  const actorId = String(claims.actor_id ?? claims.memdot_actor_id ?? "");
  const scopes = parseScopes(claims.scope ?? claims.scopes);
  if (!subject || !clientId || !accountId || !actorId || scopes.length === 0) {
    throw new Error("missing_claims");
  }
  return { accountId, actorId, clientId, subject, scopes, exp, token };
}
