"""In-process Notion provider adapter (fixture + fail-closed live)."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from memdot_domain.ports.notion import NotionPageRef, NotionPageSnapshot, NotionProviderPort

FIXTURE_PAGES: list[NotionPageRef] = [
    NotionPageRef(notion_page_id="fixture-page-1", title="Getting Started"),
    NotionPageRef(notion_page_id="fixture-page-2", title="Project Notes"),
]


def encrypt_token(token: str, *, pepper: str | None = None) -> tuple[bytes, bytes]:
    key_material = (pepper or os.environ.get("CORE_SESSION_SIGNING_PEPPER") or "").encode()
    if len(key_material) < 16:
        msg = "notion token encryption requires CORE_SESSION_SIGNING_PEPPER"
        raise RuntimeError(msg)
    key = hashlib.sha256(key_material).digest()
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, token.encode("utf-8"), b"memdot-notion-token-v1")
    return ciphertext, nonce


def decrypt_token(ciphertext: bytes, nonce: bytes, *, pepper: str | None = None) -> str:
    key_material = (pepper or os.environ.get("CORE_SESSION_SIGNING_PEPPER") or "").encode()
    key = hashlib.sha256(key_material).digest()
    return AESGCM(key).decrypt(nonce, ciphertext, b"memdot-notion-token-v1").decode("utf-8")


@dataclass
class NotionAdapter(NotionProviderPort):
    """Requires encrypted token envelope; fixture mode is explicit and testable."""

    encrypted_token: bytes | None = None
    token_nonce: bytes | None = None
    mode: str = "fixture"
    page_size: int = 1
    _rate_limit_hits: int = field(default=0, init=False)

    def _token(self) -> str | None:
        if self.encrypted_token is None or self.token_nonce is None:
            return None
        return decrypt_token(self.encrypted_token, self.token_nonce)

    def rate_limit_sleep_seconds(self) -> float:
        self._rate_limit_hits += 1
        return 0.0 if self.mode == "fixture" else min(0.25 * self._rate_limit_hits, 2.0)

    def list_pages(self, *, cursor: str | None = None) -> tuple[list[NotionPageRef], str | None]:
        if self.mode == "fixture":
            start = int(cursor or "0")
            end = start + self.page_size
            page = FIXTURE_PAGES[start:end]
            next_cursor = str(end) if end < len(FIXTURE_PAGES) else None
            time.sleep(self.rate_limit_sleep_seconds())
            return page, next_cursor
        if not self._token():
            msg = "notion_token_missing"
            raise ValueError(msg)
        msg = "notion_live_http_not_configured"
        raise ValueError(msg)

    def fetch_page(self, notion_page_id: str) -> NotionPageSnapshot:
        if self.mode == "fixture":
            match = next((p for p in FIXTURE_PAGES if p.notion_page_id == notion_page_id), None)
            title = match.title if match else notion_page_id
            content = f"fixture content for {notion_page_id}"
            digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
            time.sleep(self.rate_limit_sleep_seconds())
            return NotionPageSnapshot(
                notion_page_id=notion_page_id,
                title=title,
                content_text=content,
                content_sha256=digest,
            )
        if not self._token():
            msg = "notion_token_missing"
            raise ValueError(msg)
        msg = "notion_live_http_not_configured"
        raise ValueError(msg)
