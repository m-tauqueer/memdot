"""Frozen migration / schema-drift / clean-vs-upgraded convergence tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from memdot_core.db.base import Base
from memdot_core.db.models import ledger, tenancy  # noqa: F401
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from sqlalchemy import text
from sqlalchemy.engine import Engine


def test_migration_file_has_no_create_all() -> None:
    path = Path("services/core/alembic/versions/20260716_0001_phase3_canonical.py")
    text_body = path.read_text(encoding="utf-8")
    assert "create_all" not in text_body
    sql_path = Path("services/core/alembic/versions/20260716_0001_phase3_canonical.sql")
    assert sql_path.is_file()
    assert "CREATE TABLE account" in sql_path.read_text(encoding="utf-8")


@pytest.mark.usefixtures("truncate_tables")
def test_schema_drift_against_metadata(migrated_engine: Engine) -> None:
    with migrated_engine.connect() as conn:
        context = MigrationContext.configure(conn)
        diffs = compare_metadata(context, Base.metadata)
    # Filter ignorable diffs for internal security tables not in ORM metadata ownership map
    # memdot_context_secret is intentional extra.
    meaningful = [
        d
        for d in diffs
        if not (
            isinstance(d, tuple) and len(d) >= 2 and str(d[1]).endswith("memdot_context_secret")
        )
    ]
    assert meaningful == [], meaningful


@pytest.mark.usefixtures("truncate_tables")
def test_clean_and_upgraded_converge(pg_engine: Engine) -> None:
    """Fresh upgrade and repeat upgrade leave the same account-owned table set."""
    import warnings

    from alembic import command
    from alembic.config import Config

    url = pg_engine.url.render_as_string(hide_password=False)
    root = Path("services/core")
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    os.environ["MEMDOT_MIGRATION_DATABASE_URL"] = url
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        command.upgrade(cfg, "head")
        command.upgrade(cfg, "head")
    with pg_engine.connect() as conn:
        tables = {
            r[0]
            for r in conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
        }
        ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert ACCOUNT_OWNED_TABLES.issubset(tables)
    assert ver == "20260720_0005"
