"""Authored document lifecycle service."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from memdot_domain.document import (
    DocumentValidationError,
    content_sha256,
    extract_plain_text,
    validate_document_payload,
)
from memdot_domain.ids import new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    AuthoredDocument,
    CurrentDocumentRevision,
    DocumentRevision,
)
from memdot_core.db.tenant import set_current_document_revision, tenant_scope
from memdot_core.jobs.service import payload_sha256
from memdot_core.request_context import RequestContext


@dataclass(frozen=True)
class DocumentCreateResult:
    document_id: uuid.UUID
    revision_id: uuid.UUID
    space_id: uuid.UUID


@dataclass(frozen=True)
class RevisionSaveResult:
    document_id: uuid.UUID
    revision_id: uuid.UUID
    content_sha256: str


class StaleBaseRevisionError(Exception):
    def __init__(self, *, current_revision_id: uuid.UUID | None) -> None:
        self.current_revision_id = current_revision_id
        super().__init__("stale_base_revision")


def _empty_document(document_id: uuid.UUID) -> dict[str, Any]:
    return {
        "schema": "memdot-document",
        "schemaVersion": 1,
        "documentId": str(document_id),
        "root": {"type": "doc", "content": []},
    }


def create_document(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID,
    title: str,
    document_body: dict[str, Any] | None = None,
) -> DocumentCreateResult:
    document_id = new_uuid7()
    revision_id = new_uuid7()
    pointer_id = new_uuid7()
    event_id = new_uuid7()
    body = document_body or _empty_document(document_id)
    body["documentId"] = str(document_id)
    validated = validate_document_payload(body)
    digest = content_sha256(validated)
    plain = extract_plain_text(validated)
    content_json = validated.model_dump(mode="json", by_alias=True)
    outbox_payload = {
        "document_id": str(document_id),
        "revision_id": str(revision_id),
        "space_id": str(space_id),
        "content_sha256": digest,
        "author_actor_id": str(ctx.actor_id),
    }
    with tenant_scope(db, ctx.tenant()):
        db.add(
            AuthoredDocument(
                id=document_id,
                account_id=ctx.account_id,
                space_id=space_id,
                title=title,
            )
        )
        db.add(
            DocumentRevision(
                id=revision_id,
                account_id=ctx.account_id,
                space_id=space_id,
                document_id=document_id,
                base_revision_id=None,
                content_sha256=digest,
                schema_version=1,
                content_json=content_json,
                plain_text=plain,
                author_actor_id=ctx.actor_id,
            )
        )
        set_current_document_revision(
            db,
            pointer_id=pointer_id,
            account_id=ctx.account_id,
            space_id=space_id,
            document_id=document_id,
            revision_id=revision_id,
            event_id=event_id,
            payload_sha256=payload_sha256(outbox_payload),
            payload_json=json.dumps(outbox_payload),
        )
    return DocumentCreateResult(document_id=document_id, revision_id=revision_id, space_id=space_id)


def save_revision(
    db: Session,
    ctx: RequestContext,
    *,
    document_id: uuid.UUID,
    base_revision_id: uuid.UUID | None,
    document_body: dict[str, Any],
    proposal_id: uuid.UUID | None = None,
) -> RevisionSaveResult:
    document_body = dict(document_body)
    document_body["documentId"] = str(document_id)
    validated = validate_document_payload(document_body)
    current = db.execute(
        select(CurrentDocumentRevision).where(
            CurrentDocumentRevision.account_id == ctx.account_id,
            CurrentDocumentRevision.document_id == document_id,
        )
    ).scalar_one_or_none()
    current_revision_id = current.revision_id if current else None
    if base_revision_id != current_revision_id:
        raise StaleBaseRevisionError(current_revision_id=current_revision_id)

    doc_row = db.execute(
        select(AuthoredDocument).where(
            AuthoredDocument.account_id == ctx.account_id,
            AuthoredDocument.id == document_id,
        )
    ).scalar_one()
    revision_id = new_uuid7()
    pointer_id = current.id if current else new_uuid7()
    event_id = new_uuid7()
    digest = content_sha256(validated)
    plain = extract_plain_text(validated)
    content_json = validated.model_dump(mode="json", by_alias=True)
    outbox_payload = {
        "document_id": str(document_id),
        "revision_id": str(revision_id),
        "space_id": str(doc_row.space_id),
        "base_revision_id": str(base_revision_id) if base_revision_id else None,
        "content_sha256": digest,
        "author_actor_id": str(ctx.actor_id),
        "proposal_id": str(proposal_id) if proposal_id else None,
    }
    with tenant_scope(db, ctx.tenant()):
        db.add(
            DocumentRevision(
                id=revision_id,
                account_id=ctx.account_id,
                space_id=doc_row.space_id,
                document_id=document_id,
                base_revision_id=base_revision_id,
                content_sha256=digest,
                schema_version=1,
                content_json=content_json,
                plain_text=plain,
                author_actor_id=ctx.actor_id,
                proposal_id=proposal_id,
            )
        )
        set_current_document_revision(
            db,
            pointer_id=pointer_id,
            account_id=ctx.account_id,
            space_id=doc_row.space_id,
            document_id=document_id,
            revision_id=revision_id,
            event_id=event_id,
            payload_sha256=payload_sha256(outbox_payload),
            payload_json=json.dumps(outbox_payload),
        )
    return RevisionSaveResult(
        document_id=document_id, revision_id=revision_id, content_sha256=digest
    )


def get_current_revision(
    db: Session,
    ctx: RequestContext,
    *,
    document_id: uuid.UUID,
) -> DocumentRevision | None:
    current = db.execute(
        select(CurrentDocumentRevision).where(
            CurrentDocumentRevision.account_id == ctx.account_id,
            CurrentDocumentRevision.document_id == document_id,
        )
    ).scalar_one_or_none()
    if current is None:
        return None
    return db.execute(
        select(DocumentRevision).where(
            DocumentRevision.account_id == ctx.account_id,
            DocumentRevision.id == current.revision_id,
        )
    ).scalar_one_or_none()


def list_revisions(
    db: Session,
    ctx: RequestContext,
    *,
    document_id: uuid.UUID,
) -> list[DocumentRevision]:
    return list(
        db.execute(
            select(DocumentRevision)
            .where(
                DocumentRevision.account_id == ctx.account_id,
                DocumentRevision.document_id == document_id,
            )
            .order_by(DocumentRevision.created_at.asc())
        )
        .scalars()
        .all()
    )


def get_revision(
    db: Session,
    ctx: RequestContext,
    *,
    document_id: uuid.UUID,
    revision_id: uuid.UUID,
) -> DocumentRevision | None:
    return db.execute(
        select(DocumentRevision).where(
            DocumentRevision.account_id == ctx.account_id,
            DocumentRevision.document_id == document_id,
            DocumentRevision.id == revision_id,
        )
    ).scalar_one_or_none()


def revision_payload(revision: DocumentRevision) -> dict[str, Any]:
    return {
        "revisionId": str(revision.id),
        "documentId": str(revision.document_id),
        "spaceId": str(revision.space_id),
        "baseRevisionId": str(revision.base_revision_id) if revision.base_revision_id else None,
        "contentSha256": revision.content_sha256,
        "schemaVersion": revision.schema_version,
        "document": revision.content_json,
        "plainText": revision.plain_text,
        "authorActorId": str(revision.author_actor_id) if revision.author_actor_id else None,
        "createdAt": revision.created_at.isoformat(),
    }


def validate_or_raise(document_body: dict[str, Any]) -> None:
    try:
        validate_document_payload(document_body)
    except DocumentValidationError as exc:
        raise ValueError(str(exc)) from exc
