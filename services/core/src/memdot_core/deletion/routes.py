"""Deletion tombstone API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deletion import service as deletion_service
from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/deletion", tags=["deletion"])


class CreateTombstoneBody(BaseModel):
    entity_type: str = Field(min_length=1, max_length=64)
    entity_id: uuid.UUID
    space_id: uuid.UUID | None = None
    restore_key: str | None = Field(default=None, max_length=128)


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("/tombstones", response_model=None)
def create_tombstone(
    body: CreateTombstoneBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        tombstone_id = deletion_service.create_tombstone(
            db,
            resolved,
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            space_id=body.space_id,
            restore_key=body.restore_key,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "tombstoneId": str(tombstone_id),
        "entityType": body.entity_type,
        "entityId": str(body.entity_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/restore-replay", response_model=None)
def restore_replay(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    applied = deletion_service.replay_tombstones_after_restore(
        db, account_id=resolved.account_id
    )
    return {"applied": applied, "correlationId": str(resolved.correlation_id)}
