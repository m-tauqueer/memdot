"""Export API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import safe_not_found
from memdot_core.export import service as export_service
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext

router = APIRouter(prefix="/api/v1/export", tags=["export"])


class ExportBody(BaseModel):
    space_id: uuid.UUID | None = None


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("/account", response_model=None)
def export_account(
    body: ExportBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        manifest = export_service.create_export(db, resolved, space_id=body.space_id)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {**manifest, "correlationId": str(resolved.correlation_id)}
