"""Signed job auth snapshots: tamper, expiry, revocation, wrong space."""

from __future__ import annotations

import time
import uuid

import pytest
from factories import create_account_bundle
from memdot_core.jobs.auth_snapshot import (
    auth_snapshot_from_context,
    validate_auth_snapshot,
    verify_snapshot_signature,
)
from memdot_core.request_context import RequestContext
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("truncate_tables")

KEY = b"test-job-auth-snapshot-key-32b!!"


@pytest.fixture(autouse=True)
def _keys(monkeypatch):
    monkeypatch.setenv(
        "CORE_TENANT_CONTEXT_SIGNING_KEY", "test-tenant-context-signing-key-32-bytes"
    )
    monkeypatch.setenv("CORE_JOB_AUTH_SNAPSHOT_KEY", KEY.decode())
    monkeypatch.setenv("CORE_SESSION_SIGNING_PEPPER", "test-session-pepper-16xxxxxxxx")


def _ctx(bundle, *, space_id: uuid.UUID | None = None) -> RequestContext:
    return RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
        scopes=frozenset(),
        eligible_space_ids=frozenset({space_id} if space_id else ()),
    )


def test_snapshot_round_trip(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    db_session.commit()
    snap = auth_snapshot_from_context(_ctx(bundle, space_id=space_id), space_id=space_id, key=KEY)
    assert verify_snapshot_signature(snap, key=KEY)
    assert validate_auth_snapshot(
        db_session, account_id=bundle.account_id, snapshot=snap, expected_space_id=space_id, key=KEY
    )


def test_tamper_rejected(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    db_session.commit()
    snap = auth_snapshot_from_context(_ctx(bundle, space_id=space_id), space_id=space_id, key=KEY)
    snap["actor_id"] = str(new_uuid7())
    assert not verify_snapshot_signature(snap, key=KEY)
    assert not validate_auth_snapshot(
        db_session, account_id=bundle.account_id, snapshot=snap, key=KEY
    )


def test_expiry_rejected(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    db_session.commit()
    now = int(time.time()) - 10
    snap = auth_snapshot_from_context(
        _ctx(bundle, space_id=space_id),
        space_id=space_id,
        ttl_seconds=1,
        now=now,
        key=KEY,
    )
    assert not verify_snapshot_signature(snap, key=KEY, now=int(time.time()))


def test_wrong_space_rejected(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    other_space = new_uuid7()
    db_session.commit()
    snap = auth_snapshot_from_context(_ctx(bundle, space_id=space_id), space_id=space_id, key=KEY)
    assert not validate_auth_snapshot(
        db_session,
        account_id=bundle.account_id,
        snapshot=snap,
        expected_space_id=other_space,
        key=KEY,
    )


def test_revoked_actor_rejected(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    spare_actor = new_uuid7()
    db_session.execute(
        text("INSERT INTO actor (id, account_id, kind) VALUES (:id, :aid, 'user')"),
        {"id": spare_actor, "aid": bundle.account_id},
    )
    ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=spare_actor,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )
    snap = auth_snapshot_from_context(ctx, space_id=space_id, key=KEY)
    db_session.execute(text("DELETE FROM actor WHERE id = :id"), {"id": spare_actor})
    db_session.commit()
    assert not validate_auth_snapshot(
        db_session, account_id=bundle.account_id, snapshot=snap, key=KEY
    )


def test_tombstoned_source_rejected(db_session) -> None:
    from memdot_core.deletion import service as deletion_service

    bundle, space_id = create_account_bundle(db_session)
    source_id = new_uuid7()
    db_session.execute(
        text(
            """
            INSERT INTO source (id, account_id, space_id, title, processing_status)
            VALUES (:id, :aid, :space, 's', 'draft')
            """
        ),
        {"id": source_id, "aid": bundle.account_id, "space": space_id},
    )
    ctx = _ctx(bundle, space_id=space_id)
    deletion_service.create_tombstone(
        db_session, ctx, entity_type="source", entity_id=source_id, space_id=space_id
    )
    db_session.commit()
    snap = auth_snapshot_from_context(
        ctx,
        space_id=space_id,
        resource_ids={"source_id": str(source_id)},
        key=KEY,
    )
    assert not validate_auth_snapshot(
        db_session, account_id=bundle.account_id, snapshot=snap, key=KEY
    )
