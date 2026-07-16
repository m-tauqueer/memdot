"""Stable error-code registry and problem detail helpers."""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorCode(StrEnum):
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    VALIDATION_ERROR = "validation_error"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    RATE_LIMITED = "rate_limited"
    RECENT_AUTH_REQUIRED = "recent_auth_required"
    CSRF_INVALID = "csrf_invalid"
    CURSOR_INVALID = "cursor_invalid"
    UPLOAD_INVALID = "upload_invalid"
    PROCESSING_FAILED = "processing_failed"
    CONCURRENCY_LIMIT = "concurrency_limit"


class FieldError(BaseModel):
    pointer: str
    code: ErrorCode
    detail: str | None = None


class ProblemDetail(BaseModel):
    type: str
    title: str
    status: int
    code: ErrorCode
    detail: str | None = None
    instance: str | None = None
    correlation_id: uuid.UUID | None = None
    errors: list[FieldError] | None = None


def problem_response(
    *,
    status: int,
    code: ErrorCode,
    title: str | None = None,
    detail: str | None = None,
    instance: str | None = None,
    correlation_id: uuid.UUID | None = None,
    errors: list[FieldError] | None = None,
) -> JSONResponse:
    body = ProblemDetail(
        type=f"about:memdot/problems/{code.value}",
        title=title or code.value.replace("_", " ").title(),
        status=status,
        code=code,
        detail=detail,
        instance=instance,
        correlation_id=correlation_id,
        errors=errors,
    )
    return JSONResponse(
        status_code=status,
        content=body.model_dump(mode="json", exclude_none=True),
        media_type="application/problem+json",
    )


def correlation_id_from_request(request: Request) -> uuid.UUID | None:
    raw = request.headers.get("X-Correlation-Id") or request.headers.get("X-Request-Id")
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def safe_not_found(*, correlation_id: uuid.UUID | None = None) -> JSONResponse:
    return problem_response(
        status=404,
        code=ErrorCode.NOT_FOUND,
        detail="The requested resource was not found.",
        correlation_id=correlation_id,
    )


def safe_unauthorized(*, correlation_id: uuid.UUID | None = None) -> JSONResponse:
    return problem_response(
        status=401,
        code=ErrorCode.UNAUTHORIZED,
        detail="Authentication is required.",
        correlation_id=correlation_id,
    )


def validation_problem(
    *,
    errors: list[FieldError],
    correlation_id: uuid.UUID | None = None,
) -> JSONResponse:
    return problem_response(
        status=422,
        code=ErrorCode.VALIDATION_ERROR,
        detail="One or more fields are invalid.",
        correlation_id=correlation_id,
        errors=errors,
    )


def http_exception_detail(code: ErrorCode, detail: str | None = None) -> dict[str, Any]:
    return {"code": code.value, "detail": detail}
