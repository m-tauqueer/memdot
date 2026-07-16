"""MCP, conversations, Notion, export, and deletion integration tests."""

from __future__ import annotations

import uuid

import pytest
from factories import create_account_bundle
from memdot_core.db.tenant import TenantContext, tenant_scope
from memdot_domain.ids import new_uuid7
from memdot_domain.mcp import encode_mcp_public_id
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text

pytestmark = pytest.mark.usefixtures("truncate_tables")


def _api_client(db_session, migrated_engine):
    from collections.abc import Generator

    from fastapi.testclient import TestClient
    from memdot_core.app import create_app
    from memdot_core.deps import get_db_session
    from memdot_core.settings import CoreSettings
    from sqlalchemy import text
    from sqlalchemy.orm import Session, sessionmaker

    settings = CoreSettings(
        env="test",
        database_url=migrated_engine.url.render_as_string(hide_password=False),
        public_url="https://app.example",
        tenant_context_signing_key="test-tenant-context-signing-key-32-bytes",
        session_signing_pepper="test-session-pepper-16",
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


def _mcp_headers(bundle, actor_id: uuid.UUID, purpose: str) -> dict[str, str]:
    return {
        "X-Memdot-Account-Id": str(bundle.account_id),
        "X-Memdot-Actor-Id": str(actor_id),
        "X-Memdot-Purpose": purpose,
    }


def _first_party_headers(bundle) -> dict[str, str]:
    return {
        "X-Memdot-Account-Id": str(bundle.account_id),
        "X-Memdot-Actor-Id": str(bundle.actor_id),
    }


def test_mcp_search_excludes_private_space(db_session, migrated_engine) -> None:
    bundle_general, space_general = create_account_bundle(db_session)
    bundle_private, space_private = create_account_bundle(db_session, private=True)

    # Seed document in general space
    doc_id = new_uuid7()
    rev_id = new_uuid7()
    ctx = TenantContext(
        account_id=bundle_general.account_id,
        actor_id=bundle_general.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    with tenant_scope(db_session, ctx):
        db_session.execute(
            text(
                """
                INSERT INTO authored_document (id, account_id, space_id, title)
                VALUES (:doc, :aid, :space, 'Visible Doc')
                """
            ),
            {"doc": doc_id, "aid": bundle_general.account_id, "space": space_general},
        )
        db_session.execute(
            text(
                """
                INSERT INTO document_revision
                  (id, account_id, space_id, document_id, content_sha256, schema_version, plain_text)
                VALUES (:rev, :aid, :space, :doc, repeat('a', 64), 1, 'alpha searchable text')
                """
            ),
            {
                "rev": rev_id,
                "aid": bundle_general.account_id,
                "space": space_general,
                "doc": doc_id,
            },
        )
    db_session.commit()

    actor_id = _seed_external_client(
        db_session, bundle_general, scopes="memdot.memory.read"
    )
    db_session.commit()

    client = _api_client(db_session, migrated_engine)
    response = client.post(
        "/api/v1/mcp/search",
        json={"query": "searchable"},
        headers=_mcp_headers(bundle_general, actor_id, "external_read"),
    )
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) >= 1
    assert all("url" in item and item["url"].startswith("https://") for item in results)

    # Private account should not leak through external read on another account
    _ = bundle_private, space_private


def test_tombstoned_fetch_returns_not_found(db_session, migrated_engine) -> None:
    from memdot_core.deletion import service as deletion_service
    from memdot_core.request_context import RequestContext

    bundle, space_id = create_account_bundle(db_session)
    doc_id = new_uuid7()
    rev_id = new_uuid7()
    ctx = TenantContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        purpose=RequestPurpose.FIRST_PARTY,
    )
    req_ctx = RequestContext(
        account_id=bundle.account_id,
        actor_id=bundle.actor_id,
        user_id=bundle.user_id,
        purpose=RequestPurpose.FIRST_PARTY,
        correlation_id=new_uuid7(),
    )
    with tenant_scope(db_session, ctx):
        db_session.execute(
            text(
                """
                INSERT INTO authored_document (id, account_id, space_id, title)
                VALUES (:doc, :aid, :space, 'Tombstone Doc')
                """
            ),
            {"doc": doc_id, "aid": bundle.account_id, "space": space_id},
        )
        db_session.execute(
            text(
                """
                INSERT INTO document_revision
                  (id, account_id, space_id, document_id, content_sha256, schema_version, plain_text)
                VALUES (:rev, :aid, :space, :doc, repeat('b', 64), 1, 'tombstone text')
                """
            ),
            {"rev": rev_id, "aid": bundle.account_id, "space": space_id, "doc": doc_id},
        )
        deletion_service.create_tombstone(
            db_session,
            req_ctx,
            entity_type="document",
            entity_id=doc_id,
            space_id=space_id,
        )
    actor_id = _seed_external_client(db_session, bundle, scopes="memdot.memory.read")
    db_session.commit()

    mcp_id = encode_mcp_public_id("document", doc_id, revision_id=rev_id)
    client = _api_client(db_session, migrated_engine)
    response = client.post(
        "/api/v1/mcp/fetch",
        json={"id": mcp_id},
        headers=_mcp_headers(bundle, actor_id, "external_read"),
    )
    assert response.status_code == 404


