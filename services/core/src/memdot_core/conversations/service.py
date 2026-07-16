"""Conversation capture and lifecycle service."""

from __future__ import annotations

import uuid
from typing import Any

from memdot_domain.ids import new_uuid7
from memdot_domain.mcp import ConversationCompleteness, capture_origin_for_client
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.deletion import service as deletion_service
from memdot_core.db.models.ledger import Conversation, ConversationTurn
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext


def create_conversation(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    source_client: str = "native",
    completeness: str = ConversationCompleteness.COMPLETE.value,
) -> dict[str, Any]:
    conversation_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            Conversation(
                id=conversation_id,
                account_id=ctx.account_id,
                space_id=space_id,
                source_client=source_client,
                completeness=completeness,
            )
        )
    return {
        "conversationId": str(conversation_id),
        "spaceId": str(space_id),
        "sourceClient": source_client,
        "completeness": completeness,
        "captureOrigin": capture_origin_for_client(source_client).value,
    }


def list_conversations(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    query = select(Conversation).where(Conversation.account_id == ctx.account_id)
    if space_id:
        query = query.where(Conversation.space_id == space_id)
    rows = db.execute(query.order_by(Conversation.created_at.desc())).scalars().all()
    visible: list[dict[str, Any]] = []
    for row in rows:
        if deletion_service.is_tombstoned(
            db,
            account_id=ctx.account_id,
            entity_type="conversation",
            entity_id=row.id,
        ):
            continue
        visible.append(
            {
                "conversationId": str(row.id),
                "spaceId": str(row.space_id),
                "sourceClient": row.source_client,
                "completeness": row.completeness,
                "captureOrigin": capture_origin_for_client(row.source_client).value,
                "createdAt": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return visible


def get_conversation(
    db: Session,
    ctx: RequestContext,
    *,
    conversation_id: uuid.UUID,
) -> dict[str, Any] | None:
    if deletion_service.is_tombstoned(
        db,
        account_id=ctx.account_id,
        entity_type="conversation",
        entity_id=conversation_id,
    ):
        return None
    row = db.execute(
        select(Conversation).where(
            Conversation.account_id == ctx.account_id,
            Conversation.id == conversation_id,
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    turns = db.execute(
        select(ConversationTurn)
        .where(
            ConversationTurn.account_id == ctx.account_id,
            ConversationTurn.conversation_id == conversation_id,
        )
        .order_by(ConversationTurn.turn_index.asc())
    ).scalars().all()
    return {
        "conversationId": str(row.id),
        "spaceId": str(row.space_id),
        "sourceClient": row.source_client,
        "completeness": row.completeness,
        "captureOrigin": capture_origin_for_client(row.source_client).value,
        "turns": [
            {
                "turnId": str(turn.id),
                "role": turn.role,
                "turnIndex": turn.turn_index,
            }
            for turn in turns
        ],
    }


def append_turn(
    db: Session,
    ctx: RequestContext,
    *,
    conversation_id: uuid.UUID,
    role: str,
    auto_native: bool = True,
) -> dict[str, Any] | None:
    if deletion_service.is_tombstoned(
        db,
        account_id=ctx.account_id,
        entity_type="conversation",
        entity_id=conversation_id,
    ):
        return None
    conversation = db.execute(
        select(Conversation).where(
            Conversation.account_id == ctx.account_id,
            Conversation.id == conversation_id,
        )
    ).scalar_one_or_none()
    if conversation is None:
        return None

    last_turn = db.execute(
        select(ConversationTurn.turn_index)
        .where(
            ConversationTurn.account_id == ctx.account_id,
            ConversationTurn.conversation_id == conversation_id,
        )
        .order_by(ConversationTurn.turn_index.desc())
    ).scalar_one_or_none()
    turn_index = (last_turn or -1) + 1
    turn_id = new_uuid7()

    with tenant_scope(db, ctx.tenant()):
        db.add(
            ConversationTurn(
                id=turn_id,
                account_id=ctx.account_id,
                space_id=conversation.space_id,
                conversation_id=conversation_id,
                role=role,
                turn_index=turn_index,
            )
        )
        if auto_native and conversation.source_client in {"native", "memdot", "first_party"}:
            conversation.completeness = ConversationCompleteness.COMPLETE.value

    return {
        "turnId": str(turn_id),
        "turnIndex": turn_index,
        "role": role,
        "autoNative": auto_native,
    }


def delete_conversation(
    db: Session,
    ctx: RequestContext,
    *,
    conversation_id: uuid.UUID,
) -> bool:
    row = db.execute(
        select(Conversation).where(
            Conversation.account_id == ctx.account_id,
            Conversation.id == conversation_id,
        )
    ).scalar_one_or_none()
    if row is None:
        return False
    deletion_service.create_tombstone(
        db,
        ctx,
        entity_type="conversation",
        entity_id=conversation_id,
        space_id=row.space_id,
    )
    return True
