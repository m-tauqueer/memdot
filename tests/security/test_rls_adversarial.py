"""Cross-account and Private Space adversarial suite (full table matrix)."""

from __future__ import annotations

import time

import pytest
from factories import create_account_bundle, create_source, seed_account_owned_graph
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from memdot_core.db.tenant import (
    TenantContext,
    apply_tenant_context,
    reset_tenant_context,
    sign_tenant_context,
)
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose, SpaceVisibility
from rls_helpers import runtime_tenant_scope
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, ProgrammingError

# Explicit registration for check_rls_registry adversarial coverage gate.
REGISTERED_ACCOUNT_OWNED_TABLES = frozenset(
    {
        "account",
        "user",
        "account_member",
        "space",
        "space_member",
        "hosted_adult_attestation",
        "external_identity",
        "actor",
        "browser_session",
        "session_revocation",
        "external_client_grant",
        "operator_bootstrap",
        "source",
        "source_revision",
        "source_blob",
        "authored_document",
        "document_revision",
        "parse_run",
        "document_element",
        "provenance_record",
        "truth_classification",
        "conflict_set",
        "conflict_member",
        "proposal",
        "conversation",
        "conversation_turn",
        "audit_event",
        "current_source_revision",
        "current_document_revision",
        "outbox_event",
        "idempotency_record",
        "durable_job",
        "job_attempt",
        "projection_state",
    }
)


def test_adversarial_registry_covers_all_account_owned_tables() -> None:
    assert REGISTERED_ACCOUNT_OWNED_TABLES == ACCOUNT_OWNED_TABLES


