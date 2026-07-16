"""Notion connector stub service with fixture-driven inbound sync."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from memdot_domain.ids import deterministic_uuid5, new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    NotionConnection,
    NotionPageBinding,
    Source,
    SourceRevision,
)
from memdot_core.db.tenant import tenant_scope
from memdot_core.request_context import RequestContext

# Fixture pages for deterministic inbound sync tests (no live Notion OAuth).
NOTION_FIXTURE_PAGES: list[dict[str, str]] = [
    {"notion_page_id": "fixture-page-1", "title": "Getting Started"},
    {"notion_page_id": "fixture-page-2", "title": "Project Notes"},
]


def connect_stub(db: Session, ctx: RequestContext) -> dict[str, Any]:
    connection_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            NotionConnection(
                id=connection_id,
                account_id=ctx.account_id,
                workspace_id="fixture-workspace",
                status="connected",
                oauth_stub={"mode": "stub", "connected_at": datetime.now(UTC).isoformat()},
            )
        )
    return {
        "connectionId": str(connection_id),
        "status": "connected",
        "workspaceId": "fixture-workspace",
    }


def list_pages(db: Session, ctx: RequestContext, *, connection_id: uuid.UUID) -> list[dict[str, str]]:
    with tenant_scope(db, ctx.tenant()):
        connection = db.execute(
            select(NotionConnection).where(
                NotionConnection.account_id == ctx.account_id,
                NotionConnection.id == connection_id,
            )
        ).scalar_one_or_none()
    if connection is None:
        return []
    return [{"notionPageId": page["notion_page_id"], "title": page["title"]} for page in NOTION_FIXTURE_PAGES]


def select_pages(
    db: Session,
    ctx: RequestContext,
    *,
    connection_id: uuid.UUID,
    space_id: uuid.UUID,
    notion_page_ids: list[str],
) -> list[dict[str, Any]]:
    with tenant_scope(db, ctx.tenant()):
        connection = db.execute(
            select(NotionConnection).where(
                NotionConnection.account_id == ctx.account_id,
                NotionConnection.id == connection_id,
            )
        ).scalar_one_or_none()
    if connection is None:
        return []

    selected: list[dict[str, Any]] = []
    with tenant_scope(db, ctx.tenant()):
        for page_id in notion_page_ids:
            fixture = next(
                (page for page in NOTION_FIXTURE_PAGES if page["notion_page_id"] == page_id),
                None,
            )
            title = fixture["title"] if fixture else page_id
            existing = db.execute(
                select(NotionPageBinding).where(
                    NotionPageBinding.account_id == ctx.account_id,
                    NotionPageBinding.connection_id == connection_id,
                    NotionPageBinding.notion_page_id == page_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                selected.append(
                    {
                        "bindingId": str(existing.id),
                        "notionPageId": existing.notion_page_id,
                        "title": existing.title,
                        "syncState": existing.sync_state,
                    }
                )
                continue
            binding_id = new_uuid7()
            db.add(
                NotionPageBinding(
                    id=binding_id,
                    account_id=ctx.account_id,
                    space_id=space_id,
                    connection_id=connection_id,
                    notion_page_id=page_id,
                    title=title,
                    direction="inbound_only",
                    sync_state="idle",
                )
            )
            selected.append(
                {
                    "bindingId": str(binding_id),
                    "notionPageId": page_id,
                    "title": title,
                    "syncState": "idle",
                }
            )
    return selected


def sync_binding_snapshot(
    db: Session,
    ctx: RequestContext,
    *,
    binding_id: uuid.UUID,
    fixture_content: str | None = None,
) -> dict[str, Any] | None:
    """Inbound sync into source revision seam; pauses on conflict instead of LWW."""
    with tenant_scope(db, ctx.tenant()):
        binding = db.execute(
            select(NotionPageBinding).where(
                NotionPageBinding.account_id == ctx.account_id,
                NotionPageBinding.id == binding_id,
            )
        ).scalar_one_or_none()
        if binding is None:
            return None

        if binding.conflict_state == "unresolved":
            binding.sync_state = "paused"
            return {
                "bindingId": str(binding.id),
                "syncState": "paused",
                "conflictState": binding.conflict_state,
                "message": "Sync paused until conflict resolved",
            }

        content = fixture_content or f"Notion snapshot for {binding.notion_page_id}"
        snapshot_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

        if binding.last_snapshot_sha256 and binding.last_snapshot_sha256 != snapshot_sha:
            binding.conflict_state = "unresolved"
            binding.sync_state = "paused"
            return {
                "bindingId": str(binding.id),
                "syncState": "paused",
                "conflictState": "unresolved",
                "message": "Concurrent change detected; sync paused",
            }

        source_id = new_uuid7()
        revision_id = deterministic_uuid5(source_id, snapshot_sha)
        db.add(
            Source(
                id=source_id,
                account_id=ctx.account_id,
                space_id=binding.space_id,
                title=binding.title or binding.notion_page_id,
                processing_status="succeeded",
            )
        )
        db.add(
            SourceRevision(
                id=revision_id,
                account_id=ctx.account_id,
                space_id=binding.space_id,
                source_id=source_id,
                snapshot_sha256=snapshot_sha,
                captured_at=datetime.now(UTC),
            )
        )
        binding.last_snapshot_sha256 = snapshot_sha
        binding.sync_state = "idle"

        return {
            "bindingId": str(binding.id),
            "sourceId": str(source_id),
            "revisionId": str(revision_id),
            "snapshotSha256": snapshot_sha,
            "syncState": binding.sync_state,
            "conflictState": binding.conflict_state,
        }


def resolve_conflict(
    db: Session,
    ctx: RequestContext,
    *,
    binding_id: uuid.UUID,
    resolution: str,
) -> dict[str, Any] | None:
    if resolution not in {"keep_notion", "keep_memdot", "reviewed_merge"}:
        msg = "invalid resolution"
        raise ValueError(msg)

    with tenant_scope(db, ctx.tenant()):
        binding = db.execute(
            select(NotionPageBinding).where(
                NotionPageBinding.account_id == ctx.account_id,
                NotionPageBinding.id == binding_id,
            )
        ).scalar_one_or_none()
        if binding is None:
            return None
        binding.conflict_state = resolution
        binding.sync_state = "idle"
        return {
            "bindingId": str(binding.id),
            "conflictState": binding.conflict_state,
            "syncState": binding.sync_state,
        }
