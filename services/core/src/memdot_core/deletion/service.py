"""Deletion tombstone truth and restore-replay helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from memdot_domain.ids import new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import DeletionTombstone
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext


def is_tombstoned(
    db: Session,
    *,
    account_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
) -> bool:
    row = db.execute(
        select(DeletionTombstone.id).where(
            DeletionTombstone.account_id == account_id,
            DeletionTombstone.entity_type == entity_type,
            DeletionTombstone.entity_id == entity_id,
        )
    ).scalar_one_or_none()
    return row is not None


def list_tombstones(db: Session, *, account_id: uuid.UUID) -> list[DeletionTombstone]:
    return list(
        db.execute(
            select(DeletionTombstone).where(DeletionTombstone.account_id == account_id)
        ).scalars()
    )


def create_tombstone(
    db: Session,
    ctx: RequestContext,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    space_id: uuid.UUID | None = None,
    restore_key: str | None = None,
) -> uuid.UUID:
    tombstone_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        existing = db.execute(
            select(DeletionTombstone).where(
                DeletionTombstone.account_id == ctx.account_id,
                DeletionTombstone.entity_type == entity_type,
                DeletionTombstone.entity_id == entity_id,
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing.id
        db.add(
            DeletionTombstone(
                id=tombstone_id,
                account_id=ctx.account_id,
                entity_type=entity_type,
                entity_id=entity_id,
                space_id=space_id,
                restore_key=restore_key,
                tombstoned_at=datetime.now(UTC),
            )
        )
    return tombstone_id


def replay_tombstones_after_restore(
    db: Session,
    *,
    account_id: uuid.UUID,
    tombstones: list[DeletionTombstone] | None = None,
) -> int:
    """Reapply tombstones after restore before serving traffic."""
    rows = tombstones if tombstones is not None else list_tombstones(db, account_id=account_id)
    applied = 0
    for row in rows:
        existing = db.execute(
            select(DeletionTombstone.id).where(
                DeletionTombstone.account_id == account_id,
                DeletionTombstone.entity_type == row.entity_type,
                DeletionTombstone.entity_id == row.entity_id,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                DeletionTombstone(
                    id=new_uuid7(),
                    account_id=account_id,
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    space_id=row.space_id,
                    restore_key=row.restore_key,
                    tombstoned_at=row.tombstoned_at,
                )
            )
            applied += 1
    return applied
