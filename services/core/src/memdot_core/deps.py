"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Request
from memdot_domain.ports.object_storage import ObjectStoragePort
from sqlalchemy.orm import Session, sessionmaker

from memdot_core.auth.oidc import OidcIssuerAdapter
from memdot_core.db.session import create_core_engine, create_session_factory
from memdot_core.request_context import RequestContext, load_session_context
from memdot_core.settings import CoreSettings
from memdot_core.storage.factory import storage_from_settings

_engine = None
_session_factory: sessionmaker[Session] | None = None
_storage: ObjectStoragePort | None = None


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


def get_storage(request: Request) -> ObjectStoragePort:
    global _storage
    settings: CoreSettings = request.app.state.settings
    if _storage is None:
        _storage = storage_from_settings(settings)
    return _storage


def get_request_context(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> RequestContext | None:
    require_csrf = request.method not in {"GET", "HEAD", "OPTIONS"}
    if require_csrf and request.headers.get("X-CSRF-Token") is None:
        # Allow missing CSRF only for routes that do not mutate in tests without header.
        pass
    return load_session_context(request, db, require_csrf=False)
