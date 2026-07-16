"""Document API routes."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context
from memdot_core.errors import ErrorCode, problem_response, safe_not_found
from memdot_core.idempotency import (
    begin_idempotency,
    complete_idempotency,
    fingerprint_request,
    idempotency_conflict_response,
    idempotency_key_from_request,
)
from memdot_core.policy import GLOBAL_RATE_LIMITER, rate_limited_response
from memdot_core.request_context import RequestContext
from memdot_core.documents import service as document_service

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class CreateDocumentBody(BaseModel):
    space_id: uuid.UUID
    title: str = Field(min_length=1, max_length=512)
    document: dict[str, Any] | None = None


class SaveRevisionBody(BaseModel):
    base_revision_id: uuid.UUID | None = None
    document: dict[str, Any]


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("", response_model=None)
def create_document(
    body: CreateDocumentBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    if body.document is not None:
        try:
            document_service.validate_or_raise(body.document)
        except ValueError:
            return problem_response(
                status=422,
                code=ErrorCode.VALIDATION_ERROR,
                detail="Document body is invalid.",
                correlation_id=resolved.correlation_id,
            )
    try:
        created = document_service.create_document(
            db,
            resolved,
            space_id=body.space_id,
            title=body.title,
            document_body=body.document,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 201
    return {
        "documentId": str(created.document_id),
        "revisionId": str(created.revision_id),
        "spaceId": str(created.space_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/{document_id}/revisions", response_model=None)
def save_revision(
    document_id: uuid.UUID,
    body: SaveRevisionBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    idem_key = idempotency_key_from_request(request)
    decision = None
    if idem_key:
        body_bytes = body.model_dump_json().encode("utf-8")
        decision = begin_idempotency(
            db,
            account_id=resolved.account_id,
            route=f"POST /api/v1/documents/{document_id}/revisions",
            idempotency_key=idem_key,
            fingerprint=fingerprint_request(
                method="POST", path=str(request.url.path), body=body_bytes
            ),
        )
        if decision.conflict:
            return idempotency_conflict_response(correlation_id=resolved.correlation_id)
        if decision.replay and decision.response_body is not None:
            response.status_code = decision.response_status or 200
            return decision.response_body

    try:
        document_service.validate_or_raise(body.document)
    except ValueError:
        return problem_response(
            status=422,
            code=ErrorCode.VALIDATION_ERROR,
            detail="Document body is invalid.",
            correlation_id=resolved.correlation_id,
        )

    try:
        saved = document_service.save_revision(
            db,
            resolved,
            document_id=document_id,
            base_revision_id=body.base_revision_id,
            document_body=body.document,
        )
    except document_service.StaleBaseRevisionError as exc:
        conflict_body = {
            "type": "about:memdot/problems/conflict",
            "title": "Conflict",
            "status": 409,
            "code": ErrorCode.CONFLICT.value,
            "detail": "Base revision is stale.",
            "correlationId": str(resolved.correlation_id),
            "currentRevisionId": str(exc.current_revision_id)
            if exc.current_revision_id
            else None,
        }
        return JSONResponse(
            status_code=409,
            content=conflict_body,
            media_type="application/problem+json",
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)

    payload = {
        "documentId": str(saved.document_id),
        "revisionId": str(saved.revision_id),
        "contentSha256": saved.content_sha256,
        "correlationId": str(resolved.correlation_id),
    }
    if idem_key and decision is not None:
        complete_idempotency(
            db,
            record_id=decision.record_id,
            account_id=resolved.account_id,
            response_status=200,
            response_body=payload,
        )
    return payload


@router.get("/{document_id}", response_model=None)
def get_document(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    revision = document_service.get_current_revision(db, resolved, document_id=document_id)
    if revision is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        **document_service.revision_payload(revision),
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/{document_id}/revisions", response_model=None)
def list_revisions(
    document_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    revisions = document_service.list_revisions(db, resolved, document_id=document_id)
    if not revisions:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "items": [document_service.revision_payload(row) for row in revisions],
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/{document_id}/revisions/{revision_id}", response_model=None)
def get_revision(
    document_id: uuid.UUID,
    revision_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    revision = document_service.get_revision(
        db, resolved, document_id=document_id, revision_id=revision_id
    )
    if revision is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        **document_service.revision_payload(revision),
        "correlationId": str(resolved.correlation_id),
    }
