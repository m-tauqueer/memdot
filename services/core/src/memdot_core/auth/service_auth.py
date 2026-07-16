"""HMAC service-auth envelope for MCP edge → Core calls with durable nonce replay protection."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from fastapi import Request
from memdot_domain.tenancy import RequestPurpose
from sqlalchemy import text
from sqlalchemy.orm import Session

SERVICE_AUTH_VERSION = 1
MAX_SKEW_SECONDS = 300
MIN_SECRET_BYTES = 32
HEADER_VERSION = "X-Memdot-Service-Auth"
HEADER_TS = "X-Memdot-Service-Ts"
HEADER_NONCE = "X-Memdot-Service-Nonce"
HEADER_BODY = "X-Memdot-Service-Body"
HEADER_SIG = "X-Memdot-Service-Sig"


@dataclass(frozen=True)
class ServiceAuthGrant:
    account_id: uuid.UUID
    actor_id: uuid.UUID
    purpose: RequestPurpose
    scopes: frozenset[str]
    client_id: str
    subject: str
    exp: int


def resolve_mcp_service_secret() -> str:
    value = (
        os.environ.get("CORE_MCP_SERVICE_SECRET") or os.environ.get("MCP_CORE_SERVICE_SECRET") or ""
    ).strip()
    return value


def _require_secret(secret: str) -> str:
    if len(secret.encode("utf-8")) < MIN_SECRET_BYTES:
        msg = f"MCP service secret must contain at least {MIN_SECRET_BYTES} bytes"
        raise ValueError(msg)
    return secret


def _b64encode(raw: bytes) -> str:
    return urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(value + padding)


def _sign(secret: str, *, ts: str, nonce: str, body_b64: str) -> str:
    message = f"{ts}.{nonce}.{body_b64}".encode()
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def build_service_auth_headers(
    secret: str,
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    purpose: RequestPurpose,
    scopes: frozenset[str] | set[str] | list[str],
    client_id: str,
    subject: str,
    exp: int | None = None,
    authorization: str | None = None,
    now: int | None = None,
) -> dict[str, str]:
    resolved = _require_secret(secret)
    ts = str(now if now is not None else int(time.time()))
    nonce = secrets.token_hex(16)
    payload: dict[str, Any] = {
        "v": SERVICE_AUTH_VERSION,
        "account_id": str(account_id),
        "actor_id": str(actor_id),
        "purpose": purpose.value,
        "scopes": sorted(scopes),
        "client_id": client_id,
        "sub": subject,
        "exp": exp if exp is not None else int(ts) + 300,
    }
    if authorization:
        payload["authorization_sha256"] = hashlib.sha256(authorization.encode("utf-8")).hexdigest()
    body_b64 = _b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    signature = _sign(resolved, ts=ts, nonce=nonce, body_b64=body_b64)
    return {
        HEADER_VERSION: f"v{SERVICE_AUTH_VERSION}",
        HEADER_TS: ts,
        HEADER_NONCE: nonce,
        HEADER_BODY: body_b64,
        HEADER_SIG: signature,
    }


def consume_service_auth_nonce(db: Session, *, nonce: str, now: int) -> bool:
    """Atomic insert/consume of nonce digest. Returns False if replayed."""
    digest = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
    expires_at = datetime.fromtimestamp(now + MAX_SKEW_SECONDS, tz=UTC)
    consumed = db.execute(
        text("SELECT memdot_consume_service_auth_nonce(:digest, :expires)"),
        {"digest": digest, "expires": expires_at},
    ).scalar_one()
    return bool(consumed)


def parse_service_auth(
    request: Request,
    db: Session,
    *,
    secret: str | None = None,
) -> ServiceAuthGrant | None:
    try:
        resolved_secret = _require_secret(
            (secret if secret is not None else resolve_mcp_service_secret()).strip()
        )
    except ValueError:
        return None
    version = (request.headers.get(HEADER_VERSION) or "").strip()
    ts_raw = (request.headers.get(HEADER_TS) or "").strip()
    nonce = (request.headers.get(HEADER_NONCE) or "").strip()
    body_b64 = (request.headers.get(HEADER_BODY) or "").strip()
    signature = (request.headers.get(HEADER_SIG) or "").strip()
    if not version or not ts_raw or not nonce or not body_b64 or not signature:
        return None
    if version not in {f"v{SERVICE_AUTH_VERSION}", str(SERVICE_AUTH_VERSION)}:
        return None
    try:
        ts = int(ts_raw)
    except ValueError:
        return None
    now = int(time.time())
    if abs(now - ts) > MAX_SKEW_SECONDS:
        return None
    expected = _sign(resolved_secret, ts=ts_raw, nonce=nonce, body_b64=body_b64)
    if not hmac.compare_digest(expected, signature):
        return None
    try:
        decoded = json.loads(_b64decode(body_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    if not isinstance(decoded, dict):
        return None
    payload = cast(dict[str, Any], decoded)
    authorization = request.headers.get("Authorization")
    expected_hash = payload.get("authorization_sha256")
    if isinstance(expected_hash, str) and expected_hash:
        if not authorization:
            return None
        actual = hashlib.sha256(authorization.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(actual, expected_hash):
            return None
    try:
        account_id = uuid.UUID(str(payload["account_id"]))
        actor_id = uuid.UUID(str(payload["actor_id"]))
        purpose = RequestPurpose(str(payload["purpose"]))
        exp = int(payload["exp"])
        client_id = str(payload.get("client_id") or "")
    except (KeyError, ValueError, TypeError):
        return None
    if purpose not in {
        RequestPurpose.EXTERNAL_READ,
        RequestPurpose.EXTERNAL_PROPOSE,
        RequestPurpose.EXTERNAL_INTERACTION,
    }:
        return None
    if exp < now:
        return None
    scopes_value = payload.get("scopes", [])
    if not isinstance(scopes_value, list):
        return None
    scopes_list = cast(list[object], scopes_value)
    scopes = frozenset(str(item) for item in scopes_list)
    if not client_id:
        return None
    # Durable shared replay protection (multi-replica safe).
    if not consume_service_auth_nonce(db, nonce=nonce, now=now):
        return None
    return ServiceAuthGrant(
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        scopes=scopes,
        client_id=client_id,
        subject=str(payload.get("sub") or ""),
        exp=exp,
    )


def clear_service_auth_nonce_cache() -> None:
    """No-op retained for test imports; durable nonces live in PostgreSQL."""
    return None
