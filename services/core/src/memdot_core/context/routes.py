"""Context compile API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.context import service as context_service
from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/context", tags=["context"])


class CompileContextBody(BaseModel):
    query: str = Field(min_length=1, max_length=4096)
    purpose: str | None = None
    max_tokens: int = Field(default=4096, ge=256, le=32768)
    max_items: int = Field(default=32, ge=1, le=128)


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("/compile", response_model=None)
def compile_context(
    body: CompileContextBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = context_service.compile_context_for_request(
            db,
            resolved,
            query=body.query,
            purpose=body.purpose,
            max_tokens=body.max_tokens,
            max_items=body.max_items,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**result, "correlationId": str(resolved.correlation_id)}
