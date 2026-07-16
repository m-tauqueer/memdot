"""External MCP/client request context — grant-resolved only; no browser MCP fallback."""

from __future__ import annotations

import os
import uuid

from fastapi import Request
from memdot_domain.tenancy import RequestPurpose, SpaceVisibility
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from memdot_core.auth.bearer import (
    BearerValidationError,
    scopes_allow_purpose,
    validate_bearer_token,
)
from memdot_core.auth.grant_resolve import resolve_external_grant
from memdot_core.auth.jwks import get_jwks_client
from memdot_core.auth.service_auth import parse_service_auth
from memdot_core.db.models.tenancy import Space
from memdot_core.db.tenant import TenantContext, apply_tenant_context, reset_tenant_context
from memdot_core.request_context import RequestContext, correlation_id_for_request


def _eligible_non_private_spaces(db: Session, account_id: uuid.UUID) -> frozenset[uuid.UUID]:
    """Empty set means no access — never treat as all Spaces."""
    spaces = db.execute(select(Space).where(Space.account_id == account_id)).scalars().all()
    return frozenset(
        row.id for row in spaces if SpaceVisibility(row.visibility) != SpaceVisibility.PRIVATE
    )


def build_external_request_context(
    request: Request,
    db: Session,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    purpose: RequestPurpose,
    scopes: frozenset[str],
) -> RequestContext | None:
    if purpose not in {
        RequestPurpose.EXTERNAL_READ,
        RequestPurpose.EXTERNAL_PROPOSE,
        RequestPurpose.EXTERNAL_INTERACTION,
    }:
        return None
    if not scopes_allow_purpose(scopes, purpose):
        return None
    tenant = TenantContext(account_id=account_id, actor_id=actor_id, purpose=purpose)
    try:
        reset_tenant_context(db)
        apply_tenant_context(db, tenant)
    except DBAPIError:
        reset_tenant_context(db)
        return None
    return RequestContext(
        account_id=account_id,
        actor_id=actor_id,
        user_id=actor_id,
        purpose=purpose,
        correlation_id=correlation_id_for_request(request),
        scopes=scopes,
        eligible_space_ids=_eligible_non_private_spaces(db, account_id),
    )


def _extract_bearer(request: Request) -> str | None:
    header = request.headers.get("Authorization") or ""
    if not header.lower().startswith("bearer "):
        return None
    token = header[7:].strip()
    return token or None


def load_external_context(
    request: Request,
    db: Session,
    *,
    required_purpose: RequestPurpose | None = None,
) -> RequestContext | None:
    """Load context from service-auth or bearer, always re-resolving DB grant."""
    purpose_hint = required_purpose
    service_grant = parse_service_auth(
        request,
        db,
        secret=os.environ.get("CORE_MCP_SERVICE_SECRET")
        or os.environ.get("MCP_CORE_SERVICE_SECRET"),
    )
    if service_grant is not None:
        try:
            resolved = resolve_external_grant(
                db,
                client_id=service_grant.client_id,
                account_id=service_grant.account_id,
                actor_id=service_grant.actor_id,
                token_scopes=service_grant.scopes,
            )
        except BearerValidationError:
            return None
        if (
            resolved.account_id != service_grant.account_id
            or resolved.actor_id != service_grant.actor_id
        ):
            return None
        purpose = purpose_hint or service_grant.purpose
        if purpose_hint is not None and service_grant.purpose != purpose_hint:
            return None
        return build_external_request_context(
            request,
            db,
            account_id=resolved.account_id,
            actor_id=resolved.actor_id,
            purpose=purpose,
            scopes=resolved.scopes,
        )

    token = _extract_bearer(request)
    if token is None:
        return None

    issuer = (os.environ.get("CORE_OIDC_ISSUER") or os.environ.get("MCP_OIDC_ISSUER") or "").strip()
    audience = (
        os.environ.get("CORE_OIDC_AUDIENCE") or os.environ.get("MCP_OIDC_AUDIENCE") or "memdot-mcp"
    ).strip()
    resource = (os.environ.get("CORE_MCP_RESOURCE") or "").strip()
    if not resource:
        # Audience-as-resource only when explicitly enabled.
        if os.environ.get("CORE_MCP_AUDIENCE_AS_RESOURCE", "").lower() in {"1", "true", "yes"}:
            resource = audience
        else:
            return None
    hmac_key = os.environ.get("CORE_MCP_JWT_HS256_KEY") or os.environ.get("MCP_JWT_HS256_KEY")
    try:
        jwks_client = None
        if not hmac_key:
            jwks_client = get_jwks_client(issuer)
        claims = validate_bearer_token(
            token,
            issuer=issuer,
            audience=audience,
            resource=resource,
            require_resource_claim=True,
            signing_key=hmac_key.encode("utf-8") if hmac_key else None,
            algorithms=["HS256"] if hmac_key else None,
            jwks_client=jwks_client,
        )
        token_scopes = frozenset(claims["_parsed_scopes"])
        client_id = str(claims["_client_id"])
        account_hint = claims.get("account_id") or claims.get("memdot_account_id")
        actor_hint = claims.get("actor_id") or claims.get("memdot_actor_id")
        resolved = resolve_external_grant(
            db,
            client_id=client_id,
            account_id=uuid.UUID(str(account_hint)) if account_hint else None,
            actor_id=uuid.UUID(str(actor_hint)) if actor_hint else None,
            token_scopes=token_scopes,
        )
    except (BearerValidationError, ValueError, KeyError):
        return None

    purpose = purpose_hint or RequestPurpose.EXTERNAL_READ
    if not scopes_allow_purpose(resolved.scopes, purpose):
        return None
    return build_external_request_context(
        request,
        db,
        account_id=resolved.account_id,
        actor_id=resolved.actor_id,
        purpose=purpose,
        scopes=resolved.scopes,
    )


def load_mcp_context(
    request: Request,
    db: Session,
    *,
    required_purpose: RequestPurpose | None = None,
) -> RequestContext | None:
    """MCP routes accept only validated external grants — never browser cookies."""
    return load_external_context(request, db, required_purpose=required_purpose)
