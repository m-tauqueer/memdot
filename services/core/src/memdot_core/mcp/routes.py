"""MCP Core API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_settings
from memdot_core.errors import safe_not_found
from memdot_core.external_context import load_mcp_context
from memdot_core.mcp import service as mcp_service
from memdot_core.policy import (
    GLOBAL_OVERLOAD_BREAKER,
    GLOBAL_RATE_LIMITER,
    overload_reject_response,
    rate_limited_response,
)
from memdot_core.request_context import RequestContext
from memdot_core.settings import CoreSettings

router = APIRouter(prefix="/api/v1/mcp", tags=["mcp"])


class SearchBody(BaseModel):
    query: str = Field(min_length=1, max_length=2048)


class FetchBody(BaseModel):
    id: str = Field(min_length=1, max_length=512)


class PrepareContextBody(BaseModel):
    query: str = Field(min_length=1, max_length=4096)
    purpose: str | None = None
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    max_items: int = Field(default=32, ge=1, le=128)


class ProposeMemoryBody(BaseModel):
    space_id: uuid.UUID
    assertion_text: str = Field(min_length=1)
    title: str = Field(default="MCP proposal", max_length=512)
    target_type: str = Field(default="memory", max_length=64)
    target_id: uuid.UUID | None = None


class RecordInteractionBody(BaseModel):
    space_id: uuid.UUID
    client_conversation_id: str = Field(min_length=1, max_length=128)
    role: str = Field(min_length=1, max_length=32)
    content: str = Field(min_length=1)
    completeness: str = Field(min_length=1, max_length=32)
    context_receipt_id: uuid.UUID | None = None


def _require_mcp_ctx(
    request: Request,
    db: Session,
    *,
    purpose: str | None = None,
) -> RequestContext | Response:
    if not GLOBAL_OVERLOAD_BREAKER.try_acquire():
        return overload_reject_response()
    ctx = load_mcp_context(request, db)
    if ctx is None:
        GLOBAL_OVERLOAD_BREAKER.release()
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        GLOBAL_OVERLOAD_BREAKER.release()
        return rate_limited_response(correlation_id=ctx.correlation_id)
    if purpose and ctx.purpose.value != purpose:
        GLOBAL_OVERLOAD_BREAKER.release()
        return safe_not_found(correlation_id=ctx.correlation_id)
    return ctx


def _release_overload() -> None:
    GLOBAL_OVERLOAD_BREAKER.release()


@router.post("/search", response_model=None)
def mcp_search(
    body: SearchBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[CoreSettings, Depends(get_settings)],
) -> dict[str, Any] | Response:
    resolved = _require_mcp_ctx(request, db, purpose="external_read")
    if isinstance(resolved, Response):
        return resolved
    try:
        result = mcp_service.search(
            db,
            resolved,
            query=body.query,
            public_base_url=settings.public_url,
        )
    except Exception:
        _release_overload()
        return safe_not_found(correlation_id=resolved.correlation_id)
    _release_overload()
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.post("/fetch", response_model=None)
def mcp_fetch(
    body: FetchBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[CoreSettings, Depends(get_settings)],
) -> dict[str, Any] | Response:
    resolved = _require_mcp_ctx(request, db, purpose="external_read")
    if isinstance(resolved, Response):
        return resolved
    try:
        result = mcp_service.fetch(
            db,
            resolved,
            mcp_id=body.id,
            public_base_url=settings.public_url,
        )
    except Exception:
        _release_overload()
        return safe_not_found(correlation_id=resolved.correlation_id)
    _release_overload()
    if result is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.post("/prepare-context", response_model=None)
def mcp_prepare_context(
    body: PrepareContextBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, Any] | Response:
    resolved = _require_mcp_ctx(request, db, purpose="external_read")
    if isinstance(resolved, Response):
        return resolved
    try:
        result = mcp_service.prepare_context(
            db,
            resolved,
            query=body.query,
            purpose=body.purpose,
            max_tokens=body.max_tokens,
            max_items=body.max_items,
        )
    except Exception:
        _release_overload()
        return safe_not_found(correlation_id=resolved.correlation_id)
    _release_overload()
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.post("/propose-memory", response_model=None)
def mcp_propose_memory(
    body: ProposeMemoryBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, Any] | Response:
    resolved = _require_mcp_ctx(request, db, purpose="external_propose")
    if isinstance(resolved, Response):
        return resolved
    try:
        result = mcp_service.propose_memory(
            db,
            resolved,
            space_id=body.space_id,
            assertion_text=body.assertion_text,
            title=body.title,
            target_type=body.target_type,
            target_id=body.target_id,
        )
    except Exception:
        _release_overload()
        return safe_not_found(correlation_id=resolved.correlation_id)
    _release_overload()
    response.status_code = 201
    return {**result, "correlationId": str(resolved.correlation_id)}


@router.post("/record-interaction", response_model=None)
def mcp_record_interaction(
    body: RecordInteractionBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> dict[str, Any] | Response:
    resolved = _require_mcp_ctx(request, db, purpose="external_interaction")
    if isinstance(resolved, Response):
        return resolved
    try:
        result = mcp_service.record_interaction(
            db,
            resolved,
            space_id=body.space_id,
            client_conversation_id=body.client_conversation_id,
            role=body.role,
            content=body.content,
            completeness=body.completeness,
            context_receipt_id=body.context_receipt_id,
        )
    except Exception:
        _release_overload()
        return safe_not_found(correlation_id=resolved.correlation_id)
    _release_overload()
    response.status_code = 201
    return {**result, "correlationId": str(resolved.correlation_id)}
