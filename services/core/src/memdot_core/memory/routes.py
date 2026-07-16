"""Memory API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.memory import service as memory_service
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class CreateMemoryItemBody(BaseModel):
    space_id: uuid.UUID
    title: str = Field(min_length=1, max_length=512)
    assertion_text: str = Field(min_length=1)


class CreateProposalBody(BaseModel):
    space_id: uuid.UUID
    target_type: str = Field(min_length=1, max_length=64)
    target_id: uuid.UUID
    patch_json: dict[str, Any] = Field(default_factory=dict)
    base_revision_id: uuid.UUID | None = None


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("/items", response_model=None)
def create_memory_item(
    body: CreateMemoryItemBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        created = memory_service.create_memory_item(
            db,
            resolved,
            space_id=body.space_id,
            title=body.title,
            assertion_text=body.assertion_text,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "memoryItemId": str(created.memory_item_id),
        "spaceId": str(created.space_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/proposals", response_model=None)
def create_proposal(
    body: CreateProposalBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        created = memory_service.create_proposal(
            db,
            resolved,
            space_id=body.space_id,
            target_type=body.target_type,
            target_id=body.target_id,
            patch_json=body.patch_json,
            base_revision_id=body.base_revision_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "proposalId": str(created.proposal_id),
        "status": created.status,
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/proposals/{proposal_id}/approve", response_model=None)
def approve_proposal(
    proposal_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = memory_service.resolve_proposal(
            db, resolved, proposal_id=proposal_id, approve=True
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "proposalId": str(result.proposal_id),
        "status": result.status,
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/proposals/{proposal_id}/reject", response_model=None)
def reject_proposal(
    proposal_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = memory_service.resolve_proposal(
            db, resolved, proposal_id=proposal_id, approve=False
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "proposalId": str(result.proposal_id),
        "status": result.status,
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/items/{memory_item_id}", response_model=None)
def get_memory_item(
    memory_item_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    payload = memory_service.get_memory_item(db, resolved, memory_item_id=memory_item_id)
    if payload is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**payload, "correlationId": str(resolved.correlation_id)}
