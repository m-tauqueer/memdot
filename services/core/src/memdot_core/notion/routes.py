"""Notion connector API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.notion import service as notion_service
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/notion", tags=["notion"])


class SelectPagesBody(BaseModel):
    connection_id: uuid.UUID
    space_id: uuid.UUID
    notion_page_ids: list[str] = Field(min_length=1)


class SyncBindingBody(BaseModel):
    fixture_content: str | None = None


class ResolveConflictBody(BaseModel):
    resolution: str = Field(min_length=1, max_length=32)


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("/connect", response_model=None)
def connect(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = notion_service.connect_stub(db, resolved)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.get("/connections/{connection_id}/pages", response_model=None)
def list_pages(
    connection_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    pages = notion_service.list_pages(db, resolved, connection_id=connection_id)
    return {"pages": pages, "correlationId": str(resolved.correlation_id)}


@router.post("/pages/select", response_model=None)
def select_pages(
    body: SelectPagesBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        bindings = notion_service.select_pages(
            db,
            resolved,
            connection_id=body.connection_id,
            space_id=body.space_id,
            notion_page_ids=body.notion_page_ids,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {"bindings": bindings, "correlationId": str(resolved.correlation_id)}


@router.post("/bindings/{binding_id}/sync", response_model=None)
def sync_binding(
    binding_id: uuid.UUID,
    body: SyncBindingBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    result = notion_service.sync_binding_snapshot(
        db,
        resolved,
        binding_id=binding_id,
        fixture_content=body.fixture_content,
    )
    if result is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.post("/bindings/{binding_id}/resolve", response_model=None)
def resolve_conflict(
    binding_id: uuid.UUID,
    body: ResolveConflictBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = notion_service.resolve_conflict(
            db,
            resolved,
            binding_id=binding_id,
            resolution=body.resolution,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    if result is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**result, "correlationId": str(resolved.correlation_id)}
