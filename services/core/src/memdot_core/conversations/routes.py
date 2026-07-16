"""Conversation API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.conversations import service as conversation_service
from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class CreateConversationBody(BaseModel):
    space_id: uuid.UUID
    source_client: str = Field(default="native", max_length=64)
    completeness: str = Field(default="complete", max_length=32)


class AppendTurnBody(BaseModel):
    role: str = Field(min_length=1, max_length=32)
    content: str | None = None
    client_turn_id: str | None = Field(default=None, max_length=128)
    parent_turn_id: uuid.UUID | None = None
    context_receipt_id: uuid.UUID | None = None
    auto_native: bool = True


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("", response_model=None)
def create_conversation(
    body: CreateConversationBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        created = conversation_service.create_conversation(
            db,
            resolved,
            space_id=body.space_id,
            source_client=body.source_client,
            completeness=body.completeness,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {**created, "correlationId": str(resolved.correlation_id)}


@router.get("", response_model=None)
def list_conversations(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
    space_id: uuid.UUID | None = None,
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    items = conversation_service.list_conversations(db, resolved, space_id=space_id)
    return {"items": items, "correlationId": str(resolved.correlation_id)}


@router.get("/{conversation_id}", response_model=None)
def get_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    payload = conversation_service.get_conversation(db, resolved, conversation_id=conversation_id)
    if payload is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**payload, "correlationId": str(resolved.correlation_id)}


@router.post("/{conversation_id}/turns", response_model=None)
def append_turn(
    conversation_id: uuid.UUID,
    body: AppendTurnBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    result = conversation_service.append_turn(
        db,
        resolved,
        conversation_id=conversation_id,
        role=body.role,
        content=body.content,
        client_turn_id=body.client_turn_id,
        parent_turn_id=body.parent_turn_id,
        context_receipt_id=body.context_receipt_id,
        auto_native=body.auto_native,
    )
    if result is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.delete("/{conversation_id}", response_model=None)
def delete_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    deleted = conversation_service.delete_conversation(
        db, resolved, conversation_id=conversation_id
    )
    if not deleted:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {"deleted": True, "correlationId": str(resolved.correlation_id)}
