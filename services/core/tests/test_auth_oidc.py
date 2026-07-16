"""OIDC validation and session security tests."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from memdot_core.auth.oidc import OidcIssuerAdapter, OidcValidationError
from memdot_core.auth.sessions import (
    hash_secret,
    is_session_active,
    new_session_material,
    recent_auth_satisfied,
    verify_session_secret,
)


def _rsa_keys() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


class _StaticJWKClient:
    def __init__(self, private_pem: str) -> None:
        from cryptography.hazmat.primitives import serialization

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


def _token(
    private_pem: str,
    *,
    issuer: str = "https://issuer.example",
    audience: str = "memdot-core",
    subject: str = "user-1",
    nonce: str | None = None,
    expired: bool = False,
    provider_claim: str | None = "google",
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "iss": issuer,
        "aud": audience,
        "sub": subject,
        "exp": now - 10 if expired else now + 300,
        "iat": now,
        "jti": f"jti-{now}",
    }
    if nonce is not None:
        payload["nonce"] = nonce
    if provider_claim is not None:
        payload["identity_provider"] = provider_claim
    return jwt.encode(payload, private_pem, algorithm="RS256")


def test_valid_token() -> None:
    private_pem, _ = _rsa_keys()
    adapter = OidcIssuerAdapter(
        issuer="https://issuer.example",
        audience="memdot-core",
        jwks_client=_StaticJWKClient(private_pem),
        hosted_google_only=True,
    )
    claims = adapter.validate_id_token(
        _token(private_pem, nonce="n1"), expected_nonce="n1", seen_jti=set()
    )
    assert claims.subject == "user-1"
    assert claims.provider == "google"


def test_wrong_audience() -> None:
    private_pem, _ = _rsa_keys()
    adapter = OidcIssuerAdapter(
        issuer="https://issuer.example",
        audience="expected",
        jwks_client=_StaticJWKClient(private_pem),
    )
    token = _token(private_pem, audience="other")
    with pytest.raises(OidcValidationError) as exc:
        adapter.validate_id_token(token)
    assert exc.value.code == "invalid_audience"


def test_expired_token() -> None:
    private_pem, _ = _rsa_keys()
    adapter = OidcIssuerAdapter(
        issuer="https://issuer.example",
        audience="memdot-core",
        jwks_client=_StaticJWKClient(private_pem),
    )
    with pytest.raises(OidcValidationError) as exc:
        adapter.validate_id_token(_token(private_pem, expired=True))
    assert exc.value.code == "token_expired"


def test_non_google_rejected_in_hosted_mode() -> None:
    private_pem, _ = _rsa_keys()
    adapter = OidcIssuerAdapter(
        issuer="https://issuer.example",
        audience="memdot-core",
        jwks_client=_StaticJWKClient(private_pem),
        hosted_google_only=True,
    )
    token = _token(private_pem, provider_claim="azure")
    with pytest.raises(OidcValidationError) as exc:
        adapter.validate_id_token(token)
    assert exc.value.code == "non_google_provider"


def test_session_secret_hash_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CORE_SESSION_SIGNING_PEPPER", "test-session-signing-pepper-32bytes")
    material = new_session_material()
    digest = hash_secret(material.secret)
    assert verify_session_secret(material.secret, digest)
    assert not verify_session_secret("wrong", digest)


def test_session_expiry_and_recent_auth() -> None:
    now = datetime.now(UTC)
    assert is_session_active(
        expires_at=now + timedelta(hours=1),
        idle_expires_at=now + timedelta(minutes=30),
        revoked_at=None,
        now=now,
    )
    assert not is_session_active(
        expires_at=now - timedelta(minutes=1),
        idle_expires_at=now + timedelta(minutes=30),
        revoked_at=None,
        now=now,
    )
    assert recent_auth_satisfied(now - timedelta(minutes=5), now=now)
    assert not recent_auth_satisfied(now - timedelta(minutes=30), now=now)
