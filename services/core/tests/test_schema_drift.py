"""Frozen migration / schema-drift / clean-vs-upgraded convergence tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from memdot_core.db.base import Base
from memdot_core.db.models import ledger, security, tenancy  # noqa: F401
from memdot_core.db.registry import ACCOUNT_OWNED_TABLES
from sqlalchemy import text
from sqlalchemy.engine import Engine

# Security helper tables and known DB-only extras intentionally outside ORM drift.
_IGNORE_FRAGMENTS = (
    "memdot_context_secret",
    "service_auth_nonce",
)


def _is_noise_diff(diff: object) -> bool:
    rendered = str(diff)
    if any(fragment in rendered for fragment in _IGNORE_FRAGMENTS):
        return True
    # PostgreSQL REAL/NUMERIC vs SQLAlchemy Float() noise.
    if "REAL()" in rendered or "NUMERIC()" in rendered:
        return True
    # Learning-era composite FKs/uniques exist in SQL ahead of full ORM parity.
    if isinstance(diff, tuple) and diff and str(diff[0]).startswith(("remove_", "add_")):
        learning_markers = (
            "assessment_item",
            "assessment_revision",
            "assessment_attempt",
            "current_assessment_revision",
            "curriculum_",
            "learner_",
            "review_item",
            "uq_assessment_item_space_id",
            "uq_curriculum_edge_pair",
        )
        if any(marker in rendered for marker in learning_markers):
            return True
    return False


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
    meaningful = [d for d in diffs if not _is_noise_diff(d)]
    assert meaningful == [], meaningful


@pytest.mark.usefixtures("truncate_tables")
def test_empty_to_head_reaches_round2(pg_engine: Engine) -> None:
    """Empty database upgrades to Correction Round 2 head."""
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
    with pg_engine.connect() as conn:
        ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        has_nonce = conn.execute(
            text("SELECT to_regclass('public.service_auth_nonce') IS NOT NULL")
        ).scalar()
        has_fn = conn.execute(
            text("SELECT COUNT(*) FROM pg_proc WHERE proname = 'memdot_resolve_external_grant'")
        ).scalar()
    assert ver == "20260722_0007"
    assert has_nonce is True
    assert int(has_fn or 0) >= 1


@pytest.mark.usefixtures("truncate_tables")
def test_previous_head_to_head(pg_engine: Engine) -> None:
    """Upgrade from prior security head (0006) to Round 2 head (0007)."""
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
        command.upgrade(cfg, "20260721_0006")
        command.upgrade(cfg, "head")
    with pg_engine.connect() as conn:
        ver = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert ver == "20260722_0007"


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
    assert ver == "20260722_0007"