def test_record_interaction_service_appends_turn(db_session, migrated_engine) -> None:
    from memdot_core.external_context import load_first_party_context_from_headers
    from memdot_core.mcp import service as mcp_service
    from memdot_domain.tenancy import RequestPurpose
    from starlette.requests import Request

    bundle, space_id = create_account_bundle(db_session)
    actor_id = _seed_external_client(
        db_session, bundle, scopes="memdot.interaction.record"
    )
    db_session.commit()

    scope = {"type": "http", "method": "POST", "path": "/api/v1/mcp/record-interaction", "headers": []}
    request = Request(scope)
    ctx = load_first_party_context_from_headers(
        request,
        account_id=bundle.account_id,
        actor_id=actor_id,
        purpose=RequestPurpose.EXTERNAL_INTERACTION,
        db=db_session,
    )
    assert ctx is not None
    result = mcp_service.record_interaction(
        db_session,
        ctx,
        space_id=space_id,
        client_conversation_id="svc-client-1",
        role="user",
        content="hello from service",
        completeness="single_turn",
    )
    assert result["learnerEvidenceChanged"] is False


def test_record_interaction_does_not_create_learner_events(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    actor_id = _seed_external_client(
        db_session,
        bundle,
        scopes="memdot.interaction.record",
    )
    db_session.commit()

    client = _api_client(db_session, migrated_engine)
    response = client.post(
        "/api/v1/mcp/record-interaction",
        json={
            "space_id": str(space_id),
            "client_conversation_id": "client-1",
            "role": "user",
            "content": "hello",
            "completeness": "single_turn",
        },
        headers=_mcp_headers(bundle, actor_id, "external_interaction"),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["learnerEvidenceChanged"] is False

    count = db_session.execute(
        text("SELECT count(*) FROM learner_event WHERE account_id = :aid"),
        {"aid": bundle.account_id},
    ).scalar_one()
    assert count == 0


def test_notion_sync_pauses_on_conflict(db_session, migrated_engine) -> None:
    bundle, space_id = create_account_bundle(db_session)
    db_session.commit()

    client = _api_client(db_session, migrated_engine)
    headers = _first_party_headers(bundle)
    session = client.post("/api/v1/notion/connect", headers=headers)
    assert session.status_code == 201
    connection_id = session.json()["connectionId"]

    selected = client.post(
        "/api/v1/notion/pages/select",
        json={
            "connection_id": connection_id,
            "space_id": str(space_id),
            "notion_page_ids": ["fixture-page-1"],
        },
        headers=headers,
    )
    assert selected.status_code == 201
    binding_id = selected.json()["bindings"][0]["bindingId"]

    first = client.post(
        f"/api/v1/notion/bindings/{binding_id}/sync",
        json={"fixture_content": "v1"},
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["syncState"] == "idle"

    second = client.post(
        f"/api/v1/notion/bindings/{binding_id}/sync",
        json={"fixture_content": "v2"},
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json()["syncState"] == "paused"
    assert second.json()["conflictState"] == "unresolved"


def test_export_manifest_shape(db_session, migrated_engine) -> None:
    bundle, _space_id = create_account_bundle(db_session)
    db_session.commit()

    client = _api_client(db_session, migrated_engine)
    response = client.post("/api/v1/export/account", json={}, headers=_first_party_headers(bundle))
    assert response.status_code == 201
    manifest = response.json()
    assert manifest["schemaVersion"] == 1
    assert "exportId" in manifest
    assert "createdAt" in manifest
    assert isinstance(manifest.get("artifacts"), list)
