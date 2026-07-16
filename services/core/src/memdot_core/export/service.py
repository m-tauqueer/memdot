"""Account/space export request as a durable workflow.

Packaging is intentionally worker-owned. The request path must never claim a
downloadable archive exists when it only used an in-memory test adapter.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from memdot_domain.ids import new_uuid7
from sqlalchemy.orm import Session

from memdot_core.db.models.ledger import (
    ExportJob,
    OutboxEvent,
)
from memdot_core.db.tenant import tenant_scope
from memdot_core.jobs.service import payload_sha256
from memdot_core.request_context import RequestContext


def create_export(
    db: Session,
    ctx: RequestContext,
    *,
    space_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    export_id = new_uuid7()
    outbox_payload = {
        "export_id": str(export_id),
        "space_id": str(space_id) if space_id else None,
        "requested_at": datetime.now(UTC).isoformat(),
    }
    with tenant_scope(db, ctx.tenant()):
        db.add(
            ExportJob(
                id=export_id,
                account_id=ctx.account_id,
                space_id=space_id,
                status="pending",
                workflow_state="accepted",
                manifest_json={"schemaVersion": 1, "exportId": str(export_id)},
            )
        )
        db.add(
            OutboxEvent(
                id=new_uuid7(),
                account_id=ctx.account_id,
                event_type="export.requested",
                payload_sha256=payload_sha256(outbox_payload),
                payload=outbox_payload,
            )
        )

    return {
        "schemaVersion": 1,
        "exportId": str(export_id),
        "createdAt": outbox_payload["requested_at"],
        "status": "pending",
        "workflowState": "accepted",
    }
