"""Idempotency replay and conflict tests."""

from __future__ import annotations

import uuid

from factories import create_account_bundle
from memdot_core.idempotency import begin_idempotency, complete_idempotency, fingerprint_request
from sqlalchemy.orm import Session


def test_idempotency_replay(db_session: Session, truncate_tables: None) -> None:
    bundle, _space = create_account_bundle(db_session)
    key = "idem-1"
    fp = fingerprint_request(method="POST", path="/api/v1/sources", body=b"{}")
    first = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key=key,
        fingerprint=fp,
    )
    complete_idempotency(
        db_session,
        record_id=first.record_id,
        account_id=bundle.account_id,
        response_status=201,
        response_body={"sourceId": str(uuid.uuid4())},
    )
    db_session.commit()
    second = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key=key,
        fingerprint=fp,
    )
    assert second.replay is True
    assert second.response_body is not None


def test_idempotency_conflict(db_session: Session, truncate_tables: None) -> None:
    bundle, _space = create_account_bundle(db_session)
    key = "idem-2"
    begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key=key,
        fingerprint=fingerprint_request(method="POST", path="/x", body=b"a"),
    )
    db_session.commit()
    conflict = begin_idempotency(
        db_session,
        account_id=bundle.account_id,
        route="POST /api/v1/sources",
        idempotency_key=key,
        fingerprint=fingerprint_request(method="POST", path="/x", body=b"b"),
    )
    assert conflict.conflict is True
