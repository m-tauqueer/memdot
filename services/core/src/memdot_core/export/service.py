"""Account/space export manifest service."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from memdot_domain.ids import new_uuid7
from sqlalchemy import select
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    AuthoredDocument,
    Conversation,
    ExportJob,
    MemoryItem,
    Source,
)
from memdot_core.db.tenant import tenant_scope
from memdot_core.deletion import service as deletion_service
from memdot_core.request_context import RequestContext


def _manifest_artifact(path: str, content: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}


def create_export(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    export_id = new_uuid7()
    created_at = datetime.now(UTC).isoformat()

    sources = db.execute(
        select(Source).where(Source.account_id == ctx.account_id)
    ).scalars().all()
    documents = db.execute(
        select(AuthoredDocument).where(AuthoredDocument.account_id == ctx.account_id)
    ).scalars().all()
    memories = db.execute(
        select(MemoryItem).where(MemoryItem.account_id == ctx.account_id)
    ).scalars().all()
    conversations = db.execute(
        select(Conversation).where(Conversation.account_id == ctx.account_id)
    ).scalars().all()

    if space_id is not None:
        sources = [row for row in sources if row.space_id == space_id]
        documents = [row for row in documents if row.space_id == space_id]
        memories = [row for row in memories if row.space_id == space_id]
        conversations = [row for row in conversations if row.space_id == space_id]

    index_payload = {
        "sources": [str(row.id) for row in sources],
        "documents": [str(row.id) for row in documents],
        "memories": [str(row.id) for row in memories],
        "conversations": [
            str(row.id)
            for row in conversations
            if not deletion_service.is_tombstoned(
                db,
                account_id=ctx.account_id,
                entity_type="conversation",
                entity_id=row.id,
            )
        ],
    }

    artifacts = [
        _manifest_artifact("index.json", json.dumps(index_payload, sort_keys=True)),
        _manifest_artifact("warnings.json", json.dumps({"tombstonesExcluded": True})),
    ]

    manifest = {
        "schemaVersion": 1,
        "exportId": str(export_id),
        "createdAt": created_at,
        "artifacts": artifacts,
    }

    with tenant_scope(db, ctx.tenant()):
        db.add(
            ExportJob(
                id=export_id,
                account_id=ctx.account_id,
                space_id=space_id,
                status="succeeded",
                manifest_json=manifest,
                completed_at=datetime.now(UTC),
            )
        )

    return manifest
