"""SQLAlchemy engine and session helpers."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from memdot_core.db.tenant import reset_tenant_context


def normalize_database_url(database_url: str) -> str:
    """Accept postgres:// / postgresql:// URLs; force SQLAlchemy psycopg dialect."""
    raw = database_url.strip()
    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://") and "+psycopg" not in raw:
        return "postgresql+psycopg://" + raw[len("postgresql://") :]
    return raw


def create_core_engine(database_url: str, *, pool_pre_ping: bool = True) -> Engine:
    engine = create_engine(normalize_database_url(database_url), pool_pre_ping=pool_pre_ping)

    @event.listens_for(engine, "checkout")
    def _reset_on_checkout(
        dbapi_conn: object, connection_record: object, connection_proxy: object
    ) -> None:
        del dbapi_conn, connection_record, connection_proxy
        # Pool checkout reset happens at ORM layer; connection-level reset in tests.

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, autocommit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        reset_tenant_context(session)
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        reset_tenant_context(session)
        session.close()
