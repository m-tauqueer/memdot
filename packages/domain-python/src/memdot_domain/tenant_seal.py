"""Shared tenant-context HMAC sealing for Core and workers."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
import uuid
from dataclasses import dataclass

from memdot_domain.tenancy import RequestPurpose


@dataclass(frozen=True)
class TenantSealMaterial:
    account_id: uuid.UUID
    actor_id: uuid.UUID
    purpose: RequestPurpose
    issued_at: int
    nonce: str
    signature: str


def signing_key_from_env() -> bytes:
    value = os.environ.get("CORE_TENANT_CONTEXT_SIGNING_KEY") or os.environ.get(
        "MEMDOT_TENANT_CONTEXT_SIGNING_KEY", ""
    )
    if len(value) < 32:
        msg = "CORE_TENANT_CONTEXT_SIGNING_KEY must contain at least 32 characters"
        raise RuntimeError(msg)
    return value.encode("utf-8")


def sign_tenant_context(
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    purpose: RequestPurpose,
    issued_at: int,
    nonce: str,
    signing_key: bytes | None = None,
) -> str:
    key = signing_key if signing_key is not None else signing_key_from_env()
    message = f"{account_id}:{actor_id}:{purpose.value}:{issued_at}:{nonce}".encode()
    return hmac.new(key, message, hashlib.sha256).hexdigest()


def new_tenant_seal(
    *,
    account_id: uuid.UUID,
    actor_id: uuid.UUID,
    purpose: RequestPurpose,
    signing_key: bytes | None = None,
) -> TenantSealMaterial:
    issued_at = int(time.time())
    nonce = secrets.token_hex(16)
    signature = sign_tenant_context(
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        issued_at=issued_at,
        nonce=nonce,
        signing_key=signing_key,
    )
    return TenantSealMaterial(
        account_id=account_id,
        actor_id=actor_id,
        purpose=purpose,
        issued_at=issued_at,
        nonce=nonce,
        signature=signature,
    )
