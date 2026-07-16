"""External MCP/client request context loading."""

from __future__ import annotations

import uuid

from fastapi import Request
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import select
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from memdot_core.db.models.tenancy import Space
from memdot_core.db.tenant import TenantContext, apply_tenant_context, reset_tenant_context
from memdot_core.request_context import RequestContext, correlation_id_for_request


def _parse_uuid_header(request: Request, name: str) -> uuid.UUID | None:
    raw = request.headers.get(name)
    if not raw:
        return None
    try:
        return uuid.UUID(raw.strip())
    except ValueError:
        return None


def _context_from_headers(
    request: Request,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    purpose: RequestPurpose,
    db: Session,
) -> RequestContext | None:
    tenant = TenantContext(account_id=account_id, actor_id=actor_id, purpose=purpose)
    try:
        reset_tenant_context(db)
        apply_tenant_context(db, tenant)
    except DBAPIError:
        reset_tenant_context(db)
        return None

    spaces = db.execute(select(Space).where(Space.account_id == account_id)).scalars().all()
    scopes: frozenset[str] = frozenset()
    if purpose == RequestPurpose.EXTERNAL_READ:
        scopes = frozenset({"memdot.memory.read"})
    elif purpose == RequestPurpose.EXTERNAL_PROPOSE:
        scopes = frozenset({"memdot.memory.propose"})
    elif purpose == RequestPurpose.EXTERNAL_INTERACTION:
        scopes = frozenset({"memdot.interaction.record"})

    return RequestContext(
        account_id=account_id,
        actor_id=actor_id,
        user_id=actor_id,
        purpose=purpose,
        correlation_id=correlation_id_for_request(request),
        scopes=scopes,
        eligible_space_ids=frozenset(row.id for row in spaces),
    )


def load_external_context(request: Request, db: Session) -> RequestContext | None:
    """Load external client context from trusted edge headers (MCP after OAuth)."""
    account_id = _parse_uuid_header(request, "X-Memdot-Account-Id")
    actor_id = _parse_uuid_header(request, "X-Memdot-Actor-Id")
    purpose_raw = (request.headers.get("X-Memdot-Purpose") or "").strip().lower()
    if account_id is None or actor_id is None or not purpose_raw:
        return None
    try:
        purpose = RequestPurpose(purpose_raw)
    except ValueError:
        return None
    if purpose not in {
        RequestPurpose.EXTERNAL_READ,
        RequestPurpose.EXTERNAL_PROPOSE,
        RequestPurpose.EXTERNAL_INTERACTION,
    }:
        return None

    return _context_from_headers(
        request,
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        db=db,
    )


def load_mcp_context(request: Request, db: Session) -> RequestContext | None:
    """Prefer external MCP context; fall back to first-party session."""
    external = load_external_context(request, db)
    if external is not None:
        return external
    from memdot_core.request_context import load_session_context

    session_ctx = load_session_context(request, db, require_csrf=False)
    if session_ctx is None:
        account_id = _parse_uuid_header(request, "X-Memdot-Account-Id")
        actor_id = _parse_uuid_header(request, "X-Memdot-Actor-Id")
        purpose_header = (request.headers.get("X-Memdot-Purpose") or "").strip().lower()
        if account_id and actor_id and request.url.path.startswith("/api/v1/mcp"):
            try:
                purpose = RequestPurpose(purpose_header or RequestPurpose.FIRST_PARTY.value)
            except ValueError:
                return None
            if purpose in {
                RequestPurpose.EXTERNAL_READ,
                RequestPurpose.EXTERNAL_PROPOSE,
                RequestPurpose.EXTERNAL_INTERACTION,
            }:
                return _context_from_headers(
                    request,
                    account_id=account_id,
                    actor_id=actor_id,
                    purpose=purpose,
                    db=db,
                )
        return None
    if request.url.path.startswith("/api/v1/mcp"):
        purpose_header = (request.headers.get("X-Memdot-Purpose") or "").strip().lower()
        if purpose_header:
            try:
                purpose = RequestPurpose(purpose_header)
            except ValueError:
                return session_ctx
            return RequestContext(
                account_id=session_ctx.account_id,
                actor_id=session_ctx.actor_id,
                user_id=session_ctx.user_id,
                purpose=purpose,
                correlation_id=session_ctx.correlation_id,
                session_id=session_ctx.session_id,
                scopes=session_ctx.scopes,
                eligible_space_ids=session_ctx.eligible_space_ids,
                last_auth_at=session_ctx.last_auth_at,
            )
    return session_ctx
