"""Outbox dispatch and durable job execution for Wave 4 ingestion."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, cast

from memdot_core.db.models.ledger import DurableJob
from memdot_core.ingestion.orchestrator import run_ingestion_for_revision
from memdot_core.jobs.auth_snapshot import validate_auth_snapshot
from memdot_core.jobs.service import ack_outbox_event, claim_outbox_batch, payload_sha256
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.ports.object_storage import ObjectStoragePort
from sqlalchemy import select
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DispatchResult:
    event_id: uuid.UUID
    acknowledged: bool
    job_id: uuid.UUID | None = None


INGESTION_EVENT_TYPES = frozenset(
    {
        "source.upload_completed",
        "source.retry_requested",
        "source.reprocess_requested",
    }
)

DELETION_EVENT_TYPES = frozenset(
    {
        "deletion.tombstoned",
        "deletion.workflow_advanced",
    }
)


def _ack(
    db: Session,
    *,
    account_id: uuid.UUID,
    event: dict[str, Any],
    job_id: uuid.UUID | None = None,
) -> DispatchResult:
    event_id = uuid.UUID(str(event["id"]))
    token = event.get("claim_token")
    if token is None:
        return DispatchResult(event_id=event_id, acknowledged=False, job_id=job_id)
    acked = ack_outbox_event(
        db,
        account_id=account_id,
        event_id=event_id,
        claim_token=uuid.UUID(str(token)),
    )
    return DispatchResult(event_id=event_id, acknowledged=acked, job_id=job_id)


def _process_deletion_event(
    db: Session,
    *,
    account_id: uuid.UUID,
    event: dict[str, Any],
    payload: dict[str, Any],
) -> DispatchResult:
    """Advance deletion workflow checkpoints after tombstone-first acceptance."""
    from datetime import UTC, datetime

    from memdot_core.db.models.ledger import DeletionWorkflow
    from memdot_core.db.tenant import TenantContext, tenant_scope
    from memdot_domain.tenancy import RequestPurpose

    workflow_raw = payload.get("workflow_id")
    if workflow_raw is None:
        return _ack(db, account_id=account_id, event=event)
    try:
        workflow_id = uuid.UUID(str(workflow_raw))
    except ValueError:
        return DispatchResult(event_id=uuid.UUID(str(event["id"])), acknowledged=False)

    row = db.execute(
        select(DeletionWorkflow).where(
            DeletionWorkflow.account_id == account_id,
            DeletionWorkflow.id == workflow_id,
        )
    ).scalar_one_or_none()
    if row is None:
        return _ack(db, account_id=account_id, event=event)

    progression = {
        "tombstoned": "revoking_grants",
        "revoking_grants": "purging_projections",
        "purging_projections": "completed",
    }
    next_state = progression.get(row.state)
    if next_state is not None:
        actor_raw = payload.get("actor_id")
        try:
            actor_id = uuid.UUID(str(actor_raw)) if actor_raw else account_id
        except ValueError:
            actor_id = account_id
        tenant = TenantContext(
            account_id=account_id,
            actor_id=actor_id,
            purpose=RequestPurpose.WORKER,
        )
        with tenant_scope(db, tenant):
            row.state = next_state
            row.updated_at = datetime.now(UTC)
    return _ack(db, account_id=account_id, event=event)


def process_claimed_event(
    db: Session,
    storage: ObjectStoragePort,
    *,
    event: dict[str, Any],
) -> DispatchResult:
    event_id = uuid.UUID(str(event["id"]))
    account_id = uuid.UUID(str(event["account_id"]))
    event_type = str(event["event_type"])
    payload_raw = event.get("payload")
    if not isinstance(payload_raw, dict):
        return DispatchResult(event_id=event_id, acknowledged=False)
    payload = cast(dict[str, Any], payload_raw)
    if event_type in DELETION_EVENT_TYPES:
        return _process_deletion_event(db, account_id=account_id, event=event, payload=payload)
    if event_type not in INGESTION_EVENT_TYPES:
        # A worker must never silently discard an outbox fact it does not own.
        return DispatchResult(event_id=event_id, acknowledged=False)

    source_id = uuid.UUID(str(payload["source_id"]))
    revision_id = uuid.UUID(str(payload["revision_id"]))
    shadow = bool(payload.get("shadow", False))
    job_raw = payload.get("durable_job_id") or event.get("durable_job_id")
    if job_raw is None:
        return DispatchResult(event_id=event_id, acknowledged=False)
    try:
        job_id = uuid.UUID(str(job_raw))
    except ValueError:
        return DispatchResult(event_id=event_id, acknowledged=False)
    job = db.execute(
        select(DurableJob).where(DurableJob.account_id == account_id, DurableJob.id == job_id)
    ).scalar_one_or_none()
    # Never execute worker effects without a verified signed auth snapshot.
    if job is None or not job.auth_snapshot:
        return DispatchResult(event_id=event_id, acknowledged=False, job_id=job_id)
    if not validate_auth_snapshot(
        db,
        account_id=account_id,
        snapshot=job.auth_snapshot,
        expected_space_id=job.space_id,
    ):
        # Terminal re-authorization required — do not retry forever.
        from datetime import UTC, datetime

        from memdot_core.jobs.service import mark_dead_letter
        from memdot_domain.ingestion import JobStatus

        job.error_code = "auth_snapshot_invalid"
        job.error_detail_safe = (
            "Authorization snapshot expired or revoked; re-authorization required."
        )
        job.updated_at = datetime.now(UTC)
        job.status = JobStatus.DEAD_LETTER.value
        mark_dead_letter(db, account_id=account_id, job_id=job_id)
        return _ack(db, account_id=account_id, event=event, job_id=job_id)

    actor_id = uuid.UUID(str(job.auth_snapshot["actor_id"]))
    run_ingestion_for_revision(
        db,
        storage,
        account_id=account_id,
        actor_id=actor_id,
        source_id=source_id,
        revision_id=revision_id,
        job_id=job_id,
        shadow=shadow,
    )
    token = event.get("claim_token")
    if token is None:
        return DispatchResult(event_id=event_id, acknowledged=False, job_id=job_id)
    acked = ack_outbox_event(
        db,
        account_id=account_id,
        event_id=event_id,
        claim_token=uuid.UUID(str(token)),
    )
    return DispatchResult(event_id=event_id, acknowledged=acked, job_id=job_id)


def dispatch_outbox_batch(
    db: Session,
    storage: ObjectStoragePort | None = None,
    *,
    worker_id: str,
    batch_size: int = 10,
) -> list[DispatchResult]:
    store = storage or MemoryObjectStorage()
    claimed = claim_outbox_batch(db, worker_id=worker_id, batch_size=batch_size)
    results: list[DispatchResult] = []
    for event in claimed:
        payload_raw = event.get("payload")
        if isinstance(payload_raw, dict):
            digest = payload_sha256(cast(dict[str, Any], payload_raw))
            if digest and str(event.get("payload_sha256")) != digest:
                continue
        results.append(process_claimed_event(db, store, event=cast(dict[str, Any], event)))
    return results
