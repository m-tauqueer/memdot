"""Runtime role privilege and connection identity tests."""

from __future__ import annotations

import pytest
from factories import create_account_bundle
from memdot_core.db.tenant import TenantContext, apply_tenant_context, reset_tenant_context
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError


@pytest.mark.usefixtures("truncate_tables")
def test_runtime_role_identity_and_privileges(migrated_engine) -> None:
    with migrated_engine.connect() as conn:
        conn.execute(text("SET ROLE memdot_core"))
        user = conn.execute(text("SELECT current_user")).scalar()
        assert user == "memdot_core"
        bypass = conn.execute(
            text("SELECT rolbypassrls FROM pg_roles WHERE rolname = current_user")
        ).scalar()
        assert bypass is False
        superuser = conn.execute(
            text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        ).scalar()
        assert superuser is False
        with pytest.raises(ProgrammingError):
            conn.execute(text("CREATE TABLE memdot_runtime_ddl_probe (id int)"))
        conn.rollback()
        # Runtime role must not be a member of migrate/admin roles.
        member = conn.execute(
            text("SELECT pg_has_role('memdot_core', 'memdot_migrate', 'MEMBER')")
        ).scalar()
        assert member is False
        member_admin = conn.execute(
            text("SELECT pg_has_role('memdot_core', 'memdot_test_admin', 'MEMBER')")
        ).scalar()
        assert member_admin is False


@pytest.mark.usefixtures("truncate_tables")
def test_migrate_owns_account_table(migrated_engine) -> None:
    with migrated_engine.connect() as conn:
        owner = conn.execute(
            text(
                """
                SELECT pg_get_userbyid(c.relowner)
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'account'
                """
            )
        ).scalar()
        assert owner == "memdot_migrate"


@pytest.mark.usefixtures("truncate_tables")
def test_runtime_rls_under_compose_style_role(db_session) -> None:
    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    db_session.execute(text("SET ROLE memdot_core"))
    reset_tenant_context(db_session)
    apply_tenant_context(
        db_session,
        TenantContext(
            account_id=bundle.account_id,
            actor_id=bundle.actor_id,
            purpose=RequestPurpose.FIRST_PARTY,
        ),
    )
    count = db_session.execute(text("SELECT count(*) FROM account")).scalar()
    assert count == 1
    user = db_session.execute(text("SELECT current_user")).scalar()
    assert user == "memdot_core"
    reset_tenant_context(db_session)
    db_session.execute(text("RESET ROLE"))
