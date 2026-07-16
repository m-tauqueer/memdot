"""AES-GCM encryption for conversation turn payloads at rest."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

AAD = b"memdot-conversation-turn-v1"


def _pepper() -> str:
    value = (os.environ.get("CORE_CONVERSATION_PAYLOAD_KEY") or "").strip()
    if len(value.encode("utf-8")) < 32:
        msg = (
            "CORE_CONVERSATION_PAYLOAD_KEY must contain at least 32 bytes "
            "(no session-pepper fallback)"
        )
        raise RuntimeError(msg)
    return value


def _key(pepper: str | None = None) -> bytes:
    material = (pepper if pepper is not None else _pepper()).encode("utf-8")
    return hashlib.sha256(material).digest()


def encrypt_payload(
    payload: dict[str, Any],
    *,
    pepper: str | None = None,
) -> tuple[bytes, bytes]:
    nonce = secrets.token_bytes(12)
    plaintext = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ciphertext = AESGCM(_key(pepper)).encrypt(nonce, plaintext, AAD)
    return ciphertext, nonce


def decrypt_payload(
    ciphertext: bytes,
    nonce: bytes,
    *,
    pepper: str | None = None,
) -> dict[str, Any]:
    plaintext = AESGCM(_key(pepper)).decrypt(nonce, ciphertext, AAD)
    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        msg = "invalid_conversation_payload"
        raise ValueError(msg)
    return decoded  # type: ignore[return-value]


def payload_content(turn_payload: dict[str, Any] | None) -> str | None:
    if not turn_payload:
        return None
    content = turn_payload.get("content")
    return str(content) if content is not None else None
