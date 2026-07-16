"""Bearer JWT validation for external MCP clients."""

from __future__ import annotations

import time
from typing import Any, cast

import jwt
from memdot_domain.tenancy import RequestPurpose

REQUIRED_READ_SCOPE = "memdot.memory.read"
REQUIRED_PROPOSE_SCOPE = "memdot.memory.propose"
REQUIRED_INTERACTION_SCOPE = "memdot.interaction.record"

PURPOSE_REQUIRED_SCOPE: dict[RequestPurpose, str] = {
    RequestPurpose.EXTERNAL_READ: REQUIRED_READ_SCOPE,
    RequestPurpose.EXTERNAL_PROPOSE: REQUIRED_PROPOSE_SCOPE,
    RequestPurpose.EXTERNAL_INTERACTION: REQUIRED_INTERACTION_SCOPE,
}


class BearerValidationError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def parse_scopes(raw: object) -> frozenset[str]:
    if raw is None:
        return frozenset()
    if isinstance(raw, str):
        return frozenset(part for part in raw.replace(",", " ").split() if part)
    if isinstance(raw, (list, tuple, set)):
        items = cast(list[object] | tuple[object, ...] | set[object], raw)
        return frozenset(str(item) for item in items if str(item))
    return frozenset()


def scopes_allow_purpose(scopes: frozenset[str], purpose: RequestPurpose) -> bool:
    required = PURPOSE_REQUIRED_SCOPE.get(purpose)
    if required is None:
        return False
    return required in scopes


def _resource_matches(claims: dict[str, Any], resource: str) -> bool:
    if "resource" in claims:
        token_resource = claims["resource"]
        if isinstance(token_resource, list):
            return resource in {str(item) for item in cast(list[object], token_resource)}
        return str(token_resource) == resource
    # Audience-as-resource contract: aud must match configured resource exactly.
    aud = claims.get("aud")
    if isinstance(aud, list):
        return resource in {str(item) for item in cast(list[object], aud)}
    return str(aud) == resource


def validate_bearer_token(
    token: str,
    *,
    issuer: str,
    audience: str,
    resource: str | None = None,
    require_resource_claim: bool = True,
    jwks_client: Any | None = None,
    signing_key: str | bytes | None = None,
    algorithms: list[str] | None = None,
    leeway_seconds: int = 30,
) -> dict[str, Any]:
    """Validate JWT claims (issuer/JWKS|HMAC/audience/resource/exp/nbf/sub/client/scopes)."""
    if not token.strip():
        raise BearerValidationError("missing_token")
    if not issuer.strip() or not audience.strip():
        raise BearerValidationError("issuer_or_audience_unconfigured")
    if require_resource_claim and not (resource or "").strip():
        raise BearerValidationError("resource_unconfigured")

    options = {"require": ["exp", "sub", "iss", "aud"]}
    decode_kwargs: dict[str, Any] = {
        "algorithms": algorithms or ["RS256", "ES256", "HS256"],
        "issuer": issuer.rstrip("/"),
        "audience": audience,
        "leeway": leeway_seconds,
        "options": options,
    }
    try:
        if signing_key is not None:
            claims = jwt.decode(token, signing_key, **decode_kwargs)
        else:
            from memdot_core.auth.jwks import decode_with_jwks_rotation

            if jwks_client is not None:
                key = jwks_client.get_signing_key_from_jwt(token).key
                claims = jwt.decode(token, key, **decode_kwargs)
            else:
                claims = decode_with_jwks_rotation(
                    token, issuer=issuer, decode_kwargs=decode_kwargs
                )
    except BearerValidationError:
        raise
    except jwt.PyJWTError as exc:
        raise BearerValidationError("invalid_token") from exc

    now = int(time.time())
    nbf = claims.get("nbf")
    if nbf is not None and int(nbf) > now + leeway_seconds:
        raise BearerValidationError("token_not_yet_valid")
    exp = int(claims["exp"])
    if exp < now - leeway_seconds:
        raise BearerValidationError("token_expired")

    client_id = str(claims.get("client_id") or claims.get("azp") or claims.get("clientId") or "")
    if not client_id:
        raise BearerValidationError("missing_client")
    subject = str(claims["sub"])
    if not subject:
        raise BearerValidationError("missing_sub")

    if resource:
        if not _resource_matches(claims, resource):
            # Missing resource claim fails unless aud equals resource (documented contract).
            if "resource" not in claims and str(claims.get("aud")) != resource:
                if not (
                    isinstance(claims.get("aud"), list)
                    and resource in {str(x) for x in cast(list[object], claims["aud"])}
                ):
                    raise BearerValidationError("resource_mismatch")
            elif "resource" in claims:
                raise BearerValidationError("resource_mismatch")

    scopes = parse_scopes(claims.get("scope") or claims.get("scopes"))
    if not scopes:
        raise BearerValidationError("missing_scopes")

    claims["_parsed_scopes"] = scopes
    claims["_client_id"] = client_id
    claims["_subject"] = subject
    claims["_expires_at"] = exp
    return claims
