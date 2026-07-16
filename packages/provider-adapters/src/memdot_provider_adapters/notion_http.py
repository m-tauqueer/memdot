"""Injectable Notion HTTP transport + emulator for contract tests.

Live Notion workspace calls require owner authorization. Automated tests must
use the emulator or fixture mode — never a real workspace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class NotionHttpTransport(Protocol):
    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
        query: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]: ...


@dataclass
class UrllibNotionTransport:
    """Minimal urllib transport for real HTTP (owner-authorized only)."""

    base_url: str = "https://api.notion.com/v1"
    timeout_seconds: float = 15.0

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
        query: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
        if query:
            url = f"{url}?{urlencode(query)}"
        req = Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urlopen(req, timeout=self.timeout_seconds) as resp:  # noqa: S310
                raw = resp.read()
                return int(resp.status), dict(resp.headers.items()), raw
        except HTTPError as exc:
            return int(exc.code), dict(exc.headers.items() if exc.headers else {}), exc.read()
        except URLError as exc:
            msg = f"notion_http_transport_error:{type(exc).__name__}"
            raise ValueError(msg) from exc


def _empty_pages() -> list[dict[str, Any]]:
    return []


@dataclass
class EmulatorNotionTransport:
    """In-process Notion API emulator for automated contract tests."""

    pages: list[dict[str, Any]] = field(default_factory=_empty_pages)
    rate_limit_after: int | None = None
    _calls: int = field(default=0, init=False)

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
        query: dict[str, str] | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        del body
        self._calls += 1
        if self.rate_limit_after is not None and self._calls > self.rate_limit_after:
            payload = {"object": "error", "code": "rate_limited", "message": "slow down"}
            return 429, {"Retry-After": "1"}, json.dumps(payload).encode("utf-8")

        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return 401, {}, b'{"object":"error","code":"unauthorized"}'

        if method.upper() == "GET" and path.rstrip("/") == "search":
            start = int((query or {}).get("start_cursor") or "0")
            page_size = int((query or {}).get("page_size") or "100")
            chunk = self.pages[start : start + page_size]
            next_cursor = str(start + page_size) if start + page_size < len(self.pages) else None
            payload = {
                "object": "list",
                "results": chunk,
                "next_cursor": next_cursor,
                "has_more": next_cursor is not None,
            }
            return 200, {}, json.dumps(payload).encode("utf-8")

        if method.upper() == "GET" and path.startswith("pages/"):
            page_id = path.split("/", 1)[1]
            match = next((p for p in self.pages if p.get("id") == page_id), None)
            if match is None:
                return 404, {}, b'{"object":"error","code":"object_not_found"}'
            return 200, {}, json.dumps(match).encode("utf-8")

        return 404, {}, b'{"object":"error","code":"not_found"}'
