"""Outbox dispatch and durable job execution for Wave 4 ingestion."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, cast

from memdot_core.db.models.ledger import DurableJob
from memdot_core.db.models.tenancy import Account
from memdot_core.ingestion.orchestrator import run_ingestion_for_revision
from memdot_core.jobs.service import ack_outbox_event, claim_outbox_batch, payload_sha256
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.ports.object_storage import ObjectStoragePort
from memdot_domain.tenancy import RequestPurpose
from memdot_domain.tenant_seal import TenantSealMaterial, sign_tenant_context
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


def validate_auth_snapshot(
    db: Session,
    *,
    account_id: uuid.UUID,
    snapshot: dict[str, object] | None,
) -> bool:
    """Reauthorize worker effect against current account/source existence."""
    if snapshot is None:
        return False
    if str(snapshot.get("account_id")) != str(account_id):
        return False
    actor_raw = snapshot.get("actor_id")
    if actor_raw is None:
        return False
    purpose = snapshot.get("purpose")
    if purpose not in {RequestPurpose.FIRST_PARTY.value, RequestPurpose.WORKER.value}:
        return False
    account = db.execute(select(Account.id).where(Account.id == account_id)).scalar_one_or_none()
    return account is not None


def seal_from_auth_snapshot(snapshot: dict[str, object]) -> TenantSealMaterial | None:
    account_raw = snapshot.get("account_id")
    actor_raw = snapshot.get("actor_id")
    purpose_raw = snapshot.get("purpose")
    if not isinstance(account_raw, str) or not isinstance(actor_raw, str):
        return None
    try:
        purpose = RequestPurpose(str(purpose_raw))
        account_id = uuid.UUID(account_raw)
        actor_id = uuid.UUID(actor_raw)
    except ValueError:
        return None
    issued_at = 0
    nonce = "worker"
    signature = sign_tenant_context(
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        issued_at=issued_at,
        nonce=nonce,
    )
    return TenantSealMaterial(
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        issued_at=issued_at,
        nonce=nonce,
        signature=signature,
    )


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
    if event_type not in INGESTION_EVENT_TYPES:
        token = event.get("claim_token")
        if token is None:
            return DispatchResult(event_id=event_id, acknowledged=False)
        acked = ack_outbox_event(
            db,
            account_id=account_id,
            event_id=event_id,
            claim_token=uuid.UUID(str(token)),
        )
        return DispatchResult(event_id=event_id, acknowledged=acked)

    source_id = uuid.UUID(str(payload["source_id"]))
    revision_id = uuid.UUID(str(payload["revision_id"]))
    shadow = bool(payload.get("shadow", False))
    job = (
        db.execute(
            select(DurableJob)
            .where(DurableJob.account_id == account_id)
            .order_by(DurableJob.created_at.desc())
        )
        .scalars()
        .first()
    )
    if job is not None and job.payload.get("source_id") != str(source_id):
        job = None
    if job is not None and job.payload.get("revision_id") != str(revision_id):
        job = None
    job_id = job.id if job is not None else None
    if job is not None and not validate_auth_snapshot(
        db, account_id=account_id, snapshot=job.auth_snapshot
    ):
        return DispatchResult(event_id=event_id, acknowledged=False, job_id=job_id)

    actor_id = (
        uuid.UUID(str(job.auth_snapshot["actor_id"])) if job and job.auth_snapshot else account_id
    )
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
