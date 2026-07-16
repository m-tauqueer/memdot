"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session, sessionmaker

from memdot_core.auth.oidc import OidcIssuerAdapter
from memdot_core.db.session import create_core_engine, create_session_factory
from memdot_core.settings import CoreSettings

_engine = None
_session_factory: sessionmaker[Session] | None = None


def _ensure_factory(settings: CoreSettings) -> sessionmaker[Session]:
    global _engine, _session_factory
    if _session_factory is None:
        _engine = create_core_engine(settings.database_url)
        _session_factory = create_session_factory(_engine)
    return _session_factory


def get_settings(request: Request) -> CoreSettings:
    return request.app.state.settings


def get_db_session(request: Request) -> Generator[Session, None, None]:
    settings: CoreSettings = request.app.state.settings
    factory = _ensure_factory(settings)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        from memdot_core.db.tenant import reset_tenant_context

        reset_tenant_context(session)
        session.close()


def get_oidc_adapter(request: Request) -> OidcIssuerAdapter:
    settings: CoreSettings = request.app.state.settings
    return OidcIssuerAdapter(
        issuer=settings.oidc_issuer,
        audience=settings.oidc_audience,
        hosted_google_only=settings.is_hosted(),
    )
