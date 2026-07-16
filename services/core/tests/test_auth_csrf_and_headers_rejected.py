"""First-party auth must be session+CSRF; identity headers are rejected."""

from __future__ import annotations

import os

import pytest
from factories import create_account_bundle
from session_helpers import ensure_session_pepper, mint_session_cookies

pytestmark = pytest.mark.usefixtures("truncate_tables")


def _api_client(migrated_engine):
    from collections.abc import Generator

    from fastapi.testclient import TestClient
    from memdot_core.app import create_app
    from memdot_core.deps import get_db_session
    from memdot_core.settings import CoreSettings
    from sqlalchemy import text
    from sqlalchemy.orm import Session, sessionmaker

    ensure_session_pepper()
    settings = CoreSettings(
        env="test",
        database_url=migrated_engine.url.render_as_string(hide_password=False),
        tenant_context_signing_key="test-tenant-context-signing-key-32-bytes",
        session_signing_pepper="test-session-pepper-16xxxxxxxx",
        mcp_service_secret="test-mcp-service-secret-32bytes-xx",
    )
    app = create_app(settings)
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    def _db() -> Generator[Session, None, None]:
        session = factory()
        session.execute(text("SET ROLE memdot_core"))
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            try:
                session.execute(text("RESET ROLE"))
            except Exception:
                session.rollback()
            session.close()

    app.dependency_overrides[get_db_session] = _db
    return TestClient(app)


def test_identity_headers_rejected_for_first_party(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    db_session.commit()
    client = _api_client(migrated_engine)
    response = client.post(
        "/api/v1/conversations",
        json={"space_id": str(space_id), "source_client": "native"},
        headers={
            "X-Memdot-Account-Id": str(bundle.account_id),
            "X-Memdot-Actor-Id": str(bundle.actor_id),
            "X-Memdot-Purpose": "first_party",
        },
    )
    assert response.status_code in {401, 404}


def test_missing_csrf_rejects_mutating_session(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    cookies, _headers = mint_session_cookies(
        db_session,
        account_id=bundle.account_id,
        user_id=bundle.user_id,
        actor_id=bundle.actor_id,
    )
    db_session.commit()
    client = _api_client(migrated_engine)
    for key, value in cookies.items():
        client.cookies.set(key, value)
    response = client.post(
        "/api/v1/conversations",
        json={"space_id": str(space_id), "source_client": "native"},
    )
    assert response.status_code in {401, 404}


def test_session_with_csrf_succeeds(db_session, migrated_engine) -> None:
    os.environ["CORE_SESSION_SIGNING_PEPPER"] = "test-session-pepper-16xxxxxxxx"
    bundle, space_id = create_account_bundle(db_session)
    cookies, headers = mint_session_cookies(
        db_session,
        account_id=bundle.account_id,
        user_id=bundle.user_id,
        actor_id=bundle.actor_id,
    )
    db_session.commit()
    client = _api_client(migrated_engine)
    for key, value in cookies.items():
        client.cookies.set(key, value)
    response = client.post(
        "/api/v1/conversations",
        json={"space_id": str(space_id), "source_client": "native"},
        headers=headers,
    )
    assert response.status_code == 201
    assert "conversationId" in response.json()
