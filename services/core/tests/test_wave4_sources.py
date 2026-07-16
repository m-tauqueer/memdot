"""Wave 4 source lifecycle and ingestion integration tests."""

from __future__ import annotations

import hashlib
import uuid

from factories import create_account_bundle
from memdot_core.db.models.ledger import SourceRevision
from memdot_core.db.models.tenancy import BrowserSession
from memdot_core.db.tenant import tenant_scope
from memdot_core.ingestion.orchestrator import run_ingestion_for_revision
from memdot_core.request_context import RequestContext
from memdot_core.sources import service as source_service
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.ids import source_revision_id
from memdot_domain.ingestion import SourceProcessingStatus
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import select


def _session_for_bundle(db_session, bundle) -> RequestContext:
    session_id = uuid.uuid4()
    db_session.add(
        BrowserSession(
            id=session_id,
            account_id=bundle.account_id,
            user_id=bundle.user_id,
            actor_id=bundle.actor_id,
            secret_hash="hash",
            csrf_token_hash="csrf",
            expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC)
            + __import__("datetime").timedelta(hours=1),
            idle_expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC)
            + __import__("datetime").timedelta(hours=1),
            last_auth_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )
    )
    db_session.flush()
    return RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=uuid.uuid4(),
        session_id=session_id,
    )


def test_source_upload_revision_and_ingestion(db_session, truncate_tables) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _session_for_bundle(db_session, bundle)
    storage = MemoryObjectStorage()

    created = source_service.create_source(db_session, ctx, space_id=space_id, title="Notes")
    content = b"Line one\nLine two\n"
    sha = hashlib.sha256(content).hexdigest()
    intent = source_service.begin_upload(
        db_session,
        ctx,
        storage,
        source_id=created.source_id,
        filename="notes.txt",
        content_type="text/plain",
        byte_count=len(content),
        sha256=sha,
    )
    storage.put_bytes(
        object_key=intent.object_key,
        data=content,
        content_type="text/plain",
        account_id=bundle.account_id,
        sha256=sha,
    )
    result = source_service.complete_upload(
        db_session,
        ctx,
        storage,
        source_id=created.source_id,
        upload_id=intent.upload_id,
    )
    expected_revision = source_revision_id(created.source_id, sha)
    assert result.revision_id == expected_revision

    outcome = run_ingestion_for_revision(
        db_session,
        storage,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        source_id=created.source_id,
        revision_id=result.revision_id,
    )
    assert outcome.element_count == 2
    assert outcome.quality_score == 1.0

    with tenant_scope(db_session, ctx.tenant()):
        revision = db_session.execute(
            select(SourceRevision).where(
                SourceRevision.account_id == bundle.account_id,
                SourceRevision.id == result.revision_id,
            )
        ).scalar_one()
        assert revision.snapshot_sha256 == sha
        status = source_service.processing_status(db_session, ctx, source_id=created.source_id)
    assert status["processingStatus"] == SourceProcessingStatus.SUCCEEDED.value


def test_reprocess_preserves_revision_identity(db_session, truncate_tables) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = _session_for_bundle(db_session, bundle)
    storage = MemoryObjectStorage()
    created = source_service.create_source(db_session, ctx, space_id=space_id, title="Doc")
    content = b"alpha\n"
    sha = hashlib.sha256(content).hexdigest()
    intent = source_service.begin_upload(
        db_session,
        ctx,
        storage,
        source_id=created.source_id,
        filename="a.txt",
        content_type="text/plain",
        byte_count=len(content),
        sha256=sha,
    )
    storage.put_bytes(
        object_key=intent.object_key,
        data=content,
        content_type="text/plain",
        account_id=bundle.account_id,
        sha256=sha,
    )
    first = source_service.complete_upload(
        db_session,
        ctx,
        storage,
        source_id=created.source_id,
        upload_id=intent.upload_id,
    )
    job = source_service.reprocess_revision(
        db_session,
        ctx,
        source_id=created.source_id,
        revision_id=first.revision_id,
        shadow=True,
    )
    assert job.job_id is not None
    revisions = source_service.list_revisions(db_session, ctx, source_id=created.source_id)
    assert len(revisions) == 1
    assert revisions[0].id == first.revision_id
