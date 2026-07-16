"""FastAPI + PostgreSQL auth route integration tests under runtime role."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from memdot_core.app import create_app
from memdot_core.auth.oidc import OidcIssuerAdapter
from memdot_core.auth.sessions import SessionCookieNames
from memdot_core.deps import get_db_session, get_oidc_adapter
from memdot_core.settings import CoreSettings
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker


def _rsa_keys() -> tuple[str, Any]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return private_pem, private_key


class _StaticJWKClient:
    def __init__(self, private_pem: str) -> None:
        private_key = serialization.load_pem_private_key(private_pem.encode(), password=None)
        public_key = private_key.public_key()
        self._public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def get_signing_key_from_jwt(self, _token: str) -> Any:
        class _Key:
            key = self._public_pem

        return _Key()


@pytest.fixture
def auth_client(migrated_engine, truncate_tables):
    private_pem, _ = _rsa_keys()
    code_tokens: dict[str, str] = {}
    exchanges: list[dict[str, str]] = []

    def token_handler(request: httpx.Request) -> httpx.Response:
        form = {key: values[0] for key, values in parse_qs(request.content.decode()).items()}
        exchanges.append(form)
        token = code_tokens.get(form.get("code", ""))
        if token is None:
            return httpx.Response(400, json={"error": "invalid_grant"})
        return httpx.Response(200, json={"id_token": token})

    http_client = httpx.Client(transport=httpx.MockTransport(token_handler))
    adapter = OidcIssuerAdapter(
        issuer="https://issuer.example",
        audience="memdot-core",
        jwks_client=_StaticJWKClient(private_pem),
        hosted_google_only=True,
        authorization_endpoint="https://issuer.example/authorize",
        token_endpoint="https://issuer.example/token",
        http_client=http_client,
    )
    settings = CoreSettings(
        env="development",
        database_url=migrated_engine.url.render_as_string(hide_password=False),
        oidc_issuer="https://issuer.example",
        oidc_audience="memdot-core",
        session_signing_pepper="test-session-pepper-16",
        tenant_context_signing_key="test-tenant-context-signing-key-32-bytes",
        oidc_client_id="memdot-core",
        oidc_client_secret="test-client-secret",
        oidc_redirect_uri="https://memdot.example/api/v1/auth/oidc/callback",
    )
    app = create_app(settings)
    factory = sessionmaker(bind=migrated_engine, expire_on_commit=False)

    def _db():
        session: Session = factory()
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
    app.dependency_overrides[get_oidc_adapter] = lambda: adapter
    client = TestClient(app)
    client.private_pem = private_pem  # type: ignore[attr-defined]
    client.code_tokens = code_tokens  # type: ignore[attr-defined]
    client.exchanges = exchanges  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        client.close()
        http_client.close()


def _token(private_pem: str, *, nonce: str, subject: str = "user-1", jti: str | None = None) -> str:
    now = int(time.time())
    payload = {
        "iss": "https://issuer.example",
        "aud": "memdot-core",
        "sub": subject,
        "exp": now + 300,
        "iat": now,
        "nonce": nonce,
        "jti": jti or f"jti-{now}-{subject}",
        "identity_provider": "google",
        "email": "user@example.com",
    }
    return jwt.encode(payload, private_pem, algorithm="RS256")


def _begin(auth_client) -> tuple[str, str]:
    begin = auth_client.post("/api/v1/auth/oidc/begin")
    assert begin.status_code == 200
    body = begin.json()
    assert "nonce" not in body
    assert "state" not in body
    query = parse_qs(urlparse(body["authorization_url"]).query)
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    return query["nonce"][0], query["state"][0]


def _authenticate(auth_client, *, subject: str = "user-1", jti: str | None = None):
    nonce, state = _begin(auth_client)
    code = f"code-{subject}-{jti or 'default'}"
    auth_client.code_tokens[code] = _token(
        auth_client.private_pem, nonce=nonce, subject=subject, jti=jti
    )
    response = auth_client.get(
        "/api/v1/auth/oidc/callback",
        params={"code": code, "state": state},
    )
    return response, code, state


@pytest.mark.usefixtures("truncate_tables")
def test_callback_pending_attestation_and_csrf(auth_client) -> None:
    cb, _, _ = _authenticate(auth_client)
    assert cb.status_code == 200
    assert cb.json()["status"] == "authenticated"
    assert auth_client.exchanges[-1]["grant_type"] == "authorization_code"
    assert len(auth_client.exchanges[-1]["code_verifier"]) >= 43

    # CSRF required on attestation
    bad = auth_client.post("/api/v1/auth/attestation", json={"confirmed": True})
    assert bad.status_code == 403

    csrf = auth_client.cookies.get(SessionCookieNames().csrf)
    ok = auth_client.post(
        "/api/v1/auth/attestation",
        json={"confirmed": True},
        headers={"x-csrf-token": csrf},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "active"

    session = auth_client.get("/api/v1/auth/session")
    assert session.status_code == 200
    assert session.json()["authenticated"] is True


@pytest.mark.usefixtures("truncate_tables")
def test_attestation_declined(auth_client) -> None:
    _authenticate(auth_client)
    csrf = auth_client.cookies.get(SessionCookieNames().csrf)
    declined = auth_client.post(
        "/api/v1/auth/attestation",
        json={"confirmed": False},
        headers={"x-csrf-token": csrf},
    )
    assert declined.status_code == 403


@pytest.mark.usefixtures("truncate_tables")
def test_malformed_cookie_returns_401(auth_client) -> None:
    auth_client.cookies.set(SessionCookieNames().session, "not-a-uuid.secret")
    malformed = auth_client.get("/api/v1/auth/session")
    assert malformed.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
def test_logout_revocation(auth_client) -> None:
    _authenticate(auth_client)
    csrf = auth_client.cookies.get(SessionCookieNames().csrf)
    logout = auth_client.post("/api/v1/auth/logout", headers={"x-csrf-token": csrf})
    assert logout.status_code == 200
    again = auth_client.get("/api/v1/auth/session")
    assert again.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
def test_nonce_state_replay_rejected(auth_client) -> None:
    first, code, state = _authenticate(auth_client, jti="unique-jti-1")
    assert first.status_code == 200
    replay = auth_client.get(
        "/api/v1/auth/oidc/callback",
        params={"code": code, "state": state},
    )
    assert replay.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
def test_non_google_rejected(auth_client) -> None:
    nonce, state = _begin(auth_client)
    now = int(time.time())
    payload = {
        "iss": "https://issuer.example",
        "aud": "memdot-core",
        "sub": "user-x",
        "exp": now + 300,
        "iat": now,
        "nonce": nonce,
        "jti": "jti-azure",
        "identity_provider": "azure",
    }
    token = jwt.encode(payload, auth_client.private_pem, algorithm="RS256")
    auth_client.code_tokens["azure-code"] = token
    resp = auth_client.get(
        "/api/v1/auth/oidc/callback",
        params={"code": "azure-code", "state": state},
    )
    assert resp.status_code == 401


@pytest.mark.usefixtures("truncate_tables")
def test_session_rotation(auth_client) -> None:
    _authenticate(auth_client)
    old_session = auth_client.cookies.get(SessionCookieNames().session)
    csrf = auth_client.cookies.get(SessionCookieNames().csrf)
    rotated = auth_client.post("/api/v1/auth/session/rotate", headers={"x-csrf-token": csrf})
    assert rotated.status_code == 200
    new_session = auth_client.cookies.get(SessionCookieNames().session)
    assert new_session != old_session
    assert auth_client.get("/api/v1/auth/session").status_code == 200
