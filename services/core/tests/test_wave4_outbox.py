"""Wave 4 outbox and durable job tests."""

from __future__ import annotations

import uuid

from factories import create_account_bundle, create_source
from memdot_core.db.tenant import tenant_scope
from memdot_core.jobs.service import (
    ack_outbox_event,
    claim_outbox_batch,
    complete_job,
    enqueue_job_with_outbox,
    mark_dead_letter,
    retry_delay_seconds,
    start_job_attempt,
)
from memdot_core.request_context import RequestContext
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text


def test_outbox_claim_ack_and_job_lifecycle(db_session, truncate_tables) -> None:
    bundle, space_id = create_account_bundle(db_session)
    source_id = create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=uuid.uuid4(),
    )
    with tenant_scope(db_session, ctx.tenant()):
        job = enqueue_job_with_outbox(
            db_session,
            ctx,
            job_type="ingestion.parse",
            space_id=space_id,
            payload={"source_id": str(source_id), "revision_id": str(uuid.uuid4())},
            event_type="source.upload_completed",
        )
    db_session.commit()

    db_session.execute(text("SET ROLE memdot_test_admin"))
    claimed = claim_outbox_batch(db_session, worker_id="worker-1", batch_size=5, lease_seconds=30)
    assert len(claimed) == 1
    row = claimed[0]
    acked = ack_outbox_event(
        db_session,
        account_id=uuid.UUID(str(row["account_id"])),
        event_id=uuid.UUID(str(row["id"])),
        claim_token=uuid.UUID(str(row["claim_token"])),
    )
    assert acked

    attempt_id = start_job_attempt(db_session, account_id=bundle.account_id, job_id=job.job_id)
    complete_job(
        db_session,
        account_id=bundle.account_id,
        job_id=job.job_id,
        attempt_id=attempt_id,
        succeeded=True,
    )
    mark_dead_letter(db_session, account_id=bundle.account_id, job_id=job.job_id)
    assert retry_delay_seconds(3) >= 8


def test_duplicate_ack_is_idempotent(db_session, truncate_tables) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=uuid.uuid4(),
    )
    with tenant_scope(db_session, ctx.tenant()):
        enqueue_job_with_outbox(
            db_session,
            ctx,
            job_type="ingestion.parse",
            space_id=space_id,
            payload={"source_id": str(uuid.uuid4())},
            event_type="source.upload_completed",
        )
    db_session.commit()
    db_session.execute(text("SET ROLE memdot_test_admin"))
    claimed = claim_outbox_batch(db_session, worker_id="worker-2", batch_size=1, lease_seconds=30)
    row = claimed[0]
    account_id = uuid.UUID(str(row["account_id"]))
    event_id = uuid.UUID(str(row["id"]))
    token = uuid.UUID(str(row["claim_token"]))
    assert ack_outbox_event(db_session, account_id=account_id, event_id=event_id, claim_token=token)
    assert not ack_outbox_event(
        db_session, account_id=account_id, event_id=event_id, claim_token=token
    )
