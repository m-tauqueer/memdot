"""Transactional outbox and durable job orchestration."""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from memdot_core.db.models.ledger import DurableJob, JobAttempt, OutboxEvent
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext
from memdot_domain.ids import new_uuid7
from memdot_domain.ingestion import JobStatus
from sqlalchemy import select, text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class EnqueuedJob:
    job_id: uuid.UUID
    outbox_event_id: uuid.UUID


def payload_sha256(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def auth_snapshot_from_context(
    ctx: RequestContext,
    *,
    space_id: uuid.UUID | None = None,
    resource_ids: dict[str, str] | None = None,
) -> dict[str, object]:
    from memdot_core.jobs.auth_snapshot import auth_snapshot_from_context as signed_snapshot

    return signed_snapshot(ctx, space_id=space_id, resource_ids=resource_ids)


def enqueue_job_with_outbox(
    db: Session,
    ctx: RequestContext,
    *,
    job_type: str,
    space_id: uuid.UUID,
    payload: dict[str, Any],
    event_type: str,
    idempotency_key: str | None = None,
) -> EnqueuedJob:
    digest = payload_sha256(payload)
    if idempotency_key:
        existing = db.execute(
            select(DurableJob).where(
                DurableJob.account_id == ctx.account_id,
                DurableJob.idempotency_key == idempotency_key,
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing_payload = dict(existing.payload or {})
            existing_payload.pop("durable_job_id", None)
            if (
                existing.job_type != job_type
                or existing.space_id != space_id
                or payload_sha256(existing_payload) != digest
            ):
                msg = "idempotency_conflict"
                raise ValueError(msg)
            existing_event = db.execute(
                select(OutboxEvent)
                .where(
                    OutboxEvent.account_id == ctx.account_id,
                    OutboxEvent.durable_job_id == existing.id,
                    OutboxEvent.event_type == event_type,
                )
                .order_by(OutboxEvent.created_at.desc())
            ).scalar_one_or_none()
            if existing_event is not None:
                return EnqueuedJob(job_id=existing.id, outbox_event_id=existing_event.id)
    job_id = new_uuid7()
    event_id = new_uuid7()
    bound_payload = {**payload, "durable_job_id": str(job_id)}
    digest = payload_sha256(bound_payload)
    with tenant_scope(db, ctx.tenant()):
        db.add(
            DurableJob(
                id=job_id,
                account_id=ctx.account_id,
                space_id=space_id,
                job_type=job_type,
                status=JobStatus.QUEUED.value,
                correlation_id=ctx.correlation_id,
                idempotency_key=idempotency_key,
                payload=bound_payload,
                auth_snapshot=auth_snapshot_from_context(
                    ctx,
                    space_id=space_id,
                    resource_ids={
                        key: str(value)
                        for key, value in bound_payload.items()
                        if key.endswith("_id") and value is not None
                    },
                ),
            )
        )
        db.add(
            OutboxEvent(
                id=event_id,
                account_id=ctx.account_id,
                event_type=event_type,
                payload_sha256=digest,
                payload=bound_payload,
                durable_job_id=job_id,
            )
        )
    return EnqueuedJob(job_id=job_id, outbox_event_id=event_id)


def claim_outbox_batch(
    db: Session,
    *,
    worker_id: str,
    batch_size: int = 10,
    lease_seconds: int = 30,
) -> list[dict[str, object]]:
    rows = (
        db.execute(
            text(
                "SELECT id, account_id, event_type, payload_sha256, payload, claim_token "
                "FROM memdot_claim_outbox_events(:worker_id, :batch_size, :lease_seconds)"
            ),
            {
                "worker_id": worker_id,
                "batch_size": batch_size,
                "lease_seconds": lease_seconds,
            },
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def ack_outbox_event(
    db: Session,
    *,
    account_id: uuid.UUID,
    event_id: uuid.UUID,
    claim_token: uuid.UUID,
) -> bool:
    result = db.execute(
        text("SELECT memdot_ack_outbox_event(:account_id, :event_id, :claim_token)"),
        {
            "account_id": account_id,
            "event_id": event_id,
            "claim_token": claim_token,
        },
    ).scalar_one()
    return bool(result)


def start_job_attempt(db: Session, *, account_id: uuid.UUID, job_id: uuid.UUID) -> uuid.UUID:
    job = db.execute(
        select(DurableJob).where(DurableJob.account_id == account_id, DurableJob.id == job_id)
    ).scalar_one()
    attempt_no = (
        db.execute(
            select(JobAttempt)
            .where(JobAttempt.account_id == account_id, JobAttempt.job_id == job_id)
            .order_by(JobAttempt.attempt_number.desc())
        )
        .scalars()
        .first()
    )
    next_no = 1 if attempt_no is None else attempt_no.attempt_number + 1
    attempt_id = new_uuid7()
    db.add(
        JobAttempt(
            id=attempt_id,
            account_id=account_id,
            job_id=job_id,
            attempt_number=next_no,
            status=JobStatus.RUNNING.value,
            started_at=datetime.now(UTC),
        )
    )
    job.status = JobStatus.RUNNING.value
    job.updated_at = datetime.now(UTC)
    db.flush()
    return attempt_id


def complete_job(
    db: Session,
    *,
    account_id: uuid.UUID,
    job_id: uuid.UUID,
    attempt_id: uuid.UUID,
    succeeded: bool,
    error_code: str | None = None,
    error_detail_safe: str | None = None,
) -> None:
    job = db.execute(
        select(DurableJob).where(DurableJob.account_id == account_id, DurableJob.id == job_id)
    ).scalar_one()
    attempt = db.execute(
        select(JobAttempt).where(JobAttempt.account_id == account_id, JobAttempt.id == attempt_id)
    ).scalar_one()
    attempt.finished_at = datetime.now(UTC)
    attempt.status = JobStatus.SUCCEEDED.value if succeeded else JobStatus.FAILED.value
    attempt.error_code = error_code
    attempt.error_detail_safe = error_detail_safe
    job.status = attempt.status
    job.error_code = error_code
    job.error_detail_safe = error_detail_safe
    job.updated_at = datetime.now(UTC)
    db.flush()


def retry_delay_seconds(attempt_number: int) -> int:
    base = min(2**attempt_number, 300)
    return base + (attempt_number % 7)


def mark_dead_letter(db: Session, *, account_id: uuid.UUID, job_id: uuid.UUID) -> None:
    job = db.execute(
        select(DurableJob).where(DurableJob.account_id == account_id, DurableJob.id == job_id)
    ).scalar_one()
    job.status = JobStatus.DEAD_LETTER.value
    job.dead_letter_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    db.flush()


def cancel_job(db: Session, *, account_id: uuid.UUID, job_id: uuid.UUID) -> None:
    job = db.execute(
        select(DurableJob).where(DurableJob.account_id == account_id, DurableJob.id == job_id)
    ).scalar_one()
    job.status = JobStatus.CANCELLED.value
    job.cancelled_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    db.flush()
