"""Shared PostgreSQL pytest fixtures."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from memdot_core.db.tenant import reset_tenant_context
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _database_url_from_env() -> str | None:
    return os.environ.get("MEMDOT_TEST_DATABASE_URL") or os.environ.get("TEST_DATABASE_URL")


@pytest.fixture(scope="session")
def pg_engine() -> Generator[Engine, None, None]:
    url = _database_url_from_env()
    container = None
    if url is None:
        from testcontainers.postgres import PostgresContainer

        container = PostgresContainer("postgres:16-alpine")
        container.start()
        url = container.get_connection_url(driver="psycopg")
    engine = create_engine(url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield engine
    engine.dispose()
    if container is not None:
        container.stop()


@pytest.fixture(scope="session")
def migrated_engine(pg_engine: Engine) -> Generator[Engine, None, None]:
    import warnings

    url = pg_engine.url.render_as_string(hide_password=False)
    os.environ["MEMDOT_MIGRATION_DATABASE_URL"] = url
    signing_key = "test-tenant-context-signing-key-32-bytes"
    os.environ["MEMDOT_TENANT_CONTEXT_SIGNING_KEY"] = signing_key
    os.environ["CORE_TENANT_CONTEXT_SIGNING_KEY"] = signing_key
    os.environ["CORE_SESSION_SIGNING_PEPPER"] = "test-session-signing-pepper-32bytes"
    from alembic import command
    from alembic.config import Config

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "services", "core"))
    cfg = Config(os.path.join(root, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(root, "alembic"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        command.upgrade(cfg, "head")
    yield pg_engine


@pytest.fixture
def db_session(migrated_engine: Engine) -> Generator[Session, None, None]:
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)
    session = factory()
    reset_tenant_context(session)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if session.in_transaction():
            session.rollback()
        reset_tenant_context(session)
        session.close()


@pytest.fixture
def truncate_tables(migrated_engine: Engine) -> Generator[None, None, None]:
    from memdot_core.db.registry import ACCOUNT_OWNED_TABLES

    tables = ", ".join(f'"{t}"' if t == "user" else t for t in sorted(ACCOUNT_OWNED_TABLES))
    with migrated_engine.begin() as conn:
        conn.execute(text("RESET ROLE"))
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        # Also clear non-account auth challenge tables
        conn.execute(
            text("TRUNCATE oidc_login_challenge, oidc_token_replay RESTART IDENTITY CASCADE")
        )
    yield
    with migrated_engine.begin() as conn:
        conn.execute(text("RESET ROLE"))
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        conn.execute(
            text("TRUNCATE oidc_login_challenge, oidc_token_replay RESTART IDENTITY CASCADE")
        )
