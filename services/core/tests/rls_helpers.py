"""RLS test helpers."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from memdot_core.db.tenant import TenantContext, apply_tenant_context, reset_tenant_context
from sqlalchemy import text
from sqlalchemy.orm import Session


@contextmanager
def runtime_tenant_scope(session: Session, ctx: TenantContext) -> Iterator[None]:
    """Apply tenant context under the memdot_core runtime role."""
    session.execute(text("SET ROLE memdot_core"))
    reset_tenant_context(session)
    apply_tenant_context(session, ctx)
    try:
        yield
    finally:
        try:
            reset_tenant_context(session)
        except Exception:
            session.rollback()
            reset_tenant_context(session)
        session.execute(text("RESET ROLE"))
