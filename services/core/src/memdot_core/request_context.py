"""Authenticated request context and transaction ownership."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import Request
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text
from sqlalchemy.orm import Session

from memdot_core.auth.sessions import (
    SessionCookieNames,
    hash_secret,
    is_session_active,
    recent_auth_satisfied,
    verify_csrf_token,
)
from memdot_core.db.tenant import TenantContext


@dataclass
class RequestContext:
    account_id: uuid.UUID
    actor_id: uuid.UUID
    user_id: uuid.UUID
    purpose: RequestPurpose
    correlation_id: uuid.UUID
    session_id: uuid.UUID | None = None
    scopes: frozenset[str] = field(default_factory=lambda: frozenset())
    eligible_space_ids: frozenset[uuid.UUID] = field(default_factory=lambda: frozenset())
    last_auth_at: datetime | None = None

    def tenant(self) -> TenantContext:
        return TenantContext(
            account_id=self.account_id,
            actor_id=self.actor_id,
            purpose=self.purpose,
        )

    def require_recent_auth(self, *, max_age_minutes: int = 15) -> bool:
        if self.last_auth_at is None:
            return False
        return recent_auth_satisfied(self.last_auth_at, max_age_minutes=max_age_minutes)


def correlation_id_for_request(request: Request) -> uuid.UUID:
    raw = request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id")
    if raw:
        try:
            return uuid.UUID(raw)
        except ValueError:
            pass
    return new_uuid7()


def load_session_context(
    request: Request,
    db: Session,
    *,
    require_csrf: bool = False,
) -> RequestContext | None:
    """Load first-party context via SECURITY DEFINER session lookup (RLS-safe)."""
    names = SessionCookieNames()
    cookie = request.cookies.get(names.session)
    if not cookie or "." not in cookie:
        return None
    session_id_raw, secret = cookie.split(".", 1)
    try:
        session_id = uuid.UUID(session_id_raw)
    except ValueError:
        return None
    try:
        secret_digest = hash_secret(secret)
    except RuntimeError:
        return None
    row = (
        db.execute(
            text("SELECT * FROM memdot_auth_load_session(:session_id, :secret_hash)"),
            {"session_id": str(session_id), "secret_hash": secret_digest},
        )
        .mappings()
        .first()
    )
    if row is None:
        return None
    if not is_session_active(
        expires_at=row["expires_at"],
        idle_expires_at=row["idle_expires_at"],
        revoked_at=row["revoked_at"],
    ):
        return None
    if require_csrf:
        csrf_header = request.headers.get("X-CSRF-Token", "")
        if not csrf_header or not verify_csrf_token(csrf_header, row["csrf_token_hash"]):
            return None
    return RequestContext(
        account_id=row["account_id"],
        actor_id=row["actor_id"],
        user_id=row["user_id"],
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=correlation_id_for_request(request),
        session_id=row["id"],
        last_auth_at=row["last_auth_at"],
    )
