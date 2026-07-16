"""Outbox claim and job durability tests."""

from __future__ import annotations

import uuid

from factories import create_account_bundle
from memdot_core.jobs.service import (
    ack_outbox_event,
    claim_outbox_batch,
    enqueue_job_with_outbox,
    payload_sha256,
)
from memdot_core.request_context import RequestContext
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy.orm import Session


def test_outbox_claim_and_ack(db_session: Session, truncate_tables: None) -> None:
    bundle, space_id = create_account_bundle(db_session)
    ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=uuid.uuid4(),
    )
    payload = {"hello": "world"}
    enqueue_job_with_outbox(
        db_session,
        ctx,
        job_type="ingestion.parse",
        space_id=space_id,
        payload=payload,
        event_type="source.upload_completed",
    )
    db_session.commit()
    claimed = claim_outbox_batch(db_session, worker_id="worker-1", batch_size=5, lease_seconds=30)
    assert len(claimed) == 1
    row = claimed[0]
    ok = ack_outbox_event(
        db_session,
        account_id=uuid.UUID(str(row["account_id"])),
        event_id=uuid.UUID(str(row["id"])),
        claim_token=uuid.UUID(str(row["claim_token"])),
    )
    db_session.commit()
    assert ok is True


def test_payload_hash_stable() -> None:
    payload = {"b": 2, "a": 1}
    assert payload_sha256(payload) == payload_sha256({"a": 1, "b": 2})
