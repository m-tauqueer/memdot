"""Ingestion orchestration: sniff, parse, checkpoint, and durable stage transitions."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from memdot_domain.ids import new_uuid7
from memdot_domain.ids import parse_run_id as deterministic_parse_run_id
from memdot_domain.ingestion import ParseRunStatus, SourceProcessingStatus
from memdot_domain.ports.object_storage import (
    ObjectKeyParts,
    ObjectLifecycleClass,
    ObjectStoragePort,
)
from memdot_domain.ports.parser import ParseResult
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import DocumentElement, ParseRun, Source, SourceRevision
from memdot_core.db.tenant import tenant_scope
from memdot_core.ingestion.normalize import promote_active_parse_run, validate_parse_result
from memdot_core.jobs.service import complete_job, start_job_attempt
from memdot_core.parsers.ocr_fallback import OCR_QUALITY_THRESHOLD
from memdot_core.parsers.registry import select_parser
from memdot_core.parsers.resource_limits import (
    ResourceLimitExceeded,
    check_file_size,
    check_page_count,
)
from memdot_core.request_context import RequestContext


@dataclass(frozen=True)
class IngestionOutcome:
    parse_run_id: uuid.UUID
    status: ParseRunStatus
    quality_score: float
    element_count: int


def sniff_mime(content_type: str, filename: str, content_head: bytes) -> str:
    lowered = content_type.split(";")[0].strip().lower()
    if content_head.startswith(b"%PDF"):
        return "application/pdf"
    if lowered and lowered != "application/octet-stream":
        return lowered
    if filename.lower().endswith(".pdf"):
        return "application/pdf"
    if filename.lower().endswith((".txt", ".md")):
        return "text/plain"
    return lowered or "application/octet-stream"


def language_hints_from_revision(revision: SourceRevision) -> tuple[str, ...]:
    if not revision.language_hints:
        return ("en",)
    return tuple(part.strip() for part in revision.language_hints.split(",") if part.strip())


def load_revision_bytes(
    storage: ObjectStoragePort,
    revision: SourceRevision,
    account_id: uuid.UUID,
) -> bytes:
    if revision.object_key is None:
        msg = "revision_missing_object_key"
        raise ValueError(msg)
    return storage.read_object_bytes(object_key=revision.object_key, account_id=account_id)


def _persist_parse_run(
    db: Session,
    *,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    revision: SourceRevision,
    profile: str,
    profile_hash: str,
    run_uuid: uuid.UUID,
    status: ParseRunStatus,
    quality_score: float | None,
    stage_checkpoint: dict[str, object],
    artifact_key: str | None,
    error_code: str | None = None,
    error_detail_safe: str | None = None,
    is_shadow: bool = False,
) -> ParseRun:
    row = ParseRun(
        id=run_uuid,
        account_id=account_id,
        space_id=space_id,
        source_revision_id=revision.id,
        parser_profile=profile,
        profile_hash=profile_hash,
        status=status.value,
        quality_score=quality_score,
        stage_checkpoint=stage_checkpoint,
        artifact_object_key=artifact_key,
        error_code=error_code,
        error_detail_safe=error_detail_safe,
        is_shadow=is_shadow,
    )
    db.add(row)
    db.flush()
    return row


def _store_parser_artifact(
    storage: ObjectStoragePort,
    *,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    run_uuid: uuid.UUID,
    artifact_bytes: bytes,
) -> str:
    parts = ObjectKeyParts(
        account_id=account_id,
        space_id=space_id,
        lifecycle=ObjectLifecycleClass.ARTIFACT,
        artifact_id=run_uuid,
        filename="parser-artifact.json",
    )
    key = storage.build_key(parts)
    if hasattr(storage, "put_bytes"):
        storage.put_bytes(  # type: ignore[attr-defined]
            object_key=key,
            data=artifact_bytes,
            content_type="application/json",
            account_id=account_id,
            sha256=hashlib.sha256(artifact_bytes).hexdigest(),
        )
    return key


def _persist_elements(
    db: Session,
    *,
    account_id: uuid.UUID,
    space_id: uuid.UUID,
    run_uuid: uuid.UUID,
    result: ParseResult,
) -> int:
    for element in result.elements:
        db.add(
            DocumentElement(
                id=element.element_id,
                account_id=account_id,
                space_id=space_id,
                parse_run_id=run_uuid,
                element_kind=element.kind.value,
                locator=element.locator.value,
                element_index=element.order_index,
                parent_element_id=element.parent_element_id,
                content_hash=element.content_hash,
                exact_text=element.exact_text,
                normalized_text=element.normalized_text,
                element_metadata=dict(element.metadata),
            )
        )
    db.flush()
    return len(result.elements)


def run_ingestion_for_revision(
    db: Session,
    storage: ObjectStoragePort,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    source_id: uuid.UUID,
    revision_id: uuid.UUID,
    job_id: uuid.UUID | None = None,
    shadow: bool = False,
) -> IngestionOutcome:
    ctx = RequestContext(
        account_id=account_id,
        actor_id=actor_id,
        user_id=actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )
    revision = db.execute(
        select(SourceRevision).where(
            SourceRevision.account_id == account_id,
            SourceRevision.id == revision_id,
            SourceRevision.source_id == source_id,
        )
    ).scalar_one()
    source = db.execute(
        select(Source).where(Source.account_id == account_id, Source.id == source_id)
    ).scalar_one()

    attempt_id: uuid.UUID | None = None
    if job_id is not None:
        attempt_id = start_job_attempt(db, account_id=account_id, job_id=job_id)

    with tenant_scope(db, ctx.tenant()):
        source.processing_status = SourceProcessingStatus.RUNNING.value
        source.updated_at = datetime.now(UTC)

        content = load_revision_bytes(storage, revision, account_id)
        try:
            check_file_size(len(content))
        except ResourceLimitExceeded as exc:
            failed = _persist_parse_run(
                db,
                account_id=account_id,
                space_id=revision.space_id,
                revision=revision,
                profile="resource_limits",
                profile_hash="resource_limits_v1",
                run_uuid=new_uuid7(),
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                stage_checkpoint={"stage": "resource_limits", "error": exc.code},
                artifact_key=None,
                error_code=exc.code,
                error_detail_safe=exc.code,
                is_shadow=shadow,
            )
            source.processing_status = SourceProcessingStatus.FAILED.value
            if job_id is not None and attempt_id is not None:
                complete_job(
                    db,
                    account_id=account_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    succeeded=False,
                )
            return IngestionOutcome(
                parse_run_id=failed.id,
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                element_count=0,
            )
        mime = sniff_mime(revision.mime_type or "", revision.object_key or "", content[:16])
        hints = language_hints_from_revision(revision)

        primary = select_parser(mime, ocr_fallback=False)
        run_uuid = deterministic_parse_run_id(revision.id, primary.profile_hash())
        existing = db.execute(
            select(ParseRun).where(ParseRun.account_id == account_id, ParseRun.id == run_uuid)
        ).scalar_one_or_none()
        if (
            existing is not None
            and existing.status == ParseRunStatus.SUCCEEDED.value
            and not shadow
        ):
            source.processing_status = SourceProcessingStatus.SUCCEEDED.value
            if job_id is not None and attempt_id is not None:
                complete_job(
                    db,
                    account_id=account_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    succeeded=True,
                )
            return IngestionOutcome(
                parse_run_id=run_uuid,
                status=ParseRunStatus.SUCCEEDED,
                quality_score=float(existing.quality_score or 0.0),
                element_count=0,
            )

        try:
            result = primary.parse(
                content=content,
                mime_type=mime,
                language_hints=hints,
                parse_run_id=run_uuid,
            )
            check_page_count(result.page_count)
        except ResourceLimitExceeded as exc:
            failed = _persist_parse_run(
                db,
                account_id=account_id,
                space_id=revision.space_id,
                revision=revision,
                profile=primary.profile.value,
                profile_hash=primary.profile_hash(),
                run_uuid=run_uuid,
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                stage_checkpoint={"stage": "resource_limits", "error": exc.code},
                artifact_key=None,
                error_code=exc.code,
                error_detail_safe=exc.code,
                is_shadow=shadow,
            )
            source.processing_status = SourceProcessingStatus.FAILED.value
            if job_id is not None and attempt_id is not None:
                complete_job(
                    db,
                    account_id=account_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    succeeded=False,
                    error_code=exc.code,
                    error_detail_safe=exc.code,
                )
            return IngestionOutcome(
                parse_run_id=failed.id,
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                element_count=0,
            )
        except ValueError as exc:
            failed = _persist_parse_run(
                db,
                account_id=account_id,
                space_id=revision.space_id,
                revision=revision,
                profile=primary.profile.value,
                profile_hash=primary.profile_hash(),
                run_uuid=run_uuid,
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                stage_checkpoint={"stage": "parse", "error": str(exc)},
                artifact_key=None,
                error_code="parse_failed",
                error_detail_safe="Parsing failed.",
                is_shadow=shadow,
            )
            source.processing_status = SourceProcessingStatus.FAILED.value
            if job_id is not None and attempt_id is not None:
                complete_job(
                    db,
                    account_id=account_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    succeeded=False,
                    error_code="parse_failed",
                    error_detail_safe="Parsing failed.",
                )
            return IngestionOutcome(
                parse_run_id=failed.id,
                status=ParseRunStatus.FAILED,
                quality_score=0.0,
                element_count=0,
            )

        if result.quality_score < OCR_QUALITY_THRESHOLD:
            ocr = select_parser(mime, ocr_fallback=True)
            ocr_run_uuid = deterministic_parse_run_id(revision.id, ocr.profile_hash())
            ocr_result = ocr.parse(
                content=content,
                mime_type=mime,
                language_hints=hints,
                parse_run_id=ocr_run_uuid,
            )
            if ocr_result.quality_score > result.quality_score:
                result = ocr_result
                run_uuid = ocr_run_uuid
                primary = ocr

        artifact_key = _store_parser_artifact(
            storage,
            account_id=account_id,
            space_id=revision.space_id,
            run_uuid=run_uuid,
            artifact_bytes=result.raw_artifact_bytes,
        )
        _persist_parse_run(
            db,
            account_id=account_id,
            space_id=revision.space_id,
            revision=revision,
            profile=primary.profile.value,
            profile_hash=primary.profile_hash(),
            run_uuid=run_uuid,
            status=ParseRunStatus.RUNNING,
            quality_score=result.quality_score,
            stage_checkpoint={"stage": "parsed", "pages": result.page_count},
            artifact_key=artifact_key,
            is_shadow=shadow,
        )
        element_count = _persist_elements(
            db,
            account_id=account_id,
            space_id=revision.space_id,
            run_uuid=run_uuid,
            result=result,
        )
        validation_errors = validate_parse_result(result)
        if validation_errors:
            db.execute(
                select(ParseRun).where(ParseRun.account_id == account_id, ParseRun.id == run_uuid)
            ).scalar_one()
            parse_row = db.get(ParseRun, run_uuid)
            assert parse_row is not None
            parse_row.status = ParseRunStatus.FAILED.value
            parse_row.error_code = "validation_failed"
            parse_row.error_detail_safe = "Normalized output failed validation."
            source.processing_status = SourceProcessingStatus.FAILED.value
            if job_id is not None and attempt_id is not None:
                complete_job(
                    db,
                    account_id=account_id,
                    job_id=job_id,
                    attempt_id=attempt_id,
                    succeeded=False,
                    error_code="validation_failed",
                )
            return IngestionOutcome(
                parse_run_id=run_uuid,
                status=ParseRunStatus.FAILED,
                quality_score=result.quality_score,
                element_count=element_count,
            )

        if not shadow and result.quality_score >= OCR_QUALITY_THRESHOLD:
            promote_active_parse_run(
                db,
                account_id=account_id,
                space_id=revision.space_id,
                source_id=source_id,
                revision_id=revision_id,
                parse_run_id=run_uuid,
                payload={
                    "source_id": str(source_id),
                    "revision_id": str(revision_id),
                    "parse_run_id": str(run_uuid),
                },
            )
            parse_row = db.get(ParseRun, run_uuid)
            assert parse_row is not None
            parse_row.status = ParseRunStatus.SUCCEEDED.value
            source.processing_status = SourceProcessingStatus.SUCCEEDED.value
        elif shadow:
            parse_row = db.get(ParseRun, run_uuid)
            assert parse_row is not None
            parse_row.status = ParseRunStatus.SUCCEEDED.value
            parse_row.is_shadow = True
        else:
            parse_row = db.get(ParseRun, run_uuid)
            assert parse_row is not None
            parse_row.status = ParseRunStatus.FAILED.value
            parse_row.error_code = "quality_below_threshold"
            source.processing_status = SourceProcessingStatus.PARTIAL.value

        if job_id is not None and attempt_id is not None:
            complete_job(
                db,
                account_id=account_id,
                job_id=job_id,
                attempt_id=attempt_id,
                succeeded=source.processing_status
                in {SourceProcessingStatus.SUCCEEDED.value, SourceProcessingStatus.PARTIAL.value},
            )

        return IngestionOutcome(
            parse_run_id=run_uuid,
            status=ParseRunStatus(parse_row.status if parse_row else ParseRunStatus.FAILED.value),
            quality_score=result.quality_score,
            element_count=element_count,
        )
