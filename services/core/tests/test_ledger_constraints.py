"""Ledger immutability and pointer constraint tests."""

from __future__ import annotations

import pytest
from factories import create_account_bundle, create_source
from memdot_core.db.tenant import (
    TenantContext,
    set_current_source_revision,
    tenant_scope,
)
from memdot_domain.ids import deterministic_uuid5, new_uuid7
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


def _create_source_revision(db_session, bundle, space_id, source_id, sha: str):
    revision_id = deterministic_uuid5(source_id, sha)
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    with tenant_scope(db_session, ctx):
        db_session.execute(
            text(
                """
                INSERT INTO source_revision (
                  id, account_id, space_id, source_id, snapshot_sha256, captured_at
                ) VALUES (:id,:account_id,:space_id,:source_id,:sha,now())
                """
            ),
            {
                "id": revision_id,
                "account_id": bundle.account_id,
                "space_id": space_id,
                "source_id": source_id,
                "sha": sha,
            },
        )
    return revision_id, ctx


@pytest.mark.usefixtures("truncate_tables")
def test_immutable_revision_update_rejected(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    source_id = create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    revision_id = deterministic_uuid5(source_id, "a" * 64)
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    with tenant_scope(db_session, ctx):
        db_session.execute(
            text(
                """
                INSERT INTO source_revision (
                  id, account_id, space_id, source_id, snapshot_sha256,
                  captured_at, mime_type
                ) VALUES (
                  :id, :account_id, :space_id, :source_id, :sha,
                  now(), 'application/pdf'
                )
                """
            ),
            {
                "id": revision_id,
                "account_id": bundle.account_id,
                "space_id": space_id,
                "source_id": source_id,
                "sha": "a" * 64,
            },
        )
    db_session.commit()
    with pytest.raises(SQLAlchemyError):
        with tenant_scope(db_session, ctx):
            db_session.execute(
                text("UPDATE source_revision SET mime_type = 'text/plain' WHERE id = :id"),
                {"id": revision_id},
            )
        db_session.commit()


@pytest.mark.usefixtures("truncate_tables")
def test_cross_account_space_attachment_rejected(db_session) -> None:
    bundle_a, space_a = create_account_bundle(db_session)
    bundle_b, _ = create_account_bundle(db_session)
    with pytest.raises(IntegrityError):
        create_source(
            db_session,
            account_id=bundle_b.account_id,
            actor_id=bundle_b.actor_id,
            space_id=space_a,
        )
    db_session.rollback()


@pytest.mark.usefixtures("truncate_tables")
def test_current_pointer_and_outbox_are_atomic_and_idempotent(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    source_id = create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    revision_id, ctx = _create_source_revision(db_session, bundle, space_id, source_id, "b" * 64)
    pointer_id = new_uuid7()
    event_id = new_uuid7()
    kwargs = {
        "pointer_id": pointer_id,
        "account_id": bundle.account_id,
        "space_id": space_id,
        "source_id": source_id,
        "revision_id": revision_id,
        "event_id": event_id,
        "payload_sha256": "c" * 64,
        "payload_json": '{"revision":"current"}',
    }
    with tenant_scope(db_session, ctx):
        set_current_source_revision(db_session, **kwargs)
        set_current_source_revision(db_session, **kwargs)
    db_session.commit()

    assert (
        db_session.execute(
            text("SELECT revision_id FROM current_source_revision WHERE id=:id"),
            {"id": pointer_id},
        ).scalar_one()
        == revision_id
    )
    assert (
        db_session.execute(
            text("SELECT count(*) FROM outbox_event WHERE id=:id"), {"id": event_id}
        ).scalar_one()
        == 1
    )


@pytest.mark.usefixtures("truncate_tables")
def test_current_pointer_rolls_back_with_outbox(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session)
    source_id = create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    revision_id, ctx = _create_source_revision(db_session, bundle, space_id, source_id, "d" * 64)
    pointer_id = new_uuid7()
    event_id = new_uuid7()
    with tenant_scope(db_session, ctx):
        set_current_source_revision(
            db_session,
            pointer_id=pointer_id,
            account_id=bundle.account_id,
            space_id=space_id,
            source_id=source_id,
            revision_id=revision_id,
            event_id=event_id,
            payload_sha256="e" * 64,
            payload_json="{}",
        )
    db_session.rollback()
    assert (
        db_session.execute(
            text("SELECT count(*) FROM current_source_revision WHERE id=:id"),
            {"id": pointer_id},
        ).scalar_one()
        == 0
    )
    assert (
        db_session.execute(
            text("SELECT count(*) FROM outbox_event WHERE id=:id"), {"id": event_id}
        ).scalar_one()
        == 0
    )
