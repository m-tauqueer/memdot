"""Browser session management with hashed secrets and CSRF."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from memdot_domain.ids import new_uuid7


@dataclass(frozen=True)
class SessionMaterial:
    session_id: uuid.UUID
    secret: str
    csrf_token: str


@dataclass(frozen=True)
class SessionCookieNames:
    session: str = "memdot_session"
    csrf: str = "memdot_csrf"
    oidc_state: str = "memdot_oidc_state"


def _hash_secret(value: str) -> str:
    pepper = os.environ.get("CORE_SESSION_SIGNING_PEPPER", "")
    if len(pepper) < 16:
        raise RuntimeError("CORE_SESSION_SIGNING_PEPPER must contain at least 16 characters")
    return hmac.new(pepper.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def new_session_material() -> SessionMaterial:
    return SessionMaterial(
        session_id=new_uuid7(),
        secret=secrets.token_urlsafe(48),
        csrf_token=secrets.token_urlsafe(32),
    )


def session_expiry(
    *, now: datetime | None = None, ttl_hours: int = 24, idle_minutes: int = 60
) -> tuple[datetime, datetime]:
    current = now or datetime.now(UTC)
    return current + timedelta(hours=ttl_hours), current + timedelta(minutes=idle_minutes)


def verify_session_secret(secret: str, secret_hash: str) -> bool:
    return hmac.compare_digest(_hash_secret(secret), secret_hash)


def verify_csrf_token(token: str, token_hash: str) -> bool:
    return hmac.compare_digest(_hash_secret(token), token_hash)


def hash_secret(secret: str) -> str:
    return _hash_secret(secret)


def encrypt_ephemeral_secret(value: str) -> str:
    """Encrypt short-lived auth material with the configured session pepper."""
    pepper = os.environ.get("CORE_SESSION_SIGNING_PEPPER", "")
    if len(pepper) < 16:
        raise RuntimeError("CORE_SESSION_SIGNING_PEPPER must contain at least 16 characters")
    key = hashlib.sha256(pepper.encode("utf-8")).digest()
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), b"memdot-oidc-pkce-v1")
    return urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_ephemeral_secret(value: str) -> str:
    pepper = os.environ.get("CORE_SESSION_SIGNING_PEPPER", "")
    if len(pepper) < 16:
        raise RuntimeError("CORE_SESSION_SIGNING_PEPPER must contain at least 16 characters")
    raw = urlsafe_b64decode(value.encode("ascii"))
    if len(raw) < 13:
        raise ValueError("invalid encrypted auth material")
    key = hashlib.sha256(pepper.encode("utf-8")).digest()
    return AESGCM(key).decrypt(raw[:12], raw[12:], b"memdot-oidc-pkce-v1").decode("utf-8")


def is_session_active(
    *,
    expires_at: datetime,
    idle_expires_at: datetime,
    revoked_at: datetime | None,
    now: datetime | None = None,
) -> bool:
    current = now or datetime.now(UTC)
    if revoked_at is not None:
        return False
    return current <= expires_at and current <= idle_expires_at


def recent_auth_satisfied(
    last_auth_at: datetime, *, max_age_minutes: int = 15, now: datetime | None = None
) -> bool:
    current = now or datetime.now(UTC)
    return current - last_auth_at <= timedelta(minutes=max_age_minutes)