@pytest.mark.usefixtures("truncate_tables")
def test_cross_account_read_returns_zero(db_session) -> None:
    bundle_a, space_a = create_account_bundle(db_session)
    create_source(
        db_session,
        account_id=bundle_a.account_id,
        actor_id=bundle_a.actor_id,
        space_id=space_a,
        title="secret",
    )
    bundle_b, _ = create_account_bundle(db_session)
    db_session.commit()
    ctx_b = TenantContext(
        account_id=bundle_b.account_id,
        actor_id=bundle_b.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    with runtime_tenant_scope(db_session, ctx_b):
        count = db_session.execute(text("SELECT count(*) FROM source")).scalar()
        assert count == 0


@pytest.mark.usefixtures("truncate_tables")
def test_private_space_hidden_from_external_read(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session, private=True)
    create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    db_session.commit()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.EXTERNAL_READ,
    )
    # external_read requires external_client actor + grant
    ext_actor = new_uuid7()
    db_session.execute(
        text(
            """
            INSERT INTO actor (id, account_id, kind, reference_id)
            VALUES (:id, :account_id, 'external_client', NULL)
            """
        ),
        {"id": str(ext_actor), "account_id": str(bundle.account_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO external_client_grant (id, account_id, actor_id, client_id, scopes)
            VALUES (:id, :account_id, :actor_id, 'mcp', 'memdot.memory.read')
            """
        ),
        {
            "id": str(new_uuid7()),
            "account_id": str(bundle.account_id),
            "actor_id": str(ext_actor),
        },
    )
    db_session.commit()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=ext_actor,
        purpose=RequestPurpose.EXTERNAL_READ,
    )
    with runtime_tenant_scope(db_session, ctx):
        spaces = db_session.execute(text("SELECT count(*) FROM space")).scalar()
        sources = db_session.execute(text("SELECT count(*) FROM source")).scalar()
        assert spaces == 0
        assert sources == 0


@pytest.mark.usefixtures("truncate_tables")
def test_external_read_sees_non_private_space(db_session) -> None:
    bundle, space_id = create_account_bundle(db_session, visibility=SpaceVisibility.GENERAL)
    create_source(
        db_session,
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        space_id=space_id,
    )
    ext_actor = new_uuid7()
    db_session.execute(
        text("INSERT INTO actor (id, account_id, kind) VALUES (:id, :aid, 'external_client')"),
        {"id": str(ext_actor), "aid": str(bundle.account_id)},
    )
    db_session.execute(
        text(
            """
            INSERT INTO external_client_grant (id, account_id, actor_id, client_id, scopes)
            VALUES (:id, :aid, :actor, 'mcp', 'memdot.memory.read')
            """
        ),
        {"id": str(new_uuid7()), "aid": str(bundle.account_id), "actor": str(ext_actor)},
    )
    db_session.commit()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=ext_actor,
        purpose=RequestPurpose.EXTERNAL_READ,
    )
    with runtime_tenant_scope(db_session, ctx):
        spaces = db_session.execute(text("SELECT count(*) FROM space")).scalar()
        sources = db_session.execute(text("SELECT count(*) FROM source")).scalar()
        assert spaces == 1
        assert sources == 1


@pytest.mark.usefixtures("truncate_tables")
def test_pooled_context_reset_denies_after_scope(db_session) -> None:
    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    with runtime_tenant_scope(db_session, ctx):
        inside = db_session.execute(text("SELECT count(*) FROM account")).scalar()
        assert inside == 1
    db_session.execute(text("SET ROLE memdot_core"))
    reset_tenant_context(db_session)
    outside = db_session.execute(text("SELECT count(*) FROM account")).scalar()
    db_session.execute(text("RESET ROLE"))
    assert outside == 0


@pytest.mark.usefixtures("truncate_tables")
def test_forged_gucs_without_seal_return_zero(db_session) -> None:
    bundle_a, space_a = create_account_bundle(db_session)
    create_source(
        db_session,
        account_id=bundle_a.account_id,
        actor_id=bundle_a.actor_id,
        space_id=space_a,
    )
    bundle_b, _ = create_account_bundle(db_session)
    db_session.commit()
    db_session.execute(text("SET ROLE memdot_core"))
    # Malicious raw GUC forgery — must not unlock rows without seal.
    db_session.execute(
        text("SELECT set_config('app.account_id', :v, true)"),
        {"v": str(bundle_a.account_id)},
    )
    db_session.execute(
        text("SELECT set_config('app.actor_id', :v, true)"),
        {"v": str(bundle_a.actor_id)},
    )
    db_session.execute(text("SELECT set_config('app.purpose', 'first_party', true)"))
    db_session.execute(text("SELECT set_config('app.context_seal', 'forged', true)"))
    count = db_session.execute(text("SELECT count(*) FROM source")).scalar()
    db_session.execute(text("RESET ROLE"))
    assert count == 0


@pytest.mark.usefixtures("truncate_tables")
def test_signed_context_rejects_altered_account(db_session) -> None:
    bundle_a, _ = create_account_bundle(db_session)
    bundle_b, _ = create_account_bundle(db_session)
    db_session.commit()
    ctx_a = TenantContext(
        account_id=bundle_a.account_id,
        actor_id=bundle_a.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    issued_at = int(time.time())
    nonce = "signed-context-probe"
    signature = sign_tenant_context(ctx_a, issued_at=issued_at, nonce=nonce)
    db_session.execute(text("SET ROLE memdot_core"))
    try:
        with pytest.raises(DBAPIError):
            db_session.execute(
                text(
                    "SELECT memdot_begin_tenant_context("
                    ":account_id,:actor_id,:purpose,:issued_at,:nonce,:signature)"
                ),
                {
                    "account_id": str(bundle_b.account_id),
                    "actor_id": str(bundle_b.actor_id),
                    "purpose": "first_party",
                    "issued_at": issued_at,
                    "nonce": nonce,
                    "signature": signature,
                },
            )
    finally:
        db_session.rollback()
        db_session.execute(text("RESET ROLE"))


@pytest.mark.usefixtures("truncate_tables")
def test_signed_context_rejects_expired_envelope(db_session) -> None:
    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    issued_at = int(time.time()) - 120
    nonce = "expired-context-probe"
    signature = sign_tenant_context(ctx, issued_at=issued_at, nonce=nonce)
    db_session.execute(text("SET ROLE memdot_core"))
    try:
        with pytest.raises(DBAPIError):
            db_session.execute(
                text(
                    "SELECT memdot_begin_tenant_context("
                    ":account_id,:actor_id,:purpose,:issued_at,:nonce,:signature)"
                ),
                {
                    "account_id": str(bundle.account_id),
                    "actor_id": str(bundle.actor_id),
                    "purpose": "first_party",
                    "issued_at": issued_at,
                    "nonce": nonce,
                    "signature": signature,
                },
            )
    finally:
        db_session.rollback()
        db_session.execute(text("RESET ROLE"))


@pytest.mark.usefixtures("truncate_tables")
def test_forged_actor_rejected(db_session) -> None:
    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    fake_actor = new_uuid7()
    db_session.execute(text("SET ROLE memdot_core"))
    try:
        with pytest.raises((ValueError, DBAPIError, ProgrammingError)):
            apply_tenant_context(
                db_session,
                TenantContext(
                    account_id=bundle.account_id,
                    actor_id=fake_actor,
                    purpose=RequestPurpose.FIRST_PARTY,
                ),
            )
            db_session.flush()
    finally:
        db_session.rollback()
        db_session.execute(text("RESET ROLE"))


@pytest.mark.usefixtures("truncate_tables")
def test_migration_purpose_rejected_for_runtime_role(db_session) -> None:
    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    db_session.execute(text("SET ROLE memdot_core"))
    try:
        with pytest.raises((ValueError, DBAPIError, ProgrammingError)):
            apply_tenant_context(
                db_session,
                TenantContext(
                    account_id=bundle.account_id,
                    actor_id=bundle.actor_id,
                    purpose=RequestPurpose.MIGRATION,
                ),
            )
            db_session.flush()
    finally:
        db_session.rollback()
        db_session.execute(text("RESET ROLE"))


@pytest.mark.usefixtures("truncate_tables")
@pytest.mark.parametrize("table", sorted(ACCOUNT_OWNED_TABLES))
def test_matrix_cross_account_existing_row_crud_is_hidden(db_session, table: str) -> None:
    bundle_a, space_a = create_account_bundle(db_session)
    target_ids = seed_account_owned_graph(db_session, bundle_a, space_a)
    bundle_b, _ = create_account_bundle(db_session)
    db_session.commit()
    ctx_b = TenantContext(
        account_id=bundle_b.account_id,
        actor_id=bundle_b.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    sql_table = f'"{table}"' if table == "user" else table
    with runtime_tenant_scope(db_session, ctx_b):
        target = str(target_ids[table])
        rows = db_session.execute(
            text(f"SELECT id FROM {sql_table} WHERE id = :id"), {"id": target}
        ).fetchall()
        assert rows == []
        if table in {"current_source_revision", "current_document_revision"}:
            # Runtime has no direct pointer mutation grants; writes use the
            # atomic pointer-plus-outbox SECURITY DEFINER functions.
            return
        updated = db_session.execute(
            text(f"UPDATE {sql_table} SET account_id=account_id WHERE id=:id"),
            {"id": target},
        )
        deleted = db_session.execute(text(f"DELETE FROM {sql_table} WHERE id=:id"), {"id": target})
        assert updated.rowcount == 0
        assert deleted.rowcount == 0
