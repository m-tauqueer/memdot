"""Notion connector service backed by provider adapter (not fixture-only success)."""

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
from memdot_core.notion.adapter import NotionAdapter, encrypt_token
from memdot_core.request_context import RequestContext


def _adapter_for_connection(connection: NotionConnection) -> NotionAdapter:
    mode = "fixture"
    stub = connection.oauth_stub or {}
    if stub.get("mode") == "live":
        mode = "live"
    return NotionAdapter(
        encrypted_token=connection.token_ciphertext,
        token_nonce=connection.token_nonce,
        mode=mode,
    )


def connect(
    db: Session,
    ctx: RequestContext,
    *,
    access_token: str | None = None,
    workspace_id: str = "fixture-workspace",
    mode: str = "fixture",
) -> dict[str, Any]:
    """Create a connection via adapter. Fixture mode still stores encrypted token envelope."""
    if mode not in {"fixture", "live"}:
        msg = "invalid_notion_mode"
        raise ValueError(msg)
    token = access_token or f"fixture-token:{workspace_id}"
    ciphertext, nonce = encrypt_token(token)
    connection_id = new_uuid7()
    with tenant_scope(db, ctx.tenant()):
        db.add(
            NotionConnection(
                id=connection_id,
                account_id=ctx.account_id,
                workspace_id=workspace_id,
                status="connected",
                oauth_stub={
                    "mode": mode,
                    "connected_at": datetime.now(UTC).isoformat(),
                    "adapter": "notion_adapter_v1",
                },
                token_ciphertext=ciphertext,
                token_nonce=nonce,
                pagination_cursor=None,
            )
        )
    return {
        "connectionId": str(connection_id),
        "status": "connected",
        "workspaceId": workspace_id,
        "mode": mode,
    }


# Back-compat alias used by older routes/tests.
def connect_stub(db: Session, ctx: RequestContext) -> dict[str, Any]:
    return connect(db, ctx, mode="fixture")


def list_pages(
    db: Session, ctx: RequestContext, *, connection_id: uuid.UUID
) -> list[dict[str, str]]:
    with tenant_scope(db, ctx.tenant()):
        connection = db.execute(
            select(NotionConnection).where(
                NotionConnection.account_id == ctx.account_id,
                NotionConnection.id == connection_id,
            )
        ).scalar_one_or_none()
    if connection is None:
        return []
    if connection.rate_limited_until and connection.rate_limited_until > datetime.now(UTC):
        return []
    adapter = _adapter_for_connection(connection)
    pages, next_cursor = adapter.list_pages(cursor=connection.pagination_cursor)
    with tenant_scope(db, ctx.tenant()):
        connection.pagination_cursor = next_cursor
        connection.updated_at = datetime.now(UTC)
    return [{"notionPageId": page.notion_page_id, "title": page.title} for page in pages]


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

    adapter = _adapter_for_connection(connection)
    selected: list[dict[str, Any]] = []
    with tenant_scope(db, ctx.tenant()):
        for page_id in notion_page_ids:
            try:
                snapshot = adapter.fetch_page(page_id)
                title = snapshot.title
            except ValueError:
                # A provider error is a visible failure, never a fabricated page.
                raise
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
        connection = db.execute(
            select(NotionConnection).where(
                NotionConnection.account_id == ctx.account_id,
                NotionConnection.id == binding.connection_id,
            )
        ).scalar_one_or_none()
        if connection is None:
            return None

        if binding.conflict_state == "unresolved":
            binding.sync_state = "paused"
            return {
                "bindingId": str(binding.id),
                "syncState": "paused",
                "conflictState": binding.conflict_state,
                "message": "Sync paused until conflict resolved",
            }

        adapter = _adapter_for_connection(connection)
        if fixture_content is not None:
            content = fixture_content
            snapshot_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        else:
            snapshot = adapter.fetch_page(binding.notion_page_id)
            content = snapshot.content_text
            snapshot_sha = snapshot.content_sha256

        if binding.last_snapshot_sha256 and binding.last_snapshot_sha256 != snapshot_sha:
            binding.conflict_state = "unresolved"
            binding.sync_state = "paused"
            return {
                "bindingId": str(binding.id),
                "syncState": "paused",
                "conflictState": "unresolved",
                "message": "Concurrent change detected; sync paused",
            }
        if binding.last_snapshot_sha256 == snapshot_sha and binding.source_id is not None:
            return {
                "bindingId": str(binding.id),
                "sourceId": str(binding.source_id),
                "snapshotSha256": snapshot_sha,
                "syncState": binding.sync_state,
                "conflictState": binding.conflict_state,
                "idempotent": True,
            }

        source_id = binding.source_id or new_uuid7()
        revision_id = deterministic_uuid5(source_id, snapshot_sha)
        if binding.source_id is None:
            db.add(
                Source(
                    id=source_id,
                    account_id=ctx.account_id,
                    space_id=binding.space_id,
                    title=binding.title or binding.notion_page_id,
                    processing_status="succeeded",
                )
            )
            binding.source_id = source_id
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
