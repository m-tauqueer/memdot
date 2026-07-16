"""Alembic migration and role gate tests."""

from __future__ import annotations

import os

import pytest
from alembic import command
from alembic.config import Config
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError


def _alembic_config(engine_url: str) -> Config:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "alembic"))
    os.environ["MEMDOT_MIGRATION_DATABASE_URL"] = engine_url
    return cfg


@pytest.mark.usefixtures("truncate_tables")
def test_clean_migration_upgrade(migrated_engine: Engine) -> None:
    inspector = inspect(migrated_engine)
    tables = set(inspector.get_table_names())
    for name in ACCOUNT_OWNED_TABLES:
        assert name in tables


@pytest.mark.usefixtures("truncate_tables")
def test_repeat_migration_is_idempotent(pg_engine: Engine) -> None:
    import warnings

    url = pg_engine.url.render_as_string(hide_password=False)
    cfg = _alembic_config(url)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")


@pytest.mark.usefixtures("truncate_tables")
def test_runtime_role_cannot_create_table(migrated_engine: Engine) -> None:
    with migrated_engine.begin() as conn:
        conn.execute(text("SET ROLE memdot_core"))
        with pytest.raises(ProgrammingError):
            conn.execute(text("CREATE TABLE memdot_runtime_ddl_probe (id int)"))


@pytest.mark.usefixtures("truncate_tables")
def test_rls_force_enabled(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as conn:
        for table in ACCOUNT_OWNED_TABLES:
            row = conn.execute(
                text(
                    """
                    SELECT c.relrowsecurity, c.relforcerowsecurity
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = :table AND n.nspname = 'public'
                    """
                ),
                {"table": table},
            ).one()
            assert row[0] is True
            assert row[1] is True


@pytest.mark.usefixtures("truncate_tables")
def test_missing_tenant_context_denies_select(db_session, migrated_engine) -> None:
    from factories import create_account_bundle

    bundle, _ = create_account_bundle(db_session)
    db_session.commit()
    with migrated_engine.connect() as conn:
        conn.execute(text("SET ROLE memdot_core"))
        count = conn.execute(text("SELECT count(*) FROM account")).scalar()
        conn.execute(text("RESET ROLE"))
        assert count == 0
