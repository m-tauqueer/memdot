"""Protected transaction-scoped tenant context for PostgreSQL RLS (TRD-DATA-004).

Runtime code MUST NOT set app.* GUCs directly. Context is established only through
SECURITY DEFINER ``memdot_begin_tenant_context``, which validates actor membership
or external grant, purpose, and revocation, then seals the transaction GUCs with
an HMAC that RLS policies re-verify via ``memdot_rls_ok``.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass

from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text
from sqlalchemy.orm import Session

# Purposes allowed for the memdot_core runtime role (migration/admin excluded).
RUNTIME_PURPOSES = frozenset(
    {
        RequestPurpose.FIRST_PARTY,
        RequestPurpose.EXTERNAL_READ,
        RequestPurpose.EXTERNAL_PROPOSE,
        RequestPurpose.EXTERNAL_INTERACTION,
        RequestPurpose.WORKER,
    }
)


@dataclass(frozen=True)
class TenantContext:
    account_id: uuid.UUID
    actor_id: uuid.UUID
    purpose: RequestPurpose


def reset_tenant_context(session: Session) -> None:
    """Clear sealed tenant settings (fail-closed default)."""
    session.execute(text("SELECT memdot_clear_tenant_context()"))


def _signing_key() -> bytes:
    value = os.environ.get("CORE_TENANT_CONTEXT_SIGNING_KEY", "")
    if len(value) < 32:
        raise RuntimeError("CORE_TENANT_CONTEXT_SIGNING_KEY must contain at least 32 characters")
    return value.encode("utf-8")


def _context_message(ctx: TenantContext, *, issued_at: int, nonce: str) -> bytes:
    return (f"{ctx.account_id}:{ctx.actor_id}:{ctx.purpose.value}:{issued_at}:{nonce}").encode()


def sign_tenant_context(ctx: TenantContext, *, issued_at: int, nonce: str) -> str:
    return hmac.new(
        _signing_key(),
        _context_message(ctx, issued_at=issued_at, nonce=nonce),
        hashlib.sha256,
    ).hexdigest()


def apply_tenant_context(session: Session, ctx: TenantContext) -> None:
    """Establish protected tenant context via the database validation seam."""
    if ctx.purpose not in RUNTIME_PURPOSES:
        msg = f"unsupported purpose: {ctx.purpose}"
        raise ValueError(msg)
    issued_at = int(time.time())
    nonce = secrets.token_hex(16)
    signature = sign_tenant_context(ctx, issued_at=issued_at, nonce=nonce)
    session.execute(
        text(
            "SELECT memdot_begin_tenant_context("
            ":account_id, :actor_id, :purpose, :issued_at, :nonce, :signature)"
        ),
        {
            "account_id": str(ctx.account_id),
            "actor_id": str(ctx.actor_id),
            "purpose": ctx.purpose.value,
            "issued_at": issued_at,
            "nonce": nonce,
            "signature": signature,
        },
    )


@contextmanager
def tenant_scope(session: Session, ctx: TenantContext) -> Generator[None, None, None]:
    """Apply protected context and flush while sealed; leave seal for caller commit."""
    reset_tenant_context(session)
    apply_tenant_context(session, ctx)
    try:
        yield
        session.flush()
    except Exception:
        session.rollback()
        reset_tenant_context(session)
        raise


def current_account_id(session: Session) -> str | None:
    row = session.execute(text("SELECT current_setting('app.account_id', true)")).scalar()
    if row is None or str(row).strip() == "":
        return None
    return str(row)


def set_current_source_revision(
    session: Session,
    *,
    pointer_id: uuid.UUID,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
    event_id: uuid.UUID,
    payload_sha256: str,
    payload_json: str,
) -> None:
    session.execute(
        text(
            "SELECT memdot_set_current_source_revision("
            ":pointer_id,:account_id,:space_id,:source_id,:revision_id,"
            ":event_id,:payload_sha256,CAST(:payload_json AS jsonb))"
        ),
        {
            "pointer_id": pointer_id,
            "account_id": account_id,
            "space_id": space_id,
            "source_id": source_id,
            "revision_id": revision_id,
            "event_id": event_id,
            "payload_sha256": payload_sha256,
            "payload_json": payload_json,
        },
    )


def set_current_document_revision(
    session: Session,
    *,
    pointer_id: uuid.UUID,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    document_id: uuid.UUID,
    revision_id: uuid.UUID,
    event_id: uuid.UUID,
    payload_sha256: str,
    payload_json: str,
) -> None:
    session.execute(
        text(
            "SELECT memdot_set_current_document_revision("
            ":pointer_id,:account_id,:space_id,:document_id,:revision_id,"
            ":event_id,:payload_sha256,CAST(:payload_json AS jsonb))"
        ),
        {
            "pointer_id": pointer_id,
            "account_id": account_id,
            "space_id": space_id,
            "document_id": document_id,
            "revision_id": revision_id,
            "event_id": event_id,
            "payload_sha256": payload_sha256,
            "payload_json": payload_json,
        },
    )
