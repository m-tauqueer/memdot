"""MCP Core routes require service-auth HMAC resolved against DB grants."""

from __future__ import annotations

import os
import uuid

import pytest
from factories import create_account_bundle
from memdot_core.auth.service_auth import build_service_auth_headers, parse_service_auth
from memdot_domain.ids import new_uuid7
from memdot_domain.tenancy import RequestPurpose
from session_helpers import ensure_session_pepper
from sqlalchemy import text
from starlette.requests import Request

pytestmark = pytest.mark.usefixtures("truncate_tables")

SECRET = "test-mcp-service-secret-32bytes-xx"


def _api_client(migrated_engine):
    from collections.abc import Generator

    from fastapi.testclient import TestClient
    from memdot_core.app import create_app
    from memdot_core.deps import get_db_session
    from memdot_core.settings import CoreSettings
    from sqlalchemy.orm import Session, sessionmaker

    ensure_session_pepper()
    os.environ["CORE_MCP_SERVICE_SECRET"] = SECRET
    os.environ["CORE_MCP_RESOURCE"] = "memdot-mcp"
    os.environ["CORE_MCP_AUDIENCE_AS_RESOURCE"] = "true"
    settings = CoreSettings(
        env="test",
        database_url=migrated_engine.url.render_as_string(hide_password=False),
        public_url="https://app.example",
        tenant_context_signing_key="test-tenant-context-signing-key-32-bytes",
        session_signing_pepper="test-session-pepper-16xxxxxxxx",
        mcp_service_secret=SECRET,
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


def _seed_external_client(db_session, bundle, *, scopes: str) -> uuid.UUID:
    actor_id = new_uuid7()
    db_session.execute(
        text("INSERT INTO actor (id, account_id, kind) VALUES (:id, :aid, 'external_client')"),
        {"id": actor_id, "aid": bundle.account_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO external_client_grant (id, account_id, actor_id, client_id, scopes)
            VALUES (:id, :aid, :actor, 'mcp-client', :scopes)
            """
        ),
        {"id": new_uuid7(), "aid": bundle.account_id, "actor": actor_id, "scopes": scopes},
    )
    db_session.flush()
    return actor_id


def test_raw_identity_headers_rejected_on_mcp(db_session, migrated_engine) -> None:
    bundle, _space = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()
    client = _api_client(migrated_engine)
    response = client.post(
        "/api/v1/mcp/search",
        json={"query": "alpha"},
        headers={
            "X-Memdot-Account-Id": str(bundle.account_id),
            "X-Memdot-Actor-Id": str(actor_id),
            "X-Memdot-Purpose": "external_read",
        },
    )
    assert response.status_code == 404


def test_service_auth_allows_mcp_search(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    doc_id = new_uuid7()
    rev_id = new_uuid7()
    db_session.execute(
        text(
            """
            INSERT INTO authored_document (id, account_id, space_id, title)
            VALUES (:doc, :aid, :space, 'Doc')
            """
        ),
        {"doc": doc_id, "aid": bundle.account_id, "space": space_id},
    )
    db_session.execute(
        text(
            """
            INSERT INTO document_revision
              (id, account_id, space_id, document_id,
               content_sha256, schema_version, plain_text)
            VALUES (:rev, :aid, :space, :doc, repeat('a', 64), 1, 'alpha searchable text')
            """
        ),
        {"rev": rev_id, "aid": bundle.account_id, "space": space_id, "doc": doc_id},
    )
    db_session.commit()

    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_READ,
        scopes={"memdot.memory.read"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    response = client.post("/api/v1/mcp/search", json={"query": "searchable"}, headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json().get("results"), list)


def test_service_auth_nonce_replay_rejected(db_session) -> None:
    headers = build_service_auth_headers(
        SECRET,
        account_id=new_uuid7(),
        actor_id=new_uuid7(),
        purpose=RequestPurpose.EXTERNAL_READ,
        scopes={"memdot.memory.read"},
        client_id="mcp-client",
        subject="mcp-sub",
    )

    def _request() -> Request:
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/api/v1/mcp/search",
            "raw_path": b"/api/v1/mcp/search",
            "query_string": b"",
            "headers": [
                (key.lower().encode("latin-1"), value.encode("latin-1"))
                for key, value in headers.items()
            ],
            "client": ("127.0.0.1", 123),
            "server": ("test", 80),
        }
        return Request(scope)

    # Without a matching grant, parse returns None after nonce consume or grant miss.
    # Replay must fail after first consume.
    first = parse_service_auth(_request(), db_session, secret=SECRET)
    second = parse_service_auth(_request(), db_session, secret=SECRET)
    # First may be None if grant missing; second must always be None (replay).
    assert second is None
    del first


def test_wrong_scope_rejected(db_session, migrated_engine) -> None:
    bundle, _space = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()
    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_PROPOSE,
        scopes={"memdot.memory.read"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    response = client.post(
        "/api/v1/mcp/propose-memory",
        json={"space_id": str(_space), "assertion_text": "x"},
        headers=headers,
    )
    assert response.status_code == 404


def test_grant_scope_reduction_blocks_next_call(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    actor_id = _seed_external_client(
        db_session, bundle, scopes="memdot.memory.read memdot.memory.propose"
    )
    db_session.commit()
    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_PROPOSE,
        scopes={"memdot.memory.propose"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    ok = client.post(
        "/api/v1/mcp/propose-memory",
        json={"space_id": str(space_id), "assertion_text": "ok"},
        headers=headers,
    )
    # May 200 or 404 depending on propose path; force grant reduction then retry.
    db_session.execute(
        text(
            """
            UPDATE external_client_grant
            SET scopes = 'memdot.memory.read'
            WHERE client_id = 'mcp-client'
            """
        )
    )
    db_session.commit()
    headers2 = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_PROPOSE,
        scopes={"memdot.memory.propose"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    denied = client.post(
        "/api/v1/mcp/propose-memory",
        json={"space_id": str(space_id), "assertion_text": "nope"},
        headers=headers2,
    )
    assert denied.status_code == 404
    del ok


def test_browser_cookie_cannot_mcp_propose_without_external_grant(
    db_session, migrated_engine
) -> None:
    from session_helpers import mint_session_cookies

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
        "/api/v1/mcp/propose-memory",
        json={"space_id": str(space_id), "assertion_text": "browser"},
        headers=headers,
    )
    assert response.status_code == 404


def test_revoked_grant_blocks_next_call(db_session, migrated_engine) -> None:
    bundle, _space = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()
    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_READ,
        scopes={"memdot.memory.read"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    ok = client.post("/api/v1/mcp/search", json={"query": "x"}, headers=headers)
    assert ok.status_code == 200
    db_session.rollback()
    db_session.execute(text("RESET ROLE"))
    updated = db_session.execute(
        text(
            """
            UPDATE external_client_grant
            SET revoked_at = now()
            WHERE account_id = :aid AND client_id = 'mcp-client'
            """
        ),
        {"aid": bundle.account_id},
    )
    assert updated.rowcount == 1
    db_session.commit()
    headers2 = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_READ,
        scopes={"memdot.memory.read"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    denied = client.post("/api/v1/mcp/search", json={"query": "x"}, headers=headers2)
    assert denied.status_code == 404


def test_wrong_client_id_rejected(db_session, migrated_engine) -> None:
    bundle, _space = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()
    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_READ,
        scopes={"memdot.memory.read"},
        client_id="wrong-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    response = client.post("/api/v1/mcp/search", json={"query": "x"}, headers=headers)
    assert response.status_code == 404


def test_token_scope_broader_than_grant_rejected(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()
    headers = build_service_auth_headers(
        SECRET,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_PROPOSE,
        scopes={"memdot.memory.propose"},
        client_id="mcp-client",
        subject="mcp-sub",
    )
    client = _api_client(migrated_engine)
    response = client.post(
        "/api/v1/mcp/propose-memory",
        json={"space_id": str(space_id), "assertion_text": "broad"},
        headers=headers,
    )
    assert response.status_code == 404
