"""Source lifecycle service: uploads, revisions, processing."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from memdot_domain.ids import new_uuid7, source_revision_id
from memdot_domain.ingestion import BlobKind, SourceProcessingStatus
from memdot_domain.object_keys import sanitize_filename
from memdot_domain.ports.object_storage import (
    ObjectKeyParts,
    ObjectLifecycleClass,
    ObjectStoragePort,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    DurableJob,
    Source,
    SourceBlob,
    SourceRevision,
    UploadIntent,
)
from memdot_core.db.tenant import tenant_scope
from memdot_core.jobs.service import EnqueuedJob, cancel_job, enqueue_job_with_outbox
from memdot_core.policy import DEFAULT_LIMITS as INGESTION_LIMITS
from memdot_core.request_context import RequestContext
from memdot_core.storage.s3 import MemoryObjectStorage


@dataclass(frozen=True)
class SourceCreateResult:
    source_id: uuid.UUID
    space_id: uuid.UUID


@dataclass(frozen=True)
class UploadIntentResult:
    upload_id: uuid.UUID
    upload_url: str
    object_key: str
    expires_at: datetime


@dataclass(frozen=True)
class RevisionResult:
    revision_id: uuid.UUID
    snapshot_sha256: str
    job: EnqueuedJob


def sniff_mime(content_type: str, filename: str) -> str:
    lowered = content_type.split(";")[0].strip().lower()
    if lowered and lowered != "application/octet-stream":
        return lowered
    if filename.lower().endswith(".pdf"):
        return "application/pdf"
    if filename.lower().endswith(".txt"):
        return "text/plain"
    if filename.lower().endswith(".md"):
        return "text/markdown"
    return "application/octet-stream"


def create_source(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    title: str,
) -> SourceCreateResult:
    source_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            Source(
                id=source_id,
                account_id=ctx.account_id,
                space_id=space_id,
                title=title,
                processing_status=SourceProcessingStatus.DRAFT.value,
            )
        )
    return SourceCreateResult(source_id=source_id, space_id=space_id)


def begin_upload(
    db: Session,
    ctx: RequestContext,
    storage: ObjectStoragePort,
    *,
    source_id: uuid.UUID,
    filename: str,
    content_type: str,
    byte_count: int,
    sha256: str,
) -> UploadIntentResult:
    if byte_count > INGESTION_LIMITS.max_object_bytes:
        msg = "file_too_large"
        raise ValueError(msg)
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    upload_id = new_uuid7()
    mime = sniff_mime(content_type, filename)
    parts = ObjectKeyParts(
        account_id=ctx.account_id,
        space_id=source.space_id,
        lifecycle=ObjectLifecycleClass.QUARANTINE,
        artifact_id=upload_id,
        filename=sanitize_filename(filename),
    )
    presigned = storage.create_presigned_upload(
        parts=parts,
        byte_count=byte_count,
        content_type=mime,
        sha256=sha256,
    )
    with tenant_scope(db, ctx.tenant()):
        db.add(
            UploadIntent(
                id=upload_id,
                account_id=ctx.account_id,
                space_id=source.space_id,
                source_id=source_id,
                object_key=presigned.object_key,
                expected_sha256=sha256,
                expected_byte_count=byte_count,
                content_type=mime,
                expires_at=presigned.expires_at,
            )
        )
        source.processing_status = SourceProcessingStatus.UPLOAD_PENDING.value
        source.updated_at = datetime.now(UTC)
    return UploadIntentResult(
        upload_id=upload_id,
        upload_url=presigned.url,
        object_key=presigned.object_key,
        expires_at=presigned.expires_at,
    )


def complete_upload(
    db: Session,
    ctx: RequestContext,
    storage: ObjectStoragePort,
    *,
    source_id: uuid.UUID,
    upload_id: uuid.UUID,
) -> RevisionResult:
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    intent = db.execute(
        select(UploadIntent).where(
            UploadIntent.account_id == ctx.account_id,
            UploadIntent.id == upload_id,
            UploadIntent.source_id == source_id,
        )
    ).scalar_one()
    if intent.completed_at is not None:
        existing = db.execute(
            select(SourceRevision).where(
                SourceRevision.account_id == ctx.account_id,
                SourceRevision.source_id == source_id,
                SourceRevision.snapshot_sha256 == intent.expected_sha256,
            )
        ).scalar_one_or_none()
        if existing is None:
            msg = "upload_already_completed_without_revision"
            raise ValueError(msg)
        latest_job = (
            db.execute(
                select(DurableJob)
                .where(DurableJob.account_id == ctx.account_id)
                .order_by(DurableJob.created_at.desc())
            )
            .scalars()
            .first()
        )
        job_ref = (
            EnqueuedJob(job_id=latest_job.id, outbox_event_id=new_uuid7())
            if latest_job is not None and latest_job.payload.get("revision_id") == str(existing.id)
            else EnqueuedJob(job_id=new_uuid7(), outbox_event_id=new_uuid7())
        )
        return RevisionResult(
            revision_id=existing.id,
            snapshot_sha256=existing.snapshot_sha256,
            job=job_ref,
        )

    storage.verify_upload_completion(
        object_key=intent.object_key,
        account_id=ctx.account_id,
        expected_sha256=intent.expected_sha256,
        expected_byte_count=intent.expected_byte_count,
    )
    original_parts = ObjectKeyParts(
        account_id=ctx.account_id,
        space_id=source.space_id,
        lifecycle=ObjectLifecycleClass.ORIGINAL,
        artifact_id=upload_id,
        filename=intent.object_key.rsplit("/", 1)[-1],
    )
    if isinstance(storage, MemoryObjectStorage):
        storage.head_object(object_key=intent.object_key, account_id=ctx.account_id)
        original_key = storage.build_key(original_parts)
        data = storage.read_object_bytes(object_key=intent.object_key, account_id=ctx.account_id)
        storage.put_bytes(
            object_key=original_key,
            data=data,
            content_type=intent.content_type,
            account_id=ctx.account_id,
            sha256=intent.expected_sha256,
        )
    else:
        promoted = storage.promote_from_quarantine(
            quarantine_key=intent.object_key,
            target_parts=original_parts,
            account_id=ctx.account_id,
        )
        original_key = promoted.object_key

    revision_uuid = source_revision_id(source_id, intent.expected_sha256)
    with tenant_scope(db, ctx.tenant()):
        existing = db.execute(
            select(SourceRevision).where(
                SourceRevision.account_id == ctx.account_id,
                SourceRevision.id == revision_uuid,
            )
        ).scalar_one_or_none()
        if existing is None:
            db.add(
                SourceRevision(
                    id=revision_uuid,
                    account_id=ctx.account_id,
                    space_id=source.space_id,
                    source_id=source_id,
                    snapshot_sha256=intent.expected_sha256,
                    captured_at=datetime.now(UTC),
                    mime_type=intent.content_type,
                    byte_count=intent.expected_byte_count,
                    object_key=original_key,
                )
            )
            db.flush()
            db.add(
                SourceBlob(
                    id=new_uuid7(),
                    account_id=ctx.account_id,
                    space_id=source.space_id,
                    source_revision_id=revision_uuid,
                    blob_kind=BlobKind.ORIGINAL.value,
                    object_key=original_key,
                    sha256=intent.expected_sha256,
                    byte_count=intent.expected_byte_count,
                )
            )
        intent.completed_at = datetime.now(UTC)
        source.processing_status = SourceProcessingStatus.QUEUED.value
        source.updated_at = datetime.now(UTC)

    payload = {
        "source_id": str(source_id),
        "revision_id": str(revision_uuid),
        "space_id": str(source.space_id),
    }
    idem = f"upload-complete:{upload_id}"
    job = enqueue_job_with_outbox(
        db,
        ctx,
        job_type="ingestion.parse",
        space_id=source.space_id,
        payload=payload,
        event_type="source.upload_completed",
        idempotency_key=idem,
    )
    return RevisionResult(
        revision_id=revision_uuid,
        snapshot_sha256=intent.expected_sha256,
        job=job,
    )


def list_revisions(
    db: Session,
    ctx: RequestContext,
    *,
    source_id: uuid.UUID,
) -> list[SourceRevision]:
    with tenant_scope(db, ctx.tenant()):
        rows = (
            db.execute(
                select(SourceRevision)
                .where(
                    SourceRevision.account_id == ctx.account_id,
                    SourceRevision.source_id == source_id,
                )
                .order_by(SourceRevision.captured_at.desc())
            )
            .scalars()
            .all()
        )
    return list(rows)


def citation_for_revision(revision: SourceRevision) -> dict[str, str]:
    return {
        "sourceId": str(revision.source_id),
        "revisionId": str(revision.id),
        "snapshotSha256": revision.snapshot_sha256,
        "capturedAt": revision.captured_at.isoformat(),
        "mimeType": revision.mime_type or "application/octet-stream",
    }


def processing_status(
    db: Session,
    ctx: RequestContext,
    *,
    source_id: uuid.UUID,
) -> dict[str, str | None]:
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    latest_job = (
        db.execute(
            select(DurableJob)
            .where(DurableJob.account_id == ctx.account_id)
            .order_by(DurableJob.created_at.desc())
        )
        .scalars()
        .first()
    )
    matched_job = None
    if latest_job is not None:
        payload_source = latest_job.payload.get("source_id")
        if payload_source == str(source_id):
            matched_job = latest_job
    return {
        "sourceId": str(source_id),
        "processingStatus": source.processing_status,
        "jobId": str(matched_job.id) if matched_job else None,
        "jobStatus": matched_job.status if matched_job else None,
        "errorCode": matched_job.error_code if matched_job else None,
    }


def cancel_processing(
    db: Session,
    ctx: RequestContext,
    *,
    source_id: uuid.UUID,
) -> None:
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    job = (
        db.execute(
            select(DurableJob)
            .where(
                DurableJob.account_id == ctx.account_id,
                DurableJob.status.in_(("queued", "running", "pending")),
            )
            .order_by(DurableJob.created_at.desc())
        )
        .scalars()
        .first()
    )
    if job is not None and job.payload.get("source_id") != str(source_id):
        job = None
    with tenant_scope(db, ctx.tenant()):
        if job is not None:
            cancel_job(db, account_id=ctx.account_id, job_id=job.id)
        source.processing_status = SourceProcessingStatus.CANCELLED.value
        source.updated_at = datetime.now(UTC)


def retry_processing(
    db: Session,
    ctx: RequestContext,
    *,
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
) -> EnqueuedJob:
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    db.execute(
        select(SourceRevision).where(
            SourceRevision.account_id == ctx.account_id,
            SourceRevision.id == revision_id,
            SourceRevision.source_id == source_id,
        )
    ).scalar_one()
    payload = {
        "source_id": str(source_id),
        "revision_id": str(revision_id),
        "space_id": str(source.space_id),
    }
    with tenant_scope(db, ctx.tenant()):
        source.processing_status = SourceProcessingStatus.QUEUED.value
        source.updated_at = datetime.now(UTC)
    return enqueue_job_with_outbox(
        db,
        ctx,
        job_type="ingestion.parse",
        space_id=source.space_id,
        payload=payload,
        event_type="source.retry_requested",
    )


def reprocess_revision(
    db: Session,
    ctx: RequestContext,
    *,
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
    shadow: bool = False,
) -> EnqueuedJob:
    source = db.execute(
        select(Source).where(Source.account_id == ctx.account_id, Source.id == source_id)
    ).scalar_one()
    db.execute(
        select(SourceRevision).where(
            SourceRevision.account_id == ctx.account_id,
            SourceRevision.id == revision_id,
            SourceRevision.source_id == source_id,
        )
    ).scalar_one()
    payload = {
        "source_id": str(source_id),
        "revision_id": str(revision_id),
        "space_id": str(source.space_id),
        "shadow": shadow,
    }
    with tenant_scope(db, ctx.tenant()):
        source.processing_status = SourceProcessingStatus.QUEUED.value
        source.updated_at = datetime.now(UTC)
    return enqueue_job_with_outbox(
        db,
        ctx,
        job_type="ingestion.reprocess",
        space_id=source.space_id,
        payload=payload,
        event_type="source.reprocess_requested",
    )
