"""Source API routes (Wave 4)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from memdot_domain.ports.object_storage import ObjectStoragePort
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from memdot_core.deps import get_db_session, get_request_context, get_settings, get_storage
from memdot_core.errors import (
    ErrorCode,
    problem_response,
    safe_not_found,
)
from memdot_core.idempotency import (
    begin_idempotency,
    complete_idempotency,
    fingerprint_request,
    idempotency_conflict_response,
    idempotency_key_from_request,
)
from memdot_core.policy import (
    GLOBAL_RATE_LIMITER,
    payload_too_large_response,
    rate_limited_response,
)
from memdot_core.request_context import RequestContext
from memdot_core.settings import CoreSettings
from memdot_core.sources import service as source_service

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


class CreateSourceBody(BaseModel):
    space_id: uuid.UUID
    title: str = Field(min_length=1, max_length=512)


class UploadIntentBody(BaseModel):
    filename: str = Field(min_length=1, max_length=256)
    content_type: str = Field(min_length=1, max_length=128)
    byte_count: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)


class CompleteUploadBody(BaseModel):
    upload_id: uuid.UUID


class ReprocessBody(BaseModel):
    revision_id: uuid.UUID
    shadow: bool = False


def _require_ctx(ctx: RequestContext | None, request: Request) -> RequestContext | Response:
    if ctx is None:
        return safe_not_found(correlation_id=uuid.uuid4())
    if not GLOBAL_RATE_LIMITER.allow(str(ctx.account_id)):
        return rate_limited_response(correlation_id=ctx.correlation_id)
    return ctx


@router.post("", response_model=None)
def create_source(
    body: CreateSourceBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    settings: Annotated[CoreSettings, Depends(get_settings)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    del settings
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
            route="POST /api/v1/sources",
            idempotency_key=idem_key,
            fingerprint=fingerprint_request(
                method="POST", path=str(request.url.path), body=body_bytes
            ),
        )
        if decision.conflict:
            return idempotency_conflict_response(correlation_id=resolved.correlation_id)
        if decision.replay and decision.response_body is not None:
            response.status_code = decision.response_status or 201
            return decision.response_body
        if decision.replay:
            return safe_not_found(correlation_id=resolved.correlation_id)

    try:
        created = source_service.create_source(
            db,
            resolved,
            space_id=body.space_id,
            title=body.title,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)

    payload = {
        "sourceId": str(created.source_id),
        "spaceId": str(created.space_id),
        "correlationId": str(resolved.correlation_id),
    }
    if idem_key and decision is not None:
        complete_idempotency(
            db,
            record_id=decision.record_id,
            account_id=resolved.account_id,
            response_status=201,
            response_body=payload,
        )
    response.status_code = 201
    response.headers["X-Correlation-Id"] = str(resolved.correlation_id)
    return payload


@router.post("/{source_id}/uploads", response_model=None)
def create_upload_intent(
    source_id: uuid.UUID,
    body: UploadIntentBody,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    storage: Annotated[ObjectStoragePort, Depends(get_storage)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    if body.byte_count > source_service.INGESTION_LIMITS.max_object_bytes:
        return payload_too_large_response(correlation_id=resolved.correlation_id)
    try:
        intent = source_service.begin_upload(
            db,
            resolved,
            storage,
            source_id=source_id,
            filename=body.filename,
            content_type=body.content_type,
            byte_count=body.byte_count,
            sha256=body.sha256,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "uploadId": str(intent.upload_id),
        "uploadUrl": intent.upload_url,
        "objectKey": intent.object_key,
        "expiresAt": intent.expires_at.isoformat(),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/{source_id}/uploads/complete", response_model=None)
def complete_upload(
    source_id: uuid.UUID,
    body: CompleteUploadBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    storage: Annotated[ObjectStoragePort, Depends(get_storage)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        result = source_service.complete_upload(
            db,
            resolved,
            storage,
            source_id=source_id,
            upload_id=body.upload_id,
        )
    except ValueError as exc:
        if str(exc) in {"upload_verification_failed", "upload_checksum_mismatch"}:
            return problem_response(
                status=422,
                code=ErrorCode.UPLOAD_INVALID,
                detail="Upload verification failed.",
                correlation_id=resolved.correlation_id,
            )
        return safe_not_found(correlation_id=resolved.correlation_id)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 202
    return {
        "revisionId": str(result.revision_id),
        "snapshotSha256": result.snapshot_sha256,
        "jobId": str(result.job.job_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/{source_id}/status", response_model=None)
def get_processing_status(
    source_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        status = source_service.processing_status(db, resolved, source_id=source_id)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {**status, "correlationId": str(resolved.correlation_id)}


@router.post("/{source_id}/cancel", response_model=None)
def cancel_source_processing(
    source_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        source_service.cancel_processing(db, resolved, source_id=source_id)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "sourceId": str(source_id),
        "processingStatus": "cancelled",
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/{source_id}/retry", response_model=None)
def retry_source_processing(
    source_id: uuid.UUID,
    body: ReprocessBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        job = source_service.retry_processing(
            db,
            resolved,
            source_id=source_id,
            revision_id=body.revision_id,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 202
    return {
        "jobId": str(job.job_id),
        "revisionId": str(body.revision_id),
        "correlationId": str(resolved.correlation_id),
    }


@router.post("/{source_id}/reprocess", response_model=None)
def reprocess_source_revision(
    source_id: uuid.UUID,
    body: ReprocessBody,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        job = source_service.reprocess_revision(
            db,
            resolved,
            source_id=source_id,
            revision_id=body.revision_id,
            shadow=body.shadow,
        )
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    response.status_code = 202
    return {
        "jobId": str(job.job_id),
        "revisionId": str(body.revision_id),
        "shadow": body.shadow,
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/{source_id}/versions", response_model=None)
def list_versions(
    source_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    try:
        revisions = source_service.list_revisions(db, resolved, source_id=source_id)
    except Exception:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        "items": [source_service.citation_for_revision(revision) for revision in revisions],
        "correlationId": str(resolved.correlation_id),
    }


@router.get("/{source_id}/versions/{revision_id}", response_model=None)
def get_version(
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
    ctx: Annotated[RequestContext | None, Depends(get_request_context)],
) -> dict[str, Any] | Response:
    resolved = _require_ctx(ctx, request)
    if isinstance(resolved, Response):
        return resolved
    revisions = source_service.list_revisions(db, resolved, source_id=source_id)
    match = next((row for row in revisions if row.id == revision_id), None)
    if match is None:
        return safe_not_found(correlation_id=resolved.correlation_id)
    return {
        **source_service.citation_for_revision(match),
        "correlationId": str(resolved.correlation_id),
    }
