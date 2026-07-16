"""Notion connector port — adapters never own authz or canonical IDs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class NotionPageRef:
    notion_page_id: str
    title: str
    last_edited: str | None = None


@dataclass(frozen=True)
class NotionPageSnapshot:
    notion_page_id: str
    title: str
    content_text: str
    content_sha256: str
    cursor: str | None = None


class NotionProviderPort(Protocol):
    def list_pages(
        self, *, cursor: str | None = None
    ) -> tuple[list[NotionPageRef], str | None]: ...

    def fetch_page(self, notion_page_id: str) -> NotionPageSnapshot: ...

    def rate_limit_sleep_seconds(self) -> float: ...
