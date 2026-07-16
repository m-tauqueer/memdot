"""Deletion tombstone truth and restore-replay helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from memdot_domain.ids import new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import DeletionTombstone, DeletionWorkflow, OutboxEvent
from memdot_core.db.tenant import tenant_scope
from memdot_core.jobs.service import payload_sha256
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
    workflow_id = new_uuid7()
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
        # Tombstone-first: write tombstone before workflow progression / outbox.
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
        db.add(
            DeletionWorkflow(
                id=workflow_id,
                account_id=ctx.account_id,
                entity_type=entity_type,
                entity_id=entity_id,
                space_id=space_id,
                state="tombstoned",
                tombstone_id=tombstone_id,
            )
        )
        payload = {
            "workflow_id": str(workflow_id),
            "tombstone_id": str(tombstone_id),
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "state": "tombstoned",
        }
        db.add(
            OutboxEvent(
                id=new_uuid7(),
                account_id=ctx.account_id,
                event_type="deletion.tombstoned",
                payload_sha256=payload_sha256(payload),
                payload=payload,
            )
        )
    return tombstone_id


def replay_tombstones_after_restore(
    db: Session,
    *,
    account_id: uuid.UUID,
    tombstones: list[DeletionTombstone] | None = None,
) -> int:
    """Reapply tombstones after restore before serving traffic (tombstone-first)."""
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
            tombstone_id = new_uuid7()
            db.add(
                DeletionTombstone(
                    id=tombstone_id,
                    account_id=account_id,
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    space_id=row.space_id,
                    restore_key=row.restore_key,
                    tombstoned_at=row.tombstoned_at,
                )
            )
            db.add(
                DeletionWorkflow(
                    id=new_uuid7(),
                    account_id=account_id,
                    entity_type=row.entity_type,
                    entity_id=row.entity_id,
                    space_id=row.space_id,
                    state="tombstoned",
                    tombstone_id=tombstone_id,
                )
            )
            applied += 1
    return applied


def advance_deletion_workflow(
    db: Session,
    ctx: RequestContext,
    *,
    workflow_id: uuid.UUID,
    state: str,
) -> dict[str, object] | None:
    allowed = {
        "accepted",
        "tombstoned",
        "revoking_grants",
        "purging_projections",
        "completed",
        "failed",
        "cancelled",
    }
    if state not in allowed:
        msg = "invalid_deletion_state"
        raise ValueError(msg)
    with tenant_scope(db, ctx.tenant()):
        row = db.execute(
            select(DeletionWorkflow).where(
                DeletionWorkflow.account_id == ctx.account_id,
                DeletionWorkflow.id == workflow_id,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        row.state = state
        row.updated_at = datetime.now(UTC)
        payload = {
            "workflow_id": str(row.id),
            "tombstone_id": str(row.tombstone_id) if row.tombstone_id else None,
            "entity_type": row.entity_type,
            "entity_id": str(row.entity_id),
            "state": state,
        }
        db.add(
            OutboxEvent(
                id=new_uuid7(),
                account_id=ctx.account_id,
                event_type="deletion.workflow_advanced",
                payload_sha256=payload_sha256(payload),
                payload=payload,
            )
        )
    return {"workflowId": str(workflow_id), "state": state}
