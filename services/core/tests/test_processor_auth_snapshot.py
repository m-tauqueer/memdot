"""Worker effects require a verified signed auth snapshot."""

from __future__ import annotations

import pytest
from factories import create_account_bundle, create_source
from memdot_core.db.tenant import tenant_scope
from memdot_core.jobs.processor import process_claimed_event
from memdot_core.jobs.service import claim_outbox_batch, enqueue_job_with_outbox
from memdot_core.request_context import RequestContext
from memdot_core.storage.s3 import MemoryObjectStorage
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("truncate_tables")


@pytest.fixture(autouse=True)
def _keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "CORE_TENANT_CONTEXT_SIGNING_KEY",
        "test-tenant-context-signing-key-32-bytes",
    )
    monkeypatch.setenv("CORE_JOB_AUTH_SNAPSHOT_KEY", "test-job-auth-snapshot-key-32b!!")
    monkeypatch.setenv("CORE_SESSION_SIGNING_PEPPER", "test-session-signing-pepper-32bytes")


def test_tampered_snapshot_blocks_ingestion(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    source_id = create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    revision_id = new_uuid7()
    ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )
    with tenant_scope(db_session, ctx.tenant()):
        enqueue_job_with_outbox(
            db_session,
            ctx,
            job_type="ingestion.parse",
            space_id=space_id,
            payload={"source_id": str(source_id), "revision_id": str(revision_id)},
            event_type="source.upload_completed",
        )
    db_session.commit()

    # Tamper stored snapshot actor without updating signature.
    from memdot_core.db.models.ledger import DurableJob
    from sqlalchemy import select

    job = db_session.execute(
        select(DurableJob).where(DurableJob.account_id == bundle.account_id)
    ).scalar_one()
    snap = dict(job.auth_snapshot or {})
    snap["actor_id"] = str(new_uuid7())
    job.auth_snapshot = snap
    db_session.commit()

    db_session.execute(text("SET ROLE memdot_test_admin"))
    claimed = claim_outbox_batch(db_session, worker_id="w-tamper", batch_size=1)
    assert len(claimed) == 1
    result = process_claimed_event(db_session, MemoryObjectStorage(), event=claimed[0])
    assert result.acknowledged is False
