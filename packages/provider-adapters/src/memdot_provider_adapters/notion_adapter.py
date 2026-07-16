"""Notion provider adapter with encrypted token storage and injectable HTTP."""

from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, cast

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from memdot_domain.ports.notion import NotionPageRef, NotionPageSnapshot, NotionProviderPort

from memdot_provider_adapters.notion_http import EmulatorNotionTransport, NotionHttpTransport

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
    """Adapter that requires an encrypted token envelope; fixture/http modes are explicit.

    ``mode=http`` uses an injectable transport (emulator in tests). Live urllib
    calls against a real Notion workspace require owner authorization and are
    not invoked by default automated gates.
    """

    encrypted_token: bytes | None = None
    token_nonce: bytes | None = None
    mode: str = "fixture"
    page_size: int = 1
    transport: NotionHttpTransport | None = None
    _rate_limit_hits: int = field(default=0, init=False)

    def _token(self) -> str | None:
        if self.encrypted_token is None or self.token_nonce is None:
            return None
        return decrypt_token(self.encrypted_token, self.token_nonce)

    def rate_limit_sleep_seconds(self) -> float:
        self._rate_limit_hits += 1
        return 0.0 if self.mode == "fixture" else min(0.25 * self._rate_limit_hits, 2.0)

    def _http_headers(self) -> dict[str, str]:
        token = self._token()
        if not token:
            msg = "notion_token_missing"
            raise ValueError(msg)
        return {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def _transport(self) -> NotionHttpTransport:
        if self.transport is not None:
            return self.transport
        msg = "notion_http_transport_required"
        raise ValueError(msg)

    def list_pages(self, *, cursor: str | None = None) -> tuple[list[NotionPageRef], str | None]:
        if self.mode == "fixture":
            start = int(cursor or "0")
            end = start + self.page_size
            page = FIXTURE_PAGES[start:end]
            next_cursor = str(end) if end < len(FIXTURE_PAGES) else None
            time.sleep(self.rate_limit_sleep_seconds())
            return page, next_cursor
        if self.mode != "http":
            msg = f"notion_mode_unsupported:{self.mode}"
            raise ValueError(msg)

        status, _hdrs, raw = self._transport().request(
            "GET",
            "search",
            headers=self._http_headers(),
            query={"start_cursor": cursor or "0", "page_size": str(self.page_size)},
        )
        if status == 429:
            time.sleep(self.rate_limit_sleep_seconds())
            status, _hdrs, raw = self._transport().request(
                "GET",
                "search",
                headers=self._http_headers(),
                query={"start_cursor": cursor or "0", "page_size": str(self.page_size)},
            )
        if status >= 400:
            msg = f"notion_list_failed:{status}"
            raise ValueError(msg)
        decoded_obj: object = json.loads(raw.decode("utf-8"))
        if not isinstance(decoded_obj, dict):
            msg = "notion_list_invalid_payload"
            raise ValueError(msg)
        payload = cast(dict[str, object], decoded_obj)
        results_obj = payload.get("results", [])
        results = cast(list[object], results_obj) if isinstance(results_obj, list) else []
        refs: list[NotionPageRef] = []
        for item_obj in results:
            if not isinstance(item_obj, dict):
                continue
            item = cast(dict[str, object], item_obj)
            page_id = str(item.get("id") or "")
            props_obj = item.get("properties")
            title_value = ""
            if isinstance(props_obj, dict):
                props = cast(dict[str, object], props_obj)
                title_value = str(props.get("title") or page_id)
            else:
                title_value = page_id
            refs.append(NotionPageRef(notion_page_id=page_id, title=title_value))
        next_cursor_obj = payload.get("next_cursor")
        return refs, str(next_cursor_obj) if next_cursor_obj is not None else None

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
        if self.mode != "http":
            msg = f"notion_mode_unsupported:{self.mode}"
            raise ValueError(msg)

        status, _hdrs, raw = self._transport().request(
            "GET",
            f"pages/{notion_page_id}",
            headers=self._http_headers(),
        )
        if status == 429:
            time.sleep(self.rate_limit_sleep_seconds())
            status, _hdrs, raw = self._transport().request(
                "GET",
                f"pages/{notion_page_id}",
                headers=self._http_headers(),
            )
        if status >= 400:
            msg = f"notion_fetch_failed:{status}"
            raise ValueError(msg)
        payload: dict[str, Any] = json.loads(raw.decode("utf-8"))
        # Preserve raw JSON snapshot bytes for source revision determinism.
        content_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(content_text.encode("utf-8")).hexdigest()
        title = str(payload.get("id") or notion_page_id)
        return NotionPageSnapshot(
            notion_page_id=notion_page_id,
            title=title,
            content_text=content_text,
            content_sha256=digest,
        )


def default_emulator_adapter(*, token: str = "test-notion-token") -> NotionAdapter:
    """Build an HTTP-mode adapter backed by the in-process emulator."""
    ciphertext, nonce = encrypt_token(token)
    pages = [
        {"id": "fixture-page-1", "object": "page", "properties": {"title": "Getting Started"}},
        {"id": "fixture-page-2", "object": "page", "properties": {"title": "Project Notes"}},
    ]
    return NotionAdapter(
        encrypted_token=ciphertext,
        token_nonce=nonce,
        mode="http",
        transport=EmulatorNotionTransport(pages=pages),
        page_size=1,
    )
