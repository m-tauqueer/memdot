"""Signed opaque pagination cursors (TRD-API-003)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

from memdot_core.errors import ErrorCode, FieldError, validation_problem


@dataclass(frozen=True)
class CursorPayload:
    account_id: uuid.UUID
    query_hash: str
    sort_value: str
    item_id: uuid.UUID
    issued_at: int
    expires_at: int


def _cursor_key() -> bytes:
    value = os.environ.get("CORE_CURSOR_SIGNING_KEY") or os.environ.get(
        "CORE_TENANT_CONTEXT_SIGNING_KEY", ""
    )
    if len(value) < 32:
        msg = "CORE_CURSOR_SIGNING_KEY or CORE_TENANT_CONTEXT_SIGNING_KEY required"
        raise RuntimeError(msg)
    return value.encode("utf-8")


def query_hash(query: dict[str, Any]) -> str:
    canonical = json.dumps(query, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def encode_cursor(payload: CursorPayload) -> str:
    body = {
        "a": str(payload.account_id),
        "q": payload.query_hash,
        "s": payload.sort_value,
        "i": str(payload.item_id),
        "iat": payload.issued_at,
        "exp": payload.expires_at,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig = hmac.new(_cursor_key(), raw, hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(raw + b"." + sig.encode("ascii")).decode("ascii")


def decode_cursor(
    token: str,
    *,
    account_id: uuid.UUID,
    query: dict[str, Any],
    max_age_seconds: int = 3600,
) -> CursorPayload | None:
    try:
        padded = token + "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
        raw, sig = decoded.rsplit(b".", 1)
        expected = hmac.new(_cursor_key(), raw, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig.decode("ascii")):
            return None
        body = json.loads(raw.decode("utf-8"))
        if body["a"] != str(account_id):
            return None
        if body["q"] != query_hash(query):
            return None
        now = int(time.time())
        if body["exp"] < now or body["iat"] > now + 60:
            return None
        if now - body["iat"] > max_age_seconds:
            return None
        return CursorPayload(
            account_id=account_id,
            query_hash=body["q"],
            sort_value=body["s"],
            item_id=uuid.UUID(body["i"]),
            issued_at=body["iat"],
            expires_at=body["exp"],
        )
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def cursor_validation_problem(correlation_id: uuid.UUID | None = None):
    return validation_problem(
        correlation_id=correlation_id,
        errors=[FieldError(pointer="/cursor", code=ErrorCode.CURSOR_INVALID)],
    )
