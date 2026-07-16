"""Idempotency-key validation, fingerprinting, and replay (TRD-API-002)."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from typing import Any

from fastapi import Request
from memdot_domain.ids import new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import IdempotencyRecord
from memdot_core.errors import ErrorCode, problem_response


@dataclass(frozen=True)
class IdempotencyDecision:
    replay: bool
    conflict: bool
    record_id: uuid.UUID
    response_status: int | None = None
    response_body: dict[str, Any] | None = None


def fingerprint_request(*, method: str, path: str, body: bytes) -> str:
    canonical = f"{method.upper()}:{path}:{body.decode('utf-8', errors='replace')}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def idempotency_key_from_request(request: Request) -> str | None:
    raw = request.headers.get("Idempotency-Key", "").strip()
    if not raw:
        return None
    if len(raw) > 256:
        return None
    return raw


def begin_idempotency(
    db: Session,
    *,
    account_id: uuid.UUID,
    route: str,
    idempotency_key: str,
    fingerprint: str,
) -> IdempotencyDecision:
    existing = db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.account_id == account_id,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.fingerprint_sha256 != fingerprint:
            return IdempotencyDecision(
                replay=False, conflict=True, record_id=existing.id, response_status=409
            )
        body = existing.response_body if isinstance(existing.response_body, dict) else None
        return IdempotencyDecision(
            replay=True,
            conflict=False,
            record_id=existing.id,
            response_status=existing.response_status,
            response_body=body,
        )
    record_id = new_uuid7()
    db.add(
        IdempotencyRecord(
            id=record_id,
            account_id=account_id,
            idempotency_key=idempotency_key,
            fingerprint_sha256=fingerprint,
            response_status=0,
            route=route,
        )
    )
    db.flush()
    return IdempotencyDecision(replay=False, conflict=False, record_id=record_id)


def complete_idempotency(
    db: Session,
    *,
    record_id: uuid.UUID,
    account_id: uuid.UUID,
    response_status: int,
    response_body: dict[str, Any],
) -> None:
    row = db.execute(
        select(IdempotencyRecord).where(
            IdempotencyRecord.id == record_id,
            IdempotencyRecord.account_id == account_id,
        )
    ).scalar_one_or_none()
    if row is None:
        return
    row.response_status = response_status
    row.response_body = response_body
    db.flush()


def idempotency_conflict_response(*, correlation_id: uuid.UUID | None = None):
    return problem_response(
        status=409,
        code=ErrorCode.IDEMPOTENCY_CONFLICT,
        detail="Idempotency key was reused with a different request fingerprint.",
        correlation_id=correlation_id,
    )
